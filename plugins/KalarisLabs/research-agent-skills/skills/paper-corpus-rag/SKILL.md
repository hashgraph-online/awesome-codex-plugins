---
name: paper-corpus-rag
description: Build grounded question answering and retrieval-augmented generation (RAG) over your own collection of research papers, with answers that cite the exact paper and passage. Use when a user wants to "chat with" or search a folder of PDFs, synthesize evidence across a literature corpus, find which paper says X, or build a vector/hybrid index with SQLite FTS5, pgvector (Postgres), Chroma, Qdrant or FAISS. Includes a zero-dependency local full-text index with citable hits.
license: MIT
compatibility: Python 3.9+ with SQLite FTS5 (standard in CPython builds). Optional pypdf, sentence-transformers, psycopg/pgvector, chromadb or qdrant-client for the vector tiers.
metadata:
  version: "1.0"
  category: knowledge-and-rag
  maintainer: Kalaris Labs
  author: Kalaris Labs (Sayan Chowdhury)
  tags: RAG, retrieval, vector database, pgvector, Chroma, Qdrant, FAISS, SQLite, full-text search, literature synthesis
---

# RAG over a Research Paper Corpus

The goal is answers a researcher can check: every claim is traceable to a
specific passage of a specific paper. Retrieval quality and citation discipline
matter more than the choice of vector database.

To discover *new* candidate papers before building your local collection, use
`firecrawl-research-index` for hosted paper search and passage reads. Save only
papers you have a lawful copy of, with their DOI or source ID. This skill indexes
the user's own files; Firecrawl's hosted index is not a local corpus download.

## Tier 0: citable full-text search in one minute (no dependencies)

1. Convert PDFs to Markdown first (layout-aware converters beat raw PDF text): use the
   `markitdown` or `liteparse` skill, or `pip install pypdf` for the built-in fallback.
2. Index and query:

```bash
python scripts/paper_index.py index papers_md/ --db corpus.sqlite      # incremental: re-run after adding papers
python scripts/paper_index.py query "effect of batch size on calibration" --db corpus.sqlite -k 8
python scripts/paper_index.py query '"label smoothing" calibration' --db corpus.sqlite --json --full
```

Each hit is `file#chunk` + section heading + BM25 score. Quote phrases for exact matches.
BM25 is strong for scientific text full of exact terms (gene names, method names, datasets),
so start here before adding embeddings.

## Tier 1: semantic and hybrid retrieval

Add dense embeddings when queries are conceptual ("methods that avoid labeled data").
Use hybrid scoring: BM25 and vector ranks fused with Reciprocal Rank Fusion (RRF),
`score = Σ 1/(60 + rank)`. It is robust and needs no tuning.

Embedding model choice: a scientific-domain or strong general model from
`sentence-transformers` (see that skill). Embed **chunks**, not whole papers. Store the
model name and dimension with the index, because changing models means re-embedding.

**pgvector (Postgres).** Best when you already run Postgres or need SQL filters (year, venue, author):

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE chunks (id bigserial PRIMARY KEY, paper_id text, chunk int, section text,
                     body text, tsv tsvector GENERATED ALWAYS AS (to_tsvector('english', body)) STORED,
                     embedding vector(768));
CREATE INDEX ON chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ON chunks USING gin (tsv);
-- hybrid: fetch top-k from each, fuse with RRF in the application
SELECT id FROM chunks ORDER BY embedding <=> $1 LIMIT 50;
SELECT id FROM chunks WHERE tsv @@ websearch_to_tsquery('english', $2)
  ORDER BY ts_rank(tsv, websearch_to_tsquery('english', $2)) DESC LIMIT 50;
```

**Chroma / Qdrant / FAISS.** Local-first prototyping (Chroma), production filtering and
payloads (Qdrant), or in-memory at scale (FAISS). See the `chroma`, `qdrant-vector-search`
and `faiss` skills for APIs. Keep `paper_id`, `chunk`, `section`, `year` as metadata on every vector.

## Chunking rules for papers

- 800-1500 characters with 10-20% overlap. Split on paragraph boundaries, never mid-sentence.
- Keep the section heading with each chunk ("Methods > Training details"), since it disambiguates.
- Index figure/table captions as their own chunks. Drop reference lists from the main index
  (they pollute BM25), but keep them in a separate table for citation lookups.
- Store bibliographic metadata (DOI, title, authors, year) per paper, looked up by DOI, not guessed.

## Answering protocol (grounding)

1. Retrieve 8-20 chunks. Re-rank if a cross-encoder is available.
2. Answer **only** from retrieved text. Cite every factual sentence as `[file#chunk]`
   (or author-year once mapped to the bibliography).
3. If the corpus does not contain the answer, say so. Do not fill gaps from memory.
4. When papers disagree, present both with citations rather than picking one silently.
5. For quantitative claims, quote the number verbatim with its context (dataset, metric, split).

## Integrity rules

- Never fabricate a citation handle or quote. Every cited `file#chunk` must exist in the index output.
- Verify numbers against the source passage before reporting them.

## Evaluation

Before trusting a pipeline, write 20-50 question→expected-passage pairs from the corpus
and measure recall@k of retrieval. Most "hallucination" in paper QA is actually a
retrieval miss. Re-check after changing chunking, the embedding model or the corpus.

## Related skills

`research-knowledge-graph` (citation/concept graphs of the same corpus),
`markitdown`, `liteparse`, `sentence-transformers`, `chroma`, `qdrant-vector-search`,
`faiss`, `open-notebook`, `literature-review`, `firecrawl-research-index`.
