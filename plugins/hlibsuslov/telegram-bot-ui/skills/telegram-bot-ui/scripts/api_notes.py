#!/usr/bin/env python3
"""Agent notes: the curated layer over the Bot API catalog, and the short card built from both.

The catalog (data/bot-api/catalog.json) says what a method or type is: fields, types, the official text.
A note (data/bot-api/agent-notes/<domain>.json, one file per domain) adds what an agent needs at the
moment of the call and the catalog cannot say: purpose in one line, when to use it and when not, pitfalls
with their source, related symbols, rights and chat types, the release it arrived in, the reference
section that teaches it and a checked example. `card()` merges catalog, note and example into one text
of at most 1.5 KB (plus a one-line REVIEW warning while a note waits for a re-check); a symbol
without a note gets a catalog-only card that says so.

File shape:
  {"domain": "<file stem>", "notes": {"<Symbol>": {
      "purpose": "one line", "use_when": [...], "avoid_when": [...],
      "pitfalls": [{"text": "...", "source": "API|Official|Observed|Heuristic|Unverified|Third-party",
                    "cite": "quote, URL or client+date (optional only for Heuristic/Unverified)"}],
      "related": ["<Symbol>", ...], "rights": "...", "chat_types": ["private", ...], "since": "10.4",
      "refs": ["references/<file>.md#<anchor>", ...], "example": "examples/payloads/<file>.json",
      "review": true}}}
`review` is set by `sync_bot_api.py` when the catalog entry changed after the note was written.

  py -3 scripts/api_notes.py check          # validate every note against the catalog and the files
"""
from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
NOTES_DIR = os.path.join(SKILL_DIR, "data", "bot-api", "agent-notes")
CARD_LIMIT = 1536
PURPOSE_LIMIT = 200
FIELDS = {"purpose", "use_when", "avoid_when", "pitfalls", "related", "rights", "chat_types", "since", "refs",
          "example", "review"}
PITFALL_FIELDS = {"text", "source", "cite"}
SOURCES = {"API", "Official", "Observed", "Heuristic", "Unverified", "Third-party"}
UNCITED_SOURCES = {"Heuristic", "Unverified"}
CHAT_TYPES = ("private", "group", "supergroup", "channel", "business")
VERSION_RE = re.compile(r"^\d+\.\d+$")
REF_ROOTS = ("references/", "recipes/")


def load_files(notes_dir: str = NOTES_DIR) -> list[tuple[str, dict]]:
    """(path, parsed JSON) of every domain file, sorted by name."""
    if not os.path.isdir(notes_dir):
        return []
    out = []
    for name in sorted(os.listdir(notes_dir)):
        if name.endswith(".json"):
            path = os.path.join(notes_dir, name)
            with open(path, encoding="utf-8") as fh:
                out.append((path, json.load(fh)))
    return out


def index(files: list[tuple[str, dict]]) -> dict[str, dict]:
    """Symbol -> note across every domain file (the first file wins; `validate` reports duplicates).
    A file without a "notes" object is skipped, so one broken file never breaks unrelated lookups;
    their cards fall back to the catalog and `check` reports the file."""
    notes: dict[str, dict] = {}
    for _, data in files:
        for symbol, note in _notes_of(data).items():
            notes.setdefault(symbol, note)
    return notes


def _notes_of(data) -> dict:
    notes = data.get("notes") if isinstance(data, dict) else None
    return notes if isinstance(notes, dict) else {}


def load_notes(notes_dir: str = NOTES_DIR) -> dict[str, dict]:
    return index(load_files(notes_dir))


def _inside(skill_dir: str, rel: str) -> str | None:
    """Absolute path of a skill-relative path, or None when it climbs (`..`) or a link leads out of the skill."""
    if not isinstance(rel, str) or not rel or os.path.isabs(rel) or "\\" in rel or ".." in rel.split("/"):
        return None
    root = os.path.realpath(skill_dir)
    path = os.path.realpath(os.path.join(skill_dir, *rel.split("/")))
    return path if os.path.commonpath([root, path]) == root else None


