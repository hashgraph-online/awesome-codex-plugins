#!/usr/bin/env python3
"""Local, citable retrieval over a folder of papers: SQLite FTS5 (BM25) plus optional embeddings.

Search is for *locating* papers and passages. Synthesis should read the whole converted file
(`read`), not a handful of chunks. Feed it Markdown from `paper_convert.py` (page markers and a
quality grade), or any .md/.txt; plain PDFs are read through `pypdf` as a fallback.

Usage:
    python paper_index.py index papers_md/ --db corpus.sqlite            # incremental; --rebuild to start over
    python paper_index.py query "contrastive loss temperature" --db corpus.sqlite -k 8
    python paper_index.py query "..." --by-paper                          # which papers to read, not which chunks
    python paper_index.py embed --db corpus.sqlite --model BAAI/bge-base-en-v1.5   # optional: hybrid search
    python paper_index.py query "..." --mode hybrid                       # BM25 + vectors fused by RRF
    python paper_index.py read paper.md --pages 3-5 --db corpus.sqlite    # read the source, with its quality grade
    python paper_index.py eval questions.jsonl --db corpus.sqlite -k 8    # recall@k over known question->passage pairs
    python paper_index.py stats --db corpus.sqlite

Each hit carries a citation handle `file#chunk`, the section path, the page range and the
conversion grade of that paper. Chunks follow headings (about 400 words, never more than 600, never
crossing a heading); reference lists are not indexed; figure and table captions are their own chunks.

Exit codes: 0 ok, 1 eval below --min-recall, 2 bad input or an index from an older version.
Standard library only; numpy and sentence-transformers are needed for `embed` and hybrid queries.
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

DEFAULT_DB = "corpus.sqlite"
DEFAULT_MODEL = "BAAI/bge-base-en-v1.5"
SCHEMA_VERSION = "2"
TARGET_WORDS, MAX_WORDS, MIN_WORDS = 400, 600, 60
RRF_K = 60
POOL = 50

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS docs (path TEXT PRIMARY KEY, sha256 TEXT, title TEXT, n_chunks INTEGER,
                                 grade TEXT, n_pages INTEGER);
CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5(
    text, section, path UNINDEXED, chunk UNINDEXED, page_start UNINDEXED, page_end UNINDEXED,
    tokenize = 'porter unicode61');
CREATE TABLE IF NOT EXISTS vectors (chunk_id INTEGER, model TEXT, dim INTEGER, vec BLOB,
                                    PRIMARY KEY (chunk_id, model));
"""
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$|^(\d+(?:\.\d+)*)\.?\s+([A-Z][^\n]{2,80})$")
PAGE_RE = re.compile(r"^<!--\s*page:\s*(\d+)\s*-->\s*$")
CAPTION_RE = re.compile(r"^(?:\*\*)?(?:Figure|Fig\.|Table|Supplementary (?:Figure|Table))\s+[A-Z]?\d+", re.I)
REFS_RE = re.compile(r"^(references|bibliography|literature cited|works cited)$", re.I)
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9(\[])")


_OPEN: list[sqlite3.Connection] = []  # every connection opened by this run; main() closes them on exit


class IndexError_(Exception):
    """Raised for an unusable index or bad arguments; main() maps it to exit code 2."""


# --------------------------------------------------------------------------------------------- reading
def read_doc(path: Path) -> str:
    """Read a document as text; PDFs go through pypdf with page markers."""
    if path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader  # optional
        except ImportError:
            raise RuntimeError(
                "pypdf not installed; convert PDFs first (paper_convert.py, markitdown or liteparse)") from None
        pages = [page.extract_text() or "" for page in PdfReader(str(path)).pages]
        return "\n\n".join(f"<!-- page: {n} -->\n{t}" for n, t in enumerate(pages, 1))
    return path.read_text(encoding="utf-8", errors="replace")


def sidecar(path: Path) -> dict:
    """Load `<stem>.quality.json` written by paper_convert.py, or {} when absent or unreadable."""
    side = path.with_suffix(".quality.json")
    try:
        return json.loads(side.read_text(encoding="utf-8")) if side.exists() else {}
    except (OSError, json.JSONDecodeError):
        return {}


