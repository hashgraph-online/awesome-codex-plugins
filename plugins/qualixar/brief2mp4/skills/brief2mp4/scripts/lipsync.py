#!/usr/bin/env python3
"""lipsync.py: turn word timestamps (or, failing that, a WAV file) into a mouth-shape track for the character rig.

    python3 lipsync.py words.json                      # word timestamps -> [{"t": 3.4, "v": "AI"}, ...]
    python3 lipsync.py words.json --lang hi --fps 24   # romanised Hindi, best effort
    python3 lipsync.py --wav voice.wav                 # no timestamps: open, half-open and closed mouth from loudness
    python3 lipsync.py words.json --from 3.2 --to 6.0 --out visemes.json   # only the words in a time range

Input is what `npx hyperframes transcribe voice.wav` writes: a list of {"text", "start", "end"} words (an object
with a "words" list also works). Output is a list of {"t", "v"} keys; a mouth shape holds until the next key. The
nine shapes are rest, AI, E, O, U, MBP, FV, L and etc (every other consonant).

How a word becomes shapes: letter rules (digraphs first, then single letters) with a small table of exceptions,
spread across the word's time in proportion to how long each sound takes (vowels longest). The mouth closes
("rest") in a pause longer than 150 ms, and no shape is held for less than one frame at --fps: every key is snapped
to the frame grid, a shape that would be shorter is merged into its neighbour, and a word too short for all its
shapes drops the weakest consonants first. Words that overlap (speech-to-text often gives them) are cut at the next
word's start, so the track never goes backwards. English rules are tuned for English; Devanagari is read letter by
letter (vowel signs to AI, E, O or U, pa ba bha ma to MBP, pha va to FV, la to L, the rest to etc), accented Latin
letters are folded (café reads as cafe), and a word with no letters it knows is reported on stderr instead of vanishing; --lang hi reads romanised Hindi
(aa, ee, oo, kh, bh and so on) and is approximate: it is a mouth, not a phonetic transcription. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import operator
import re
import sys
import unicodedata
import wave
from array import array
from pathlib import Path

VISEMES = ("rest", "AI", "E", "O", "U", "MBP", "FV", "L", "etc")
VOWEL_WEIGHT, CONSONANT_WEIGHT = 2.0, 0.8
PAUSE_CLOSE = 0.15           # a gap longer than this closes the mouth

# Words the letter rules get wrong, as the shapes you see when they are said.
EXCEPTIONS = {
    "the": ["L", "E"], "a": ["AI"], "i": ["AI"], "you": ["etc", "U"], "your": ["etc", "O", "etc"], "one": ["U", "etc"], "once": ["U", "etc"],
    "two": ["etc", "U"], "to": ["etc", "U"], "do": ["etc", "U"], "who": ["U"], "whose": ["U", "etc"], "what": ["U", "AI", "etc"], "was": ["U", "AI", "etc"],
    "were": ["U", "E"], "said": ["etc", "E", "etc"], "are": ["AI", "etc"], "of": ["O", "FV"], "love": ["L", "AI", "FV"], "some": ["etc", "AI", "MBP"],
    "come": ["etc", "AI", "MBP"], "give": ["etc", "E", "FV"], "have": ["etc", "AI", "FV"], "my": ["MBP", "AI"], "me": ["MBP", "E"], "we": ["U", "E"],
    "she": ["etc", "E"], "he": ["etc", "E"], "be": ["MBP", "E"], "no": ["etc", "O"], "so": ["etc", "O"], "go": ["etc", "O"], "hey": ["etc", "E"],
    "kite": ["etc", "AI", "etc"], "little": ["L", "E", "etc", "L"], "one's": ["U", "etc"], "water": ["U", "O", "etc", "E"], "mister": ["MBP", "E", "etc", "etc", "E"],
}

DIGRAPHS = [   # (letters, shapes), longest first
    ("tch", ["etc"]), ("sch", ["etc"]), ("igh", ["AI"]), ("ough", ["O"]), ("eigh", ["E"]), ("th", ["L"]), ("sh", ["etc"]), ("ch", ["etc"]), ("zh", ["etc"]),
    ("ph", ["FV"]), ("gh", []), ("ng", ["etc"]), ("ck", ["etc"]), ("qu", ["etc", "U"]), ("wh", ["U"]), ("kn", ["etc"]), ("wr", ["etc"]),
    ("oo", ["U"]), ("ou", ["O"]), ("ow", ["O"]), ("oa", ["O"]), ("oi", ["O"]), ("oy", ["O"]), ("ee", ["E"]), ("ea", ["E"]), ("ie", ["E"]), ("ey", ["E"]),
    ("ai", ["AI"]), ("ay", ["AI"]), ("au", ["O"]), ("aw", ["O"]), ("ew", ["U"]), ("ue", ["U"]), ("ar", ["AI", "etc"]), ("or", ["O", "etc"]),
]
HINDI_DIGRAPHS = [
    ("chh", ["etc"]), ("aa", ["AI"]), ("ee", ["E"]), ("ii", ["E"]), ("oo", ["U"]), ("uu", ["U"]), ("ai", ["E"]), ("au", ["O"]), ("kh", ["etc"]), ("gh", ["etc"]),
    ("ch", ["etc"]), ("jh", ["etc"]), ("th", ["etc"]), ("dh", ["etc"]), ("sh", ["etc"]), ("ph", ["MBP"]), ("bh", ["MBP"]), ("ng", ["etc"]),
]
SINGLE = {"a": "AI", "e": "E", "i": "E", "o": "O", "u": "AI", "b": "MBP", "m": "MBP", "p": "MBP", "f": "FV", "v": "FV", "l": "L", "w": "U", "q": "etc", "y": "E"}
SINGLE_HI = {"a": "AI", "e": "E", "i": "E", "o": "O", "u": "U", "b": "MBP", "m": "MBP", "p": "MBP", "f": "FV", "v": "FV", "l": "L", "w": "U", "y": "E"}


def _is_vowel(shape: str) -> bool:
    return shape in ("AI", "E", "O", "U")


DEV_VOWELS = {"अ": "AI", "आ": "AI", "इ": "E", "ई": "E", "उ": "U", "ऊ": "U", "ऋ": "E", "ऍ": "E", "ए": "E", "ऐ": "E", "ऑ": "O", "ओ": "O", "औ": "O"}
DEV_SIGNS = {"ा": "AI", "ि": "E", "ी": "E", "ु": "U", "ू": "U", "ृ": "E", "ॅ": "E", "े": "E", "ै": "E", "ॉ": "O", "ो": "O", "ौ": "O"}
DEV_VIRAMA, DEV_NUKTA = "्", "़"
DEV_LIPS, DEV_TEETH, DEV_L = set("पबभम"), set("फव") | {"\u095e"}, set("लळ")
DEV_CONSONANTS = set("कखगघङचछजझञटठडढणतथदधनयरशषसह") | {chr(c) for c in range(0x0958, 0x0960)}


def _is_dev(ch: str) -> bool:
    return "\u0900" <= ch <= "\u097f"


def _dev_shapes(word: str) -> list[str]:
    """One Devanagari word to shapes. A consonant carries an inherent short a unless a vowel sign or a virama follows,
    and that a is not said at the end of a word (namaste, not namastea)."""
    out, i, n = [], 0, len(word)
    while i < n:
        ch = word[i]
        if ch in DEV_VOWELS:
            out.append(DEV_VOWELS[ch])
        elif ch in DEV_CONSONANTS or ch in DEV_LIPS | DEV_TEETH | DEV_L:
            out.append("MBP" if ch in DEV_LIPS else "FV" if ch in DEV_TEETH else "L" if ch in DEV_L else "etc")
            j = i + 1
            while j < n and word[j] == DEV_NUKTA:
                j += 1
            if j < n and word[j] in DEV_SIGNS:
                out.append(DEV_SIGNS[word[j]])
                j += 1
            elif j < n and word[j] == DEV_VIRAMA:
                j += 1
            elif any(c in DEV_VOWELS or c in DEV_CONSONANTS or c in DEV_LIPS | DEV_TEETH | DEV_L for c in word[j:]):
                out.append("AI")
            i = j - 1
        i += 1
    return out


def _fold(text: str) -> str:
    """Accented Latin letters lose their accents (café -> cafe, señor -> senor); other scripts are left as they are."""
    return "".join(ch if ord(ch) < 0x80 or _is_dev(ch) else "".join(c for c in unicodedata.normalize("NFKD", ch) if not unicodedata.combining(c)) for ch in text)


def _shapes_for(word: str, lang: str) -> list[str]:
    """Letters to mouth shapes, in order. Empty if the word has no letters it knows (a bare number or punctuation)."""
    runs = re.findall(r"[\u0900-\u097f]+|[^\u0900-\u097f]+", _fold(word))
    if len(runs) > 1 or (runs and _is_dev(runs[0][0])):
        out: list[str] = []
        for run in runs:
            out += _dev_shapes(run) if _is_dev(run[0]) else _latin_shapes(run, lang)
        return [s for n, s in enumerate(out) if n == 0 or s != out[n - 1]]
    return _latin_shapes(runs[0], lang) if runs else []


def _latin_shapes(word: str, lang: str) -> list[str]:
    letters = re.sub(r"[^a-z]", "", word.lower().replace("'", ""))
    if not letters:
        return []
    if lang == "en" and letters in EXCEPTIONS:
        return list(EXCEPTIONS[letters])
    table, single = (HINDI_DIGRAPHS, SINGLE_HI) if lang == "hi" else (DIGRAPHS, SINGLE)
    if lang == "hi" and len(letters) > 2 and letters.endswith("a") and not letters.endswith("aa"):
        letters = letters[:-1]       # a final schwa is usually not said: "namaste", "bahut"
    elif lang == "en" and len(letters) > 3 and letters.endswith("e") and letters[-2] not in "aeiouly":
        letters = letters[:-1]       # a silent final e: "make", "kite"
    out, i = [], 0
    while i < len(letters):
        hit = next(((k, v) for k, v in table if letters.startswith(k, i)), None)
        if hit:
            out += hit[1]
            i += len(hit[0])
            continue
        ch = letters[i]
        shape = single.get(ch, "etc")
        if ch == "i" and lang == "en" and (letters[i + 1:i + 3] in ("nd", "ld", "gh") or i == len(letters) - 1):
            shape = "AI"
        if ch == "y" and lang == "en":
            shape = "AI" if (i == len(letters) - 1 and len(letters) <= 3) else "etc" if i == 0 else "E"
        out.append(shape)
        i += 1
    return [s for n, s in enumerate(out) if n == 0 or s != out[n - 1]]      # "ll", "mm", "pp" are one shape


def _allocate(shapes: list[str], start: float, end: float, min_dur: float) -> list[tuple[float, str]]:
    """Spread a word's shapes over its time. Each gets at least min_dur; the rest is shared by how long the sound is."""
    shapes = shapes[:]
    room = max(1, int((end - start) / min_dur + 1e-9))
    while len(shapes) > room:           # no room for every shape: drop the weakest consonant, else the last
        weak = [n for n, s in enumerate(shapes) if s == "etc"] or [n for n, s in enumerate(shapes) if not _is_vowel(s)] or [len(shapes) - 1]
        shapes.pop(weak[0])
    weights = [VOWEL_WEIGHT if _is_vowel(s) else CONSONANT_WEIGHT for s in shapes]
    spare = max(0.0, (end - start) - min_dur * len(shapes))
    t, out = start, []
    for s, w in zip(shapes, weights):
        out.append((t, s))
        t += min_dur + spare * w / sum(weights)
    return out


