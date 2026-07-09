---
name: wave-executor
user-invocable: false
tags: [orchestration, execution, agents, waves]
model: inherit
model-preference: opus
model-preference-codex: gpt-5.4-mini
model-preference-cursor: claude-sonnet-4-6
description: >
  Use this skill when executing the agreed session plan in waves with role-based execution and parallel subagents. Handles inter-wave
  quality checks, plan adaptation, and progress tracking. Core orchestration engine for
  feature and deep sessions. Triggered by /go command.
---

# Wave Executor Skill

## Execution Model

You are the **coordinator**. You do NOT implement — you orchestrate. Your job:
1. Dispatch subagents for each wave
2. Wait for ALL agents in a wave to complete
3. Review their outputs
4. Adapt the plan if needed
5. Dispatch the next wave
6. Repeat until all waves complete

## Design Philosophy

This harness exists to enable multi-agent coordination at scale — not by removing friction, but by making it visible, classifiable, and recoverable.

The wave-executor is process scaffolding around LLM agents. It handles task breakdown, scope enforcement, circuit breaker guards, and recovery patterns. Unlike direct chat with an agent, it trades flexibility for safety and repeatability across a bounded execution envelope.

Every harness creates friction. The goal is not minimum friction — it is useful friction that prevents higher-cost problems downstream.

**Friction we accept:**
- Wave planning overhead and `wave-scope.json` pre-dispatch setup
- Per-wave quality gates before proceeding
- Worktree isolation costs for parallel agents
- Turn-limit constraints that stop runaway agents early

**Friction we prevent:**
- Agent scope violations (PreToolUse hooks block out-of-scope file edits)
- Cascading failures (circuit breaker + spiral detection halt broken agents before they propagate damage)
- Silent partial completion (STATUS line requirement forces explicit reporting)
- Untracked carryover work (session-end plan verification catches unresolved tasks)

The harness does not hope agents self-correct. It detects stagnation patterns — pagination-spiral, turn-key-repetition, error-echo — classifies them into the Error-Class Taxonomy defined in `circuit-breaker.md`, and re-scopes mechanically. Review logic lives in `wave-loop.md` § "Review Agent Outputs".

## Platform Note

> State files live in the platform's native directory: `.claude/` for Claude Code, `.codex/` for Codex CLI, `.cursor/` for Cursor IDE. All references to `.claude/` below should use the platform's state directory. Shared metrics (sessions.jsonl, learnings.jsonl) live in `.orchestrator/metrics/` — both platforms read and write there. See `skills/_shared/platform-tools.md` for tool mappings.

## Phase 0: Bootstrap Gate

Read `skills/_shared/bootstrap-gate.md` and execute the gate check. If the gate is CLOSED, invoke `skills/bootstrap/SKILL.md` and wait for completion before proceeding. If the gate is OPEN, continue to the Pre-Execution Check.

> **Session-start only:** This gate check runs ONCE at the start of `/go` execution — before the first wave. It does NOT run before each wave step. Repeating the check per wave would add latency with no safety benefit, since `bootstrap.lock` is immutable within a session.

<HARD-GATE>
Do NOT proceed past Phase 0 if GATE_CLOSED. There is no bypass. Refer to `skills/_shared/bootstrap-gate.md` for the full HARD-GATE constraints.
</HARD-GATE>

## Phase 0.5: Parallel-Aware Preamble

> Skip silently when `persistence: false` in Session Config.

Before Phase 1, run the parallel-aware preamble per `skills/_shared/parallel-aware-preamble.md`. The preamble detects other active sessions in the worktree-family via `findPeers(repoRoot, { mySessionId })`, classifies the caller's mode via `classifyMode(callerMode)` against the exclusivity-matrix, and fires the appropriate AUQ on conflict.

**Outcome handling:**
- `PASS_THROUGH` → continue to Phase 1
- `EXCLUSIVE_BLOCKED` → exit Phase 0 cleanly per the AUQ outcome
- `PROMOTION_OFFER` → user picks Worktree-Promotion (see `parallel-aware-auq.md` outcome-handling — calls `enterWorktree()`), in-place + Deviation, or Abbrechen

For session-end specifically: the preamble is DETECTION-ONLY. The lock-release path in later phases keeps its current behavior — releasing the OWN session's lock requires no matrix consultation.

