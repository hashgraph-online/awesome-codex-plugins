---
name: reviewer_sync-codebase
description: Build or update the reviewer base index (vector store + code graph) from a local repo clone. Use when the user asks to "index the codebase", "build the index", "sync the code", "rebuild the graph", "просиндексируй код", "построй индекс".
---

# Sync Codebase

Builds or updates the reviewer base index — vector embeddings (Postgres/pgvector) and code graph
(Neo4j) — from a local repo clone using `reviewer index`. This is a one-time setup operation;
subsequent runs are incremental (only changed files are re-embedded).

## Inputs

Parse from $ARGUMENTS (all optional):
- `--path <path>`: path to the local repo clone. Default: current working directory.
- `--ref <branch>`: git ref to index. Default: `main`.
- `--repo <owner/name>`: repo identifier for multi-repo setups. If omitted, derived automatically
  from `git remote get-url origin`.
- `--backend <auto|scip|treesitter>`: graph backend override. Default: `auto` (SCIP if in PATH,
  else tree-sitter).

## Pipeline

1. **Resolve inputs.** If `--path` not given, use the current working directory. If `--ref` not
   given, use `main`. If `--repo` not given, run:
   ```bash
   git -C <path> remote get-url origin
   ```
   Strip `.git` suffix, extract the last two path segments (`owner/name`).

2. **Check prerequisites.** Verify:
   - `uvx` is available: `uvx --version` succeeds.
   - The path is a git repo: `git -C <path> rev-parse --git-dir` succeeds.
   - The reviewer MCP server is reachable (run `reviewer check` or confirm the user has `.env`
     configured with `PG_DSN`, `NEO4J_URI`, `VOYAGE_API_KEY`).
   - Docker services are up if using the default stack: `docker compose ps` shows `paradedb` and
     `neo4j` running.
   - Stop and tell the user what is missing if any check fails.

3. **Run indexing.**
   ```bash
   uvx --from rag-reviewer reviewer index <path> --ref <ref>
   ```
   Add `--repo <owner/name>` if resolved or provided. Stream the output to the user.

   Expected duration: seconds for small repos, minutes for large ones — Voyage free tier
   (3 RPM / 10K TPM) causes throttling with automatic retry/backoff. That is normal, not an error.
   Use `--limit N` (if supported) for a quick smoke run.

4. **Verify.** After indexing completes, optionally run a diagnostic search to confirm the corpus:
   ```bash
   uvx --from rag-reviewer reviewer search "your query here"
   ```
   Or call `search_code` via the reviewer MCP tools directly.

5. **Report.** Summarise the output: chunks indexed/updated, graph nodes/edges upserted, warnings
   (e.g. "SCIP unavailable, fell back to tree-sitter"). If the SCIP backend was used, note that
   `IMPLEMENTS` edges and full call-graph accuracy are available; if tree-sitter, only `CALLS` by
   name are available.

## Notes

- This indexes the **local clone on disk** — not via GitHub API. The repo must be cloned locally
  before running.
- For accurate graph with `IMPLEMENTS` edges: install `scip-python` first:
  ```bash
  npm install -g @sourcegraph/scip-python
  ```
  Then re-run — `GRAPH_BACKEND=auto` picks it up automatically.
- After `reviewer index`, individual PR reviews (`reviewer_review-pr`) trigger **incremental**
  re-sync of changed files automatically via `prepare_review`. Full re-index is only needed when
  the base branch diverges significantly or after a fresh deploy.
- For task graph sync (Yougile/Jira board), use `reviewer_sync-tasks` instead.
