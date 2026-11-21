#!/usr/bin/env python3
"""List the included papers that have no full text yet, with ready-made ways to get each one.

After abstract screening, the bottleneck is full text. Given your included records (CSV or JSON) and the
folder where PDFs live (`<record_id>.pdf`, `.md` or `.txt`), this writes:

  missing.csv     one row per paper still missing, with its DOI, PMID, an open-access URL when known, and the
                  fields an interlibrary-loan request asks for
  retrieval.md    a worklist page: for each missing paper the free-copy search links, your institution's link
                  resolver, and the prefilled ILL fields

Offline by default: it builds links and queries nothing. `--resolve-oa --email you@uni.edu` asks Unpaywall
(api.unpaywall.org, polite pool) for a legal open-access PDF URL for each DOI.

Usage:
    python fulltext_status.py included.csv --library papers/ -o work/
    python fulltext_status.py included.csv --library papers/ -o work/ --resolver "https://resolver.research-agent-skills.local/openurl?"
    python fulltext_status.py included.csv --library papers/ -o work/ --resolve-oa --email you@uni.edu

CSV columns (case-insensitive; the first present wins): record_id|id|key, doi, pmid, pmcid, title, authors|author,
year, journal|source|venue, volume, issue, pages. Output of systematic-review-prisma/dedupe_records.py works as is.
Exit codes: 0 ok (even when papers are missing: read the summary), 2 bad input. Standard library only.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

ALIASES = {
    "id": ("record_id", "id", "key", "citekey"),
    "doi": ("doi",),
    "pmid": ("pmid", "pubmed_id"),
    "pmcid": ("pmcid",),
    "title": ("title", "article_title"),
    "authors": ("authors", "author"),
    "year": ("year", "publication_year", "pub_year"),
    "journal": ("journal", "source", "venue", "container_title"),
    "volume": ("volume",),
    "issue": ("issue", "number"),
    "pages": ("pages", "page"),
}
LIBRARY_SUFFIXES = (".pdf", ".md", ".txt")
UA = "research-agent-skills-fulltext-acquisition/1.0 (https://github.com/KalarisLabs/research-agent-skills)"


def clean_doi(doi: str) -> str:
    """Strip URL and `doi:` prefixes and trailing punctuation; return a lower-case bare DOI."""
    doi = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", (doi or "").strip(), flags=re.I)
    return doi.rstrip(".,;)").lower()


def load_records(path: Path) -> list[dict]:
    """Load records from CSV or JSON and normalise the column names."""
    if path.suffix.lower() == ".json":
        rows = json.loads(path.read_text(encoding="utf-8"))
    else:
        with path.open(encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{path} has no records")
    out = []
    for i, row in enumerate(rows, 1):
        low = {str(k).strip().lower(): v for k, v in row.items() if k}
        rec = {field: next((str(low[a]).strip() for a in names if low.get(a) not in (None, "")), "")
               for field, names in ALIASES.items()}
        rec["id"] = rec["id"] or f"R{i:05d}"
        rec["doi"] = clean_doi(rec["doi"])
        out.append(rec)
    ids = [r["id"] for r in out]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        raise ValueError(f"duplicate record ids: {', '.join(sorted(dup))}")
    return out


def have_fulltext(library: Path, rec_id: str) -> Path | None:
    """Return the library file for a record id, if any."""
    for suffix in LIBRARY_SUFFIXES:
        candidate = library / f"{rec_id}{suffix}"
        if candidate.is_file() and candidate.stat().st_size > 0:
            return candidate
    return None


def unpaywall(doi: str, email: str) -> dict:
    """Ask Unpaywall for the best legal open-access copy of a DOI. Returns {} on any failure."""
    url = f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi, safe='/')}?email={urllib.parse.quote(email)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=20) as r:  # noqa: S310
            data = json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
        return {}
    best = data.get("best_oa_location") or {}
    return {"is_oa": bool(data.get("is_oa")), "oa_url": best.get("url_for_pdf") or best.get("url") or "",
            "oa_status": data.get("oa_status") or "", "license": best.get("license") or ""}


def links_for(rec: dict, resolver: str) -> dict[str, str]:
    """Free-copy search links and an OpenURL for the institution's resolver (nothing is fetched)."""
    links: dict[str, str] = {}
    doi, pmid, pmcid = rec["doi"], rec["pmid"], rec["pmcid"]
    if doi:
        links["DOI"] = f"https://doi.org/{doi}"
        links["Unpaywall"] = f"https://unpaywall.org/{urllib.parse.quote(doi, safe='/')}"
        links["Europe PMC"] = "https://europepmc.org/search?query=" + urllib.parse.quote(f'DOI:"{doi}"')
    if pmcid:
        links["PubMed Central"] = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/"
    elif pmid:
        links["PubMed"] = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
    if resolver:
        params = {"url_ver": "Z39.88-2004", "rft.atitle": rec["title"], "rft.jtitle": rec["journal"],
                  "rft.date": rec["year"], "rft.volume": rec["volume"], "rft.issue": rec["issue"],
                  "rft.pages": rec["pages"]}
        if doi:
            params["rft_id"] = f"info:doi/{doi}"
        if pmid:
            params["rft_id.pmid"] = f"info:pmid/{pmid}"
        links["Institution resolver"] = resolver + urllib.parse.urlencode({k: v for k, v in params.items() if v})
    return links


