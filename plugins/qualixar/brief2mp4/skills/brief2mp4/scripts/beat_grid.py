#!/usr/bin/env python3
"""beat_grid.py: find the beats, downbeats and onsets of a music file, and snap video cuts to them.

  python3 beat_grid.py analyze music.wav --out grid.json [--beats-per-bar 4] [--tolerance 0.04]
  python3 beat_grid.py snap grid.json --times 1.2,3.4,5.9 [--to beats|downbeats|onsets] [--max-shift 0.12] [--fps 30]
  python3 beat_grid.py snap grid.json --times 1.2,3.4 --emit js        # a ready-to-paste snippet for a HyperFrames timeline

analyze needs librosa (optional: python3 -m pip install --user librosa). Without it, the command prints the
install line and a SKIP and exits 3 (nothing was made: never read as success, never a failure either). snap needs nothing.

How the grid is built, and why:
  1. librosa tracks the beats. A tempo estimate alone drifts, so the beats are then fitted with a straight
     line, t = t0 + i * period (least squares). A good fit has a residual under about 15 ms.
  2. The tracker can lock onto half or double speed. Three candidates (half, same, double) are scored by how
     well their grid points match the detected onsets (F1 within --tolerance); the best wins.
  3. Downbeats (the first beat of each bar) are estimated: of the --beats-per-bar possible phases, the one whose
     beats carry the most onset energy. librosa has no downbeat tracker, so treat these as a good first guess.
  4. The output keeps times as float seconds. Convert to frames only at the end (snap --fps does that last step).
A song whose tempo changes needs one grid per section: cut the file at the change and analyze each part.

The JSON has: file, duration, bpm, period, t0, residual_ms, factor, beats (the fitted grid across the whole file),
beats_detected (raw), downbeats, onsets, beats_per_bar.
"""
import argparse
import json
import math
import statistics
import sys

INSTALL = "python3 -m pip install --user librosa"
HOP = 256  # analysis hop in samples at 22050 Hz: about 11.6 ms per frame


def fit_grid(beats):
    """Least-squares line through beat times: returns (t0, period, residual_ms). Needs at least 3 beats."""
    if len(beats) < 3:
        raise ValueError("fewer than 3 beats found: the file may be silent, too short or have no steady pulse")
    gaps = sorted(b - a for a, b in zip(beats, beats[1:]))
    approx = statistics.median(gaps)
    idx = [round((b - beats[0]) / approx) for b in beats]
    n = len(beats)
    mi, mt = sum(idx) / n, sum(beats) / n
    var = sum((i - mi) ** 2 for i in idx)
    if var == 0:
        raise ValueError("the beats do not advance: cannot fit a grid")
    period = sum((i - mi) * (t - mt) for i, t in zip(idx, beats)) / var
    t0 = mt - period * mi
    resid = [t - (t0 + period * i) for i, t in zip(idx, beats)]
    rms = (sum(r * r for r in resid) / n) ** 0.5
    return t0, period, rms * 1000.0


def grid_points(t0, period, duration):
    """Every t0 + i * period inside [0, duration], including the beats before the first one the tracker found."""
    out, i = [], math.ceil(-t0 / period - 1e-9)
    while t0 + i * period <= duration:
        out.append(t0 + i * period)
        i += 1
    return out


def near(times, targets, tol):
    """How many of `times` have a target within tol seconds (both lists sorted)."""
    hits, j = 0, 0
    for t in times:
        while j + 1 < len(targets) and abs(targets[j + 1] - t) <= abs(targets[j] - t):
            j += 1
        if targets and abs(targets[j] - t) <= tol:
            hits += 1
    return hits


def f1(grid, onsets, tol):
    if not grid or not onsets:
        return 0.0
    precision = near(grid, onsets, tol) / len(grid)
    recall = near(onsets, grid, tol) / len(onsets)
    return 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)


def pick_speed(t0, period, duration, onsets, tol):
    """Score half, same and double speed by how well the grid lines up with the onsets. Returns (factor, scores)."""
    scores = {}
    for factor in (0.5, 1.0, 2.0):
        scores[factor] = f1(grid_points(t0, period / factor, duration), onsets, tol)
    best = max(scores, key=lambda f: (round(scores[f], 3), f == 1.0))
    return best, scores


def downbeat_phase(beats, onset_strength_at, per_bar):
    energy = [0.0] * per_bar
    for i, b in enumerate(beats):
        energy[i % per_bar] += onset_strength_at(b)
    return max(range(per_bar), key=lambda p: energy[p])


def window_max(env, centre, radius):
    """Largest onset strength within +/- radius frames: a beat time is only good to about one hop."""
    lo, hi = max(0, centre - radius), min(len(env), centre + radius + 1)
    return float(max(env[lo:hi])) if hi > lo else 0.0