**Implementation reference:** `skills/_shared/parallel-aware-preamble.md § Implementation`.
**AUQ reference:** `skills/_shared/parallel-aware-auq.md`.

## Pre-Execution Check

Before starting the first wave (Discovery role):
1. `git status --short` — ensure clean working directory (commit or stash if needed)
2. Verify no parallel session conflicts (unexpected modified files)
3. Confirm the agreed plan is still valid (no new critical issues since planning)
4. **Verify `jq` is installed** — run `command -v jq`. If not found, warn the user: "⚠ jq is not installed. Scope and command enforcement hooks will be DISABLED. Install jq (`brew install jq` / `apt install jq`) to enable security enforcement." Do NOT proceed with waves until user acknowledges.
5. **Read Session Config**: Parse Session Config per `skills/_shared/config-reading.md`. Store result as `$CONFIG`. Extract these fields:
   - `persistence` (default: true), `enforcement` (default: warn), `isolation` (default: auto)
   - `agents-per-wave` (default: 6), `max-turns` (default: auto), `pencil` (default: null)
   
   **Execution Config shortcut:** If the session-plan output contains an `### Execution Config` section, its execution-level fields (waves, agents-per-wave, isolation, enforcement, max-turns) take precedence over `$CONFIG`. Session-level fields (persistence, pencil) always come from `$CONFIG`. If the Execution Config section is missing, use `$CONFIG` alone.
6. **Initialize session metrics** (if `persistence` enabled): Prepare a metrics tracking object for this session:
   - `session_id`: `<branch>-<YYYY-MM-DD>-<HHmm>` (HHmm from `started_at` — ensures uniqueness across multiple sessions per day)
   - `session_type`: from Session Config
   - `started_at`: ISO 8601 timestamp
   - `waves`: empty array (populated after each wave)
   This object lives in memory during execution — it is written to disk by session-end.

## Pre-Execution: User Instructions

If the user provided additional instructions with `/go` (e.g., `/go focus on API endpoints`), apply them as a priority modifier:

1. **Incorporate into agent prompts**: Add a "**Priority Focus:**" section to each agent's prompt that includes the user's instructions verbatim
2. **Do NOT override the plan**: User instructions adjust emphasis within the existing plan, they do not replace it. If the instructions conflict with the plan, note the conflict and follow the plan.

Example: If user said `/go focus on API endpoints`, each agent prompt includes:
```
**Priority Focus (from user):** focus on API endpoints
```

## Pre-Wave 1a: Capture Session Start Ref

Before dispatching Wave 1, capture the current commit as the session baseline:

```bash
SESSION_START_REF=$(git rev-parse HEAD)
```

Store this value for use throughout the session — it is needed by the simplification pass (Quality wave) and session-reviewer dispatch to determine which files changed during this session. Include it in the coordinator's context, NOT in individual agent prompts.

## Pre-Wave 1b: Initialize STATE.md

> Skip this section entirely if `persistence: false`.

Before dispatching Wave 1, write `<state-dir>/STATE.md` with YAML frontmatter and Markdown body:

```yaml
---
schema-version: 1
session-type: feature|deep|housekeeping
branch: <current branch>
issues: [<issue numbers from plan>]
started_at: <ISO 8601 timestamp with timezone>
status: active
current-wave: 0
total-waves: <from session plan>
---
```

```markdown
## Current Wave

Wave 0 — Initializing

## Wave History

(none yet)

## Deviations

(none yet)
```

Create the `<state-dir>` directory if needed (`mkdir -p <state-dir>`) before writing. This file is the persistent state record — other skills and resumed sessions read it.

#### Pre-Wave 1b Extension: Docs Tasks Persistence (A3 / #230)

After writing the base STATE.md frontmatter above, conditionally persist the docs tasks block emitted by session-plan:

**Condition:** BOTH of the following must be true:
1. The session plan contains a `### Docs Tasks (machine-readable)` section with a YAML code block.
2. `$CONFIG."docs-orchestrator".enabled` is `true`.

If either condition is false → omit the `docs-tasks` field entirely. Do NOT write an empty key (`docs-tasks: []`). Absence means "no docs tasks planned this session" — downstream consumers (session-end Phase 3.2) treat absence the same as an empty list.