# ------------------------------------------------------------------------------------------- chunking
def paragraphs(text: str) -> list[tuple[str, int, int]]:
    """Split text into (paragraph, first_page, last_page); page markers are consumed, never kept."""
    out: list[tuple[str, int, int]] = []
    page, buf, start = 1, [], 1

    def flush() -> None:
        if buf:
            para = re.sub(r"-\n(?=[a-z])", "", "\n".join(buf)).strip()  # de-hyphenate PDF line breaks
            if para:
                out.append((para, start, page))
            buf.clear()

    for line in text.splitlines():
        m = PAGE_RE.match(line.strip())
        if m:
            page = int(m.group(1))
            continue
        if not line.strip():
            flush()
            continue
        if not buf:
            start = page
        buf.append(line.rstrip())
    flush()
    return out


def heading_of(para: str) -> tuple[int, str] | None:
    """Return (level, title) when a single-line paragraph is a heading."""
    if "\n" in para or len(para) >= 120:
        return None
    m = HEADING_RE.match(para)
    if not m:
        return None
    if m.group(1):
        return len(m.group(1)), m.group(2).strip().strip("*")
    return m.group(3).count(".") + 1, f"{m.group(3)} {m.group(4).strip()}"


def split_long(para: str) -> list[str]:
    """Split an over-long paragraph on sentence boundaries into pieces of about TARGET_WORDS words."""
    pieces, cur, n = [], [], 0
    for sent in SENTENCE_RE.split(para):
        w = len(sent.split())
        if cur and n + w > TARGET_WORDS:
            pieces.append(" ".join(cur))
            cur, n = [], 0
        cur.append(sent)
        n += w
    if cur:
        pieces.append(" ".join(cur))
    return pieces


def chunk_text(text: str) -> list[dict]:
    """Chunk a paper along its headings: dicts with text, section, page_start and page_end."""
    chunks: list[dict] = []
    stack: list[tuple[int, str]] = []
    skip_level = None  # inside a reference list until a heading of the same or higher level
    cur: dict | None = None

    def section() -> str:
        return " > ".join(t for _, t in stack)

    def flush() -> None:
        nonlocal cur
        if cur and cur["text"].strip():
            prev = chunks[-1] if chunks else None
            if (prev and prev["section"] == cur["section"] and not cur["caption"] and not prev["caption"]
                    and len(cur["text"].split()) < MIN_WORDS
                    and len(prev["text"].split()) + len(cur["text"].split()) <= MAX_WORDS):
                prev["text"] += "\n\n" + cur["text"]  # fold a tiny tail into the previous chunk of the same section
                prev["page_end"] = cur["page_end"]
            else:
                chunks.append(cur)
        cur = None

    for para, p0, p1 in paragraphs(text):
        h = heading_of(para)
        if h:
            flush()
            level, title = h
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, title))
            skip_level = level if REFS_RE.match(re.sub(r"^\d+(\.\d+)*\.?\s+", "", title)) else (
                skip_level if skip_level is not None and level > skip_level else None)
            continue
        if skip_level is not None:
            continue
        if CAPTION_RE.match(para):
            flush()
            chunks.append({"text": para, "section": (section() + " [caption]").strip(), "page_start": p0,
                           "page_end": p1, "caption": True})
            continue
        for piece in (split_long(para) if len(para.split()) > MAX_WORDS else [para]):
            words = len(piece.split())
            if cur and len(cur["text"].split()) + words > TARGET_WORDS:
                flush()
            if cur is None:
                cur = {"text": piece, "section": section(), "page_start": p0, "page_end": p1, "caption": False}
            else:
                cur["text"] += "\n\n" + piece
                cur["page_end"] = p1
    flush()
    return chunks


# --------------------------------------------------------------------------------------------- database
def open_db(db: str, rebuild: bool = False, create: bool = True) -> sqlite3.Connection:
    """Open the index, creating it or refusing one written by an incompatible version."""
    if not create and not Path(db).exists():
        raise IndexError_(f"no index at {db}; run `index` first")
    con = sqlite3.connect(db)
    _OPEN.append(con)
    names = {r[0] for r in con.execute("SELECT name FROM sqlite_master")}
    if rebuild:
        for t in ("vectors", "chunks", "docs", "meta"):
            con.execute(f"DROP TABLE IF EXISTS {t}")
        names = set()
    if "docs" in names:
        row = con.execute("SELECT value FROM meta WHERE key = 'schema'").fetchone() if "meta" in names else None
        if not row or row[0] != SCHEMA_VERSION:
            raise IndexError_(f"{db} was built by an older version; re-run `index --rebuild`")
    con.executescript(SCHEMA)
    con.execute("INSERT OR IGNORE INTO meta VALUES ('schema', ?)", (SCHEMA_VERSION,))
    con.commit()
    return con


