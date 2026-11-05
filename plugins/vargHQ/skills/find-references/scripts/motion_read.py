#!/usr/bin/env python3
"""Measure a motion reference: where it cuts, what it holds, how the camera moves, how elements land and grow.

Pick the clip by eye first. A search box finds "kinetic type"; it cannot find "2-frame holds". This script takes
those numbers out of the clip you picked, so you can write them into a prompt or into code.

Usage:
  motion_read.py cuts     VIDEO [--start S] [--end S] [--out DIR] [--detector adaptive|content] [--min-shot S]
  motion_read.py holds    VIDEO [--start S] [--end S] [--stills]
  motion_read.py camera   VIDEO [--start S] [--end S]
  motion_read.py elements VIDEO [--start S] [--end S] [--crop X:Y:W:H]
  motion_read.py elements VIDEO --grid COLSxROWS [--threshold N] [--start S] [--end S]
  motion_read.py scale    VIDEO [--start S] [--end S] [--crop X:Y:W:H] [--threshold N]

What each one does (all print JSON to stdout):
  cuts      Cut times and shot lengths (PySceneDetect detect-adaptive). Saves one frame per shot in --out.
            --detector content compares each frame with the one before. --min-shot 0.04 drops the 0.6 s floor on a
            shot, which hides fast cuts. On a flat graphic clip run both and look at the frames: neither finds all.
  holds     Which frames repeat: on ones, twos or threes (ffmpeg mpdecimate, plain and denoised).
            --stills adds long freezes (freezedetect), which also counts black at fades.
  camera    One shot only. Pan and tilt curve by phase correlation; zoom and roll by optical flow.
            Gives t50, t90, overshoot, nearest named ease, a cubic-bezier, speed_cv and jitter.
            Set --start and --end one or two frames inside the cuts, or the cut reads as motion.
  elements  Flat ground only. Default: one element's position curve by centroid (use --crop to isolate it).
            Position only: it warns when the size changes more than the position, so run scale there.
            --grid: onset frame per cell, which gives the stagger. It prints null, with a warning, if the ground is
            not flat or every cell has the same onset.
  scale     Flat ground only. One move: width and height of what differs from the ground, per frame, then the fast
            part, the settle and the hold. Start the window on the ground or a held frame.
            It reads a box, so it cannot measure rotation (it warns when the box changes and the area does not), part
            two elements (crop them), see past the frame edge, or tell a growing word from a word gaining letters.

Dependencies:
  all subcommands   ffmpeg and ffprobe 5.1 or newer on PATH
  cuts              pip install scenedetect opencv-python
  camera, elements, scale  pip install opencv-python numpy
  holds             nothing else

Frame rate: read from the packet timestamps and checked against r_frame_rate and avg_frame_rate, because avg_frame_rate
is 1000/1 on some WebMs. If the values disagree or the rate varies, it warns and gives the re-encode command.

Limits: real footage has no ground truth, and a moving subject contaminates the global read. Read `warnings`.
Run it only on a clip you may process: your own, licensed, or Creative Commons.
"""
import argparse
import csv
import importlib
import importlib.util
import json
import re
import shutil
import statistics
import subprocess
import sys
from collections import Counter
from pathlib import Path


RATES = {}
NOTES = []  # warnings about the file itself, printed with whatever the subcommand reads
FLAT_SHARE = 0.8  # share of pixels in the two commonest luma levels. Flat clips read 0.85 to 1, real footage under 0.6


def fail(message):
    sys.exit(f"motion_read.py: {message}")


def show(result):
    """Print valid JSON with one top-level key per line, so that it reads well in a terminal."""
    if NOTES:
        result["warnings"] = list(dict.fromkeys(NOTES + result.get("warnings", [])))
    print("{\n" + ",\n".join(f" {json.dumps(k)}: {json.dumps(v)}" for k, v in result.items()) + "\n}")


def numeric_modules():
    """Import OpenCV and numpy only for the subcommands that need them."""
    modules = []
    for name, package in (("cv2", "opencv-python"), ("numpy", "numpy")):
        try:
            modules.append(importlib.import_module(name))
        except ImportError:
            fail(f"this subcommand needs the Python module '{name}'. Install it: pip install {package}")
    return modules


def ratio(text):
    top, _, bottom = (text or "").partition("/")
    try:
        return float(top) / float(bottom or 1)
    except (ValueError, ZeroDivisionError):
        return 0.0


