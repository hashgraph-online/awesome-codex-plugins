#!/usr/bin/env python3
"""Local, citable full-text search over a folder of papers (SQLite FTS5, BM25).

Zero-dependency retrieval layer for RAG over research literature. Converts
nothing itself: feed it .md/.txt produced by a PDF converter (e.g. the
`markitdown` or `liteparse` skills). If `pypdf` is installed, plain PDFs are
read directly as a fallback.

Usage:
    python paper_index.py index papers/ --db corpus.sqlite          # (re)index a folder
    python paper_index.py query "contrastive loss temperature" --db corpus.sqlite -k 8
    python paper_index.py query "..." --db corpus.sqlite --json      # for programmatic use
    python paper_index.py stats --db corpus.sqlite

Each hit carries a stable citation handle `file#chunk` plus the nearest section
heading, so answers can cite exactly where evidence came from.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

SCHEMA = """
CREATE TABLE IF NOT EXISTS docs (path TEXT PRIMARY KEY, sha256 TEXT, title TEXT, n_chunks INTEGER);
CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5(
    text, section, path UNINDEXED, chunk UNINDEXED, tokenize = 'porter unicode61');
"""
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$|^(\d+(?:\.\d+)*)\s+([A-Z][^\n]{2,80})$", re.M)


def read_doc(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader  # optional
        except ImportError:
            raise RuntimeError("pypdf not installed; convert PDFs to Markdown first (markitdown/liteparse skills)")
        return "\n\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
    return path.read_text(encoding="utf-8", errors="replace")


def chunk_text(text: str, size: int = 1200, overlap: int = 200) -> list[tuple[str, str]]:
    """Split into ~size-char chunks on paragraph boundaries; return (section, chunk) pairs."""
    text = re.sub(r"-\n(?=[a-z])", "", text)          # de-hyphenate line breaks from PDFs
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, buf, section, buf_section = [], "", "", ""
    for p in paras:
        m = HEADING_RE.match(p)
        if m and len(p) < 120:
            section = (m.group(2) or m.group(4) or "").strip()
        if buf and len(buf) + len(p) > size:
            chunks.append((buf_section, buf))
            buf = buf[-overlap:] + "\n\n" + p if overlap else p
            buf_section = section
        else:
            buf = f"{buf}\n\n{p}" if buf else p
            buf_section = buf_section or section
    if buf:
        chunks.append((buf_section, buf))
    return chunks


def cmd_index(args: argparse.Namespace) -> int:
    root = Path(args.folder)
    con = sqlite3.connect(args.db)
    con.executescript(SCHEMA)
    files = sorted(p for p in root.rglob("*") if p.suffix.lower() in {".md", ".txt", ".pdf"} and p.is_file())
    added = skipped = 0
    for f in files:
        rel = f.relative_to(root).as_posix()
        digest = hashlib.sha256(f.read_bytes()).hexdigest()
        row = con.execute("SELECT sha256 FROM docs WHERE path = ?", (rel,)).fetchone()
        if row and row[0] == digest:
            skipped += 1
            continue
        try:
            text = read_doc(f)
        except RuntimeError as exc:
            print(f"skip {rel}: {exc}", file=sys.stderr)
            continue
        con.execute("DELETE FROM chunks WHERE path = ?", (rel,))
        pieces = chunk_text(text, args.chunk_size, args.overlap)
        con.executemany("INSERT INTO chunks (text, section, path, chunk) VALUES (?, ?, ?, ?)",
                        [(t, s, rel, i) for i, (s, t) in enumerate(pieces)])
        title = next((ln.lstrip("# ").strip() for ln in text.splitlines() if ln.strip()), rel)[:200]
        con.execute("INSERT OR REPLACE INTO docs VALUES (?, ?, ?, ?)", (rel, digest, title, len(pieces)))
        added += 1
    present = {f.relative_to(root).as_posix() for f in files}
    for (path,) in con.execute("SELECT path FROM docs").fetchall():
        if path not in present:
            con.execute("DELETE FROM chunks WHERE path = ?", (path,))
            con.execute("DELETE FROM docs WHERE path = ?", (path,))
    con.commit()
    print(f"indexed {added} documents, {skipped} unchanged -> {args.db}")
    return 0


def fts_query(q: str) -> str:
    """Turn free text into a safe FTS5 query: quoted terms OR-ed, phrases kept."""
    phrases = re.findall(r'"([^"]+)"', q)
    rest = re.sub(r'"[^"]+"', " ", q)
    terms = [t for t in re.findall(r"[\w-]+", rest) if len(t) > 1]
    parts = [f'"{p}"' for p in phrases] + [f'"{t}"' for t in terms]
    return " OR ".join(parts) if parts else '""'


def cmd_query(args: argparse.Namespace) -> int:
    con = sqlite3.connect(args.db)
    rows = con.execute(
        "SELECT path, chunk, section, snippet(chunks, 0, '[', ']', ' ... ', 24), bm25(chunks), text "
        "FROM chunks WHERE chunks MATCH ? ORDER BY bm25(chunks) LIMIT ?", (fts_query(args.query), args.k)).fetchall()
    hits = [{"cite": f"{p}#{c}", "section": s, "score": round(-b, 3), "snippet": sn,
             **({"text": t} if args.full else {})} for p, c, s, sn, b, t in rows]
    if args.json:
        print(json.dumps(hits, indent=2, ensure_ascii=False))
    else:
        for h in hits:
            print(f"[{h['cite']}] {h['section'] or ''} (score {h['score']})\n    {h['snippet']}\n")
        if not hits:
            print("no matches")
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    con = sqlite3.connect(args.db)
    docs, chunks = con.execute("SELECT COUNT(*), COALESCE(SUM(n_chunks), 0) FROM docs").fetchone()
    print(f"{docs} documents, {chunks} chunks in {args.db}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("index")
    i.add_argument("folder")
    i.add_argument("--db", default="corpus.sqlite")
    i.add_argument("--chunk-size", type=int, default=1200)
    i.add_argument("--overlap", type=int, default=200)
    q = sub.add_parser("query")
    q.add_argument("query")
    q.add_argument("--db", default="corpus.sqlite")
    q.add_argument("-k", type=int, default=8)
    q.add_argument("--json", action="store_true")
    q.add_argument("--full", action="store_true", help="include full chunk text")
    s = sub.add_parser("stats")
    s.add_argument("--db", default="corpus.sqlite")
    args = ap.parse_args()
    return {"index": cmd_index, "query": cmd_query, "stats": cmd_stats}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
