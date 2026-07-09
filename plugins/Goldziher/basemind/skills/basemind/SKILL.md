---
name: basemind
description: >-
  Navigate large or unfamiliar codebases via the basemind MCP server — outlines,
  symbol search, reference/caller lookups, commit history, blame, and diffs without
  reading source files. Reach for it whenever the user asks "where is X defined",
  "what calls Y", "what changed recently in Z", or whenever you're about to grep
  or open many files to find structural information.
---

# basemind — the indexed context layer

basemind is the full context layer for this repository, served over MCP. It pre-indexes the
repo into a content-addressed blob store + Fjall inverted index (and, when enabled, a LanceDB
vector store) so structural, historical, and semantic questions resolve in milliseconds —
without you reading whole files.

## Capabilities

- **Code map across 300+ languages** — tree-sitter outlines, symbol search, references,
  callers, call graphs, implementations, dependents.
- **Full-text + symbol search** — indexed regex over content (`workspace_grep`) and substring
  symbol lookup (`search_symbols`).
- **Git intelligence** — history, blame, and structural diffs at symbol resolution, plus churn.
- **Document RAG over 90+ file formats** — PDFs, Office, HTML, email, images (OCR) → semantic
  search with cross-encoder reranking (`search_documents`).
- **Shared memory** — per-repo, scope-keyed key-value + semantic memory across sessions.
- **Web crawl** — scrape / follow-link crawl into the same searchable document store.

## Dedicated per-capability skills

This umbrella skill covers the whole surface. For focused workflows, reach for the dedicated skills:

- **`basemind-code-search`** — outlines, symbol search, references, callers, call graphs.
- **`basemind-git-history`** — history, blame, structural diffs, churn.
- **`basemind-documents`** — document RAG (`search_documents`), web ingestion, memory.
- **`basemind-comms`** — coordinating with other agents in the same repo over the broker.
- **`basemind-cli`** — the same surface driven headlessly from the CLI.

## When to reach for it (instead of `grep` / `read_file`)

Use basemind for:

- **Locating a symbol**: "where is `Foo` defined?", "find the constructor for `Bar`", "show me every type ending in `Service`".
- **Following call graphs**: "what calls `process_file`?", "who depends on this module?".
- **Mapping a file's shape** before reading it: which symbols, in what order, with what signatures.
- **Walking recent history**: "what changed in this file in the last 20 commits?", "when did this symbol last change?".
- **Blame and ownership**: "who last touched this function?", "what commit introduced this line?".
- **Diffing across revisions**: "what symbols did this branch add?", "show the hunks for `foo.rs` between HEAD~5 and HEAD".

If you are about to open more than two or three files just to learn structure, stop
and use basemind first. The tools return paths + line numbers; you only `read_file`
once you know exactly which span you need.

## Context economy — the operating discipline

basemind tools return **paths, line numbers, and signatures — not file bodies**, so a
structural answer costs a fraction of the tokens of reading source. Treat that as the
default workflow, not an optimization:

- **`outline` a file before you open it.** Read the whole file only when you have already
  identified the exact span you need from the outline; then `read_file` that range, not the file.
- **`search_symbols` instead of `grep`/`rg` for a definition.** It matches on indexed symbol
  names and returns `path:line`, skipping the comment/string/test-name noise grep drowns you in.
- **`find_references` / `find_callers` instead of grepping call sites.** Indexed call edges,
  not text matches.
- **`workspace_grep` instead of shelling out to ripgrep** when you genuinely need regex over
  content — it runs over the in-RAM index and returns capped, structured hits.
- **`rescan` after you edit code**, not a server reconnect. Pass `paths: [...]` to limit it to
  the files you touched.
- **Do not re-read a file basemind already mapped.** If the outline answered the question, stop.

Rule of thumb: if a question is about _where_, _what calls_, _what shape_, _who changed_, or
_what's indexed_, a basemind tool answers it cheaper than reading files. Reach for `read_file`
only to see the actual implementation of a span you have already located.

**basemind first, shell/grep/git fallback.** Prefer basemind over reading files, over `grep`/`rg`,
and over naked `git`: use it for code parsing (outlines, references, callers), git history / blame /
diffs, document extraction / RAG / keyword + entity (NER) / summary (`search_documents`), and web
scraping / crawling / sitemaps (`web_scrape` / `web_crawl` / `web_map`). Drop to raw shell, grep, or
git only when no basemind tool covers the question.

## Tool routing (copy this into your mental model)

