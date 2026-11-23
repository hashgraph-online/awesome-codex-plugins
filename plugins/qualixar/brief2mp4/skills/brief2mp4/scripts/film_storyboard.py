"""film_storyboard.py: SCRIPT.md to STORYBOARD.json: one entry per beat with its lines, picture, camera move, transition and sound.

A beat is one screen. Lines that share a `beat:` number (and sit next to each other) share a beat; every other line is a beat
of its own. Each beat gets:

  kind       archive (a still), map, or title (a typeset statement when there is no picture); a counter and an inset map are
             extras a beat can carry, not kinds
  route      hyperframes:archive-still | hyperframes:map | hyperframes:title (film mode builds every beat with the archive desk template)
  camera     the same speed in every beat (rate, vx, vy), only the point of focus changes: a hard cut then joins two moves of
             one velocity (references/motion-doctrine.md, "velocity-matched cuts"). velocity_problems() checks it.
  transition hard-cut between beats of one act, a dip to dark between acts (time passes), with its meaning written down
  sound      at most three cues (hit, typewriter, whoosh, tick, paper, thud), resolved to film time by retime.py

Durations here are estimates from the script pace; retime.py replaces them with the measured voice. Standard library only.
"""
from __future__ import annotations

import re
from pathlib import Path

sys_path = str(Path(__file__).resolve().parent)
import sys  # noqa: E402

if sys_path not in sys.path:
    sys.path.insert(0, sys_path)
import art_route  # noqa: E402
from film_lib import FilmError  # noqa: E402
from film_script import Script  # noqa: E402

LOOKS = ("archive-desk", "archive desk", "archive", "documentary")
CAMERA = {"rate": 0.014, "vx": -10.0, "vy": -4.0}
FOCI = [(0.42, 0.46), (0.58, 0.50), (0.50, 0.42), (0.46, 0.56)]
GAP_LINE, GAP_BEAT = 0.30, 0.45
ACT_SECONDS = 45.0
MEANING = {"hard-cut": "a new thing in the same place: the camera keeps its speed across the cut",
           "dip": "a chapter change: a short dip to dark says time has passed", "none": "the cold open: nothing before it"}
PRIORITY = ["hit", "thud", "typewriter", "whoosh", "tick", "paper"]
COUNT = re.compile(r"^\s*([\d,._]+)\s*(?:->|→|\bto\b)\s*([\d,._]+)\s*(?:\|\s*(.*))?$")


def _number(text: str) -> float:
    return float(text.replace(",", "").replace("_", ""))


def parse_count(text: str, line_id: str) -> dict:
    m = COUNT.match(text)
    if not m:
        raise FilmError(f"{line_id}: 'count: {text}' should read like 'count: 0 -> 1400000 | km of cable'")
    return {"from": _number(m.group(1)), "to": _number(m.group(2)), "label": (m.group(3) or "").strip(), "line": line_id}


def group_lines(script: Script) -> list[list[dict]]:
    groups: list[list[dict]] = []
    seen: dict[str, int] = {}
    for line in script.lines:
        key = line["beat"]
        if key and groups and seen.get(key) == len(groups) - 1:
            groups[-1].append(line)
            continue
        if key and key in seen:
            raise FilmError(f"beat {key} comes back after another beat ({line['id']}): lines that share a beat number must be next to each other")
        groups.append([line])
        if key:
            seen[key] = len(groups) - 1
    return groups


def _first(lines: list[dict], key: str):
    return next((l[key] for l in lines if l[key]), "" if key not in ("points", "routes") else [])


def _map(lines: list[dict]) -> dict | None:
    region = _first(lines, "region")
    if not region:
        return None
    src = next(l for l in lines if l["region"])
    return {"region": region, "points": list(src["points"]), "routes": list(src["routes"])}


def beat_kind(lines: list[dict], has_picture: bool, has_map: bool) -> str:
    if any(l["visual"] == "title" for l in lines) and not has_picture:
        return "title"
    if has_picture:
        return "archive"
    return "map" if has_map and any(l["visual"] in ("map", "") for l in lines) else "title"


def cues_for(beat: dict, first: bool, last: bool) -> list[dict]:
    want: dict[str, dict] = {}
    if first:
        want["hit"] = {"cue": "hit", "at": "start", "offset": 0.0}
    if last and not first:
        want["thud"] = {"cue": "thud", "at": "start", "offset": 0.0}
    if beat["date"]:
        want["typewriter"] = {"cue": "typewriter", "at": "start", "offset": 0.15}
    if beat["transition"]["type"] == "dip" or (beat["kind"] == "map" and beat["map"] and beat["map"]["routes"]):
        want["whoosh"] = {"cue": "whoosh", "at": "start", "offset": -0.1 if beat["transition"]["type"] == "dip" else 0.5}
    if beat["counter"]:
        want["tick"] = {"cue": "tick", "at": "start", "offset": 0.6}
    if beat["kind"] == "archive" and not first:
        want["paper"] = {"cue": "paper", "at": "start", "offset": 0.0}
    return [want[name] for name in PRIORITY if name in want][:3]


