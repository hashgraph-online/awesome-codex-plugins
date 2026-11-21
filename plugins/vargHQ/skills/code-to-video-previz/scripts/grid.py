#!/usr/bin/env python3
"""Lay a 10x10 grid over a frame so positions can be read as fractions of the frame. Needs only ffmpeg.

  python3 grid.py frame.jpg --out frame_grid.png [--width 1200] [--step .05] [--crop x0,y0,x1,y1]

Lines every 0.1 of width and height by default. Top-left is (0, 0), bottom-right is (1, 1). The red lines are the centre (0.5).
With --crop, the grid counts in the crop's own fractions: a crop of .4,.5,.7,.8 with --step .1 has lines every .03 and .03 of the frame.
"""
import argparse
import subprocess

a = argparse.ArgumentParser()
a.add_argument("image")
a.add_argument("--out", required=True)
a.add_argument("--width", type=int, default=1200)
a.add_argument("--step", type=float, default=.1)
a.add_argument("--crop", default=None)
a = a.parse_args()
crop = ""
if a.crop:
    x0, y0, x1, y1 = (float(v) for v in a.crop.split(","))
    crop = f"crop=iw*{x1 - x0}:ih*{y1 - y0}:iw*{x0}:ih*{y0},"
vf = (f"{crop}scale={a.width}:-2,format=rgb24,"
      f"drawgrid=w=iw*{a.step}:h=ih*{a.step}:t=1:c=white@0.55,"
      "drawbox=x=iw/2-1:y=0:w=2:h=ih:c=red@0.8:t=fill,drawbox=x=0:y=ih/2-1:w=iw:h=2:c=red@0.8:t=fill")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.image, "-vf", vf, "-frames:v", "1", a.out], check=True)
print(a.out, "grid: 0.1 steps, red = 0.5")
