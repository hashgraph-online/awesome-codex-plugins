#!/usr/bin/env python3
"""Turn solve_camera.py's result into a camera path for staging.json. Standard library only.

  python3 solved_to_staging.py solved.json --horizon-v .35 --height 1.7 --scale 1 --keys 7 --start 0 --out path.json

A solve has no gravity and no scale, so you supply them from what you can see:
  --horizon-v  where the horizon sits in the first frame, as a fraction from the top. .5 means the camera starts level.
               A horizon above the middle (v below .5) means the camera looks down. Assumes no roll on the first frame.
  --scale      metres per solve unit. Read two points of known distance from path.json's "points", or set --travel-m if you
               know how far the camera moved. Angles don't depend on it.
  --height     camera height on the first frame, in metres.

World: x right, y into the picture, z up, first camera at x = y = 0. Prints what the camera did, and writes path.json with a "shot"
to paste into staging.json and "points", the tracked features in the same world, so you can put sets where the film has things.
"""
import argparse
import json
import math
from pathlib import Path


def add(a, b): return [x + y for x, y in zip(a, b)]
def sub(a, b): return [x - y for x, y in zip(a, b)]
def mul(a, k): return [x * k for x in a]
def dot(a, b): return sum(x * y for x, y in zip(a, b))
def cross(a, b): return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
def norm(a): return math.sqrt(dot(a, a))
def unit(a): n = norm(a) or 1e-9; return [x / n for x in a]


ap = argparse.ArgumentParser()
ap.add_argument("solved")
ap.add_argument("--out", default="path.json")
ap.add_argument("--horizon-v", type=float, default=.5)
ap.add_argument("--height", type=float, default=1.6)
ap.add_argument("--scale", type=float, default=None)
ap.add_argument("--travel-m", type=float, default=None, help="how far the camera really moved; sets the scale")
ap.add_argument("--keys", type=int, default=7)
ap.add_argument("--start", type=float, default=0, help="where the shot starts on your timeline, seconds")
ap.add_argument("--id", default="s01")
a = ap.parse_args()

S = json.loads(Path(a.solved).read_text())
W, H = S["size"]
fpx = S["focal"] / 36 * max(W, H)
fps = S.get("fps") or 24
cams = sorted(S["cameras"], key=lambda c: c["frame"])
col = lambda m, i: [m[0][i], m[1][i], m[2][i]]
R0 = cams[0]["matrix"]
r0, u0, f0 = col(R0, 0), col(R0, 1), mul(col(R0, 2), -1)
P0 = col(R0, 3)
d = add(f0, mul(u0, (.5 - a.horizon_v) * H / fpx))       # the horizon's direction on frame 1 is horizontal
Z = unit(cross(r0, unit(d)))
X = unit(sub(r0, mul(Z, dot(r0, Z))))
Y = cross(Z, X)
base = lambda v: [dot(v, X), dot(v, Y), dot(v, Z)]
path = [sub(col(c["matrix"], 3), P0) for c in cams]
raw_travel = sum(norm(sub(p, q)) for p, q in zip(path[1:], path))
scale = a.scale or (a.travel_m / raw_travel if a.travel_m else 1.0)
if not a.scale and not a.travel_m:
    print("No scale given, so distances are in solve units, not metres. Angles are right.")


def state(c):
    m = c["matrix"]
    p = base(mul(sub(col(m, 3), P0), scale))
    p[2] += a.height
    f, r = unit(base(mul(col(m, 2), -1))), unit(base(col(m, 0)))
    hr = unit(cross(f, [0, 0, 1]))
    hu = cross(hr, f)
    roll = math.degrees(math.atan2(dot(r, hu), dot(r, hr)))
    heading = math.degrees(math.atan2(f[0], f[1]))
    pitch = math.degrees(math.asin(max(-1, min(1, f[2]))))
    return dict(p=p, f=f, roll=roll, heading=heading, pitch=pitch, frame=c["frame"])


st = [state(c) for c in cams]
idx = sorted({round(i * (len(st) - 1) / max(a.keys - 1, 1)) for i in range(a.keys)})
LOOK = 10.0
keys = [dict(t=round((st[i]["frame"] - st[0]["frame"]) / fps, 4),
             pos=[round(x, 4) for x in st[i]["p"]],
             look=[round(x, 4) for x in add(st[i]["p"], mul(st[i]["f"], LOOK))],
             roll=round(st[i]["roll"], 3)) for i in idx]
end = a.start + len(cams) / fps
shot = dict(id=a.id, start=round(a.start, 4), end=round(end, 4), lens=round(S["focal"], 2), ease="linear", keys=keys, subjects=[])
pts = []
for b in S.get("points", []):
    q = base(mul(sub(b["co"], P0), scale))
    q[2] += a.height
    pts.append(dict(name=b["name"], at=[round(x, 3) for x in q], error=round(b["error"], 2)))
Path(a.out).write_text(json.dumps(dict(shot=shot, points=pts, solve_error_px=S["error"], scale=scale), indent=1))

trav = [norm(sub(p["p"], q["p"])) for p, q in zip(st[1:], st)]
total = sum(trav)
thirds = [round(sum(trav[i * len(trav) // 3:(i + 1) * len(trav) // 3]) / (total or 1), 3) for i in range(3)]
span = sub(st[-1]["p"], st[0]["p"])
print(json.dumps(dict(
    lens_mm=round(S["focal"], 1), seconds=round(len(cams) / fps, 2),
    travel_m=round(total, 3), right_m=round(span[0], 3), forward_m=round(span[1], 3), up_m=round(span[2], 3),
    speed_share_by_third=thirds,
    pan_deg=round(st[-1]["heading"] - st[0]["heading"], 2), pitch_deg=[round(st[0]["pitch"], 2), round(st[-1]["pitch"], 2)],
    roll_deg=[round(st[0]["roll"], 2), round(st[-1]["roll"], 2)],
    height_m=[round(st[0]["p"][2], 3), round(st[-1]["p"][2], 3)],
    error_px=round(S["error"], 3), points=len(pts), out=a.out), indent=1))
print("A positive pan_deg turns the camera right. Paste path.json's \"shot\" into staging.json and add \"subjects\".")
