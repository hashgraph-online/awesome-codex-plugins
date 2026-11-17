#!/usr/bin/env python3
"""Verify that references exist and match their metadata (Crossref, DataCite, OpenAlex, arXiv).

Catches hallucinated or corrupted citations: DOIs that do not resolve, DOIs that
point to a different paper, wrong years/first authors, titles with no match, and
retracted papers (Crossref `updated-by` notices from Retraction Watch, OpenAlex `is_retracted`).
Dataset and software DOIs registered with DataCite (Zenodo, figshare, arXiv) are resolved too.

Usage:
    python verify_citations.py refs.bib                    # verify every entry
    python verify_citations.py refs.bib --keys a2020,b2021 # subset
    python verify_citations.py --doi 10.1038/nature14539   # one or more DOIs
    python verify_citations.py refs.bib --json report.json
    python verify_citations.py refs.bib --annotate         # add "% UNVERIFIED" comments above bad entries

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
    """Handle http json."""
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
                retry_after = exc.headers.get("Retry-After", "") if exc.headers else ""
                time.sleep(min(int(retry_after), 30) if retry_after.isdigit() else 2 ** attempt * 2)
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
    """Handle value."""
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
    """Parse bib."""
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
    """Handle norm."""
    s = re.sub(r"\\[a-zA-Z]+\s*|[{}$\\]", "", s or "")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def similarity(a: str, b: str) -> float:
    """Handle similarity."""
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()


def first_surname(authors: str) -> str:
    """Handle first surname."""
    first = (authors or "").split(" and ")[0].strip()
    if "," in first:
        surname = first.split(",")[0]
    elif first.split():
        surname = first.split()[-1]
    else:
        surname = ""
    return norm(surname)


def crossref_record(doi: str) -> dict | None:
    """Handle crossref record."""
    data = http_json(f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='/')}")
    return data.get("message") if data else None


def crossref_search(title: str, author: str) -> list[dict]:
    """Handle crossref search."""
    q = urllib.parse.urlencode({"query.bibliographic": f"{title} {author}".strip(), "rows": 3,
                                "select": "DOI,title,author,issued,container-title,type"})
    data = http_json(f"https://api.crossref.org/works?{q}")
    return (data or {}).get("message", {}).get("items", [])


def openalex_search(title: str) -> list[dict]:
    """Handle openalex search."""
    select = "id,doi,title,publication_year,authorships,is_retracted"
    q = urllib.parse.urlencode({"search": title, "per-page": 3, "select": select})
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


RETRACTION_TYPES = {"retraction", "withdrawal", "removal"}
CONCERN_TYPES = {"expression_of_concern", "expression-of-concern"}


def crossref_notices(rec: dict) -> list[dict]:
    """Return editorial notices (retraction, correction, concern) attached to a Crossref work record."""
    out = []
    for n in rec.get("updated-by") or []:
        kind = str(n.get("type", "")).lower().replace(" ", "_")
        out.append({"type": kind, "doi": n.get("DOI", ""), "source": n.get("source", "")})
    return out


def datacite_record(doi: str) -> dict | None:
    """Resolve a DataCite DOI (datasets, software, arXiv, Zenodo) and return normalised fields."""
    data = http_json(f"https://api.datacite.org/dois/{urllib.parse.quote(doi, safe='/')}")
    attrs = ((data or {}).get("data") or {}).get("attributes")
    if not attrs:
        return None
    creators = attrs.get("creators") or [{}]
    first = creators[0].get("familyName") or (creators[0].get("name") or "").split(",")[0]
    return {"doi": doi, "title": (attrs.get("titles") or [{}])[0].get("title", ""),
            "year": attrs.get("publicationYear"), "first_author": norm(first),
            "venue": attrs.get("publisher") or "", "source": "datacite", "notices": []}


def cr_fields(rec: dict) -> dict:
    """Handle cr fields."""
    authors = rec.get("author") or []
    year = None
    for k in ("published-print", "published-online", "issued", "created"):
        parts = (rec.get(k) or {}).get("date-parts") or [[None]]
        if parts[0] and parts[0][0]:
            year = parts[0][0]
            break
    return {"doi": rec.get("DOI", ""), "title": (rec.get("title") or [""])[0], "year": year,
            "first_author": norm(authors[0].get("family", "")) if authors else "",
            "venue": (rec.get("container-title") or [""])[0], "notices": crossref_notices(rec),
            "source": "crossref"}


def _oa_first_author(item: dict) -> str:
    """Return the normalised surname of the first author in an OpenAlex work record."""
    first = ((item.get("authorships") or [{}])[0].get("author") or {}).get("display_name", "")
    return norm(first.split(" ")[-1]) if first else ""


def _oa_notice(is_retracted: object) -> list[dict]:
    """Translate OpenAlex's is_retracted flag into a notice list."""
    return [{"type": "retraction", "doi": "", "source": "openalex"}] if is_retracted else []


