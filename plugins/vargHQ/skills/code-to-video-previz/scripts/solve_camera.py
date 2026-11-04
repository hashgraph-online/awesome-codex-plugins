#!/usr/bin/env python3
"""Recover a shot's real 3D camera with Blender's motion tracker, headless, on CPU. One shot only, no cuts in the clip.

  ffmpeg -ss 74.083 -to 79.375 -i reference.mp4 -an shot.mp4
  uv run --python 3.13 --with bpy==5.2.3 python solve_camera.py shot.mp4 --out solved.json
  python3 solved_to_staging.py solved.json --horizon-v .35 --height 1.7 --out path.json

It tracks features across the whole shot, solves with the long tracks, repeats at several fixed lenses and prints the error of
each: the lowest shows the lens, and a flat stretch means a range. It needs parallax, meaning a camera that really moves through
a static world. A nodal pan or a locked-off shot can't be solved this way, and neither can a moving subject that fills the frame.
Lens distortion isn't modelled. The world it returns has no scale and no gravity: solved_to_staging.py adds those.
"""
import argparse
import json
import os
import sys
import time

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
ap = argparse.ArgumentParser()
ap.add_argument("clip")
ap.add_argument("--out", default="solved.json")
ap.add_argument("--lenses", default="18,22,25,28,32,36,40,50,65,85", help="fixed lenses to try, full-frame mm")
ap.add_argument("--min-span", type=float, default=.45, help="keep tracks that last this share of the shot")
ap.add_argument("--births", type=int, default=6, help="how many frames to look for new features on")
a = ap.parse_args(argv)

t0 = time.time()
bpy.ops.wm.read_factory_settings()
win = bpy.context.window_manager.windows[0]
scene = bpy.context.scene
clip = bpy.data.movieclips.load(os.path.abspath(a.clip))
# Headless, the tracker's operators need a real Clip Editor area to run in.
area = win.screen.areas[0]
area.type = "CLIP_EDITOR"
sp = area.spaces.active
sp.clip, sp.mode = clip, "TRACKING"
region = next(r for r in area.regions if r.type == "WINDOW")
tr, cam = clip.tracking, clip.tracking.camera
s = tr.settings
s.default_pattern_size, s.default_search_size = 15, 41
s.default_motion_model, s.use_default_brute = "Affine", False
s.default_correlation_min, s.default_frames_limit = .78, 0
cam.sensor_width, cam.pixel_aspect = 36., 1.
cam.k1 = cam.k2 = cam.k3 = 0.
n = clip.frame_duration
W, H = clip.size
scene.frame_start, scene.frame_end = 1, n
ov = dict(window=win, area=area, region=region, space_data=sp, edit_movieclip=clip)
obj = tr.objects.active
rec = obj.reconstruction


def goto(f):
    # Both are needed: without clip_user, detect_features silently works on frame 1 every time.
    scene.frame_current = f
    scene.frame_set(f)
    sp.clip_user.frame_current = f


def select_delete(names):
    for t in tr.tracks:
        t.select = t.name in names
    if names:
        bpy.ops.clip.delete_track()


def solve(focal, refine=False):
    cam.focal_length = float(focal)
    s.refine_intrinsics_focal_length = refine
    goto(1)
    bpy.ops.clip.solve_camera()
    return rec.average_error if rec.is_valid else None


def dump(path):
    json.dump(dict(
        focal=cam.focal_length, error=rec.average_error, size=[W, H], frames=n, fps=clip.fps,
        cameras=[dict(frame=c.frame, error=c.average_error, matrix=[list(r) for r in c.matrix]) for c in rec.cameras],
        points=[dict(name=t.name, co=list(t.bundle), error=t.average_error) for t in tr.tracks if t.has_bundle],
    ), open(path, "w"))


with bpy.context.temp_override(**ov):
    births = sorted({1 + round(i * (n - 1) / max(a.births - 1, 1)) for i in range(a.births)})
    for f in births:
        goto(f)
        before = {t.name for t in tr.tracks}
        taken = [(m.co[0] * W, m.co[1] * H) for t in tr.tracks for m in [t.markers.find_frame(f, exact=True)] if m and not m.mute]
        bpy.ops.clip.detect_features(threshold=.08, min_distance=10, margin=6, placement="FRAME")
        fresh = [t for t in tr.tracks if t.name not in before]
        dup = set()
        for t in fresh:
            m = t.markers.find_frame(f, exact=True)
            if any((m.co[0] * W - x) ** 2 + (m.co[1] * H - y) ** 2 < 36 for x, y in taken):
                dup.add(t.name)
        select_delete(dup)
        for t in tr.tracks:
            t.select = t.name not in before
        if f < n:
            bpy.ops.clip.track_markers(backwards=False, sequence=True)
        goto(f)
        if f > 1:
            bpy.ops.clip.track_markers(backwards=True, sequence=True)
        print(f"frame {f}: {len(tr.tracks)} tracks, {time.time() - t0:.0f} s", flush=True)

    # Long tracks hold the geometry. Automatic keyframes with heavy cleaning sent this to 13.8 px, first and last frame was stable.
    short = set()
    for t in tr.tracks:
        fr = [m.frame for m in t.markers if not m.mute]
        if not fr or max(fr) - min(fr) < a.min_span * n:
            short.add(t.name)
    select_delete(short)
    print(f"long tracks: {len(tr.tracks)} of {len(tr.tracks) + len(short)}", flush=True)
    if len(tr.tracks) < 12:
        raise SystemExit("too few long tracks to solve: the shot is too dark, too short or too blurred. Fix the camera by eye instead.")
    s.refine_intrinsics_radial_distortion = s.refine_intrinsics_principal_point = False
    s.use_keyframe_selection = False
    obj.keyframe_a, obj.keyframe_b = 1, n

    def scan():
        table = []
        for focal in (float(x) for x in a.lenses.split(",")):
            err = solve(focal)
            table.append((focal, err, len(rec.cameras) if err is not None else 0))
        good = [t for t in table if t[1] is not None and t[2] >= .9 * n]
        if not good:
            raise SystemExit("no lens solved the shot. Probably not enough parallax: a nodal pan, a locked-off shot or a moving subject.")
        return table, good, min(good, key=lambda t: t[1])

    # Scan, drop the tracks that don't fit (mostly on moving things), then scan again: the error curve only sharpens once they're gone.
    _, _, best = scan()
    err = solve(best[0])
    bad = {t.name for t in tr.tracks if t.has_bundle and t.average_error > max(.9, err * 2.2)}
    select_delete(bad)
    print(f"dropped {len(bad)} tracks that didn't fit", flush=True)
    table, good, best = scan()
    for focal, e, frames in table:
        print(f"lens {focal:>5.1f} mm: error {'failed' if e is None else f'{e:.3f} px'}, {frames} of {n} frames", flush=True)
    free = None
    try:
        free_err = solve(best[0], refine=True)
        free = (round(cam.focal_length, 2), round(free_err, 3)) if free_err is not None else None
    except RuntimeError:
        pass
    err = solve(best[0])
    dump(a.out)
    flat = [t[0] for t in good if t[1] <= best[1] * 1.05]
    print(json.dumps(dict(lens_mm=best[0], lens_range_mm=[min(flat), max(flat)], free_solve_mm_error=free, error_px=round(err, 3),
                          frames=f"{len(rec.cameras)} of {n}", tracks=sum(t.has_bundle for t in tr.tracks),
                          seconds=round(time.time() - t0), out=a.out)))
    print("Trust check: render a test scene with surface detail through a known camera and solve that too, if the result matters.")
