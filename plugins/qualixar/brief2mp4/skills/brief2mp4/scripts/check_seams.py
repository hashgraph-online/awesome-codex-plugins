#!/usr/bin/env python3
"""check_seams.py: find one-frame pops, flicker, bad joins and true freezes in a finished video.

Uses only the Python standard library plus ffmpeg and ffprobe. Every frame is decoded once as a
96x54 grey copy, so a minute of 30 fps video takes a few seconds.

  python3 check_seams.py final.mp4
  python3 check_seams.py final.mp4 --joins 12.0,24.5      # the times where separately rendered acts were joined
  python3 check_seams.py final.mp4 --freeze-seconds 2 --flicker-min 10
  python3 check_seams.py final.mp4 --flash-ok 16,32,48 --strict   # planned flashes pass, any other flicker fails

What it measures, and why each rule is built the way it is:

  Flicker (WARN, or FAIL with --strict). A frame, or up to 3 frames in a row, that differs sharply
    from the frame before AND from the frame after, while the frames on either side match each other.
    That is a flash, a missing frame or a wrong layer for a moment. Some looks flicker on purpose
    (a flash on the downbeat, silent-film or VHS flicker), so list planned flashes with --flash-ok
    and they are reported as INFO; --strict makes every unlisted flicker a FAIL.
  Joins (FAIL or WARN). For each time in --joins, the SSIM between the last frame of one segment
    and the first frame of the next. Under 0.99 means the pictures do not match across the join.
    On moving pictures SSIM is low everywhere, so the jump is also compared with the frame-to-frame
    change around the join: 3x bigger is a FAIL, 2x a WARN, anything smaller is a join that
    moves like its neighbours and passes.
  Hard cuts and soft changes (information). A change is a hard cut only when two signals agree:
    ffmpeg's scdet score is at least 6 AND the frame difference is at least 2x the average of the
    3 frames before and after. scdet alone calls a fast pan a cut and misses a cut made mid-pan.
  Freeze (WARN). A stretch is frozen only when every frame matches the previous one AND the last
    frame still matches the first of the stretch. The second test is what stops a slow pan or
    push-in over a detailed picture from being flagged: its frames differ by a hair, but they drift.
    Over a low-texture plate (flat grey, faint grid) a slow push-in can drift too little to see at 96x54.

Prints one PASS / WARN / FAIL line per check (plus INFO lines). Exit 1 if anything FAILs. A check that could not
measure never passes: a file ffprobe cannot read, a decode error, fewer frames decoded than the file says it holds,
or fewer than 4 frames are each a FAIL line (exit 1). Frames are read at the file's average frame rate (constant
frame rate), so the times of a variable-frame-rate recording line up with --joins.
"""
import argparse
import statistics
import subprocess
import sys
import tempfile
from collections import deque
from operator import sub

W, H = 96, 54
BLOCK = 6          # SSIM block size: 96x54 splits into 16x9 blocks of 6x6
SCDET_MIN = 6.0    # ffmpeg scdet score for a possible scene change
CUT_RATIO = 2.0    # a hard cut must also be this many times the frames around it
FREEZE_EPS = 0.25  # mean grey difference (0-255) below which two frames count as identical
DRIFT_EPS = 0.6    # ... and the last frame of a freeze may not drift further than this from the first


def mad(a, b):
    """Mean absolute difference between two grey frames, 0-255."""
    return sum(map(abs, map(sub, a, b))) / len(a)


def ssim(a, b):
    """Mean SSIM over 6x6 blocks of two grey frames (1.0 = identical)."""
    c1, c2, n = (0.01 * 255) ** 2, (0.03 * 255) ** 2, BLOCK * BLOCK
    total, blocks = 0.0, 0
    for by in range(0, H - BLOCK + 1, BLOCK):
        for bx in range(0, W - BLOCK + 1, BLOCK):
            xs = [a[(by + y) * W + bx:(by + y) * W + bx + BLOCK] for y in range(BLOCK)]
            ys = [b[(by + y) * W + bx:(by + y) * W + bx + BLOCK] for y in range(BLOCK)]
            x = [v for row in xs for v in row]
            y = [v for row in ys for v in row]
            mx, my = sum(x) / n, sum(y) / n
            vx = sum((v - mx) ** 2 for v in x) / n
            vy = sum((v - my) ** 2 for v in y) / n
            cov = sum((p - mx) * (q - my) for p, q in zip(x, y)) / n
            total += ((2 * mx * my + c1) * (2 * cov + c2)) / ((mx * mx + my * my + c1) * (vx + vy + c2))
            blocks += 1
    return total / blocks


