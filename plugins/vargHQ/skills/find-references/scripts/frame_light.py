#!/usr/bin/env python3
"""Measure the light in a still or a video frame from its pixels.

Use it to check a reading before you trust it, and to compare a test take against its reference.

  python3 frame_light.py a.jpg [b.jpg ...]
  python3 frame_light.py --at 12.5 clip.mp4             one frame of a video, at 12.5 s
  python3 frame_light.py --crop 200:150:40:300 a.jpg    one region, W:H:X:Y in source pixels
  python3 frame_light.py --compare reference.jpg take.jpg

Prints one JSON object per file:

  left_mid_right, top_mid_bottom   mean linear luminance of each third of the frame
  bright_side, lr_ratio            brighter of the left and right thirds, and how much brighter. "even" under 1.1
  contrast_stops                   log2(p95 / p5) of luminance
  p5, p50, p95, clip_high_pct      luminance percentiles (0 to 1), and % of pixels at luminance 0.98 or above
  pct_below_half_grey              % of pixels under 0.09, half of 18% grey
  highlight_k, shadow_k            apparent colour (McCamy) of the top 5% of pixels, and of the p5 to p25 band
  source_size                      source pixels, null without ffprobe

--compare adds the round-trip check: same bright side, contrast within 1 stop, highlight colour within 500 K. That
tolerance is our proposal and has not been validated. Exit code 1 means the take is outside it.

What this cannot tell you. It measures the frame as graded, and reflectance as well as light: a white wall reads
bright. So lr_ratio is not a key-to-fill ratio, and the K values are not the Kelvin of a lamp. Two crops on the same
material (skin and skin, one wall) remove most of the reflectance question; take log2 of their p50 values for stops.

Every frame is scaled to 320x240 first, so clip_high_pct undercounts small highlights. It measures whatever is in the
frame, film borders and sprocket holes too: crop them out with --crop, or every percentile moves.

Needs ffmpeg on PATH. Standard library only.
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys

W, H = 320, 240
EVEN_BELOW = 1.1
TOLERANCE = "our proposal, not validated: same bright side, within 1 stop, within 500 K"


def to_linear(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


LINEAR = [to_linear(c) for c in range(256)]


def mccamy(r, g, b):
    """Apparent colour temperature of a linear sRGB colour, or None for black and out-of-range colours."""
    x_, y_, z_ = (0.4124 * r + 0.3576 * g + 0.1805 * b, 0.2126 * r + 0.7152 * g + 0.0722 * b,
                  0.0193 * r + 0.1192 * g + 0.9505 * b)
    total = x_ + y_ + z_
    if total <= 0 or y_ / total == 0.1858:
        return None
    n = (x_ / total - 0.3320) / (0.1858 - y_ / total)
    return round(449 * n ** 3 + 3525 * n ** 2 + 6823.3 * n + 5520.33)


def grab(path, at, crop):
    """Decode one frame to raw RGB through ffmpeg, scaled to W x H."""
    vf = f"scale={W}:{H}"
    if crop:
        vf = f"crop={crop}," + vf
    cmd = ["ffmpeg", "-nostdin", "-v", "error"]
    if at is not None:
        cmd += ["-ss", str(at)]
    cmd += ["-i", path, "-frames:v", "1", "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    out = subprocess.run(cmd, capture_output=True)
    if out.returncode or len(out.stdout) != W * H * 3:
        sys.exit(f"{path}: ffmpeg could not read one frame. {out.stderr.decode(errors='replace').strip()}")
    return out.stdout


def source_size(path):
    if not shutil.which("ffprobe"):
        return None
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                          "-of", "csv=p=0:s=x", path], capture_output=True, text=True)
    return out.stdout.strip().split("\n")[0] or None


def thirds(values):
    a, b = len(values) // 3, 2 * len(values) // 3
    parts = values[:a], values[a:b], values[b:]
    return [sum(p) / len(p) for p in parts]


def band_mean(pixels):
    count = len(pixels)
    return [sum(p[i] for p in pixels) / count for i in (1, 2, 3)]


def measure(path, at=None, crop=None):
    raw = grab(path, at, crop)
    n = W * H
    cols, rows, pixels = [0.0] * W, [0.0] * H, []
    for i in range(n):
        r, g, b = LINEAR[raw[3 * i]], LINEAR[raw[3 * i + 1]], LINEAR[raw[3 * i + 2]]
        y = 0.2126 * r + 0.7152 * g + 0.0722 * b
        cols[i % W] += y / H
        rows[i // W] += y / W
        pixels.append((y, r, g, b))
    pixels.sort(key=lambda p: p[0])
    lum = [p[0] for p in pixels]

    def pct(q):
        return lum[int(n * q)]

    left, mid, right = thirds(cols)
    ratio = max(left, right) / max(min(left, right), 1e-6)
    below = next((i for i, v in enumerate(lum) if v > 0.09), n)
    return {
        "file": os.path.basename(path),
        "left_mid_right": [round(left, 3), round(mid, 3), round(right, 3)],
        "top_mid_bottom": [round(v, 3) for v in thirds(rows)],
        "bright_side": "even" if ratio < EVEN_BELOW else ("left" if left > right else "right"),
        "lr_ratio": round(ratio, 2),
        "contrast_stops": round(math.log2(pct(0.95) / max(pct(0.05), 1e-4)), 1),
        "p5": round(pct(0.05), 3),
        "p50": round(pct(0.5), 3),
        "p95": round(pct(0.95), 3),
        "clip_high_pct": round(100 * sum(v >= 0.98 for v in lum) / n, 1),
        "pct_below_half_grey": round(100 * below / n),
        "highlight_k": mccamy(*band_mean(pixels[int(n * 0.95):])),
        "shadow_k": mccamy(*band_mean(pixels[int(n * 0.05):int(n * 0.25)])),
        "source_size": source_size(path),
    }


def compare(ref, take):
    side = ref["bright_side"] == take["bright_side"]
    stops = round(take["contrast_stops"] - ref["contrast_stops"], 1)
    both_k = ref["highlight_k"] is not None and take["highlight_k"] is not None
    kelvin = take["highlight_k"] - ref["highlight_k"] if both_k else None
    return {
        "same_bright_side": side,
        "contrast_delta_stops": stops,
        "highlight_delta_k": kelvin,
        "within_tolerance": side and abs(stops) <= 1 and kelvin is not None and abs(kelvin) <= 500,
        "tolerance": TOLERANCE,
    }


def main():
    parser = argparse.ArgumentParser(description="Measure the light of a still or video frame. Needs ffmpeg.")
    parser.add_argument("files", nargs="+")
    parser.add_argument("--at", type=float, help="seconds into a video")
    parser.add_argument("--crop", help="region to measure, W:H:X:Y in source pixels")
    parser.add_argument("--compare", action="store_true", help="exactly two files: reference, then take")
    args = parser.parse_args()
    if args.compare and len(args.files) != 2:
        parser.error("--compare takes exactly two files: reference, then take")
    results = [measure(f, args.at, args.crop) for f in args.files]
    for result in results:
        print(json.dumps(result, ensure_ascii=False))
    if args.compare:
        verdict = compare(*results)
        print(json.dumps(verdict, ensure_ascii=False))
        sys.exit(0 if verdict["within_tolerance"] else 1)


if __name__ == "__main__":
    main()
