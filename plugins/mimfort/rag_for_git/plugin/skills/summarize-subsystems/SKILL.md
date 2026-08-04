---
name: summarize-subsystems
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
Plus `list_subsystem_clusters`, `get_subsystem_summary_work`, `index_subsystem_summary`,
`prune_subsystem_summaries` and `backfill_summary_embeddings` (reviewer MCP), and the harness
`Read`.

## Pipeline

1. **Resolve repo/branch.**

<!-- include: _common/branch-selection.md -->

2. **List clusters.** Call `list_subsystem_clusters(repo, branch)`. Empty / `note` about an empty
   index → tell the user (in Russian) to run `rag-reviewer:sync-codebase` first, then stop. The response
   carries `depth` (the applied cluster depth), `layout_token` (server-owned identity of the
   effective default depth plus sorted per-prefix overrides), `depth_source`
   (`env` | `.review.yml` | `arg`),
   `deferred` (stale clusters held back this pass under the cost cap, env `SUMMARY_REBUILD_CAP`),
   `deferred_files` (their pending file jobs), `orphans` (stored summaries whose `cluster_key` is
   no longer a current cluster), and the (already cap-capped) `clusters`. Save the returned
   `layout_token` and build `expected_source_hashes = {cluster_key: source_hash}` from every
   returned cluster; these exact list-snapshot values are required for finalization. Each cluster
   also carries `stale`, `bootstrap`, `full_rebuild`, and a file-delta preview.

3. **Preflight — echo the applied depth and ask for confirmation (gate the run).** BEFORE summarizing,
   show the user (in Russian):
   - the applied `depth` and where it came from (`depth_source`: env `SUMMARY_CLUSTER_DEPTH`, the repo's
     `.review.yml`, or an explicit arg);
   - how many clusters there are and at what path level — e.g. «depth=2 → 15 кластеров уровня
     `reviewer/index`» — sampling a few `cluster_key`s from `clusters`;
   - how many are `stale` vs fresh, how many require `bootstrap`, plus `deferred` clusters and
     `deferred_files` (held back by the cap).
   - If `orphans > 0`, **warn**: the depth changed or modules were removed, so N summaries are orphaned;
     a full (uncapped) pass will rebuild and prune them.
   - If any cluster has `bootstrap == true`, explain that this is the first post-upgrade fragment
     bootstrap: all current files in selected clusters get fragments, cap-deferred clusters wait for
     later passes, and old cluster summaries remain available until their replacements are stored.
   - State the invariant explicitly: `cluster_key` depends on the whole layout policy, so
     **changing default depth or any depth override triggers a full rebuild of every summary**
     (old-layout summaries orphan and get pruned).
   Then **ask the user to confirm** before running. If they decline, stop without summarizing or pruning.

4. **Choose the summary model (only if work is selected).** Select clusters where
   `stale == true OR bootstrap == true`; full rebuilds already arrive as stale. A subsystem summary
   is a coarse, high-level prior — a small/cheap model is appropriate, and reviewing on an expensive
   model burns tokens. Ask the user which model tier to use for writing summaries, defaulting to a
   cheap tier (e.g. Haiku/Sonnet/Fable). Remember the choice for this run. If no cluster is selected,
   skip this step. Where model override is supported, dispatch a subagent on the chosen model.

5. **Build selected clusters from file fragments.** Initialize run totals for `created`, `reused`,
   `removed`, `moved`, `raced`, and `embedded`; initialize `deferred` from step 2. For each selected
   cluster:
   1. Call `get_subsystem_summary_work(repo, branch, cluster_key, source_hash)` **once**, passing the
      cluster's listed `source_hash`. If `ready=false`, count the cluster as deferred/raced, increment
      `raced`, and continue without jobs or persistence.
   2. Let pending work be exactly `added_files + changed_files`. Dispatch exactly one file-summary job
      on the chosen model for each pending entry, and no other source-reading jobs. Each file prompt must name only its own path
      (plus that entry's fingerprint), tell the job to `Read` exactly that path, and require one Russian result:
      `{path, fingerprint, summary, provenance}`. The orchestrator and every job must not read unchanged
      source files. If per-subagent model override is unavailable, generate the same
      per-file result inline and note that fallback in the report.
   3. Build the **ordered reused/moved/new fragment texts** by merging `reused_fragments`,
      `moved_files`, and the new file results, then sorting by `path`. Dispatch exactly one cluster
      composer on the chosen model with only those ordered fragment records; do not pass `files`,
      `top_symbols`, or source text. Its prompt must say: **composer must not call `Read`** and must
      not make **source-code claims absent from the fragments**. It returns `{title, summary}` in
      Russian: a one-line subsystem title and a compact paragraph about responsibilities, key
      symbols, and invariants supported by the fragments.
   4. Persist the bundle:
      `index_subsystem_summary(repo, branch, cluster_key, title, summary, source_hash,
      fragments=[new file results])`. Pass only the newly generated pending-file results in
      `fragments`; reused and moved fragments are committed server-side. If the response has
      `stored=false`, count the cluster as deferred/raced, increment `raced`, and must not count it as success
      or add its metrics. For `stored=true`, add returned `created`, `reused`, `removed`,
      and `moved` to the run totals, and add one to `embedded` when its `embedded` is true.

6. **Prune orphaned summaries (only on a full pass).** If the pass was full — `deferred == 0`, you
   have `raced == 0`, and you did NOT pass an explicit `depth`/`cap` override (so `clusters` covered
   every current cluster) — call
   `prune_subsystem_summaries(repo, branch, layout_token, expected_source_hashes)` with the exact
   values saved from step 2. The server re-derives the layout/hashes and verifies complete
   same-generation fragment coverage under its branch lock before deleting summaries whose
   `cluster_key` is no longer current. If prune returns `completed=false`, count the prune as
   raced/partial, increment `raced`, do not treat depth/layout as finalized, and report its
   `deferred`/`note`; do not add prune metrics. For `completed=true`, accumulate both returned
   `pruned` and `fragments_pruned`. On a **partial** pass (`deferred > 0`,
   any race, or an override) skip pruning — deferred clusters are not orphans and an incomplete
   bootstrap must not finalize depth state — and say so in the report (mirrors `sync_board --limit`).

6.5. **Backfill summary embeddings (every pass).** Call `backfill_summary_embeddings(repo, branch)` so
   any summaries still missing an embedding (older summaries written before vectorization, or where a
   prior pass's Voyage call failed) become searchable by proximity. It embeds from stored title+summary
   (no LLM), is idempotent (a warm corpus embeds nothing), and is fail-soft. Add its returned
   `embedded` count to the run total.

7. **Report (Russian).** The applied `depth` + `depth_source`; clusters stored vs skipped-as-fresh;
   cap-deferred clusters/files and optimistic `raced` clusters (the report's deferred/raced total);
   fragment metrics `created`, `reused`, `removed`, and `moved`; summaries `pruned` and
   `fragments_pruned`, or that pruning was skipped on a partial pass; and total `embedded`. Never
   silently truncate. If file summaries or composers were written inline (no model override), say so.

## Grounding (hard rule)

<!-- include: _common/anti-hallucination.md -->

Each new file fragment must reflect the one pending source file its job read. Cluster composers
ground only on provided fragments and never read source. If the fragments leave a cluster unclear,
say so briefly rather than guessing.

## Notes

- Precondition: base index built (`reviewer index`). Re-running is incremental at file-skeleton
  fingerprint granularity: unchanged source files are not read or summarized again.
- Read-only on code and GitHub; only writes summaries to the reviewer store.
