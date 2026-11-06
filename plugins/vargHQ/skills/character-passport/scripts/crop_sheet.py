#!/usr/bin/env python3
"""Cut a 3x2 turnaround or expression sheet into panels, for models that want one clean image per reference.

  python3 crop_sheet.py sheet.png --out panels/ [--cols 3 --rows 2] [--trim 0.01]

Writes r1c1.png ... r2c3.png. On the default turnaround layout: r1c1 = full-body front, r1c2 = side,
r1c3 = back, r2c1 = face front, r2c2 = three-quarter, r2c3 = profile. Video models lock onto the largest
face they see: give them the face close-up (r2c1) and the full-body front (r1c1), not the whole sheet.
Needs Pillow (pip install pillow).
"""
import argparse, pathlib
from PIL import Image
ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("sheet"); ap.add_argument("--out", default="panels"); ap.add_argument("--cols", type=int, default=3)
ap.add_argument("--rows", type=int, default=2); ap.add_argument("--trim", type=float, default=0.01, help="fraction cut off each panel edge (gutters)")
a = ap.parse_args()
im = Image.open(a.sheet).convert("RGB"); W, H = im.size
out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
pw, ph = W / a.cols, H / a.rows
for r in range(a.rows):
    for c in range(a.cols):
        tx, ty = pw * a.trim, ph * a.trim
        box = (int(c * pw + tx), int(r * ph + ty), int((c + 1) * pw - tx), int((r + 1) * ph - ty))
        p = out / f"r{r + 1}c{c + 1}.png"; im.crop(box).save(p); print(p, box)
