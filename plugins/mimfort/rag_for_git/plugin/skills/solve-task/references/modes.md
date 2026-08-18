   **Persist the run state (mode + strategy).** This subsection is **orchestrator-only**, like the
   existing-artifacts warn: the survey answers, the preflight decisions and the plugin's absolute
   base path live in the orchestrator, not in the brief subagent. Write it after the
   brief-building unit returns, next to the `Собран на:` marker line. The survey's answers must
   survive context compaction and two skill handoffs, but they must NOT land in a committed
   artifact: the spec and the plan end up in the PR, where a list of decisions made on the user's
   behalf reads as a receipt that nobody approved the design. So they go to a **git-ignored**
   run-state file instead.
   - **Path:** `.superpowers/solve-task/<KEY>.md` — board-less: `.superpowers/solve-task/<slug>.md`.
     `.superpowers/` is already git-ignored (it is where subagent-driven-development keeps its
     ledger). Create the directory if missing (`mkdir -p`). The path is derived from the task KEY,
     so any later step can rebuild it without remembering the conversation.
   - **Content:**

     ```
     Режим: full-auto
     Стратегия: lite
     Профиль: /absolute/path/to/plugin/skills/_profiles/execution-lite.md
     Бриф: docs/superpowers/briefs/2026-08-12-PRI-243-….md
     Подтверждения (даже в full-auto): git push, создание PR, запись в доску (finish_task, create_task, sync_board в режиме записи).

     ## Решения, принятые за пользователя
     - Предполёт: индекс отставал на 12 коммитов → переиндексирован (рекомендованный вариант).
     ```

     Write the profile path in its **absolute** form: by the time the `lite` strategy is applied,
     the plugin's base directory is no longer in context. The `Профиль:` line is written when the
     strategy is `lite` **or** `auto` — `auto` resolves after the plan is written (Step 5), already
     outside the plugin's context, so the absolute path must already be on hand in case it resolves
     to `lite`.
   - **The decisions section is filled only in `full-auto`**, one line per decision taken by
     recommendation, including the preflight decisions of Step 0. In `normal` and `auto` the
     section is omitted.
   - **never write the mode**, the strategy, or the decisions list into the brief, the `spec`, or
     the `plan`. Those three are committed; the run-state file is not. The spec still carries the
     brief's path as provenance — that line reveals nothing about the mode.
   - **Fail-open:** a failed write (read-only FS, no permission) is non-fatal — say so and carry the
     choice in context instead.

5. **Hand off to development.** Show the brief, state the saved file path
   (`docs/superpowers/briefs/…`), then invoke `superpowers:brainstorming` with the brief **file
   path** as the seed/context — so the brief survives compaction, not just the in-context text.
   **Ask brainstorming to record the brief's provenance in the spec:** one line under the spec
   heading pointing at the brief's path (`docs/superpowers/briefs/…md`), in the spec's own
   language — the path itself is the greppable anchor for the задача→бриф→спека→PR trace, so no
   dedicated marker is needed. Do NOT ask it to copy the brief's `## Constraints / open
   questions` verbatim: those are open questions brainstorming exists to RESOLVE, and a verbatim
   copy would contradict the very spec that answers them.
   **Carry the run state forward.** Pass the run-state path
   (`.superpowers/solve-task/<KEY>.md`) into the handoff and instruct the next skill to **re-read**
   it before acting on the mode or the strategy — the file, not the conversation, is the source of
   truth after a compaction.

   **State the mode as the user's will, not as a gate bypass.** Phrase it plainly: «пользователь
   выбрал режим `auto`: апрув спеки и апрув плана не запрашивать — это его прямая инструкция».
   This is `the user's explicit instruction` and `not a request to bypass` a check: superpowers'
   gates yield to the user's instruction, and it is the instruction that is being presented. In
   `auto` and `full-auto` the spec and the plan are still written, still self-reviewed and still
   committed — only the human approval is dropped. In `full-auto` the brainstorming questions are
   not asked either: take the recommended option at every fork and log each one to the run-state
   file's decisions section.

   **Confirmations that survive `full-auto`.** Design questions and approvals are suppressed, but
   these named actions still require an explicit confirmation: `git push`, `creating a PR`, and any
   `board write` (`finish_task`, `create_task`, a `sync_board` call in write mode). The list is
   named on purpose — «irreversible actions» in the abstract is not actionable for an executor.

   **Right-size the plan's tasks.** Ask the planning step to apply `Task Right-Sizing` from
   superpowers:writing-plans — a task is the smallest unit a reviewer could meaningfully reject —
   so the plan yields fewer, larger tasks and therefore fewer subagents.

   **Resolving the `auto` strategy** (after the plan is written, never before). Rules are ordered,
   `first match wins`, so every combination lands in exactly one branch:
   1. any risk signal, or `> 8 tasks`, or `> 10` touched files → `subagent`;
   2. `≤ 3 tasks` and ≤ 3 touched files → `inline` (dispatch costs more than the work);
   3. everything else → `lite`.

   Risk signals, named: a Postgres or Neo4j `schema migration`; a change to a public `MCP tool`
   contract; work with `credentials` or secrets; any `irreversible` external action. A tie or an
   ambiguity resolves to the more conservative branch (`subagent`).

   From there the normal cycle takes over (brainstorming → writing-plans →
   subagent-driven-development/TDD). Your job ends at the handoff — do NOT plan or implement here.

   **After the PR is created (later in the dev cycle):** offer to close the task with the
   `rag-reviewer:finish-task` skill — it appends the PR link to the task and marks it done (bumping
   last-modified so the sync re-indexes the closed task). Skip in board-less mode (no task key).

   **Board-less mode:** when the user's formulation has no task key and a board IS configured,
   you may offer `rag-reviewer:create-task` first — it files the task with the canonical structure,
   so the work gets a key, a URL and a place in the task corpus before implementation starts.