def frame_rate(video, stream):
    """The rate to trust. Timestamps decide, because avg_frame_rate is 1000/1 on some WebMs with millisecond timestamps.
    Warn if the header values disagree or the gaps between frames vary, and fail if nothing is believable."""
    real, average = ratio(stream.get("r_frame_rate")), ratio(stream.get("avg_frame_rate"))
    done = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=pts_time",
                           "-of", "csv=p=0", video], capture_output=True, text=True)
    # A set, because VP8 stores hidden frames at the time of the next shown frame: that zero gap is what breaks avg.
    times = sorted({float(x) for x in re.findall(r"^-?[0-9]+(?:\.[0-9]+)?", done.stdout, re.M)})
    counted = (len(times) - 1) / (times[-1] - times[0]) if len(times) > 1 and times[-1] > times[0] else 0.0
    sane = lambda rate: 1 <= rate <= 240
    close = lambda a, b: abs(a - b) <= 0.02 * b
    header = [rate for rate in (real, average) if sane(rate)]
    if sane(counted):
        fps = next((rate for rate in header if close(rate, counted)), counted)
    elif header:
        fps = header[0]
    else:
        fail(f"no believable frame rate in {video}: r_frame_rate {stream.get('r_frame_rate')}, avg_frame_rate "
             f"{stream.get('avg_frame_rate')}, {len(times)} packets. Re-encode it: {reencode(video, 25)}")
    gaps = [b - a for a, b in zip(times, times[1:])]
    uneven = 0.0
    if gaps:
        middle = statistics.median(gaps)
        uneven = sum(abs(gap - middle) > max(0.0025, 0.25 * middle) for gap in gaps) / len(gaps)
    if real and average and not close(real, average):
        NOTES.append(f"Header frame rates disagree: r_frame_rate {stream.get('r_frame_rate')}, avg_frame_rate "
                     f"{stream.get('avg_frame_rate')}, timestamps {round(counted, 3)}. Used {round(fps, 3)}. To be sure, "
                     f"re-encode to constant rate and read the copy: {reencode(video, fps)}")
    if uneven > 0.01:
        NOTES.append(f"Variable frame rate: {round(uneven * 100)}% of frame gaps are off the median, so frame counts hold "
                     f"and seconds do not. Re-encode to constant rate and read the copy: {reencode(video, fps)}")
    return fps


def reencode(video, fps):
    return f"ffmpeg -i {video} -vf fps={round(fps, 3)} -an -c:v libx264 -crf 18 -pix_fmt yuv420p constant.mp4"


def probe(video):
    """Return (width, height, fps) as ffmpeg will decode it, with phone rotation applied."""
    command = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-of", "json", "-show_entries",
               "stream=width,height,avg_frame_rate,r_frame_rate:stream_side_data=rotation", video]
    done = subprocess.run(command, capture_output=True, text=True)
    streams = json.loads(done.stdout or "{}").get("streams")
    if done.returncode or not streams:
        fail(f"ffprobe found no video stream in {video}. {done.stderr.strip()}")
    stream = streams[0]
    width, height = stream["width"], stream["height"]
    rotation = next((s["rotation"] for s in stream.get("side_data_list", []) if "rotation" in s), 0)
    if abs(rotation) % 180 == 90:
        width, height = height, width
    if video not in RATES:
        RATES[video] = frame_rate(video, stream)
    return width, height, RATES[video]


def window_args(start, end):
    """ffmpeg input options for the time window. Before -i they seek fast and stop reading exactly at the end."""
    return (["-ss", str(start)] if start else []) + (["-t", str(end - start)] if end else [])


def gray_frames(np, video, start=0.0, end=None, crop=None):
    """Return fps and a generator of 8-bit luma frames from ffmpeg, with every source frame passed through once."""
    width, height, fps = probe(video)
    filters = "format=gray"
    if crop:
        x, y, width, height = crop
        filters = f"crop={width}:{height}:{x}:{y},{filters}"
    command = ["ffmpeg", "-nostdin", "-v", "error", *window_args(start, end), "-i", video, "-an", "-sn",
               "-vf", filters, "-fps_mode", "passthrough", "-f", "rawvideo", "-"]

    def generate():
        process = subprocess.Popen(command, stdout=subprocess.PIPE)
        while True:
            raw = process.stdout.read(width * height)
            if len(raw) < width * height:
                break
            yield np.frombuffer(raw, dtype=np.uint8).reshape(height, width)
        process.stdout.close()
        process.wait()

    return fps, generate()


# ---- cuts ------------------------------------------------------------------------------------------------------


