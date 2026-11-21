#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = ["opencv-python-headless>=4.9", "numpy", "pillow"]
# ///
"""Seed one known defect per clip into real footage, so a judge can be tested against the truth.

  uv run make_fixtures.py --clips a.mp4 b.mp4 --person one.mp4 --person-t 5 --other-person two.mp4 --other-t 28 --out fixtures/

Every clip has one defect at a known time. truth.json says which check should fire. Clips named control_* have none."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FPS = 24
W, H = 1280, 720
SR = 48000
FONTS = ["/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "C:/Windows/Fonts/arial.ttf"]


def font(size: int):
    for f in FONTS:
        if Path(f).exists():
            return ImageFont.truetype(f, size)
    return ImageFont.load_default(size)


def read_clip(path: str, start: float, dur: float, w: int = W, h: int = H) -> np.ndarray:
    vf = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps={FPS},format=bgr24"
    cmd = ["ffmpeg", "-v", "error", "-nostdin", "-ss", str(start), "-t", str(dur), "-i", path, "-vf", vf, "-f", "rawvideo", "-"]
    data = subprocess.run(cmd, capture_output=True).stdout
    n = len(data) // (w * h * 3)
    return np.frombuffer(data[: n * w * h * 3], np.uint8).reshape(n, h, w, 3).copy()


def text(frame: np.ndarray, s: str, xy, size: int, colour=(255, 255, 255), stroke: int = 2) -> np.ndarray:
    im = Image.fromarray(frame[..., ::-1])
    d = ImageDraw.Draw(im)
    d.text(xy, s, font=font(size), fill=colour, stroke_width=stroke, stroke_fill=(0, 0, 0))
    return np.array(im)[..., ::-1].copy()


def glyphs_proportional(frame: np.ndarray, s: str, cx: int, y: int, size: int) -> np.ndarray:
    """Proportional figures: each digit takes only its own ink width, so the line reflows as it counts."""
    im = Image.fromarray(frame[..., ::-1])
    d = ImageDraw.Draw(im)
    f = font(size)
    widths = [d.textbbox((0, 0), c, font=f)[2] - d.textbbox((0, 0), c, font=f)[0] for c in s]
    gap = int(size * 0.08)
    # Proportional figures in the wild differ more than Arial's ink does, so make each digit's advance follow its shape.
    extra = {"1": -int(size * 0.02), "7": int(size * 0.03), "0": int(size * 0.05), "4": int(size * 0.04), "8": int(size * 0.03)}
    widths = [w + extra.get(c, 0) for c, w in zip(s, widths)]
    total = sum(widths) + gap * (len(s) - 1)
    x = cx - total // 2
    for c, w in zip(s, widths):
        box = d.textbbox((0, 0), c, font=f)
        d.text((x - box[0], y), c, font=f, fill=(255, 255, 255))
        x += w + gap
    return np.array(im)[..., ::-1].copy()


def glyphs_tabular(frame: np.ndarray, s: str, cx: int, y: int, size: int) -> np.ndarray:
    """Tabular figures: every digit sits in a cell of one width, so the line never moves."""
    im = Image.fromarray(frame[..., ::-1])
    d = ImageDraw.Draw(im)
    f = font(size)
    cell = max(d.textbbox((0, 0), c, font=f)[2] - d.textbbox((0, 0), c, font=f)[0] for c in "0123456789") + int(size * 0.08)
    x = cx - cell * len(s) // 2
    for c in s:
        box = d.textbbox((0, 0), c, font=f)
        w = box[2] - box[0]
        d.text((x + (cell - w) // 2 - box[0], y), c, font=f, fill=(255, 255, 255))
        x += cell
    return np.array(im)[..., ::-1].copy()


def score_track(cuts: list[float], dur: float, late_ms: float = 0.0, extra_hits: list[float] | None = None) -> np.ndarray:
    """A quiet pad with one percussive hit per cut. late_ms moves every hit after its cut."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    pad = 0.16 * (np.sin(2 * np.pi * 110 * t) + 0.5 * np.sin(2 * np.pi * 165 * t) + 0.3 * np.sin(2 * np.pi * 220 * t))
    y = pad.copy()
    rng = np.random.default_rng(3)
    for c in list(cuts) + list(extra_hits or []):
        at = int((c + (late_ms / 1000 if c in cuts else 0)) * SR)
        ln = int(0.18 * SR)
        if at + ln >= n:
            continue
        tt = np.arange(ln) / SR
        hit = 0.34 * np.sin(2 * np.pi * 70 * tt) * np.exp(-tt * 22) + 0.2 * rng.standard_normal(ln) * np.exp(-tt * 45)
        y[at:at + ln] += hit
    fade = int(0.4 * SR)
    y[-fade:] *= np.linspace(1, 0, fade)
    y = y / max(float(np.abs(y).max()), 1e-6) * (0.72 if cuts or extra_hits else 0.3)
    return np.c_[y, y].astype(np.float32)


