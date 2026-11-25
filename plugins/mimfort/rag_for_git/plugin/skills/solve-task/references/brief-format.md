   **Brief-building unit — details (continues the summary given before Step 2).** These are the two
   paths, the pre-dispatch warn, the completion marker and the fail-open fallback referenced there —
   not a new instruction to dispatch again from here.
   - **Path A — per-subagent model override available:** **dispatch a subagent on the chosen model** to
     execute Steps 2–4, giving it the reviewer session-less tools (`get_task`, `search_codebase`,
     `get_subsystem_summaries`, `get_task_context`, `search_tasks`, the graph tools, `get_pr_diff`) plus
     the harness `Read`/`Bash`/`Glob`/`Write`. When Step 0 supplies a `brief_evidence_id` and the
     verifier is available, return the other brief sections and one ordered list of `references`
     for both citation sections. The orchestrator verifies the list and saves the brief.
     Without a verifier or an evidence ID, the subagent can save the legacy brief and return
     its path and a short summary (kept / dropped).
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
   `search_tasks`'s `score` is an RRF rank score (`SUM(1/(k+rank))`, k from `reviewer/rrf.py::RRF_K`, ≈0.016–0.033), NOT comparable
   across queries, so never gate on an absolute value (`search_codebase` exposes no score at all,
   only result order). So DO NOT re-truncate to a fixed number and DO NOT pad artificially: include
   EVERY returned item that *directly informs* the implementation. The keep/drop judgment stays
   binary (directly-informs), with a dropped-count note for each group.
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
   - **Report what you dropped.** End Related work with `(dropped N: reason)`. Put the dropped counts
     and reasons for Relevant code and Test exemplars under Constraints / open questions.
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
   ## Relevant code — citation section filled by the server or the legacy fallback below.
   ## Test exemplars — citation section filled the same way (omit when absent).
   ## Constraints / open questions — terse bullets: limits, unknowns, context gaps (e.g. "board unavailable", "task corpus empty").
   ```

   **Prepare one ordered list of references.** Keep the retrieval order within each section.
   Each record has `section` (`code` for Relevant code, `test_exemplars` for Test exemplars),
   the exact relative `path`, a positive integer `line` from the visible numbered snippet, and a
   single-line `reason` explaining why it directly informs the task. Include the blast radius for
   code or the useful test pattern where relevant. An optional `role` (`edit` or `read`) adds
   context to the reason. Apply the same relevance test and grounding to every reference,
   regardless of role.

   **Verify references before saving.** If Step 0 returned `brief_evidence_id` and
   `verify_task_brief` accepts `references`, the orchestrator calls
   `verify_task_brief(evidence_id=<brief_evidence_id>, references=<ordered list>)` on the same
   reviewer MCP connection used for Step 0. For an inline brief, call the verifier directly on
   that connection. After a restart, retry with the same ID on the reconnected reviewer under
   the same local state directory. Send `references` alone as the citation input. Only fully
   visible rows of the corresponding Step 0 section can enter the rendered block. When the
   verification `status` is `ok`, branch on `render_status` below.

   - `render_status` of `ok` or `empty`: copy the `markdown` field as one block without changes
     into the brief between Subsystems (or Related work) and Constraints / open questions. Replace
     both citation-section placeholders with this block. `empty` supplies a valid Relevant code
     section with no citations. The server's block includes its verification marker. An anchored
     record with an unusable reason or path receives `invalid_reason` or `invalid_path` and is omitted
     from the block. Preserve the confirmed rows. To recover an omitted reference, correct its
     reason or verify its exact anchor as appropriate, then resubmit the full ordered list.
     Account for outstanding omissions in Constraints / open questions.
   - `invalid_format`: inspect the submitted records, correct the formatting (for example, make a
     multi-line reason a single line), and retry on the same connection. If rendering still fails,
     record the issue in Constraints / open questions and continue without a rendered citation
     block. Keep this failure distinct from a successful `empty` response.

   **Legacy fallback.** When the verifier only accepts `citations` and Step 0 supplies an evidence
   ID, project the ordered references onto `section`, `path` and `line` and use
   `verify_task_brief(evidence_id=<brief_evidence_id>, citations=<projected list>)` on the original
   reviewer MCP connection. With `status` of `ok`, keep only entries with a `verified` verdict and
   write their one-line reasons from the original list.

   If there is no verifier or evidence ID, or either verification call returns
   `evidence_unavailable`, manually match each citation's exact path and positive line to fully
   visible numbered rows of the original snippets for that section of the brief. A snippet
   header, advertised line range, or cut-off row is insufficient. When a snippet section has a
   line consisting exactly of `[...truncated]`, exclude the row immediately before
   `[...truncated]` even if it appears numbered. Also exclude the marker and all subsequent rows
   in that section. Omit unmatched anchors.
   If Step 0 returned `brief_line_checks` with nonzero `mismatched` or `unavailable` for
   a section, the printed numbers alone do not suffice for that section. In the fallback,
   confirm the exact text and line using the Git object at `brief_source_sha`. Omit
   the citation if you cannot read that snapshot or confirm its anchor.
   In both cases, use the usual Relevant code and Test exemplars headings and the one-line
   `path:line — reason` form. Do not add `<!-- reviewer:verified-citations -->`.

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
   - **Read back verified blocks.** For a brief with a server-rendered block, read the saved file back
     and check that the citation block matches the verifier's `markdown` exactly and appears once.
     If the write changed or omitted the block, replace it with the original response and check
     again before handing off. Treat a remaining mismatch as a failed write.
   - **Capture Git provenance.** When readback succeeds and Step 0 has an `indexed_sha`, run
     `reviewer brief-provenance <brief> --path <local-clone> --repo <repo> --branch <branch> --indexed-sha <sha>`.
     Read `--indexed-sha` from `payload.preflight.indexed_sha` and use the same resolved repo and
     branch as in Step 0. Prefer the installed reviewer CLI. Use
     `uvx --from rag-reviewer reviewer brief-provenance ...` when reviewer runs through uvx.
     The command adds Git blob IDs to the brief without rewriting the verified sections.
     If it is unavailable or reports missing source paths, report the gap and keep the brief.
     Run the read-only command from Step 5 before using citations from an existing brief;
     do not stamp an older brief with the current index SHA to repair missing provenance.
   - **Fail-open:** a failed write (read-only FS, no permission) is non-fatal — note it and still
     hand off with the in-context brief.
