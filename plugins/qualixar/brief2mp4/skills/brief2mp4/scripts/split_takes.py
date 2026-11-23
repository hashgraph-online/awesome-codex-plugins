#!/usr/bin/env python3
"""split_takes.py: find every script line in one long recording and cut it into its own WAV, with measured durations.

  python3 split_takes.py take.wav SCRIPT.md --out-dir audio/lines --timings TIMINGS.json
  python3 split_takes.py take.m4a SCRIPT.md --words words.json          # word timings from `npx hyperframes transcribe`
  python3 split_takes.py take.wav SCRIPT.md --model ggml-base.en.bin    # or a local whisper.cpp model (whisper-cli)

Read the script lines in order and say them with a pause between each. The take is converted to 48 kHz mono, its
loudness is measured every 10 ms, and speech is found against the room noise. If the pauses between lines are the
longest ones, they are the cuts; a short pause inside a line is ignored as long as every line gap is longer. When the
gaps are too short or too alike, word timings are used if there are any (--words, or whisper-cli with --model or
WHISPER_MODEL): the script is matched to the heard words, and each cut goes to the quietest moment between two lines.
A word the recogniser got wrong does not matter; the cut still falls in the gap.

Each line is cut with 0.10 s before its first word and 0.15 s after its last, and a 5 ms fade at the cut edges. The voice
is never time-stretched: the picture is re-timed to it (retime.py). TIMINGS.json gets, per line: the file, its measured
duration, where the speech sits inside the file and each script word's start and end (heard times where a word matched,
spread by length where not), for captions and lip sync. Standard library plus ffmpeg (only for files that are not
48 kHz mono WAV).
"""
from __future__ import annotations

import argparse
import difflib
import math
import os
import shutil
import subprocess
import sys
import tempfile
import wave
from array import array
from operator import mul
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lipsync  # noqa: E402
from film_lib import FilmError, save_json  # noqa: E402
from film_script import estimate_seconds, norm_token, read_script, words_of  # noqa: E402

RATE = 48000
HOP = 0.01
PAD_HEAD, PAD_TAIL, FADE = 0.10, 0.15, 0.005
MIN_GAPS = (0.30, 0.20, 0.12)           # tried in turn: the longest pause that still separates two spoken stretches
MIN_SPEECH = 0.08
SURE_RATIO = 1.5                         # line gaps must beat the longest in-line pause by this factor to trust pauses alone


# ---- reading the take ----------------------------------------------------------------------------------------------

def read_pcm(path: Path) -> array:
    """The take as 48 kHz mono 16-bit samples (converted with ffmpeg unless it already is)."""
    path = Path(path)
    if not path.is_file():
        raise FilmError(f"the take {path} does not exist")
    try:
        with wave.open(str(path), "rb") as wf:
            if (wf.getframerate(), wf.getnchannels(), wf.getsampwidth()) == (RATE, 1, 2):
                a = array("h")
                a.frombytes(wf.readframes(wf.getnframes()))
                return a
    except (wave.Error, EOFError):
        pass
    if shutil.which("ffmpeg") is None:
        raise FilmError("this take is not a 48 kHz mono 16-bit WAV and ffmpeg is not installed to convert it (macOS: brew install ffmpeg)")
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "take.wav"
        done = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-ac", "1", "-ar", str(RATE), "-c:a", "pcm_s16le", str(wav)], capture_output=True, text=True)
        if done.returncode != 0:
            raise FilmError(f"ffmpeg could not read {path.name}: {done.stderr.strip()[-200:]}")
        return read_pcm(wav)


def levels(samples: array) -> list[float]:
    """Loudness in dB below full scale for every 10 ms."""
    hop = int(RATE * HOP)
    out = []
    for i in range(0, len(samples) - hop + 1, hop):
        chunk = samples[i:i + hop]
        out.append(10 * math.log10(max(sum(map(mul, chunk, chunk)) / hop, 1.0) / (32768.0 ** 2)))
    return out


def threshold(db: list[float]) -> float:
    s = sorted(db)
    floor, loud = s[int(len(s) * 0.10)], s[int(len(s) * 0.90)]
    return floor + max(10.0, 0.3 * (loud - floor))


