---
name: basemind-scan
description: >-
  Build or refresh the basemind index by running `basemind scan` via the CLI. Use this when
  basemind reports "no index" / "no indexed files", when the MCP server isn't available, or
  after large changes when the index is stale. Works without the MCP server — it shells the
  basemind binary directly.
---

# basemind-scan — build or refresh the index (no MCP server required)

basemind answers code-map questions from an index under `.basemind/`. That index is built by
`basemind scan`. This skill runs the scan via the **CLI**, so it works even when the MCP server
(`basemind serve`) is not running — which is exactly the situation when basemind reports
**"no index"** or **"no indexed files"**, or when MCP tools aren't loaded in the session.

## When to use

- basemind / the statusline reports **no index** for this repo.
- An MCP tool returns "no indexed files" or empty results that should not be empty.
- The MCP server isn't running or isn't reachable, and you need the code map.
- The index is stale after large changes and you want a full rebuild.

## How to run

From the repository root:

```sh
basemind scan            # full working-tree scan
basemind scan <path>     # scope to a path (incremental)
```

Finding the binary (in order of preference):

1. `basemind` on `PATH`.
2. The plugin-managed binary the MCP launcher caches:
   `${XDG_CACHE_HOME:-~/.cache}/basemind/bin/<version>/basemind`.
3. A dev build: `cargo build --release` then `./target/release/basemind scan`.

## Notes

- The scan writes the content-addressed blob store + Fjall inverted index under `.basemind/`.
  Seconds for small repos; ~22 s for an ~80k-file TypeScript monorepo.
- Files tree-sitter doesn't recognize as code go through the document tier; anything that isn't an
  extractable document (e.g. an exotic source file) is **skipped**, not counted as a failure.
- If a `basemind serve` MCP server is already running for this repo it holds the store lock, so a
  CLI `scan` will fail with a lock error. Use the `rescan` MCP tool (it re-indexes in-process)
  instead, or stop the server first.
- **Indexing directories outside the repo** — set `scan.extra_roots` in `.basemind/basemind.toml`
  to a list of absolute paths (e.g. a Bazel external repo cache) to index them alongside the repo.
  Their files are keyed by absolute path (so results for them are absolute, not repo-relative) and
  are (re-)indexed on a full `scan` only — the live watcher does not track them. Git tools (blame)
  don't apply to external files; the code map (symbols / references / outlines) and document search
  do.
- After a successful scan, both the MCP tools and `basemind query …` have a fresh index.
- The CLI shares the exact same `.basemind/` index as the MCP server — see the `basemind-cli`
  skill for the full query surface, or `basemind-code-search` / `basemind-git-history` /
  `basemind-documents` for the per-capability workflows.