def write_outputs(missing: list[dict], out_dir: Path, resolver: str, summary: dict) -> None:
    """Write missing.csv and retrieval.md."""
    out_dir.mkdir(parents=True, exist_ok=True)
    cols = ["id", "doi", "pmid", "pmcid", "title", "authors", "year", "journal", "volume", "issue", "pages",
            "oa_url", "oa_status"]
    with (out_dir / "missing.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(missing)
    lines = ["# Full-text retrieval worklist", "",
             f"{summary['missing']} of {summary['total']} papers still need full text "
             f"({summary['have']} in the library"
             + (f", {summary['open_access']} with a legal open-access copy" if summary["resolved_oa"] else "") + ").",
             "", "Work down the list: free copy first, then your institution, then interlibrary loan. Drop each "
             "PDF in the inbox; `match_pdf.py` identifies it, checks it against its own text and attaches it.", ""]
    for rec in missing:
        lines += [f"## {rec['id']}: {rec['title'] or '(no title)'}", ""]
        meta = [rec[k] for k in ("authors", "journal", "year") if rec[k]]
        if meta:
            lines += ["_" + "; ".join(meta) + "_", ""]
        if rec.get("oa_url"):
            lines += [f"- **Open-access PDF**: {rec['oa_url']} ({rec.get('oa_status') or 'oa'})"]
        lines += [f"- {name}: {url}" for name, url in links_for(rec, resolver).items()]
        lines += ["", "ILL request fields:", "", "| Field | Value |", "|---|---|"]
        lines += [f"| {label} | {rec[key]} |" for label, key in (
            ("Article title", "title"), ("Authors", "authors"), ("Journal", "journal"), ("Year", "year"),
            ("Volume", "volume"), ("Issue", "issue"), ("Pages", "pages"), ("DOI", "doi"), ("PMID", "pmid")) if rec[key]]
        lines.append("")
    (out_dir / "retrieval.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    """Run the command-line interface."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("records", help="CSV or JSON of the included records")
    ap.add_argument("--library", required=True, help="folder of full texts named <record_id>.pdf|md|txt")
    ap.add_argument("-o", "--out", default="fulltext-work", help="output folder (default fulltext-work)")
    ap.add_argument("--resolver", default="", help="institution link-resolver base URL, ending in ? or &")
    ap.add_argument("--resolve-oa", action="store_true", help="look up legal open-access copies via Unpaywall")
    ap.add_argument("--email", help="your email, required by Unpaywall with --resolve-oa")
    ap.add_argument("--delay", type=float, default=0.2, help="seconds between Unpaywall calls")
    args = ap.parse_args()
    if args.resolve_oa and not args.email:
        ap.error("--resolve-oa needs --email (Unpaywall asks callers to identify themselves)")
    try:
        records = load_records(Path(args.records))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    library = Path(args.library)
    missing = []
    for rec in records:
        if have_fulltext(library, rec["id"]):
            continue
        rec.update({"oa_url": "", "oa_status": ""})
        if args.resolve_oa and rec["doi"]:
            rec.update({k: v for k, v in unpaywall(rec["doi"], args.email).items() if k in ("oa_url", "oa_status")})
            time.sleep(args.delay)
        missing.append(rec)
    summary = {"total": len(records), "have": len(records) - len(missing), "missing": len(missing),
               "no_doi": sum(1 for r in missing if not r["doi"]), "resolved_oa": bool(args.resolve_oa),
               "open_access": sum(1 for r in missing if r["oa_url"])}
    write_outputs(missing, Path(args.out), args.resolver, summary)
    print(json.dumps(summary))
    print(f"wrote {Path(args.out) / 'missing.csv'} and {Path(args.out) / 'retrieval.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