When the condition is met, parse the YAML block from the session plan's `### Docs Tasks (machine-readable)` section and append the following field to the STATE.md YAML frontmatter (alongside the base fields above):

```yaml
docs-tasks:
  - id: <task id from plan>
    audience: <user|dev|vault>
    target-pattern: <glob pattern from plan>
    rationale: <rationale string from plan>
    wave: <wave number the task is assigned to>
    status: planned
```

Each entry's `status` is initialized to `planned`. session-end Phase 3.2 (Docs Verify) writes the terminal value per task: `ok` (diff is substantive), `partial` (diff region contains `<!-- REVIEW: source needed -->` markers), or `gap` (no matching diff). wave-executor does NOT perform intermediate status updates — `planned` remains until session-end runs.

> **Schema note:** `schema-version: 1` now includes the optional `docs-tasks` array. The field is backwards-compatible — its absence is a valid schema-version-1 STATE.md meaning "no docs tasks planned". Readers MUST treat a missing `docs-tasks` key identically to `docs-tasks: []`.

> **Ownership clarification:** session-plan does NOT write STATE.md directly. The wave-executor owns ALL STATE.md writes — initialization here (Pre-Wave 1b) is the canonical write point for `docs-tasks`. session-plan only emits the source `### Docs Tasks (machine-readable)` block for the coordinator to consume. See `skills/_shared/state-ownership.md` for the full ownership matrix.

> **Consumer cross-reference:** session-end reads `STATE.md` frontmatter's `docs-tasks` field (if present) during Phase 3.2 Docs Verify — see `skills/session-end/SKILL.md`. The field is also readable by the docs-writer agent if it needs to know which tasks were planned for the current session.

> **Ownership:** STATE.md is owned by the wave-executor. Only the wave-executor writes to it (initialization + post-wave updates). session-end reads it for metrics extraction and sets `status: completed`. session-start reads it only for continuity checks (Phase 0.5). No other skill should write to STATE.md.

## Wave Execution Loop

Read and follow `wave-loop.md` in this skill directory for the complete wave execution loop, including agent dispatch, output review, plan adaptation, progress updates, and scope manifest creation.

### Mission-Status Updates (#340)

The coordinator (you) is responsible for updating per-task mission status in STATE.md as tasks progress through the wave. Use `setMissionStatus(stateContent, taskId, status)` from `scripts/lib/state-md.mjs` and write the result back to STATE.md immediately.

**Per-task transition rules (coordinator fires these, NOT wave-loop.md):**

| Transition | When to fire |
|---|---|
| `brainstormed` → `validated` | User runs `/go` to approve the wave plan (all items simultaneously) |
| `validated` → `in-dev` | Agent for that wave-plan item is dispatched via `Agent()` tool |
| `in-dev` → `testing` | Quality wave begins and this item's implementation wave completed without failure |
| `testing` → `completed` | Quality-Lite gate passes (green) for this task's wave — coordinator confirms item done |
| Any → `brainstormed` | Item is discarded, re-planned, or rolled back |

**Important scoping notes:**
- These transitions are **coordinator-level orchestration** decisions, not part of `wave-loop.md` dispatch/review logic. Do NOT modify `wave-loop.md` to add mission-status calls.
- `wave-loop.md` is NOT modified by #340 — the transitions listed above are called by the coordinator after observing the wave-loop outcomes.
- Only update items whose `id` appears in the `### Wave-Plan Mission Status (machine-readable)` block emitted by session-plan. Invent no new IDs.
- When STATE.md does not yet have a `## Mission Status` body section, `setMissionStatus` creates it automatically (see `scripts/lib/state-md.mjs`).
- `readMissionStatus(stateContent, taskId)` from the same module returns the current status string for a task (or `null` if not found), useful for guard-checking before transitions.

**Backward compat:** STATE.md files without a `## Mission Status` section are valid — absence means no status tracking was started. The helpers are no-throw on bad input.

## Circuit Breaker & Worktree Isolation

> **Reference:** See `circuit-breaker.md` in this skill directory for MaxTurns enforcement, spiral detection, recovery protocol, and worktree isolation configuration. Apply those rules during every wave dispatch and post-wave review.

## Coordinator CWD Discipline (#219)

