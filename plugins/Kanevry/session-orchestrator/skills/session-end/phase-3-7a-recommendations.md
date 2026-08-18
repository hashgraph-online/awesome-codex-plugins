# Phase 3.7a: Compute and Write Recommendations (Epic #271 Phase A)

> Gate: Only run if `persistence` is `true` in Session Config AND `<state-dir>/STATE.md` exists. Skip silently otherwise.

> **Ownership Reference:** See `skills/_shared/state-ownership.md`. session-end is the ONLY writer of the 5 Recommendation fields (`recommended-mode`, `top-priorities`, `carryover-ratio`, `completion-rate`, `rationale`). No other skill may write these keys.

> **Ordering:** Runs AFTER Phase 3.7 (sessions.jsonl is just-written — reads in-memory session metrics, NOT JSONL) and BEFORE Phase 3.4 `status: completed` setting. See the Phase 3.4 Runtime Ordering Note for rationale.

Compute the v0 recommendation from in-memory session metrics and additively write 5 fields to STATE.md frontmatter:

```bash
node --input-type=module -e "
import {appendFileSync, mkdirSync} from 'node:fs';
import {updateFrontmatterFieldsOnDisk} from '${PLUGIN_ROOT}/scripts/lib/state-md.mjs';
import {computeV0Recommendation} from '${PLUGIN_ROOT}/scripts/lib/recommendations-v0.mjs';

const SWEEP_LOG = '.orchestrator/metrics/sweep.log';

try {
  // In-memory session metrics — pulled from the session's running state,
  // NOT re-read from sessions.jsonl (which was just-written in Phase 3.7).
  const completionRate = <number from session metrics: completed_issues / planned_issues>;
  const carryoverRatio = <number: carryover_count / planned_issues (0 when planned=0)>;
  const carryoverIssues = [<priority-sorted carryover issue IIDs, critical/high first, FIFO tiebreak>];

  const rec = computeV0Recommendation({completionRate, carryoverRatio, carryoverIssues});

  const fields = {
    'recommended-mode': rec.mode,
    'top-priorities': rec.priorities,
    'carryover-ratio': Number(carryoverRatio.toFixed(2)),
    'completion-rate': Number(completionRate.toFixed(2)),
    'rationale': rec.rationale,
  };

  await updateFrontmatterFieldsOnDisk(undefined, fields);
  console.log('Recommendations written: ' + rec.mode + ' (' + rec.rationale + ')');
} catch (err) {
  // AC3: defensive — exception must NOT block Phase 3.4 status: completed.
  mkdirSync('.orchestrator/metrics', {recursive: true});
  const evt = {
    timestamp: new Date().toISOString(),
    event: 'recommendation-compute-failed',
    error: String(err && err.message ? err.message : err),
  };
  appendFileSync(SWEEP_LOG, JSON.stringify(evt) + '\n');
  console.error('⚠ Phase 3.7a: recommendation compute failed — fields omitted, sweep.log entry written. Continuing.');
}
"
```

**Data source guarantee:** The three inputs (`completionRate`, `carryoverRatio`, `carryoverIssues`) MUST come from the in-memory session metrics object built in Phase 1.7, NOT from a re-read of `.orchestrator/metrics/sessions.jsonl`. Reading the just-written JSONL would introduce a circular dependency and risk reading a truncated line if Phase 3.7's `appendJsonl` was mid-flush.

**Field precision:**
- `carryover-ratio` and `completion-rate` are rounded to 2 decimal places.
- `top-priorities` contains 0–5 integer issue IIDs, already priority-sorted by the Phase 1.1 carryover loop.
- `rationale` is a ≤ 120-char single-line string (v0 produces ≤ 40 chars).

**Error mode (AC3):** On any exception from `computeV0Recommendation` or the file I/O, the catch block writes a `recommendation-compute-failed` event to `.orchestrator/metrics/sweep.log` and returns without touching STATE.md. Phase 3.4 then proceeds as normal, setting `status: completed` without Recommendation fields. The Reader (session-start Phase 1.5) handles the absent-fields case via graceful-no-banner fallback.

---

## Phase 3.7b: Durable-Commit Session Telemetry (#490 AC2)

> **Ordering:** Runs AFTER Phase 3.7a (Recommendation fields just-written to STATE.md) and BEFORE Phase 3.4 (`status: completed`). The canonical runtime order is `… → 3.6.7 → 3.6.8 → 3.7 → 3.7a → 3.7b → 3.7c → 3.7d → 3.4`. Both session-end-owned files (`sessions.jsonl` from Phase 3.7, `STATE.md` from Phase 3.7a) have already been written to disk; this step only declares them as the durable-commit set.

> **Ownership:** session-end commits ONLY the two files it owns — `.orchestrator/metrics/sessions.jsonl` and `<state-dir>/STATE.md`. `.orchestrator/metrics/autopilot.jsonl` is NOT session-end's responsibility: `scripts/lib/autopilot/loop.mjs` commits that file in the autopilot loop (the core `loop.mjs` wiring shipped in #490 Wave-2). Do not add autopilot.jsonl to the files array here.

Wrap the (already-completed) telemetry writes with `withDurableCommit` so the two session-end-owned files survive ephemeral-clone reclamation when `/close` runs inside a cloud Routines execution context. Local execution: `enabled: false` makes this a no-op (returns `{ok: true, skipped: true}` without touching git). The flag flips to `true` only in cloud Routines execution.

```javascript
import { withDurableCommit } from '${PLUGIN_ROOT}/scripts/lib/autopilot/durable-telemetry.mjs';

await withDurableCommit(
  () => {}, // writes already done by Phase 3.7 (sessions.jsonl) + Phase 3.7a (STATE.md)
  {
    sessionId: SESSION_ID,
    files: ['.orchestrator/metrics/sessions.jsonl', '<state-dir>/STATE.md'],
    enabled: false, // local no-op; cloud Routines execution flips this true
  }
);
```

- Use the platform-resolved `<state-dir>/STATE.md` path (e.g. `~/.claude/STATE.md` on Claude Code) — NOT a hardcoded `.claude/STATE.md`.
- The `files` array is staged individually by `durableCommit` (PSA-004: never `git add .`/`-A`); the existing `SAFE_BRANCH_RE` branch-name allowlist + cwd-confinement guards in `durable-telemetry.mjs` apply unchanged.
- `enabled: false` short-circuits before any git command runs, so the local-execution path performs zero VCS mutation — Phase 4 (`git add` + commit) remains the single staging point for local closes.