def _lookup_doi(doi: str) -> dict | None:
    """Resolve a DOI via Crossref, then DataCite, then OpenAlex; return normalised fields or None."""
    quoted = urllib.parse.quote(doi, safe="/")
    rec = crossref_record(doi)
    if rec is not None:
        got = cr_fields(rec)
        if not got["notices"]:  # Crossref lists Retraction Watch notices; OpenAlex is an independent second signal
            oa = http_json(f"https://api.openalex.org/works/doi:{quoted}?select=is_retracted")
            got["notices"] = _oa_notice(oa and oa.get("is_retracted"))
        return got
    dc = datacite_record(doi)
    if dc is not None:
        return dc
    oa = http_json(f"https://api.openalex.org/works/doi:{quoted}")
    if oa is None:
        return None
    return {"doi": doi, "title": oa.get("title") or "", "year": oa.get("publication_year"),
            "first_author": _oa_first_author(oa), "source": "openalex", "notices": _oa_notice(oa.get("is_retracted"))}


def _notice_problems(got: dict) -> tuple[list[str], bool]:
    """Describe retraction/concern notices on a record; return (problems, is_retracted)."""
    problems, retracted = [], False
    for n in got.get("notices") or []:
        where = f" (notice DOI {n['doi']}, source {n['source']})" if n.get("doi") else f" (source {n['source']})"
        if n["type"] in RETRACTION_TYPES:
            retracted = True
            problems.append(f"RETRACTED: record carries a {n['type']} notice{where}; do not cite as support")
        elif n["type"] in CONCERN_TYPES:
            problems.append(f"expression of concern on this work{where}; review before citing")
    return problems, retracted


def _doi_problems(title: str, year: str, author: str, got: dict) -> list[str]:
    """Compare a bib entry with the record its DOI resolves to and list every disagreement."""
    problems = []
    if title:
        sim = similarity(title, got["title"])
        if sim < TITLE_WEAK:
            problems.append(f"DOI points to a different work: '{got['title']}' (similarity {sim:.2f})")
        elif sim < TITLE_OK:
            problems.append(f"title differs from record: '{got['title']}' (similarity {sim:.2f})")
    if year and got.get("year") and abs(int(year) - int(got["year"])) > 1:
        problems.append(f"year {year} but record says {got['year']}")
    if author and got.get("first_author") and author != got["first_author"]:
        problems.append(f"first author '{author}' but record says '{got['first_author']}'")
    return problems


def _check_by_doi(res: dict, title: str, doi: str, year: str, author: str) -> dict:
    """Fill the result for an entry that carries a DOI."""
    got = _lookup_doi(doi)
    if got is None:
        res["status"] = "doi-not-found"
        res["problems"].append(f"DOI {doi} does not resolve in Crossref, DataCite or OpenAlex")
        return res
    res["problems"].extend(_doi_problems(title, year, author, got))
    notice_problems, retracted = _notice_problems(got)
    res["problems"].extend(notice_problems)
    if retracted:
        res["status"] = "retracted"
    elif notice_problems:
        res["status"] = "uncertain"
    else:
        res["status"] = "verified" if not res["problems"] else "mismatch"
    return res


SOURCE_ERRORS = (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError)