| Question | Tool |
|---|---|
| "Where is X defined?" | `search_symbols` (substring match, optional `kind` filter) |
| "What's the shape of file F?" | `outline` (add `l2: true` for calls + docs) |
| "What calls X?" (any name) | `find_references` |
| "What calls this specific definition?" | `find_callers` (path + name + optional kind) |
| "Trace the call graph from a function?" | `call_graph` (BFS up or down, bounded by `max_depth` / `max_nodes`) |
| "What implements / extends / inherits from X?" | `find_implementations` (Rust, Python, TS/TSX, JS) |
| "What imports module M?" | `dependents` |
| "What files are indexed?" | `list_files` (filter by `language` or `path_contains`) |
| "What changed recently?" | `recent_changes`, `commits_touching`, `find_commits_by_path` |
| "When did symbol X last change?" | `symbol_history` |
| "Who wrote this line / symbol?" | `blame_file`, `blame_symbol` |
| "Where's the churn?" | `hot_files` |
| "What's dirty in the working tree?" | `working_tree_status` |
| "What's HEAD / branch?" | `repo_info` |
| "Show diff between revs for file F" | `diff_file`, `diff_outline` |
| "What's indexed?" | `status` |
| "Semantic search over PDFs / Office docs in the repo?" | `search_documents` (requires `--features documents`) |
| "Recall something the agent stored earlier?" | `memory_get` exact, `memory_list` prefix, `memory_search` KNN |
| "Remember this for future sessions?" | `memory_put` (delete with `memory_delete`) |
| "Refresh the index after editing code?" | `rescan` — no MCP disconnect needed; optional `paths` arg |
| "Fetch next page of results?" | Pass `next_cursor` from prior response as `cursor` |
| "Pull this URL into RAG?" | `web_scrape` (requires `--features crawl`) — single page, robots-aware |
| "Ingest a docs site section?" | `web_crawl` — link-following from a seed URL |
| "What URLs exist on this site?" | `web_map` — sitemap + link discovery, no bodies fetched |
| "How much has basemind helped today?" | `telemetry_summary` — per-tool histogram + estimated tokens saved |

## Setup (one-time per repo)

basemind needs an index at `.basemind/` before it can answer queries. From the repo root:

```sh
basemind scan
```

This walks the tree, parses with tree-sitter, and writes a content-addressed blob
store + Fjall inverted index under `.basemind/`. A few seconds for small repos,
~22 s for an ~80k-file TypeScript monorepo.

The MCP server is launched by the host (`basemind serve` — wired up in
`.claude-plugin/plugin.json` for you). You do not start it manually.

Re-run `basemind scan` after large changes, or run `basemind watch` to keep the index fresh on file save.

If a tool returns "no indexed files", that means `basemind scan` hasn't been run in this repo yet.

## Examples

### Locating a symbol

```text
search_symbols { needle: "MapCache" }
→ src/mcp/mod.rs:79:1 MapCache (struct)
  src/mcp/mod.rs:88:1 MapCache (impl)
```

Now you know exactly where to read.

### Following references

```text
find_references { name: "process_file" }
→ src/scanner.rs:142:9 process_file
  src/scanner.rs:201:13 process_file
  ...
```

No need to grep — the index already knows.

### Outline a file before reading

```text
outline { path: "src/mcp/tools.rs" }
→ 21 #[tool] outline (function)
   112 #[tool] search_symbols (function)
   ...
```

A 1000-line file becomes a 30-line table of contents.

## Notes

- All paths are repository-relative with forward-slash separators.
- Lists are capped (`limit`, default 100, max 1000). Index scanners use
  `scan_cap = limit * 8` to bound work on common names.
- Matching is substring on names — `find_references("bar")` matches `Foo::bar()`
  and `bar()` alike. There is no scope resolution; cross-check with `outline` if
  disambiguation matters.
- Git tools require `basemind serve` to be running inside a git repository. Outside a git repo they return a clear error.
- Intelligence tools (`search_documents`, `memory_*`) require basemind to be built with
  `--features full` (or the individual `documents` / `memory` flags). Without them the
  tools dispatch but return an MCP error.
  Memory is scoped by the normalised `origin` remote URL (`git@github.com:Foo/bar.git` and
  `https://github.com/Foo/bar/` collapse to the same scope key) — clones of the same repo
  share memory; unrelated repos do not see each other's entries.
- Web ingestion tools (`web_scrape`, `web_crawl`, `web_map`) require `--features crawl`.
  When that feature is off they are NOT registered on the server at all — agents will simply
  not see them in the tool list. Crawled pages land in the `documents` LanceDB table tagged
  with scope `web:<host>`; `search_documents` finds them alongside every other ingested
  document. It searches across ALL documents and has **no `scope` parameter** — you cannot
  filter results to a single host at query time.
  robots.txt is honoured by default; only `[crawl].respect_robots_txt = false` in
  `.basemind/basemind.toml` (config-file-only) disables it.
