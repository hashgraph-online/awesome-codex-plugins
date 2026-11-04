#!/usr/bin/env python3
"""Measure one generated take so nobody has to trust the request.

Reads the clip with ffprobe and ffmpeg and reports what came back: length, frames, codec, bitrate, audio, where the
cuts really are, how far they sit from the plan, whether the previz came back unchanged, and how many frames are held.

    python3 take_check.py take.mp4
    python3 take_check.py take.mp4 --plan 0,2.5,5 --reference previz.mp4 --cadence --json

Exit code: 0 clean, 1 at least one warning, 2 the clip could not be read.
Thresholds are varg house defaults from a few films, not published standards. Standard library, ffmpeg and ffprobe.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

SCENE_THRESHOLD = 0.25  # Segmind and Krea checked for hidden cuts with scene detection at 0.2 to 0.3
PASS_THROUGH_SSIM = 0.85  # a redrawn clip should not sit this close to its previz in luma
CUT_TOLERANCE_FRAMES = 1


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, errors="replace")


def probe(path):
    r = run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path])
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or "ffprobe failed")
    data = json.loads(r.stdout)
    video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    if video is None:
        raise RuntimeError("no video stream")
    audio = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
    fmt = data.get("format", {})
    fps = float(Fraction(video.get("avg_frame_rate") or "0/1")) if video.get("avg_frame_rate") != "0/0" else 0.0
    duration = float(video.get("duration") or fmt.get("duration") or 0)
    frames = int(video["nb_frames"]) if str(video.get("nb_frames", "")).isdigit() else round(duration * fps)
    bit_rate = video.get("bit_rate") or fmt.get("bit_rate") or 0
    return {
        "width": video.get("width"),
        "height": video.get("height"),
        "fps": round(fps, 3),
        "frames": frames,
        "duration": round(duration, 3),
        "codec": video.get("codec_name"),
        "pix_fmt": video.get("pix_fmt"),
        "color_space": video.get("color_space"),
        "bit_mbps": round(int(bit_rate) / 1e6, 2),
        "has_audio": audio is not None,
    }


def keyframes(path):
    r = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-skip_frame", "nokey",
             "-show_entries", "frame=pts_time", "-of", "csv=p=0", path])
    times = []
    for line in r.stdout.splitlines():
        value = line.strip().strip(",")
        if value and value != "N/A":
            times.append(round(float(value), 3))
    return sorted(times)


def is_periodic(times):
    """A regular keyframe interval is the encoder's GOP, not a list of cuts. Scene-cut keyframes can sit in between."""
    if len(times) < 4:
        return False
    gaps = [round(b - a, 1) for a, b in zip(times, times[1:])]
    most_common = max(set(gaps), key=gaps.count)
    return gaps.count(most_common) / len(gaps) >= 0.6


def scene_cuts(path):
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-an", "-vf",
             f"select='gt(scene,{SCENE_THRESHOLD})',showinfo", "-f", "null", "-"])
    return [round(float(m), 3) for m in re.findall(r"pts_time:([0-9.]+)", r.stderr)]


def compare_plan(plan, cuts, fps, duration):
    rows = []
    interior = [t for t in plan if 0 < t < duration - 0.5]  # the end of the last shot is not a cut
    for t in interior:
        nearest = min(cuts, key=lambda c: abs(c - t)) if cuts else None
        offset = None if nearest is None else round((nearest - t) * fps, 1)
        rows.append({
            "planned": t,
            "measured": nearest,
            "offset_frames": offset,
            "ok": offset is not None and abs(offset) <= CUT_TOLERANCE_FRAMES,
        })
    return rows


def ssim_per_shot(path, reference, width, height, cuts, fps):
    """Score each shot alone: one previz shot that came back unchanged is lost in a whole-clip average."""
    graph = (f"[0:v]scale={width}:{height},format=gray[a];"
             f"[1:v]scale={width}:{height},format=gray[b];[a][b]ssim=stats_file=-")
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-i", reference, "-an",
             "-filter_complex", graph, "-f", "null", "-"])
    scores = [float(v) for v in re.findall(r"All:([0-9.]+)", r.stdout)]
    if not scores:
        return []
    edges = [0] + [round(c * fps) for c in cuts] + [len(scores)]
    shots = []
    for start, end in zip(edges, edges[1:]):
        chunk = scores[start:end]
        if chunk:
            shots.append({"start": round(start / fps, 3), "end": round(end / fps, 3),
                          "ssim_luma": round(sum(chunk) / len(chunk), 3)})
    return shots


def saturation(path):
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-an", "-vf",
             "signalstats,metadata=print:key=lavfi.signalstats.SATAVG:file=-", "-f", "null", "-"])
    values = [float(v) for v in re.findall(r"SATAVG=([0-9.]+)", r.stdout)]
    return round(sum(values) / len(values), 2) if values else None