Claude Code's `Agent` tool with `isolation: "worktree"` changes `process.cwd()` into the agent's worktree and does not restore it on agent return. Without discipline, the coordinator's subsequent Edit/Write/Bash calls silently route to a worktree branch — producing data loss when the worktree is later pruned.

**Rules for the coordinator (this is YOU during wave execution):**

1. **After every Agent() dispatch** (before reading its output), call `restoreCoordinatorCwd()` from `scripts/lib/worktree.mjs`. `wave-loop.md § 2` makes this explicit.
2. **Prefer absolute file paths** for Read/Edit/Write tool calls. A drifted CWD turns relative paths into silent cross-tree writes.
3. **Before any Bash git command**, either `cd` inside a subshell (`cd /path && cmd`) or rely on `git -C /path <cmd>`. Do not assume CWD.
4. **Verify at checkpoints** — when in doubt, run `git rev-parse --show-toplevel` to confirm which tree is currently active.
5. **Never `cd` into a worktree in the coordinator's top-level shell.** If you need to inspect a worktree, use `git -C <wt-path> ...` or spawn a subshell.

## Coordinator User Interaction

Every mid-wave user decision — pause/continue, scope changes, plan revisions, routing between alternate tracks, confirming a risky recovery step, picking between recommendations — MUST go through the `AskUserQuestion` tool. Inline markdown-list "choose 1/2/3" questions in chat prose are forbidden: the user reliably misses them in the dense wave-execution stream. See `.claude/rules/ask-via-tool.md` for the full rule (AUQ-001 through AUQ-005).

Mechanics:
- `AskUserQuestion` is a deferred tool in Claude Code. On the first coordinator decision point in a session, call `ToolSearch` with `"select:AskUserQuestion"` once to load its schema, then call the tool. Do not skip the question to avoid the load.
- Option 1 always carries `(Recommended)` in the label. Each option carries a one-line `description` stating the trade-off.
- `AskUserQuestion` is **not available inside dispatched subagents**. If an agent surfaces a decision back to you, ask the user via `AskUserQuestion` from the coordinator turn — do not let the agent emit a prose question.

Applies to every interaction point in `wave-loop.md` that currently says "inform the user", "propose revised plan", "ask the user whether to…", or "report specific mismatches to user" when a choice is implied.

## Agent Prompt Best Practices

Each agent prompt MUST include:

1. **Clear scope boundary**: "You are working on [X]. Do NOT modify files outside [paths]."
2. **Full context**: file paths, current code structure, issue description. If a bite-sized executable plan exists at `docs/plans/<feature>.md` for the wave's tasks (see `skills/write-executable-plan/SKILL.md`), include the path in each agent's prompt and instruct the agent to follow the plan's 5-step structure verbatim.
3. **Acceptance criteria**: measurable definition of done
4. **Rule references**: the wave's applicable rules are injected automatically as the `<APPLICABLE-RULES>` block produced by `scripts/print-applicable-rules.mjs` (see `wave-loop.md` § "Pre-Dispatch: Glob-Scoped Rule Injection (#336/#694)"). The block is computed once per wave from the wave's `allowedPaths` and prepended to every agent prompt — do not hand-copy rule paths into the prompt.
5. **Testing expectation**: "Write tests for your changes" or "Run existing tests"
6. **Commit instruction**: "Do NOT commit. The coordinator handles commits."
7. **Turn limit**: Include the maxTurns instruction from `circuit-breaker.md`
8. **Verification before completion**: Before claiming any task done, run the verification command and quote the evidence inline. See `.claude/rules/verification-before-completion.md`.

Each agent prompt MUST NOT include:
- References to other agents' tasks (isolation)
- Vague instructions like "improve" or "optimize" without specifics
- Assumptions about code state — provide the actual state

## Agent Memory-Proposal Capability (#501)

Wave-executor agents may propose memory entries (learnings) mid-session via the `memory.propose` CLI. The coordinator surfaces proposals at session-end Phase 3.6.3 (`skills/session-end/SKILL.md`) for AUQ-confirm before promoting them to `learnings.jsonl` with `_provenance: agent-proposed@<wave-id>`. Conservative safety model: max `memory.proposals.quota-per-wave` (default 5) per wave, `memory.proposals.confidence-floor` (default 0.5).

