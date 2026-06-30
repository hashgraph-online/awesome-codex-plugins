---
name: session-end
user-invocable: false
tags: [orchestration, verification, commits, issues]
model: inherit
model-preference: sonnet
model-preference-codex: gpt-5.4-mini
model-preference-cursor: claude-sonnet-4-6
description: >
  Use this skill when performing a full session close-out: verifies all planned work against the agreed plan, creates issues
  for gaps, runs quality gates, commits cleanly, mirrors to GitHub, and produces a session
  summary. Triggered by /close command.
---

# Session End Skill

> **Platform Note:** State files (STATE.md, wave-scope.json) live in the platform's native directory: `.claude/` (Claude Code), `.codex/` (Codex CLI), `.cursor/` (Cursor IDE), or `.pi/` (Pi). All references to `.claude/` below should use the platform's state directory. Shared metrics live in `.orchestrator/metrics/`. See `skills/_shared/platform-tools.md`.

> **Project-instruction file:** `CLAUDE.md` and `AGENTS.md` (Codex CLI) are transparent aliases — see [skills/_shared/instruction-file-resolution.md](../_shared/instruction-file-resolution.md). All references to `CLAUDE.md` in this skill resolve via that precedence rule.

## Phase 0: Bootstrap Gate

Read `skills/_shared/bootstrap-gate.md` and execute the gate check. If the gate is CLOSED, invoke `skills/bootstrap/SKILL.md` and wait for completion before proceeding. If the gate is OPEN, continue to Phase 1.

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

## Phase 1: Plan Verification

Read back the session plan that was agreed at the start. For EACH planned item:

### 1.1 Done Items
- **Verify with evidence**: read the changed files, check git diff, run relevant test
- Confirm acceptance criteria are met
- Mark as completed

### 1.2 Partially Done Items
- Document what was completed and what remains
- Create a VCS issue for the remaining work with:
  - Title: `[Carryover] <original task description>`
  - Labels: `priority:<original>`, `status:ready`
  - Description: what's done, what's left, context for next session
- Link to original issue if applicable

### 1.3 Not Started Items
- Document WHY (blocked? de-scoped? out of time?)
- If still relevant: ensure original issue remains `status:ready`
- If no longer relevant: close with comment explaining why

### 1.3a Optional /goal Backlog-Drain (opt-in — #636)

> Advisory-only continuation anchor at the session-end backlog seam. Never auto-invokes `/goal`, never blocks the close. `/goal` is a user slash-command; the operator decides whether to drain now or carry over.

**Gate conditions** — ALL must be true for this nudge to surface:

1. `goal-integration.enabled: true` in Session Config (default: `false`).
2. `session-end-backlog` is listed in `goal-integration.seams`.

When any gate condition is false, skip this step silently — no surfaced suggestion, no STATE.md write, no AUQ.

**What it does** — when the gate fires AND ≥1 still-relevant Not-Started (§1.3) or Partially-Done (§1.2) item exists AND the operator would rather drain the backlog now than carry it to a future session, surface ONE suggested `/goal` command as an advisory bullet. Example:

```
/goal Drain the remaining backlog items <list>; done when each item's acceptance check passes as shown by 'npm test' output in this turn AND 'npm run typecheck' prints 0 errors in this turn, or stop after 20 turns.
```

**Advisory-only contract:** this step never auto-invokes `/goal`, never blocks the close, raises no AskUserQuestion, and writes nothing to STATE.md. It is informational prose only — the operator copies the command if they want it. The deterministic **Phase 2 Quality Gate** of session-end remains the completion authority: `/goal` keeps the loop alive across turns, but `npm test` / `npm run typecheck` / `npm run lint` and their exit codes decide whether the drained work is correct.

The `/goal` evaluator reads the transcript only and runs NO tools — it anchors CONTINUATION, never JUDGMENT. The suggested condition therefore references freshly-run gate output "in this turn's output" and embeds a bound ("or stop after N turns"). Cross-reference `.claude/rules/loop-and-monitor.md § LM-008` for the full `/goal` continuation-vs-judgment contract rather than restating it here.

**One goal per session:** only ONE `/goal` can be active at a time. This backlog seam and the inter-wave fix-loop seam (`wave-loop.md` § /goal Continuation Anchor) cannot both hold an active goal simultaneously — the operator picks one.

### 1.4 Emergent Work
- Tasks that were NOT in the plan but were done (fixes, discoveries)
- Document and attribute to relevant issues
- If new issues were identified: create them on the VCS platform

### 1.5 Discovery Scan (if enabled)

Read `skills/session-end/discovery-scan.md` for embedded discovery dispatch and findings triage.

### 1.6 Safety Review

