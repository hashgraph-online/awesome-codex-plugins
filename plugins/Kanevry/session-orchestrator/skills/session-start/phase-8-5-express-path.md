# Phase 8.5: Express Path Evaluation (#214)

> Project-instruction file resolution: `CLAUDE.md` and `AGENTS.md` (Codex CLI) are transparent aliases — see [skills/_shared/instruction-file-resolution.md](../_shared/instruction-file-resolution.md). All references to `CLAUDE.md` below apply to whichever file the repo uses.

After the user confirms the session type and scope via the Q&A above, evaluate whether the **Express Path** applies before handing off to session-plan. The express path collapses the full 5-wave plan into a single coordinator-direct phase for lightweight sessions.

**Do not evaluate these conditions by hand — run the CLI (#1119, #1146).**

```bash
node scripts/express-path.mjs \
  --repo-root "$PWD" \
  --session-type <housekeeping|feature|deep> \
  --task-count <N> \
  --parallel-agents <true|false>
```

stdout is one JSON line — `{"activated":<bool>,"reasons":[…]}`. The activation banner and every
diagnostic go to stderr. Exit `0` means the evaluation COMPLETED, activation and refusal alike:
branch on the `activated` field, never on the exit code. Exit `1` is an input error (a missing or
invalid `--session-type` / `--task-count` / `--repo-root`), exit `2` an unreadable config file.
`--parallel-agents` is optional and tri-state — omitting it asserts nothing and leaves the field
out of the record, which is NOT the same claim as `false`.

`--repo-root` is required and is never defaulted from `SO_PROJECT_DIR` (#941): an ambient
destination once put a synthetic record into the operator's real fleet ledger.

Until #1146 this block was a fenced `js` snippet with an `import` — prose no process runs. Measured
at HEAD `01eb35d`: `rg -n "evaluateExpressPath" scripts hooks` returned the definition and nothing
else, so the module had ZERO production callers. A hook cannot close that gap either — `sessionType`
and `taskCount` exist only AFTER the Phase 8 Q&A, and no hook event fires there. The caller has to
be something the coordinator RUNS at this point in the flow, which is what `scripts/express-path.mjs`
is.

`evaluateExpressPath` (behind the CLI) makes the decision AND records it as `orchestrator.express_path.evaluated`
— on **every** evaluation, activation and refusal alike. That is the whole point: until #1119 the
conditions below were prose only, `scripts/lib/config.mjs` discarded `express-path` **even when the
block was present** (measured: 88 keys emitted, none of them this one), and the ledger held **0**
express-path events across its entire history. Whether the path ever fired was unanswerable.
Re-deriving the conditions in a coordinator turn re-opens exactly that hole; the conditions below
are the specification the module implements, not a second implementation.

`reasons` carries the blocking codes when `activated: false` and the satisfied ones when `true`.
Nothing short-circuits, so a refusal names **every** blocker — a reader can see whether trimming
the issue list alone would have helped. Unmeasured inputs are omitted from the payload, never
written as `0`/`false`, and an unmeasured `sessionType`/`taskCount` fails CLOSED.

**Activation conditions (the module's specification):**

1. `express-path.enabled` is `true` in Session Config (default: `true` — opt-in by default, opt-out via `express-path.enabled: false`).
2. Session type is `housekeeping` (the user confirmed `housekeeping` in Phase 8).
3. Agreed issue scope is ≤ 3 issues AND no parallel agents are required (i.e., tasks are sequential, no wave decomposition needed).

> Condition 3 carries **two** clauses, so the module takes **four** inputs, not three. The
> condition matrix below and `docs/session-config-reference.md` both list a `housekeeping` / 1–3 /
> `enabled: true` row that still does NOT activate, because parallel agents are required.

**Backward compat:** when `express-path.enabled: false`, the normal 5-wave session-plan flow runs as before. Note that the EVALUATION itself is not skipped — run the CLI regardless, and it returns `{"activated":false,"reasons":["disabled-by-config"]}` and records that refusal. An opt-out that leaves no record is indistinguishable in the ledger from an evaluation that never happened, which is the #1119 hole.

**Historical context:** The 13 prior coordinator-direct sessions documented in `CLAUDE.md` (or `AGENTS.md` on Codex CLI; 2026-04 series — vault-mirror GH#31, phased-rollout #307, v3.2.0 release, etc.) were all running this pattern implicitly: no wave decomposition, coordinator executes tasks directly in sequence. This phase codifies what was already proven to work.

**When Express Path activates:**

Emit the following banner immediately after the Phase 8 Q&A resolves:

```
Express path activated — <N> tasks, coordinator-direct, no inter-wave checks.
```

> **RESOLVED (#1146, operator decision) — session-plan RUNS, in shortened form.** Five documents
> described the post-activation routing and two of them said session-plan was skipped entirely.
> That reading cannot work: `commands/go.md` gates on a 1-wave Express Path plan, which under a
> skipped session-plan would never have been produced — `/go` would look for a plan that does not
> exist. The routing is now one sentence everywhere:
>
> **Phase 8.5 evaluates via `scripts/express-path.mjs`, prints the banner, then hands off NORMALLY
> to Phase 9 → session-plan.** session-plan detects the banner and its
> `## Express Path Short-Circuit (#214)` section emits a minimal 1-wave `coordinator-direct` plan
> (0 agents dispatched, no role decomposition, no wave splitting). `/go` detects that plan per
> `commands/go.md` § Express Path Detection and routes to coord-direct execution plus
> session-end auto-invocation — never to wave-executor.
>
> What activation skips is the WAVE MACHINERY (subagent dispatch, role decomposition, inter-wave
> checkpoints), not the planning handoff. The two sites that said otherwise —
> this file and `skills/session-start/SKILL.md` — were corrected in the same pass;
> `docs/session-config-reference.md`, `skills/session-plan/SKILL.md` and `commands/go.md`
> already carried the surviving reading.

Hand off to Phase 9 as usual. The coordinator then executes the 1-wave plan session-plan emits directly, without dispatching subagents:

1. Proceed to Phase 9 (session-plan handoff) carrying the banner. session-plan short-circuits to the 1-wave `coordinator-direct` plan; `/go` detects it and does NOT invoke wave-executor.
2. For each agreed task (in dependency order): execute as a direct coordinator action — read files, make changes, run quality checks inline. No subagents, no inter-wave checkpoints.
3. Log the express-path activation in STATE.md `## Deviations` section: `Express path: N tasks executed coord-direct (express-path.enabled: true, session-type: housekeeping, scope: N issues)` — written BEFORE session-end is invoked. Then invoke `skills/session-end/SKILL.md` directly.
4. After session-end completes successfully: verify STATE.md `status` is `completed` and `## Deviations` contains the express-path entry from step 3. If either is missing, warn the user with a one-line note and instructions to re-run `/close` manually. Then return the final session summary to the user.

**Persistence contract:**

Step 1 is the Phase 9 handoff and ends the session-start turn — the operator types `/go` next, exactly as on the normal path. Steps 2–4 then MUST all happen within a SINGLE coordinator turn, the one `/go` opens. Specifically:

- Step 2 (execute tasks) happens first in that turn's main flow.
- Step 3a (deviations log) is written BEFORE session-end is invoked. The coordinator calls `appendDeviation()` from `scripts/lib/state-md.mjs` to append the `Express path:` bullet to the `## Deviations` section while STATE.md is still `status: active`.
- Step 3b (invoke session-end) flips `status` to `completed`, writes the metrics record to `.orchestrator/metrics/sessions.jsonl`, and runs the standard close flow. Session-end has no Express Path-specific logic — it treats this run identically to any other completed session.
- Step 4 (verification) is the coordinator's final action before returning control. The verification check uses `parseStateMd()` from `scripts/lib/state-md.mjs` to read the file and check `frontmatter.status === 'completed'` and that the body contains the literal string `Express path:`.

When `/go` is invoked and session-plan emitted a 1-wave Express Path plan (per `skills/session-plan/SKILL.md` § "Express Path Short-Circuit"), the `/go` command MUST detect this and route to coord-direct execution + session-end auto-invocation, NOT to wave-executor. See `commands/go.md` for the detection branch — that plan is the artifact `/go` keys on, which is why Phase 8.5 hands off to session-plan rather than skipping it.

**When Express Path does NOT activate** (conditions not met):

Proceed normally to Phase 9 (session-plan handoff). The express-path evaluation is a silent no-op when any condition fails.

**Condition examples:**

| Scenario | Activates? | Reason |
|---|---|---|
| `housekeeping`, 2 issues, `express-path.enabled: true` | Yes | All 3 conditions met |
| `housekeeping`, 4 issues, `express-path.enabled: true` | No | Scope > 3 |
| `feature`, 2 issues, `express-path.enabled: true` | No | Not housekeeping |
| `housekeeping`, 2 issues, `express-path.enabled: false` | No | Opted out |
| `housekeeping`, 3 issues needing parallel agents, `express-path.enabled: true` | No | Parallel agents needed |

## See Also

- `scripts/express-path.mjs` — the CLI this phase runs; `scripts/lib/express-path.mjs` holds the decision + its `orchestrator.express_path.evaluated` record
- `skills/session-plan/SKILL.md` § "Express Path Short-Circuit (#214)" — the 1-wave plan Phase 9 emits when the banner is present
- `commands/go.md` — Express Path detection and auto-invocation of session-end after coord-direct tasks
- `skills/session-end/SKILL.md` — Phase 1 pre-check (Rule 2) blocks `/close` when STATE.md `status: completed`; auto-invocation from express-path bypasses this
- `commands/close.md` — Rule 2 wording the user sees if express-path persistence breaks
