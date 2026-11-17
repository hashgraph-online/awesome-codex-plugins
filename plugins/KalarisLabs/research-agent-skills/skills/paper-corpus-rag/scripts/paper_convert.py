#!/usr/bin/env python3
"""Convert papers to page-marked Markdown and grade how far the conversion can be trusted.

Retrieval is only as good as the text underneath it. This script turns a PDF (or the output of
`pdftotext`, where form feeds separate pages) into one Markdown file per paper with
`<!-- page: N -->` markers, so every passage can be cited to a page, and writes a sidecar
`<name>.quality.json` that `paper_index.py` stores with the paper. Nothing is repaired silently:
each fix is listed in the sidecar with its before and after text.

Grades (worst first):
    scan-poor    pages with almost no text layer: needs OCR (or a vision parser) before it can be searched
    math-poor    symbol-font or encoding damage (private-use glyphs, "(cid:N)", "P 5 0.04"): numbers are suspect
    tables-poor  tables present but flattened to loose numbers: go back to the PDF for any table value
    good         none of the above was detected (a heuristic, not a guarantee)

Usage:
    python paper_convert.py paper.pdf -o papers_md/              # one paper
    python paper_convert.py papers/ -o papers_md/                # every .pdf and .txt in a folder
    python paper_convert.py paper.txt -o papers_md/              # pdftotext output, \\f between pages
    python paper_convert.py paper.pdf -o papers_md/ --abstract abstract.txt   # check abstract numbers against the text

Engines (--engine auto): pymupdf4llm (layout-aware, pipe tables), else pypdf. Both are optional installs;
the .txt route needs neither. Exit codes: 0 ok, 2 bad input or no engine. Standard library otherwise.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

SCHEMA = 1
MIN_PAGE_CHARS = 200
LIGATURES = {"ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl"}
SYMBOL_FONT_REPAIRS = [  # (pattern, replacement, why): statistics whose "=" or "<" glyph came out as another character
    (re.compile(r"\b(P|p|r|n|t|d|OR|HR|RR|SD|SE|df)\s+5\s+(?=[-−–]?\d)"), r"\1 = ", "'5' read as '=' in a statistic"),
    (re.compile(r"\b(P|p)\s+,\s*(?=0?\.\d)"), r"\1 < ", "',' read as '<' in a p-value"),
    (re.compile(r"(?<=\s)¼(?=\s)"), "=", "'¼' read as '='"),
]
PUA_RE = re.compile("[-�]")
CID_RE = re.compile(r"\(cid:\d+\)")
STAT_LEFTOVER_RE = re.compile(r"\b[Pp]\s+[5¼]\s+0?\.\d")
TABLE_CAPTION_RE = re.compile(r"^\W*Table\s+[A-Z]?\d+", re.I | re.M)
PIPE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$", re.M)
_NUM = r"[-\u2212+]?\(?\d[\d.,%)]*\)?"
NUMERIC_RUN_RE = re.compile(rf"^(?:[ \t]*{_NUM}[ \t]+){{4,}}{_NUM}[ \t]*$", re.M)  # 5+ numbers on one line
NUMBER_RE = re.compile(r"(?<![\w.])[-−]?\d+(?:\.\d+)?%?")


def repair_page(text: str, page: int) -> tuple[str, list[dict]]:
    """Fix ligatures and symbol-font statistics; return the new text and a list of logged repairs."""
    text = text.translate(str.maketrans(LIGATURES))
    repairs: list[dict] = []
    for pattern, repl, why in SYMBOL_FONT_REPAIRS:
        def sub(m: re.Match, repl=repl, why=why) -> str:
            after = m.expand(repl)
            repairs.append({"page": page, "before": m.group(0).strip(), "after": after.strip(), "why": why})
            return after
        text = pattern.sub(sub, text)
    return text, repairs


def grade_pages(pages: list[str]) -> tuple[str, list[str], dict]:
    """Return (grade, human-readable flags, stats) for converted pages."""
    flags: list[str] = []
    low = [i for i, t in enumerate(pages, 1) if len(re.sub(r"\s", "", t)) < MIN_PAGE_CHARS]
    # A short last page or a figure-only page is normal; flag a scan only when a real share of pages is empty.
    scan = len(low) >= max(1, len(pages) // 3) and len(low) > 0 and len(pages) > 0
    if scan:
        flags.append(f"{len(low)} of {len(pages)} pages have almost no text layer (pages {low[:10]}): OCR needed")
    body = "\n".join(pages)
    damage = len(PUA_RE.findall(body)) + len(CID_RE.findall(body)) + len(STAT_LEFTOVER_RE.findall(body))
    density = damage / max(len(body), 1) * 10_000
    math_poor = density > 3 or damage >= 10
    if damage:
        flags.append(f"{damage} damaged symbols or encodings ({density:.1f} per 10k chars): "
                     "statistics and equations are suspect")
    flat_pages = []
    for i, t in enumerate(pages, 1):
        has_caption = bool(TABLE_CAPTION_RE.search(t))
        pipe_rows = len(PIPE_ROW_RE.findall(t))
        numeric_runs = len(NUMERIC_RUN_RE.findall(t))
        if (has_caption and pipe_rows < 2 and numeric_runs >= 2) or (pipe_rows < 2 and numeric_runs >= 6):
            flat_pages.append(i)
    if flat_pages:
        flags.append(f"tables flattened to loose numbers on pages {flat_pages[:10]}: read table values from the PDF")
    grade = "scan-poor" if scan else "math-poor" if math_poor else "tables-poor" if flat_pages else "good"
    return grade, flags, {"low_text_pages": low, "damage": damage, "flat_table_pages": flat_pages}


def check_abstract(abstract: str, body: str) -> dict:
    """Check that every number quoted in the abstract also appears in the converted text."""
    def norm(n: str) -> str:
        return n.replace("−", "-").rstrip("%")

    body_numbers = {norm(n) for n in NUMBER_RE.findall(unicodedata.normalize("NFKC", body))}
    wanted = [norm(n) for n in NUMBER_RE.findall(unicodedata.normalize("NFKC", abstract))]
    missing = sorted({n for n in wanted if n not in body_numbers})
    return {"checked": len(set(wanted)), "missing": missing}


def extract_pages(path: Path, engine: str) -> tuple[list[str], str]:
    """Return (page texts, engine used) for a .pdf, or split a .txt on form feeds."""
    if path.suffix.lower() == ".txt":
        return path.read_text(encoding="utf-8", errors="replace").split("\f"), "text"
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"unsupported file type: {path.suffix}")
    if engine in ("auto", "pymupdf4llm"):
        try:
            import pymupdf4llm
            chunks = pymupdf4llm.to_markdown(str(path), page_chunks=True)
            return [c["text"] for c in chunks], "pymupdf4llm"
        except ImportError:
            if engine == "pymupdf4llm":
                raise RuntimeError("pymupdf4llm is not installed: pip install pymupdf4llm") from None
    try:
        from pypdf import PdfReader
        return [p.extract_text() or "" for p in PdfReader(str(path)).pages], "pypdf"
    except ImportError:
        raise RuntimeError("no PDF engine installed: pip install pymupdf4llm (or pypdf), or run `pdftotext` and "
                           "pass the .txt") from None


def convert(path: Path, out_dir: Path, engine: str, abstract: str | None) -> dict:
    """Convert one paper; write NAME.md and NAME.quality.json; return the summary."""
    raw_pages, used = extract_pages(path, engine)
    while raw_pages and not raw_pages[-1].strip():  # pdftotext ends with a trailing form feed
        raw_pages.pop()
    pages, repairs = [], []
    for n, text in enumerate(raw_pages, 1):
        fixed, r = repair_page(text, n)
        pages.append(fixed)
        repairs += r
    grade, flags, stats = grade_pages(pages)
    if repairs:
        flags.append(f"{len(repairs)} symbol-font repairs applied (listed in the sidecar): "
                     "verify the statistics against the PDF")
    report = {"schema": SCHEMA, "source": path.name, "engine": used, "pages": len(pages), "grade": grade,
              "flags": flags, "repairs": repairs, "stats": stats}
    if abstract is not None:
        report["abstract_numbers"] = check_abstract(abstract, "\n".join(pages))
        if report["abstract_numbers"]["missing"]:
            missing = ", ".join(report["abstract_numbers"]["missing"][:10])
            flags.append("numbers in the abstract not found in the text: " + missing)
    out_dir.mkdir(parents=True, exist_ok=True)
    md = "\n\n".join(f"<!-- page: {n} -->\n{t.strip()}" for n, t in enumerate(pages, 1))
    (out_dir / f"{path.stem}.md").write_text(md + "\n", encoding="utf-8")
    (out_dir / f"{path.stem}.quality.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                                                       encoding="utf-8")
    return report


def main() -> int:
    """Run the command-line interface."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", help="PDF or .txt files, or folders of them")
    ap.add_argument("-o", "--out", default="papers_md", help="output folder (default papers_md)")
    ap.add_argument("--engine", choices=["auto", "pymupdf4llm", "pypdf"], default="auto")
    ap.add_argument("--abstract", help="text file with the paper's abstract; its numbers are checked against the text")
    ap.add_argument("--json", action="store_true", help="print the per-paper reports as JSON")
    args = ap.parse_args()
    files: list[Path] = []
    for item in args.inputs:
        p = Path(item)
        if p.is_dir():
            files += sorted(f for f in p.rglob("*") if f.is_file() and f.suffix.lower() in {".pdf", ".txt"})
        elif p.is_file():
            files.append(p)
        else:
            print(f"error: {item} does not exist", file=sys.stderr)
            return 2
    if not files:
        print("error: no .pdf or .txt files found", file=sys.stderr)
        return 2
    if args.abstract and len(files) != 1:
        print("error: --abstract works with exactly one paper", file=sys.stderr)
        return 2
    abstract = Path(args.abstract).read_text(encoding="utf-8") if args.abstract else None
    reports = []
    for f in files:
        try:
            r = convert(f, Path(args.out), args.engine, abstract)
        except (RuntimeError, ValueError, OSError) as exc:
            print(f"error: {f}: {exc}", file=sys.stderr)
            return 2
        reports.append(r)
        print(f"{f.name} -> {Path(args.out) / (f.stem + '.md')}  grade={r['grade']} pages={r['pages']} "
              f"repairs={len(r['repairs'])}")
        for flag in r["flags"]:
            print(f"    - {flag}")
    if args.json:
        print(json.dumps(reports, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
