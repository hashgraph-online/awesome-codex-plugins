#!/usr/bin/env python3
"""Split a video into shots and make contact sheets an agent can look at. Needs only ffmpeg and ffprobe.

  python3 shots.py reference.mp4 --out breakdown/ [--threshold 0.28] [--min 0.5] [--start 0] [--end 120]

Writes breakdown/shots.json (id, start, end, frames) and breakdown/sheet_NN.jpg. Every row of a sheet is one shot and
its three cells are the first, middle and last frame of that shot, so the camera move reads left to right.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("video")
    a.add_argument("--out", default="breakdown")
    a.add_argument("--threshold", type=float, default=0.28)
    a.add_argument("--min", type=float, default=0.5, help="drop shots shorter than this, in seconds")
    a.add_argument("--start", type=float, default=0)
    a.add_argument("--end", type=float, default=None)
    a.add_argument("--rows", type=int, default=12)
    a = a.parse_args()
    out = Path(a.out)
    (out / "frames").mkdir(parents=True, exist_ok=True)

    dur = float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", a.video]).stdout)
    end = min(a.end or dur, dur)
    cmd = ["ffmpeg", "-hide_banner", "-ss", str(a.start), "-t", str(end - a.start), "-i", a.video,
           "-vf", f"select='gt(scene,{a.threshold})',showinfo", "-an", "-f", "null", "-"]
    cuts = [a.start + float(t) for t in re.findall(r"pts_time:([0-9.]+)", run(cmd).stderr)]
    edges = [a.start] + cuts + [end]
    shots = []
    for s, e in zip(edges, edges[1:]):
        if e - s >= a.min:
            shots.append(dict(id=f"s{len(shots) + 1:03d}", start=round(s, 3), end=round(e, 3), seconds=round(e - s, 3)))

    tiles = []
    for sh in shots:
        pad = min(0.08, sh["seconds"] / 4)
        for i, t in enumerate((sh["start"] + pad, (sh["start"] + sh["end"]) / 2, sh["end"] - pad)):
            f = out / "frames" / f"{sh['id']}_{i}.jpg"
            run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", a.video, "-frames:v", "1",
                 "-vf", "scale=426:-2", str(f)])
            tiles.append(f)
        sh["frames"] = [str(p) for p in tiles[-3:]]

    sheets = []
    per = a.rows * 3
    for n in range(0, len(tiles), per):
        batch = out / f"list_{n // per:02d}.txt"
        batch.write_text("".join(f"file '{p.resolve()}'\nduration 1\n" for p in tiles[n:n + per]))
        name = out / f"sheet_{n // per:02d}.jpg"
        rows = (min(per, len(tiles) - n) + 2) // 3
        run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(batch),
             "-vf", f"tile=3x{rows}:padding=4:color=white", "-frames:v", "1", str(name)])
        batch.unlink()
        sheets.append(dict(file=str(name), shots=[s["id"] for s in shots[n // 3:(n + per) // 3]]))
    (out / "shots.json").write_text(json.dumps(dict(video=a.video, duration=dur, shots=shots, sheets=sheets), indent=1))
    print(f"{len(shots)} shots, {len(sheets)} sheet(s) in {out}/. Each row of a sheet: first, middle, last frame of a shot.")


if __name__ == "__main__":
    main()
