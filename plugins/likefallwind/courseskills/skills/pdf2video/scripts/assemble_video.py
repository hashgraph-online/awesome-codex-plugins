#!/usr/bin/env python3
"""Assemble slides + audio into a single narrated video using ffmpeg.

Usage:
    python assemble_video.py <course-dir> [--output PATH]

For each <stem>.png in <course-dir>/slides/ paired (alphabetically) with the
matching <stem>.mp3 in <course-dir>/audio/, render a per-page mp4 (image
held for head_silence + audio_length + tail_silence), then concat-mux the
segments into <course-dir>/<course title>.mp4 (falls back to course-video.mp4
when outline.md is missing or has no usable H1).

Reads padding from <course-dir>/audio.md keys head_silence_sec / tail_silence_sec
(defaults: 0.3 / 0.5). Course title comes from <course-dir>/outline.md's H1
(stripping `课程标题:` / `Course:` prefix), matching codex2course/images2pdf.py.

Requires: ffmpeg on PATH. No third-party libs.
"""
import argparse
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULTS = {
    "head_silence_sec": 0.3,
    "tail_silence_sec": 0.5,
    "width": 1920,
    "height": 1080,
    "fps": 30,
}

KEY_RE = re.compile(r"^\s*-\s*\*\*([^*]+):\*\*\s*(.+?)\s*$")

# Same conventions as codex2course/scripts/images2pdf.py — keep them in sync
# so the .pdf and .mp4 land next to each other with matching names.
_TITLE_PREFIX = re.compile(r"^(?:课程标题|课程名称|课程|标题|title|course)\s*[:：]\s*", re.IGNORECASE)
_FILENAME_BAD = re.compile(r'[\\/:*?"<>|\r\n\t]+')


def extract_course_title(outline_path: Path) -> str | None:
    if not outline_path.is_file():
        return None
    for line in outline_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("# ") and not stripped.startswith("## "):
            title = stripped[2:].strip()
            title = _TITLE_PREFIX.sub("", title).strip()
            return title or None
    return None


def sanitize_filename(name: str) -> str:
    cleaned = _FILENAME_BAD.sub(" ", name).strip().rstrip(".")
    return re.sub(r"\s+", " ", cleaned)


def default_output_path(course_dir: Path) -> Path:
    title = extract_course_title(course_dir / "outline.md")
    if title:
        safe = sanitize_filename(title)
        if safe:
            return course_dir / f"{safe}.mp4"
    return course_dir / "course-video.mp4"


def parse_audio_md(path: Path) -> dict:
    cfg: dict = {}
    if not path.exists():
        return cfg
    for line in path.read_text(encoding="utf-8").splitlines():
        m = KEY_RE.match(line)
        if not m:
            continue
        key = m.group(1).strip().lower().replace(" ", "_")
        cfg[key] = m.group(2).strip()
    return cfg


def resolve_settings(cfg: dict) -> dict:
    s = dict(DEFAULTS)
    for k in ("head_silence_sec", "tail_silence_sec"):
        if k in cfg:
            s[k] = float(cfg[k])
    return s


def pair_slides_audio(slides_dir: Path, audio_dir: Path) -> list[tuple[Path, Path]]:
    slides = sorted(p for p in slides_dir.iterdir() if p.suffix.lower() == ".png")
    audios = sorted(p for p in audio_dir.iterdir() if p.suffix.lower() == ".mp3")
    if not slides:
        sys.exit(f"No .png in {slides_dir}")
    if not audios:
        sys.exit(f"No .mp3 in {audio_dir}. Run synth_audio.py first.")

    audio_by_stem = {p.stem: p for p in audios}
    pairs: list[tuple[Path, Path]] = []
    missing: list[str] = []
    for s in slides:
        a = audio_by_stem.get(s.stem)
        if a is None:
            missing.append(s.stem)
        else:
            pairs.append((s, a))
    if missing:
        sys.exit(
            "Missing audio for slides: "
            + ", ".join(missing)
            + "\nRun: python synth_audio.py <course-dir> --only <prefix>"
        )
    extra = sorted(set(audio_by_stem) - {s.stem for s in slides})
    if extra:
        print(f"warning: audio without matching slide (will be ignored): {extra}", file=sys.stderr)
    return pairs


def probe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    return float(out)


def render_segment(image: Path, audio: Path, out: Path, settings: dict) -> None:
    head_sec = float(settings["head_silence_sec"])
    tail_sec = float(settings["tail_silence_sec"])
    w, h, fps = settings["width"], settings["height"], settings["fps"]

    # Lock segment duration to an integer number of frames so that video and
    # audio stream durations match exactly. Otherwise -shortest cuts video at
    # the last full frame, leaving a per-segment gap of up to 1/fps that
    # accumulates across concat copy and drifts the final mp4 (audio ends up
    # later than video, by ~16ms × N segments).
    audio_body = probe_duration(audio)
    target = head_sec + audio_body + tail_sec
    frames = math.ceil(target * fps)
    seg_dur = frames / fps  # exact frame-aligned duration
    head_ms = int(round(head_sec * 1000))

    vf = (
        f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
        f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1"
    )
    # adelay shifts the body by head_silence; apad with whole_dur pads to the
    # exact frame-aligned target so the audio stream ends at the same instant
    # as the last video frame.
    af = f"adelay={head_ms}:all=1,apad=whole_dur={seg_dur:.6f}"
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-loop", "1", "-framerate", str(fps), "-i", str(image),
        "-i", str(audio),
        "-af", af,
        "-vf", vf,
        "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
        "-r", str(fps), "-frames:v", str(frames),
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        "-t", f"{seg_dur:.6f}",
        "-movflags", "+faststart",
        str(out),
    ]
    subprocess.run(cmd, check=True)


def concat_segments(segments: list[Path], output: Path) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        for s in segments:
            # ffmpeg concat demuxer wants single-quoted absolute paths
            f.write(f"file '{s.as_posix()}'\n")
        list_path = Path(f.name)
    try:
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "concat", "-safe", "0", "-i", str(list_path),
            "-c", "copy", "-movflags", "+faststart",
            str(output),
        ]
        subprocess.run(cmd, check=True)
    finally:
        list_path.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("course_dir", type=Path)
    parser.add_argument("--output", type=Path, default=None,
                        help="Output mp4 path (default: <course-dir>/<course title>.mp4, "
                             "derived from outline.md's H1; falls back to course-video.mp4)")
    args = parser.parse_args()

    if shutil.which("ffmpeg") is None:
        sys.exit("ffmpeg not found on PATH. Install it first.")

    course = args.course_dir.resolve()
    slides_dir = course / "slides"
    audio_dir = course / "audio"
    if not slides_dir.is_dir():
        sys.exit(f"slides/ missing under {course}")
    if not audio_dir.is_dir():
        sys.exit(f"audio/ missing under {course}. Run synth_audio.py first.")

    settings = resolve_settings(parse_audio_md(course / "audio.md"))
    pairs = pair_slides_audio(slides_dir, audio_dir)
    output = args.output or default_output_path(course)

    with tempfile.TemporaryDirectory(prefix="pdf2video-") as tmp:
        tmp_dir = Path(tmp)
        segments: list[Path] = []
        for i, (img, aud) in enumerate(pairs):
            seg = tmp_dir / f"seg-{i:04d}.mp4"
            print(f"render {img.name} + {aud.name} -> {seg.name}")
            render_segment(img, aud, seg, settings)
            segments.append(seg)
        print(f"concat {len(segments)} segments -> {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        concat_segments(segments, output)
    print(f"done   {output}")


if __name__ == "__main__":
    main()