def _anchors(path: str) -> set[str]:
    from validate_references import parse_headings, split_front_matter
    with open(path, encoding="utf-8") as fh:
        _, body = split_front_matter(fh.read())
    return {h[3] for h in parse_headings(body)}


def snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def example_step(path: str, method: str) -> dict | None:
    """The first recorded request for `method` in a payload file, or None."""
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError):
        return None
    steps = doc.get("steps", []) if isinstance(doc, dict) else doc if isinstance(doc, list) else []
    return next((s for s in steps if isinstance(s, dict) and s.get("method") == method
                 and isinstance(s.get("params"), dict)), None)


def _strings(value) -> bool:
    return isinstance(value, list) and all(isinstance(v, str) and v.strip() for v in value)


def validate(files: list[tuple[str, dict]], catalog: dict, skill_dir: str = SKILL_DIR,
             versions: set[str] | None = None) -> list[str]:
    """Every problem in the notes: shape, unknown symbols, dead refs, missing examples, oversized cards."""
    problems: list[str] = []
    symbols = {**catalog["methods"], **catalog["types"]}
    seen: dict[str, str] = {}
    anchor_cache: dict[str, set[str]] = {}
    for path, data in files:
        where = os.path.basename(path)
        if not isinstance(data, dict):
            problems.append(f"{where}: not a JSON object")
            continue
        for key in set(data) - {"$comment", "domain", "notes"}:
            problems.append(f"{where}: unknown top-level field {key!r}")
        if data.get("domain") != where[:-5]:
            problems.append(f"{where}: \"domain\" must be {where[:-5]!r}")
        notes = data.get("notes")
        if not isinstance(notes, dict):
            problems.append(f"{where}: \"notes\" must be an object of Symbol -> note")
            continue
        for symbol, note in notes.items():
            at = f"{where}: {symbol}"
            before = len(problems)
            if symbol in seen:
                problems.append(f"{at}: also noted in {seen[symbol]}")
            seen[symbol] = where
            if symbol not in symbols:
                problems.append(f"{at}: not in the Bot API catalog (check the exact case)")
                continue
            if not isinstance(note, dict):
                problems.append(f"{at}: note must be an object")
                continue
            problems += [f"{at}: unknown field {k!r}" for k in sorted(set(note) - FIELDS)]
            purpose = note.get("purpose")
            if not isinstance(purpose, str) or not purpose.strip():
                problems.append(f"{at}: \"purpose\" is required (one line)")
            elif len(purpose) > PURPOSE_LIMIT or "\n" in purpose:
                problems.append(f"{at}: \"purpose\" must be one line of at most {PURPOSE_LIMIT} characters")
            for key in ("use_when", "avoid_when"):
                if key in note and not _strings(note[key]):
                    problems.append(f"{at}: \"{key}\" must be a list of non-empty strings")
            for i, pit in enumerate(note.get("pitfalls", []) if isinstance(note.get("pitfalls", []), list) else [None]):
                if not isinstance(pit, dict):
                    problems.append(f"{at}: pitfalls[{i}] must be an object")
                    continue
                problems += [f"{at}: pitfalls[{i}] unknown field {k!r}" for k in sorted(set(pit) - PITFALL_FIELDS)]
                if not isinstance(pit.get("text"), str) or not pit["text"].strip():
                    problems.append(f"{at}: pitfalls[{i}] needs \"text\"")
                if not isinstance(pit.get("source"), str) or pit["source"] not in SOURCES:
                    problems.append(f"{at}: pitfalls[{i}] \"source\" must be one of {', '.join(sorted(SOURCES))}")
                elif pit["source"] not in UNCITED_SOURCES and not (isinstance(pit.get("cite"), str) and pit["cite"].strip()):
                    problems.append(f"{at}: pitfalls[{i}] needs \"cite\" (official quote, URL or client and date)")
            related = note.get("related", [])
            if not _strings(related) and related != []:
                problems.append(f"{at}: \"related\" must be a list of symbol names")
            else:
                problems += [f"{at}: related {r!r} is not in the catalog" for r in related if r not in symbols]
                if symbol in related:
                    problems.append(f"{at}: related lists the symbol itself")
            if "rights" in note and not (isinstance(note["rights"], str) and note["rights"].strip()):
                problems.append(f"{at}: \"rights\" must be a non-empty string")
            chats = note.get("chat_types", [])
            if not isinstance(chats, list) or any(c not in CHAT_TYPES for c in chats):
                problems.append(f"{at}: \"chat_types\" must be a list of {', '.join(CHAT_TYPES)}")
            if "since" in note:
                since = note["since"]
                if not isinstance(since, str) or not VERSION_RE.match(since):
                    problems.append(f"{at}: \"since\" must be a version like \"10.4\"")
                elif versions and since not in versions:
                    problems.append(f"{at}: \"since\" {since} is not a release in the changelog")
            if "review" in note and not isinstance(note["review"], bool):
                problems.append(f"{at}: \"review\" must be true or false")
            refs = note.get("refs", [])
            if not isinstance(refs, list):
                problems.append(f"{at}: \"refs\" must be a list")
                refs = []
            for ref in refs:
                rel, _, anchor = ref.partition("#") if isinstance(ref, str) else ("", "", "")
                target = _inside(skill_dir, rel)
                if not rel.startswith(REF_ROOTS) or not rel.endswith(".md") or target is None:
                    problems.append(f"{at}: ref {ref!r} must be references/<file>.md#anchor or recipes/<file>.md")
                elif not os.path.isfile(target):
                    problems.append(f"{at}: ref {ref!r}: no such file")
                elif anchor:
                    if target not in anchor_cache:
                        anchor_cache[target] = _anchors(target)
                    if anchor not in anchor_cache[target]:
                        problems.append(f"{at}: ref {ref!r}: no heading with that anchor")
            if "example" in note:
                problems += [f"{at}: {p}" for p in _check_example(skill_dir, note["example"], symbol,
                                                                  symbols[symbol]["kind"])]
            if len(problems) > before:
                continue  # a malformed note is reported, not rendered
            # The authored card must fit; a REVIEW line that a sync adds is allowed on top of it.
            text = card(symbols[symbol], {**note, "review": False}, catalog.get("meta", {}), skill_dir=skill_dir)
            size = len(text.encode("utf-8"))
            if size > CARD_LIMIT:
                problems.append(f"{at}: card is {size} bytes, the limit is {CARD_LIMIT}; shorten the note")
    return problems