def cuts(args):
    for module, package in (("scenedetect", "scenedetect"), ("cv2", "opencv-python")):
        if importlib.util.find_spec(module) is None:
            fail(f"cuts needs the Python module '{module}'. Install it: pip install {package}")
    video = Path(args.video)
    out = Path(args.out or f"{video.stem}_cuts")
    fps = probe(args.video)[2]  # OpenCV's own rate is the wrong one on the files that break avg_frame_rate
    command = [sys.executable, "-I", "-m", "scenedetect", "-i", str(video), "-f", str(fps), "-o", str(out), "-q"]
    if args.min_shot is not None:
        command += ["-m", f"{args.min_shot}s"]
    if args.start or args.end:
        command += ["time", "-s", str(args.start or 0)] + (["-e", str(args.end)] if args.end else [])
    command += [f"detect-{args.detector}", "list-scenes", "save-images", "--num-images", "1"]
    done = subprocess.run(command, capture_output=True, text=True)
    table = out / f"{video.stem}-Scenes.csv"
    if done.returncode or not table.exists():
        fail(f"scenedetect failed. {done.stderr.strip()[-400:]}")
    rows = list(csv.reader(table.open()))
    header = rows[1]  # rows[0] is the timecode list
    begin, stop = header.index("Start Time (seconds)"), header.index("End Time (seconds)")
    shots = [(float(row[begin]), float(row[stop])) for row in rows[2:] if row]
    lengths = sorted(b - a for a, b in shots) or [0.0]
    if lengths[0] < 0:
        fail(f"impossible result: a shot of {round(lengths[0], 3)} s, so the frame rate is wrong. Re-encode to constant "
             f"rate and read the copy: {reencode(args.video, fps)}")
    total = sum(lengths)
    deciles = statistics.quantiles(lengths, n=10, method="inclusive") if len(lengths) > 1 else lengths * 9
    show({
        "detector": args.detector,
        "fps": round(fps, 3),
        "cuts": max(len(shots) - 1, 0),
        "shots": len(shots),
        "cuts_per_minute": round((len(shots) - 1) * 60 / total, 1) if total else 0,
        "shot_length_s": {"mean": round(total / len(lengths), 2), "median": round(statistics.median(lengths), 2),
                          "p10": round(deciles[0], 2), "p90": round(deciles[8], 2),
                          "shortest": round(lengths[0], 3), "longest": round(lengths[-1], 3)},
        "cut_times_s": [round(a, 3) for a, _ in shots[1:]],
        "table": str(table),
        "frames_in": str(out),
    })


# ---- holds -----------------------------------------------------------------------------------------------------


def read_pattern(video, start, end, chain):
    """Run mpdecimate and return K for each frame it keeps and d for each frame it drops as a repeat."""
    command = ["ffmpeg", "-nostdin", "-hide_banner", "-nostats", "-loglevel", "debug", *window_args(start, end),
               "-i", video, "-an", "-vf", chain, "-f", "null", "-"]
    process = subprocess.Popen(command, stderr=subprocess.PIPE, text=True, errors="replace")
    pattern = []
    for line in process.stderr:
        found = re.search(r"\b(keep|drop) pts:\d+", line)
        if found:
            pattern.append("K" if found.group(1) == "keep" else "d")
    process.wait()
    if not pattern:
        fail("mpdecimate read no frames. Check the file and the time window.")
    return "".join(pattern)


def describe_pattern(pattern):
    holds = [len(run) for run in re.findall(r"Kd*", pattern)]
    frames_by_length = Counter()
    for length in holds:
        frames_by_length[length] += length
    length, frames = frames_by_length.most_common(1)[0]
    names = {1: "on ones", 2: "on twos", 3: "on threes"}
    return {
        "frames": len(pattern),
        "keep": pattern.count("K"),
        "drop": pattern.count("d"),
        "reads_as": names.get(length, f"held {length} frames") if frames / len(pattern) >= 0.6 else "mixed",
        "longest_hold_frames": max(holds),
        "pattern": pattern if len(pattern) <= 96 else pattern[:96] + "...",
    }


def holds(args):
    result = {
        # Counts depend on the read size, so read at a fixed width. Compare clips only at the same width.
        "plain": describe_pattern(read_pattern(args.video, args.start, args.end, "scale=640:-2,mpdecimate")),
        # Grain hides every hold from plain mpdecimate. Shrinking and denoising brings them back, and also
        # reads a slow move as holds. Believe a regular pattern; check anything else on a motion sheet.
        "denoised": describe_pattern(read_pattern(args.video, args.start, args.end,
                                                  "scale=160:-2,hqdn3d=8:8:12:12,mpdecimate")),
    }
    if args.stills:
        done = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-nostats", *window_args(args.start, args.end),
                               "-i", args.video, "-an", "-vf", "freezedetect=n=-60dB:d=0.5", "-f", "null", "-"],
                              capture_output=True, text=True, errors="replace")
        begins = [float(x) for x in re.findall(r"freeze_start: ([0-9.]+)", done.stderr)]
        spans = [float(x) for x in re.findall(r"freeze_duration: ([0-9.]+)", done.stderr)]
        result["stills_over_0.5s"] = [{"start": b, "seconds": s} for b, s in zip(begins, spans)]
    show(result)


# ---- curves shared by camera and elements --------------------------------------------------------------------


