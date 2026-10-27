#!/usr/bin/env python3
"""Lint a BibTeX file for problems that break builds or embarrass authors.

Checks: duplicate keys, duplicate works (same DOI or near-identical title),
missing required fields per entry type, malformed DOIs/years/pages, unprotected
capitals in titles (lost acronyms), unbalanced braces, URL-only DOIs, and
arXiv preprints that should cite a published version.

Usage:
    python bib_lint.py refs.bib                 # human-readable report
    python bib_lint.py refs.bib --json          # machine-readable
    python bib_lint.py refs.bib --fix out.bib   # write normalized copy (safe fixes only)

Exit codes: 0 clean, 1 findings, 2 bad input. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass, field

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

REQUIRED = {
    "article": ["author", "title", "journal", "year"],
    "inproceedings": ["author", "title", "booktitle", "year"],
    "conference": ["author", "title", "booktitle", "year"],
    "book": ["title", "publisher", "year"],
    "incollection": ["author", "title", "booktitle", "publisher", "year"],
    "phdthesis": ["author", "title", "school", "year"],
    "mastersthesis": ["author", "title", "school", "year"],
    "techreport": ["author", "title", "institution", "year"],
    "misc": ["title"],
    "online": ["title", "url"],
}
DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")
ACRONYM_RE = re.compile(r"(?<![{\\\w])([A-Z][A-Za-z]*[A-Z][A-Za-z]*|[A-Z]{2,}\d*)(?![}\w])")


@dataclass
class Entry:
    type: str
    key: str
    fields: dict[str, str] = field(default_factory=dict)
    line: int = 0


class BibError(ValueError):
    pass


def _read_value(text: str, i: int) -> tuple[str, int]:
    """Read a field value starting at text[i] (brace, quote, or bare token, with # concatenation)."""
    parts = []
    while True:
        while i < len(text) and text[i].isspace():
            i += 1
        if i >= len(text):
            raise BibError("unexpected end of file in field value")
        if text[i] == "{":
            depth, j = 0, i
            while j < len(text):
                if text[j] == "\\":
                    j += 2
                    continue
                if text[j] == "{":
                    depth += 1
                elif text[j] == "}":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            if depth != 0:
                raise BibError("unbalanced braces in field value")
            parts.append(text[i + 1:j])
            i = j + 1
        elif text[i] == '"':
            j = i + 1
            depth = 0
            while j < len(text) and not (text[j] == '"' and depth == 0):
                depth += text[j] == "{"
                depth -= text[j] == "}"
                j += 1
            parts.append(text[i + 1:j])
            i = j + 1
        else:
            m = re.match(r"[^,}\s#]+", text[i:])
            if not m:
                raise BibError("empty field value")
            parts.append(m.group(0))
            i += m.end()
        while i < len(text) and text[i].isspace():
            i += 1
        if i < len(text) and text[i] == "#":
            i += 1
            continue
        return "".join(parts), i


def parse_bib(text: str) -> list[Entry]:
    entries: list[Entry] = []
    for m in re.finditer(r"@(\w+)\s*([{(])", text):
        etype = m.group(1).lower()
        if etype in ("comment", "preamble", "string"):
            continue
        i = m.end()
        line = text.count("\n", 0, m.start()) + 1
        km = re.match(r"\s*([^,\s]+)\s*,", text[i:])
        if not km:
            raise BibError(f"line {line}: entry without a citation key")
        entry = Entry(etype, km.group(1), line=line)
        i += km.end()
        while True:
            fm = re.match(r"\s*([A-Za-z][\w:-]*)\s*=\s*", text[i:])
            if not fm:
                break
            value, i = _read_value(text, i + fm.end())
            entry.fields[fm.group(1).lower()] = re.sub(r"\s+", " ", value).strip()
            cm = re.match(r"\s*,", text[i:])
            if not cm:
                break
            i += cm.end()
        entries.append(entry)
    return entries


def norm_title(t: str) -> str:
    t = unicodedata.normalize("NFKD", re.sub(r"[{}\\]", "", t)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def lint(entries: list[Entry]) -> list[dict]:
    out: list[dict] = []

    def add(e: Entry, severity: str, code: str, msg: str) -> None:
        out.append({"key": e.key, "line": e.line, "severity": severity, "code": code, "message": msg})

    seen_keys: dict[str, Entry] = {}
    seen_doi: dict[str, Entry] = {}
    seen_title: dict[str, Entry] = {}
    for e in entries:
        f = e.fields
        if e.key.lower() in seen_keys:
            add(e, "error", "duplicate-key", f"key also used at line {seen_keys[e.key.lower()].line}")
        seen_keys.setdefault(e.key.lower(), e)
        for req in REQUIRED.get(e.type, ["title"]):
            if not f.get(req) and not (req == "author" and f.get("editor")):
                add(e, "error", "missing-field", f"@{e.type} is missing '{req}'")
        doi = f.get("doi", "")
        if doi:
            bare = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:)", "", doi, flags=re.I)
            if bare != doi:
                add(e, "warning", "doi-url", f"store the bare DOI '{bare}', not a URL/prefix")
            if not DOI_RE.match(bare):
                add(e, "error", "doi-format", f"'{doi}' is not a valid DOI")
            if bare.lower() in seen_doi:
                add(e, "error", "duplicate-work", f"same DOI as '{seen_doi[bare.lower()].key}'")
            seen_doi.setdefault(bare.lower(), e)
        title = f.get("title", "")
        if title:
            nt = norm_title(title)
            if nt and nt in seen_title and seen_title[nt].key != e.key:
                add(e, "warning", "duplicate-work", f"same title as '{seen_title[nt].key}'")
            seen_title.setdefault(nt, e)
            unprotected = sorted(set(ACRONYM_RE.findall(re.sub(r"\{[^{}]*\}", "", title))))
            if unprotected:
                add(e, "warning", "title-case",
                    f"protect capitals with braces so styles keep them: {', '.join(unprotected)}")
        year = f.get("year", "")
        if year and not re.fullmatch(r"(1[5-9]|20)\d{2}[a-z]?", year):
            add(e, "error", "year-format", f"year '{year}' is not a 4-digit year")
        pages = f.get("pages", "")
        if pages and re.fullmatch(r"\d+\s*[-–]\s*\d+", pages) and "--" not in pages:
            normalized_pages = re.sub(r"\s*[-–]\s*", "--", pages)
            add(e, "info", "pages-dash", f"use an en dash in page ranges: '{normalized_pages}'")
        journal = f.get("journal", "").lower()
        if ("arxiv" in journal or f.get("eprinttype", "").lower() == "arxiv" or f.get("archiveprefix", "").lower() == "arxiv"):
            add(e, "info", "preprint", "arXiv preprint: check whether a peer-reviewed version exists and cite it")
        if f.get("author", "").count(" and ") >= 1 and re.search(r",\s*,", f.get("author", "")):
            add(e, "error", "author-format", "malformed author list (empty name between commas)")
        if "others" in f.get("author", "").split(" and ")[-1:] and len(f.get("author", "").split(" and ")) < 3:
            add(e, "warning", "author-others", "'and others' with fewer than 3 authors: list them all")
    return out


def normalized_bib(entries: list[Entry]) -> str:
    chunks = []
    order = ["author", "editor", "title", "journal", "booktitle", "publisher", "school", "institution", "year",
             "volume", "number", "pages", "doi", "url", "eprint", "archiveprefix", "primaryclass", "note"]
    for e in entries:
        f = dict(e.fields)
        if "doi" in f:
            f["doi"] = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:)", "", f["doi"], flags=re.I)
        if "pages" in f and re.fullmatch(r"\d+\s*[-–]\s*\d+", f["pages"]):
            f["pages"] = re.sub(r"\s*[-–]\s*", "--", f["pages"])
        keys = [k for k in order if k in f] + sorted(k for k in f if k not in order)
        width = max((len(k) for k in keys), default=0)
        body = ",\n".join(f"  {k.ljust(width)} = {{{f[k]}}}" for k in keys)
        chunks.append(f"@{e.type}{{{e.key},\n{body}\n}}\n")
    return "\n".join(chunks)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bib")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--fix", metavar="OUT", help="write a normalized copy (bare DOIs, en-dash pages, field order)")
    args = ap.parse_args()
    try:
        with open(args.bib, encoding="utf-8") as fh:
            entries = parse_bib(fh.read())
    except (OSError, UnicodeDecodeError, BibError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    findings = lint(entries)
    if args.fix:
        with open(args.fix, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(normalized_bib(entries))
    if args.json:
        print(json.dumps({"entries": len(entries), "findings": findings}, indent=2))
    else:
        for x in findings:
            print(f"{x['severity']:<7} {x['key']} (line {x['line']}) [{x['code']}] {x['message']}")
        counts = {s: sum(x["severity"] == s for x in findings) for s in ("error", "warning", "info")}
        print(f"\n{len(entries)} entries: {counts['error']} errors, {counts['warning']} warnings, {counts['info']} info")
    return 1 if any(x["severity"] in ("error", "warning") for x in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
