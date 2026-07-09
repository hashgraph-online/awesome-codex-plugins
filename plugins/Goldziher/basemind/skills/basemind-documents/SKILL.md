---
name: basemind-documents
description: >-
  Semantic + full-text search over documents and the web via basemind's RAG store — PDFs, Office,
  HTML, email, images (OCR), plus scraped/crawled web pages, with cross-encoder reranking, keyword
  and named-entity (NER) filters, and per-document summaries. Reach for it whenever the user asks to
  "search the docs / PDFs", "find where a topic is discussed", "pull this URL into context", or
  "what does the documentation say about X".
---

# basemind-documents — document RAG and web ingestion

basemind extracts 90+ file formats (PDF, Office, HTML, email, images via OCR) into a LanceDB vector
store and answers meaning-based queries with cross-encoder reranking. Web pages scraped or crawled
into the same store are searchable the same way. This is the surface for "find the passage about X",
not "grep for the string X".

**basemind first, open-the-file fallback.** Prefer `search_documents` over opening PDFs/Office/HTML
by hand, and the web tools over ad-hoc fetching. For source code use `basemind-code-search` instead —
this skill is for prose and documents.

## Requirements

- `search_documents` and the `memory_*` tools need a build with `--features documents` (or `full`).
  Without them the tools dispatch but return an MCP error.
- Web ingestion (`web_scrape` / `web_crawl` / `web_map`) needs `--features crawl`. When that feature
  is **off** these tools are not registered at all — they simply won't appear in the tool list.
- Documents must be scanned first: `basemind scan` with the documents feature extracts and embeds
  them into `.basemind/`. See the `basemind-scan` skill.

## Tool routing

| Question | MCP tool | CLI |
|---|---|---|
| "Semantic search over PDFs/Office/HTML docs?" | `search_documents` | `basemind memory search-documents "query"` |
| "Narrow to docs mentioning an entity?" | `search_documents { entity_category: "…" }` | *(MCP only)* |
| "Narrow to docs with a keyword?" | `search_documents { keywords_contains: "…" }` | *(MCP only)* |
| "Filter by file type?" | `search_documents { mime_type: "application/pdf" }` | *(MCP only)* |
| "Pull a single URL into RAG?" | `web_scrape` (robots-aware) | `basemind web scrape <url>` |
| "Ingest a docs site section?" | `web_crawl` (link-following from a seed) | `basemind web crawl <seed-url>` |
| "What URLs exist on this site?" | `web_map` (sitemap + link discovery, no bodies) | `basemind web map <url>` |
| "Recall something the agent stored earlier?" | `memory_get` exact / `memory_list` prefix / `memory_search` KNN | `basemind memory get "key"` / `list` / `search "q"` |
| "Remember this for future sessions?" | `memory_put` (delete with `memory_delete`) | `basemind memory put "key" "value"` |

## What a hit carries

`search_documents` returns chunk-level hits with `path`, `chunk_idx`, the matched `text`, byte span,
vector `distance`, and — when enabled at scan time — a cross-encoder `rerank_score` in `[0,1]`, the
parent document's `keywords` and named `entities` (NER), and a document-level `summary`. Use
`entity_category` / `keywords_contains` to constrain to documents whose parent carries a matching
entity or keyword (AND-combined when both are set).

## Examples

```text
search_documents { query: "how is the index schema versioned", limit: 5 }
→ docs/architecture.pdf#chunk3  rerank 0.91  "INDEX_SCHEMA_VER reads from RELEASE_MINOR…"
  README.md#chunk12             rerank 0.74  "…wipe-on-mismatch rebuilds from source…"

web_crawl { url: "https://docs.example.com/guide" }
→ ingested 24 pages under scope "web:docs.example.com"

search_documents { query: "rate limiting", mime_type: "text/html" }
→ web:docs.example.com/limits#chunk1  rerank 0.88  "requests are capped at …"
```

## Notes

- Crawled/scraped pages land in the `documents` table tagged with a `scope` of `web:<host>`
  (override on `web_scrape`); `search_documents` searches across every ingested document.
- `robots.txt` is honoured by default; only `[crawl].respect_robots_txt = false` in
  `.basemind/basemind.toml` (config-file-only) disables it. The crawler SSRF-blocks private/loopback
  hosts unless `[crawl].allow_private_network = true`.
- Memory is scoped by the normalised git `origin` URL, so clones of the same repo share stored
  entries and unrelated repos do not.
- Lists are capped (`limit`, default 100, max 1000); use `next_cursor` → `cursor` to page.

For code structure see `basemind-code-search`; for git history see `basemind-git-history`; for agent
coordination see `basemind-comms`.