def named_eases(np):
    """GSAP names. power1 is quad, power2 cubic, power3 quart, power4 quint."""
    ease_out = lambda p: lambda t: 1 - (1 - t) ** p
    ease_in = lambda p: lambda t: t ** p
    ease_in_out = lambda p: lambda t: np.where(t < 0.5, (2 * t) ** p / 2, 1 - (2 * (1 - t)) ** p / 2)
    back_out = lambda c: lambda t: 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2
    return {
        "none": lambda t: t,
        "sine.inOut": lambda t: -(np.cos(np.pi * t) - 1) / 2,
        "power1.out": ease_out(2), "power2.out": ease_out(3), "power3.out": ease_out(4), "power4.out": ease_out(5),
        "expo.out": lambda t: np.where(t >= 1, 1.0, 1 - 2.0 ** (-10 * t)),
        "back.out(1.2)": back_out(1.2), "back.out(1.7)": back_out(1.7), "back.out(2.5)": back_out(2.5),
        "power1.in": ease_in(2), "power2.in": ease_in(3), "power3.in": ease_in(4),
        "power1.inOut": ease_in_out(2), "power2.inOut": ease_in_out(3), "power3.inOut": ease_in_out(4),
    }


def fit_bezier(np, curve):
    """Fit a CSS cubic-bezier: coarse grid, then a shrinking pattern search. Check it against t50 and t90."""
    t = np.linspace(0, 1, len(curve))
    s = np.linspace(0, 1, 400)

    def error(p):
        x = 3 * (1 - s) ** 2 * s * p[0] + 3 * (1 - s) * s ** 2 * p[2] + s ** 3
        y = 3 * (1 - s) ** 2 * s * p[1] + 3 * (1 - s) * s ** 2 * p[3] + s ** 3
        return float(np.sqrt(np.mean((np.interp(t, x, y) - curve) ** 2)))

    xs, ys = np.arange(0.0, 1.01, 0.2), np.arange(-0.2, 1.61, 0.3)
    best = min(([x1, y1, x2, y2] for x1 in xs for x2 in xs for y1 in ys for y2 in ys), key=error)
    best_error, step = error(best), 0.1
    while step > 0.0005:
        improved = False
        for i in range(4):
            for delta in (step, -step):
                trial = list(best)
                trial[i] += delta
                if i in (0, 2):  # x handles must stay in 0..1 or the curve stops being a function of time
                    trial[i] = min(max(trial[i], 0.0), 1.0)
                trial_error = error(trial)
                if trial_error < best_error:
                    best, best_error, improved = trial, trial_error, True
        if not improved:
            step /= 2
    return [round(float(v), 3) for v in best], round(best_error, 4)


def describe_move(np, steps):
    """Steps are dx, dy per frame. The curve is progress along the net direction: 0 at the start, 1 at the end."""
    total = steps.sum(axis=0)
    progress = np.concatenate([[0.0], np.cumsum(steps @ (total / np.hypot(*total)))])
    return describe_curve(np, progress / progress[-1])


def describe_curve(np, curve):
    n = len(curve) - 1
    t = np.linspace(0, 1, n + 1)
    fits = sorted((float(np.sqrt(np.mean((f(t) - curve) ** 2))), name) for name, f in named_eases(np).items())
    bezier, bezier_error = fit_bezier(np, curve)
    return {
        "t50": round(float(np.argmax(curve >= 0.5)) / n, 3),
        "t90": round(float(np.argmax(curve >= 0.9)) / n, 3),
        "overshoot_pct": round(max(0.0, float(curve.max()) - 1) * 100, 2),
        "anticipation_pct": round(max(0.0, -float(curve.min())) * 100, 2),
        "peak_speed_at": round(float(np.argmax(np.diff(curve))) / max(n - 1, 1), 3),
        "nearest_named": [[name, round(e, 4)] for e, name in fits[:3]],
        "cubic_bezier": bezier,
        "bezier_rmse": bezier_error,
    }


# ---- camera ----------------------------------------------------------------------------------------------------


def flow_step(cv2, np, previous, current):
    """Similarity transform between two frames: dx, dy of the image centre, log zoom, roll, inliers."""
    points = cv2.goodFeaturesToTrack(previous, maxCorners=300, qualityLevel=0.01, minDistance=8)
    if points is None or len(points) < 8:
        return 0.0, 0.0, 0.0, 0.0, 0
    moved, status, _ = cv2.calcOpticalFlowPyrLK(previous, current, points, None, winSize=(31, 31), maxLevel=5)
    a, b = points[status == 1], moved[status == 1]
    if len(a) < 8:
        return 0.0, 0.0, 0.0, 0.0, 0
    m, inliers = cv2.estimateAffinePartial2D(a, b, method=cv2.RANSAC, ransacReprojThreshold=2.0)
    if m is None:
        return 0.0, 0.0, 0.0, 0.0, 0
    cx, cy = previous.shape[1] / 2, previous.shape[0] / 2
    dx = m[0, 0] * cx + m[0, 1] * cy + m[0, 2] - cx
    dy = m[1, 0] * cx + m[1, 1] * cy + m[1, 2] - cy
    log_zoom = float(np.log(max(np.hypot(m[0, 0], m[1, 0]), 1e-6)))
    return dx, dy, log_zoom, float(np.arctan2(m[1, 0], m[0, 0])), int(inliers.sum())


