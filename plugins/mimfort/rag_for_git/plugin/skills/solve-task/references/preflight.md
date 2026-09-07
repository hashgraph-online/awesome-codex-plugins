   0. **Startup survey.** Ask the user, in **one panel** (`AskUserQuestion`), three questions at
      once. This is the only survey of the run: none of the three is asked again later. Talk to the
      user in Russian.
      1. **Brief model tier** — `cheap` / `mid` (recommended) / `premium`. Phrase the choice by
         tier, not by concrete model names, so it works across CLIs (Claude Code, Codex, Gemini,
         Cursor, …). Do not recommend a coarse tier such as Fable — the brief still needs sound
         judgment. This question used to be a separate step earlier in the pipeline; it now lives
         here, in the startup panel.
      2. **Interaction mode** — three values; the option text must **explain what it means**:
         - `normal` — «вопросы на брейншторме, апрув спеки и апрув плана» (current behaviour);
         - `auto` — «вопросы задаются, апрувы спеки и плана не запрашиваются»;
         - `full-auto` — «вопросы не задаются, на каждой развилке берётся рекомендованный вариант,
           апрувы не запрашиваются». Add the cost to the same option text: «уместен для задач с
           полным описанием и критериями; для расплывчатых формулировок подавляет канал, по
           которому в дизайн попадает недостающая информация».
      3. **Execution strategy** — `inline` (superpowers:executing-plans), `subagent`
         (superpowers:subagent-driven-development as-is), `lite` (the profile at
         `_profiles/execution-lite.md`), `auto` (resolved by the rubric in Step 5 after the plan is
         written). Asked now, applied later.

      **Defaults (fail-open).** No answer, a decline, or a headless / `non-interactive` run → tier
      `mid`, mode `normal`, strategy `subagent`. In a headless / `non-interactive` run do not show
      the panel at all and apply those defaults silently. Otherwise the panel is always shown.
      **never block** — the survey must not stop the pipeline under any circumstance.

      **The mode governs the preflight questions below.** In `full-auto`, do not ask the
      confirmations of Steps 0a., 0.1 and 0.4 (storage unavailable, stale index, missing
      summaries): take the recommended option in each (`reviewer start` when a `remedy` is
      available, else continue without the section; reindex; warm the summaries) and record each
      one as a decision made on the user's behalf, per the run-state file of pipeline Step 4. In
      `normal` and `auto`, ask them as written.

      **The panel is fixed, not a theme to improvise on.** Ask these three questions,
      in one `AskUserQuestion` call, using the headers **verbatim**: `Brief model tier`,
      `Interaction mode`, `Execution strategy`. Do not reformulate the questions in your
      own words, do not split them across several panels, do not substitute your own
      questions for them, and do not omit any of the three — a panel that asks two of
      them is a violation, not a shortcut. Option wording may be phrased in the user's
      language, but each option must still state what that value means, per the option
      texts given above.

      **Self-check.** After the panel returns, verify you actually asked all three. If
      any is missing, say so plainly and ask the missing ones immediately, in a new
      panel, before any preflight check runs — the answers govern the preflight
      questions below, so a late answer governs nothing.

   0a. **Storage reachability — check this before anything else.** Scan `payload.gaps` for an
       entry whose `cause` is `storage_unavailable`. Present it: **never build the brief on a
       gutted context silently.** The gaps list also carries `cause_detail` and `remedy`.
       `remedy` is the command that fixes it (`reviewer start`), or `null` when no command
       applies. `cause_detail` says WHY it does not apply: `auth_failed` — the storage rejected
       the credentials; `missing_database` — the database does not exist; `null` — the cause was
       not named, and only then does a `null` `remedy` mean the storages are remote, where a
       local docker stack fixes nothing.

       Tell the user (in Russian) which sections were lost, then present **three options**:
       1. «Поднять сейчас» — offered **only** when the gap carries a `remedy`. Run that command
          (`reviewer start`), wait for it to finish, then re-run `prepare_task_context(...)` once
          and continue with the fresh payload.
       2. «Подниму сам» → **PAUSE HERE** and wait for the user to write «готово», «поднял»,
          «done» or any confirmation. Once confirmed, re-run `prepare_task_context(...)` and
          continue.
       3. «Продолжить без контекста» → note under **Constraints / open questions** in the brief:
          «хранилище не отвечает (`cause: storage_unavailable`); секции <перечислить> собраны не
          были», and continue.

       When `remedy` is `null`, option 1 is not shown at all, and what you say depends on
       `cause_detail`: `auth_failed` → the containers ARE up and the storage rejected the
       credentials, so the password in `.env` is what to check; `missing_database` → the
       containers ARE up but the database does not exist, so the database name in `PG_DSN` is
       what to check; `null` → the storages are remote and `reviewer start` does not apply here.
       Never say «хранилища удалённые» on a named `cause_detail`: the containers are running and
       the claim is false.

       **The server never starts containers.** It only classifies the failure and names the cure;
       bringing the infrastructure up is the user's call, made here. In `full-auto` do not ask:
       take option 1, or option 3 when there is no `remedy`, and record it in the run-state file's
       decisions section.

       If no gap carries `cause: storage_unavailable`, say nothing and go straight to Step 0.1.

   1. **Base-index freshness.** Read `drift` from `preflight.drift` in the `prepare_task_context`
      payload fetched above — the same field `uvx --from rag-reviewer reviewer status <path>
      --branch <branch> --json` would report. Two distinct cases, do not conflate them:
      - `prepare_task_context` itself is unavailable (the tool is not registered on an older MCP
        deploy, or the call raised entirely) → fall back to running
        `uvx --from rag-reviewer reviewer status <path> --branch <branch> --json` directly and
        read `drift` from its output instead.
      - the call succeeded but `preflight` in the payload is `None` (a `gaps` entry explains why —
        e.g. Postgres/Neo4j unreachable) → do **not** retry via `reviewer status`: it goes through
        the same status-building code and would fail the same way. Treat this exactly like
        `drift == null` below.

      For that branch:
      - `drift == 0` → continue;
      - `drift > 0` → tell the user (in Russian) «индекс отстаёт на N коммитов» and **ask for
        confirmation**: reindex now? **Yes** → delegate to `rag-reviewer:sync-codebase`
        (`--path <path> --ref <branch>`), which reindexes and reports problems, then continue;
        **No** → continue on the stale index and record the gap under **Constraints / open
        questions** in the brief;
      - `drift == null` (no clone / no index record, or `preflight` is `None` per above) →
        do not block; note it in the brief.
   2. **Problem report — in the style of `sync-codebase`.** If `reviewer status` fails (Postgres /
      reviewer MCP / Neo4j unreachable, no index, or `uvx` missing): tell the user (in Russian)
      what is missing and the command to fix it. **Fail-open** — never abort; continue on the
      stale/unknown index.
   3. **Warm the task corpus.** Already warmed inside `prepare_task_context(..., warm_board=True)`
      above — do NOT call `sync_board` again when that warm-up succeeded. Call it directly only as
      a fallback: when `gaps`/`warnings` carries an entry saying the board warm-up did not happen,
      or when `prepare_task_context` itself is unavailable.
      `sync_board(board=<task_board.project or null>, board_type=<task_board.type or null>,
      provider_options=<task_board.options or {}>, limit=null, purge_orphaned=false)` —
      the resolved `task_board.type`, `task_board.project`, and `task_board.options` from this
      preflight. If board work is disabled or no board resolves, skip this call and continue
      board-less.
      Скоупированный прогрев корпуса своего проекта (PRI-170); пустой project → весь корпус.
      Incremental (timestamp watermark), cheap when the corpus is warm. Board not configured or
      `status=error` → tell the user to run `reviewer init`, configure the selected registered
      provider's registry-declared credentials as documented in `docs/board-providers.md`, run
      `reviewer check`, and reconnect MCP; continue board-less.
   4. **Summary warmth.** Read `summaries` from `preflight.summaries` in the same `prepare_task_context`
      payload — the Step 0.1 status payload used for freshness above —
      do NOT probe the summaries tool here. Skip this check if `drift == null` (no index at all —
      summaries can't exist); per Step 0.1, `preflight` being `None` already counts as
      `drift == null`, so a `None` `preflight` skips this check too — do not probe the legacy
      summaries tool for that case either (same underlying failure, same code path).
      - `summaries > 0` → silently continue (no message needed — summaries are warm).
      - `summaries == 0` (summaries not built yet) → tell the user (in Russian): «Сводки подсистем
        не построены — архитектурный приор будет пустым. Как поступим?» and present **three
        options**:
        1. «Прогреть сейчас» → delegate to `rag-reviewer:summarize-subsystems`, wait for it to
           complete, then continue. (Good if using the default model.)
        2. «Прогрею сам» → **PAUSE HERE** and wait for the user to write something like «готово»,
           «прогрел», «done» or any confirmation that they have run their own tool (e.g. an
           external CLI with a cheaper model). Once confirmed, re-run `prepare_task_context(...)`
           and verify `preflight.summaries > 0`, then continue.
        3. «Пропустить» → note in brief under **Constraints**: «сводки подсистем не построены;
           `rag-reviewer:summarize-subsystems` не запускался». Continue without them.
      - `preflight` is not `None` (drift is known — this is NOT the skipped case above) but
        `summaries` inside it is `null`, or the key is absent (deploy older than this field) → fall
        back to the legacy probe: call `get_subsystem_summaries(repo, branch)` and use the returned
        count with the same three options; unlike the main path, this fallback's option 2
        re-verifies by repeating the same legacy probe rather than re-reading the status payload.
        An error from the probe counts as 0 and adds the error detail to option 3's Constraints
        note.

   Decisions: stale → confirmation, never auto (Voyage free tier is 3 RPM / 10K TPM); failures →
   reported like `sync-codebase`; `sync_board` runs incrementally at start; summaries missing →
   three-way choice (build now / build yourself / skip), read from the status
   payload instead of dumping every summary into context.
