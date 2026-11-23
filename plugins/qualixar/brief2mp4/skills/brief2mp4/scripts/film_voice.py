"""film_voice.py: the voice stage: per-line WAVs and measured durations in TIMINGS.json, from one of three sources.

  standin   a buzz that follows the words (standin_voice.py), for drafts: timing, captions and loudness are real, the voice is not
  take      the user's own recording, cut into lines by split_takes.py (pauses, and word timings when there are any)
  f5-tts    F5-TTS, if the user installed it (python3 -m pip install f5-tts); a short reference clip and its text set the voice

Every line ends up a 48 kHz mono 16-bit WAV with its measured duration, where the speech sits inside it, and each script word's
start and end. The voice is never time-stretched. F5-TTS: the code is MIT but the pre-trained models are CC BY-NC (non-commercial),
and a voice should only be cloned with the right to do so. Standard library plus ffmpeg (F5-TTS only).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from array import array
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import split_takes  # noqa: E402
import standin_voice  # noqa: E402
from film_lib import FilmError, save_json  # noqa: E402
from film_script import Script, estimate_seconds, words_of  # noqa: E402

F5_INSTALL = "python3 -m pip install f5-tts"
F5_NOTE = "F5-TTS code is MIT; its pre-trained models are CC BY-NC (non-commercial use only). Clone only a voice you have the right to."


def _entry(lid: str, dest: Path, base: Path, duration: float, t0: float, t1: float, words: list) -> dict:
    return {"id": lid, "file": Path(os.path.relpath(dest, base)).as_posix(), "duration": round(duration, 4), "speech_start": round(t0, 4),
            "speech_end": round(t1, 4), "source_start": 0.0, "words": words}


def _write(timings_path: Path, source: str, script: Script, lines: list[dict], extra: dict | None = None) -> dict:
    data = {"version": 1, "source": source, "rate": 48000, "pace": script.pace, "lines": {l["id"]: l for l in lines}, "order": [l["id"] for l in lines], **(extra or {})}
    save_json(Path(timings_path), data)
    return data


def spread_words(text: str, t0: float, t1: float) -> list[dict]:
    """Script words with times spread by length across [t0, t1], a little extra at commas and full stops."""
    tokens = words_of(text)
    times = split_takes.word_times(tokens, None, t0, t1)
    return [{"text": t, "start": round(a, 4), "end": round(max(b, a + 0.001), 4)} for t, (a, b) in zip(tokens, times)]


def standin(script: Script, out_dir: Path, timings_path: Path) -> dict:
    lines = []
    base = Path(timings_path).parent
    for line in script.lines:
        seconds = max(0.6, estimate_seconds(line["say"], script.pace))
        words = spread_words(line["say"], 0.0, seconds)
        dest = Path(out_dir) / f"{line['id']}.wav"
        dest.parent.mkdir(parents=True, exist_ok=True)
        standin_voice.write_wav(dest, standin_voice.render(words, seconds))
        lines.append(_entry(line["id"], dest, base, seconds, 0.0, seconds, words))
    return _write(timings_path, "standin", script, lines, {"note": "stand-in voice for drafts: not speech"})


def from_take(script_path: Path, take: Path, out_dir: Path, timings_path: Path, words_path: Path | None = None, model: str | None = None) -> dict:
    return split_takes.split(Path(take), Path(script_path), Path(out_dir), Path(timings_path), words_path, model)


def f5_command(exe: str, model: str, ref: Path, ref_text: str, text: str, out_dir: Path, name: str) -> list[str]:
    return [exe, "--model", model, "--ref_audio", str(ref), "--ref_text", ref_text, "--gen_text", text, "--output_dir", str(out_dir), "--output_file", name]


def f5(script: Script, out_dir: Path, timings_path: Path, ref_audio: Path, ref_text: str, model: str = "F5TTS_v1_Base", exe: str | None = None) -> dict:
    exe = exe or shutil.which("f5-tts_infer-cli")
    if not exe:
        raise FilmError(f"F5-TTS is not installed. Install it with: {F5_INSTALL}  ({F5_NOTE}) Or record the voice yourself and use --take.")
    if not Path(ref_audio).is_file() or not ref_text.strip():
        raise FilmError("F5-TTS needs --ref-audio (a clean 5-12 s clip of the voice) and --ref-text (exactly what is said in it)")
    base, lines = Path(timings_path).parent, []
    with tempfile.TemporaryDirectory() as tmp:
        for line in script.lines:
            done = subprocess.run(f5_command(exe, model, Path(ref_audio), ref_text, line["say"], Path(tmp), f"{line['id']}.wav"), capture_output=True, text=True)
            raw = Path(tmp) / f"{line['id']}.wav"
            if done.returncode != 0 or not raw.is_file():
                raise FilmError(f"F5-TTS failed on {line['id']}: {done.stderr.strip()[-200:] or 'no output file'}")
            lines.append(_trim(raw, Path(out_dir) / f"{line['id']}.wav", line, base))
    return _write(timings_path, "f5-tts", script, lines, {"note": F5_NOTE})


def _trim(raw: Path, dest: Path, line: dict, base: Path) -> dict:
    """Keep 0.10 s before the first word and 0.15 s after the last of a generated line; measure where the speech is."""
    samples = split_takes.read_pcm(raw)
    db = split_takes.levels(samples)
    a, b = split_takes.speech_edges(db, split_takes.threshold(db), 0, len(db), line["id"])
    lo, hi = max(0.0, a * split_takes.HOP - split_takes.PAD_HEAD), min(len(samples) / split_takes.RATE, b * split_takes.HOP + split_takes.PAD_TAIL)
    cut = array("h", samples[int(lo * split_takes.RATE):int(hi * split_takes.RATE)])
    split_takes.write_wav(dest, cut)
    duration = len(cut) / split_takes.RATE
    t0, t1 = a * split_takes.HOP - lo, b * split_takes.HOP - lo
    return _entry(line["id"], dest, base, duration, t0, t1, spread_words(line["say"], t0, t1))