def camera(args):
    cv2, np = numeric_modules()
    fps, frames = gray_frames(np, args.video, args.start, args.end)
    fit = lambda frame, width: cv2.resize(frame, (width, max(2, round(frame.shape[0] * width / frame.shape[1]))),
                                          interpolation=cv2.INTER_AREA)
    phase, flow, change = [], [], []  # phase at 320 wide, flow at 480 wide, mean luma change per frame
    previous = window = small_previous = None
    for full in frames:
        frame, small = fit(full, 480), fit(full, 320).astype(np.float32)
        if previous is not None:
            shift, response = cv2.phaseCorrelate(small_previous, small, window)
            phase.append((shift[0], shift[1], response))
            flow.append(flow_step(cv2, np, previous, frame))
            change.append(float(np.mean(np.abs(small - small_previous))))
        else:
            window = cv2.createHanningWindow((small.shape[1], small.shape[0]), cv2.CV_32F)
        previous, small_previous = frame, small
    if len(phase) < 12:
        fail(f"camera needs at least 13 frames, got {len(phase) + 1 if phase else 0}. Check --start and --end.")
    phase, flow = np.nan_to_num(np.array(phase)), np.array(flow)

    # A response near zero means the correlation found nothing and its shift is a random number. Fill from neighbours.
    steps, strong = phase[:, :2].copy(), phase[:, 2] >= 0.05
    for i in (0, 1):
        steps[:, i] = (np.interp(np.arange(len(steps)), np.flatnonzero(strong), steps[strong, i])
                       if strong.sum() >= 2 else 0.0)
    speed = np.hypot(steps[:, 0], steps[:, 1])
    total = steps.sum(axis=0)
    net = float(np.hypot(*total))
    moving = speed > 0.05
    moving_speed = speed[moving] if moving.sum() > 3 else speed
    kernel = np.ones(9) / 9
    residual = [steps[4:-4, i] - np.convolve(steps[:, i], kernel, mode="same")[4:-4] for i in (0, 1)]
    duration = len(steps) / fps
    flow_travel = float(np.hypot(*flow[:, :2].sum(axis=0)))
    zoom = float((np.exp(flow[:, 2].sum()) - 1) * 100 / duration)
    roll = float(np.degrees(flow[:, 3].sum()) / duration)
    straightness = net / max(float(speed.sum()), 1e-6)
    flow_agrees = abs(flow_travel - net * 1.5) <= max(0.1 * net * 1.5, 5)

    move = []
    if net * 1.5 >= 5:  # under 5 px at 480 wide counts as locked off
        move += [name for name, part in (("pan", total[0]), ("tilt", total[1])) if abs(part) >= 0.3 * net]
    if flow_agrees and abs(zoom) >= 1:
        move.append("zoom")
    if flow_agrees and abs(roll) >= 1:
        move.append("roll")

    result = {
        "frames": len(steps) + 1,
        "fps": round(fps, 3),
        "duration_s": round(duration, 3),
        "move": move or ["locked off"],
        # Signs follow the picture. Positive pan: it slides right, so the camera turns left. Positive tilt: it slides
        # down. Positive zoom: it grows. Positive roll: it turns clockwise.
        "pan_px_480w": round(float(total[0]) * 1.5, 1),
        "tilt_px_480w": round(float(total[1]) * 1.5, 1),
        "travel_px_480w": round(net * 1.5, 1),
        "zoom_pct_s": round(zoom, 2),
        "roll_deg_s": round(roll, 3),
        "speed_cv": round(float(moving_speed.std() / max(moving_speed.mean(), 1e-6)), 2),
        "jitter_px_320w": round(float(np.sqrt(np.mean(np.array(residual) ** 2))), 3),
        "hold_share": round(1 - float(moving.mean()), 2),
        "straightness": round(straightness, 2),
        "flow_travel_px_480w": round(flow_travel, 1),
        "flow_inliers_median": int(np.median(flow[:, 4])),
        "phase_weak_frames": int((~strong).sum()),
    }
    warnings = []
    if net * 1.5 >= 5:
        ease = result["ease_phase"] = describe_move(np, steps)
        if ease["bezier_rmse"] > 0.05:
            warnings.append("Poor curve fit. The camera may move, then rest: split the window at the rest, read again.")
        if straightness < 0.8:
            warnings.append("Path is not straight, so overshoot is unreliable here.")
        if flow_agrees:
            other = result["ease_flow"] = describe_move(np, flow[:, :2])
            if abs(ease["t50"] - other["t50"]) > 0.03 or abs(ease["t90"] - other["t90"]) > 0.03:
                warnings.append("The two reads give different curves. Report t50 and t90 as a range, not one number.")
    if strong.mean() < 0.5:
        warnings.append("Phase correlation found little to read: flat, dark or fast-changing picture. Weak read.")
    if not flow_agrees:
        result["zoom_pct_s"] = result["roll_deg_s"] = None  # flow lost track, so any number here would be noise
        warnings.append("Flow and phase disagree on travel. On a clean pan, phase is right and flow lost track. "
                        "With a moving subject, neither is safe: check a motion sheet. Zoom and roll are null: "
                        "flow cannot give them here.")
    if max(change) > 8 and max(change) > 4 * max(statistics.median(change), 0.5):
        at = round(args.start + (int(np.argmax(change)) + 1) / fps, 3)
        warnings.append(f"Sudden picture change near {at} s. A cut may sit in this window: read one shot at a time.")
    result["warnings"] = warnings
    show(result)


