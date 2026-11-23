"""film_script.py: read SCRIPT.md, estimate how long each line takes, and say which lines have no source.

SCRIPT.md is plain text a person or an agent writes. A few header lines, then one block per narration line:

    # Script
    pace: 150            words a minute (150 for an explainer, 170 for a Short)
    format: explainer

    ## L01
    say: Ninety-nine percent of intercontinental data does not fly. It swims.
    screen: UNDER THE SEA           words shown on screen (kept apart from the narration)
    source: https://example.org/page   a URL (with a host) for every factual line; `none (no factual claim)` for a line
                                       that states nothing checkable ("Then it failed."); left out, the line is UNVERIFIED
    visual: archive                 archive, map, counter or title (default: archive when there is a query or asset)
    query: submarine cable ship     what to search for (archive)
    asset: assets/archive/ship.jpg  or a picture you already have
    date: MARCH 1931                the date stamp
    beat: 2                         lines with the same beat number share one screen

A map beat also takes `region:`, `point: Name=lat,lon` and `route: A>B`. A counter takes `count: 0 -> 1400000 | km of cable`.
A line with no `source:` (or a URL with no host, such as `https://`) is UNVERIFIED: it must be cut or confirmed before render.
`source: none` is an explicit exemption, listed in REPORT.md so a reader can disagree. Standard library only.
"""
from __future__ import annotations

import re
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

from film_lib import FilmError

ID = re.compile(r"^L\d+$")
LIST_KEYS = {"point", "route"}
KEYS = {"say", "screen", "source", "visual", "query", "asset", "date", "beat", "region", "point", "route", "count"}
VISUALS = ("archive", "map", "counter", "title")


@dataclass(frozen=True)
class Script:
    meta: dict
    lines: tuple

    @property
    def pace(self) -> float:
        return float(self.meta.get("pace", 150))


def words_of(text: str) -> list[str]:
    return text.split()


def norm_token(token: str) -> str:
    return re.sub(r"[^0-9a-z]+", "", token.lower())


def estimate_seconds(text: str, wpm: float = 150.0) -> float:
    """Words at the pace, plus 0.3 s for each sentence end and 0.12 s for each comma, colon or semicolon."""
    n = len(words_of(text))
    return round(n * 60.0 / wpm + 0.3 * len(re.findall(r"[.!?](?:\s|$)", text)) + 0.12 * len(re.findall(r"[,;:](?:\s|$)", text)), 3)


def _split_blocks(text: str) -> tuple[list[str], list[tuple[str, list[str]]]]:
    head, blocks, cur = [], [], None
    for raw in text.splitlines():
        m = re.match(r"^##\s+(\S+)\s*$", raw)
        if m:
            cur = (m.group(1), [])
            blocks.append(cur)
        elif cur is not None:
            cur[1].append(raw)
        else:
            head.append(raw)
    return head, blocks


def _parse_fields(lines: list[str], where: str) -> dict:
    fields: dict = {}
    last = None
    for raw in lines:
        text = raw.strip()
        if not text:
            continue
        m = re.match(r"^([a-z]+):\s*(.*)$", text)
        if m and m.group(1) in KEYS:
            last = m.group(1)
            if last in LIST_KEYS:
                fields.setdefault(last, []).append(m.group(2).strip())
            else:
                fields[last] = m.group(2).strip()
        elif last and last not in LIST_KEYS:
            fields[last] = (fields[last] + " " + text).strip()      # a wrapped value continues the line above
        elif m:
            raise FilmError(f"{where}: unknown key '{m.group(1)}' (use {', '.join(sorted(KEYS))})")
        else:
            raise FilmError(f"{where}: cannot read '{text[:50]}': write each field as 'key: value'")
    return fields


def parse_script(text: str) -> Script:
    head, blocks = _split_blocks(text)
    meta = {}
    for raw in head:
        m = re.match(r"^([a-z]+):\s*(.+)$", raw.strip())
        if m:
            meta[m.group(1)] = m.group(2).strip()
    pace = float(meta.get("pace", 150))
    lines = []
    for ident, body in blocks:
        f = _parse_fields(body, f"SCRIPT.md {ident}")
        source = f.get("source", "").strip()
        urls = [u for u in re.split(r"[\s,]+", source) if is_url(u)]
        no_claim = bool(re.match(r"^none\b", source, re.I))
        line = {"id": ident, "say": f.get("say", ""), "screen": f.get("screen", ""), "source": source,
                "sources": urls, "no_claim": no_claim and not urls, "unverified": not urls and not no_claim, "visual": f.get("visual", ""), "query": f.get("query", ""),
                "asset": f.get("asset", ""), "date": f.get("date", ""), "region": f.get("region", ""),
                "points": f.get("point", []), "routes": f.get("route", []), "count": f.get("count", ""),
                "beat": f.get("beat", ""), "words": len(words_of(f.get("say", "")))}
        line["seconds"] = estimate_seconds(line["say"], pace)
        lines.append(line)
    return Script(meta, tuple(lines))


def is_url(text: str) -> bool:
    """An http(s) link with a real host name (a dot in it): `https://` alone, or `https://x`, is not a source."""
    parts = urllib.parse.urlsplit(text.strip())
    return parts.scheme in ("http", "https") and bool(parts.hostname) and "." in (parts.hostname or "")


def read_script(path: Path) -> Script:
    path = Path(path)
    if not path.is_file():
        raise FilmError(f"SCRIPT.md not found at {path}: write it (see film_script.py) or run `film.py script`")
    return parse_script(path.read_text(encoding="utf-8"))


def check_script(script: Script) -> tuple[list[str], list[str]]:
    """(errors, warnings). Errors stop the film; an UNVERIFIED line is a warning here and blocks the render stage."""
    errors, warnings, seen = [], [], set()
    if not script.lines:
        errors.append("SCRIPT.md has no lines: add blocks that start with '## L01'")
    for line in script.lines:
        i = line["id"]
        if not ID.match(i):
            errors.append(f"{i}: line ids look like L01, L02, ...")
        if i in seen:
            errors.append(f"{i}: used twice")
        seen.add(i)
        if not line["say"]:
            errors.append(f"{i}: no 'say:' narration")
        if line["visual"] and line["visual"] not in VISUALS:
            errors.append(f"{i}: visual '{line['visual']}' is not one of {', '.join(VISUALS)}")
        if line["unverified"]:
            warnings.append(f"{i} is UNVERIFIED (no source URL): cut it or confirm it before render")
    return errors, warnings


def unverified(script: Script) -> list[str]:
    return [line["id"] for line in script.lines if line["unverified"]]


def no_claim(script: Script) -> list[str]:
    """Lines marked `source: none`: no factual claim, so no source; REPORT.md lists them."""
    return [line["id"] for line in script.lines if line.get("no_claim")]