def held_share(path, frames):
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-an", "-vf", "mpdecimate,showinfo",
             "-f", "null", "-"])
    kept = len(re.findall(r"pts_time:", r.stderr))
    return round(1 - kept / frames, 3) if frames else None


def main():
    parser = argparse.ArgumentParser(description="Measure one generated take.")
    parser.add_argument("take")
    parser.add_argument("--plan", help="planned cut times in seconds, comma separated, for example 0,2.5,5")
    parser.add_argument("--reference", help="the previz clip sent as @video1, to catch a pass-through")
    parser.add_argument("--cadence", action="store_true", help="share of held frames (on twos reads about 0.5)")
    parser.add_argument("--json", action="store_true", help="print JSON for the take's sidecar")
    args = parser.parse_args()

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        print("needs ffmpeg and ffprobe on PATH", file=sys.stderr)
        return 2

    if args.reference and not Path(args.reference).is_file():
        print(f"reference not found: {args.reference}", file=sys.stderr)
        return 2

    try:
        tech = probe(args.take)
    except (RuntimeError, ValueError, KeyError, json.JSONDecodeError) as err:
        print(f"could not read {args.take}: {err}", file=sys.stderr)
        return 2

    warnings = []
    keys = keyframes(args.take)
    periodic = is_periodic(keys)
    key_cuts = [] if periodic else [t for t in keys if t > 0]
    scenes = scene_cuts(args.take)
    tech["keyframes"] = keys
    tech["extra_frame"] = bool(tech["fps"]) and tech["frames"] % round(tech["fps"]) == 1
    # Keyframes sit exactly on cuts on the routes measured so far, so prefer them. Scene detection covers the rest.
    cuts = key_cuts if key_cuts else scenes
    source = "keyframes" if key_cuts else "scene detection"

    report = {
        "take": args.take,
        "tech": tech,
        "cuts": cuts,
        "cuts_source": source,
        "scene_cuts": scenes,
        "keyframes_periodic": periodic,
    }

    if key_cuts and len(scenes) != len(key_cuts):
        warnings.append(f"keyframes show {len(key_cuts)} cuts, scene detection {len(scenes)}: look at those frames")
    if tech["has_audio"]:
        warnings.append("clip has an audio track: strip it before the edit unless it is a guide or a layer")

    if args.plan:
        plan = [float(x) for x in args.plan.split(",") if x.strip()]
        rows = compare_plan(plan, cuts, tech["fps"], tech["duration"])
        report["plan"] = rows
        for row in rows:
            if not row["ok"]:
                warnings.append(f"planned cut at {row['planned']} s: nearest measured {row['measured']} "
                                f"({row['offset_frames']} frames off). Write the measured in-point into the edit")
        extra = [c for c in cuts if all(abs(c - p) * tech["fps"] > 12 for p in plan if p > 0)]
        if extra:
            warnings.append(f"cuts nobody planned at {extra}")

    if args.reference:
        shots = ssim_per_shot(args.take, args.reference, tech["width"], tech["height"], cuts, tech["fps"])
        sat = saturation(args.take)
        report["reference"] = {"shots": shots, "saturation": sat}
        if not shots:
            print(f"could not compare {args.take} with {args.reference}", file=sys.stderr)
            return 2
        for shot in shots:
            if shot["ssim_luma"] >= PASS_THROUGH_SSIM:
                warnings.append(f"{shot['start']}-{shot['end']} s: SSIM {shot['ssim_luma']} against the reference. "
                                "The previz may have come back, or the shot is nearly empty. Look at the frames")
        if sat is not None and sat < 4:
            warnings.append(f"mean saturation {sat}: the clip is nearly grey, so the blockout look may have copied")

    if args.cadence:
        report["held_share"] = held_share(args.take, tech["frames"])

    report["warnings"] = warnings

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        extra = " (whole seconds plus one: trim the extra frame)" if tech["extra_frame"] else ""
        print(f"{args.take}: {tech['width']}x{tech['height']} {tech['fps']} fps, {tech['frames']} frames{extra}, "
              f"{tech['duration']} s, {tech['codec']} {tech['pix_fmt']}, {tech['bit_mbps']} Mbps, "
              f"audio {'yes' if tech['has_audio'] else 'no'}")
        print(f"cuts ({source}): {cuts or 'none'}")
        for row in report.get("plan", []):
            print(f"  planned {row['planned']} s, measured {row['measured']}, {row['offset_frames']} frames off")
        if "reference" in report:
            per_shot = ", ".join(f"{s['start']}-{s['end']} s {s['ssim_luma']}" for s in report["reference"]["shots"])
            print(f"against the reference: SSIM {per_shot}; saturation {report['reference']['saturation']}")
        if "held_share" in report:
            print(f"held frames: {report['held_share']}")
        for warning in warnings:
            print(f"WARNING {warning}")
        if not warnings:
            print("no warnings")

    return 1 if warnings else 0


if __name__ == "__main__":
    sys.exit(main())
