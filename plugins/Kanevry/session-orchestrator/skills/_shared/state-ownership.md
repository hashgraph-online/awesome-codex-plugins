# STATE.md Ownership Contract

> Defines who can read and write `<state-dir>/STATE.md` and under what conditions.
> Referenced by: wave-executor, session-end, session-start, evolve.

## Schema

```yaml
---
schema-version: 1
session-type: feature|deep|housekeeping|none
branch: <current branch>
issues: [<issue numbers>]
started_at: <ISO 8601 with timezone>
status: active|paused|completed|idle
current-wave: <N>
total-waves: <N>
# Optional fields (schema-version 1, additive for backward-compat):
updated: <ISO 8601 UTC>      # last write timestamp, touched by any writer
session: <session-id>        # <branch>-<YYYY-MM-DD>-<mode>-<n> (semantic, since #573); legacy UUID-v4 also accepted by parseSessionId
session-start-ref: <sha>     # git ref at session start
---
```

### Required vs. optional fields

- `schema-version`, `session-type`, `branch`, `issues`, `started_at`, `status`, `current-wave`, `total-waves` — **required** in every session-owned STATE.md.
- `updated`, `session`, `session-start-ref` — **optional**. Added by #184. STATE.md files without these fields remain valid and should be treated as `updated: null` / `session: null`. Writers SHOULD populate these fields but readers MUST tolerate their absence. The `session` field's value format is `<branch>-<YYYY-MM-DD>-<mode>-<n>` since #573 (Epic #568 Parallel-Aware Sessions P2.2); pre-#573 files may contain a UUID-v4 — both formats are read via `parseSessionId()` from `scripts/lib/session-id.mjs` per PRD §3 P2 row 3 (backward-compat).

The `session-type: none` + `status: idle` combination is used only for bootstrap-scaffolded placeholder files (no active session).

### Body Sections