def cmd_index(args: argparse.Namespace) -> int:
    """Index a folder incrementally (new or changed files only)."""
    root = Path(args.folder)
    if not root.is_dir():
        raise IndexError_(f"{args.folder} is not a folder")
    con = open_db(args.db, rebuild=args.rebuild)
    con.execute("INSERT OR REPLACE INTO meta VALUES ('root', ?)", (str(root.resolve()),))
    files = sorted(p for p in root.rglob("*") if p.suffix.lower() in {".md", ".txt", ".pdf"} and p.is_file())
    added = skipped = 0
    for f in files:
        rel = f.relative_to(root).as_posix()
        side = sidecar(f)
        digest = hashlib.sha256(f.read_bytes() + json.dumps(side, sort_keys=True).encode()).hexdigest()
        row = con.execute("SELECT sha256 FROM docs WHERE path = ?", (rel,)).fetchone()
        if row and row[0] == digest:
            skipped += 1
            continue
        try:
            text = read_doc(f)
        except RuntimeError as exc:
            print(f"skip {rel}: {exc}", file=sys.stderr)
            continue
        if row:
            drop_doc(con, rel)
        pieces = chunk_text(text)
        con.executemany(
            "INSERT INTO chunks (text, section, path, chunk, page_start, page_end) VALUES (?, ?, ?, ?, ?, ?)",
            [(c["text"], c["section"], rel, i, c["page_start"], c["page_end"]) for i, c in enumerate(pieces)])
        title = next((ln.lstrip("# ").strip() for ln in text.splitlines()
                      if ln.strip() and not PAGE_RE.match(ln.strip())), rel)[:200]
        n_pages = side.get("pages") or max([c["page_end"] for c in pieces] or [1])
        con.execute("INSERT OR REPLACE INTO docs VALUES (?, ?, ?, ?, ?, ?)",
                    (rel, digest, title, len(pieces), side.get("grade") or "ungraded", n_pages))
        added += 1
    present = {f.relative_to(root).as_posix() for f in files}
    for (path,) in con.execute("SELECT path FROM docs").fetchall():
        if path not in present:
            drop_doc(con, path)
    con.commit()
    print(f"indexed {added} documents, {skipped} unchanged -> {args.db}")
    return 0


def drop_doc(con: sqlite3.Connection, path: str) -> None:
    """Delete a document with its chunks and vectors."""
    con.execute("DELETE FROM vectors WHERE chunk_id IN (SELECT rowid FROM chunks WHERE path = ?)", (path,))
    con.execute("DELETE FROM chunks WHERE path = ?", (path,))
    con.execute("DELETE FROM docs WHERE path = ?", (path,))


# ------------------------------------------------------------------------------------------ embeddings
def embed_texts(model: str, texts: list[str], is_query: bool = False):
    """Return an L2-normalised float32 matrix of embeddings (needs numpy and sentence-transformers)."""
    try:
        import numpy as np
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError("embeddings need `pip install numpy sentence-transformers`") from exc
    cache = embed_texts.__dict__.setdefault("_models", {})
    if model not in cache:
        cache[model] = SentenceTransformer(model)
    if is_query and "bge" in model.lower():
        texts = ["Represent this sentence for searching relevant passages: " + t for t in texts]
    arr = cache[model].encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return np.asarray(arr, dtype="float32")


