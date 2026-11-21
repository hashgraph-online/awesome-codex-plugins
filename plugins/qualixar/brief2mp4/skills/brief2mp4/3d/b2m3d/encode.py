"""b2m3d encode: PNG frames -> video with ffmpeg, using hardware encoding only where it exists.

Opaque frames -> HEVC via hevc_videotoolbox on macOS when ffmpeg has it, else H.264 (libx264).
Frames with alpha -> ProRes 4444 (prores_ks, .mov), which editors and HyperFrames keep
transparency in.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from .run import B2M3DError


def ffmpeg_path() -> str:
    found = shutil.which("ffmpeg")
    if not found:
        raise B2M3DError("ffmpeg was not found on PATH (macOS: brew install ffmpeg; "
                         "Windows: winget install ffmpeg; Linux: your package manager)")
    return found


def has_encoder(name: str) -> bool:
    proc = subprocess.run([ffmpeg_path(), "-hide_banner", "-encoders"], capture_output=True, text=True)
    return name in proc.stdout


def pick_encoder(alpha: bool, platform: str | None = None, available=has_encoder) -> tuple[str, list[str]]:
    """(encoder, extra ffmpeg args). Pure given `available`, so it is unit-testable."""
    platform = platform or sys.platform
    if alpha:
        return "prores_ks", ["-profile:v", "4444", "-pix_fmt", "yuva444p10le"]
    if platform == "darwin" and available("hevc_videotoolbox"):
        return "hevc_videotoolbox", ["-q:v", "70", "-tag:v", "hvc1", "-pix_fmt", "yuv420p"]
    return "libx264", ["-crf", "16", "-pix_fmt", "yuv420p"]


def _ffmpeg(args: list[str]) -> None:
    proc = subprocess.run([ffmpeg_path(), "-hide_banner", "-loglevel", "error", "-y", *args],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        raise B2M3DError(f"ffmpeg failed: {proc.stderr[-1500:]}")


def frames_to_video(frames_dir: Path, out: Path, fps: int = 30, alpha: bool = False) -> dict:
    out.parent.mkdir(parents=True, exist_ok=True)
    encoder, extra = pick_encoder(alpha)
    if alpha:
        out = out.with_suffix(".mov")
    movflags = [] if alpha else ["-movflags", "+faststart"]
    _ffmpeg(["-framerate", str(fps), "-i", str(frames_dir / "frame_%04d.png"),
             "-c:v", encoder, *extra, *movflags, str(out)])
    return {"path": str(out), "encoder": encoder}
