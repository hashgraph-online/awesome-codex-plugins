#!/usr/bin/env python3
"""Deduplicate search exports from several databases before screening.

Reads RIS (.ris), CSV (.csv with title/doi/year/authors columns, e.g. PubMed,
Scopus, Web of Science exports) and BibTeX (.bib). Matches on normalized DOI,
then on normalized title + year (+ first-author surname when present).
Writes a merged CSV plus a JSON summary with per-source counts for PRISMA.

Usage:
    python dedupe_records.py pubmed.ris scopus.csv wos.bib -o screening.csv --summary counts.json

Standard library only.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

RIS_MAP = {"TI": "title", "T1": "title", "DO": "doi", "PY": "year", "Y1": "year", "AU": "authors", "A1": "authors",
           "JO": "journal", "T2": "journal", "JF": "journal", "AB": "abstract", "N2": "abstract", "UR": "url"}


def norm_doi(d: str) -> str:
    return re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", (d or "").strip(), flags=re.I).lower()


def norm_title(t: str) -> str:
    t = unicodedata.normalize("NFKD", re.sub(r"[{}\\]", "", t or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def surname(authors: str) -> str:
    first = re.split(r";| and |\|", authors or "")[0].strip()
    s = first.split(",")[0] if "," in first else (first.split()[-1] if first.split() else "")
    return norm_title(s)


def read_ris(path: Path) -> list[dict]:
    recs, cur = [], {}
    for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        m = re.match(r"^([A-Z][A-Z0-9])  - ?(.*)$", line)
        if not m:
            continue
        tag, val = m.group(1), m.group(2).strip()
        if tag == "ER":
            recs.append(cur)
            cur = {}
        elif tag in RIS_MAP:
            key = RIS_MAP[tag]
            if key == "authors":
                cur["authors"] = f"{cur['authors']}; {val}" if cur.get("authors") else val
            elif key == "year":
                cur.setdefault("year", val[:4])
            else:
                cur.setdefault(key, val)
    if cur:
        recs.append(cur)
    return recs


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", errors="replace", newline="") as fh:
        rows = list(csv.DictReader(fh))
    out = []
    for r in rows:
        low = {k.strip().lower(): (v or "").strip() for k, v in r.items() if k}
        pick = lambda *names: next((low[n] for n in names if low.get(n)), "")  # noqa: E731
        out.append({"title": pick("title", "article title", "document title", "ti"),
                    "doi": pick("doi", "do"), "year": pick("year", "publication year", "py", "publication_year")[:4],
                    "authors": pick("authors", "author", "author full names", "au"),
                    "journal": pick("journal", "source title", "journal/book", "so"),
                    "abstract": pick("abstract", "ab")})
    return out


def _bib_value(text: str, i: int) -> tuple[str, int]:
    parts = []
    while True:
        while text[i].isspace():
            i += 1
        if text[i] == "{":
            depth, j = 0, i
            while True:
                depth += (text[j] == "{") - (text[j] == "}")
                if depth == 0:
                    break
                j += 1
            parts.append(text[i + 1:j])
            i = j + 1
        elif text[i] == '"':
            j = text.index('"', i + 1)
            parts.append(text[i + 1:j])
            i = j + 1
        else:
            m = re.match(r"[^,}\s#]+", text[i:])
            parts.append(m.group(0) if m else "")
            i += m.end() if m else 1
        while i < len(text) and text[i].isspace():
            i += 1
        if i < len(text) and text[i] == "#":
            i += 1
            continue
        return "".join(parts), i


def read_bib(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    out = []
    for m in re.finditer(r"@(\w+)\s*[{(]\s*([^,\s]+)\s*,", text):
        if m.group(1).lower() in ("comment", "string", "preamble"):
            continue
        f, i = {}, m.end()
        while True:
            fm = re.match(r"\s*([A-Za-z][\w:-]*)\s*=\s*", text[i:])
            if not fm:
                break
            v, i = _bib_value(text, i + fm.end())
            f[fm.group(1).lower()] = re.sub(r"\s+", " ", re.sub(r"(?<!\\)[{}]", "", v)).strip()
            cm = re.match(r"\s*,", text[i:])
            if not cm:
                break
            i += cm.end()
        out.append({"title": f.get("title", ""), "doi": f.get("doi", ""), "year": f.get("year", "")[:4],
                    "authors": f.get("author", ""), "journal": f.get("journal", f.get("booktitle", "")),
                    "abstract": f.get("abstract", "")})
    return out


READERS = {".ris": read_ris, ".txt": read_ris, ".csv": read_csv, ".bib": read_bib}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", type=Path)
    ap.add_argument("-o", "--output", type=Path, default=Path("deduplicated.csv"))
    ap.add_argument("--summary", type=Path, help="write per-source and duplicate counts as JSON")
    args = ap.parse_args()

    merged: list[dict] = []
    by_doi: dict[str, dict] = {}
    by_title: dict[tuple, dict] = {}
    per_source: dict[str, int] = {}
    dups = 0
    for path in args.inputs:
        reader = READERS.get(path.suffix.lower())
        if not reader:
            print(f"error: unsupported file type {path.suffix} ({path})", file=sys.stderr)
            return 2
        recs = reader(path)
        per_source[path.name] = len(recs)
        for r in recs:
            r["source"] = path.name
            doi, title = norm_doi(r.get("doi", "")), norm_title(r.get("title", ""))
            tkey = (title, r.get("year", ""), surname(r.get("authors", ""))) if title else None
            existing = (by_doi.get(doi) if doi else None) or (by_title.get(tkey) if tkey else None)
            if existing is None and tkey:  # tolerate a missing author on one side
                existing = by_title.get((title, r.get("year", ""), ""))
            if existing:
                dups += 1
                existing["sources"] = ";".join(sorted(set(existing["sources"].split(";")) | {path.name}))
                for k in ("doi", "abstract", "journal", "authors"):
                    if not existing.get(k) and r.get(k):
                        existing[k] = r[k]
                continue
            r["sources"] = path.name
            merged.append(r)
            if doi:
                by_doi[doi] = r
            if tkey:
                by_title[tkey] = r
                by_title.setdefault((title, r.get("year", ""), ""), r)

    fields = ["record_id", "title", "authors", "year", "journal", "doi", "sources", "abstract",
              "screen_title_abstract", "screen_full_text", "exclusion_reason"]
    with args.output.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for i, r in enumerate(merged, 1):
            w.writerow({**r, "record_id": f"R{i:05d}"})
    summary = {"per_source": per_source, "records_identified": sum(per_source.values()),
               "duplicates_removed": dups, "records_to_screen": len(merged)}
    if args.summary:
        args.summary.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