def cmd_embed(args: argparse.Namespace) -> int:
    """Embed every chunk that has no vector for the model (resumable)."""
    import numpy as np  # noqa: F401  (fail early with a clear message)

    con = open_db(args.db, create=False)
    for model in args.model or [DEFAULT_MODEL]:
        todo = con.execute("SELECT rowid, text FROM chunks WHERE rowid NOT IN "
                           "(SELECT chunk_id FROM vectors WHERE model = ?)", (model,)).fetchall()
        for i in range(0, len(todo), args.batch):
            batch = todo[i:i + args.batch]
            mat = embed_texts(model, [t for _, t in batch])
            con.executemany("INSERT OR REPLACE INTO vectors VALUES (?, ?, ?, ?)",
                            [(rid, model, mat.shape[1], mat[j].tobytes()) for j, (rid, _) in enumerate(batch)])
            con.commit()
        print(f"{model}: embedded {len(todo)} chunks")
    return 0


def vector_models(con: sqlite3.Connection) -> list[str]:
    """Models that have stored vectors."""
    return [r[0] for r in con.execute("SELECT DISTINCT model FROM vectors")]


def vector_ranking(con: sqlite3.Connection, model: str, query: str, pool: int) -> list[int]:
    """Rank chunk ids by cosine similarity to the query (brute-force; fine up to ~100k chunks)."""
    import numpy as np

    rows = con.execute("SELECT chunk_id, vec FROM vectors WHERE model = ?", (model,)).fetchall()
    if not rows:
        return []
    ids = [r[0] for r in rows]
    mat = np.vstack([np.frombuffer(r[1], dtype="float32") for r in rows])
    q = embed_texts(model, [query], is_query=True)[0]
    order = np.argsort(-(mat @ q))[:pool]
    return [ids[int(i)] for i in order]


# ---------------------------------------------------------------------------------------------- search
def fts_query(q: str) -> str:
    """Turn free text into a safe FTS5 query: quoted terms OR-ed, phrases kept."""
    phrases = re.findall(r'"([^"]+)"', q)
    rest = re.sub(r'"[^"]+"', " ", q)
    terms = [t for t in re.findall(r"[\w-]+", rest) if len(t) > 1]
    parts = [f'"{p}"' for p in phrases] + [f'"{t}"' for t in terms]
    return " OR ".join(parts) if parts else '""'


def bm25_ranking(con: sqlite3.Connection, query: str, pool: int) -> tuple[list[int], dict[int, str]]:
    """Rank chunk ids by BM25 and return highlighted snippets keyed by chunk id."""
    rows = con.execute("SELECT rowid, snippet(chunks, 0, '[', ']', ' ... ', 24) FROM chunks WHERE chunks MATCH ? "
                       "ORDER BY bm25(chunks) LIMIT ?", (fts_query(query), pool)).fetchall()
    return [r[0] for r in rows], {r[0]: r[1] for r in rows}


def rrf(rankings: list[list[int]]) -> list[tuple[int, float]]:
    """Reciprocal Rank Fusion: score = sum of 1 / (60 + rank) over every ranking."""
    score: dict[int, float] = {}
    for ranking in rankings:
        for rank, cid in enumerate(ranking, 1):
            score[cid] = score.get(cid, 0.0) + 1.0 / (RRF_K + rank)
    return sorted(score.items(), key=lambda kv: -kv[1])


def search(con: sqlite3.Connection, query: str, k: int, mode: str = "auto",
           full: bool = False) -> tuple[list[dict], str]:
    """Return (hits, mode_used). Modes: bm25, hybrid (error without embeddings), auto (hybrid when possible)."""
    bm, snippets = bm25_ranking(con, query, POOL)
    rankings, used = [bm], "bm25"
    if mode in ("hybrid", "auto"):
        models = vector_models(con)
        try:
            if not models:
                raise RuntimeError("no embeddings stored; run `embed` first")
            rankings += [vector_ranking(con, m, query, POOL) for m in models]
            used = "hybrid"
        except RuntimeError as exc:
            if mode == "hybrid":
                raise IndexError_(str(exc)) from exc
            if models:  # vectors exist but could not be used: say so rather than silently degrading
                print(f"note: {exc}; using BM25 only", file=sys.stderr)
    hits = []
    for cid, score in rrf(rankings)[:k]:
        text, section, p0, p1, path, chunk = con.execute(
            "SELECT text, section, page_start, page_end, path, chunk FROM chunks WHERE rowid = ?", (cid,)).fetchone()
        title, grade = con.execute("SELECT title, grade FROM docs WHERE path = ?", (path,)).fetchone()
        hit = {"cite": f"{path}#{chunk}", "paper": path, "title": title, "section": section,
               "pages": f"{p0}-{p1}" if p1 != p0 else str(p0), "grade": grade, "score": round(score, 4),
               "snippet": snippets.get(cid) or " ".join(text.split())[:200]}
        if full:
            hit["text"] = text
        hits.append(hit)
    return hits, used