**Agent prompt boilerplate** — when dispatching an Impl-Core / Impl-Polish / Quality agent in a session where `memory.proposals.enabled: true` (default), include this block in the agent's prompt so the capability is discoverable:

```
## Memory Proposal Capability (optional)

During this wave, you may propose a learning to the session's memory via the CLI:

  SO_WAVE_AGENT=1 node scripts/memory-propose.mjs \
      --type <one of: workflow-pattern|anti-pattern|recurring-issue|fragile-file|effective-sizing|proven-pattern|mode-selector-accuracy|hardware-pattern|autopilot-effectiveness|domain-regression|convention|architecture-pattern|design-pattern> \
      --subject "one-line title (max 100 chars, no newlines)" \
      --insight "your discovery paragraph (max 2000 chars)" \
      --evidence "concrete proof: code citation / log excerpt / commit ref (max 5000 chars)" \
      --confidence <0.5 to 1.0>

MUST prefix with `SO_WAVE_AGENT=1` — without it the CLI returns exit 3 `rejected-wrong-context`. The env-var is the per-process guard that distinguishes wave-executor agents from coordinator-context invocations.

Exit code 0 = queued (the coordinator will present at session-end via AskUserQuestion); 1 = quota-exceeded; 2 = rejected-low-confidence (below floor 0.5); 3 = rejected-wrong-context (STATE.md not active OR SO_WAVE_AGENT != "1"); 4 = error (arg validation or internal).

Use ONLY when you find a recurring pattern, anti-pattern, or constraint worth carrying into future sessions. The coordinator confirms each proposal before it lands in learnings.jsonl. Do NOT over-propose — quota is bounded per wave.

Analyzer-only learning types, including `autonomy-verdict`, are intentionally not valid here; those are emitted by `/evolve` after their analyzer-specific evidence gates pass.
```

**Skip injection** when:
- `memory.proposals.enabled: false` in Session Config, OR
- Discovery / Finalization waves (Discovery is read-only; Finalization is coordinator-direct)

**Audit trail:** the `hooks/pre-bash-memory-propose-audit.mjs` hook logs every CLI invocation to `.orchestrator/metrics/events.jsonl` with the value of `--insight` / `--subject` / `--evidence` redacted (privacy-by-default).

Cross-reference: PRD F2.1 / issue #501 / `agents/memory-proposal-collector.md` (coordinator-side AUQ rendering reference doc) / `scripts/lib/memory-proposals/{schema,store,collector,sink}.mjs` (the modules).

## Session Type Behavior

### Housekeeping Sessions

Housekeeping sessions use a simplified single-wave execution model instead of the multi-wave role-based dispatch:

1. Initialize STATE.md as normal (`session-type: housekeeping`, `total-waves: 1`)
2. Do NOT create `wave-scope.json` — scope enforcement is not needed for low-risk housekeeping tasks
3. Dispatch tasks serially with 1-2 agents per task
4. Run Baseline quality checks after all tasks complete (not between tasks)
5. Skip session-reviewer dispatch — housekeeping changes are low-risk
6. Do NOT update STATE.md to `status: completed` — that write is reserved for session-end per state-ownership contract (`skills/_shared/state-ownership.md`). Leave `status: active`.
7. Proceed directly to session-end (`/close`)

Focus: git cleanup, SSOT refresh, CI fixes, branch merges, documentation.
End with a single commit summarizing all housekeeping work.

### Feature Sessions
- Full wave execution (5 roles mapped to configured wave count)
- 4-6 agents per wave (read from Session Config)
- Balance between implementation speed and quality

### Deep Sessions
- Full wave execution (5 roles mapped to configured wave count)
- Up to 10-18 agents per wave (read from Session Config)
- Extra emphasis on Discovery role and Quality role
- May include security audits, performance profiling, architecture refactoring

## Error Recovery

| Situation | Action |
|-----------|--------|
| Agent times out | Re-dispatch with smaller scope |
| Agent produces broken code | Add fix task to next wave |
| Tests fail after wave | Diagnose in next wave, don't skip |
| Merge conflict between agents | Resolve manually, document |
| TypeScript errors introduced | Track count, run Full Gate per quality-gates by Quality wave |
| New critical issue discovered | Inform user, add to Impl-Polish+ roles if fits scope |
| Agent edits wrong files | Revert via git, re-dispatch with stricter scope |
| New critical issue discovered with broken behavior | Apply `skills/debug/SKILL.md` Iron Law 4-phase investigation before proposing a fix |