def _tidy(keys: list[tuple[float, str]], end: float, fps: float) -> list[dict]:
    """Snap every key to the frame grid, fold shapes shorter than a frame into their neighbours, drop repeats."""
    frame = 1.0 / fps
    if any(b[0] < a[0] - 1e-9 for a, b in zip(keys, keys[1:])):
        raise ValueError("mouth keys must be in time order; got " + ", ".join(f"{t:.3f}" for t, _ in keys[:8]))
    snapped: list[tuple[int, str]] = []
    for t, v in keys:
        n = int(round(t * fps))
        if snapped and snapped[-1][0] == n:
            snapped[-1] = (n, v)            # two keys on one frame: the later one wins
        else:
            snapped.append((n, v))
    out: list[tuple[int, str]] = []
    for n, v in snapped:
        if out and out[-1][1] == v:
            continue
        out.append((n, v))
    end_n = max(int(round(end * fps)), out[-1][0] + 1) if out else 0
    return [{"t": round(n * frame, 4), "v": v} for n, v in out] + ([{"t": round(end_n * frame, 4), "v": "rest"}] if out and out[-1][1] != "rest" else [])


def build_track(words: list[dict], fps: float = 30.0, lang: str = "en", skipped: list[str] | None = None) -> list[dict]:
    """Word timestamps to a viseme track. The mouth is closed before the first word, in pauses over 150 ms and after
    the last. Words are taken in time order and a word that runs into the next is cut at the next one's start. Words
    with no letters the rules know are left out and their text is added to `skipped` when you pass a list."""
    ordered = sorted((w for w in words if w["end"] > w["start"]), key=lambda w: (w["start"], w["end"]))
    min_dur, keys, last_end = 1.0 / fps, [], 0.0
    for i, w in enumerate(ordered):
        nxt = ordered[i + 1]["start"] if i + 1 < len(ordered) else None
        end = w["end"] if nxt is None else min(w["end"], nxt)
        shapes = _shapes_for(w["text"], lang)
        if not shapes:
            if skipped is not None:
                skipped.append(w["text"])
            continue
        if end <= w["start"]:
            continue                                  # two words starting together: the later one is kept
        keys += _allocate(shapes, w["start"], end, min_dur)
        last_end = end
        if nxt is None or nxt - end > PAUSE_CLOSE:
            keys.append((end, "rest"))
    if not keys:
        return []
    return _tidy([(max(0.0, keys[0][0] - min_dur), "rest")] + keys, last_end, fps)