def analyze(path, per_bar, tol):
    try:
        import librosa
    except ImportError:
        print("SKIP  beat_grid: librosa is not installed, so no beat grid was made.")
        print(f"      Install it: {INSTALL}   (needs Python 3.9 or newer; the first import takes a few seconds)")
        return 3
    y, sr = librosa.load(path, sr=22050, mono=True)
    duration = len(y) / sr
    hop = HOP
    env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    _, frames = librosa.beat.beat_track(onset_envelope=env, sr=sr, hop_length=hop, units="frames")
    detected = [float(t) for t in librosa.frames_to_time(frames, sr=sr, hop_length=hop)]
    onsets = [float(t) for t in librosa.onset.onset_detect(onset_envelope=env, sr=sr, hop_length=hop, units="time")]
    try:
        t0, period, resid = fit_grid(detected)
    except ValueError as err:
        print(f"FAIL  beat_grid: {err}")
        return 1
    factor, scores = pick_speed(t0, period, duration, onsets, tol)
    period /= factor
    grid = grid_points(t0, period, duration)
    strength = lambda t: window_max(env, int(round(t * sr / hop)), 3)
    phase = downbeat_phase(grid, strength, per_bar)
    result = {"file": str(path), "duration": round(duration, 4), "bpm": round(60.0 / period, 2), "period": round(period, 5),
              "t0": round(grid[0] if grid else t0, 5),
              "residual_ms": round(resid, 2), "factor": factor, "beats_per_bar": per_bar,
              "beats": [round(t, 4) for t in grid], "beats_detected": [round(t, 4) for t in detected],
              "downbeats": [round(t, 4) for t in grid[phase::per_bar]], "onsets": [round(t, 4) for t in onsets]}
    return result


def nearest(grid, t):
    return min(grid, key=lambda g: abs(g - t)) if grid else t


def snap(times, grid, max_shift, fps=None):
    """Move each time to the nearest grid point if it is within max_shift seconds. Frames are the last step."""
    out = []
    for t in times:
        g = nearest(grid, t)
        moved = abs(g - t) <= max_shift
        final = g if moved else t
        if fps:
            final = round(final * fps) / fps
        out.append({"in": round(t, 4), "out": round(final, 4), "shift_ms": round((final - t) * 1000, 1), "snapped": moved})
    return out


JS = """// from beat_grid.py: seconds on the beat grid. Use inside a HyperFrames timeline: tl.to(el, {...}, snap(1.2))
const GRID = %s;
const snap = (t, maxShift = %s) => {
  let best = GRID[0];
  for (const g of GRID) if (Math.abs(g - t) < Math.abs(best - t)) best = g;
  return Math.abs(best - t) <= maxShift ? best : t;
};
"""


def cmd_snap(args):
    data = json.load(open(args.grid, encoding="utf-8"))
    grid = data.get(args.to)
    if not grid:
        print(f"FAIL  beat_grid: {args.grid} has no '{args.to}' list", file=sys.stderr)
        return 1
    if args.emit == "js":
        print(JS % (json.dumps(grid), args.max_shift), end="")
        if args.times:
            print("// snapped: " + json.dumps([r["out"] for r in snap([float(t) for t in args.times.split(",")], grid, args.max_shift, args.fps)]))
        return 0
    if not args.times:
        print("FAIL  beat_grid: snap needs --times (or --emit js)", file=sys.stderr)
        return 1
    print(json.dumps(snap([float(t) for t in args.times.split(",")], grid, args.max_shift, args.fps), indent=1))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyze", help="music file to a grid JSON")
    a.add_argument("audio")
    a.add_argument("--out", help="write the JSON here (default: print it)")
    a.add_argument("--beats-per-bar", type=int, default=4)
    a.add_argument("--tolerance", type=float, default=0.04, help="seconds within which an onset matches a grid point")
    s = sub.add_parser("snap", help="move times onto the grid")
    s.add_argument("grid")
    s.add_argument("--times", help="comma-separated seconds")
    s.add_argument("--to", default="beats", choices=["beats", "downbeats", "onsets"])
    s.add_argument("--max-shift", type=float, default=0.12, help="never move a time further than this many seconds")
    s.add_argument("--fps", type=float, help="round the result to whole frames (the last step)")
    s.add_argument("--emit", choices=["json", "js"], default="json")
    args = ap.parse_args()
    if args.cmd == "snap":
        return cmd_snap(args)
    result = analyze(args.audio, args.beats_per_bar, args.tolerance)
    if isinstance(result, int):
        return result
    text = json.dumps(result)
    if args.out:
        open(args.out, "w", encoding="utf-8").write(text)
        print(f"PASS  beat grid: {result['bpm']} BPM, fit residual {result['residual_ms']} ms, "
              f"{len(result['beats'])} beats, {len(result['downbeats'])} downbeats, {len(result['onsets'])} onsets -> {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
