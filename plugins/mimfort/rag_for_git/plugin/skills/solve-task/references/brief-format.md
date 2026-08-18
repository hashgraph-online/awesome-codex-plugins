   **Brief-building unit — details (continues the summary given before Step 2).** These are the two
   paths, the pre-dispatch warn, the completion marker and the fail-open fallback referenced there —
   not a new instruction to dispatch again from here.
   - **Path A — per-subagent model override available:** **dispatch a subagent on the chosen model** to
     execute Steps 2–4, giving it the reviewer session-less tools (`get_task`, `search_codebase`,
     `get_subsystem_summaries`, `get_task_context`, `search_tasks`, the graph tools, `get_pr_diff`) plus
     the harness `Read`/`Bash`/`Glob`/`Write` (to persist the brief). The subagent returns the brief file
     path and a short summary (kept / dropped).
     **Pass the Step 0 `prepare_task_context` payload into the dispatch prompt verbatim** (or as an
     attached/inlined JSON blob) — the payload lives in the orchestrator's context, not the
     subagent's, and Steps 2–4 are written to consume `payload.task` / `payload.related` /
     `payload.subsystems` / `payload.code` / `payload.test_exemplars` / `payload.gaps`. The subagent
     must NOT call `prepare_task_context` again and must NOT re-call the tools it already replaced
     (`get_task`, `get_task_context`, `search_tasks`, `search_codebase`, `get_subsystem_summaries`)
     except through the documented per-section fallback conditions (payload section absent/empty
     without a matching `gaps` entry, or `prepare_task_context` itself unavailable) — otherwise the
     consolidation into one call is undone and every tool is paid for twice.
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
     `Собран на: <tier/модель>, сборка: subagent | inline` — records which model built the brief. The
     `brief_cost` token block is best-effort and may miss subagent sidechain tokens (documented limitation).
   - Fail-open: an error or empty return from the subagent → the orchestrator finishes the brief inline
     on the session model. Model choice must never break the pipeline.

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
   ## Subsystems — ≤8 relevant subsystems, one line: «cluster_key — gist of summary». For `stale: true`,
   either omit the item or use exactly: `- [stale] <cluster_key> — summary content omitted; verify against code.`
   (omit if prior empty)
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
     the harness auto-approves prompts), list the found artifacts under `## Constraints` with
     the tag `[existing_artifacts]`. In `full-auto` do not ask: continue and record the warning
     under `## Constraints` with `[existing_artifacts]`, plus one line in the run-state decisions
     section.
   - **Idempotency:** before writing, glob `docs/superpowers/briefs/*-<KEY>-*.md` and overwrite
     the match if any (slug drift between runs must not spawn duplicates); board-less → exact name.
   - **Content:** the distilled brief verbatim (the `# Brief — <KEY> <title>` skeleton); add the
     task `url` on the line below the heading when available, for grep-by-key.
   - **Fail-open:** a failed write (read-only FS, no permission) is non-fatal — note it and still
     hand off with the in-context brief.
