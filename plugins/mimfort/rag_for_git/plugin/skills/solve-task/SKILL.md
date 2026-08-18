---
name: solve-task
description: Gather disciplined context for solving a task, then hand off to development. Use when the user asks to solve/implement a task ("solve PRI-4", "rag-reviewer:solve-task <key or description>", "реши задачу X"). Reads a keyed task from the reviewer store, pulls related/similar tasks and relevant code, distills a brief, and enters brainstorming. Requires the reviewer MCP server.
---

# Solve Task

Gather the right context for a task, distill it into a brief, then enter the normal development
workflow. This skill does NOT plan or implement — it disciplines context-gathering and hands the
brief to `superpowers:brainstorming` (which leads to writing-plans → subagent-driven-development,
or the execution strategy chosen in the startup survey (inline / subagent / lite)).

## Inputs

`$ARGUMENTS` is either:
- a task key (e.g. `PRI-4`, matching the board's `key_pattern`), or
- a free-text description (e.g. "add a logout endpoint").

## Pipeline

0. **Startup: survey + Preflight (index freshness + task-corpus warm-up).** Run this BEFORE anything else.
   First resolve, once, the repo path (`git rev-parse --show-toplevel`) and the working branch
   (`git branch --show-current`; if it is in `REVIEW_BRANCHES` use it, else the primary branch) —
   step 3 reuses the same branch for `search_codebase`.

   **Resolve `task_board` exactly once before any board call.** Read the repo `.review.yml` block:
   its `task_board` mapping has priority; an absent block falls back to `get_board_config()`;
   an explicit empty `task_board:` disables board work for this run. Keep the resolved
   `{type, project, key_pattern, create_target, done_target, options}` value and **reuse this resolved value** in Step 1 and every board operation. Never call the deploy fallback when the
   repo explicitly disables the board.

   **Call `prepare_task_context(repo, key, branch, warm_board=True)` once here** — pass the
   resolved `key` when `$ARGUMENTS` matches `key_pattern`, else board-less: pass the user's
   formulation verbatim as `key` (the tool's `key` parameter is required and accepts free text
   when no board key matches). It folds
   the manual round trips below into one deterministic call and returns a single payload:
   `preflight` (branch, indexed_sha, drift, summaries, chunks, graph_nodes — feeds Step 0.1/0.4
   below), `task_board`/`task` (feeds Step 2), `related`/`subsystems`/`code`/`test_exemplars`
   (feeds Step 3), `gaps` (a list of `{section, reason}` — copy every entry into **Constraints /
   open questions** in the Step 4 brief verbatim) and `warnings` (surface to the user). No source
   failure raises — a failed section just adds a `gaps` entry, so the steps below stay fail-open.

<!-- include: solve-task/references/preflight.md -->

1. **Config.** Reuse the resolved value from preflight; do not read `.review.yml` or call
   `get_board_config()` again. If no board resolved, continue board-less. For incomplete metadata
   call `get_board_targets(board_type=<task_board.type>,
   project=<task_board.project>, provider_options=<task_board.options or {}>)`: select from
   `targets` by `label`, and use option `required_for` / `choices` to ask for missing `options`.
   Never guess a target or an option and never branch on a board type.

**Brief-building unit (Steps 2–4) runs on the chosen model.** Steps 2–4 (identify → gather → distill
→ persist) are non-interactive; run them on the model chosen in the Step 0 startup survey. Dispatch
a subagent on the chosen model when a per-subagent model override is available (session-less tools +
`Read`/`Bash`/`Glob`/`Write` to persist the brief), passing the Step 0 `prepare_task_context` payload
into its dispatch prompt so it does not re-call `prepare_task_context` or the tools it already
replaced; otherwise build the brief inline. Details, the existing-artifacts pre-dispatch warn, the
`Собран на:` marker line and the fail-open fallback are in `references/brief-format.md` below.

2. **Identify the task.**
   - If `$ARGUMENTS` matches the board's `key_pattern`:
     1. **Store-first.** Use `payload.task` from the Step 0 `prepare_task_context` call — it already
        carries the task's own normalized content (`{key, aliases[], title, description, criteria[],
        status, url}`) from the reviewer store, refreshed by that call's board warm-up. Call reviewer
        `get_task(key, project=<task_board.project>)` directly only as a fallback: when
        `payload.task` is empty without a matching `gaps` entry explaining why, or when
        `prepare_task_context` itself is unavailable — it returns the same normalized shape.
        - **Hit** (a task object with a `key`, from `payload.task` or the fallback `get_task` call):
          use it directly as the `TaskBrief`. The task is
          already indexed (the preflight sync persisted it) — do NOT call `index_task`. Note in the
          brief that the task data came from the reviewer store (after sync).
          - **Thin criteria (optional, fail-open).** The store can return `criteria=[]`; requirements
            normally live in `description`. If it has NO heading matching
            `(?i)(критери|приёмк|acceptance)`, leave `criteria` empty and record the gap. Do NOT call `index_task`.
        - **Miss** (`null` / no `key`) AND a board is resolved: call generic incremental
          `sync_board(board=<task_board.project or null>, board_type=<task_board.type>,
          provider_options=<task_board.options or {}>, limit=null, purge_orphaned=false)`, then
          retry `get_task(key, project=<task_board.project>)` once. Error or second miss →
          board-less: treat `$ARGUMENTS` as the task description and record the gap.
        - **Miss** AND no board: board-less — treat `$ARGUMENTS` as the task description.
   - Otherwise: treat `$ARGUMENTS` as the task description; do not perform external task reads.

   Store-first cuts the double-fetch: `prepare_task_context`'s board warm-up already pulled the whole
   board into the reviewer store, and a miss gets one generic incremental sync/retry (fewer LLM
   tokens and no provider-specific client dependency).

3. **Gather context (best-effort, fail-open).** Any tool returning a "(… unavailable)" / "(ничего не
   найдено)" note or an error is non-fatal — continue. Details (subsystem prior, project scope,
   related-task lookups, `search_codebase`, graph deepening, test exemplars, lazy expansion/PR diff)
   are in `references/context-gathering.md` below.

<!-- include: solve-task/references/context-gathering.md -->

<!-- include: _common/tool-usage.md -->
Use the session-less tools above.

   **Branch selection for `search_codebase`.**

<!-- include: _common/branch-selection.md -->

4. **Distill the solution brief.** Write a structured markdown brief whose only job is to seed
   `brainstorming` — compact, scannable, nothing the implementer won't act on.

<!-- include: solve-task/references/brief-format.md -->

<!-- include: solve-task/references/modes.md -->

## Failure handling (fail-open)

- No configured `task_board` / failed generic sync / task not found → board-less: build the brief
  from `search_tasks` (if the corpus is warm) + `search_codebase` + the user's formulation; note
  the missing task context.
- Neo4j down → `get_task_context` / `index_task` graph parts degrade (empty + warning); build the
  brief from `search_tasks` + `search_codebase`.
- Empty task corpus (no prior `rag-reviewer:sync-tasks` or reviews) → `search_tasks` is empty; use
  `search_codebase` + the user's formulation and note the missing task context.
- Postgres down → `search_codebase` / `search_tasks` return empty; build the brief from the user's
  formulation alone and note the missing task context; still hand off to brainstorming.
- Never abort: with any gap, distill what you have, note the deficit in the brief, and still hand off
  to brainstorming.
- This skill reads task data only through the reviewer store and generic `sync_board`/retry. It
  writes exactly two files: the brief under `docs/superpowers/briefs/` and the git-ignored
  run-state file under `.superpowers/solve-task/`; nothing else in the repository.

## Reporting a reviewer defect

<!-- include: _common/bug-reporting.md -->
