"""film_lib.py: the small shared pieces of film mode: project paths, JSON files, errors.

Every film-mode script reads and writes plain files in one project folder, so any stage can be run alone:

    BRIEF.md -> STORY.md -> SCRIPT.md -> STORYBOARD.json -> ASSETS.json -> TIMINGS.json -> (retimed STORYBOARD.json)
             -> project/ (HyperFrames) -> audio/mix.wav -> final.mp4 + REPORT.md

Standard library only.
"""
from __future__ import annotations

import json
import os
import shutil
import wave
from dataclasses import dataclass
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent


class FilmError(Exception):
    """A problem the user can fix. The message says what to do; film.py prints it as one FAIL line."""


@dataclass(frozen=True)
class Project:
    root: Path

    def p(self, *parts: str) -> Path:
        return self.root.joinpath(*parts)

    @property
    def brief(self) -> Path: return self.p("BRIEF.md")
    @property
    def story(self) -> Path: return self.p("STORY.md")
    @property
    def script(self) -> Path: return self.p("SCRIPT.md")
    @property
    def storyboard(self) -> Path: return self.p("STORYBOARD.json")
    @property
    def assets(self) -> Path: return self.p("ASSETS.json")
    @property
    def timings(self) -> Path: return self.p("TIMINGS.json")
    @property
    def lines_dir(self) -> Path: return self.p("audio", "lines")
    @property
    def sfx_dir(self) -> Path: return self.p("assets", "sfx")
    @property
    def maps_dir(self) -> Path: return self.p("assets", "maps")
    @property
    def archive_dir(self) -> Path: return self.p("assets", "archive")
    @property
    def project(self) -> Path: return self.p("project")
    @property
    def mix(self) -> Path: return self.p("audio", "mix.wav")
    @property
    def final(self) -> Path: return self.p("final.mp4")
    @property
    def report(self) -> Path: return self.p("REPORT.md")

    def rel(self, path: Path | str) -> str:
        """A path as written in the stage files: relative to the project, forward slashes."""
        try:
            return Path(path).resolve().relative_to(self.root.resolve()).as_posix()
        except ValueError:
            return Path(path).as_posix()


def load_json(path: Path, what: str = "") -> dict | list:
    path = Path(path)
    if not path.is_file():
        raise FilmError(f"{what or path.name} not found at {path}: run the stage that writes it first")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError as err:
        raise FilmError(f"{path.name} is not valid JSON ({err}): fix it or run its stage again")


def save_json(path: Path, data) -> None:
    """Write JSON as UTF-8 with LF endings, through a temp file so an interrupted run never leaves half a file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def wav_seconds(path: Path) -> float:
    with wave.open(str(path), "rb") as wf:
        return wf.getnframes() / wf.getframerate()


def frames(seconds: float, fps: float) -> int:
    return round(seconds * fps)


NTSC = {"23.976": "24000/1001", "23.98": "24000/1001", "29.97": "30000/1001", "59.94": "60000/1001", "47.952": "48000/1001"}


def parse_fps(text: str | float | int) -> tuple[float, str]:
    """A frame rate as (value, ffmpeg/HyperFrames text): 24 -> (24.0, "24"), 29.97 or 30000/1001 -> (29.97..., "30000/1001")."""
    raw = str(text).strip()
    rate = NTSC.get(raw, raw)
    num, _, den = rate.partition("/")
    try:
        value = float(num) / float(den or 1)
    except (ValueError, ZeroDivisionError):
        raise FilmError(f"--fps '{text}' is not a frame rate: use a number (24, 30, 29.97) or a ratio (30000/1001)")
    if not 1 <= value <= 240:
        raise FilmError(f"--fps {text} is outside 1-240")
    if not den:
        rate = str(int(value)) if value.is_integer() else rate
    return value, rate


def fps_text(sb: dict) -> str:
    """The storyboard's frame rate as text for ffmpeg and HyperFrames (a ratio such as 30000/1001 stays exact)."""
    fps = sb.get("fps", 30)
    return sb.get("fps_rate") or (str(int(fps)) if float(fps).is_integer() else repr(float(fps)))


def find_bash() -> str:
    """bash for the shell scripts. On Windows `bash` on PATH is often the WSL launcher in System32, which cannot run them with
    Windows paths, so Git Bash is looked for first (B2M_BASH overrides)."""
    if os.name != "nt":
        return shutil.which("bash") or "bash"
    for cand in (os.environ.get("B2M_BASH"), r"C:\Program Files\Git\bin\bash.exe", r"C:\Program Files\Git\usr\bin\bash.exe", shutil.which("bash")):
        if cand and os.path.isfile(cand) and "system32" not in cand.lower():
            return cand
    raise FilmError("Git Bash not found (the WSL bash in System32 cannot run these scripts): install Git for Windows, or set B2M_BASH to its bash.exe")
