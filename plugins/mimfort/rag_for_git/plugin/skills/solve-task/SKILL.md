---
name: reviewer_solve-task
description: Gather disciplined context for solving a task, then hand off to development. Use when the user asks to solve/implement a task ("solve PRI-4", "/reviewer_solve-task <key or description>", "реши задачу X"). Reads the task from a connected board (if a key + board), pulls related/similar tasks and relevant code, distills a brief, and enters brainstorming. Requires the reviewer MCP server (and optionally a board MCP).
---

# Solve Task

Gather the right context for a task, distill it into a brief, then enter the normal development
workflow. This skill does NOT plan or implement — it disciplines context-gathering and hands the
brief to `superpowers:brainstorming` (which leads to writing-plans → subagent-driven-development).

## Inputs

`$ARGUMENTS` is either:
- a task key (e.g. `PRI-4`, matching the board's `key_pattern`), or
- a free-text description (e.g. "add a logout endpoint").

## Pipeline

0. **Preflight (index freshness + task-corpus warm-up).** Run this BEFORE anything else.
   First resolve, once, the repo path (`git rev-parse --show-toplevel`) and the working branch
   (`git branch --show-current`; if it is in `REVIEW_BRANCHES` use it, else the primary branch) —
   step 3 reuses the same branch for `search_codebase`.

   1. **Base-index freshness.** Run
      `uvx --from rag-reviewer reviewer status <path> --branch <branch> --json` and read `drift`
      for that branch:
      - `drift == 0` → continue;
      - `drift > 0` → tell the user (in Russian) «индекс отстаёт на N коммитов» and **ask for
        confirmation**: reindex now? **Yes** → delegate to `/reviewer_sync-codebase`
        (`--path <path> --ref <branch>`), which reindexes and reports problems, then continue;
        **No** → continue on the stale index and record the gap under **Constraints / open
        questions** in the brief;
      - `drift == null` (no clone / no index record) → do not block; note it in the brief.
   2. **Problem report — in the style of `sync-codebase`.** If `reviewer status` fails (Postgres /
      reviewer MCP / Neo4j unreachable, no index, or `uvx` missing): tell the user (in Russian)
      what is missing and the command to fix it. **Fail-open** — never abort; continue on the
      stale/unknown index.
   3. **Warm the task corpus.** Call
      `sync_board(board=<task_board.project or null>, board_type=<task_board.type or null>,
      status_field=<task_board.status_field or null>, limit=null, purge_orphaned=false)` —
      `task_board.type`, `task_board.project` и `task_board.status_field` берутся из
      `<root>/.review.yml` (прочитай здесь, до вызова `sync_board`; при отсутствии файла или
      блока `task_board` — используй `null`).
      Скоупированный прогрев корпуса своего проекта (PRI-170); пустой project → весь корпус.
      Incremental (timestamp watermark), cheap when the corpus is warm. Board not configured or
      `status=error` → print the `TASK_BOARD_*` hint and continue board-less.
   4. **Summary warmth.** Call `get_subsystem_summaries(repo, branch)` (without `query`) and check
      the returned count. Skip this check if `drift == null` (no index at all — summaries can't
      exist). If count == 0 (summaries not built yet):
      - Tell the user (in Russian): «Сводки подсистем не построены — архитектурный приор будет
        пустым. Как поступим?» and present **three options**:
        1. «Прогреть сейчас» → delegate to `/reviewer_summarize-subsystems`, wait for it to
           complete, then continue. (Good if using the default model.)
        2. «Прогрею сам» → **PAUSE HERE** and wait for the user to write something like
           «готово», «прогрел», «done» or any confirmation that they have run their own tool
           (e.g. an external CLI with a cheaper model). Once confirmed, call
           `get_subsystem_summaries(repo, branch)` again to verify count > 0, then continue.
        3. «Пропустить» → note in brief under **Constraints**: «сводки подсистем не построены;
           `/reviewer_summarize-subsystems` не запускался». Continue without them.
      - If count > 0: silently continue (no message needed — summaries are warm).
      - Fail-open: an error from `get_subsystem_summaries` → treat as count == 0 and offer the
        same options, but include the error detail in option 3's Constraints note.

   Decisions: stale → confirmation, never auto (Voyage free tier is 3 RPM / 10K TPM); failures →
   reported like `sync-codebase`; `sync_board` runs incrementally at start; summaries missing →
   three-way choice (build now / build yourself / skip).

1. **Config.** Resolve the `task_board` block (`type`, `mcp`, `key_pattern`, `project`): first from the repo's
   `.review.yml`, and if there is no block there, from the deploy-wide default via
   `get_board_config()` (reviewer MCP) — so a per-repo `.review.yml` is not required when the board
   is configured once in the reviewer deploy (`TASK_BOARD_*` env). If a board is resolved, its tools
   are `mcp__<task_board.mcp>__*`. No block anywhere (`get_board_config()` → `null`), or the board MCP
   is not connected → board-less mode (continue without it).

1.5. **Choose the brief model (cross-CLI).** Building the brief (Steps 2–4: gather + distill) is a
   light reasoning task over session-less retrieval tools — a top-tier model is overkill and burns
   tokens. **If auto permission mode is active, silently choose the mid tier (Sonnet-class)** and
   continue without asking the user. Otherwise, **Ask the user which model tier to use for building the brief**, phrasing the choice by **tier (cheap / mid / premium)** — not by concrete model names — so it works across CLIs (Claude Code, Codex, Gemini, Cursor, …). **Recommend a mid tier (Sonnet-class) as the default** (do not recommend Fable — a coarse tier is fine but the brief still needs sound judgment). Talk to the user in Russian. Remember the choice for this run. Fail-open: no answer, a decline, or inability to detect auto mode → use the default tier (or, on Path B below, the session model inline). Never block.

**Brief-building unit (Steps 2–4) runs on the chosen model.** Steps 2–4 (identify → gather → distill
→ persist) are non-interactive; run them on the model chosen in Step 1.5:
- **Path A — per-subagent model override available:** **dispatch a subagent on the chosen model** to
  execute Steps 2–4, giving it the reviewer session-less tools (`get_task`, `search_codebase`,
  `get_subsystem_summaries`, `get_task_context`, `search_tasks`, the graph tools, `get_pr_diff`) plus
  the harness `Read`/`Bash`/`Glob`/`Write` (to persist the brief). The subagent returns the brief file
  path and a short summary (kept / dropped).
- **Path B — per-subagent model override unavailable** (some CLIs): build the brief **inline** on the
  session model, or offer the escape-hatch «switch model / run it yourself» in the spirit of the
  preflight «Прогрею сам» option (Step 0.4). Note in the report that the brief was built inline.
- **Existing-artifacts warn** (Step 4, user-facing «warn, don't block»): the **orchestrator** runs
  that scan-and-warn **before dispatch** (a subagent must not prompt the user). It derives the task
  KEY itself — the same `$ARGUMENTS`-vs-`key_pattern` regex match Step 2 opens with (no `get_task`
  needed) — so the KEY-based artifact globs run pre-dispatch. When Steps 2–4 run in a subagent, the
  Step 4 warn is thus **orchestrator-only**; only the idempotency overwrite-glob stays inside the
  subagent's persist.
- After the unit returns, the orchestrator **appends a marker line to the brief**:
  `Собран на: <tier/модель>, режим: subagent | inline` — records which model built the brief. The
  `brief_cost` token block is best-effort and may miss subagent sidechain tokens (documented limitation).
- Fail-open: an error or empty return from the subagent → the orchestrator finishes the brief inline
  on the session model. Model choice must never break the pipeline.

2. **Identify the task.**
   - If `$ARGUMENTS` matches the board's `key_pattern`:
     1. **Store-first.** Call reviewer `get_task(key, project=<task_board.project>)` — it returns the task's own normalized
        content (`{key, aliases[], title, description, criteria[], status, url}`) from the reviewer
        store, which the preflight `sync_board` (step 0.3) just refreshed.
        - **Hit** (a task object with a `key`): use it directly as the `TaskBrief`. The task is
          already indexed (the preflight sync persisted it) — do NOT call `index_task`. Note in the
          brief that the task data came from the reviewer store (after sync).
          - **Thin-criteria enrichment (optional, fail-open).** The store returns `criteria=[]` —
            requirements normally live in `description`. If `description` has NO acceptance-criteria
            heading (no section matching `(?i)(критери|приёмк|acceptance)`) AND a board is connected,
            resolve the task's subtasks into `criteria[]` via the board-MCP playbook
            `../review-pr/references/task-context-<task_board.type>.md` (its «Criteria note»):
            one board `get_task(key)` → for each `subtasks[]` id resolve its title. Fold the resolved
            criteria into the brief's `## Task` section only — do NOT call `index_task`. When the
            heading IS present, criteria are inline in `description` → skip (leave `[]`). No board /
            no subtasks / any error → leave `criteria` empty.
        - **Miss** (`null` / no `key`) AND a board is configured/connected: read the task via the
          playbook `../review-pr/references/task-context-<task_board.type>.md`, build a `TaskBrief`
          `{key, aliases[], title, description, criteria[], status, url, links[]}`, then call
          `index_task(TaskBrief)` to persist it (idempotent — safe to repeat).
        - **Miss** AND no board (or board MCP not connected): board-less — treat `$ARGUMENTS` as the
          task description.
   - Otherwise: treat `$ARGUMENTS` as the task description; do not read the board.

   Store-first cuts the double-fetch: the preflight `sync_board` already pulled the whole board into
   the reviewer store, so a single read of our own store avoids re-enumerating the board via board-MCP
   (fewer LLM tokens, fewer external deps). The board-MCP fallback stays for misses and for boards
   without a REST provider.

3. **Gather context (best-effort, fail-open).** Any tool returning a "(… unavailable)" / "(ничего не
   найдено)" note or an error is non-fatal — continue.
   - **Subsystem prior (architectural map).** Call
     `get_subsystem_summaries(repo, branch, query="<task title>. <first lines of description>")`
     → top-k relevant subsystems by proximity (top-k vs all is server-side; PRI-167).
     Use the same `branch` as `search_codebase`. Fail-open: an empty list / a `(… недоступно)`
     note / an error is non-fatal — omit the `## Subsystems` brief section and note the gap.
     The summary is only a prior — every `path:line` in the brief still comes from
     `search_codebase` snippets, never from the summary text.
   - **Project scope.** Pass `project=<task_board.project>` (from Step 1; empty = unscoped) to
     `get_task`, `get_task_context`, and `search_tasks` so only this repo's project surfaces (PRI-170).
   - If you have a task key: `get_task_context(key, project=<task_board.project>)` → linked tasks, their PRs, and the code those PRs
     touched.
   - `search_tasks("<title>. <first lines of description>", project=<task_board.project>)` → semantically similar tasks. If a board
     is connected, you may read the most relevant similar tasks from the board for fuller detail.
   - **Related work = linked ∪ similar.** The «Related work» brief section draws from two sources —
     `get_task_context` (linked) and `search_tasks` (similar). They overlap; the Step 4 filter
     deduplicates them by key before the cap.
   - `search_codebase("<task description>")` → relevant existing code (files/symbols to touch or
     mimic).
   - **Lazy expansion (no user prompt).** If a tool's output ends with a cliff/rails note reporting a
     high-scoring tail beyond the cut AND the task looks broad, you MAY re-call the tool once with a
     higher ceiling (pass `top_k=<bigger>`), then merge. Do this silently — never pause to ask the user.
   - **Test exemplars (optional — when `search_codebase` surfaced concrete symbols).** One extra
     `search_codebase("<how the task's area is tested — fixtures/mocks for the feature>", include_tests=True)`
     on the same `branch` — a targeted *test* query (how the area is tested), not the code query with
     the flag flipped, so it surfaces the testing pattern the TDD hand-off should mimic. Snippets are
     line-numbered like the code retrieval → cite `path:line` directly. Apply the same Step 4 adaptive
     relevance filter (every directly-informing test file/symbol, no fixed cap). Fail-open: no tests
     surfaced / a `(ничего не найдено)` note / an error → omit the `## Test exemplars` brief section;
     the default code retrieval (`include_tests=False`) is unchanged.
   - **Deepen via the code graph (optional — when `search_codebase` surfaced concrete symbols).**
     `search_codebase` chunks are headed by `path#fqn (path:start-end)`; feed those `node_id`s to the
     session-less graph tools to sharpen the brief. The default `search_codebase` (code retrieval,
     `include_tests=False`) returns deduplicated, line-numbered, test-free snippets — expand only the
     few symbols central to the task (feed graph tools the code node_ids, not test-exemplar ones), and cite
     `path:line` from the line-numbered snippets directly (no re-Read needed for grounding).
     For OO/registry/dispatch tasks («add a new provider / handler»), prefer directed
     `implementations(node_id)` (incoming IMPLEMENTS — who subclasses/overrides X) over the
     undirected `related_symbols`, which mixes callers/tests/implements. A class node → its
     subclasses; a method node → its overrides. Accurate after a full `reviewer index` with SCIP;
     fail-soft `(implementations не найдены)` is non-fatal — continue.
     Pass the same `branch` you pass to `search_codebase`.
     Fail-open: a `(граф недоступен)` / `(нет связей)` / `(вызовов не найдено)` note is non-fatal — continue.
   - **Lazy PR diff (optional).** `get_task_context` surfaces a task and its PRs (id form
     `owner/name#N`); `search_tasks` surfaces similar task keys — fetch a key's context to see
     its PRs. If a related task passed the relevance filter AND its PR is worth inspecting for
     the implementation, parse `repo`/`number` from the PR id and call `get_pr_diff(repo, number)`
     to see what that PR changed — pull it lazily, only when the LLM judges it useful (don't
     fetch diffs for low-relevance tasks).
     Fail-open: a `(diff PR недоступен)` / `(repo не задан…)` note is non-fatal — continue.
   - **Relevance signals → Step 4 filter.** `search_tasks` `score` is an RRF rank score
     (≈0.016–0.033), not comparable across queries; `search_codebase` has no score, only order.
     Carry *rank/order* — not absolute score — into the Step 4 filter, and fetch `get_pr_diff`
     only for a related task that survives that filter (within top-3, directly informing).

<!-- include: _common/tool-usage.md -->
Use the session-less tools above.

   **Branch selection for `search_codebase`.**

<!-- include: _common/branch-selection.md -->

4. **Distill the solution brief.** Write a structured markdown brief whose only job is to seed
   `brainstorming` — compact, scannable, nothing the implementer won't act on.

   **Relevance filter (adaptive — retrieval is already bounded server-side).** Server-side cliff
   (`search_codebase`) and rails (`search_tasks`) already cap retrieval adaptively per task — and
   `search_tasks`'s `score` is an RRF rank score (`SUM(1/(60+rank))`, ≈0.016–0.033), NOT comparable
   across queries, so never gate on an absolute value (`search_codebase` exposes no score at all,
   only result order). So DO NOT re-truncate to a fixed number and DO NOT pad artificially: include
   EVERY returned item that *directly informs* the implementation. The keep/drop judgment stays
   binary (directly-informs), and end each section with `(dropped N: reason)`.
   - **Order** candidates by result rank (tasks: rank/score; code: rank).
   - **No fixed ceilings.** Take exactly the directly-informing items the tools returned. Related
     tasks are bounded by the search rails; the brief lists those that directly inform. Expand the
     graph (`related_symbols`/`callers`/`definition`) only for the few symbols central to the task.
   - **Keep/drop is a binary judgment** — include an item ONLY if it *directly informs the
     implementation*. Rank/score only sets review order; it is not a numeric gate.
     - ✅ INCLUDE: a symbol/file you will edit or mimic; a task whose PR shows a concrete pattern to
       follow; a constraint that narrows the approach.
     - ❌ EXCLUDE: a task in the same area but a different mechanism; a file the search surfaced that
       you won't touch or copy; background you won't act on.
   - **Report what you dropped:** end the Related work, Relevant code and Test exemplars sections with
     `(dropped N: reason)`.
   - **Dedup related sources by key (linked ∪ similar).** «Related work» draws from
     `get_task_context` (linked) and `search_tasks` (similar). Deduplicate by canonical task key
     before inclusion, matching `PRI-N`↔`ID-N` via `aliases` (one task, two codes). On collision
     keep the linked entry (richer — carries PR/graph context) and drop the similar duplicate, so a
     task never appears twice in the brief.

   **Brief skeleton — fill it, keep each item to one line:**

   ```
   # Brief — <KEY> <title>
   ## Task — key/title/requirements/criteria (or the user's formulation in board-less mode). ≤~6 lines.
   ## Related work — every directly-informing task, one line each: «KEY — what to reuse / follow». (dropped N: …)
   ## Subsystems — ≤8 relevant subsystems, one line: «cluster_key — gist of summary». (omit if prior empty)
   ## Relevant code — every directly-informing file/symbol, one line: «path:line — why» (+ blast radius from the graph). (dropped N: …)
   ## Test exemplars — every directly-informing test file/symbol, one line: «path:line — what's mocked / which pattern». (omit if none; dropped N: …)
   ## Constraints / open questions — terse bullets: limits, unknowns, context gaps (e.g. "board unavailable", "task corpus empty").
   ```

   Cite `path:line` straight from the line-numbered Step 3 snippets — no re-Read (Step 3 contract).

   **Persist the brief (survivability).** After distilling, save the brief to a file so it
   survives context compaction / a new session and seeds the trace задача→бриф→спека→план→PR.
   - **Directory:** `docs/superpowers/briefs/` — create it if missing (`mkdir -p`). Committed like
     `specs/`/`plans/` (leave a trace, do not gitignore).
   - **Filename:** with a task key — `YYYY-MM-DD-<KEY>-<slug>.md`, where `KEY` is the board key
     matching `key_pattern` (e.g. `PRI-163`, NOT the normalized store key `ID-163`) and `slug` is a
     short ASCII kebab of the title. **Board-less** (no key): `YYYY-MM-DD-<slug>.md` (slug from the
     user's formulation). `YYYY-MM-DD` = today's date.
   - **Check for existing artifacts (warn, don't block).** Before writing the brief, scan the
     three artifact directories for files matching this task key (case-insensitive):
     - `docs/superpowers/briefs/*<KEY>*`
     - `docs/superpowers/specs/*<key>*-design.md`
     - `docs/superpowers/plans/*<key>*.md`
     Use case-insensitive matching (e.g., try both `PRI-176` and `pri-176` globs, or lowercase
     file names before matching). If any artifacts are found, warn the user (in Russian):
     > "⚠️ Похожие артефакты уже существуют: briefs/PRI-176-..., specs/pri-176-...-design.md,
     > plans/pri-176-....md. Продолжить? [Y/n]"
     Do **not** block — continue unless the user explicitly says no. If the user continues (or
     auto-permission mode leaves no choice), list the found artifacts under `## Constraints` with
     the tag `[existing_artifacts]`.
   - **Idempotency:** before writing, glob `docs/superpowers/briefs/*-<KEY>-*.md` and overwrite
     the match if any (slug drift between runs must not spawn duplicates); board-less → exact name.
   - **Content:** the distilled brief verbatim (the `# Brief — <KEY> <title>` skeleton); add the
     task `url` on the line below the heading when available, for grep-by-key.
   - **Fail-open:** a failed write (read-only FS, no permission) is non-fatal — note it and still
     hand off with the in-context brief.

5. **Hand off to development.** Show the brief, state the saved file path
   (`docs/superpowers/briefs/…`), then invoke `superpowers:brainstorming` with the brief **file
   path** as the seed/context — so the brief survives compaction, not just the in-context text.
   From there the normal cycle takes over (brainstorming → writing-plans →
   subagent-driven-development/TDD). Your job ends at the handoff — do NOT plan or implement here.

   **After the PR is created (later in the dev cycle):** offer to close the task with the
   `/reviewer_finish-task` skill — it appends the PR link to the task and marks it done (bumping
   last-modified so the sync re-indexes the closed task). Skip in board-less mode (no task key).

## Failure handling (fail-open)

- No `task_board` / board MCP not connected / task not found → board-less: build the brief from
  `search_tasks` (if the corpus is warm) + `search_codebase` + the user's formulation; note the gap.
- Neo4j down → `get_task_context` / `index_task` graph parts degrade (empty + warning); build the
  brief from `search_tasks` + `search_codebase`.
- Empty task corpus (no prior `/reviewer_sync-tasks` or reviews) → `search_tasks` is empty; rely on the board
  (if a key) + `search_codebase`.
- Postgres down → `search_codebase` / `search_tasks` return empty; build the brief from the board (if
  a key) or the user's formulation alone; still hand off to brainstorming.
- Never abort: with any gap, distill what you have, note the deficit in the brief, and still hand off
  to brainstorming.
- Read-only on the board; this skill never writes to it. The brief file under
  `docs/superpowers/briefs/` is the only write this skill makes — to the repo, not the board.