def write(path: Path, frames, audio: np.ndarray | None, w: int = W, h: int = H, crf: int = 16) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    wav = None
    cmd = ["ffmpeg", "-y", "-v", "error", "-nostdin", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}", "-r", str(FPS), "-i", "-"]
    if audio is not None:
        wav = path.with_suffix(".f32")
        wav.write_bytes(np.clip(audio, -1.0, 1.0).astype(np.float32).tobytes())
        cmd += ["-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", str(wav)]
    cmd += ["-c:v", "libx264", "-preset", "fast", "-crf", str(crf), "-pix_fmt", "yuv420p"]
    if audio is not None:
        cmd += ["-c:a", "aac", "-b:a", "192k"]
    cmd += ["-shortest", str(path)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in frames:
        p.stdin.write(np.asarray(f, np.uint8).tobytes())
    p.stdin.close()
    p.wait()
    if wav:
        wav.unlink(missing_ok=True)


def titled(frames: np.ndarray, start: float = 0.4, end: float = 3.6) -> list[np.ndarray]:
    out = []
    for i, f in enumerate(frames):
        t = i / FPS
        if start <= t <= end:
            f = text(f, "Ship your film", (90, 250), 92)
            f = text(f, "Made by one agent in one night", (94, 362), 30, stroke=1)
        if 6.2 <= t <= 9.4:
            f = text(f, "Every cut lands on the beat", (360, 610), 38)
        out.append(f)
    return out


def build(args) -> dict:
    out = Path(args.out)
    c = args.clips
    shots = [read_clip(c[0], s, 2.0) if i == 0 else read_clip(c[1], s, 2.0) for i, s in ((0, 0.2), (0, 2.6), (0, 5.2), (1, 1.0), (1, 6.2), (1, 9.4))]
    base = np.concatenate(shots)
    n = len(base)
    dur = n / FPS
    cuts = [round(sum(len(s) for s in shots[:i + 1]) / FPS, 4) for i in range(len(shots) - 1)]
    aud = score_track(cuts, dur)
    clean = titled(base)
    truth = {}

    def emit(name, frames, audio=None, expect=None, at=None, args_=None, w=W, h=H, must_clear=None):
        if args.only is None or any(k in name for k in args.only.split(",")):
            write(out / f"{name}.mp4", frames, aud if audio is None else audio, w, h)
        truth[name] = {"expect": expect or [], "at": at, "args": args_ or [], "must_clear": must_clear or []}
        print(name, flush=True)

    allow = ["--allow", "Ship"]
    emit("control_clean", clean, args_=allow)

    # broken frames
    f = list(clean)
    bi = int(5.0 * FPS)
    f[bi] = np.zeros_like(f[bi])
    f[bi + 1] = np.zeros_like(f[bi])
    emit("black_two_frames", f, expect=["black_frames"], at=5.0)

    f = list(clean)
    a = int(0.6 * FPS)
    for i in range(a, a + FPS):
        f[i] = f[a]
    emit("freeze_one_second", f, expect=["frozen_frames"], at=0.6)

    f = list(clean)
    gi = int(3.0 * FPS)
    g = f[gi].copy()
    rng = np.random.default_rng(1)
    for _ in range(90):
        x, y = rng.integers(0, W - 80), rng.integers(0, H - 40)
        g[y:y + 40, x:x + 80] = rng.integers(0, 255, 3)
    f[gi] = g
    emit("glitch_one_frame", f, expect=["glitch_frames"], at=3.0)

    f = list(clean)
    for i in range(int(6.1 * FPS), int(7.9 * FPS)):
        d = 14 if i % 2 else -14
        f[i] = np.clip(f[i].astype(np.int16) + d, 0, 255).astype(np.uint8)
    emit("flicker_shot", f, expect=["flicker"], at=6.1)

    f = list(clean)
    for i in range(int(0.3 * FPS), int(1.9 * FPS), 3):
        f[i] = f[i - 1]
    emit("stutter_repeats", f, expect=["repeated_frames"], at=0.3)

    f = list(clean)
    for i in range(int(8.2 * FPS), int(9.6 * FPS)):
        f[i] = np.full_like(f[i], 245 if (i // 2) % 2 else 8)
    emit("strobe_flash", f, expect=["flash_safety"], at=8.2)

    f = list(clean)
    si = int(5.0 * FPS)
    f[si], f[si + 1] = base[int(9 * FPS)], base[int(9 * FPS) + 1]
    emit("seam_two_frames", f, expect=["seam_shots"], at=5.0)

    # banding: a dark sky gradient with dither that the source keeps and the upload destroys
    f = list(clean)
    rng = np.random.default_rng(5)
    yy = np.linspace(4, 34, H)[:, None]
    xx = np.linspace(0, 8, W)[None, :]
    for i in range(int(6 * FPS), int(10 * FPS)):
        grad = yy + xx + 3 * np.sin(i / 40 + yy / 12)
        dith = grad + rng.normal(0, 1.1, (H, W))
        g = np.clip(dith, 0, 255).astype(np.uint8)
        f[i] = np.dstack([np.clip(g * 1.25, 0, 255).astype(np.uint8), np.clip(g * 1.05, 0, 255).astype(np.uint8), g])
    emit("dark_gradient_banding", f, expect=["upload_banding"], at=6.0)

    # counters
    vals = np.linspace(4100, 4980, int(3.4 * FPS)).astype(int)
    pf, tf = list(clean), list(clean)
    for k, i in enumerate(range(int(6.1 * FPS), int(6.1 * FPS) + len(vals))):
        s = str(vals[k])
        pf[i] = glyphs_proportional(base[i], s, W // 2, 240, 120)
        tf[i] = glyphs_tabular(base[i], s, W // 2, 240, 120)
    emit("counter_jiggles", pf, expect=["counter_jiggle"], at=6.1)
    emit("control_counter_tabular", tf, args_=allow)

    # sound after the cut
    emit("sound_late_160ms", clean, score_track(cuts, dur, late_ms=160), expect=["sound_on_cut"], at=cuts[0])
    emit("control_sound_on_cut", clean, score_track(cuts, dur, late_ms=0))

    # spelling
    f = []
    for i, fr in enumerate(base):
        t = i / FPS
        if 0.4 <= t <= 3.6:
            fr = text(fr, "Recieve your orrder", (90, 250), 84)
            fr = text(fr, "Delivered tomorow morning", (94, 362), 30, stroke=1)
        f.append(fr)
    emit("spelling_mistakes", f, expect=["spelling"], at=0.4)

    # same size
    f = []
    for i, fr in enumerate(base):
        if 0.4 <= i / FPS <= 3.6:
            for k, s in enumerate(["Fast delivery", "Free returns", "Great support", "Low prices"]):
                fr = text(fr, s, (120 + (k % 2) * 560, 180 + (k // 2) * 240), 44)
        f.append(fr)
    emit("same_size_text", f, expect=["text_scale"], at=0.4)

    # load
    f = []
    rng = np.random.default_rng(9)
    words = "fast cheap new best top free easy smart bold clean real live more next plan team work home data page shop deal save".split()
    boxes = [(rng.integers(20, W - 200), rng.integers(20, H - 60), words[rng.integers(0, len(words))], rng.integers(0, 255, 3).tolist()) for _ in range(46)]
    for i, fr in enumerate(base):
        if 0.4 <= i / FPS <= 3.6:
            for x, y, s, col in boxes:
                cv2.rectangle(fr, (int(x) - 6, int(y) - 4), (int(x) + 150, int(y) + 34), col, 2)
                fr = text(fr, s, (int(x), int(y)), 26, stroke=1)
        f.append(fr)
    emit("too_much_on_screen", f, expect=["text_load", "frame_load"], at=0.4)

    # nothing leads: a wall of equal cards
    f = []
    for i, fr in enumerate(base):
        if 0.4 <= i / FPS <= 3.6:
            fr = np.full_like(fr, 40)
            for r in range(3):
                for k in range(5):
                    x, y = 60 + k * 240, 60 + r * 215
                    cv2.rectangle(fr, (x, y), (x + 200, y + 170), (235, 235, 235), -1)
                    cv2.circle(fr, (x + 100, y + 85), 50, (30, 30, 200), -1)
        f.append(fr)
    emit("nothing_leads", f, expect=["leads_the_eye"], at=0.4)

    # motion: a shape that starts for no reason, then the same with a hit on its start
    f = list(clean)
    st = int(7.4 * FPS)
    for i in range(st - int(1.2 * FPS), int(8 * FPS) - 1):
        x = 200 if i < st else 200 + (i - st) * 30
        cv2.rectangle(f[i], (x, 120), (x + 150, 240), (240, 240, 240), -1)
    emit("motion_no_cause", f, expect=["motion_cause"], at=7.4)
    emit("control_motion_with_hit", f, score_track(cuts, dur, extra_hits=[7.4]), args_=allow)

    # pan shots: pinned, slid and locked labels
    still = read_clip(c[1], 1.0, 0.1, W * 2, H * 2)[0]
    pan_frames = int(4 * FPS)
    def panned(mode):
        out_ = []
        for i, fr in enumerate(clean):
            if 4 * FPS <= i < 4 * FPS + pan_frames:
                k = i - 4 * FPS
                dx = int(100 + k * 6)
                view = still[300:300 + H, dx:dx + W].copy()
                # a target painted into the world
                wx, wy = 700 - dx + 100, 200
                cv2.circle(view, (wx + 40, wy + 180), 22, (40, 200, 240), -1)
                lx = wx - 20
                if mode == "pinned":
                    lx = 420
                elif mode == "slid":
                    lx = wx - 20 + int(k * 3)
                view = text(view, "Battery", (lx, wy + 90), 44)
                out_.append(view)
            else:
                out_.append(fr)
        return out_
    emit("label_pinned_to_glass", panned("pinned"), expect=["pinned_graphics"], at=4.0)
    emit("label_slides_off", panned("slid"), expect=["label_drift"], at=4.0)
    emit("control_label_locked", panned("locked"), args_=allow)

    # level
    emit("audio_clipping", clean, np.clip(aud * 9, -1, 1), expect=["clipping"], at=0.0)
    a2 = aud.copy()
    a2[int(4.5 * SR):int(4.62 * SR)] = 0
    emit("audio_dropout", clean, a2, expect=["audio_dropouts"], at=4.5)

    # contrast and vertical safe zones
    f = []
    for i, fr in enumerate(base):
        if 0.4 <= i / FPS <= 3.6:
            fr = fr.copy()
            fr[220:360, 60:900] = (60, 60, 60)
            im = Image.fromarray(fr[..., ::-1])
            d = ImageDraw.Draw(im)
            d.text((90, 250), "Buy the blue one", font=font(70), fill=(84, 84, 84))
            fr = np.array(im)[..., ::-1].copy()
        f.append(fr)
    emit("low_contrast_text", f, expect=["text_contrast"], at=0.4)

    vbase = np.concatenate([read_clip(c[0], 0.0, 2.0, 1080, 1920), read_clip(c[0], 6.0, 2.0, 1080, 1920), read_clip(c[1], 4.2, 2.0, 1080, 1920)])
    vcuts = [2.0, 4.0]
    vaud = score_track(vcuts, len(vbase) / FPS)
    def vert(y):
        out_ = []
        for i, fr in enumerate(vbase):
            if 0.4 <= i / FPS <= 3.6:
                fr = text(fr, "Tap to get yours", (160, y), 84)
            out_.append(fr)
        return out_
    emit("vertical_text_under_ui", vert(1620), vaud, expect=["safe_zone"], at=0.4, args_=["--platform", "reels"], w=1080, h=1920)
    emit("control_vertical_safe", vert(800), vaud, args_=["--platform", "reels"], w=1080, h=1920)

    # a bright control: the same footage lifted out of the dark, so the upload check should stay quiet
    lifted = [np.clip(((fr.astype(np.float32) / 255.0) ** 0.42) * 235 + 12, 0, 255).astype(np.uint8) for fr in base]
    emit("control_bright", lifted, must_clear=["upload_banding"])

    # people: a person, a different shot, then the same person again or someone else
    if args.person and args.other_person:
        p1 = read_clip(args.person, args.person_t, 1.4)
        p2 = read_clip(args.person, args.person_t + 1.5, 1.4)
        other = read_clip(args.other_person, args.other_t, 1.4)
        filler = read_clip(c[1], 1.0, 1.4)
        pcuts = [round(len(p1) / FPS, 4), round((len(p1) + len(filler)) / FPS, 4)]
        paud = score_track(pcuts, (len(p1) + len(filler) + len(p2)) / FPS)
        emit("control_same_person", np.concatenate([p1, filler, p2]), paud, args_=["--one-character"])
        emit("face_swapped", np.concatenate([p1, filler, other]), paud, expect=["face_identity"], at=pcuts[1], args_=["--one-character"])

        def recolour(frames):
            out_ = []
            for fr in frames:
                fr = fr.copy()
                hsv = cv2.cvtColor(fr[args.torso_y:, :], cv2.COLOR_BGR2HSV).astype(np.int16)
                hsv[..., 0] = (hsv[..., 0] + 90) % 180
                hsv[..., 1] = np.clip(hsv[..., 1] + 150, 0, 255)
                hsv[..., 2] = np.clip(hsv[..., 2] + 70, 0, 255)
                fr[args.torso_y:, :] = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
                out_.append(fr)
            return np.stack(out_)
        q1 = read_clip(args.dressed, args.dressed_t, 1.4)
        q2 = read_clip(args.dressed, args.dressed_t + 0.8, 1.4)
        qcuts = [round(len(q1) / FPS, 4), round((len(q1) + len(filler)) / FPS, 4)]
        qaud = score_track(qcuts, (len(q1) + len(filler) + len(q2)) / FPS)
        emit("outfit_changed", np.concatenate([q1, filler, recolour(q2)]), qaud, expect=["outfit_change"], at=qcuts[1], args_=["--one-character"])
        emit("control_same_outfit", np.concatenate([q1, filler, q2]), qaud, args_=["--one-character"])

        ramp = np.linspace(2.2, 0.2, W)[None, :, None]
        lit_l = np.clip(p1.astype(np.float32) * ramp, 0, 255).astype(np.uint8)
        lit_r = np.clip(p2.astype(np.float32) * ramp[:, ::-1], 0, 255).astype(np.uint8)
        emit("key_light_flipped", np.concatenate([lit_l, filler, lit_r]), paud, expect=["face_light_change"], at=pcuts[1], args_=["--one-character"])

    # looks like the template, or like the references: same shots on both sides of the test
    def grade(frames, kind):
        out_ = []
        for fr in frames:
            x = fr.astype(np.float32)
            if kind == "warm":
                x = x * np.array([0.72, 0.95, 1.2]) + np.array([6, 14, 26])
            else:
                x = (x - 90) * 1.5 + 100
                x = x * np.array([1.3, 1.05, 0.72])
            out_.append(np.clip(x, 0, 255).astype(np.uint8))
        return np.stack(out_)

    def cut_up(clip, starts, length):
        return np.concatenate([read_clip(clip, s, length) for s in starts])

    ref = grade(cut_up(c[0], [0.2, 2.6, 5.2], 2.2), "warm")
    tpl = grade(cut_up(c[1], [0.5, 1.5, 4.2, 5.0, 6.5, 7.5], 0.75), "cold")
    near_ref = grade(cut_up(c[0], [0.6, 3.0, 5.7], 2.2), "warm")
    near_tpl = grade(cut_up(c[1], [0.9, 2.0, 4.6, 5.3, 7.0, 8.0], 0.75), "cold")
    for name, frames in (("ref_pack", ref), ("template_pack", tpl)):
        write(out / "packs" / f"{name}.mp4", frames, score_track([], len(frames) / FPS))
    pack = ["--refs", "{fixtures}/packs/ref_pack.mp4", "--template", "{fixtures}/packs/template_pack.mp4"]
    emit("looks_like_template", near_tpl, score_track([], len(near_tpl) / FPS), expect=["template_vs_references"], args_=pack)
    emit("control_looks_like_reference", near_ref, score_track([], len(near_ref) / FPS), args_=pack, must_clear=["template_vs_references"])

    (out / "truth.json").write_text(json.dumps(truth, indent=1))
    return truth


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clips", nargs=2, required=True, help="two real clips, each at least 12 s")
    ap.add_argument("--person", help="clip with one person's face filling much of the frame")
    ap.add_argument("--person-t", type=float, default=0.0)
    ap.add_argument("--other-person", help="clip with a different person")
    ap.add_argument("--other-t", type=float, default=0.0)
    ap.add_argument("--dressed", help="clip with a person whose clothing is in frame")
    ap.add_argument("--dressed-t", type=float, default=0.0)
    ap.add_argument("--torso-y", type=int, default=400, help="the row where clothing starts in that clip")
    ap.add_argument("--only", help="rebuild only clips whose name contains one of these, comma separated")
    ap.add_argument("--out", required=True)
    build(ap.parse_args())


if __name__ == "__main__":
    main()
