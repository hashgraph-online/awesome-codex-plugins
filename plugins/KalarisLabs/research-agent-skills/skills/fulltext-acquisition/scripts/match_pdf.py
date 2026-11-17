#!/usr/bin/env python3
"""Identify downloaded papers, check each against its own text, and attach it to the right record.

Drop whatever you find (PDFs, or `.txt`/`.md` conversions) into an inbox folder. For every file this script
reads the first pages, finds a DOI, PMID or title, and matches it to one of your records. A match counts only
when the file's own text supports it. A DOI in the filename alone is not enough, because downloads are routinely
misnamed. Nothing is copied unless you pass `--attach`, and it never overwrites a paper already in the library.

Statuses:
    matched         text-verified and unique: safe to attach
    filename-only   the name suggests a record but the text could not confirm it (no text layer, or no pypdf)
    ambiguous       two records fit equally well
    conflict        the filename points at one record, the text at another: a misnamed file
    duplicate       the record already has a full text in the library
    unmatched       no record fits: wrong paper, or not one of your included records

Usage:
    python match_pdf.py included.csv --inbox inbox/ --library papers/             # report only
    python match_pdf.py included.csv --inbox inbox/ --library papers/ --attach    # copy matched files in
    python match_pdf.py included.csv --inbox inbox/ --library papers/ --attach --allow-filename-only --json out.json

Attached files are saved as `<record_id><ext>` and logged in `<library>/manifest.json` with checksum, how the match
was verified and when. Reads PDFs with `pypdf` when installed; `.txt`/`.md` need nothing.
Exit codes: 0 every inbox file matched or already held, 1 something needs a human, 2 bad input.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import shutil
import sys
import unicodedata
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fulltext_status import clean_doi, have_fulltext, load_records  # noqa: E402

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"<>{}|\\^`]+", re.I)
PMID_TEXT_RE = re.compile(r"\bPMID:?\s*(\d{5,9})\b", re.I)
PMID_NAME_RE = re.compile(r"PMID[_\- ]?(\d{5,9})", re.I)
SUFFIXES = {".pdf", ".txt", ".md"}
TIE = 0.03


def norm(s: str) -> str:
    """Lower-case ASCII words only, for title comparison."""
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def read_text(path: Path, pages: int = 2) -> str | None:
    """Text of the first pages, or None when it cannot be read (scan, missing pypdf)."""
    if path.suffix.lower() in (".txt", ".md"):
        return path.read_text(encoding="utf-8", errors="replace")[:20000]
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        text = "\n".join((p.extract_text() or "") for p in reader.pages[:pages])
    except ImportError:
        return None
    except Exception:  # noqa: BLE001  (corrupt or encrypted PDFs raise many different errors)
        return None
    return text if len(text.strip()) > 80 else None


def dois_in(text: str) -> set[str]:
    """Every DOI-shaped string in a text, cleaned."""
    return {clean_doi(m.group(0)) for m in DOI_RE.finditer(text)}


def doi_from_name(name: str) -> str | None:
    """Recover a DOI from a filename such as `10.1038_nature14539.pdf` or `10.1038%2Fnature14539.pdf`."""
    stem = re.sub(r"%2f", "/", Path(name).stem, flags=re.I)
    m = re.match(r"(10\.\d{4,9})[_/](.+)$", stem)
    return clean_doi(f"{m.group(1)}/{m.group(2)}") if m else None


def title_scores(text: str, records: list[dict]) -> list[tuple[float, dict]]:
    """Best similarity of each record's title to any 1-3 line window in the first lines of the text."""
    lines = [norm(ln) for ln in text.splitlines()[:60] if len(norm(ln)) > 3]
    windows = lines + [" ".join(lines[i:i + 2]) for i in range(len(lines))] + \
        [" ".join(lines[i:i + 3]) for i in range(len(lines))]
    scored = []
    for rec in records:
        t = norm(rec["title"])
        if len(t) < 12:
            continue
        best = max((difflib.SequenceMatcher(None, t, w).ratio() for w in windows), default=0.0)
        if t in " ".join(lines):
            best = max(best, 1.0)
        scored.append((best, rec))
    return sorted(scored, key=lambda x: -x[0])