## Return Shape Contract (Autopilot Integration, #300)

When wave-executor is invoked as `sessionRunner` from `scripts/lib/autopilot.mjs::runLoop`, the value it returns to the loop drives the post-session kill-switches (`spiral`, `failed-wave`, `carryover-too-high`). The loop reads schema-canonical fields off the returned object — absent fields are treated as "no signal" (forward-compatible: an older or partial implementation simply does not trip the post-session gates).

```js
// Returned by sessionRunner({mode, autopilotRunId}) — superset of session-record schema.
{
  session_id: string,                           // required (used since Phase C-1)

  agent_summary?: {                             // schema-canonical (session-schema.mjs)
    complete?: number,
    partial?:  number,
    failed?:   number,                          // > 0 → kill-switch: failed-wave
    spiral?:   number,                          // > 0 → kill-switch: spiral
  },

  effectiveness?: {                             // schema-canonical (session-schema.mjs)
    planned_issues?: number,                    // 0 → carryover gate is no-op (avoids div-by-zero)
    carryover?:      number,                    // / planned > carryoverThreshold → carryover-too-high
    completion_rate?: number,
    completed_issues?: number,
  },

  usage?: {                                     // schema-canonical (autopilot token-budget kill-switch, #355)
    output_tokens?: number,                     // cumulative output tokens for this session; absence → 0 (forward-compat)
    total_tokens?: number,                      // alternative name accepted as fallback
  },
}
```

**`autopilot_run_id` propagation:** when wave-executor is invoked under autopilot, `args.autopilotRunId` is the loop-level run id. The per-iteration `sessions.jsonl` record MUST carry `autopilot_run_id: <id>` so retros can join autopilot.jsonl ↔ sessions.jsonl without schema changes. Manual sessions write `null` or omit the field — readers treat both identically per the v1 additive convention. See `skills/session-end/session-metrics-write.md`.

## Completion

After the Finalization wave completes successfully:
1. Report final status to the user
2. If `persistence: true`, suggest invoking `/close` to finalize the session. If `persistence: false`, note that the session is complete (no STATE.md to close — session-end would be a no-op).
3. Do NOT auto-commit — `/close` handles that with proper verification

## Vault-Sync Diff Reporting (#327)

When the inter-wave Quality-Lite checkpoint invokes vault-sync, it should prefer `--mode=diff` over full enforcement so the coordinator sees only regressions introduced by the current wave — not pre-existing issues that were already present at session start.

**Preferred checkpoint invocation (once a baseline exists):**

```bash
VAULT_DIR=<vault-dir> bash skills/vault-sync/validator.sh --mode diff
```

The diff JSON block (`{ new_errors, resolved_errors, baseline_count, current_count, schema_hash }`) is emitted to stdout. The coordinator parses it and surfaces a compact summary in the inter-wave checkpoint output. Focus on `new_errors` only — `resolved_errors` are informational.

**First-run bootstrap:** if no baseline file exists at `<vault-dir>/.orchestrator/metrics/vault-sync-baseline.json`, the coordinator runs `--mode=baseline` once before the next wave starts, then switches to `--mode=diff` for all subsequent checkpoints.

**Schema migration:** when the vendored schema in `validator.mjs` changes, the schema-hash in the existing baseline won't match. The validator falls back to full enforcement and emits a WARN to stderr. The coordinator must re-run `--mode=baseline` manually before resuming diff-mode checkpoints.

**Configuration:** diff-mode is enabled by default once a baseline exists. To force full enforcement at any checkpoint, set `vault-sync.mode: full` in Session Config or pass `--mode full` explicitly.