# ---- elements --------------------------------------------------------------------------------------------------


def flat_share(np, frame):
    """Share of the picture within 8 luma levels of its two commonest levels."""
    counts = np.bincount(frame.ravel(), minlength=256)
    share = 0
    for _ in range(2):
        peak = int(np.argmax(counts))
        share += int(counts[max(peak - 8, 0):peak + 9].sum())
        counts[max(peak - 8, 0):peak + 9] = 0
    return share / frame.size


def box_of(np, mask):
    """x0, x1, y0, y1 of a mask, ignoring rows and columns with under 2 pixels. None if nothing is there."""
    columns, rows = np.flatnonzero(mask.sum(axis=0) >= 2), np.flatnonzero(mask.sum(axis=1) >= 2)
    if not len(columns) or not len(rows):
        return None
    return int(columns[0]), int(columns[-1]), int(rows[0]), int(rows[-1])


def element_centroid(args, cv2, np):
    crop = [int(v) for v in args.crop.split(":")] if args.crop else None
    fps, frames = gray_frames(np, args.video, args.start, args.end, crop)
    positions, flats, sizes = [], [], []
    for index, frame in enumerate(frames):
        if index % 10 == 0:
            flats.append(flat_share(np, frame))
        _, mask = cv2.threshold(frame, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        if mask.mean() > 127:  # dark element on a light ground: the element is the smaller part
            mask = 255 - mask
        m = cv2.moments(mask)
        positions.append((m["m10"] / max(m["m00"], 1), m["m01"] / max(m["m00"], 1)))
        box = box_of(np, mask > 0)
        if box:
            sizes.append((box[1] - box[0] + 1, box[3] - box[2] + 1))
    if len(positions) < 3:
        fail("elements read fewer than 3 frames. Check the file and the time window.")
    positions = np.array(positions)
    axis = int(np.argmax(np.ptp(positions, axis=0)))
    track = positions[:, axis]
    moving = np.where(np.abs(np.diff(track)) > 0.3)[0]
    if len(moving) == 0:
        fail("no element moved more than 0.3 px per frame in this window.")
    first, last = int(moving[0]), int(moving[-1]) + 1
    travel = track[-1] - track[first]
    if abs(travel) < 1:
        fail("the element ends where it started, so there is no single move to read. Narrow the window.")
    result = {
        "fps": round(fps, 3),
        "axis": "xy"[axis],
        "move_starts_at_frame": first,
        "move_ends_at_frame": last,
        "move_frames": last - first,
        "travel_px": round(float(travel), 1),
    }
    result.update(describe_curve(np, (track[first:last + 1] - track[first]) / travel))
    warnings = []
    flat = float(np.median(flats))
    if flat < FLAT_SHARE:
        warnings.append(f"The ground is not flat ({round(flat, 2)} of the picture sits in its two commonest levels), so "
                        "this centroid may follow the picture and not an element. Crop to flat ground or trust a "
                        "motion sheet instead.")
    change = int(np.ptp(np.array(sizes), axis=0).max()) if sizes else 0
    result["size_change_px"] = change
    if abs(travel) < 0.5 * change:
        warnings.append(f"This reads position only. The element's size changes by {change} px against {round(abs(float(travel)), 1)} "
                        "px of travel, so the move is mostly scale and these numbers do not describe it. Run scale.")
    result["warnings"] = warnings
    show(result)


def element_onsets(args, cv2, np):
    columns, rows = (int(v) for v in args.grid.lower().split("x"))
    fps, frames = gray_frames(np, args.video, args.start, args.end)
    onsets, previous, index, flats = {}, None, 0, []
    for frame in frames:
        if index % 10 == 0:
            flats.append(flat_share(np, frame))
        if previous is not None:
            difference = cv2.absdiff(frame, previous)
            height, width = frame.shape
            for r in range(rows):
                for c in range(columns):
                    if (c, r) not in onsets:
                        cell = difference[r * height // rows:(r + 1) * height // rows,
                                          c * width // columns:(c + 1) * width // columns]
                        if cell.mean() > args.threshold:
                            onsets[(c, r)] = index
        previous = frame
        index += 1
    if not onsets:
        fail(f"no cell changed by more than {args.threshold} in this window. Lower --threshold.")
    order = sorted(onsets, key=onsets.get)
    flat = float(np.median(flats))
    warnings = []
    if flat < FLAT_SHARE:
        warnings.append(f"Could not read: the ground is not flat ({round(flat, 2)} of the picture sits in its two commonest "
                        "levels), so any change counts as an onset. Numbers are null. Crop to flat ground or check a "
                        "motion sheet.")
    if len(onsets) > 1 and len(set(onsets.values())) == 1:
        warnings.append(f"Could not read: all {len(onsets)} cells have onset {onsets[order[0]]}, so this is a global change "
                        "and not a stagger. Numbers are null. Narrow the window, or raise --threshold.")
    show({
        "fps": round(fps, 3),
        "frames_read": index,
        "flat_share": round(flat, 2),
        "onset_frames": None if warnings else {f"col{c}_row{r}": onsets[(c, r)] for c, r in order},
        "stagger_frames": None if warnings else [onsets[b] - onsets[a] for a, b in zip(order, order[1:])],
        "cells_with_no_onset": None if warnings else columns * rows - len(onsets),
        "warnings": warnings,
    })


def elements(args):
    cv2, np = numeric_modules()
    (element_onsets if args.grid else element_centroid)(args, cv2, np)


# ---- scale -----------------------------------------------------------------------------------------------------


def scale(args):
    cv2, np = numeric_modules()
    crop = [int(v) for v in args.crop.split(":")] if args.crop else None
    fps, frames = gray_frames(np, args.video, args.start, args.end, crop)
    ground, boxes, areas, flats, edge = None, [], [], [], False
    for index, frame in enumerate(frames):
        if ground is None:
            ground = int(np.argmax(np.bincount(frame.ravel(), minlength=256)))
        if index % 10 == 0:
            flats.append(flat_share(np, frame))
        difference = cv2.absdiff(frame, np.full_like(frame, ground))
        # Half way from the ground to the far end of the element puts the edge where the eye puts it.
        limit = args.threshold or max(float(np.percentile(difference, 99.9)) / 2, 12.0)
        mask = difference > limit
        box = box_of(np, mask)
        boxes.append(box)
        areas.append(int(mask.sum()))
        if box:
            edge = edge or box[0] == 0 or box[2] == 0 or box[1] == frame.shape[1] - 1 or box[3] == frame.shape[0] - 1
    present = [i for i, box in enumerate(boxes) if box]
    if len(present) < 3:
        fail("scale found fewer than 3 frames with anything off the ground. Check the window and --threshold.")
    first, final = present[0], present[-1]
    width = np.array([boxes[i][1] - boxes[i][0] + 1 if boxes[i] else 0 for i in range(first, final + 1)], dtype=float)
    height = np.array([boxes[i][3] - boxes[i][2] + 1 if boxes[i] else 0 for i in range(first, final + 1)], dtype=float)
    gone = [first + i for i in range(len(width)) if not width[i]]
    side, size = ("height", height) if np.ptp(height) >= np.ptp(width) else ("width", width)
    if np.ptp(size) < 3:
        flat = float(np.median(flats))
        fail(f"the ground is not flat ({round(flat, 2)} of the picture sits in its two commonest levels), so the box holds "
             "the whole picture. Crop to flat ground." if flat < FLAT_SHARE else
             f"width and height stay within {int(np.ptp(size))} px, so this is not a scale. Use elements for position.")
    # Held at the start: the longest run from frame 0 within 1 px of frame 0. Held at the end: the same from the end.
    begin = 0
    while begin + 1 < len(size) and abs(size[begin + 1] - size[0]) <= 1:
        begin += 1
    settle = len(size) - 1
    while settle > 0 and abs(size[settle - 1] - size[-1]) <= 1:
        settle -= 1
    if settle <= begin:
        fail("the size only flickers by a pixel or two here. Widen the window.")
    span = size[settle] - size[begin]
    if abs(span) < 1:
        fail("the box ends the size it started, so there is no single move to read. Narrow the window.")
    curve = (size[begin:settle + 1] - size[begin]) / span
    fast = begin + int(np.argmax(curve >= 0.9))
    steps = np.diff(size[begin:fast + 1])
    tail = np.diff(size[fast:settle + 1]) / np.maximum(size[fast:settle], 1)
    ends = lambda values: {"start": int(values[begin]), "end": int(values[settle]), "min": int(values[values > 0].min()),
                           "max": int(values.max())}
    centre = lambda box: ((box[0] + box[1]) / 2, (box[2] + box[3]) / 2)
    a, b = boxes[first + begin] or boxes[first], boxes[first + settle] or boxes[final]
    result = {
        "fps": round(fps, 3),
        "frames_read": len(boxes),
        "flat_share": round(float(np.median(flats)), 2),
        "reads": side,
        "appears_at_frame": first,
        "hold_before_frames": begin + 1,
        "move_starts_at_frame": first + begin + 1,
        "reaches_90pct_at_frame": first + fast,
        "fast_frames": fast - begin,
        "fast_steps_px": [int(step) for step in steps],
        "settle_ends_at_frame": first + settle,
        "settle_frames": settle - fast,
        "settle_pct_per_frame": round(float(np.mean(np.abs(tail))) * 100, 2) if len(tail) else 0.0,
        "hold_after_frames": len(boxes) - 1 - (first + settle),
        "width_px": ends(width),
        "height_px": ends(height),
        "scale_factor": round(float(size[settle] / max(size[begin], 1)), 3),
        "centre_drift_px": [round(centre(b)[0] - centre(a)[0], 1), round(centre(b)[1] - centre(a)[1], 1)],
    }
    result.update(describe_curve(np, curve))
    result["per_frame_w_h"] = [[first + i, int(width[i]), int(height[i])]
                               for i in range(max(begin - 2, 0), min(settle + 3, len(size)))]
    warnings = []
    if result["flat_share"] < FLAT_SHARE:
        warnings.append(f"The ground is not flat ({result['flat_share']} of the picture sits in its two commonest levels), "
                        "so the box may hold the picture and not an element. Do not use these numbers.")
    if edge:
        warnings.append("The box touches the frame edge, so the true size may run past what this can see.")
    if gone:
        warnings.append(f"Nothing is off the ground at frames {gone[:6]}: the window holds more than one move. Narrow it.")
    shown = [i for i in range(len(size)) if width[i]]
    box_area, area = np.array([width[i] * height[i] for i in shown]), np.array([areas[first + i] for i in shown])
    if np.ptp(np.log(box_area)) > 0.2 and np.ptp(np.log(np.maximum(area, 1))) < 0.1:
        warnings.append("The box changes and the area does not. That reads as rotation, not scale, and this cannot "
                        "measure rotation.")
    other = width if side == "height" else height
    factors = float(size[settle] / max(size[begin], 1)), float(other[settle] / max(other[begin], 1))
    if max(factors) / max(min(factors), 1e-6) > 1.15:
        warnings.append(f"Width and height change by different factors ({round(factors[1 if side == 'height' else 0], 2)} and "
                        f"{round(factors[0 if side == 'height' else 1], 2)}), so this is not a uniform scale: a second "
                        "element, a wipe or new letters may be in the box. Crop, or narrow the window.")
    turns = [step for step in np.diff(size[begin:settle + 1]) if abs(step) >= 3]
    turns = sum(a * b < 0 for a, b in zip(turns, turns[1:]))
    if turns > 1 or result["overshoot_pct"] > 40 or result["anticipation_pct"] > 40:
        warnings.append(f"The size changes direction {turns} times, or too far for an overshoot: the window holds more than "
                        "one move. Narrow it.")
    result["warnings"] = warnings
    show(result)


# ---- command line ------------------------------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    for name, run, about in (("cuts", cuts, "cut times and shot lengths"),
                             ("holds", holds, "on ones, twos or threes"),
                             ("camera", camera, "one shot: pan, tilt, zoom, roll, ease, jitter"),
                             ("elements", elements, "flat ground: position curve or stagger"),
                             ("scale", scale, "flat ground: width and height per frame, fast part, settle, hold")):
        command = commands.add_parser(name, help=about)
        command.add_argument("video")
        command.add_argument("--start", type=float, default=0.0, help="start of the window, seconds")
        command.add_argument("--end", type=float, default=None, help="end of the window, seconds")
        command.set_defaults(run=run)
        if name == "cuts":
            command.add_argument("--out", help="folder for the table and frames (default: <video name>_cuts)")
            command.add_argument("--detector", choices=("adaptive", "content"), default="adaptive",
                                 help="adaptive (default) or content; compare the two on flat graphic clips")
            command.add_argument("--min-shot", type=float,
                                 help="shortest shot in seconds. PySceneDetect's default is 0.6, which hides fast cuts")
        if name == "holds":
            command.add_argument("--stills", action="store_true", help="also list freezes over 0.5 s")
        if name == "elements":
            command.add_argument("--crop", help="X:Y:W:H in source pixels, to isolate one element")
            command.add_argument("--grid", help="COLSxROWS, such as 5x1, to read onset per cell instead")
            command.add_argument("--threshold", type=float, default=1.5, help="mean luma change that counts as onset")
        if name == "scale":
            command.add_argument("--crop", help="X:Y:W:H in source pixels, to isolate one element")
            command.add_argument("--threshold", type=float, help="luma difference from the ground that counts as element "
                                 "(default: half way to the element's far end)")
    args = parser.parse_args()
    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            fail(f"{tool} is not on PATH. Install ffmpeg 5.1 or newer.")
    if not Path(args.video).is_file():
        fail(f"no such file: {args.video}")
    if args.end is not None and args.end <= args.start:
        fail("--end must be after --start")
    args.run(args)


if __name__ == "__main__":
    main()