def by_paper(hits: list[dict]) -> list[dict]:
    """Group chunk hits into papers ranked by summed score, each with its best passage."""
    papers: dict[str, dict] = {}
    for h in hits:
        p = papers.setdefault(h["paper"], {"paper": h["paper"], "title": h["title"], "grade": h["grade"],
                                           "score": 0.0, "best": h, "n_hits": 0})
        p["score"] = round(p["score"] + h["score"], 4)
        p["n_hits"] += 1
    return sorted(papers.values(), key=lambda p: -p["score"])


def cmd_query(args: argparse.Namespace) -> int:
    """Run a query."""
    con = open_db(args.db, create=False)
    hits, used = search(con, args.query, POOL if args.by_paper else args.k, args.mode, args.full)
    if args.by_paper:
        papers = by_paper(hits)[:args.k]
        if args.json:
            print(json.dumps(papers, indent=2, ensure_ascii=False))
        for p in papers if not args.json else []:
            b = p["best"]
            print(f"{p['paper']}  (grade {p['grade']}, {p['n_hits']} passages, score {p['score']})\n"
                  f"    {p['title']}\n    best: [{b['cite']}] {b['section'] or ''} p.{b['pages']}\n"
                  f"    {b['snippet']}\n")
        if not papers and not args.json:
            print("no matches")
        return 0
    if args.json:
        print(json.dumps(hits, indent=2, ensure_ascii=False))
    else:
        for h in hits:
            warn = "" if h["grade"] in ("good", "ungraded") else f" [grade {h['grade']}: check the PDF]"
            print(f"[{h['cite']}] {h['section'] or ''} p.{h['pages']} (score {h['score']}, {used}){warn}\n"
                  f"    {h['snippet']}\n")
        if not hits:
            print("no matches")
    return 0


def parse_pages(spec: str) -> tuple[int, int]:
    """Parse '3' or '3-5' into an inclusive page range."""
    m = re.fullmatch(r"(\d+)(?:-(\d+))?", spec.strip())
    if not m:
        raise IndexError_(f"bad --pages {spec!r}; use 3 or 3-5")
    a = int(m.group(1))
    return a, int(m.group(2) or a)


def cmd_read(args: argparse.Namespace) -> int:
    """Print a whole converted paper (or a page range) with its quality grade, for synthesis."""
    con = open_db(args.db, create=False)
    row = con.execute("SELECT grade, n_pages FROM docs WHERE path = ?", (args.path,)).fetchone()
    if not row:
        raise IndexError_(f"{args.path} is not in the index; use a path printed by `query`")
    root = args.root or (con.execute("SELECT value FROM meta WHERE key = 'root'").fetchone() or [None])[0]
    if not root:
        raise IndexError_("index has no recorded folder; pass --root")
    base = Path(root).resolve()
    file = (base / args.path).resolve()
    if base not in file.parents or not file.is_file():
        raise IndexError_(f"{args.path} is outside the indexed folder or missing")
    text = read_doc(file)
    note = ""
    if args.pages:
        lo, hi = parse_pages(args.pages)
        keep, page = [], 1
        for line in text.splitlines():
            m = PAGE_RE.match(line.strip())
            if m:
                page = int(m.group(1))
            if lo <= page <= hi:
                keep.append(line)
        text = "\n".join(keep)
    if row[0] not in ("good", "ungraded"):
        note = f" WARNING: conversion graded '{row[0]}'; verify tables, numbers and equations against the PDF."
    print(f"<!-- {args.path} | grade: {row[0]} | pages: {row[1]} |{note or ' ok'} -->\n{text}")
    return 0


