"""film_render.py: render the acts side by side, join them with stream copy, finish with the mix.

Each project in BUILD.json is one act (or the whole film). Acts render at the same time, the workers split so the total stays at or
under 12 (references/render-traps.md, trap 12: more is not always faster; measure on your machine). Every render is checked to hold the
planned number of frames at the storyboard's frame rate (passed to HyperFrames as --fps): one extra frame is trimmed, and any
bigger difference is a FAIL, never trimmed into place. The dry renders are joined with stream copy, then
finish.sh lays the mix under the picture, sets the size, frame rate and exact duration, and measures loudness. Standard library plus
ffmpeg and Node (npx hyperframes).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from film_build import HF_PACKAGE  # noqa: E402
from film_lib import SCRIPTS, FilmError, Project, find_bash, fps_text, load_json  # noqa: E402

MAX_WORKERS = 12
SEGMENT_OVER = 60.0


def workers_for(acts: int) -> int:
    """Chrome workers per act: about 12 in all, shared between the acts, at most 8 each."""
    return max(1, min(8, MAX_WORKERS // max(1, acts)))


def hf_command(npx: str, directory: Path, out: Path, quality: str, workers: int, resume: bool, fps: str = "30") -> list[str]:
    cmd = [npx, "--yes", HF_PACKAGE, "render", str(directory), "-o", str(out), "--quality", quality, "--workers", str(workers), "--fps", str(fps), "--quiet"]
    return cmd + (["--resume"] if resume else [])


def frame_count(path: Path) -> int:
    done = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames", "-show_entries", "stream=nb_read_frames", "-of", "default=nw=1:nk=1", str(path)],
                          capture_output=True, text=True)
    return int(done.stdout.strip() or 0)


def trim_to(path: Path, frames: int) -> Path:
    out = path.with_name(path.stem + "-trim.mp4")
    done = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-frames:v", str(frames), "-c:v", "libx264", "-crf", "12", "-preset", "fast", "-pix_fmt", "yuv420p", "-an", str(out)],
                          capture_output=True, text=True)
    if done.returncode != 0:
        raise FilmError(f"could not trim {path.name} to {frames} frames: {done.stderr.strip()[-200:]}")
    return out


def render_acts(project: Project, quality: str = "delivery", workers: int | None = None, fps: str = "30") -> list[dict]:
    build = load_json(project.p("BUILD.json"), "BUILD.json")
    npx = shutil.which("npx")
    if not npx:
        raise FilmError("npx not found: install Node.js 22 or newer (https://nodejs.org), then run the render stage again")
    jobs = build["projects"]
    per = workers or workers_for(len(jobs))
    procs = []
    for job in jobs:
        out = project.p("render", f"{job['act']}.mp4")
        out.parent.mkdir(parents=True, exist_ok=True)
        env = {**os.environ, **({"HF_SEGMENTED_CAPTURE": "true"} if job["seconds"] > SEGMENT_OVER else {})}
        cmd = hf_command(npx, project.p(job["dir"]), out, quality, per, job["seconds"] > SEGMENT_OVER, fps)
        procs.append((job, out, subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)))
    results = []
    for job, out, proc in procs:
        log, _ = proc.communicate()
        if proc.returncode != 0 or not out.is_file():
            raise FilmError(f"HyperFrames failed on {job['act']}: {(log or '').strip()[-400:]}")
        have = frame_count(out)
        if abs(have - job["frames"]) > 1:            # a wrong frame rate or a broken render: never trimmed into place
            raise FilmError(f"{job['act']} rendered {have} frames, {job['frames']} were planned at {fps} fps: the render does not match the "
                            "plan (check the frame rate in STORYBOARD.json and BUILD.json, run build again, then render)")
        results.append({**job, "file": out, "frames_found": have, "trimmed": have > job["frames"]})
        if have > job["frames"]:                     # one extra frame (HyperFrames rounds the last one up): trimmed
            results[-1]["file"] = trim_to(out, job["frames"])
    return results


def join(project: Project, parts: list[dict]) -> Path:
    joined = project.p("render", "joined.mp4")
    if len(parts) == 1:
        shutil.copyfile(parts[0]["file"], joined)
        return joined
    listing = project.p("render", "list.txt")
    quote = lambda path: Path(path).resolve().as_posix().replace("'", "'\\''")      # the concat list's own quoting: ' becomes '\''
    listing.write_text("".join(f"file '{quote(p['file'])}'\n" for p in parts), encoding="utf-8", newline="\n")
    done = subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(joined)], capture_output=True, text=True)
    if done.returncode != 0:
        raise FilmError(f"joining the acts failed: {done.stderr.strip()[-300:]}")
    return joined


def finish(project: Project, joined: Path, seconds: float, mix: Path | None, size: str = "1920x1080", fps: str = "30") -> Path:
    cmd = [find_bash(), str(SCRIPTS / "finish.sh"), "--in", str(joined), "--out", str(project.final), "--seconds", f"{seconds:.4f}", "--fps", str(fps), "--size", size]
    cmd += ["--audio", str(mix)] if mix and Path(mix).is_file() else []
    done = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if done.returncode != 0:
        raise FilmError(f"finish.sh failed: {(done.stderr or done.stdout).strip()[-300:]}")
    return project.final


def render_film(project: Project, quality: str = "delivery", workers: int | None = None) -> dict:
    sb = load_json(project.storyboard, "STORYBOARD.json")
    rate = fps_text(sb)
    parts = render_acts(project, quality, workers, rate)
    joined = join(project, parts)
    final = finish(project, joined, sb["duration"], project.mix, "x".join(str(v) for v in sb["size"]), rate)
    joins = [round(a["start"], 4) for a in sb["acts"][1:]]
    return {"final": str(final), "acts": [p["act"] for p in parts], "joins": joins, "duration": sb["duration"], "quality": quality, "trimmed": [p["act"] for p in parts if p["trimmed"]]}