def load_words(path: Path) -> list[dict]:
    """Read the word list `hyperframes transcribe` writes (a list, or an object holding "words" or "segments")."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("words") or [w for seg in data.get("segments", []) if isinstance(seg, dict) for w in seg.get("words", [])]
    if not isinstance(data, list):
        raise ValueError(f"{path}: expected a list of {{\"text\", \"start\", \"end\"}} words, got {type(data).__name__}")
    out = []
    for i, w in enumerate(data):
        if not isinstance(w, dict):
            raise ValueError(f"word {i} must be an object with text, start and end, got {json.dumps(w)}")
        text, start, end = w.get("text", w.get("word")), w.get("start", w.get("t0")), w.get("end", w.get("t1"))
        if text is None or start is None or end is None:
            raise ValueError(f"word {i} needs text, start and end: {json.dumps(w)}")
        try:
            out.append({"text": str(text), "start": float(start), "end": float(end)})
        except (TypeError, ValueError):
            raise ValueError(f"word {i} has a start or end that is not a number: {json.dumps(w)}") from None
    return out


def _samples(path: Path) -> tuple[array | list, int, float]:
    """The samples of a PCM WAV file as one channel, the sample rate and the full-scale value of the samples."""
    with wave.open(str(path), "rb") as wf:
        width, rate, chans, frames = wf.getsampwidth(), wf.getframerate(), wf.getnchannels(), wf.getnframes()
        raw = wf.readframes(frames)
    if width == 2:
        data, full = array("h"), 32768.0
        data.frombytes(raw[:len(raw) - len(raw) % 2])
        if sys.byteorder == "big":
            data.byteswap()
    elif width == 1:
        data, full = [b - 128 for b in raw], 128.0
    elif width == 3:
        data, full = [int.from_bytes(raw[i:i + 3], "little", signed=True) for i in range(0, len(raw) - 2, 3)], 8388608.0
    elif width == 4:
        data, full = array("i"), 2147483648.0
        data.frombytes(raw[:len(raw) - len(raw) % 4])
    else:
        raise ValueError(f"unsupported sample width {width}")
    if chans > 1:
        data = [sum(data[i:i + chans]) / chans for i in range(0, len(data) - chans + 1, chans)]
    return data, rate, full


def amplitude_samples(samples, rate: int, fps: float = 30.0, full: float = 32768.0) -> list[dict]:
    """An open, half-open or closed mouth for every video frame from how loud the voice is in it. Frame i covers
    the samples from i * rate / fps on and its key is timed at i / fps, however awkward the rate (22050 Hz at 60 fps
    is 367.5 samples a frame), so the track does not drift."""
    hop = rate / fps
    count = int(len(samples) / hop)
    rms = []
    for i in range(count):
        chunk = samples[int(round(i * hop)):int(round((i + 1) * hop))]
        rms.append((sum(map(operator.mul, chunk, chunk)) / max(1, len(chunk))) ** 0.5 / full)
    if not rms:
        return []
    peak = sorted(rms)[int(0.95 * (len(rms) - 1))]
    floor = max(0.004, 0.08 * peak)
    shapes = ["rest" if r < floor else "etc" if r < 0.45 * peak else "AI" for r in rms]
    return _tidy([(i / fps, s) for i, s in enumerate(shapes)], len(rms) / fps, fps)


def amplitude_track(path: Path, fps: float = 30.0) -> list[dict]:
    """No word timestamps: an open, half-open or closed mouth from how loud the voice is in each frame."""
    try:
        data, rate, full = _samples(Path(path))
    except wave.Error as exc:
        raise ValueError(f"{path}: not a PCM WAV file ({exc}). Convert it first: ffmpeg -i in.mp3 -ar 48000 out.wav") from exc
    return amplitude_samples(data, rate, fps, full)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("words", nargs="?", help="word timestamps JSON from `npx hyperframes transcribe`")
    ap.add_argument("--wav", help="no timestamps: use the loudness of this WAV file instead")
    ap.add_argument("--fps", type=float, default=30.0, help="the video's frame rate (default 30)")
    ap.add_argument("--lang", choices=("en", "hi"), default="en", help="en, or hi for romanised Hindi (approximate)")
    ap.add_argument("--from", dest="t0", type=float, help="only words starting at or after this time (seconds)")
    ap.add_argument("--to", dest="t1", type=float, help="only words starting before this time (seconds)")
    ap.add_argument("--out", help="write the track here instead of printing it")
    args = ap.parse_args(argv)
    if not args.words and not args.wav:
        ap.error("give a words JSON file, or --wav FILE")
    if args.fps <= 0:
        ap.error("--fps must be above 0")
    try:
        if args.words:
            words = [w for w in load_words(Path(args.words)) if (args.t0 is None or w["start"] >= args.t0) and (args.t1 is None or w["start"] < args.t1)]
            skipped: list[str] = []
            track = build_track(words, args.fps, args.lang, skipped)
            for text in skipped:
                print(f'lipsync.py: warning: no mouth shapes for "{text}" (no letters the rules know); it is left out', file=sys.stderr)
            if not track:
                print("lipsync.py: " + ("no words in that range" if not words else f"no mouth shapes for any of the {len(words)} word(s)") + "; "
                      "if the language is not covered, build the track from loudness instead: lipsync.py --wav voice.wav", file=sys.stderr)
                return 2
        else:
            track = amplitude_track(Path(args.wav), args.fps)
    except (OSError, ValueError, KeyError) as exc:
        print(f"lipsync.py: {exc}", file=sys.stderr)
        return 2
    text = json.dumps(track, indent=1)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8", newline="\n")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