> Skip if `persistence` is `false` in Session Config (STATE.md won't exist).

Review safety metrics from the session. This is informational — it does NOT block the session close.

1. Read `<state-dir>/STATE.md` to extract:
   - **Circuit breaker activations**: agents that hit maxTurns (`PARTIAL`), agents that spiraled (`SPIRAL`), agents that failed (`FAILED`)
   - **Worktree status**: which agents used worktree isolation, any fallbacks or merge conflicts
2. Read enforcement hook logs from stderr (if captured): count of scope violations blocked/warned, command violations blocked/warned
3. Summarize:
   ```
   Safety review:
   - Agents: [X] complete, [Y] partial (hit turn limit), [Z] spiral/failed
   - Enforcement: [N] scope violations, [M] command blocks
   - Isolation: [K] agents in worktrees, [J] fallbacks
   ```
4. If any agents were `SPIRAL` or `FAILED`, ensure carryover issues exist (cross-reference with Phase 1.2)

5. **Carryover validation fallback (#261):** Walk each Wave History entry in STATE.md. For every agent whose status is `SPIRAL` or `FAILED`, check whether the line ends with a `→ issue #NNN` suffix (or `→ existing #NNN`). If the suffix is absent, the auto-create call in wave-executor did not run (e.g. a consumer-project #251 V0.x.y-close incident where the session crashed before dispatch completed, or the CLI was offline at detection time). Retroactively file the carryover via `createSpiralCarryoverIssue`:

   ```js
   import { createSpiralCarryoverIssue } from '${PLUGIN_ROOT}/scripts/lib/spiral-carryover.mjs';

   // For each SPIRAL/FAILED agent missing the "→ issue #NNN" suffix:
   const result = await createSpiralCarryoverIssue({
     taskDescription: '<agent task from Wave History>',
     kind: 'SPIRAL', // or 'FAILED'
     context: '<Deviations / error context from STATE.md>',
     priority: 'high',
     vcs: '<from Session Config>'
   });
   // result.created → note new issue id in Final Report under "New Issues Created"
   // result.skipped === 'duplicate' → an earlier session already filed one; record the existing id
   // result.skipped === 'error' → log in Final Report as "⚠ carryover filing failed for <task>: <error>" and continue (do NOT block close)
   ```

   The module is idempotent via its task-hash dedup marker, so re-running the fallback across sessions will not create duplicates.

#### 1.6.6 Record "What Not To Retry" entries (#623)

> Skip if `persistence` is `false` (STATE.md won't exist).

For every `SPIRAL` or `FAILED` agent surfaced in the walk above, ALSO append a cross-session "What Not To Retry" entry to STATE.md. This is the durable, human-readable continuity slot that the NEXT session-start surfaces as a forced-read block (session-start Phase 6.5.1) so a future session does not re-attempt the same failed approach. Unlike a carryover issue (which captures unfinished work), this captures the *approach that should not be repeated*.

```js
import { appendWhatNotToRetryOnDisk } from '${PLUGIN_ROOT}/scripts/lib/state-md.mjs';

// `parsed` = parseStateMd(STATE.md); session id from the `session:` frontmatter field.
const sessionId = parsed.frontmatter.session ?? 'unknown-session';
const today = new Date().toISOString().slice(0, 10); // YYYY-MM-DD

// For each SPIRAL/FAILED agent from the Wave History walk:
await appendWhatNotToRetryOnDisk(repoRoot, {
  approach: '<agent task description from Wave History>',
  why_failed: '<SPIRAL|FAILED> — <one-line context from Deviations / error>',
  session_id: sessionId,
  date: today,
});
```

The helper is lock-guarded (PSA-005) and prunes the section FIFO to the 10 most-recent entries on each append. **Optional coordinator entry:** if the session abandoned an approach for reasons NOT captured by a SPIRAL/FAILED agent (e.g. a design that proved unworkable mid-session), the coordinator MAY add a free-text entry through the SAME `appendWhatNotToRetryOnDisk` helper with a descriptive `approach` + `why_failed`. Recording is informational and does NOT block the close.

### 1.7 Metrics Collection

Read `skills/session-end/metrics-collection.md` for JSONL schema and conditional field rules.

### 1.8 Session Review

Dispatch the session-reviewer agent to verify implementation quality before the quality gate:

> On Codex CLI, dispatch via the `session-reviewer` agent role defined in `.codex-plugin/agents/session-reviewer.toml`.

1. Invoke `subagent_type: "session-orchestrator:session-reviewer"` with:
   - **Scope**: all files changed this session (from `git diff --name-only` against the base branch)
   - **Context**: the session plan (issues, acceptance criteria) and all wave results from STATE.md
2. Wait for the reviewer's **Verdict**:
   - **PROCEED** — continue to Phase 2
   - **FIX REQUIRED** — disposition each listed item by severity:

     | Finding class | Disposition |
     |---|---|
     | HIGH+ / blocking review finding | Fix inline if quick (<2 min); else create an issue (`priority:high`, `status:ready`) and note it in the Final Report |
     | MED / LOW review finding | Fold in-session if quick; else record under "Unresolved Review Findings" in the Final Report — DO NOT create an issue (#617) |
     | Planned-carryover (item was in the plan, not finished) | ALWAYS create a `[Carryover]` issue per Phase 1.2 — unchanged |
     | SPIRAL / FAILED agent carryover | ALWAYS file via `createSpiralCarryoverIssue` per Phase 1.6 — unchanged |

### 1.9 Mission-Status Classification (when `mission-status` present in STATE.md)

> Skip if `persistence` is `false` in Session Config, or if `mission-status:` is absent from STATE.md frontmatter. When absent, fall back to binary checkbox detection in 1.1–1.4 unchanged — full backward compat.

When STATE.md frontmatter contains a `mission-status:` array (set by session-plan + wave-executor per #340), use the enum values to classify items into the 1.1–1.4 buckets. Read the array via `parseMissionStatus(frontmatter)` from `scripts/lib/state-md.mjs`.

**Classification mapping:**
- `status: completed` → **1.1 Done Items** (item finished; verify with evidence per 1.1)
- `status: testing` or `status: in-dev` → **1.2 Partially Done** (carryover; document what remains)
- `status: validated` or `status: brainstormed` → **1.3 Not Started** (carryover; check if still relevant)
- Items NOT present in the `mission-status:` array → fall back to binary checkbox detection per 1.1–1.4 unchanged

**Backward compat:** When `mission-status:` is absent from STATE.md (pre-#340 STATE.md files, or sessions where session-plan did not emit the block), behave exactly as before — enum classification is skipped entirely and 1.1–1.4 binary checkbox logic runs as the sole classification mechanism.

### 1.10 Mission Status Breakdown (when `mission-status` present)

> Skip if `mission-status:` is absent from STATE.md frontmatter (backward compat — no breakdown emitted).

After classifying items in Phase 1.9, produce a **Mission Status breakdown** subsection as part of the closed/carryover summary output. Count the number of tasks at each enum value across ALL waves:

```
### Mission Status Breakdown
- completed:    <N> tasks
- testing:      <N> tasks
- in-dev:       <N> tasks
- validated:    <N> tasks
- brainstormed: <N> tasks
- Total:        <N> tasks across <W> waves
```

Rules:
- Count each task-id entry from the `mission-status:` frontmatter array by its current `status` value.
- `completed` maps to Phase 1.1 (Done). `testing` + `in-dev` map to Phase 1.2 (Partial). `validated` + `brainstormed` map to Phase 1.3 (Not Started).
- Include this block in the Phase 6 Final Report under `### Carried Over` or as a standalone subsection immediately after the Completed/Carried Over/New Issues lists.
- When all tasks are `completed`, the breakdown still appears (confirms clean session state).

## Phase 2: Quality Gate

> **Verification Reference:** See `verification-checklist.md` in this skill directory for the full quality gate checklist.

Run ALL checks listed in the verification checklist. If any check fails: fix if quick (<2 min), otherwise create a `priority:high` issue. Do NOT commit broken code.

### Phase 2.0a: Echo-Stub Detection (GH #42)

`gate-full.mjs` emits a top-level `stubbed: {}` map in its JSON result, keyed by check name (`typecheck`, `test`, `lint`); value is `{ kind: 'echo'|'noop' }`. When any check was short-circuited as a stub, `runCheck()` already returned `status: 'pass'` — so the overall gate verdict is green, but the result is meaningless.

**Detection:** immediately after parsing the `gate-full` JSON result, evaluate:

```js
const stubbedEntries = Object.entries(result.stubbed ?? {});
```

**If `stubbedEntries.length > 0`**, surface a HIGH WARN block in the close summary:

```
⚠ QUALITY GATE STUBBED — <N> command(s) are echo/noop stubs, not real checks:
  - <check-name>: <kind> stub  (configured: "<command string>")
Re-configure with a real test command in CLAUDE.md Session Config before /close,
OR document this exception in /close --reason.
```

**Behavior by `enforcement` mode:**

- `enforcement: strict` — **block /close**. Treat as a Phase 2 failure. Present the WARN block and exit without committing.
- `enforcement: warn` (default) — continue, but write `quality-gate-stubbed: true` to STATE.md Deviations so the metrics writer captures it.
- `enforcement: off` — silent. Emit a single-line `stderr` log only (`echo-stub detected: <check-name>`).

**Recipe:** for container-based test runners (e.g. EspoCRM PHPUnit) where an echo-stub was the historical workaround, see [`docs/recipes/quality-gate-container-pattern.md`](../../docs/recipes/quality-gate-container-pattern.md).

**Source issue:** GH #42 (root cause: a consumer-project #251 V0.15.7-close incident — silent false-positive close-verdicts from echo-stub test commands).

### 2.1 Vault Validation (if configured)

Read `skills/session-end/vault-operations.md` for validator bash contract and reporting matrix.

### 2.2 CLAUDE.md (or AGENTS.md) Drift Check (if configured)

Read `skills/session-end/drift-operations.md` for checker bash contract and reporting matrix. Complements 2.1: vault-sync validates frontmatter inside the vault tree; drift-check validates narrative claims (paths, counts, issue refs, session-file refs) in top-level repo docs.

### 2.3 Vault Staleness Check (if configured)

> Skip this subsection if `vault-staleness.enabled` is not `true` (default: `false`).

#### Step 1 — Resolve mode

Read `vault-staleness.mode` from `$CONFIG` (default: `warn`). Valid values: `off | warn | strict`.

If `mode === 'off'`, skip Phase 2.3 entirely.

#### Step 2 — Invoke staleness probes

Both probes already ship in `skills/discovery/probes/`. Invoke each via Node import (no shell-out):

```js
import { runProbe as runStaleness } from '$REPO_ROOT/skills/discovery/probes/vault-staleness.mjs';
import { runProbe as runNarrative }  from '$REPO_ROOT/skills/discovery/probes/vault-narrative-staleness.mjs';

const projectStaleness = await runStaleness(projectRoot, config);
const narrativeStaleness = await runNarrative(projectRoot, config);
```

Each probe returns `{ findings: Array, metrics: Object, duration_ms: Number }` and auto-appends a JSONL summary record to its respective metrics file.

#### Step 3 — Aggregate and route by mode

```
totalFindings = projectStaleness.findings.length + narrativeStaleness.findings.length
```

- `mode === 'warn'` (default): report findings to closing report Docs Health line. Never block close.
- `mode === 'strict'`:
  - If `totalFindings === 0`: continue, log `Vault staleness: clean (mode=strict)`.
  - If `totalFindings > 0`: BLOCK the close. Present the findings list and offer override:
    - On Claude Code: AskUserQuestion with options:
      1. "Fix and retry Phase 2.3" (Recommended) — exit close, let user investigate
      2. "Override and close" — proceed, log a Deviation entry in STATE.md `## Deviations`:
         `- [<ISO timestamp>] Phase 2.3: Vault staleness strict-mode findings overridden by user. Findings: <count> (projects: <N>, narratives: <M>).`
      3. "Abort close" — exit close without writing
    - On Codex CLI / Cursor IDE: same options as numbered Markdown list.

#### Step 4 — Surface to closing report

Pass the aggregated counts and mode forward to Phase 6 Final Report (Docs Health line — see Phase 6 below).

## Phase 2.5: Custom Phases (#637)

> Opt-in. Skip this phase entirely if `custom-phases` in `$CONFIG` is absent or `[]` (the default).

Repos declare deterministic close/housekeeping phases as a **contract** (not the freeform `special:` convention): each phase runs a `command` with exit-code gating and Final-Report reporting. The block is parsed by `scripts/lib/config/custom-phases.mjs`; each record is `{ name, when, command, mode, review }` (already validated — unsafe records were dropped at parse time).

#### Step 1 — Read + filter by `when`

Read `custom-phases` from `$CONFIG` and the `session-type` from STATE.md frontmatter (`feature | deep | housekeeping | none`):

- If `session-type === 'housekeeping'`: keep phases with `when ∈ {housekeeping, both}`.
- Otherwise (`feature`/`deep`/any other): keep phases with `when ∈ {session-end, both}`.

If no phases remain after filtering, skip to Phase 3.

#### Step 2 — Run each phase in declaration order

For each kept phase:

- `mode === 'off'` ⇒ skip silently (do not run the command).
- Otherwise run `command` via Bash. Capture the **exit code** and the **last ~10 lines of stdout** (these become the report summary — do NOT inline the full output).
- If `review` is set, read that file after the command as the review step and note its path in the report.

#### Step 3 — Route by `mode`

- `mode === 'warn'` (default): record the result (name, exit code, summary) for the Phase 6 Final Report "Custom Phases" line. Never block the close — even on a non-zero exit.
- `mode === 'hard'`:
  - exit code `0` ⇒ continue; record `<name>: pass (mode=hard)`.
  - exit code `≠ 0` ⇒ **BLOCK the close** using the same routing pattern as Phase 2.3 strict-mode. Present the phase name + captured summary and offer override:
    - On Claude Code: AskUserQuestion with options:
      1. "Fix and retry Phase 2.5" (Recommended) — exit close, let the user investigate.
      2. "Override and close" — proceed, log a Deviation entry in STATE.md `## Deviations`:
         `- [<ISO timestamp>] Phase 2.5: custom-phase '<name>' (mode=hard) exited <code>, overridden by user.`
      3. "Abort close" — exit close without writing.
    - On Codex CLI / Cursor IDE: same options as a numbered Markdown list.

A `hard`-fail (whether overridden or not) ALWAYS appends its result line to STATE.md `## Deviations`; `warn`-mode results do not.

#### Step 4 — Surface to closing report

Pass each phase result `(name, mode, exitCode, summary, review?)` forward to the Phase 6 Final Report "Custom Phases" line (see Phase 6 below).

## Phase 3: Documentation Updates

> **Final heartbeat (#590-3)** — at Phase 3 entry, refresh the session-lock heartbeat BEFORE the multi-minute close-out chain (vault-mirror, dialectic, durable-commit, metrics). A long-idle deep session may not have had PostToolBatch activity for >4h; without a refresh the 4h-TTL lock would lapse mid-close and appear stale to a concurrent session. Place this call BEFORE Phase 3.8 Session Lock Release (which deletes the lock — refreshing a deleted lock is a no-op). Best-effort: a failure must NOT block the close.
>
> ```js
> // Final heartbeat (#590-3) — refresh before the multi-minute close-out (vault-mirror, dialectic, durable-commit)
> // so a long-idle deep session's 4h-TTL lock does not lapse mid-close.
> // BEFORE Phase 3.8 lock-release (which deletes the lock).
> import { updateHeartbeat } from 'scripts/lib/session-lock.mjs';
> updateHeartbeat({ sessionId, repoRoot: process.cwd() });
> ```
>
> Skip silently if `persistence: false` in Session Config (no session.lock exists in that mode).

### 3.0 Defensive Cleanup

Delete `<state-dir>/wave-scope.json` if it still exists:

```bash
rm -f <state-dir>/wave-scope.json
```

This should have been cleaned up by wave-executor after the final wave, but crashed sessions or interrupted executions may leave it behind. A stale scope manifest from a previous session could incorrectly restrict the next session's enforcement hooks.

### 3.1 SSOT Files
- Update `STATUS.md` / `STATE.md` if they exist (metrics, dates, status)
- Update `CLAUDE.md` (or `AGENTS.md` on Codex CLI) if patterns or conventions changed during this session
- Check `<state-dir>/rules/` — if a new pattern was established, suggest a new rule file

### 3.2 Docs Verification (docs-orchestrator integration)

> Skip this subsection if `docs-orchestrator.enabled` config is not `true` (default: `false`). Also skip entirely if `docs-orchestrator.mode` is `off`.

Reads `docs-tasks` from STATE.md frontmatter (written by wave-executor Pre-Wave 1b), computes `CHANGED_FILES` via `git diff --name-only "$SESSION_START_REF..HEAD"`, and runs a per-task verification loop (outcome: `ok`/`partial`/`gap`). In `warn` mode logs results non-blocking; in `strict` mode blocks on any gap and presents an AskUserQuestion override prompt. Emits a `### Documentation Coverage (docs-orchestrator)` block for inclusion in the Phase 6 Final Report.

**See `phase-3-2-docs-verification.md` for full details.**

### 3.2a Session Handover (for significant sessions)
If this session made substantial changes, create or update:
- `<state-dir>/session-handover/` doc with: tasks completed, resume point, metrics changed, issues opened/closed
- Or update `<state-dir>/STATE.md` with session digest

### 3.3 Claude Rules Freshness
Review `<state-dir>/rules/` files that are relevant to this session's work:
- Are the rules still accurate after this session's changes?
- Should any rule be updated with new patterns?
- Should a new path-scoped rule be created?
- Suggest changes but DO NOT modify without user confirmation

### 3.4 Update STATE.md

> **Ownership Reference:** See `skills/_shared/state-ownership.md`. session-end is authorized to set `status: completed` plus the optional `updated` timestamp (#184), and — as of Phase A of Epic #271 — the 5 Recommendation fields written by Phase 3.7a. No other fields.

> **Runtime Ordering Note (Epic #271 Phase A):** Phase 3.4's `status: completed` write executes LAST in Phase 3, AFTER Phase 3.7 (sessions.jsonl) and Phase 3.7a (Compute and Write Recommendations). The ordinal position here (3.4) is kept for historical compatibility; the canonical runtime order is `3.1 → 3.2 → 3.3 → 3.4a → 3.5 → 3.5a → 3.6 → 3.6.5 → 3.6.7 → 3.6.8 → 3.7 → 3.7a → 3.7b → 3.7c → 3.4`. Rationale: Phase 3.7a reads in-memory session metrics and writes the 5 Recommendation fields via `updateFrontmatterFields`; that write must complete BEFORE the STATE.md frontmatter is finalized with `status: completed` so the Recommendation fields are visible to the next session-start while STATE.md is still `status: active`. Crash-resilience: if `/close` aborts between 3.7a and 3.4, STATE.md carries `status: active` + Recommendations; session-start Phase 1.5 offers resume (and the banner renders). If the reverse ordering were used (status: completed first), a crash would leave `status: completed` without Recommendations — the Reader would silently no-op the banner, losing the handoff.

> Gate: Only run if `persistence` is enabled in Session Config and `<state-dir>/STATE.md` exists.
1. Set frontmatter `status: completed`
2. Record final wave count and completion time in the frontmatter
3. Touch `updated: <ISO 8601 UTC>` in the frontmatter (issue #184). Use `scripts/lib/state-md.mjs` → `touchUpdatedField` for safety:
   ```bash
   node --input-type=module -e "
   import {readFileSync, writeFileSync} from 'node:fs';
   import {touchUpdatedField} from '${PLUGIN_ROOT}/scripts/lib/state-md.mjs';
   const p = '<state-dir>/STATE.md';
   writeFileSync(p, touchUpdatedField(readFileSync(p, 'utf8'), new Date().toISOString()));
   "
   ```
   Silent no-op if the file has no frontmatter.
4. Keep the file as a record — do NOT delete it (next session-start reads it)

If STATE.md doesn't exist, skip this subsection.

### 3.4a Coordinator Snapshot Cleanup (#196)

Pre-dispatch snapshots (`refs/so-snapshots/<sessionId>/wave-*`) are created by wave-executor before each wave dispatch so that session-start can offer recovery if a session is interrupted mid-wave. On a clean close those snapshots are no longer needed and should be deleted. In addition, orphaned refs from older sessions that were never cleaned up (e.g. after a hard crash) are garbage-collected using an age-based policy (14 days).

> Gate: Only run if `persistence` is `true` in Session Config. Skip entirely when persistence is off (snapshots are never written in that mode).

```bash
node --input-type=module -e "
import { listSnapshots, deleteSnapshot, gcSnapshots } from '${PLUGIN_ROOT}/scripts/lib/coordinator-snapshot.mjs';

// Step A: delete this session's snapshots (clean close → we don't need them)
const mine = await listSnapshots({ sessionId: '${SESSION_ID}' });
for (const s of mine) {
  const r = await deleteSnapshot({ refName: s.ref });
  if (!r.ok) console.error('snapshot cleanup:', r.error);
}

// Step B: GC orphans older than 14 days (non-fatal)
const gc = await gcSnapshots({ olderThanDays: 14 });
console.log(\`snapshot cleanup: deleted \${mine.length} from this session + \${gc.deletedCount} expired orphans (scanned \${gc.scanned}).\`);
"
```

Failures in either step are logged to stderr but do **not** block session close — a missed cleanup is self-healing via the 14-day GC on the next session.

This cleanup is the counterpart to the session-start Phase 1.5 recovery prompt: once a session closes cleanly, future sessions must not be offered recovery for its snapshots.

### 3.5 Session Memory

> Gate: Only run if `persistence` is enabled in Session Config AND platform is Claude Code (session memory at `~/.claude/projects/` is Claude Code-only). Learnings (Phase 3.5a) and metrics (Phase 3.7) still write to `.orchestrator/metrics/` on all platforms.

1. Create `~/.claude/projects/<project>/memory/session-<YYYY-MM-DD>.md` with:
   - Frontmatter: `name`, `description` (1-line summary), `type: project`
   - `## Outcomes` — per-issue status (completed / partial / not started) with evidence
   - `## Learnings` — patterns discovered, architectural insights, gotchas
   - `## Next Session` — priority recommendations, suggested session type, blockers
2. Update `~/.claude/projects/<project>/memory/MEMORY.md`:
   - Under a `## Sessions` heading (create if missing), add:
     `- [Session <date>](session-<date>.md) — <one-line summary>`

### 3.5a Learning Extraction + 3.6 Memory Cleanup & Learnings Write

Read `skills/session-end/learning-patterns.md` for extraction heuristics, confidence updates, passive decay, and JSONL write procedure.

### 3.6.3 Memory Proposals Collection (#501, F2.1)

> Gate: Skip this phase entirely when ANY of:
> - `persistence` is `false` in Session Config
> - `memory.proposals.enabled` is `false` (default: `true`)
> - `.orchestrator/metrics/proposals.jsonl` does not exist OR contains zero entries

After learnings are written (Phase 3.6) and BEFORE auto-dream dispatch (Phase 3.6.5), collect agent-proposed memory entries written during this session and present them to the operator via `AskUserQuestion` multiSelect. Approved entries flow to `learnings.jsonl` with `_provenance: agent-proposed@<wave-id>`. Rejected entries are archived to `.orchestrator/proposals.rejected.log`.

The proposals queue is populated mid-session by wave-executor agents calling `node scripts/memory-propose.mjs --type ... --subject ... --insight ... --evidence ... --confidence ...`. The CLI enforces:
- Quota per wave (default 5, configurable via `memory.proposals.quota-per-wave`)
- Confidence floor (default 0.5, configurable via `memory.proposals.confidence-floor`)
- Wrong-context guard (CLI exits non-zero when STATE.md `status` is not `active`)

#### Coordinator-direct procedure

1. Read Session Config: `memory.proposals.enabled` (default `true`), `memory.proposals.quota-per-wave` (default 5), `memory.proposals.confidence-floor` (default 0.5), `auto-dream.min-confidence` (default 0.5 — issue #566; SECOND gate above the write-time `memory.proposals.confidence-floor`).

2. Invoke `collectProposals` from `scripts/lib/memory-proposals/collector.mjs`, passing the collect-emit confidence floor from Session Config:
   ```javascript
   import { collectProposals } from '${PLUGIN_ROOT}/scripts/lib/memory-proposals/collector.mjs';
   const { queue, stats, perWaveSummaries } = await collectProposals({
     repoRoot: process.cwd(),
     // Issue #566: collect-emit confidence floor. Records with
     // `record.confidence < minConfidence` are dropped from `queue` (but
     // counted in stats). When the key is absent, defaults to 0.5 via the
     // `_parseAutoDream` parser.
     minConfidence: config['auto-dream']?.['min-confidence'],
   });
   ```

3. If `queue.length === 0`: log `memory-proposals: queue empty (stats: ${JSON.stringify(stats)})` and continue.

4. **AUQ pagination logic**: partition the queue into FIFO batches of 4 inline:

   - Empty queue → silent skip (no AUQ rendered).
   - 1-4 items → single multiSelect call with all items as options.
   - 5+ items → sequential multiSelect calls in batches of 4 (FIFO order; final batch may have < 4 items).

   ```javascript
   // Inlined from former scripts/lib/memory-proposals/auq-partition.mjs (PRD F2.2 #502 closed; see #558 M2).
   const BATCH_SIZE = 4;
   const batches = [];
   if (Array.isArray(queue) && queue.length > 0) {
     for (let i = 0; i < queue.length; i += BATCH_SIZE) {
       batches.push(queue.slice(i, i + BATCH_SIZE));
     }
   }
   ```

   Then iterate `batches` and emit one `AskUserQuestion` per batch with `header: "Memory — Confirm Proposals (Batch N of M)"`. Option label format: `[<type-12>] | <subject-40> | conf=X.XX`. Option description: `evidence: <first 60 chars of insight>`. `multiSelect: true`.

5. After all batches answered, partition the queue into `approved` (any option selected across all batches) and `rejected` (all unselected).

6. Invoke `writeApproved` and `archiveRejected` from `scripts/lib/memory-proposals/sink.mjs`:
   ```javascript
   import { writeApproved, archiveRejected, clearProposalsJsonl } from '${PLUGIN_ROOT}/scripts/lib/memory-proposals/sink.mjs';
   const writeResult = await writeApproved({ approved, repoRoot, sessionId });
   const archiveResult = await archiveRejected({ rejected, repoRoot, reason: 'user-declined' });
   await clearProposalsJsonl({ repoRoot });
   ```

7. Log outcome for Phase 6 Final Report: `memory.proposals: <queued> queued → <approved> approved, <rejected> rejected (dropped: <dropped> quota, <below_floor> below-floor)`.

#### Failure modes

- If `collectProposals` fails (fs error): log warning `⚠ memory-proposals: collect failed (${err}) — skipping`, do not block session close.
- If `writeApproved` reports errors per-record: log each, but continue (per-record fault isolation per sink contract).
- If `clearProposalsJsonl` fails: log warning; do not block. The file may be re-collected at the next session-end, idempotent.

#### Cross-references

- Spec: issue #501 — memory-proposals (F2.1); no standalone PRD file
- Modules: `scripts/lib/memory-proposals/{schema,store,collector,sink}.mjs`
- CLI: `scripts/memory-propose.mjs` (agents call this)
- Hook: `hooks/pre-bash-memory-propose-audit.mjs` (audit trail)
- Coordinator AUQ spec: `agents/memory-proposal-collector.md` (reference doc)
- Sibling phases: 3.6.5 Auto-Dream (#502), 3.6.6 Skill-Applied Judge (#645 L3), 3.6.7 Auto-Dialectic (#506)
- Issue: #501

### 3.6.5 Auto-Dream Dispatch (#502, F2.2)

> Skip this phase if `memory-cleanup-threshold: 0` (kill-switch per PRD F2.2). Also skip on non-Claude-Code platforms (memory dir at `~/.claude/projects/` is Claude Code-only, mirrors Phase 3.5 gate).

After learnings are written (Phase 3.6), determine whether to emit a **manual-cadence nudge** to run `/memory-cleanup --dry-run` in the next session. The decision uses MEMORY.md line count and a sessions-since-last-cleanup signal. There is no `memory-cleanup` agent in the registry, so the historical auto-dream subagent dispatch never fired (see #614) — the nudge replaces it. A manually-run `/memory-cleanup --dry-run` writes a unified-diff proposal to `.orchestrator/pending-dream.md` for the session after that to apply via `/memory-cleanup --apply-pending`.

1. Read `memory-cleanup-threshold` (default 5) and `memory-cleanup-soft-limit` (default 180) from `$CONFIG`.
2. Invoke `shouldDispatchAutoDream` from `scripts/lib/auto-dream.mjs`:

   ```javascript
   import { shouldDispatchAutoDream } from '${PLUGIN_ROOT}/scripts/lib/auto-dream.mjs';
   import { resolveMemoryDir } from '${PLUGIN_ROOT}/scripts/lib/memory-paths.mjs';
   const memoryDir = resolveMemoryDir();
   const decision = await shouldDispatchAutoDream({
     repoRoot: process.cwd(),
     memoryDir,
     threshold: config['memory-cleanup-threshold'] ?? 5,
     softLimit: config['memory-cleanup-soft-limit'] ?? 180,
   });
   ```
3. If `decision.trigger === false`: log `auto-dream: not triggered (${decision.reason})` and continue. Emit no nudge.
4. If `decision.trigger === true`: **do not dispatch a subagent** — there is no `memory-cleanup` agent in `agents/`, so the historical `Agent({…})` dispatch pointed at the agent name `memory-cleanup` (a subagent type that was never built) and never fired (see #614). Instead, emit a manual-cadence nudge and continue:

   `auto-dream: cadence reached (${decision.reason}) — run /memory-cleanup --dry-run manually in the next session, then apply the proposal with /memory-cleanup --apply-pending.`

   The `shouldDispatchAutoDream` decision helper and `scripts/lib/auto-dream.mjs` lib stay in use: they compute the signal that drives this nudge and back the manual `/memory-cleanup` path (`writePendingDream` / `readPendingDream` / `applyPendingDream`).
5. Record the outcome (skipped / nudge-emitted) so Phase 6 Final Report can surface a line: `auto-dream: manual /memory-cleanup --dry-run recommended (cadence reached) — apply with /memory-cleanup --apply-pending next session`.

The pending-dream sidecar at `.orchestrator/pending-dream.md` is intentionally outside the vault tree — vault-mirror (Phase 3.7) must exclude it from its scope so the proposal survives the session close without being mirrored into 50-sessions/.

Cross-reference: PRD F2.2 acceptance criteria; `scripts/lib/auto-dream.mjs` API (`shouldDispatchAutoDream`, `readDreamSignals`, `writePendingDream`, `readPendingDream`, `applyPendingDream`).

### 3.6.6 Skill-Applied Judge (#645, L3)

> **Default OFF.** Skip this phase — with NO module import and NO sidecar created — unless BOTH gates pass (evaluated in this order):
> 1. `config['skill-evolution'].judge !== true` → skip (the `judge:` key in the top-level `skill-evolution:` block; default `false`).
> 2. `persistence === false` in Session Config → skip.
>
> When skipped, log `skill-judge: disabled (skill-evolution.judge=false)` (or `persistence=false`) and return. **This is the disabled-path guarantee:** with the judge off, only L1 (`skill-invocations.jsonl`, written by the PreToolUse hook) and L2 (`scripts/lib/skill-health/join.mjs`) records exist — no judgment, no error, zero L3 code executes. Do NOT import `scripts/lib/skill-judge.mjs` on the disabled path.

After learnings are written (Phase 3.6) and the auto-dream decision is made (Phase 3.6.5), and when the judge is enabled, run a **bounded, read-only LLM-judge** over this session's selected skills to emit ADVISORY per-skill applied/completed judgments to `.orchestrator/metrics/skill-judgments.jsonl`.

**The #614 distinction (the whole point of L3's Design A):** unlike the 3.6.5 / 3.6.7 nudge-only paths — which cannot dispatch a live subagent because the target read-only agents (`memory-cleanup`, `dialectic-deriver`) cannot write their own sidecars — L3 performs a **LIVE read-only dispatch**. This is #614-safe because the read-only `skill-applied-judge` agent **RETURNS JSON** and the **COORDINATOR writes the sidecar**, not the agent. A read-only agent that returns judgments is allowed; a read-only agent that must write a file is the #614 trap.

**Advisory-only:** the judge output is written with `advisory: true` (schema-rejected otherwise) and **NEVER feeds an auto-action gate** — not a sunset decision, not a C2 repair (`scripts/lib/skill-evolution/*`), not a promotion. Per #645 R9(b) the C2 repair gate stays deterministic; L3 is a signal for humans/dashboards only.

1. Read `config['skill-evolution'].judge` (default `false`), `config['skill-evolution']['judge-budget-tokens']` (default 8000), and `persistence`. Apply the two skip gates above.

2. Determine the **judged set** — only THIS session's selected skills. Read `.orchestrator/metrics/skill-invocations.jsonl` and collect the distinct `skill` values whose `session_id` matches the current session id. If the judged set is empty, `runSkillJudge` returns `status: 'empty-input'` (no dispatch) — log and continue.

3. Invoke `runSkillJudge` from `scripts/lib/skill-judge.mjs`, wiring the real dispatch via the DI seam:

   ```javascript
   import { runSkillJudge } from '${PLUGIN_ROOT}/scripts/lib/skill-judge.mjs';
   import { appendSkillJudgment } from '${PLUGIN_ROOT}/scripts/lib/skill-judgments-schema.mjs';
   import path from 'node:path';

   const budgetTokens = config['skill-evolution']['judge-budget-tokens'] ?? 8000;
   const result = await runSkillJudge({
     // Claude Code path: wire the real read-only haiku subagent as dispatchAgent.
     dispatchAgent: ({ model, prompt, maxTokens }) =>
       Agent({ subagent_type: 'skill-applied-judge', model: 'haiku', prompt, max_tokens: maxTokens }),
     repoRoot: process.cwd(),
     sessionId,
     transcriptTail,                 // recent session transcript excerpt (UNTRUSTED — fenced by the lib)
     selectedSkills,                 // distinct skills from step 2
     model: 'haiku',
     budget: { input: budgetTokens, output: 4000 },
   });
   ```

   - **Claude Code path:** `dispatchAgent` wraps the real `Agent({ subagent_type: 'skill-applied-judge', model: 'haiku', … })`. The agent is `sandbox-tier: read-only` and RETURNS one fenced ```json block — it never writes files.
   - **Codex / Cursor path:** there is no subagent type. Wire `dispatchAgent` as a coordinator-inline call (the coordinator itself reasons over the prompt and returns `{ text }`), keeping the identical `runSkillJudge` signature. Same DI seam, no harness subagent.

4. On `result.status === 'ok'`: the **COORDINATOR** writes each returned judgment to the sidecar. Stamp the per-record metadata (`timestamp`, `event: 'judged'`, `session_id`, `advisory: true`, `model`, `schema_version: 1`) and append:

   ```javascript
   const judgmentsPath = path.join(process.cwd(), '.orchestrator/metrics/skill-judgments.jsonl');
   const nowIso = new Date().toISOString();
   for (const j of result.judgments) {
     await appendSkillJudgment(
       { timestamp: nowIso, event: 'judged', skill: j.skill, session_id: sessionId,
         applied: j.applied, completed: j.completed, confidence: j.confidence,
         advisory: true, model: 'haiku' },
       { path: judgmentsPath },
     );
   }
   ```

   `appendSkillJudgment` re-validates each record; `advisory !== true` is schema-rejected, so a tampered record can never be persisted.

5. On `result.status === 'empty-input'` or `'budget-exceeded'`: log the status (e.g. `skill-judge: skipped (budget-exceeded used=N budget=M)`) and continue. No sidecar write on either non-ok status.

6. **Failures are non-fatal.** Any error from the dispatch or write is logged to `.orchestrator/metrics/sweep.log` and the close continues — same posture as Phase 3.6.7. The judge is advisory; a failed judgment must never block session close.

Cross-reference: PRD §A L3 acceptance criteria (#645, epic #643); `scripts/lib/skill-judge.mjs` API (`runSkillJudge`, `validateModel`, `estimateInputTokens`, `checkBudget`, `buildJudgePrompt`, `parseJudgeResponse`); `scripts/lib/skill-judgments-schema.mjs` (`appendSkillJudgment`, `readSkillJudgments`, `validateSkillJudgment`); agent `agents/skill-applied-judge.md`.

### 3.6.7 Auto-Dialectic Dispatch (#506, F2.5)

> Skip this phase if `dialectic.cadence: 0` (kill-switch per PRD F2.5 AC3). Also skip if `persistence` is `false` in Session Config.

After learnings are written (Phase 3.6) and the auto-dream decision is made (Phase 3.6.5), determine whether to emit a **manual-cadence nudge** to run `/evolve --dialectic` in the next session. The decision uses sessions-since-last-dialectic counted against `.orchestrator/dialectic-last-run`. There is no `evolve` agent in the registry, and the nearest one (`dialectic-deriver`) is `sandbox-tier: read-only` and cannot write the sidecar — so the historical auto-dialectic subagent dispatch never fired (see #614). On trigger, emit the nudge and advance `.orchestrator/dialectic-last-run`; the timestamp is updated only when the nudge is emitted (not on skip), so the reminder surfaces once per cadence window rather than every session. A manually-run `/evolve --dialectic --dry-run` writes the proposed diff to `.orchestrator/dialectic-pending.md`.

1. Read `dialectic.cadence` (default 5), `dialectic.model` (default haiku), `dialectic.budget-tokens` (default 8000) from `$CONFIG`.

2. Invoke `shouldDispatchAutoDialectic` from `scripts/lib/auto-dialectic.mjs`:
   ```javascript
   import { shouldDispatchAutoDialectic } from '${PLUGIN_ROOT}/scripts/lib/auto-dialectic.mjs';
   const decision = await shouldDispatchAutoDialectic({
     repoRoot: process.cwd(),
     cadence: config.dialectic?.cadence ?? 5,
   });
   ```

3. If `decision.trigger === false`: log `auto-dialectic: not triggered (${decision.reason})` and continue. Emit no nudge. Do NOT update `.orchestrator/dialectic-last-run`.

4. **AC4 precondition guard:** Even if cadence met, if `signals.sessionsSinceLast === 0 && signals.learningsSinceLast === 0`, skip with reason `no-new-input-since-last-run`. The Final Report (Phase 6) MUST include the literal string `dialectic: skipped (no new input since last run)`.

5. If `decision.trigger === true`: **do not dispatch a subagent** (see #614 — no `evolve` agent exists; `dialectic-deriver` is read-only and cannot write the sidecar). Instead, emit a manual-cadence nudge and continue:

   `auto-dialectic: cadence reached (${decision.reason}) — run /evolve --dialectic --dry-run manually in the next session, review .orchestrator/dialectic-pending.md, then apply with /evolve --dialectic --apply.`

   The `shouldDispatchAutoDialectic` decision helper and `scripts/lib/auto-dialectic.mjs` lib stay in use: they compute the cadence signal that drives this nudge.

6. When the nudge is emitted (cadence reached), update `.orchestrator/dialectic-last-run` via `writeDialecticLastRun({ repoRoot, isoTimestamp: new Date().toISOString() })` so the cadence counter advances and the nudge does not repeat every session. Atomic; failures non-fatal.

7. Record outcome (skipped / nudge-emitted) for Phase 6 Final Report: `auto-dialectic: manual /evolve --dialectic --dry-run recommended (cadence reached) — apply with /evolve --dialectic --apply next session`.

The `.orchestrator/dialectic-pending.md` sidecar is intentionally outside the vault tree — vault-mirror (Phase 3.7) MUST exclude it from its scope.

Cross-reference: PRD F2.5 acceptance criteria (#506); `scripts/lib/auto-dialectic.mjs` API.

> **Dialectic chain rationale** — design choices in the manual `/evolve --dialectic` chain (`/evolve → runDialecticDeriver → dispatchAgent → Agent`). Session-end no longer auto-dispatches this chain (see #614 — the `evolve` agent never existed); the rationale below applies when you run `/evolve --dialectic` manually:
> - **/evolve → subagent (not direct invoke):** the manual `/evolve --dialectic` skill spawns a subagent so the dialectic pass runs in a fresh context window — keeping the deriver's input-heavy payload (top-50 learnings + last-10 sessions + 2 peer cards + steering) out of the invoking coordinator's context, and letting the deriver run as Haiku while the coordinator stays Opus.
> - **/evolve → runDialecticDeriver (not direct dispatchAgent):** /evolve owns argument parsing, config resolution, dry-run/apply gating, error-handling, and sidecar writes; runDialecticDeriver owns the pure derivation pipeline (load → payload → budget-check → dispatch → parse → guard). Separating skill-level orchestration from deriver business logic lets unit tests exercise the deriver without standing up the full evolve skill.
> - **runDialecticDeriver → dispatchAgent (DI boundary):** per `.claude/rules/prompt-caching.md:3`, session-orchestrator forbids direct `@anthropic-ai/sdk` imports in business logic (the harness manages caching at the platform layer). dispatchAgent is the injected boundary — the evolve skill wires the real `Agent({...})` harness call at runtime, tests pass a `vi.fn()` mock. Same DI shape as `scripts/lib/autopilot.mjs::runLoop({opts})` (cf. `scripts/dialectic-deriver.mjs:7-16,531`).

### 3.6.8 Reconciliation Rule Proposals (#696, FA3)

> Gate: Skip this phase entirely when ANY of:
> - `persistence` is `false` in Session Config
> - `reconcile.enabled` is `false` (default: `false` — opt-in; this is the silent no-op path for all repos that have not opted in)
> - `.orchestrator/metrics/learnings.jsonl` does not exist OR contains zero entries

After the auto-dialectic nudge decision is made (Phase 3.6.7), and when the reconcile engine is enabled, run the **reconciliation engine** to turn high-confidence learnings into conditional-rule proposals and present them to the operator via `AskUserQuestion` multiSelect. Approved proposals flow to `.claude/rules/` via `writeApprovedRules`. Rejected proposals are archived to `.orchestrator/reconcile.rejected.log`. The engine NEVER writes `.claude/rules/` itself — every write is operator-AUQ-gated (#693 FA2/FA3 brandmauer).

#### Coordinator-direct procedure

1. Read Session Config: `reconcile.enabled` (default `false`), `reconcile['rule-expiry-days']` (default `null` — falls back to per-type TTL in the engine), `reconcile['confidence-floor']` (default `0.5`). If `reconcile.enabled` is not `true`, log `reconcile: disabled (reconcile.enabled=false)` and skip all remaining steps.

2. Invoke `runReconcile` from `scripts/lib/reconcile/engine.mjs`:

   ```javascript
   import { runReconcile } from '${PLUGIN_ROOT}/scripts/lib/reconcile/engine.mjs';
   const { proposals, rejected, summary, error } = await runReconcile({
     repoRoot: process.cwd(),
     ruleExpiryDays: config.reconcile['rule-expiry-days'] ?? undefined,
     now: new Date(),
   });
   ```

   `runReconcile` NEVER throws. If `error` is present on the return value, treat it as a non-fatal failure (see Failure modes below). `proposals` is an array of `{ learningKey, slug, path, content, confidence, candidateId, status: 'proposed' }`; `rejected` carries the ineligible or already-proposed learnings with their audit reasons; `summary` carries `{ eligible, proposed, rejected, errors }` counts.

   > **Note:** `runReconcile` does NOT itself apply a confidence floor — the engine proposes every *eligible* learning and carries each one's `confidence` through. The operator's `reconcile['confidence-floor']` is the **delivery gate**, applied in the next step.

2b. **Apply the confidence floor (delivery gate).** Filter the engine's proposals by `reconcile['confidence-floor']` (default `0.5`) BEFORE the sidecar write and AUQ, so only sufficiently-confident proposals reach the operator:

   ```javascript
   const floor = config.reconcile['confidence-floor'] ?? 0.5;
   const surfaced = proposals.filter((p) => typeof p.confidence === 'number' && p.confidence >= floor);
   ```

   For the remainder of this phase, operate on `surfaced` wherever "proposals" is referenced below. Low-confidence proposals are neither surfaced nor written; they remain eligible in a future session if their confidence rises (the idempotency sidecar does not mark them processed because they were never approved/written).

3. If `surfaced.length === 0`: log `reconcile: 0 proposals above confidence floor (eligible=${summary.eligible}, rejected=${summary.rejected}, floor=${floor})` and continue. No AUQ, no sidecar write.

4. **Write the human-readable proposal sidecar** `.orchestrator/metrics/reconcile-pending.md` so the operator can review raw content outside the AUQ:

   ```
   # Reconciliation Rule Proposals — <ISO timestamp>
   Session: <sessionId>
   Engine: ${summary.eligible} eligible → ${summary.proposed} proposed, ${summary.rejected} rejected; ${surfaced.length} above confidence floor
   
   ---
   
   ## Proposal 1 of N — <slug> (conf=<confidence>)
   
   <content>
   
   ---
   
   ## Proposal 2 of N — ...
   ```

   Write failures are non-fatal — log WARN and continue to the AUQ.

5. **AUQ pagination logic**: partition proposals into FIFO batches of 4 inline:

   - Empty proposals → silent skip (gate step 3 already handles this).
   - 1–4 proposals → single multiSelect call with all proposals as options.
   - 5+ proposals → sequential multiSelect calls in batches of 4 (FIFO order; final batch may have < 4 proposals).

   ```javascript
   const BATCH_SIZE = 4;
   const batches = [];
   if (Array.isArray(surfaced) && surfaced.length > 0) {
     for (let i = 0; i < surfaced.length; i += BATCH_SIZE) {
       batches.push(surfaced.slice(i, i + BATCH_SIZE));
     }
   }
   ```

   Iterate `batches` and emit one `AskUserQuestion` per batch with `header: "Reconciliation — Confirm Rule Proposals (Batch N of M)"`. Option label format: `<slug-40> | conf=<confidence>`. Option description: first 80 chars of the rendered `content` (the rule prose preview). `multiSelect: true`.

6. After all batches are answered, partition proposals into `approved` (any option selected across all batches) and `rejected` (all unselected). Proposals the operator rejected join the engine's `rejected` array for archival.

7. Invoke `writeApprovedRules` from `scripts/lib/reconcile/writer.mjs`:

   ```javascript
   import { writeApprovedRules } from '${PLUGIN_ROOT}/scripts/lib/reconcile/writer.mjs';
   const writeResult = await writeApprovedRules({
     approved,
     rejected: [...rejected, ...operatorRejected],
     repoRoot: process.cwd(),
     sessionId,
   });
   // writeResult = { written: number, archived: number, errors: string[] }
   ```

   `writeApprovedRules` is lock-serialised (via `withFileLock` on `.orchestrator/rules.lock`) and writes each approved proposal to `.claude/rules/<slug>.md`. Rejected proposals (engine-rejected + operator-rejected) are archived to `.orchestrator/reconcile.rejected.log` with reason `user-declined` for operator-rejected and the engine's own audit reason for engine-rejected.

8. Log outcome for Phase 6 Final Report: `reconcile: ${surfaced.length} surfaced → ${approved.length} approved (written: ${writeResult.written}), ${operatorRejected.length} operator-declined${writeResult.errors.length > 0 ? `, ${writeResult.errors.length} write-errors (see sweep.log)` : ''}`.

#### Failure modes

- If `runReconcile` returns an `error` field (top-level exception caught internally): log `⚠ reconcile: engine error (${error}) — skipping`; do not block session close. No AUQ, no sidecar write.
- If the sidecar write (step 4) fails: log warning `⚠ reconcile: reconcile-pending.md write failed (${err})`; continue to the AUQ regardless.
- If `writeApprovedRules` reports per-rule errors in `writeResult.errors`: log each to `.orchestrator/metrics/sweep.log` and continue. Per-rule fault isolation — one failed write does not prevent the others.
- All failures are non-fatal. Session close is never blocked by reconcile errors — same posture as Phase 3.6.7.

#### Cross-references

- Issues: #696 (FA3 Advisory Delivery), #693 (Epic — Reconciliation Engine), #695 (FA2 engine), #697 (FA4 Guardrails — next phase)
- Modules: `scripts/lib/reconcile/engine.mjs` (`runReconcile`) · `scripts/lib/reconcile/writer.mjs` (`writeApprovedRules`) · `scripts/lib/config/reconcile.mjs` (`_parseReconcile`)
- Sibling modules: `scripts/lib/reconcile/{eligibility,emitter,renderer,idempotency}.mjs`
- Sibling phases: 3.6.3 Memory-Proposals Collection (#501), 3.6.5 Auto-Dream (#502), 3.6.6 Skill-Applied Judge (#645 L3), 3.6.7 Auto-Dialectic (#506)
- AUQ spec: `.claude/rules/ask-via-tool.md` AUQ-004 (coordinator-only; this AUQ runs in the coordinator, not in a subagent)

### 3.7 Write Session Metrics

Read `skills/session-end/session-metrics-write.md` for JSONL append, vault-mirror invocation, and behavior matrix.

> **Token Rollup (#644):** Before emitting the JSONL record (step 2 of session-metrics-write.md), step 1a calls `rollupSessionTokens({ parentSessionId })` from `scripts/lib/session-token-rollup.mjs` and merges three optional fields onto the in-memory record: `total_token_input`, `total_token_output`, and `subagents_with_tokens` (coverage count). Null totals mean "no token data captured" — not zero cost. The rollup is non-blocking: a missing `subagents.jsonl` or all-null session still writes cleanly with null/0 values.

### 3.7a Compute and Write Recommendations (Epic #271 Phase A)

> Gate: Only run if `persistence` is `true` in Session Config AND `<state-dir>/STATE.md` exists. Skip silently otherwise.

> **Ownership Reference:** See `skills/_shared/state-ownership.md`. session-end is the ONLY writer of the 5 Recommendation fields (`recommended-mode`, `top-priorities`, `carryover-ratio`, `completion-rate`, `rationale`). No other skill may write these keys.

> **Ordering:** Runs AFTER Phase 3.7 (sessions.jsonl is just-written — reads in-memory session metrics, NOT JSONL) and BEFORE Phase 3.4 `status: completed` setting. See the Phase 3.4 Runtime Ordering Note for rationale.

Calls `computeV0Recommendation({completionRate, carryoverRatio, carryoverIssues})` from in-memory session metrics and writes 5 fields to STATE.md frontmatter via `updateFrontmatterFields`. Inputs MUST come from in-memory metrics, NOT re-read from `sessions.jsonl`. On any exception writes `recommendation-compute-failed` to `sweep.log` and does NOT block Phase 3.4.

**See `phase-3-7a-recommendations.md` for full details.**

### 3.7b Durable-Commit Session Telemetry (#490 AC2)

> Gate: Always runs when persistence is enabled. Local execution is a no-op (`enabled: false`).

> **Ordering:** Runs AFTER Phase 3.7a (Recommendations written to STATE.md) and BEFORE Phase 3.4 (`status: completed`). See the Phase 3.4 Runtime Ordering Note canonical order.

Wraps the already-completed Phase 3.7 + 3.7a writes with `withDurableCommit` (from `scripts/lib/autopilot/durable-telemetry.mjs`) for the two session-end-owned files: `.orchestrator/metrics/sessions.jsonl` and `<state-dir>/STATE.md`. `enabled: false` keeps local closes a no-op (`{ok: true, skipped: true}`); the flag flips `true` only in cloud Routines execution so telemetry survives ephemeral-clone reclamation. `autopilot.jsonl` is NOT in scope here — `scripts/lib/autopilot/loop.mjs` owns its commit (#490 Wave-2).

**See `phase-3-7a-recommendations.md` § Phase 3.7b for the full `withDurableCommit` invocation.**

### Phase 3.7c: Vault Board → Closed (#674)

> Gate: Skip silently when `vault-integration.enabled` is not `true` in Session Config (the underlying helper also self-no-ops, so this is defense-in-depth, not the sole gate).

> **Ordering:** Runs AFTER Phase 3.7b (durable-commit) and BEFORE Phase 3.4 (`status: completed`) and Phase 3.8 (Session Lock Release). See the Phase 3.4 Runtime Ordering Note canonical order. Running before lock-release is deliberate — the session-lock lease still exists when the board is finalized, so the board's `in-progress → closed` transition is derived against a live lock rather than a phantom one. This mirrors the #490 durableCommit ordering discipline: persist/finalize the cross-repo status while the lease is still held, then release.

Transition THIS repo's live-status board row to `closed` so a cross-repo observer sees the session has ended. Invoke `mirrorBoard` from `scripts/lib/vault-status/board-writer.mjs` with an explicit `closed` status for the current repo:

```javascript
import { mirrorBoard } from 'scripts/lib/vault-status/board-writer.mjs';

const boardResult = await mirrorBoard({
  repoRoot: process.cwd(),
  explicitStatus: 'closed',        // force THIS repo's row to `closed`
});
// boardResult.action ∈ { 'written', 'skipped-noop', 'skipped-handwritten', 'skipped-vault-disabled', 'dry-run' }
```

> **Note (single-repo close path):** with `repos` omitted, `mirrorBoard` builds the repo descriptor itself as `[{ repoRoot, status: explicitStatus }]` — this is the supported single-repo shape, so `explicitStatus: 'closed'` lands on THIS repo's row. (When a caller DOES pass `repos`, each element must be a `{ repoRoot, repoName?, status? }` object, NOT a bare path string — bare strings are silently skipped by `collectRows`.) The board at `<vault-dir>/01-projects/_active-sessions.md` is generator-owned: `mirrorBoard` refuses to touch any file lacking the `session-orchestrator-active-sessions@1` marker, hard-refuses `_overview.md`, and is idempotent (a re-run after the row is already `closed` returns `skipped-noop`). Rows for repos NOT in this update are preserved verbatim by the idempotent merge.

**Non-blocking:** a `mirrorBoard` failure (any non-`written`/`skipped-*` outcome, thrown error, or unreachable vault) MUST NOT block the close. Log a single `WARNING: vault board → closed failed — <reason>; continuing close` line and proceed to Phase 3.4 / 3.8. The board is an observability convenience, not a close-out invariant.

## Phase 3.8: Session Lock Release (#330)

> Gate: Only run if `persistence` is `true` in Session Config. Skip silently otherwise.

After STATE.md is finalized with `status: completed` (Phase 3.4) and Recommendations are written (Phase 3.7a), release the distributed session-lock so the next session can acquire it cleanly:

```javascript
import { release } from 'scripts/lib/session-lock.mjs';
// sessionId = the session identifier established by session-start Phase 1.2 acquire()
//   and stored in .orchestrator/session.lock (session_id field); matches the
//   STATE.md frontmatter `session:` field written during Pre-Wave 1b initialization.
const result = release({ sessionId, repoRoot: process.cwd() });
// result.ok is always true unless a filesystem error occurred.
// result.deleted === true  → lock file removed successfully.
// result.deleted === false → lock was absent or belonged to a different session_id (silent-OK).
```

If `result.deleted === false`, log `info: session-lock not released — already absent or session_id mismatch (no action needed)` and continue. This is a non-error state.

If `result.ok === false` (rare filesystem error), log `⚠ session-lock: release failed — <result.reason>` and continue. Do NOT block the close for a lock-release failure — the TTL provides automatic expiry for the next session.

The lock is released here — AFTER all STATE.md writes are complete and BEFORE the commit is staged in Phase 4.1. This ordering ensures a clean handover: the lock file is absent from the working tree when the commit is assembled, so it is not accidentally staged.

## Phase 4: Commit & Push

### 4.1 Stage Changes
- **Stage files individually**: `git add <file>` — NEVER `git add .` or `git add -A`
- **Always stage these session artifacts** (if modified):
  - `.orchestrator/metrics/sessions.jsonl` (session summary from Phase 3.7)
  - `.orchestrator/metrics/learnings.jsonl` (learnings from Phase 3.6)
  - `<state-dir>/STATE.md` (session state, if persistence enabled)
  - Any files created or modified by wave agents
- Review staged changes: `git diff --cached` — verify every change is from THIS session
- If you see changes you did NOT make, ask the user (parallel session awareness)

### 4.2 Commit
Use Conventional Commits format:
```
type(scope): description

- [bullet points of what changed]
- Closes #IID1, #IID2 (if applicable)

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
```

For sessions with many changes, prefer ONE commit per logical unit (not one mega-commit).

### 4.3 Push
```bash
git push origin HEAD
```

### 4.4 GitHub Mirror (if configured in Session Config)
```bash
# Only attempt if 'mirror: github' is in Session Config AND remote exists
git remote get-url github 2>/dev/null && git push github HEAD 2>/dev/null || echo "GitHub mirror: not configured"
```

## Phase 4a: Auto-Promoted Worktree Cleanup (#575 P3.2)

> Skip if `persistence: false` in Session Config. Skip silently if the current worktree is NOT an Auto-promoted sibling (the common case).

After Phase 4 commit+push has durably persisted `sessions.jsonl` + `STATE.md` to origin, check whether the current session ran in an Auto-promoted sibling worktree (created via the P3.1 PROMOTION_OFFER path). If yes, apply Hybrid Cleanup-Pattern: clean → auto-remove, dirty → AUQ.

> **Ordering rationale (#490 durableCommit dependency):** Phase 4a runs AFTER Phase 4 commit+push, NOT before. Removing the promoted worktree before commit+push would lose the worktree's `STATE.md` before Phase 3.4 metrics writes (`sessions.jsonl`) are committed, violating the #490 durableCommit ordering invariant. Once Phase 4 has pushed all metrics + STATE.md to origin, the promoted worktree can be safely removed without data loss.

### Detection: is the current worktree an Auto-promoted sibling?

Auto-promoted sibling worktrees are created by `enterWorktree()` during the Phase 0.5 PROMOTION_OFFER path. Their path layout is `<basePath>/<repo-name>-<sessionId>/`. Detection uses `parseSessionId()` from `scripts/lib/session-id.mjs` (#572) — never custom regex.

> **Authoritative impl:** `scripts/lib/session-end/worktree-cleanup.mjs` — `detectAutoPromotedWorktree(repoRoot, sessionId, opts)`. Import and call; do NOT re-implement from this doc.
>
> Algorithm: parse `sessionId` via `parseSessionId()`; return `null` immediately for UUID-format sessions (never auto-promoted). Derive the MAIN checkout root from the first `worktree ` entry of `git worktree list --porcelain` (NOT `path.basename(repoRoot)` — the promoted worktree's basename IS the comparison target). If `repoRoot` resolves to the main checkout, return `null`. Otherwise compare `path.basename(repoRoot)` against `<main-repo-name>-<sessionId>`; on match return `{ wtPath, sessionId, branch }`, else `null`. All git invocation is via the injection-safe `opts.execFileFn` (default `execFileSync` with an args array — #577 HARDEN-001).

### Clean-check

A worktree is clean iff ALL three conditions hold:

1. **No uncommitted changes**: `git status --porcelain` is empty
2. **No untracked files**: implicit in #1 (porcelain includes `??` entries)
3. **No unpushed commits**: `git status --short --branch` does NOT contain `ahead` indicator

> **Authoritative impl:** `scripts/lib/session-end/worktree-cleanup.mjs` — `isWorktreeClean(wtPath, opts)`. Import and call; do NOT re-implement from this doc.
>
> Algorithm: run `git status --porcelain`; if non-empty → dirty (`false`). Else run `git status --short --branch`; if it matches `/\bahead\b/` → unpushed (`false`). Otherwise `true`. On ANY git error → `false` (conservative PSA-003 default: never auto-remove a worktree we could not verify). Git invocation is via the injection-safe `opts.execFileFn` (default `execFileSync` with an args array — #577 HARDEN-001).

### Clean path: auto-remove + WARN (PRD §3 P3 Gherkin row 2)

When detection returns a worktree object AND `isWorktreeClean()` returns `true`, auto-remove via `git worktree remove` (NO `--force`) and log a WARN line. The main checkout's git dir (`repoMainRoot`) is derived via the first entry of `git worktree list --porcelain`.

> **Authoritative impl:** import `detectAutoPromotedWorktree` + `isWorktreeClean` from `scripts/lib/session-end/worktree-cleanup.mjs`. All git invocation MUST go through the injection-safe arg-array form (`execFileSync('git', ['-C', dir, …])`, #577 HARDEN-001) — never the legacy `execSync(\`git -C ${var} …\`)` template-literal shell form.

```js
import { execFileSync } from 'node:child_process';
import { detectAutoPromotedWorktree, isWorktreeClean } from '${PLUGIN_ROOT}/scripts/lib/session-end/worktree-cleanup.mjs';

const promoted = detectAutoPromotedWorktree(process.cwd(), sessionId);
if (!promoted) {
  // Not auto-promoted — skip Phase 4a entirely. Continue to Phase 5.
} else {
  // Derive main checkout root from first worktree-list entry (arg-array, no shell)
  const wtList = execFileSync('git', ['-C', promoted.wtPath, 'worktree', 'list', '--porcelain'], { encoding: 'utf8' });
  const mainLine = wtList.split('\n').find((l) => l.startsWith('worktree '));
  const repoMainRoot = mainLine ? mainLine.slice('worktree '.length).trim() : null;

  if (isWorktreeClean(promoted.wtPath)) {
    // Clean path: PRD §3 P3 Gherkin row 2 — auto-remove
    console.warn(`session-end Phase 4a: auto-promoted worktree ${promoted.wtPath} is clean — removing via 'git worktree remove'`);
    execFileSync('git', ['-C', repoMainRoot, 'worktree', 'remove', promoted.wtPath], { encoding: 'utf8' });
  } else {
    // Dirty path: PRD §3 P3 Gherkin row 3 — AUQ before any destructive action
    // [AUQ block — see Dirty path subsection below]
  }
}
```

### Dirty path: AUQ before destructive action (PRD §3 P3 Gherkin row 3)

When the worktree is dirty (uncommitted, untracked, OR unpushed), render this AUQ via the coordinator's `AskUserQuestion` tool. The AUQ is coordinator-only — per `.claude/rules/ask-via-tool.md` AUQ-004, dispatched agents cannot call AUQ. Calling `git worktree remove --force` without explicit operator confirmation would violate PSA-003 (destructive action safeguards) — the dirty state may contain another session's work-in-progress or unmerged commits.

```js
AskUserQuestion({
  questions: [{
    question: `Auto-promoted worktree at ${promoted.wtPath} has uncommitted/untracked/unpushed changes. How should I proceed?`,
    header: "Worktree-Cleanup",
    multiSelect: false,
    options: [
      { label: "Behalten (Recommended)", description: "Keep the worktree as-is. No cleanup. Review and remove manually later." },
      { label: "Löschen", description: "I confirm the changes are handled or expendable. Run 'git worktree remove --force' on the worktree." },
      { label: "Manuell", description: "Exit /close. I will inspect the worktree before re-running /close." },
    ],
  }],
});
```

**Codex CLI / Cursor IDE fallback** (numbered Markdown list):

```
Worktree cleanup options:
1. **Behalten (Recommended)** — Keep the worktree as-is. No cleanup. Review and remove manually later.
2. **Löschen** — I confirm the changes are handled or expendable. Run 'git worktree remove --force'.
3. **Manuell** — Exit /close. I will inspect the worktree before re-running /close.
Reply with the number of your choice.
```

**On user choice:**

- **Behalten** → log `session-end Phase 4a: auto-promoted worktree retained (dirty); operator chose Behalten`. Continue to Phase 5.
- **Löschen** → `execFileSync('git', ['-C', repoMainRoot, 'worktree', 'remove', '--force', promoted.wtPath])` (arg-array, no shell — #577 HARDEN-001). Log WARN: `session-end Phase 4a: auto-promoted worktree force-removed by user choice`. Continue to Phase 5.
- **Manuell** → exit `/close` cleanly. Print: `session-end aborted at Phase 4a by user choice. Re-run /close after handling the worktree manually.`

### Cross-references

- **PRD:** `docs/prd/2026-05-26-parallel-aware-sessions.md` §3 P3 Gherkin rows 2-3 + §3.A P3 EARS event-driven clauses
- **PSA-003:** `.claude/rules/parallel-sessions.md` — destructive action safeguards (`git worktree remove --force` requires explicit user authorization)
- **#490 durableCommit dependency:** Phase 4a runs AFTER Phase 4 commit+push to guarantee `sessions.jsonl` + `STATE.md` are persisted to origin BEFORE worktree removal
- **Detection helper:** `parseSessionId()` from `scripts/lib/session-id.mjs` (#572)
- **AUQ rule:** `.claude/rules/ask-via-tool.md` AUQ-004 — coordinator-only invocation
- **Companion phases:** P3.1 PROMOTION_OFFER (`enterWorktree()` in `parallel-aware-auq.md`) creates the worktree; this phase removes it.

## Phase 5: Issue Cleanup

> **VCS Reference:** Use CLI commands per the "Common CLI Commands" section of the gitlab-ops skill.

1. **Close resolved issues**: Before closing each issue, strip `status:*` workflow labels using `stripStatusLabels` from `scripts/lib/issue-close-strip-labels.mjs` (#308). A closed issue carrying `status:in-progress` or `status:ready` skews dashboard filters and discovery heuristics. Then close and add a note using the issue close and note commands per the "Common CLI Commands" section of the gitlab-ops skill. Note: some VCS platforms require separate note and close commands.

   ```js
   import { stripStatusLabels } from '${PLUGIN_ROOT}/scripts/lib/issue-close-strip-labels.mjs';

   // For each resolved issue IID:
   const { stripped, error } = await stripStatusLabels({ issueId: iid, vcs: '<from Session Config>' });
   if (error) {
     console.warn(`⚠ label strip failed for #${iid}: ${error} — proceeding with close`);
   } else if (stripped.length) {
     console.log(`Stripped ${stripped.join(', ')} from #${iid}`);
   }
   // then: glab issue close <iid> / gh issue close <iid>
   ```

   The call is idempotent: if the issue has no `status:*` labels, no update CLI call is made. Failures from `stripStatusLabels` are non-fatal — log and proceed with close.

2. **Update in-progress issues**: ensure labels reflect actual state using the issue update command
3. **Create carryover issues**: for partially-done work (from Phase 1.2), use the issue create command with appropriate labels

#### Discovery Issue Creation (if discovery ran in Phase 1.5)

For each finding with severity `critical` or `high` from Phase 1.5:
1. Create a VCS issue using the detected platform CLI:
   - Title: `[Discovery] <description>` (truncated to 70 chars)
   - Body: `**Probe:** <probe>\n**File:** <file>:<line>\n**Severity:** <severity>\n**Confidence:** <confidence>%\n**Recommendation:** <recommendation>`
   - Labels: `type:discovery`, `priority:<severity>` (critical→critical, high→high)
2. Log each created issue ID for the Final Report
3. Update `discovery_stats.issues_created` count

4. **Create gap issues for HIGH+/blocking newly-discovered problems only** — MED/LOW review findings are recorded in the Final Report, not filed as issues (#617; see the Phase 1.8 severity-disposition table). This mirrors the Phase 5 "Discovery Issue Creation" gate (critical/high only).
5. **Update milestones**: if milestone progress changed

## Phase 6: Final Report

Present to the user:

```
## Session Summary

### Completed
- [x] Issue #N: [description] — [evidence: tests passing, files changed]
- [x] Issue #M: [description]

### Carried Over
- [ ] Issue #P: [what's left] — new issue #Q created
- [ ] [description] — blocked by [reason]

### New Issues Created
- #R: [title] (priority: [X], status: ready)
- #S: [title] (priority: [X], status: ready)

### Unresolved Review Findings (MED/LOW — recorded, not ticketed) [#617]
- [MED] <finding> — <file:line> — <why deferred / fold decision>
- [LOW] <finding> — <file:line>

### Metrics
- Duration: [total wall-clock time]
- Waves: [N completed]
- Agents: [total dispatched] ([X complete, Y partial, Z failed])
- Files changed: [N]
- Per-wave breakdown:
  - Wave 1 (Discovery): [duration] — [N agents] — [K files]
  - Wave 2 (Impl-Core): [duration] — [N agents] — [K files]
  - ...
- Tests: [passing/total]
- TypeScript: 0 errors
- Commits: [N] pushed to [branch]
- Mirror: [synced/skipped]
- Docs Health: Vault staleness — [render one of the three cases below based on Phase 2.3 result]
  - Findings present (warn mode): `[N stale projects, M stale narratives] (mode=warn). See .orchestrator/metrics/vault-staleness.jsonl.`
  - Skipped (disabled or mode=off): `skipped (disabled | mode=off).`
  - Clean run: `clean (mode=<mode>).`
- Custom Phases: [render based on Phase 2.5 result — omit the line entirely if `custom-phases` was absent/empty]
  - Per phase: `<name>: <pass|FAIL> (exit <code>, mode=<mode>)[ — review: <path>]`
  - None ran (all filtered out by `when`): `none applicable for session-type=<type>.`
- Enforcement: [N violations blocked / M warnings] (or "N/A" if enforcement off)
- Circuit breaker: [N agents hit limits, M spirals detected] (or "none")
- Metrics written to: `.orchestrator/metrics/sessions.jsonl`
- Learnings: [N] new, [M] confirmed, [K] contradicted/expired — written to `.orchestrator/metrics/learnings.jsonl`

### Next Session Recommendations
- Priority: [what should be tackled next]
- Type: [housekeeping/feature/deep recommended]
- Notes: [any context for next session]
```

> **Documentation Coverage anchor:** If Phase 3.2 ran and produced task verification results (i.e. `docs-orchestrator.enabled: true` and `docs-tasks` were found), the results appear here as a `### Documentation Coverage (docs-orchestrator)` subsection emitted by Phase 3.2 Step 7. The content is written dynamically — it is not pre-populated in this template. When `docs-orchestrator.enabled` is `false` or `docs-tasks` were absent, this subsection is omitted entirely.

## Sub-File Reference

| File | Purpose |
|------|---------|
| `plan-verification.md` | Phase 1 plan verification and metrics collection |
| `verification-checklist.md` | Phase 2 quality gate checklist and checks |
| `discovery-scan.md` | Phase 1.5 embedded discovery dispatch and findings triage |
| `metrics-collection.md` | Phase 1.7 JSONL schema and conditional field rules |
| `vault-operations.md` | Phase 2.1 validator bash contract and reporting matrix |
| `drift-operations.md` | Phase 2.2 drift-checker bash contract and reporting matrix |
| `phase-3-2-docs-verification.md` | Phase 3.2 full procedural body — docs-tasks load, SESSION_START_REF, per-task loop, mode-gated report, Documentation Coverage block |
| `learning-patterns.md` | Phases 3.5a + 3.6 extraction heuristics, confidence updates, passive decay, and JSONL write procedure |
| (inline) Phase 3.6.3 | Memory-Proposals Collection — `collectProposals` + AUQ multiSelect + `writeApproved` + `clearProposalsJsonl` |
| (inline) Phase 3.6.5 | Auto-Dream nudge — `shouldDispatchAutoDream` + manual-cadence nudge to run /memory-cleanup --dry-run next session (no live dispatch — #614) |
| (inline) Phase 3.6.6 | Skill-Applied Judge (#645 L3) — default OFF; when `skill-evolution.judge: true`, `runSkillJudge` does a LIVE read-only haiku dispatch returning JSON; the COORDINATOR writes advisory judgments to `.orchestrator/metrics/skill-judgments.jsonl` (#614-safe: agent returns, coordinator writes) |
| (inline) Phase 3.6.7 | Auto-Dialectic nudge — `shouldDispatchAutoDialectic` + manual-cadence nudge to run /evolve --dialectic next session + advances `.orchestrator/dialectic-last-run` (no live dispatch — #614) |
| (inline) Phase 3.6.8 | Reconciliation Rule Proposals (#696 FA3) — `runReconcile` + AUQ multiSelect batch-of-4 + `writeApprovedRules`; gated on `reconcile.enabled` (default `false`), silent no-op when disabled; engine NEVER writes `.claude/rules/` directly — every write is operator-AUQ-gated |
| `session-metrics-write.md` | Phase 3.7 JSONL append, vault-mirror invocation, durable narrative mirror (`mirrorNarrative`, #675), and behavior matrix |
| `phase-3-7a-recommendations.md` | Phase 3.7a full procedural body — computeV0Recommendation call, STATE.md field write, data source guarantee, error mode |
| `phase-3-7a-recommendations.md` § 3.7b | Phase 3.7b full procedural body — `withDurableCommit` invocation for `sessions.jsonl` + `STATE.md` (#490 AC2), `enabled:false` local no-op, autopilot.jsonl exclusion note |
| (inline) Phase 3.7c | Vault Board → Closed (#674) — `mirrorBoard({ explicitStatus: 'closed' })` transitions this repo's board row to `closed`; gated on `vault-integration.enabled`, generator-marked + idempotent, non-blocking, ordered after 3.7b and before 3.4/3.8 |
| (inline) Phase 3.8 | Session Lock Release — `release()` call, silent-OK on mismatch/absent, non-fatal on fs-error, ordering note (after STATE.md writes, before Phase 4 commit staging) |

## Anti-Patterns

- **DO NOT** commit before running quality gates — a "clean commit" with TypeScript errors is not clean
- **DO NOT** mark issues as closed without verifying the implementation actually addresses them
- **DO NOT** skip creating tracking issues for unfinished work — "I'll remember for next session" always fails
- **DO NOT** use `git add .` or `git add -A` — parallel sessions may have uncommitted work in the tree
- **DO NOT** push to mirrors before verifying origin push succeeded — broken state propagates

## Critical Rules

- **NEVER claim work is done without running verification** — evidence before assertions
- **NEVER commit with TypeScript errors** — 0 errors is non-negotiable
- **NEVER use `git add .`** — stage files individually to avoid capturing parallel session work
- **NEVER skip issue updates** — VCS must reflect reality after every session
- **ALWAYS create issues for unfinished PLANNED work** — SPIRAL/FAILED agent carryover and partially-done plan items (Phase 1.2 / 1.6) ALWAYS get a ticket; nothing planned-but-unfinished is "remembered" without one.
- **DO NOT auto-file MED/LOW review findings as issues** — newly-surfaced reviewer findings (Phase 1.8 / W4 panel) at MED or LOW severity are folded in-session or recorded in the Final Report under "Unresolved Review Findings". Only HIGH+/blocking review findings get an issue. (Issue #617 — stops the self-referential low-priority backlog.)
- **ALWAYS push to origin** — local-only work is lost work
- **ALWAYS mirror to GitHub** if configured — keep mirrors in sync
- **ALWAYS review `git diff --cached`** before committing — verify only YOUR changes are staged