def velocity_problems(sb: dict) -> list[str]:
    """Hard cuts must join two moves of the same speed and direction; a dip may hide a change."""
    problems = []
    for a, b in zip(sb["beats"], sb["beats"][1:]):
        if b["transition"]["type"] != "hard-cut":
            continue
        ca, cb = a["camera"], b["camera"]
        if (ca["rate"], ca["vx"], ca["vy"]) != (cb["rate"], cb["vx"], cb["vy"]):
            problems.append(f"{a['id']} to {b['id']}: a hard cut between camera moves of different velocity (use a dip, or the same rate and drift)")
    return problems


def _acts(beats: list[dict], n: int) -> list[dict]:
    total = sum(b["duration"] for b in beats) or 1.0
    n = max(1, min(n, len(beats)))
    done = 0.0
    for b in beats:
        b["act"] = f"A{min(n - 1, int((done + b['duration'] / 2) / (total / n))) + 1}"
        done += b["duration"]
    names = sorted({b["act"] for b in beats})
    return [{"id": a, "beats": [b["id"] for b in beats if b["act"] == a]} for a in names]


def build_storyboard(script: Script, brief: dict, brief_text: str, fps: int = 30, acts: int | None = None, look: str | None = None) -> dict:
    look = (look or brief.get("look") or "archive-desk").strip().lower()
    if look not in LOOKS:
        raise FilmError(f"film mode builds the archive desk look; '{look}' is not built here. Read references/art-forms/{look.replace(' ', '-')}.md, "
                        "build those beats by hand, then run retime, mix and render from film.py (or use the archive desk for this film)")
    beats, warnings = [], []
    for i, lines in enumerate(group_lines(script)):
        asset = _first(lines, "asset") or None
        query = _first(lines, "query") or None
        mp = _map(lines)
        kind = beat_kind(lines, bool(asset or query), bool(mp))
        caption = " ".join(dict.fromkeys(l["screen"] for l in lines if l["screen"])) or " ".join(re.sub(r"[.,;:!?]+$", "", lines[0]["say"]).split()[:10])
        count_line = next((l for l in lines if l["count"]), None)
        fx, fy = FOCI[i % len(FOCI)]
        est = sum(l["seconds"] for l in lines) + GAP_LINE * (len(lines) - 1) + GAP_BEAT
        beat = {"id": f"B{i + 1:02d}", "act": "A1", "lines": [l["id"] for l in lines], "kind": kind, "route": f"hyperframes:{'archive-still' if kind == 'archive' else kind}",
                "duration": round(est, 3), "asset": asset, "query": query, "map": mp if kind == "map" else None,
                "inset": mp if kind == "archive" and mp else None, "counter": parse_count(count_line["count"], count_line["id"]) if count_line else None,
                "caption": caption, "date": _first(lines, "date"), "art_form": "archive-documentary",
                "camera": {**CAMERA, "fx": fx, "fy": fy, "s0": 0.92 if kind == "map" else 1.08}, "transition": {"type": "hard-cut", "duration": 0.0}}
        if len(caption.split()) > 14 or len(caption) > 100:
            warnings.append(f"{beat['id']}: the on-screen caption is long ({len(caption.split())} words): it must fit two lines at 58 px, so cut it")
        beats.append(beat)
    total_est = sum(b["duration"] for b in beats)
    act_list = _acts(beats, acts if acts else max(1, round(total_est / ACT_SECONDS)))
    for i, b in enumerate(beats):
        if i == 0:
            b["transition"] = {"type": "none", "duration": 0.0}
        elif b["act"] != beats[i - 1]["act"]:
            b["transition"] = {"type": "dip", "duration": 0.4}
        b["transition"]["meaning"] = MEANING[b["transition"]["type"]]
    for i, b in enumerate(beats):
        b["sound"] = cues_for(b, i == 0, i == len(beats) - 1)
    router = art_route.route(brief_text)
    sb = {"version": 1, "title": brief.get("title", ""), "format": script.meta.get("format") or brief.get("format", "explainer"), "look": "archive-desk",
          "art_form": "archive-documentary", "router": {"form": router.get("form"), "why": router.get("why", [])[:2]}, "fps": fps, "size": [1920, 1080],
          "pace": script.pace, "acts": act_list, "beats": beats, "duration": round(total_est, 3), "retimed": False, "warnings": warnings}
    for problem in velocity_problems(sb):
        warnings.append(problem)
    return sb