def identify(path: Path, records: list[dict], min_title: float) -> dict:
    """Match one file to a record and report how well the file's own text supports it."""
    by_doi = {r["doi"]: r for r in records if r["doi"]}
    by_pmid = {r["pmid"]: r for r in records if r["pmid"]}
    out = {"file": path.name, "status": "unmatched", "record": None, "via": None, "notes": []}
    name_rec = by_doi.get(doi_from_name(path.name) or "")
    m = PMID_NAME_RE.search(path.name)
    name_rec = name_rec or (by_pmid.get(m.group(1)) if m else None)
    text = read_text(path)
    if text is None:
        if name_rec:
            return {**out, "status": "filename-only", "record": name_rec["id"], "via": "filename",
                    "notes": ["no readable text layer; the name is the only evidence"]}
        out["notes"].append("no readable text layer and no recognisable name")
        return out
    found: dict[str, tuple[str, dict]] = {}
    for d in dois_in(text):
        if d in by_doi:
            found[by_doi[d]["id"]] = ("text:doi", by_doi[d])
    for pm in PMID_TEXT_RE.findall(text):
        if pm in by_pmid:
            found.setdefault(by_pmid[pm]["id"], ("text:pmid", by_pmid[pm]))
    if len(found) > 1:
        # a paper cites others by DOI: prefer the record whose DOI appears earliest in the text
        lowered = text.lower()
        first = min(found.values(), key=lambda v: lowered.find(v[1]["doi"]) if v[1]["doi"] in lowered else 10**9)
        found = {first[1]["id"]: first}
    if found:
        rec_id, (via, rec) = next(iter(found.items()))
        scores = title_scores(text, [rec])
        title_ok = not rec["title"] or not scores or scores[0][0] >= 0.6
        if not title_ok:
            out["notes"].append("DOI/PMID is in the text but the title does not match; it may be a cited reference")
        else:
            return _verdict(out, rec, via, name_rec)
    scored = title_scores(text, records)
    if scored and scored[0][0] >= min_title:
        top = scored[0]
        rivals = [r for s, r in scored[1:] if top[0] - s < TIE and s >= min_title]
        if rivals:
            return {**out, "status": "ambiguous", "via": "text:title",
                    "notes": [f"{top[1]['id']} and {', '.join(r['id'] for r in rivals)} fit equally well"]}
        return _verdict(out, top[1], f"text:title({top[0]:.2f})", name_rec)
    if name_rec:
        out.update({"status": "conflict", "record": name_rec["id"], "via": "filename"})
        out["notes"].append(f"filename suggests {name_rec['id']} but its text matches no record: misnamed file?")
        return out
    out["notes"].append("no DOI, PMID or title in the text matches your records")
    return out


def _verdict(out: dict, rec: dict, via: str, name_rec: dict | None) -> dict:
    """Finalise a text-supported match, flagging a filename that disagrees with the text."""
    if name_rec and name_rec["id"] != rec["id"]:
        return {**out, "status": "conflict", "record": rec["id"], "via": via,
                "notes": [f"filename suggests {name_rec['id']} but the text identifies {rec['id']}: misnamed file"]}
    return {**out, "status": "matched", "record": rec["id"], "via": via}


def attach(item: dict, inbox: Path, library: Path, manifest: dict) -> str | None:
    """Copy a matched file into the library as <record_id><ext>; return a problem string or None."""
    src = inbox / item["file"]
    dest = library / f"{item['record']}{src.suffix.lower()}"
    if have_fulltext(library, item["record"]):
        return f"{item['record']} already has a full text; not overwriting"
    library.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    manifest[item["record"]] = {"file": dest.name, "source_file": src.name, "sha256":
                                hashlib.sha256(dest.read_bytes()).hexdigest(), "verified_by": item["via"],
                                "date": date.today().isoformat()}
    return None


def main() -> int:
    """Run the command-line interface."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("records", help="CSV or JSON of the included records")
    ap.add_argument("--inbox", required=True)
    ap.add_argument("--library", required=True)
    ap.add_argument("--attach", action="store_true", help="copy matched files into the library")
    ap.add_argument("--allow-filename-only", action="store_true",
                    help="also attach files only the filename vouches for (use for scans you checked by eye)")
    ap.add_argument("--min-title", type=float, default=0.85, help="title similarity needed to match (default 0.85)")
    ap.add_argument("--json", metavar="PATH")
    args = ap.parse_args()
    inbox, library = Path(args.inbox), Path(args.library)
    if not inbox.is_dir():
        print(f"error: {args.inbox} is not a folder", file=sys.stderr)
        return 2
    try:
        records = load_records(Path(args.records))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    manifest_path = library / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    results = []
    for f in sorted(p for p in inbox.iterdir() if p.is_file() and p.suffix.lower() in SUFFIXES):
        item = identify(f, records, args.min_title)
        if item["record"] and have_fulltext(library, item["record"]) and item["status"] in ("matched", "filename-only"):
            item.update(status="duplicate", notes=[*item["notes"], f"{item['record']} is already in the library"])
        elif args.attach and (item["status"] == "matched" or (item["status"] == "filename-only"
                                                              and args.allow_filename_only)):
            problem = attach(item, inbox, library, manifest)
            item["attached"] = problem is None
            if problem:
                item["notes"].append(problem)
        results.append(item)
        rec = f" -> {item['record']}" if item["record"] else ""
        print(f"{item['status']:<14} {item['file']}{rec}" + (f"  [{item['via']}]" if item["via"] else "")
              + ("  (attached)" if item.get("attached") else ""))
        for note in item["notes"]:
            print(f"    - {note}")
    if args.attach and any(r.get("attached") for r in results):
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.json:
        Path(args.json).write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    attached = sum(1 for r in results if r.get("attached"))
    print(f"\n{len(results)} files: {sum(r['status'] == 'matched' for r in results)} matched"
          + (f", {attached} attached" if args.attach else "")
          + f", {sum(r['status'] not in ('matched', 'duplicate') for r in results)} need attention")
    return 1 if any(r["status"] not in ("matched", "duplicate") for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
