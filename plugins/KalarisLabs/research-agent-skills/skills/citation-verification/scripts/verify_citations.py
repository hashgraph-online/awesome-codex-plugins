#!/usr/bin/env python3
"""Verify that references exist and match their metadata (Crossref + OpenAlex).

Catches hallucinated or corrupted citations: DOIs that do not resolve, DOIs that
point to a different paper, wrong years/first authors, and titles with no match.

Usage:
    python verify_citations.py refs.bib                    # verify every entry
    python verify_citations.py refs.bib --keys a2020,b2021 # subset
    python verify_citations.py --doi 10.1038/nature14539   # one or more DOIs
    python verify_citations.py refs.bib --json report.json

Set CROSSREF_MAILTO=you@example.org to use Crossref's polite pool (faster, fewer 429s).
Exit codes: 0 all verified, 1 problems found, 2 bad input. Standard library only.
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

UA = "research-agent-skills-citation-verification/1.0 (https://github.com/KalarisLabs/research-agent-skills)"
TITLE_OK, TITLE_WEAK = 0.90, 0.75


def http_json(url: str, retries: int = 3) -> dict | None:
    mailto = os.environ.get("CROSSREF_MAILTO")
    headers = {"User-Agent": UA + (f" mailto:{mailto}" if mailto else ""), "Accept": "application/json"}
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=20) as r:  # noqa: S310
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            if exc.code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(2 ** attempt * 2)
                continue
            raise
        except urllib.error.URLError:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
    return None


# --- minimal BibTeX reader (same grammar as bibtex-hygiene/scripts/bib_lint.py) ---
def _value(text: str, i: int) -> tuple[str, int]:
    parts = []
    while True:
        while i < len(text) and text[i].isspace():
            i += 1
        if text[i] == "{":
            depth, j = 0, i
            while j < len(text):
                if text[j] == "{":
                    depth += 1
                elif text[j] == "}":
                    depth -= 1
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


def parse_bib(text: str) -> list[dict]:
    out = []
    for m in re.finditer(r"@(\w+)\s*[{(]\s*([^,\s]+)\s*,", text):
        if m.group(1).lower() in ("comment", "preamble", "string"):
            continue
        entry, i = {"_type": m.group(1).lower(), "_key": m.group(2)}, m.end()
        while True:
            fm = re.match(r"\s*([A-Za-z][\w:-]*)\s*=\s*", text[i:])
            if not fm:
                break
            v, i = _value(text, i + fm.end())
            entry[fm.group(1).lower()] = re.sub(r"\s+", " ", v).strip()
            cm = re.match(r"\s*,", text[i:])
            if not cm:
                break
            i += cm.end()
        out.append(entry)
    return out


def norm(s: str) -> str:
    s = re.sub(r"\\[a-zA-Z]+\s*|[{}$\\]", "", s or "")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()


def first_surname(authors: str) -> str:
    first = (authors or "").split(" and ")[0].strip()
    surname = first.split(",")[0] if "," in first else (first.split()[-1] if first.split() else "")
    return norm(surname)


def crossref_record(doi: str) -> dict | None:
    data = http_json(f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='/')}")
    return data.get("message") if data else None


def crossref_search(title: str, author: str) -> list[dict]:
    q = urllib.parse.urlencode({"query.bibliographic": f"{title} {author}".strip(), "rows": 3,
                                "select": "DOI,title,author,issued,container-title,type"})
    data = http_json(f"https://api.crossref.org/works?{q}")
    return (data or {}).get("message", {}).get("items", [])


def openalex_search(title: str) -> list[dict]:
    q = urllib.parse.urlencode({"search": title, "per-page": 3, "select": "id,doi,title,publication_year,authorships"})
    data = http_json(f"https://api.openalex.org/works?{q}")
    return (data or {}).get("results", [])


def arxiv_search(title: str, author: str) -> list[dict]:
    """arXiv Atom API; many ML/physics papers exist only as preprints or DOI-less proceedings."""
    import xml.etree.ElementTree as ET  # response from export.arxiv.org (trusted, no DTDs/entities used)

    query = f'ti:"{" ".join(norm(title).split()[:15])}"' + (f" AND au:{author}" if author else "")
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode({"search_query": query, "max_results": 5})
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:  # noqa: S310
        root = ET.fromstring(r.read())  # noqa: S314
    ns = {"a": "http://www.w3.org/2005/Atom"}
    out = []
    for entry in root.findall("a:entry", ns):
        arxiv_id = re.sub(r"v\d+$", "", (entry.findtext("a:id", "", ns) or "").rsplit("/abs/", 1)[-1])
        first = entry.find("a:author/a:name", ns)
        out.append({"doi": f"10.48550/arXiv.{arxiv_id}" if arxiv_id else "",
                    "title": " ".join((entry.findtext("a:title", "", ns) or "").split()),
                    "year": int((entry.findtext("a:published", "", ns) or "0")[:4] or 0) or None,
                    "first_author": norm(first.text.split()[-1]) if first is not None and first.text else ""})
    return out


def cr_fields(rec: dict) -> dict:
    authors = rec.get("author") or []
    year = None
    for k in ("published-print", "published-online", "issued", "created"):
        parts = (rec.get(k) or {}).get("date-parts") or [[None]]
        if parts[0] and parts[0][0]:
            year = parts[0][0]
            break
    return {"doi": rec.get("DOI", ""), "title": (rec.get("title") or [""])[0], "year": year,
            "first_author": norm(authors[0].get("family", "")) if authors else "",
            "venue": (rec.get("container-title") or [""])[0]}


def check_entry(e: dict) -> dict:
    title, doi = e.get("title", ""), re.sub(r"^(https?://(dx\.)?doi\.org/|doi:)", "", e.get("doi", ""), flags=re.I)
    year = re.sub(r"\D", "", e.get("year", ""))[:4]
    author = first_surname(e.get("author", ""))
    res = {"key": e.get("_key", doi), "doi": doi, "title": title, "status": "", "problems": [], "suggestion": None}
    if doi:
        rec = crossref_record(doi)
        if rec is None:
            oa = http_json(f"https://api.openalex.org/works/doi:{urllib.parse.quote(doi, safe='/')}")
            if oa is None:
                res["status"] = "doi-not-found"
                res["problems"].append(f"DOI {doi} does not resolve in Crossref or OpenAlex")
                return res
            got = {"doi": doi, "title": oa.get("title") or "", "year": oa.get("publication_year"),
                   "first_author": norm(((oa.get("authorships") or [{}])[0].get("author") or {}).get("display_name", "").split(" ")[-1])}
        else:
            got = cr_fields(rec)
        if title:
            sim = similarity(title, got["title"])
            if sim < TITLE_WEAK:
                res["problems"].append(f"DOI points to a different work: '{got['title']}' (similarity {sim:.2f})")
            elif sim < TITLE_OK:
                res["problems"].append(f"title differs from record: '{got['title']}' (similarity {sim:.2f})")
        if year and got.get("year") and abs(int(year) - int(got["year"])) > 1:
            res["problems"].append(f"year {year} but record says {got['year']}")
        if author and got.get("first_author") and author != got["first_author"]:
            res["problems"].append(f"first author '{author}' but record says '{got['first_author']}'")
        res["status"] = "verified" if not res["problems"] else "mismatch"
        return res
    if not title:
        res["status"] = "unverifiable"
        res["problems"].append("no DOI and no title")
        return res
    # Popular titles are reused (reprints, talks, homonymous papers), so rank candidates by
    # title similarity plus agreement on year and first author, not by title alone.
    candidates = [cr_fields(item) for item in crossref_search(title, author)]
    for item in openalex_search(title):
        first = ((item.get("authorships") or [{}])[0].get("author") or {}).get("display_name", "")
        candidates.append({"doi": (item.get("doi") or "").replace("https://doi.org/", ""), "title": item.get("title") or "",
                           "year": item.get("publication_year"), "first_author": norm(first.split(" ")[-1]) if first else ""})

    def agrees(c: dict) -> tuple[bool, bool]:
        year_ok = not year or not c.get("year") or abs(int(year) - int(c["year"])) <= 1
        author_ok = not author or not c.get("first_author") or author == c["first_author"]
        return year_ok, author_ok

    def score(c: dict) -> float:
        year_ok, author_ok = agrees(c)
        return similarity(title, c["title"]) + 0.2 * year_ok + 0.2 * author_ok

    best = max(candidates, key=score, default=None)
    if not best or similarity(title, best["title"]) < TITLE_OK or not all(agrees(best)):
        try:
            candidates += arxiv_search(title, author)
        except (urllib.error.URLError, TimeoutError, ValueError):
            pass
        best = max(candidates, key=score, default=None)
    best_sim = similarity(title, best["title"]) if best else 0.0
    if best and best_sim >= TITLE_OK and all(agrees(best)):
        res["status"] = "found-add-doi" if best.get("doi") else "verified"
        res["suggestion"] = best
    elif best and best_sim >= TITLE_OK:
        year_ok, author_ok = agrees(best)
        res["status"] = "uncertain"
        res["suggestion"] = best
        if not year_ok:
            res["problems"].append(f"title matches but year {year} vs record {best['year']}")
        if not author_ok:
            res["problems"].append(f"title matches but first author '{author}' vs record '{best['first_author']}'")
    elif best and best_sim >= TITLE_WEAK:
        res["status"] = "uncertain"
        res["suggestion"] = best
        res["problems"].append(f"closest match '{best['title']}' (similarity {best_sim:.2f}); confirm manually")
    else:
        res["status"] = "not-found"
        res["problems"].append("no matching record in Crossref or OpenAlex (possible fabricated or grey-literature reference)")
    return res


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bib", nargs="?")
    ap.add_argument("--doi", nargs="+", default=[])
    ap.add_argument("--keys", help="comma-separated subset of citation keys")
    ap.add_argument("--json", metavar="PATH", help="write the full report as JSON")
    ap.add_argument("--delay", type=float, default=0.2, help="seconds between API calls (default 0.2)")
    args = ap.parse_args()
    if not args.bib and not args.doi:
        ap.error("give a .bib file or --doi")
    entries: list[dict] = [{"_key": d, "doi": d} for d in args.doi]
    if args.bib:
        try:
            with open(args.bib, encoding="utf-8") as fh:
                entries += parse_bib(fh.read())
        except (OSError, UnicodeDecodeError, ValueError, IndexError) as exc:
            print(f"error: cannot read {args.bib}: {exc}", file=sys.stderr)
            return 2
    if args.keys:
        wanted = set(args.keys.split(","))
        entries = [e for e in entries if e["_key"] in wanted]
    report = []
    for e in entries:
        try:
            r = check_entry(e)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            r = {"key": e.get("_key"), "status": "error", "problems": [f"lookup failed: {exc}"], "suggestion": None}
        report.append(r)
        mark = {"verified": "OK  ", "found-add-doi": "DOI+", "mismatch": "FAIL", "doi-not-found": "FAIL",
                "not-found": "FAIL", "uncertain": "??  ", "unverifiable": "??  ", "error": "ERR "}[r["status"]]
        print(f"{mark} {r['key']}: {r['status']}")
        for p in r["problems"]:
            print(f"       - {p}")
        if r.get("suggestion") and r["status"] == "found-add-doi":
            print(f"       + add doi = {{{r['suggestion']['doi']}}}")
        time.sleep(args.delay)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, ensure_ascii=False)
    bad = [r for r in report if r["status"] not in ("verified", "found-add-doi")]
    print(f"\n{len(report)} checked: {len(report) - len(bad)} verified, {len(bad)} need attention")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
