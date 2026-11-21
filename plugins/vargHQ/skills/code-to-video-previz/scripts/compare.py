#!/usr/bin/env python3
"""Put a render next to its reference and on top of it. Needs only ffmpeg.

  python3 compare.py reference.jpg render.png --out cmp          still: cmp_side.jpg + cmp_overlay.jpg
  python3 compare.py reference.mp4 previz.mp4 --out cmp --video [--start 74.08 --end 79.38]   clip: cmp_side.mp4 + cmp_overlay.mp4
       --start and --end pick the shot out of a longer reference. The render always starts at its first frame.

Look at the overlay first: shapes that line up mean the camera and the staging match. The side view is for judging.
"""
import argparse
import subprocess

a = argparse.ArgumentParser()
a.add_argument("reference")
a.add_argument("render")
a.add_argument("--out", required=True)
a.add_argument("--video", action="store_true")
a.add_argument("--start", type=float, default=None)
a.add_argument("--end", type=float, default=None)
a = a.parse_args()
probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                        "-of", "csv=p=0", a.reference], capture_output=True, text=True, check=True).stdout
w, h = probe.strip().split(",")[:2]
base = f"[0:v]format=rgb24,setsar=1[a];[1:v]scale={w}:{h},format=rgb24,setsar=1[b];"
ext = "mp4" if a.video else "jpg"
tail = ["-an", "-pix_fmt", "yuv420p", "-crf", "20"] if a.video else ["-frames:v", "1", "-q:v", "3"]
for name, chain in (("side", "[a][b]hstack=inputs=2"), ("overlay", "[a][b]blend=all_mode=average")):
    # yuv420p needs even dimensions
    f = base + chain + ",scale=trunc(iw/2)*2:trunc(ih/2)*2,format=rgb24"
    win = ([] if a.start is None else ["-ss", str(a.start)]) + ([] if a.end is None else ["-to", str(a.end)])
    subprocess.run(["ffmpeg", "-v", "error", "-y", *win, "-i", a.reference, "-i", a.render, "-filter_complex", f + ",setpts=N/FRAME_RATE/TB" if a.video else f, *tail, "-shortest",
                    f"{a.out}_{name}.{ext}"], check=True)
    print(f"{a.out}_{name}.{ext}")
