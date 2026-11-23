"""film_story.py: BRIEF.md to STORY.md: the logline, the audience, the one takeaway, the act structure and the pace.

A brief is free text. A few `key: value` lines in it (title, audience, takeaway, length, format, look, voice, pace) are read as
they are; everything else (the ask) is read for a length ("3-minute", "90 seconds"), a format (documentary, explainer, product,
story), a voice (a recorded take, a generated voice) and a pace. STORY.md is a scaffold written from that: edit it, it is
yours, and film.py never overwrites an edited one unless told to. Standard library only.
"""
from __future__ import annotations

import re
from pathlib import Path

from film_lib import FilmError

FIELDS = ("title", "audience", "takeaway", "length", "format", "look", "voice", "pace")
FORMATS = (("documentary", r"\bdocumentar|\barchive\b"), ("product", r"\bproduct\b|\blaunch\b"), ("story", r"\bstory\b|\bnarrative\b"), ("explainer", r"\bexplain|\bhow\b.*\bwork"))
STRUCTURE = [("Hook", 5.0, "The single most surprising fact or question, on screen and spoken in the first 5 s"),
             ("Setup", 0.12, "Where we are and why it matters: the one thing the viewer needs to follow"),
             ("Beat 1", 0.22, "The first piece of the answer, one picture or map, one number at most"),
             ("Beat 2", 0.22, "The second piece, a change of place or scale so the eye gets something new"),
             ("Beat 3", 0.22, "The third piece, the one that makes the takeaway obvious"),
             ("Turn", 0.10, "The twist, the cost or the surprise that re-hooks the viewer"),
             ("Payoff", None, "The takeaway in one sentence, held still on screen at the end")]


# A length: a number with a unit word, or a bare "s" only after a space ("20 s"), because "50s" and "1950s" are decades. "a documentary about how the 1950s changed television" has no length in it.
LENGTH = r"(?<![\d.])(\d+(?:\.\d+)?)(?:\s*-?\s*(minutes?|mins?|seconds?|secs?)\b|\s+(s)\b)"
# The user's own recording: said outright ("my voice", "my recording", "I will record"), or an audio file named in the brief.
TAKE = r"\bmy (own )?(voice|recording|take)\b|\bi('ll| will)? record\b|\b[\w-]+\.(wav|m4a|mp3|flac)\b"


def parse_brief(text: str) -> dict:
    keyed: dict[str, str] = {}
    prose = []
    for raw in text.splitlines():
        m = re.match(r"^\s*([a-z]+):\s*(.+?)\s*$", raw)
        if m and m.group(1) in FIELDS:
            keyed[m.group(1)] = m.group(2)
        else:
            prose.append(raw)
    ask = " ".join(l.strip() for l in prose if l.strip() and not l.startswith("#"))
    heading = next((re.sub(r"^#+\s*", "", l).strip() for l in prose if l.startswith("#")), "")
    flat = (ask + " " + keyed.get("length", "") + " " + keyed.get("format", "")).lower()
    m = re.search(LENGTH, (keyed.get("length", "") or flat).lower()) or re.search(LENGTH, flat)
    seconds = int(round(float(m.group(1)) * (60 if (m.group(2) or "").startswith("min") else 1))) if m else 180
    fmt = keyed.get("format") or next((name for name, rx in FORMATS if re.search(rx, flat)), "explainer")
    low = text.lower()
    voice = keyed.get("voice") or ("take" if re.search(TAKE, low) else "f5-tts" if re.search(r"generated voice|f5|synthetic voice|cloned voice", low) else "standin")
    pace = float(re.search(r"\d+", keyed["pace"]).group(0)) if "pace" in keyed else (170.0 if re.search(r"\bshort\b|\breel\b|\btiktok\b", low) else 150.0)
    sentence = re.split(r"(?<=[.!?])\s+", ask)[0] if ask else ""
    return {"title": keyed.get("title") or heading or sentence[:80], "ask": ask, "audience": keyed.get("audience", ""), "takeaway": keyed.get("takeaway", ""),
            "seconds": seconds, "format": fmt, "look": keyed.get("look", ""), "voice": voice, "pace": pace, "logline": sentence}


def act_table(seconds: float) -> list[tuple[str, int, int]]:
    """(part, start, end) in whole seconds: a 5 s hook, then shares of the length, the payoff taking what is left."""
    rows, t = [], 0
    for name, share, _ in STRUCTURE:
        if name == "Payoff":
            rows.append((name, t, int(round(seconds))))
            break
        end = t + (int(share) if share >= 1 else max(1, int(round(seconds * share))))
        rows.append((name, t, min(end, int(round(seconds)))))
        t = rows[-1][2]
    return rows


def derive_story(brief_text: str) -> str:
    b = parse_brief(brief_text)
    audience = b["audience"] or "curious viewers who have not met this idea before"
    takeaway = b["takeaway"] or "the one thing a viewer should be able to say after watching (edit this line)"
    lines = [f"# Story: {b['title']}", "", f"logline: {b['logline'] or b['title']}", f"audience: {audience}", f"takeaway: {takeaway}",
             f"format: {b['format']}", f"look: {b['look'] or 'archive-desk'}", f"voice: {b['voice']}", f"length: {b['seconds']} s", f"pace: {b['pace']:g} wpm", "",
             "## Acts", "", "| Part | Seconds | What happens |", "|---|---|---|"]
    guide = {n: g for n, _, g in STRUCTURE}
    lines += [f"| {n} | {a}-{z} s | {guide[n]} |" for n, a, z in act_table(b["seconds"])]
    lines += ["", "## Pacing", "", "A new visual idea every 8-15 s, a re-hook about every 30 s, a pattern interrupt at each chapter change, the strongest move in the "
              "weakest window (references/motion-doctrine.md, section 13). The picture is re-timed to the voice, never the other way round.", "",
              "Derived from BRIEF.md by film.py: edit any line; later stages read this file as it stands."]
    return "\n".join(lines) + "\n"


def read_story_fields(text: str) -> dict:
    return {m.group(1): m.group(2).strip() for m in (re.match(r"^([a-z]+):\s*(.+)$", l) for l in text.splitlines()) if m}


def write_story(brief: Path, story: Path, force: bool = False) -> bool:
    """Write STORY.md from the brief. Returns False (and writes nothing) when one is already there and `force` is not set."""
    brief = Path(brief)
    if not brief.is_file():
        raise FilmError(f"BRIEF.md not found at {brief}: write the brief first (what the film is about, how long, what look, whose voice)")
    if Path(story).exists() and not force:
        return False
    Path(story).write_text(derive_story(brief.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")
    return True
