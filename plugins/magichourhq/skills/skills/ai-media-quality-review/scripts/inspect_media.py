#!/usr/bin/env python3
"""Create deterministic review artifacts for an image, video, or audio file."""

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, capture_output=True, text=True)


def duration_seconds(probe: dict) -> float:
    values = [probe.get("format", {}).get("duration")]
    values.extend(stream.get("duration") for stream in probe.get("streams", []))
    for value in values:
        try:
            duration = float(value)
            if duration > 0:
                return duration
        except (TypeError, ValueError):
            continue
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    source = args.input.expanduser().resolve()
    if not source.is_file():
        parser.error(f"input file does not exist: {source}")
    for executable in ("ffmpeg", "ffprobe"):
        if not shutil.which(executable):
            parser.error(f"{executable} is required")

    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    # A failed rerun must not leave an earlier success report behind.
    (output_dir / "review.json").unlink(missing_ok=True)
    probe = json.loads(
        run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_format",
                "-show_streams",
                "-of",
                "json",
                str(source),
            ]
        ).stdout
    )
    (output_dir / "probe.json").write_text(json.dumps(probe, indent=2) + "\n")

    streams = probe.get("streams", [])
    video = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
    audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
    if not video and not audio:
        parser.error("input has no readable image, video, or audio stream")
    duration = duration_seconds(probe)
    review = {
        "input": str(source),
        "media_type": "video" if video and duration else "image" if video else "audio",
        "duration_seconds": duration or None,
        "has_image": video is not None and not duration,
        "has_video": video is not None and bool(duration),
        "has_audio": audio is not None,
        "black_segments": [],
        "silence_segments": [],
        "artifacts": [],
    }

    if video and duration:
        sample_rate = min(4.0, 12 / duration)
        preview = output_dir / "contact-sheet.jpg"
        video_filter = f"fps={sample_rate:.6f},scale=320:-2,tile=4x3:padding=4:margin=4"
    elif video:
        preview = output_dir / "preview.jpg"
        video_filter = "scale=1280:-2"

    if video:
        run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-i",
                str(source),
                "-vf",
                video_filter,
                "-frames:v",
                "1",
                "-y",
                str(preview),
            ]
        )
        review["artifacts"].append(str(preview))

    if video and duration:
        diagnostics = run(
            [
                "ffmpeg",
                "-v",
                "info",
                "-xerror",
                "-i",
                str(source),
                "-vf",
                "blackdetect=d=0.2:pix_th=0.05",
                "-an",
                "-f",
                "null",
                "-",
            ]
        ).stderr
        review["black_segments"] = [
            {"start": float(start), "end": float(end), "duration": float(length)}
            for start, end, length in re.findall(
                r"black_start:([0-9.]+) black_end:([0-9.]+) black_duration:([0-9.]+)",
                diagnostics,
            )
        ]

    if audio:
        diagnostics = run(
            [
                "ffmpeg",
                "-v",
                "info",
                "-xerror",
                "-i",
                str(source),
                "-af",
                "silencedetect=n=-50dB:d=0.5",
                "-vn",
                "-f",
                "null",
                "-",
            ]
        ).stderr
        starts = [float(value) for value in re.findall(r"silence_start: ([0-9.]+)", diagnostics)]
        ends = [
            (float(end), float(length))
            for end, length in re.findall(r"silence_end: ([0-9.]+) \| silence_duration: ([0-9.]+)", diagnostics)
        ]
        review["silence_segments"] = [
            {"start": start, "end": end, "duration": length}
            for start, (end, length) in zip(starts, ends)
        ]
        if not video:
            waveform = output_dir / "waveform.png"
            run(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-i",
                    str(source),
                    "-filter_complex",
                    "showwavespic=s=1200x300:colors=white",
                    "-frames:v",
                    "1",
                    "-y",
                    str(waveform),
                ]
            )
            review["artifacts"].append(str(waveform))

    if video:
        review["visual"] = {
            "width": video.get("width"),
            "height": video.get("height"),
        }
    if video and duration:
        review["video"] = {
            "frame_rate": video.get("avg_frame_rate"),
            "frames": video.get("nb_frames"),
        }
    (output_dir / "review.json").write_text(json.dumps(review, indent=2) + "\n")
    print(output_dir / "review.json")


if __name__ == "__main__":
    main()