| Section | Purpose | Updated by |
|---------|---------|------------|
| `## Current Wave` | Next wave to execute | wave-executor (post-wave) |
| `## Wave History` | Completed wave records | wave-executor (post-wave) |
| `## Deviations` | Plan adaptation log | wave-executor (step 3) |
| `## What Not To Retry` | Failed/abandoned approaches not to repeat (#623) | session-end (Phase 1.6) |
| `## Open Questions` | Unresolved user-facing questions (agent → gate → next session) | wave-executor (inter-wave) + session-end (marks answered) |

Wave History lines MAY include a `→ issue #NNN` suffix (or `→ existing #NNN` when a duplicate was detected) for SPIRAL/FAILED agents, linking to the auto-created carryover issue (#261). This is optional and backward-compatible; readers that do not recognize the notation can skip it. Session-end Phase 1.6 uses the presence of this suffix to decide whether to retro-file a carryover as a fallback safety net.

### `## What Not To Retry` (cross-session continuity slot, #623)

A log of failed or abandoned approaches that future sessions should NOT re-attempt. Each entry has the shape `{approach, why_failed, session_id, date}` and renders as:

```markdown
## What Not To Retry

- **<approach>** (<session_id>, <date>)
  - why: <why_failed>
```

- **Writer:** session-end Phase 1.6 — for every SPIRAL/FAILED agent it appends one entry via `appendWhatNotToRetryOnDisk(repoRoot, entry)`; the coordinator MAY also add a free-text entry through the same helper.
- **Reader:** session-start Phase 6.5.1 — surfaces the section as a forced-read block wrapped in the HISTORICAL guard banner (`scripts/lib/historical-guard.mjs`). It is a READER only and never mutates the slot.
- **Cap:** at most `MAX_WHAT_NOT_TO_RETRY` (10) entries, pruned FIFO (oldest dropped) on each append — a simple last-N trim, NOT a per-entry success-clear.
- **Idle-Reset preservation (load-bearing):** **`## What Not To Retry` SURVIVES the completed-branch Idle Reset** — unlike per-session `## Deviations` (which is emptied) and `## Wave History` (which is demoted into `## Previous Session`). It is a cross-session continuity record, so session-start's Idle Reset MUST NOT clear, demote, or drop it.

Helpers: `appendWhatNotToRetry` (pure), `readWhatNotToRetry` (pure), `appendWhatNotToRetryOnDisk` (lock-guarded write) — all exported from `scripts/lib/state-md.mjs`.

### `## Open Questions` (Close Handover-Alignment-Gate, PRD 2026-07-07)

A log of unresolved, user-facing questions surfaced by wave agents during a session, collected at inter-wave checkpoints, and (optionally) marked answered by session-end or a later Handover-Alignment-Gate run. Each entry has the shape `{question, source, priority, answered, answer?}` and renders as:

```markdown
## Open Questions

- [ ] <question> (source: <source>, prio: <high|medium|low>)
- [x] <question> (source: <source>, prio: <p>) → Antwort: <answer>
```

- **Writer:** wave-executor — at each inter-wave checkpoint, collects deduped `OPEN-QUESTIONS:` lines from the wave's agent reports and appends one entry per question via `appendOpenQuestionOnDisk(repoRoot, entry)`. session-end MAY flip an entry to answered via `markOpenQuestionAnsweredOnDisk(repoRoot, question, answer)` when the gate resolves it during close.
- **Reader:** the Handover-Alignment-Gate (session-end / session-start) reads unanswered entries via `readOpenQuestions` to decide what to surface to the operator across the session boundary.
- **Cap:** at most `MAX_OPEN_QUESTIONS_STORED` (20) entries, pruned FIFO (oldest dropped) on each append — a storage cap, distinct from the gate's own `max-open-questions` config (which caps how many questions are ASKED per gate run, not how many are stored).
- **Idle-Reset preservation (load-bearing):** **`## Open Questions` SURVIVES the completed-branch Idle Reset** — unlike per-session `## Deviations` (which is emptied) and `## Wave History` (which is demoted into `## Previous Session`). Unanswered questions are exactly the ones that need to reach the NEXT session's operator, so session-start's Idle Reset MUST NOT clear, demote, or drop it — mirroring `## What Not To Retry` above (#623).

Helpers: `readOpenQuestions` (pure), `appendOpenQuestion` (pure), `markOpenQuestionAnswered` (pure), `appendOpenQuestionOnDisk` (lock-guarded write), `markOpenQuestionAnsweredOnDisk` (lock-guarded write) — all exported from `scripts/lib/state-md.mjs`.

## Ownership Model

| Skill | Access | Operations |
|-------|--------|------------|
| **wave-executor** | Read + Write (owner) | Creates STATE.md (Pre-Wave 1b), updates after each wave (current-wave, Wave History, Deviations); appends deduped `## Open Questions` at inter-wave checkpoints via `appendOpenQuestionOnDisk` (see `wave-loop.md` § 3e + Post-Wave step 6). |
| **session-end** | Read + Status-only write | Reads for metrics extraction (Phase 1.7), sets `status: completed` (Phase 3.4). Exception: only fields modified are `status` in frontmatter and marking entries answered in `## Open Questions` via `markOpenQuestionAnsweredOnDisk` (Close Handover-Alignment-Gate). |
| **session-start** | Read + conditional reset | Reads for continuity checks (Phase 1.5): inspects `status` field to detect crashed/paused sessions. Surfaces `## What Not To Retry` as a forced-read HISTORICAL block (Phase 6.5.1). May reset STATE.md to idle at the boundary between a completed session and a new session — only when prior `status: completed`. The reset clears `current-wave` (→ 0), sets `status: idle`, demotes `## Wave History` into `## Previous Session`, and empties `## Deviations` — but PRESERVES `## What Not To Retry` (cross-session continuity, #623) and `## Open Questions` (Close Handover-Alignment-Gate, PRD 2026-07-07). Never resets on `active` or `paused` (those paths are user-interactive). |
| **evolve** | Read-only | Reads `## Deviations` section for deviation pattern extraction (Step 2.2, pattern 5) |

## Guards

### Branch Validation

Before reading STATE.md, verify the `branch` field matches the current branch:

```bash
STATE_BRANCH=$(grep '^branch:' <state-dir>/STATE.md | sed 's/branch: *//')
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "$STATE_BRANCH" != "$CURRENT_BRANCH" ]]; then
  # STATE.md belongs to a different branch — treat as stale
  echo "⚠ STATE.md is from branch '$STATE_BRANCH' but current branch is '$CURRENT_BRANCH'. Ignoring."
fi
```

### Schema Version

The `schema-version` field enables future migration. Current version: `1`. If a skill reads a STATE.md with an unrecognized schema-version, it should warn and proceed with best-effort parsing rather than failing.

## Concurrency

STATE.md is NOT safe for concurrent access. Only one session should be active per branch at a time. If session-start detects `status: active`, it prompts the user to resume or start fresh (which overwrites the stale STATE.md).

- **Discovery grep-verification** — distributional claims in W1 outputs (e.g., "N of M callers", "100% adopt pattern X") MUST quote the executed grep + file scope + count. See [`../../.claude/rules/parallel-sessions.md`](../../.claude/rules/parallel-sessions.md) § PSA-006.

## STATE.md Write-Size Guard (#739)

Every STATE.md disk write routes through `writeStateMd()` (`scripts/lib/state-md/frontmatter-mutators.mjs`), the lock-guarded read-transform-write helper. Before committing a write, `writeStateMd()` runs `evaluateSizeCeiling(before, after)` and REFUSES the write (WARN to `process.stderr`, no throw by default, prior on-disk contents left intact as last-known-good) when either:

- **Absolute:** `after` byte-size exceeds `DEFAULT_STATE_MD_SIZE_CEILING_BYTES` (256 KB), or
- **Ratio:** `after` byte-size exceeds `STATE_MD_SIZE_CEILING_RATIO` (5×) the prior on-disk (`before`) size — skipped on first-writes (`before === ''`), since there is no prior size to ratio against.

This is the mechanical backstop against the 6.3 MB frontmatter-balloon incident class. Callers may opt into `opts.throwOnCeiling: true` for a thrown `Error` (`.code === 'STATE_MD_SIZE_CEILING'`) instead of the default no-op-with-WARN.

It is a **symptom-level backstop, not the root-cause fix** — the underlying `yaml-parser` parse/serialize asymmetry that produced the balloon remains a tracked follow-up (a stricter round-trip-verification gate was evaluated and deliberately NOT shipped, because it false-positived on legitimate operator-authored scalars containing literal quote characters). Reinforces the existing guidance: mutate STATE.md via the structured writers (`scripts/lib/state-md.mjs`, `writeStateMd()`) or literal writes — never regex over the frontmatter block, which is the class of edit that produced the original balloon.

## Worktree-Auto-Promotion (#574, Epic #568 P3.1)

When a session is promoted to a sibling worktree via `enterWorktree({basePath, sessionId, branch, repoRoot})` from `scripts/lib/autopilot/worktree-pipeline.mjs`, the new worktree gets its OWN STATE.md scoped to that worktree. The original repo's STATE.md is unaffected.

- Original worktree (where PROMOTION_OFFER was issued): retains its STATE.md, no changes from the promotion event.
- New sibling worktree: runs `session-start` from scratch in the new tree; Phase 1.2 acquires its own session-lock; Phase 1b writes its own STATE.md.
- Cleanup ownership: `session-end` Phase 4a in the promoted worktree handles `git worktree remove` after Phase 4 commit+push completes. The cleanup writes a deviation entry to its own STATE.md before removing the worktree.

Cross-references:
- `skills/session-end/SKILL.md § Phase 4a` (cleanup)
- `scripts/lib/autopilot/worktree-pipeline.mjs § enterWorktree` (creation)
- `skills/_shared/parallel-aware-auq.md` (PROMOTION_OFFER AUQ)

## Session Lock Schema (v2, since Epic #583)

The `.orchestrator/session.lock` file is written mechanically by `hooks/_lib/lock-bootstrap.mjs` on every `SessionStart` hook invocation (Epic #583 D1 fix). Prior to Epic #583, the lock was only created when the coordinator-LLM executed Phase 1.2 prose — a silent-skip risk.

### Lock body (schema v2)

```json
{
  "session_id":          "<UUID-v4 OR semantic-id>",
  "semantic_session_id": "<branch>-<YYYY-MM-DD>-<mode>-<n>",
  "started_at":          "<ISO-8601 UTC>",
  "last_heartbeat":      "<ISO-8601 UTC>",
  "mode":                "deep|feature|housekeeping|session|...",
  "pid":                 12345,
  "host":                "hostname",
  "ttl_hours":           4
}
```

### Field notes

| Field | Required since | Description |
|---|---|---|
| `session_id` | v1 | The session identifier (UUID-v4 on Claude Code, semantic on Codex/Cursor). |
| `semantic_session_id` | v2 (Epic #583) | The semantic form (`<branch>-<YYYY-MM-DD>-<mode>-<n>`) **always present**, even when `session_id` is a UUID. Closes D4 gap: semantic-id branch was previously dead code on Claude Code (stdin always provides UUID). |
| `started_at` | v1 | ISO-8601 timestamp when the lock was written. |
| `last_heartbeat` | v2 (Epic #583) | ISO-8601 timestamp updated by the `SessionStart` hook and by `PostToolBatch`/`Stop` hooks. **Basis for liveness determination** — replaces PID-liveness (see below). |
| `mode` | v1 | Session mode consulted by exclusivity-matrix. May be `"unknown"` in the provisional lock written by the hook before Session Config + AUQ have settled. |
| `pid` | v1 | **Forensic only — do NOT use for liveness.** Records the writer's process PID (the hook subprocess, ~500ms lifetime). Dead PIDs are expected and normal. See D2 / D3 notes below. |
| `host` | v1 | `os.hostname()` of the machine that wrote the lock. Cross-host locks skip PID checks. |
| `ttl_hours` | v1 | Maximum age before the lock is considered stale regardless of other signals. Default 4h. |

### Liveness rule (v2)

```
isAlive = (Date.now() - Date.parse(last_heartbeat)) < ttl_hours * 3600 * 1000
```

This replaces the v1 PID-liveness check (`process.kill(pid, 0)`) which was fundamentally broken because the recorded `pid` belongs to the ephemeral hook subprocess (dies in <1s), not the long-lived Claude coordinator process. The PostgreSQL pattern — use a heartbeat timestamp rather than PID to establish liveness — is the authoritative reference (see W1-D4 best-practices §1.5).

### #744 — heartbeat is the SOLE active gate (incident + fix)

Despite the v2 liveness rule above existing since Epic #583, `acquire()`'s conflict classifier (`scripts/lib/session-lock.mjs`, the `classifyExisting()` closure) and `checkStale()` still let `pidAlive`/TTL-age act as an independent veto — which let an external `/close` observe the lock's recorded `pid` (the ephemeral hook subprocess / `node -e acquire()` PID, routinely dead within <1s) as dead and misclassify a live, actively-heartbeating session as `stale-pid-dead`, hijacking it mid-wave. Fixed in #744:

- `classifyExisting()` now checks `isLockLive(existing)` **first** and unconditionally returns `{ reason: 'active' }` when true — a dead recorded `pid` can never veto a fresh `last_heartbeat`.
- Only once `isLockLive()` is false does `pidAlive` pick the stale variant: `stale-pid-dead` when `pidAlive === false` (same-host, confirmed dead), else `stale-pid-alive` — which also covers `pidAlive === null` (cross-host locks, `host !== os.hostname()`, never a confirmable dead PID, so cross-host locks can never land on `stale-pid-dead`).
- `checkStale()` surfaces the same `isLockLive()` result as an additive `isLive` field alongside the legacy `ttlExpired`/`pidAlive` signals, so recovery-flow diagnostics can observe when the two diverge.

Net: `pid` (field notes above) stays forensic-only; `last_heartbeat` freshness is the sole determinant of "is this session still active" everywhere in `session-lock.mjs`.

### Schema v1 → v2 backward-compat

Readers (e.g., `readLock()` in `session-lock.mjs`, `discoverActiveSessions()`) MUST tolerate absent `last_heartbeat` and `semantic_session_id` fields (v1 locks written before Epic #583). When `last_heartbeat` is absent, fall back to TTL-based expiry from `started_at`. When `semantic_session_id` is absent, treat as unknown.