class Unmeasured(Exception):
    """The video could not be measured: reported as a FAIL line, never as a pass."""


def probe(path):
    """(fps as float, fps as ffmpeg's rational text, expected frame count or None) from ffprobe.

    The expected count is the stream's duration times its average rate, which is what the constant-rate decode yields."""
    proc = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                           "stream=avg_frame_rate,nb_frames,duration:format=duration", "-of", "default=nw=1", path],
                          capture_output=True, text=True)
    info = {}
    for line in proc.stdout.splitlines():
        key, _, val = line.partition("=")
        info.setdefault(key.strip(), val.strip())     # the stream's duration comes before the container's
    num, _, den = info.get("avg_frame_rate", "").partition("/")
    try:
        fps = float(num) / float(den or 1)
    except (ValueError, ZeroDivisionError):
        fps = 0.0
    if proc.returncode != 0 or fps <= 0:
        raise Unmeasured(f"ffprobe cannot read the frame rate of {path}" + (f": {' '.join(proc.stderr.split())[:200]}" if proc.stderr.strip() else ""))
    try:
        expected = round(float(info.get("duration", "")) * fps)
    except ValueError:
        expected = int(info["nb_frames"]) if info.get("nb_frames", "").isdigit() else None
    rate = info["avg_frame_rate"]
    return fps, rate, expected


class FrameReader:
    """Iterate a video as W*H grey frames at a constant rate; afterwards .returncode and .errors say how decoding went."""

    def __init__(self, path, rate):
        self.path, self.rate, self.returncode, self.errors, self.count = path, rate, None, "", 0

    def __iter__(self):
        cmd = ["ffmpeg", "-v", "error", "-i", self.path, "-an", "-vf",
               f"fps={self.rate},scale={W}:{H}:flags=area,format=gray", "-f", "rawvideo", "-"]
        size = W * H
        with tempfile.TemporaryFile() as err:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=err)
            try:
                while True:
                    buf = proc.stdout.read(size)
                    if len(buf) < size:
                        break
                    self.count += 1
                    yield buf
            finally:
                proc.stdout.close()
                self.returncode = proc.wait()
                err.seek(0)
                self.errors = err.read().decode("utf-8", "replace").strip()


def scdet_events(path, fps):
    """Frame index -> scdet score for every frame ffmpeg scores at or above SCDET_MIN. {} if scdet is missing."""
    proc = subprocess.run(["ffmpeg", "-nostats", "-hide_banner", "-i", path, "-an", "-vf", f"scdet=t={SCDET_MIN}",
                           "-f", "null", "-"], capture_output=True, text=True)
    events = {}
    for line in proc.stderr.splitlines():
        if "lavfi.scd.score" not in line:
            continue
        try:
            score = float(line.split("lavfi.scd.score:")[1].split(",")[0])
            when = float(line.split("lavfi.scd.time:")[1].strip())
        except (IndexError, ValueError):
            continue
        events[round(when * fps)] = score
    return events


def scan(reader, joins, flicker_min):
    """One pass: per-frame differences, flicker spans, freeze spans (in frames) and the SSIM at each join frame."""
    diffs, flickers, join_ssim, freeze = [0.0], [], {}, FreezeTracker()
    ring = deque(maxlen=6)           # the last frames, newest at the right
    join_set = set(joins)
    count = 0
    for idx, fr in enumerate(reader):
        count = idx + 1
        if ring:
            diffs.append(mad(ring[-1], fr))
            if idx in join_set:
                join_ssim[idx] = ssim(ring[-1], fr)
            flickers.extend(flicker_ending_at(idx, fr, ring, diffs, flicker_min))
            freeze.feed(idx, ring[-1], fr)
        ring.append(fr)
    return diffs, flickers, join_ssim, freeze.finish(count)