def cmd_eval(args: argparse.Namespace) -> int:
    """Score retrieval on question->passage pairs (JSONL: q, expect_path, optional expect_text)."""
    con = open_db(args.db, create=False)
    try:
        cases = [json.loads(ln) for ln in Path(args.questions).read_text(encoding="utf-8").splitlines() if ln.strip()]
    except (OSError, json.JSONDecodeError) as exc:
        raise IndexError_(f"cannot read {args.questions}: {exc}") from exc
    found, rr, misses = 0, 0.0, []
    for case in cases:
        if "q" not in case or "expect_path" not in case:
            raise IndexError_("each line needs `q` and `expect_path` (optional `expect_text`)")
        hits, _ = search(con, case["q"], args.k, args.mode, full=True)
        want = case.get("expect_text", "").lower()
        rank = next((i for i, h in enumerate(hits, 1)
                     if h["paper"] == case["expect_path"] and (not want or want in h["text"].lower())), None)
        if rank:
            found += 1
            rr += 1 / rank
        else:
            misses.append(case["q"])
    n = len(cases) or 1
    recall = found / n
    print(f"{len(cases)} questions  recall@{args.k}={recall:.2f}  MRR={rr / n:.2f}  mode={args.mode}")
    for q in misses:
        print(f"  MISS: {q}")
    return 0 if recall >= args.min_recall else 1


def cmd_stats(args: argparse.Namespace) -> int:
    """Print corpus statistics."""
    con = open_db(args.db, create=False)
    docs, chunks = con.execute("SELECT COUNT(*), COALESCE(SUM(n_chunks), 0) FROM docs").fetchone()
    print(f"{docs} documents, {chunks} chunks in {args.db}")
    grades = con.execute("SELECT grade, COUNT(*) FROM docs GROUP BY grade ORDER BY 2 DESC").fetchall()
    print("grades: " + (", ".join(f"{g} {n}" for g, n in grades) or "none"))
    for model in vector_models(con):
        n = con.execute("SELECT COUNT(*) FROM vectors WHERE model = ?", (model,)).fetchone()[0]
        print(f"embeddings: {model} ({n} chunks)")
    return 0


def main() -> int:
    """Run the command-line interface."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def db_arg(p: argparse.ArgumentParser) -> None:
        p.add_argument("--db", default=DEFAULT_DB)

    i = sub.add_parser("index", help="index a folder of .md/.txt (or .pdf with pypdf)")
    i.add_argument("folder")
    db_arg(i)
    i.add_argument("--rebuild", action="store_true", help="drop the index first (needed after a version change)")
    e = sub.add_parser("embed", help="optional: embed chunks for hybrid search (numpy + sentence-transformers)")
    db_arg(e)
    e.add_argument("--model", action="append", help=f"repeatable; default {DEFAULT_MODEL}")
    e.add_argument("--batch", type=int, default=32)
    q = sub.add_parser("query")
    q.add_argument("query")
    db_arg(q)
    q.add_argument("-k", type=int, default=8)
    q.add_argument("--mode", choices=["auto", "bm25", "hybrid"], default="auto")
    q.add_argument("--by-paper", action="store_true", help="rank papers to read instead of chunks")
    q.add_argument("--json", action="store_true")
    q.add_argument("--full", action="store_true", help="include full chunk text")
    r = sub.add_parser("read", help="print a whole converted paper, optionally a page range")
    r.add_argument("path", help="paper path as printed by `query`")
    db_arg(r)
    r.add_argument("--pages", help="3 or 3-5")
    r.add_argument("--root", help="folder the paper lives in (default: the indexed folder)")
    v = sub.add_parser("eval", help="recall@k over a JSONL of questions with expected papers")
    v.add_argument("questions")
    db_arg(v)
    v.add_argument("-k", type=int, default=8)
    v.add_argument("--mode", choices=["auto", "bm25", "hybrid"], default="auto")
    v.add_argument("--min-recall", type=float, default=0.0, help="exit 1 below this recall")
    s = sub.add_parser("stats")
    db_arg(s)
    args = ap.parse_args()
    handlers = {"index": cmd_index, "embed": cmd_embed, "query": cmd_query, "read": cmd_read, "eval": cmd_eval,
                "stats": cmd_stats}
    try:
        return handlers[args.cmd](args)
    except IndexError_ as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except ImportError as exc:
        print(f"error: {exc}; install numpy and sentence-transformers for embeddings", file=sys.stderr)
        return 2
    finally:
        for con in _OPEN:
            con.close()
        _OPEN.clear()


if __name__ == "__main__":
    sys.exit(main())
