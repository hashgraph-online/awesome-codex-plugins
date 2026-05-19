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

> **Platform Note:** State files (STATE.md, wave-scope.json) live in the platform's native directory: `.claude/` (Claude Code), `.codex/` (Codex CLI), or `.cursor/` (Cursor IDE). All references to `.claude/` below should use the platform's state directory. Shared metrics live in `.orchestrator/metrics/`. See `skills/_shared/platform-tools.md`.

> **Project-instruction file:** `CLAUDE.md` and `AGENTS.md` (Codex CLI) are transparent aliases — see [skills/_shared/instruction-file-resolution.md](../_shared/instruction-file-resolution.md). All references to `CLAUDE.md` in this skill resolve via that precedence rule.

## Phase 0: Bootstrap Gate

Read `skills/_shared/bootstrap-gate.md` and execute the gate check. If the gate is CLOSED, invoke `skills/bootstrap/SKILL.md` and wait for completion before proceeding. If the gate is OPEN, continue to Phase 1.

<HARD-GATE>
Do NOT proceed past Phase 0 if GATE_CLOSED. There is no bypass. Refer to `skills/_shared/bootstrap-gate.md` for the full HARD-GATE constraints.
</HARD-GATE>

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
   - **FIX REQUIRED** — address each listed item before proceeding. For quick fixes (<2 min each), fix inline. For larger items, create carryover issues (same as Phase 1.2) and note them as unresolved review findings in the Final Report

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

## Phase 3: Documentation Updates

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

> **Runtime Ordering Note (Epic #271 Phase A):** Phase 3.4's `status: completed` write executes LAST in Phase 3, AFTER Phase 3.7 (sessions.jsonl) and Phase 3.7a (Compute and Write Recommendations). The ordinal position here (3.4) is kept for historical compatibility; the canonical runtime order is `3.1 → 3.2 → 3.3 → 3.4a → 3.5 → 3.5a → 3.7 → 3.7a → 3.4`. Rationale: Phase 3.7a reads in-memory session metrics and writes the 5 Recommendation fields via `updateFrontmatterFields`; that write must complete BEFORE the STATE.md frontmatter is finalized with `status: completed` so the Recommendation fields are visible to the next session-start while STATE.md is still `status: active`. Crash-resilience: if `/close` aborts between 3.7a and 3.4, STATE.md carries `status: active` + Recommendations; session-start Phase 1.5 offers resume (and the banner renders). If the reverse ordering were used (status: completed first), a crash would leave `status: completed` without Recommendations — the Reader would silently no-op the banner, losing the handoff.

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

### 3.7 Write Session Metrics

Read `skills/session-end/session-metrics-write.md` for JSONL append, vault-mirror invocation, and behavior matrix.

### 3.7a Compute and Write Recommendations (Epic #271 Phase A)

> Gate: Only run if `persistence` is `true` in Session Config AND `<state-dir>/STATE.md` exists. Skip silently otherwise.

> **Ownership Reference:** See `skills/_shared/state-ownership.md`. session-end is the ONLY writer of the 5 Recommendation fields (`recommended-mode`, `top-priorities`, `carryover-ratio`, `completion-rate`, `rationale`). No other skill may write these keys.

> **Ordering:** Runs AFTER Phase 3.7 (sessions.jsonl is just-written — reads in-memory session metrics, NOT JSONL) and BEFORE Phase 3.4 `status: completed` setting. See the Phase 3.4 Runtime Ordering Note for rationale.

Calls `computeV0Recommendation({completionRate, carryoverRatio, carryoverIssues})` from in-memory session metrics and writes 5 fields to STATE.md frontmatter via `updateFrontmatterFields`. Inputs MUST come from in-memory metrics, NOT re-read from `sessions.jsonl`. On any exception writes `recommendation-compute-failed` to `sweep.log` and does NOT block Phase 3.4.

**See `phase-3-7a-recommendations.md` for full details.**

## Phase 3.8: Session Lock Release (#330)

> Gate: Only run if `persistence` is `true` in Session Config. Skip silently otherwise.

After STATE.md is finalized with `status: completed` (Phase 3.4) and Recommendations are written (Phase 3.7a), release the distributed session-lock so the next session can acquire it cleanly:

```javascript
import { release } from 'scripts/lib/session-lock.mjs';
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

4. **Create gap issues**: for newly-discovered problems
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
| `session-metrics-write.md` | Phase 3.7 JSONL append, vault-mirror invocation, and behavior matrix |
| `phase-3-7a-recommendations.md` | Phase 3.7a full procedural body — computeV0Recommendation call, STATE.md field write, data source guarantee, error mode |
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
- **ALWAYS create issues for unfinished work** — nothing should be "remembered" without a ticket
- **ALWAYS push to origin** — local-only work is lost work
- **ALWAYS mirror to GitHub** if configured — keep mirrors in sync
- **ALWAYS review `git diff --cached`** before committing — verify only YOUR changes are staged
