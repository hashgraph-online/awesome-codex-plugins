#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["opencv-python-headless", "numpy"]
# ///
"""Measure one shot of a reference video: how much the camera pans, tilts, rolls and pushes.

Tracks background features with optical flow and fits a similarity transform frame to frame. Pan and tilt come out in
percent of frame width, at the frame's centre, zoom as total scale change. This is a 2D estimate of the picture, not of the
camera: a pan and a truck look alike, a push-in and a zoom look alike, and on a shot with parallax the zoom is the zoom of
whatever has corners. Use it to read a shot, and to compare a generated clip with its previz. For a camera path on a shot
with parallax, use solve_camera.py. --hfov is the lens's horizontal field of view (35 mm = 54 deg, 25 mm = 72 deg) and only converts
pan and tilt to degrees. The "trust" field counts tracked points. It says nothing about parallax.

  uv run measure_shot.py clip.mp4 --start 79.4 --end 82.1 --hfov 40

The same tool checks your own previz against the reference, and a generated clip against its previz.
"""
import argparse
import json
import math
import subprocess
import tempfile
from pathlib import Path

import cv2
import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--start", type=float, default=0)
    ap.add_argument("--end", type=float, default=None)
    ap.add_argument("--hfov", type=float, default=None, help="assumed horizontal FOV in degrees, adds degrees output")
    ap.add_argument("--out", default=None, help="write JSON here")
    a = ap.parse_args()

    with tempfile.TemporaryDirectory() as d:
        clip = Path(d) / "c.mp4"
        cmd = ["ffmpeg", "-v", "error", "-y", "-ss", str(a.start), "-i", a.video]
        if a.end:
            cmd += ["-t", str(a.end - a.start)]
        cmd += ["-an", "-vf", "scale=640:-2", str(clip)]
        subprocess.run(cmd, check=True)
        cap = cv2.VideoCapture(str(clip))
        fps = cap.get(cv2.CAP_PROP_FPS) or 24
        ok, prev = cap.read()
        if not ok:
            raise SystemExit("no frames")
        h, w = prev.shape[:2]
        pg = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY)
        rows = []
        x = y = roll = 0.0
        s = 1.0
        n = 0
        while True:
            ok, cur = cap.read()
            if not ok:
                break
            n += 1
            cg = cv2.cvtColor(cur, cv2.COLOR_BGR2GRAY)
            p0 = cv2.goodFeaturesToTrack(pg, 400, 0.01, 8)
            step = dict(dx=0.0, dy=0.0, ds=1.0, dr=0.0, inliers=0)
            if p0 is not None and len(p0) >= 12:
                p1, st, _ = cv2.calcOpticalFlowPyrLK(pg, cg, p0, None)
                good = st.flatten() == 1
                if good.sum() >= 12:
                    # RANSAC discards features on moving subjects, keeps the dominant (background) motion
                    M, inl = cv2.estimateAffinePartial2D(p0[good], p1[good], method=cv2.RANSAC,
                                                         ransacReprojThreshold=1.5)
                    if M is not None:
                        ds = math.hypot(M[0, 0], M[1, 0])
                        dr = math.degrees(math.atan2(M[1, 0], M[0, 0]))
                        # Measure how the frame's centre moves. M[0, 2] alone is the top-left corner, which turns any zoom
                        # into false pan and tilt. Background moving right means the camera pans left: flip it.
                        cx = M[0, 0] * w / 2 + M[0, 1] * h / 2 + M[0, 2]
                        cy = M[1, 0] * w / 2 + M[1, 1] * h / 2 + M[1, 2]
                        step = dict(dx=-(cx - w / 2) / w, dy=-(cy - h / 2) / w, ds=ds, dr=dr, inliers=int(inl.sum()))
            x += step["dx"]
            y += step["dy"]
            s *= step["ds"]
            roll += step["dr"]
            rows.append(dict(t=round(n / fps, 3), x=round(x * 100, 3), y=round(y * 100, 3),
                             zoom=round(s, 4), roll=round(roll, 3), inliers=step["inliers"]))
            pg = cg

    dur = n / fps if n else 0
    # easing: how much of the move happens in the first and last third
    speed = np.array([math.hypot(rows[i]["x"] - (rows[i - 1]["x"] if i else 0),
                                 rows[i]["y"] - (rows[i - 1]["y"] if i else 0))
                      + abs(rows[i]["zoom"] - (rows[i - 1]["zoom"] if i else 1)) * 100 for i in range(len(rows))])
    t3 = max(1, len(speed) // 3)
    total = float(speed.sum()) or 1e-9
    res = dict(
        duration_s=round(dur, 2), fps=fps,
        pan_pct_of_width=rows[-1]["x"], tilt_pct_of_width=rows[-1]["y"],
        zoom_factor=rows[-1]["zoom"], roll_deg=rows[-1]["roll"],
        share_of_move=dict(first_third=round(float(speed[:t3].sum()) / total, 2),
                           middle=round(float(speed[t3:-t3].sum()) / total, 2),
                           last_third=round(float(speed[-t3:].sum()) / total, 2)),
        median_inliers=int(np.median([r["inliers"] for r in rows])),
    )
    if a.hfov:
        res["pan_deg"] = round(rows[-1]["x"] / 100 * a.hfov, 2)
        res["tilt_deg"] = round(rows[-1]["y"] / 100 * a.hfov, 2)
    mag = abs(res["pan_pct_of_width"]) + abs(res["tilt_pct_of_width"]) + abs(res["zoom_factor"] - 1) * 100
    if mag < 1.5:
        verb = "locked off (or tiny drift)"
    else:
        parts = []
        if abs(res["pan_pct_of_width"]) > 1.5:
            parts.append(("pan/truck right" if res["pan_pct_of_width"] > 0 else "pan/truck left"))
        if abs(res["tilt_pct_of_width"]) > 1.5:
            parts.append(("tilt/crane down" if res["tilt_pct_of_width"] > 0 else "tilt/crane up"))
        if abs(res["zoom_factor"] - 1) > 0.015:
            parts.append(("push in / zoom in" if res["zoom_factor"] > 1 else "pull out / zoom out"))
        verb = " + ".join(parts) or "small drift"
    sm = res["share_of_move"]
    ease = "even" if max(sm.values()) < 0.45 else ("slow start" if sm["last_third"] >= 0.45 else
                                                   "slow end" if sm["first_third"] >= 0.45 else "eased in and out")
    res["reads_as"], res["ease"] = verb, ease
    res["trust"] = "good" if res["median_inliers"] >= 30 else "weak: few background features, check by eye"
    print(json.dumps(res, indent=1))
    if a.out:
        Path(a.out).write_text(json.dumps(dict(summary=res, per_frame=rows), indent=1))


if __name__ == "__main__":
    main()