def speech_segments(db: list[float], thr: float, min_gap: float) -> list[tuple[int, int]]:
    """(first hop, last hop + 1) of every stretch above `thr`, joining stretches closer than `min_gap`."""
    runs, start = [], None
    for i, v in enumerate(db + [-200.0]):
        if v >= thr and start is None:
            start = i
        elif v < thr and start is not None:
            runs.append([start, i])
            start = None
    merged: list[list[int]] = []
    for r in runs:
        if merged and (r[0] - merged[-1][1]) * HOP < min_gap:
            merged[-1][1] = r[1]
        else:
            merged.append(r)
    return [(a, b) for a, b in merged if (b - a) * HOP >= MIN_SPEECH]


# ---- where the lines are ---------------------------------------------------------------------------------------------

def quietest(db: list[float], lo: int, hi: int) -> int:
    """The hop in [lo, hi] with the lowest loudness, smoothed over 5 hops so one random quiet hop beside a word does not win."""
    lo, hi = max(0, lo), min(len(db) - 1, max(lo, hi))
    smooth = lambda i: sum(db[max(0, i - 2):i + 3]) / len(db[max(0, i - 2):i + 3])
    return min(range(lo, hi + 1), key=lambda i: (round(smooth(i), 1), abs(i - (lo + hi) // 2)))


def cuts_from_pauses(db: list[float], thr: float, n: int) -> tuple[list[int], float, int] | None:
    """(cut hops, how clearly the line gaps beat the other gaps, stretches found), or None when there are fewer stretches than lines."""
    found = 0
    for gap in MIN_GAPS:
        segs = speech_segments(db, thr, gap)
        found = len(segs)
        if found >= n:
            gaps = [(segs[i + 1][0] - segs[i][1], i) for i in range(found - 1)]
            top = sorted(sorted(gaps, reverse=True)[:n - 1], key=lambda g: g[1])
            rest = [g for g in gaps if g not in top]
            ratio = min((g[0] for g in top), default=1) / max((g[0] for g in rest), default=0.5) if top else 99.0
            return [(segs[i][1] + segs[i + 1][0]) // 2 for _, i in top], ratio, found      # the middle of a gap that is silent by construction
    return None if found < n else None


def cuts_from_words(db: list[float], spans: list[tuple[float, float]]) -> list[int]:
    cuts = []
    for (_, end_a), (start_b, _) in zip(spans, spans[1:]):
        lo, hi = int((end_a - 0.05) / HOP), int((start_b + 0.05) / HOP)
        if hi - lo < 4:
            mid = int((end_a + start_b) / 2 / HOP)
            lo, hi = mid - 10, mid + 10
        cuts.append(quietest(db, lo, hi))
    return cuts


def line_spans(script_tokens: list[list[str]], heard: list[dict]) -> list[tuple[float, float]]:
    """For each script line, when its first and last matched words were heard."""
    flat = [(norm_token(t), i) for i, toks in enumerate(script_tokens) for t in toks]
    sm = difflib.SequenceMatcher(None, [t for t, _ in flat], [norm_token(h["text"]) for h in heard], autojunk=False)
    first: dict[int, float] = {}
    last: dict[int, float] = {}
    for a, b, size in sm.get_matching_blocks():
        for k in range(size):
            line = flat[a + k][1]
            first.setdefault(line, heard[b + k]["start"])
            last[line] = heard[b + k]["end"]
    missing = [i + 1 for i in range(len(script_tokens)) if i not in first]
    if missing:
        raise FilmError("line(s) " + ", ".join(f"L{m:02d}" for m in missing) + " could not be found in the heard words: re-record them, or give a clearer take")
    return [(first[i], last[i]) for i in range(len(script_tokens))]


# ---- word times ---------------------------------------------------------------------------------------------------

def word_times(tokens: list[str], heard: list[dict] | None, t0: float, t1: float) -> list[tuple[float, float]]:
    """A (start, end) for every script word: where it was heard, else spread by length between the words that were."""
    n = len(tokens)
    anchors: list[tuple[float, float] | None] = [None] * n
    if heard:
        sm = difflib.SequenceMatcher(None, [norm_token(t) for t in tokens], [norm_token(h["text"]) for h in heard], autojunk=False)
        for a, b, size in sm.get_matching_blocks():
            for k in range(size):
                anchors[a + k] = (heard[b + k]["start"], heard[b + k]["end"])
    out: list[tuple[float, float]] = [(0.0, 0.0)] * n
    i = 0
    while i < n:
        if anchors[i]:
            out[i] = anchors[i]
            i += 1
            continue
        j = i
        while j < n and not anchors[j]:
            j += 1
        lo = out[i - 1][1] if i else t0
        hi = max(lo, anchors[j][0] if j < n else t1)
        weights = [max(1, len(norm_token(tokens[k]))) + (4 if tokens[k][-1:] in ".!?" else 2 if tokens[k][-1:] in ",;:" else 0) for k in range(i, j)]
        cur = lo
        for k, w in zip(range(i, j), weights):
            nxt = cur + (hi - lo) * w / sum(weights)
            out[k] = (cur, nxt)
            cur = nxt
        i = j
    return out


# ---- recogniser ---------------------------------------------------------------------------------------------------

def parse_whisper(data: dict) -> list[dict]:
    """Words from whisper.cpp's JSON (run with -ml 1 -sow): [{text, start, end}] in seconds."""
    words = []
    for seg in data.get("transcription", []):
        text = (seg.get("text") or "").strip()
        if text and not (text.startswith("[") and text.endswith("]")):
            off = seg.get("offsets") or {}
            words.append({"text": text, "start": off.get("from", 0) / 1000.0, "end": off.get("to", 0) / 1000.0})
    return words


def asr_words(take: Path, words_path: Path | None, model: str | None, notes: list | None = None) -> list[dict] | None:
    """Word timings from a file or a local recogniser; None (with a note) when there is neither."""
    if words_path:
        return lipsync.load_words(Path(words_path))
    model = model or os.environ.get("WHISPER_MODEL")
    tool = shutil.which("whisper-cli")
    if not (tool and model and Path(model).is_file()):
        if notes is not None:
            notes.append("no word timings: pauses alone were used. For short pauses give --words (npx hyperframes transcribe take.wav) "
                         "or a whisper.cpp model (brew install whisper-cpp, then --model path/to/ggml-base.en.bin)")
        return None
    import json
    with tempfile.TemporaryDirectory() as tmp:
        wav, base = Path(tmp) / "t16.wav", Path(tmp) / "out"
        conv = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(take), "-ar", "16000", "-ac", "1", str(wav)], capture_output=True, text=True)
        if conv.returncode != 0:
            if notes is not None:
                notes.append(f"ffmpeg could not make a 16 kHz copy for whisper-cli ({conv.stderr.strip()[-120:]}): pauses alone were used")
            return None
        done = subprocess.run([tool, "-m", model, "-f", str(wav), "-oj", "-of", str(base), "-ml", "1", "-sow"], capture_output=True, text=True)
        if done.returncode != 0 or not base.with_suffix(".json").is_file():
            if notes is not None:
                notes.append(f"whisper-cli failed ({done.stderr.strip()[-120:]}): pauses alone were used")
            return None
        return parse_whisper(json.loads(base.with_suffix(".json").read_text(encoding="utf-8")))


# ---- the split ----------------------------------------------------------------------------------------------------

def _fade(buf: array) -> array:
    n = min(int(FADE * RATE), len(buf) // 2)
    for i in range(n):
        g = i / n
        buf[i] = int(buf[i] * g)
        buf[-1 - i] = int(buf[-1 - i] * g)
    return buf


def write_wav(path: Path, samples: array) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(RATE)
        wf.writeframes(samples.tobytes())


def speech_edges(db: list[float], thr: float, a: int, b: int, ident: str) -> tuple[int, int]:
    loud = [i for i in range(a, min(b, len(db))) if db[i] >= thr]
    if not loud:
        raise FilmError(f"{ident} is silent in the take: re-record it")
    return loud[0], loud[-1] + 1


def plan_cuts(db, thr, script, heard, notes):
    n = len(script.lines)
    sil = cuts_from_pauses(db, thr, n)
    if sil and (heard is None or sil[1] >= SURE_RATIO):
        if sil[1] < 1.3:
            notes.append("some pauses inside lines are about as long as the pauses between lines: check the cuts, or pass --words")
        return sil[0]
    if heard:
        try:
            return cuts_from_words(db, line_spans([words_of(l["say"]) for l in script.lines], heard))
        except FilmError:
            if not sil:
                raise
            notes.append("the heard words did not match the script; the pauses were used instead")
            return sil[0]
    segs = max((len(speech_segments(db, thr, g)) for g in MIN_GAPS), default=0)
    raise FilmError(f"found {segs} spoken stretches, but the script has {n} lines: leave a clear pause (0.4 s or more) between lines, "
                    "or give word timings with --words or --model (see --help)")


def split(take: Path, script_path: Path, out_dir: Path, timings_path: Path, words_path: Path | None = None, model: str | None = None) -> dict:
    script = read_script(script_path)
    samples = read_pcm(take)
    db = levels(samples)
    if len(db) < 20:
        raise FilmError("the take is too short to hold any speech")
    thr = threshold(db)
    notes: list[str] = []
    heard = asr_words(take, words_path, model, notes)
    cuts = [0] + plan_cuts(db, thr, script, heard, notes) + [len(db)]
    base = Path(timings_path).parent
    lines, warnings = [], []
    for k, line in enumerate(script.lines):
        a, b = speech_edges(db, thr, cuts[k], cuts[k + 1], line["id"])
        lo = max(cuts[k] * HOP, a * HOP - PAD_HEAD)
        hi = min(cuts[k + 1] * HOP, b * HOP + PAD_TAIL)
        s0, s1 = int(round(lo * RATE)), int(round(hi * RATE))
        dest = Path(out_dir) / f"{line['id']}.wav"
        write_wav(dest, _fade(array("h", samples[s0:s1])))
        t0, t1 = a * HOP - lo, b * HOP - lo
        tokens = words_of(line["say"])
        hh = [{**w, "start": w["start"] - lo, "end": w["end"] - lo} for w in (heard or []) if lo <= (w["start"] + w["end"]) / 2 <= hi]
        times = word_times(tokens, hh or None, t0, t1)
        duration = (s1 - s0) / RATE
        words = [{"text": t, "start": round(max(0.0, x), 4), "end": round(min(duration, max(y, x + 0.001)), 4)} for t, (x, y) in zip(tokens, times)]
        lines.append({"id": line["id"], "file": Path(os.path.relpath(dest, base)).as_posix(), "duration": round(duration, 4), "speech_start": round(t0, 4),
                      "speech_end": round(t1, 4), "source_start": round(lo, 4), "words": words})
        est = estimate_seconds(line["say"], script.pace)
        if (t1 - t0) > 2.5 * est + 1.0 or (t1 - t0) < 0.3 * est:
            warnings.append(f"{line['id']}: {t1 - t0:.1f} s of speech, but the script suggests {est:.1f} s at {script.pace:g} wpm: check the split")
    save_json(Path(timings_path), {"version": 1, "source": Path(take).name, "rate": RATE, "pace": script.pace, "lines": {l["id"]: l for l in lines},
                                   "order": [l["id"] for l in lines], "notes": notes, "warnings": warnings})
    return {"lines": lines, "warnings": warnings, "notes": notes}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("take", help="the recording (WAV, M4A, MP3, FLAC, MP4 ...)")
    ap.add_argument("script", help="SCRIPT.md")
    ap.add_argument("--out-dir", default="audio/lines")
    ap.add_argument("--timings", default="TIMINGS.json")
    ap.add_argument("--words", help="word timings JSON: a list of {text, start, end} (what `npx hyperframes transcribe` writes)")
    ap.add_argument("--model", help="a whisper.cpp ggml model file for whisper-cli (or set WHISPER_MODEL)")
    args = ap.parse_args(argv)
    try:
        result = split(Path(args.take), Path(args.script), Path(args.out_dir), Path(args.timings), Path(args.words) if args.words else None, args.model)
    except (FilmError, ValueError, OSError) as err:
        print(f"FAIL  split_takes: {err}")
        return 1
    for text in result["notes"]:
        print(f"INFO  {text}")
    for text in result["warnings"]:
        print(f"WARN  {text}")
    total = sum(l["duration"] for l in result["lines"])
    print(f"PASS  {len(result['lines'])} lines cut ({total:.1f} s) -> {args.out_dir}, durations in {args.timings}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
