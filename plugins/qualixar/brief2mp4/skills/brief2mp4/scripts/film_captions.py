"""film_captions.py: word-timed captions from the measured voice: an SRT file and a list of cues the template can burn in.

Words come from TIMINGS.json (the same timings lip sync reads) placed on the film timeline by the re-timed storyboard. Two to
seven words per caption, broken at the end of a sentence or a clause, never across two voice lines, at most two lines of about
32 characters, each shown at least 0.4 s and never over the next. Standard library only.
"""
from __future__ import annotations

import re

END_SENTENCE, END_CLAUSE = ".!?", ",;:—-"
MAX_WORDS, MAX_CHARS, MIN_SHOW = 7, 42, 0.4


def _break_after(word: str, count: int) -> bool:
    last = word.rstrip("\"')”’")[-1:]
    return (last in END_SENTENCE and count >= 2) or (last in END_CLAUSE and count >= 3) or count >= MAX_WORDS


def _groups(words: list[dict]) -> list[list[dict]]:
    out, cur = [], []
    for w in words:
        cur.append(w)
        text = " ".join(x["text"] for x in cur)
        if _break_after(w["text"], len(cur)) or len(text) > MAX_CHARS:
            out.append(cur)
            cur = []
    if cur:
        if out and len(out[-1]) + len(cur) <= MAX_WORDS and len(cur) == 1:
            out[-1] += cur
        else:
            out.append(cur)
    return out


def two_lines(text: str, width: int = 32) -> str:
    if len(text) <= width:
        return text
    words = text.split()
    best = min(range(1, len(words)), key=lambda i: abs(len(" ".join(words[:i])) - len(" ".join(words[i:]))))
    return " ".join(words[:best]) + "\n" + " ".join(words[best:])


def caption_cues(sb: dict, timings: dict) -> list[dict]:
    cues = []
    for beat in sb["beats"]:
        for lid in beat.get("lines", []):
            base = beat["line_starts"][lid]
            words = [{"text": w["text"], "start": base + w["start"], "end": base + w["end"]} for w in timings["lines"][lid]["words"]]
            for g in _groups(words):
                cues.append({"start": g[0]["start"], "end": g[-1]["end"] + 0.05, "text": " ".join(w["text"] for w in g), "line": lid})
    for i, c in enumerate(cues):
        nxt = cues[i + 1]["start"] - 0.02 if i + 1 < len(cues) else c["end"] + 1
        c["end"] = round(min(max(c["end"], c["start"] + MIN_SHOW), max(nxt, c["start"] + 0.1)), 3)
        c["start"] = round(c["start"], 3)
    return cues


def srt_time(t: float) -> str:
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def to_srt(cues: list[dict]) -> str:
    return "".join(f"{i}\n{srt_time(c['start'])} --> {srt_time(c['end'])}\n{two_lines(c['text'])}\n\n" for i, c in enumerate(cues, 1))


def parse_srt(text: str) -> list[dict]:
    out = []
    for block in re.split(r"\n\s*\n", text.strip()):
        m = re.search(r"(\d+):(\d+):(\d+),(\d+) --> (\d+):(\d+):(\d+),(\d+)\n(.+)", block, re.S)
        if m:
            g = [int(x) for x in m.groups()[:8]]
            out.append({"start": g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000, "end": g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000, "text": m.group(9).replace("\n", " ")})
    return out