def _title_candidates(title: str, author: str) -> tuple[list[dict], list[str]]:
    """Collect candidates for a DOI-less entry from Crossref and OpenAlex; also return the sources that failed."""
    candidates: list[dict] = []
    failed: list[str] = []
    try:
        candidates += [cr_fields(item) for item in crossref_search(title, author)]
    except SOURCE_ERRORS:
        failed.append("Crossref")
    try:
        for item in openalex_search(title):
            doi = (item.get("doi") or "").replace("https://doi.org/", "")
            candidates.append({"doi": doi, "title": item.get("title") or "",
                               "year": item.get("publication_year"), "first_author": _oa_first_author(item),
                               "notices": _oa_notice(item.get("is_retracted"))})
    except SOURCE_ERRORS:
        failed.append("OpenAlex")
    return candidates, failed


def _agrees(year: str, author: str, c: dict) -> tuple[bool, bool]:
    """Return whether a candidate agrees with the entry on year (within one) and first author."""
    year_ok = not year or not c.get("year") or abs(int(year) - int(c["year"])) <= 1
    author_ok = not author or not c.get("first_author") or author == c["first_author"]
    return year_ok, author_ok


def _find_best(title: str, year: str, author: str) -> tuple[dict | None, list[str]]:
    """Pick the best candidate by title similarity plus year/first-author agreement; also return failed sources."""
    # Popular titles are reused (reprints, talks, homonymous papers), so rank candidates by
    # title similarity plus agreement on year and first author, not by title alone.
    candidates, failed = _title_candidates(title, author)

    def score(c: dict) -> float:
        """Score a candidate by title similarity plus bonuses for year and author agreement."""
        year_ok, author_ok = _agrees(year, author, c)
        return similarity(title, c["title"]) + 0.2 * year_ok + 0.2 * author_ok

    best = max(candidates, key=score, default=None)
    if not best or similarity(title, best["title"]) < TITLE_OK or not all(_agrees(year, author, best)):
        try:
            candidates += arxiv_search(title, author)
        except SOURCE_ERRORS:
            failed.append("arXiv")
        best = max(candidates, key=score, default=None)
    if not candidates and len(failed) >= 3:
        raise urllib.error.URLError("all search sources failed: " + ", ".join(failed))
    return best, failed


def _classify_title_match(res: dict, best: dict, title: str, year: str, author: str) -> dict:
    """Classify a candidate whose title is at least as similar as TITLE_OK."""
    year_ok, author_ok = _agrees(year, author, best)
    res["suggestion"] = best
    if year_ok and author_ok:
        notices = best.get("notices") or []
        if best.get("doi") and not notices and not best["doi"].startswith("10.48550/"):
            # Title-search candidates skip the DOI lookup, so check for a retraction now. Best effort: a rate-limited
            # or failed secondary lookup must not turn an otherwise matched entry into an error.
            try:
                notices = (_lookup_doi(best["doi"]) or {}).get("notices") or []
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
                res["problems"].append("retraction check skipped (lookup failed); re-run to confirm")
        problems, retracted = _notice_problems({"notices": notices})
        res["problems"].extend(problems)
        res["status"] = "retracted" if retracted else "uncertain" if problems else (
            "found-add-doi" if best.get("doi") else "verified")
        return res
    res["status"] = "uncertain"
    if not year_ok:
        res["problems"].append(f"title matches but year {year} vs record {best['year']}")
    if not author_ok:
        res["problems"].append(f"title matches but first author '{author}' vs record '{best['first_author']}'")
    return res


def _classify_match(res: dict, best: dict | None, title: str, year: str, author: str,
                    failed: list[str] | None = None) -> dict:
    """Set status, suggestion and problems on the result from the best candidate found."""
    best_sim = similarity(title, best["title"]) if best else 0.0
    if best and best_sim >= TITLE_OK:
        return _classify_title_match(res, best, title, year, author)
    if best and best_sim >= TITLE_WEAK:
        res["status"] = "uncertain"
        res["suggestion"] = best
        res["problems"].append(f"closest match '{best['title']}' (similarity {best_sim:.2f}); confirm manually")
        return res
    if failed:  # absence of evidence from a partial search is not evidence of fabrication
        res["status"] = "uncertain"
        down = ", ".join(failed)
        res["problems"].append(f"no match found, but {down} could not be queried (rate limit or outage); re-run later")
        return res
    res["status"] = "not-found"
    res["problems"].append(
        "no matching record in Crossref, OpenAlex or arXiv (possible fabricated or grey-literature reference)")
    return res