def _check_example(skill_dir: str, rel, symbol: str, kind: str) -> list[str]:
    target = _inside(skill_dir, rel)
    if target is None or not rel.startswith("examples/"):
        return [f"example {rel!r} must be a path under examples/"]
    if not os.path.isfile(target):
        return [f"example {rel!r}: no such file"]
    if kind != "method":
        return []
    if rel.endswith(".json"):
        return [] if example_step(target, symbol) else [f"example {rel!r} records no {symbol} request"]
    with open(target, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    names = "|".join(re.escape(n) for n in (symbol, snake(symbol)))
    called = re.search(rf"[\"'](?:{names})[\"']|(?<![A-Za-z0-9_])(?:{names})\s*\(", text)
    return [] if called else [f"example {rel!r} never calls {symbol} (a quoted method name or a call)"]


# ------------------------------------------------------------------ card

def _first_sentence(text: str, limit: int = 200) -> str:
    m = re.match(r"(.+?\.)(\s|$)", text or "")
    s = m.group(1) if m else (text or "")
    return s if len(s) <= limit else s[: limit - 1] + "…"


def _compact(value, limit: int) -> str:
    s = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return s if len(s) <= limit else s[: limit - 1] + "…"


def card(sym: dict, note: dict | None, meta: dict, skill_dir: str = SKILL_DIR) -> str:
    """Catalog + note + example in at most CARD_LIMIT bytes. Optional field names are cut to fit."""
    is_method = sym["kind"] == "method"
    rows = sym.get("parameters" if is_method else "fields") or []
    since = (note or {}).get("since")
    head = f"{sym['name']} · {sym['kind']} · {sym.get('section', '')} · Bot API {meta.get('bot_api_version', '?')}"
    lines = [head + (f" · since {since}" if since else ""), sym.get("url", "")]
    if note and note.get("review"):
        lines.append("REVIEW: the catalog entry changed after this note was written; trust the catalog.")
    lines.append("Purpose: " + (note["purpose"] if note else _first_sentence(sym.get("description", ""))))
    required = [f"{r['name']}: {r['type']}" for r in rows if r.get("required")]
    if required:
        lines.append(("Required: " if is_method else "Always: ") + "; ".join(required))
    conditional = [r["name"] for r in rows if r.get("conditional") and not r.get("required")]
    if conditional:
        lines.append("Required in some cases (see `lookup show`): " + ", ".join(conditional))
    if sym.get("subtypes"):
        lines.append("One of: " + ", ".join(sym["subtypes"]))
    if is_method:
        lines.append(f"Returns: {sym.get('returns') or 'see the description'}")
    tail: list[str] = []
    if note:
        for key, label in (("use_when", "Use when"), ("avoid_when", "Avoid when")):
            if note.get(key):
                tail.append(f"{label}: " + "; ".join(note[key]))
        if note.get("pitfalls"):
            tail.append("Pitfalls:")
            # An API cite repeats the catalog text (`lookup show`); other sources keep their evidence.
            tail += [f"- {p['text']} [{p['source']}{': ' + p['cite'] if p.get('cite') and p['source'] != 'API' else ''}]"
                     for p in note["pitfalls"]]
        facts = []
        if note.get("rights"):
            facts.append("Rights: " + note["rights"])
        if note.get("chat_types"):
            facts.append("Chats: " + ", ".join(note["chat_types"]))
        if facts:
            tail.append(" · ".join(facts))
        if note.get("related"):
            tail.append("Related: " + ", ".join(note["related"]))
        if note.get("refs"):
            tail.append("Read: " + ", ".join(note["refs"]))
        if note.get("example"):
            ex = note["example"]
            step = example_step(_inside(skill_dir, ex) or "", sym["name"]) if is_method and ex.endswith(".json") else None
            tail.append(f"Example: {ex}" + (" " + _compact(step.get("params", {}), 160) if step else ""))
    else:
        tail.append(f"Note: none yet, catalog only. `tgui.py lookup show {sym['name']}` has the full official text.")

    optional = [r["name"] for r in rows if not r.get("required") and not r.get("conditional")]
    label = "Optional: " if is_method else "Optional fields: "
    fixed = "\n".join(lines + tail)
    if optional:
        budget = CARD_LIMIT - len(fixed.encode("utf-8")) - len(label) - 2
        shown: list[str] = []
        for i, name in enumerate(optional):
            rest = len(optional) - i - 1
            more = f", … +{rest} more" if rest else ""
            if len((", ".join(shown + [name]) + more).encode("utf-8")) > budget:
                break
            shown.append(name)
        cut = len(optional) - len(shown)
        line = label + ", ".join(shown) + (f"{', ' if shown else ''}… +{cut} more" if cut else "")
        if len(fixed.encode("utf-8")) + 1 + len(line.encode("utf-8")) <= CARD_LIMIT:
            lines.append(line)  # dropped when even the count would not fit; `lookup show` lists them
    return "\n".join(lines + tail)


def main(argv: list[str] | None = None) -> int:
    import argparse
    sys.path.insert(0, HERE)
    from sync_bot_api import DATA_DIR, load_catalog, load_changelog
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["check"])
    ap.add_argument("--notes", default=NOTES_DIR, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    catalog = load_catalog(DATA_DIR)
    changelog = load_changelog(DATA_DIR)
    versions = {r["version"] for r in changelog.get("releases", []) if r.get("version")} \
        if isinstance(changelog, dict) else set()
    files = load_files(args.notes)
    problems = validate(files, catalog, versions=versions)
    for p in problems:
        print(p)
    count = sum(len(_notes_of(d)) for _, d in files)
    print(f"agent notes: {'FAILED' if problems else 'OK'} ({count} notes in {len(files)} files, "
          f"{len(problems)} problems)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
