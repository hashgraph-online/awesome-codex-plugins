---
name: reviewer_summarize-subsystems
description: Precompute concise per-subsystem summaries (GraphRAG community summaries) over the base code index, so ask / PR-walkthrough get a cheap high-level prior. Use when the user asks to build/refresh subsystem summaries ("просуммируй подсистемы", "построй обзоры модулей", "summarize subsystems"). Requires a built base index + the reviewer MCP server.
---

# Summarize subsystems (community summaries)

Cluster the base code graph into subsystems (by module path) and write a short, **grounded**
summary for each, persisted for `ask` / PR-walkthrough to use as a cheap high-level prior. This
skill reads code and writes summaries to the reviewer store; it does NOT modify code or post to
GitHub.

**Always write summaries and answer the user in Russian** (the project language), regardless of this
file's language. Tool calls, code identifiers and `path:line` stay verbatim.

## Tools

<!-- include: _common/tool-usage.md -->
Plus `list_subsystem_clusters`, `index_subsystem_summary` and `prune_subsystem_summaries`
(reviewer MCP), and the harness `Read`.

## Pipeline

1. **Resolve repo/branch.**

<!-- include: _common/branch-selection.md -->

2. **List clusters.** Call `list_subsystem_clusters(repo, branch)`. Empty / `note` about an empty
   index → tell the user (in Russian) to run `/reviewer_sync-codebase` first, then stop. The response
   carries `depth` (the applied cluster depth), `depth_source` (`env` | `.review.yml` | `arg`),
   `deferred` (stale clusters held back this pass under the cost cap, env `SUMMARY_REBUILD_CAP`),
   `orphans` (stored summaries whose `cluster_key` is no longer a current cluster), and the
   (already cap-capped) `clusters`.

3. **Preflight — echo the applied depth and ask for confirmation (gate the run).** BEFORE summarizing,
   show the user (in Russian):
   - the applied `depth` and where it came from (`depth_source`: env `SUMMARY_CLUSTER_DEPTH`, the repo's
     `.review.yml`, or an explicit arg);
   - how many clusters there are and at what path level — e.g. «depth=2 → 15 кластеров уровня
     `reviewer/index`» — sampling a few `cluster_key`s from `clusters`;
   - how many are `stale` vs fresh, plus `deferred` (held back by the cap).
   - If `orphans > 0`, **warn**: the depth changed or modules were removed, so N summaries are orphaned;
     a full (uncapped) pass will rebuild and prune them.
   - State the invariant explicitly: `cluster_key` depends on depth, so **changing depth triggers a
     full rebuild of every summary** (old-depth summaries orphan and get pruned).
   Then **ask the user to confirm** before running. If they decline, stop without summarizing or pruning.

4. **Choose the summary model (only if any cluster is `stale == true`).** A subsystem summary is a
   coarse, high-level prior — a small/cheap model is appropriate, and reviewing on an expensive model
   burns tokens. Ask the user which model tier to use for writing summaries, defaulting to a cheap
   tier (e.g. Haiku/Sonnet/Fable). Remember the choice for this run. If nothing is stale, skip this
   step (nothing to generate).

5. **Summarize only STALE clusters.** For each cluster with `stale == true` (fresh ones are already
   up to date — skip them, this keeps the pass incremental and cheap):
   - Where your harness supports per-subagent model override, **dispatch a subagent on the chosen
     model** to read a few representative files (from `files` / `top_symbols`) and return
     `{title, summary}` (Russian, grounded — see Grounding below); the orchestrator then persists it.
     Where override is unavailable, write the summary inline on the session model and note this in the
     report. Either way:
     - `title` — one line: what this subsystem is.
     - `summary` — a compact paragraph: what it does, its key symbols (from `top_symbols`) and
       invariants. No `path:line` required; it is a high-level prior.
   - Persist: `index_subsystem_summary(repo, branch, cluster_key, title, summary, source_hash)` —
     pass back the cluster's own `source_hash` from step 2.

6. **Prune orphaned summaries (only on a full pass).** If the pass was full — `deferred == 0` and you
   did NOT pass an explicit `depth`/`cap` override (so `clusters` covered every current cluster) — call
   `prune_subsystem_summaries(repo, branch)` to delete summaries whose `cluster_key` is no longer a
   current cluster (orphaned by a depth change or removed modules). On a **partial** pass
   (`deferred > 0`) skip pruning — deferred clusters are not orphans — and say so in the report
   (mirrors `sync_board --limit`).

6.5. **Backfill summary embeddings (every pass).** Call `backfill_summary_embeddings(repo, branch)` so
   any summaries still missing an embedding (older summaries written before vectorization, or where a
   prior pass's Voyage call failed) become searchable by proximity. It embeds from stored title+summary
   (no LLM), is idempotent (a warm corpus embeds nothing), and is fail-soft. Mention the `embedded`
   count in the report.

7. **Report (Russian).** The applied `depth` + `depth_source`; how many clusters summarized vs
   skipped-as-fresh vs **deferred by the cap** (`deferred` from step 2 — never silently truncate); how
   many summaries were **pruned** (step 6), or that pruning was skipped on a partial pass; how many
   embeddings were backfilled (`embedded` from step 6.5). If summaries were written inline (no model
   override), say so.

## Grounding (hard rule)

<!-- include: _common/anti-hallucination.md -->

Every summary must reflect real code you read. If a cluster is unclear, say so briefly rather than
guessing.

## Notes

- Precondition: base index built (`reviewer index`). Re-running is incremental: unchanged subsystems
  (matching `source_hash`) are skipped.
- Read-only on code and GitHub; only writes summaries to the reviewer store.