def flicker_ending_at(idx, fr, ring, diffs, floor):
    """Spans of 1-3 odd frames that end just before frame idx (frame idx is the first normal one again)."""
    found = []
    base = statistics.median(diffs[max(0, idx - 24):idx - 1] or [0.0])
    thr = max(floor, 4.0 * base)
    for length in (1, 2, 3):
        if len(ring) < length + 1 or idx - length < 1:
            continue
        before = ring[-(length + 1)]
        d_in, d_out = diffs[idx - length], diffs[idx]
        if d_in >= thr and d_out >= thr and mad(before, fr) <= 0.35 * min(d_in, d_out):
            found.append((idx - length, length, min(d_in, d_out)))
            break
    return found


def neighbours(diffs, idx, span=3):
    near = [diffs[k] for k in range(idx - span, idx + span + 1) if k != idx and 0 < k < len(diffs)]
    return sum(near) / len(near) if near else 0.0


def classify_changes(diffs, events, skip):
    """Split scdet events into hard cuts (two signals agree) and soft changes (one signal only)."""
    hard, soft = [], []
    for idx in sorted(events):
        hit = next((k for k in (idx, idx - 1, idx + 1) if 0 < k < len(diffs)), None)
        if hit is None or idx in skip or (idx - 1) in skip:
            continue
        if diffs[hit] >= CUT_RATIO * neighbours(diffs, hit) and diffs[hit] > 1.0:
            hard.append(hit)
        else:
            soft.append(hit)
    return hard, soft


class FreezeTracker:
    """Streaming freeze finder: a span is frozen while every frame matches the previous AND the first of the span."""

    def __init__(self):
        self.spans, self.start, self.anchor = [], None, None

    def feed(self, idx, prev, fr):
        ok = mad(prev, fr) <= FREEZE_EPS and mad(self.anchor if self.start is not None else prev, fr) <= DRIFT_EPS
        if ok and self.start is None:
            self.start, self.anchor = idx - 1, prev
        elif not ok and self.start is not None:
            self.spans.append((self.start, idx - self.start))
            self.start = None

    def finish(self, count):
        if self.start is not None:
            self.spans.append((self.start, count - self.start))
        return self.spans


def stamp(idx, fps):
    return f"{idx / fps:.2f}s"


def times(text):
    """argparse type: comma-separated seconds, each a number >= 0."""
    try:
        vals = [float(t) for t in text.split(",") if t.strip()]
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{text}' is not a comma-separated list of seconds")
    if any(v < 0 or v != v for v in vals):
        raise argparse.ArgumentTypeError(f"'{text}' has a negative or invalid time")
    return vals


def decode_problems(reader, count, expected):
    """FAIL messages when the decode did not read the whole video."""
    found = []
    if reader.returncode not in (0, None):
        found.append(f"ffmpeg could not decode the video (exit {reader.returncode})"
                     + (f": {reader.errors.splitlines()[-1][:200]}" if reader.errors else ""))
    if expected is not None and abs(count - expected) > 1:
        found.append(f"read {count} frame(s) but the file says it holds {expected}: the video is truncated or damaged"
                     + (f" ({reader.errors.splitlines()[-1][:160]})" if reader.errors else ""))
    if count < 4:
        found.append(f"only {count} frame(s) could be read: nothing was measured")
    return found