def check_entry(e: dict) -> dict:
    """Check one bib entry against Crossref, DataCite, OpenAlex and arXiv and return a status report."""
    title, doi = e.get("title", ""), re.sub(r"^(https?://(dx\.)?doi\.org/|doi:)", "", e.get("doi", ""), flags=re.I)
    year = re.sub(r"\D", "", e.get("year", ""))[:4]
    author = first_surname(e.get("author", ""))
    res = {"key": e.get("_key", doi), "doi": doi, "title": title, "status": "", "problems": [], "suggestion": None}
    if doi:
        return _check_by_doi(res, title, doi, year, author)
    if not title:
        res["status"] = "unverifiable"
        res["problems"].append("no DOI and no title")
        return res
    best, failed = _find_best(title, year, author)
    return _classify_match(res, best, title, year, author, failed)


GOOD = ("verified", "found-add-doi")


def annotate_bib(text: str, report: list[dict]) -> str:
    """Return the .bib text with a `% UNVERIFIED (<status>): <problem>` comment above each entry needing attention.

    Idempotent: an existing marker above an entry is replaced, and a marker above an entry that now verifies is
    removed. Entry bodies are never modified.
    """
    for r in report:
        key = r.get("key")
        if not key:
            continue
        pat = re.compile(r"(?:^% UNVERIFIED[^\n]*\n)?^(@\w+\s*[{(]\s*" + re.escape(str(key)) + r"\s*,)", re.M)
        m = pat.search(text)
        if not m:
            continue
        marker = ""
        if r.get("status") not in GOOD:
            why = (r.get("problems") or ["no reason recorded"])[0].replace("\n", " ")
            marker = f"% UNVERIFIED ({r.get('status')}): {why}\n"
        text = text[:m.start()] + marker + m.group(1) + text[m.end():]
    return text


def main() -> int:
    """Run the command-line interface."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bib", nargs="?")
    ap.add_argument("--doi", nargs="+", default=[])
    ap.add_argument("--keys", help="comma-separated subset of citation keys")
    ap.add_argument("--json", metavar="PATH", help="write the full report as JSON")
    ap.add_argument("--annotate", action="store_true",
                    help="rewrite the .bib in place, adding '%% UNVERIFIED' comments above entries needing attention")
    ap.add_argument("--delay", type=float, default=0.2, help="seconds between API calls (default 0.2)")
    args = ap.parse_args()
    if not args.bib and not args.doi:
        ap.error("give a .bib file or --doi")
    entries: list[dict] = [{"_key": d, "doi": d} for d in args.doi]
    if args.bib:
        try:
            with open(args.bib, encoding="utf-8") as fh:
                entries += parse_bib(fh.read())
        except (OSError, ValueError, IndexError) as exc:
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
                "not-found": "FAIL", "retracted": "RETR", "uncertain": "??  ", "unverifiable": "??  ",
                "error": "ERR "}[r["status"]]
        print(f"{mark} {r['key']}: {r['status']}")
        for p in r["problems"]:
            print(f"       - {p}")
        if r.get("suggestion") and r["status"] == "found-add-doi":
            print(f"       + add doi = {{{r['suggestion']['doi']}}}")
        time.sleep(args.delay)
    if args.annotate and args.bib:
        with open(args.bib, encoding="utf-8", newline="") as fh:
            original = fh.read()
        annotated = annotate_bib(original, [r for r in report if r.get("key")])
        if annotated != original:
            with open(args.bib, "w", encoding="utf-8", newline="") as fh:
                fh.write(annotated)
            print(f"annotated {args.bib}")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, ensure_ascii=False)
    bad = [r for r in report if r["status"] not in ("verified", "found-add-doi")]
    print(f"\n{len(report)} checked: {len(report) - len(bad)} verified, {len(bad)} need attention")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