> **Cross-reference:** baseline file shape, diff output schema, and schema-hash mismatch handling are documented in `skills/vault-sync/SKILL.md` § Modes (#327).

## Inter-Wave Quality-Gate (with Auto-Fix Loop — #521)

After each wave, run the Quality-Gate. If `verification-auto-fix.enabled: true`
in Session Config, the gate uses `runQualityGateWithRetry()` from
`scripts/lib/quality-gate.mjs` which dispatches up to `max-retries` (default 2)
fixer-agent dispatches on failure.

**Quality-wave Full-Gate mandate (#724 C6):** the inter-wave gate following the **Quality wave** is ALWAYS the Full Gate (typecheck + test + lint) — never the cached Incremental short-circuit. The wave-executor threads the wave's `waveRole` into `shouldSkipIncremental` (see `wave-loop.md § Baseline cache check`); when `waveRole === 'Quality'` the cache is bypassed mechanically, so a valid cache or a narrow diff cannot downgrade the Quality-wave close-safety gate. See `skills/quality-gates/SKILL.md § Variant 3: Full Gate` — its dual consumers are session-end (Phase 2) and the Quality wave, and its Baseline-Cache invariant records that both are un-skippable.

### Invocation

```javascript
import { runQualityGateWithRetry } from '../../scripts/lib/quality-gate.mjs';

const result = await runQualityGateWithRetry({
  maxRetries: config['verification-auto-fix']?.['max-retries'] ?? 2,
  repoRoot: process.cwd(),
  dispatchFixer: async ({ failures, correctiveContext, changedFiles }) => {
    // Coordinator dispatches a code-implementer fixer subagent here with:
    //   - failures (gate + output)
    //   - correctiveContext (from .orchestrator/current-session.json)
    //   - changedFiles (since last green SHA)
    // Subagent's task: fix the failing gate, never broaden scope.
    await dispatchFixerSubagent({ failures, correctiveContext, changedFiles });
  },
});
```

### Decision flow

- `result.ok === true` → Wave green, proceed to next wave or session-end.
- `result.ok === false` → Hard abort.
  - quality-gate.mjs writes `.orchestrator/metrics/verification-failures/<ts>.json` (diagnostics bundle — automatic, redacted per `redactDiagnosticsBundle()`).
  - **Coordinator** (not fixer-subagent) appends a deviation entry to STATE.md via `appendDeviationOnDisk()` — see `wave-loop.md` § STATE.md Deviation — Auto-Fix Result.
  - Wave execution is blocked; operator must manually fix or disable auto-fix.
- `result.attempts > 1` → **Coordinator** logs a Deviation in STATE.md via `appendDeviationOnDisk()`: `auto-fix used N retries to clear Wave <wave>`.

### Skip Conditions

- `verification-auto-fix.enabled: false` (default) → fall back to single-shot
  quality-gate, abort on first failure (current behavior preserved per PRD § 3
  Gherkin negative path).
- `verification-auto-fix.max-retries: 0` → equivalent to disabled.

### /goal Continuation Anchor (opt-in — #636)

When `goal-integration.enabled: true` with seam `inter-wave-fixloop` in Session Config, the coordinator may surface ONE advisory `/goal` command at the inter-wave fix-loop seam to anchor continuation across the auto-fix retries — see `wave-loop.md` § "##### /goal Continuation Anchor" for the gate conditions, suggested command, and the LM-008 cross-reference. The advisory never alters gate semantics: `runQualityGateWithRetry()`'s exit-code result remains the judgment, and the hard-abort + diagnostics-bundle path after `max-retries` is unchanged. Default off → zero behaviour change.

### Anti-pattern (BE-012 awareness)

The fixer-agent prompt MUST include a reminder of `.claude/rules/testing.md` § "Test Quality — False-Positive Prevention"
"test-the-mock" anti-pattern. A fix that makes tests green by mocking out the
real failure is a regression vector. The fixer prompt should explicitly say:
"Do NOT change test mocks to make tests pass. Fix the actual code defect."

### Heartbeat cadence at inter-wave checkpoints (#590-3)

After each quality-gate PASS, the coordinator refreshes the session-lock heartbeat via the post-wave STATE.md step. See `wave-loop.md § 3a. Post-Wave: Update STATE.md` — step 5 contains the `updateHeartbeat` instruction and best-effort framing. The `sessionId` passed to `updateHeartbeat` is the session identifier established by session-start Phase 1.2 `acquire()` and stored in `.orchestrator/session.lock` (its `session_id` field); it matches the STATE.md frontmatter `session:` field written during Pre-Wave 1b initialization.

## Agent-Status Telemetry (#565)

Optional, best-effort operator-side observability: the coordinator pushes lightweight per-agent status at three anchors (dispatch, agent-end, wave-end rollup) via `scripts/lib/agent-status.mjs`, gated on `persistence: true`. A push NEVER blocks a wave. The tmux `--with-status-pane` flag (`skills/tmux-layout/SKILL.md`) renders the live feed. See `wave-loop.md § 3a-bis. Agent-Status Telemetry` for the exact anchors and invocation.

## Frontmatter-Guard (#328)

When an agent's task scope includes vault paths (`~/Projects/vault/` or vault subdirectories such as `40-learnings/`, `50-sessions/`, `03-daily/`, `01-projects/`), the wave-executor injects a deterministic frontmatter-schema snippet into the agent's prompt. This eliminates the recurring failure class where agents guess at enum values for `type`, `status`, or `tags`.

See `wave-loop.md` § Pre-Dispatch: Frontmatter-Guard Injection for the exact contract. The snippet generator is `scripts/lib/frontmatter-guard.mjs` (skill: `skills/frontmatter-guard/`).

## Worker-Pool Dispatch (#415)

An opt-in bounded-concurrency cursor-based pull loop that replaces the default Promise.all() fan-out for agent dispatch. Controlled by three Session Config fields under the `worker-pool` object:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `worker-pool.enabled` | boolean | `false` | When `false` (default), the small-batch Agent() dispatch is used (3–4 calls per message, cumulative up to `agents-per-wave`; large single-message fan-outs of >4 are forbidden — see `wave-loop.md § Dispatch Agents`, conf 1.0 silent-drop evidence). When `true`, `runWavePool()` from `scripts/lib/wave-executor/pool.mjs` is used instead. |
| `worker-pool.max-parallel` | integer | value of `agents-per-wave` | Maximum concurrent workers in the pool. Falls back to `agents-per-wave` when unset. Useful for capping concurrency below `agents-per-wave` on memory-constrained hosts. |
| `worker-pool.drain-timeout-ms` | integer | `10000` (10 s) | When an abort signal fires mid-run (e.g., a MAX_HOURS kill-switch), workers are sent SIGTERM via their per-worker AbortController and the pool waits at most this many milliseconds before returning partial results. |

**Backward compatibility:** `worker-pool.enabled` defaults to `false`. Sessions that omit the `worker-pool` block use the default small-batch Agent() dispatch (3–4 calls per message, waiting for each batch's tool-results before the next batch — never a large single-message fan-out). No migration required.

**When to enable:** use `worker-pool.enabled: true` when `agents-per-wave` is high (≥ 8) and the host is memory-constrained, or when you want to observe incremental agent completion rather than waiting for all agents to finish before inter-wave checks begin.

## Anti-Patterns

- **NEVER** run `run_in_background: true` during waves — you lose coordination ability
- **NEVER** skip inter-wave review — quality degrades exponentially
- **NEVER** let agents commit independently — coordinator commits at session end
- **NEVER** continue to next wave if previous wave has unresolved failures
- **NEVER** dispatch more agents than configured in `agents-per-wave`
- **NEVER** let wave execution run without reporting progress to the user
- **NEVER** ask the user a decision as inline prose or a numbered markdown list — always use `AskUserQuestion` (see `.claude/rules/ask-via-tool.md`)
- **NEVER** perform auto-commits from inside a dispatched subagent — the Auto-Commit Checkpoint (see `wave-loop.md § Auto-Commit Checkpoint`) is coordinator-only and fires only after Quality-Lite PASS. Agents report STATUS lines; the coordinator decides whether and when to commit. Subagent commits bypass the quality gate, skip the STATE.md deviation log, and violate parallel-session isolation (PSA-004 in `.claude/rules/parallel-sessions.md`).

**Auto-commit vs. coordinator-snapshot:** these two features are complementary, not competing.
- `coordinator-snapshot.mjs` (`wave-loop.md § Pre-Dispatch Coordinator Snapshot`) fires **before** agent dispatch as a stash-based working-tree backup — it protects uncommitted coordinator state from worktree merge-back collisions.
- Auto-Commit Checkpoint fires **after** Quality-Lite PASS as a durable git commit — it provides a permanent recovery point for session crashes or `git stash` incidents (V3.3 RESCUE incident, GitLab #214).

Both are gated on `persistence: true`. Neither replaces the other. The snapshot is pre-dispatch insurance; the auto-commit is post-gate durability.