def report(args, path):
    results, fails = [], 0

    def out(level, text):
        nonlocal fails
        fails += level == "FAIL"
        results.append(f"{level:<5} {text}")

    try:
        fps, rate, expected = probe(path)
    except (Unmeasured, OSError) as err:
        print(f"FAIL  seams not measured: {err}")
        return 1
    joins = [round(t * fps) for t in (args.joins or [])]
    reader = FrameReader(path, rate)
    try:
        diffs, flickers, join_ssim, spans = scan(reader, joins, args.flicker_min)
    except OSError as err:
        print(f"FAIL  seams not measured: cannot run ffmpeg ({err})")
        return 1
    problems = decode_problems(reader, reader.count, expected)
    for msg in problems:
        out("FAIL", f"seams not measured: {msg}")
    if problems:
        print("\n".join(results))
        return 1
    if reader.errors:
        out("WARN", f"the decoder reported errors but read every frame: {reader.errors.splitlines()[-1][:200]}")
    planned = [t * fps for t in (args.flash_ok or [])]
    surprise = 0
    for idx, length, size in flickers:
        what = f"{length} odd frame(s), change {size:.1f}/255 each way, then the picture returns"
        if any(abs(idx - p) <= 2 for p in planned):
            out("INFO", f"planned flash at {stamp(idx, fps)}: {what}")
            continue
        surprise += 1
        out("FAIL" if args.strict else "WARN", f"flicker at {stamp(idx, fps)}: {what}"
            + ("" if args.strict else ". Intended (a flash, a flickering look)? List it with --flash-ok; if not, fix it"))
    if not surprise:
        out("PASS", "no one-frame pop or flicker")
    for idx in joins:
        ratio = diffs[idx] / max(neighbours(diffs, idx), 0.05) if idx < len(diffs) else 0
        s = join_ssim.get(idx)
        if s is None:
            out("WARN", f"join at {stamp(idx, fps)} is outside the video")
        elif s >= args.join_ssim:
            out("PASS", f"join at {stamp(idx, fps)} SSIM {s:.4f}")
        elif ratio >= 3 and diffs[idx] > 1.0:
            out("FAIL", f"join at {stamp(idx, fps)} SSIM {s:.4f} (< {args.join_ssim}) and the jump is {ratio:.0f}x its neighbours: a pop")
        elif ratio >= 2 and diffs[idx] > 1.0:
            out("WARN", f"join at {stamp(idx, fps)} SSIM {s:.4f} (< {args.join_ssim}), jump {ratio:.1f}x its neighbours: look at the frames either side")
        else:
            out("PASS", f"join at {stamp(idx, fps)} SSIM {s:.4f} (< {args.join_ssim}, but the change matches the motion around it)")
    events = scdet_events(path, fps)
    skip = {i for idx, length, _ in flickers for i in range(idx, idx + length + 1)}
    hard, soft = classify_changes(diffs, events, skip)
    out("INFO", f"hard cuts (scdet >= {SCDET_MIN:g} and {CUT_RATIO:g}x its neighbours): {len(hard)}"
        + (" at " + ", ".join(stamp(i, fps) for i in hard) if hard else ""))
    if soft:
        out("INFO", f"soft changes (one signal only, a fast move or a dissolve): {len(soft)} at "
            + ", ".join(stamp(i, fps) for i in soft))
    if not events and not scdet_available():
        out("INFO", "this ffmpeg has no scdet filter: cuts are not classified")
    freezes = [(st, n / fps) for st, n in spans if n / fps >= args.freeze_seconds]
    if freezes:
        out("WARN", f"{len(freezes)} frozen stretch(es) over {args.freeze_seconds:g}s: "
            + ", ".join(f"{stamp(s, fps)} for {d:.1f}s" for s, d in freezes)
            + ". Expected where the brief asks for a hold (say so in REPORT.md), otherwise dead air")
    else:
        out("PASS", f"nothing frozen over {args.freeze_seconds:g}s (slow pans over a detailed picture do not count)")
    print("\n".join(results))
    return 1 if fails else 0


def scdet_available():
    proc = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True)
    return " scdet " in proc.stdout


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--joins", type=times, help="comma-separated times (s) where separate segments were joined")
    ap.add_argument("--join-ssim", type=float, default=0.99, help="lowest SSIM across a join that counts as a match (default 0.99)")
    ap.add_argument("--freeze-seconds", type=float, default=1.5, help="shortest frozen stretch to report (default 1.5)")
    ap.add_argument("--flicker-min", type=float, default=6.0,
                    help="smallest frame change (0-255 scale) that can be a flicker (default 6)")
    ap.add_argument("--flash-ok", type=times, help="comma-separated times (s) of planned flashes; flicker within 2 frames of one is INFO")
    ap.add_argument("--strict", action="store_true", help="an unlisted flicker is a FAIL instead of a WARN")
    args = ap.parse_args()
    return report(args, args.video)


if __name__ == "__main__":
    sys.exit(main())
