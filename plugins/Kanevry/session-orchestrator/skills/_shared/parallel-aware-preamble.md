# Parallel-Aware Preamble

> Single source of truth for the parallel-session-detection preamble.
> Referenced by: autopilot, session-start, session-plan, wave-executor, session-end (5 orchestrator entry-points).

## Purpose

Every session-orchestrator entry-point runs this preamble silently at Phase-0.x (after the bootstrap-gate, before config-reading). It detects other active sessions in the same repository worktree-family, classifies the caller's mode against the exclusivity-matrix, and either passes through, offers Worktree-Auto-Promotion (P3), or blocks via AskUserQuestion.

When no parallel session is detected, execution continues with zero overhead. When a conflict is detected, the appropriate AUQ from `parallel-aware-auq.md` fires.

## Gate Classes

The preamble applies one of three gate semantics based on the caller's mode-class:

<HARD-GATE>
**Exclusive class** (`bootstrap`, `housekeeping`, `memory-cleanup`):
If any other active session exists in the worktree-family, you MUST NOT proceed. The preamble fires the Exclusive-Conflict AUQ from `parallel-aware-auq.md` (`[Warten / Andere Session beenden / Abbrechen]`).
There is no bypass. There is no exception for urgent housekeeping. The ONLY valid next action is the user's AUQ response.
</HARD-GATE>

<SOFT-GATE>
**Parallel-OK class** (`deep`, `feature`):
If another `parallel-ok`-class session is active in the same worktree, the preamble offers Worktree-Auto-Promotion via the Promotion AUQ from `parallel-aware-auq.md` (`[Worktree anlegen + starten (Recommended) / Manuell / Abbrechen]`). The user may proceed in-place by selecting "Manuell" — the preamble logs a Deviation but does not block.

If an `exclusive`-class session is also active, the Exclusive-Conflict AUQ takes precedence (HARD-GATE wins).
</SOFT-GATE>

**Always-OK class** (`discovery`, `evolve`, `plan`, `repo-audit`, `portfolio`):
The preamble passes through with zero AUQ regardless of other active sessions. Read-only modes never conflict.

## Preamble Algorithm

Execute these steps in order. Any classification determines outcome.

```
1. Call findPeers(repoRoot, { mySessionId: callerSessionId }) from scripts/lib/peer-discovery.mjs.
   - Returns: { peers: Array<{source, sessionId, mode, pid, host, worktreePath, ageHours?, currentWave?}> }
   - Phase 0.5 consumes the non-'state-md' subset: peers.filter(p => p.source !== 'state-md').
   - 2-second timeout built-in (via discoverActiveSessions). On timeout or git failure: A1 fallback (single-worktree mode).
   - Empty active list → no parallel context → PASS_THROUGH (continue immediately).

2. Classify the caller's mode via classifyMode(callerMode) from scripts/lib/exclusivity-matrix.mjs.
   - GOTCHA: classifyMode throws on unknown mode. Wrap in try/catch; on throw, default to 'parallel-ok' (most permissive default) and log a stderr WARN.
   - Returns: 'exclusive' | 'parallel-ok' | 'always-ok'

3. Apply the decision matrix:
   - If callerClass === 'always-ok' → return PASS_THROUGH (no AUQ; preamble done).
   - For each active session, classify entry.mode via classifyMode (same safe fallback).
   - If any entry has entryClass === 'exclusive' AND callerClass !== 'always-ok':
       → fire Exclusive-Conflict AUQ from parallel-aware-auq.md
       → block until user response
   - Else if callerClass === 'parallel-ok' AND any entry has entryClass === 'parallel-ok':
       → fire Promotion AUQ from parallel-aware-auq.md
       → user may pick "Worktree anlegen" (P3 fills the action), "Manuell" (in-place + Deviation), or "Abbrechen" (exit)
   - Otherwise (no overlap) → return PASS_THROUGH.

4. Record any non-PASS_THROUGH outcome as a Deviation in STATE.md via appendDeviationOnDisk().
```

## Implementation (JavaScript reference)

```js
import { findPeers } from '../../scripts/lib/peer-discovery.mjs';
import { classifyMode } from '../../scripts/lib/exclusivity-matrix.mjs';

async function runParallelAwarePreamble({ repoRoot, callerMode, callerSessionId }) {
  // Step 1: discover active sessions via unified findPeers (fail-open, never throws).
  // Phase 0.5 consumes only the non-'state-md' subset (lock+registry surface).
  // The 'state-md' subset is reserved for Phase 1.2.1 (peer-guard after lock acquire).
  let active;
  try {
    const { peers } = await findPeers(repoRoot, { mySessionId: callerSessionId });
    active = peers.filter((p) => p.source !== 'state-md');
  } catch (err) {
    process.stderr.write(`[parallel-aware-preamble] WARN: findPeers failed: ${err.message} — passing through (A1 fallback)\n`);
    return { outcome: 'PASS_THROUGH', reason: 'discovery-error' };
  }

  // Step 2: classify caller (safe — never throw)
  let callerClass;
  try {
    callerClass = classifyMode(callerMode);
  } catch {
    process.stderr.write(`[parallel-aware-preamble] WARN: unknown mode '${callerMode}' — defaulting to 'parallel-ok'\n`);
    callerClass = 'parallel-ok';
  }

  // Step 3: always-ok passes through
  if (callerClass === 'always-ok') return { outcome: 'PASS_THROUGH', callerClass, active };

  // Step 4: empty active list → no conflict
  if (!Array.isArray(active) || active.length === 0) {
    return { outcome: 'PASS_THROUGH', callerClass, active: [] };
  }

  // Step 5: classify each entry (safe)
  const classifiedActive = active.map((entry) => {
    let entryClass;
    try { entryClass = classifyMode(entry.mode); } catch { entryClass = 'parallel-ok'; }
    return { ...entry, _class: entryClass };
  });

  // Step 6: decision matrix
  const exclusiveActive = classifiedActive.find((e) => e._class === 'exclusive' && e.sessionId !== callerSessionId);
  if (exclusiveActive && callerClass !== 'always-ok') {
    return { outcome: 'EXCLUSIVE_BLOCKED', callerClass, blockingSession: exclusiveActive, active: classifiedActive };
  }

  const parallelPeer = callerClass === 'parallel-ok'
    ? classifiedActive.find((e) => e._class === 'parallel-ok' && e.sessionId !== callerSessionId)
    : null;
  if (parallelPeer) {
    return { outcome: 'PROMOTION_OFFER', callerClass, parallelPeer, active: classifiedActive };
  }

  return { outcome: 'PASS_THROUGH', callerClass, active: classifiedActive };
}
```

## Outcome Handling

The skill consuming the preamble translates the outcome:

| Outcome | Action |
|---------|--------|
| `PASS_THROUGH` | Continue immediately. No AUQ. Pre-P1.3 behavior. |
| `EXCLUSIVE_BLOCKED` | Fire Exclusive-Conflict AUQ from `parallel-aware-auq.md`. Block until user response. On "Abbrechen": exit cleanly. On "Andere Session beenden": surface to user (preamble does NOT kill other session). On "Warten": pause Phase 0; re-run preamble on user retry. |
| `PROMOTION_OFFER` | Fire Promotion AUQ from `parallel-aware-auq.md`. On "Worktree anlegen": call enterWorktree() from worktree-pipeline.mjs (see parallel-aware-auq.md outcome-handling). On "Manuell": append Deviation (`Worktree-Auto-Promotion declined; running in-place alongside session_id=<peer.sessionId>`) and continue. On "Abbrechen": exit. |

## Phase 1b Peer-Guard (defense-in-depth)

After Phase 0.5 (parallel-aware preamble) and Phase 1.2 (session-lock acquire), session-start Phase 1b initializes STATE.md. Before overwriting, the guard MUST run — via `findPeers(repoRoot, { mySessionId })` consuming the `state-md`-sourced subset (which delegates internally to `scripts/lib/state-md-peer-guard.mjs:checkPeerStateMd()`).

If `findPeers` yields a `state-md`-sourced peer (non-null), fire the Worktree-Promotion AUQ from `parallel-aware-auq.md`. This catches races where the preamble's lock-based detection missed an active peer (e.g., a session whose lock was force-deleted but STATE.md is still status:active).

The guard is a SOFT-GATE — operator can override, but the warning is mandatory.

### Guard decision tree (for Phase 1b callers)

```
findPeers(repoRoot, { mySessionId }) → peer = peers.find((p) => p.source === 'state-md') →
  peer === null  →  safe to write STATE.md; continue Phase 1b normally.
  peer !== null  →  fire Promotion AUQ (parallel-aware-auq.md "Promotion" block).
                    On "Worktree anlegen": enterWorktree() → continue in sibling.
                    On "Manuell": appendDeviationOnDisk() + continue in-place.
                    On "Abbrechen": exit cleanly.
```

### Integration reference

```js
import { findPeers } from '../../scripts/lib/peer-discovery.mjs';

// Inside Phase 1b, before writing STATE.md:
const { peers } = await findPeers(repoRoot, { mySessionId: sessionId });
const peer = peers.find((p) => p.source === 'state-md') ?? null;
// Phase 1.2.1 consumes only the 'state-md' subset (STATE.md surface only).
if (peer !== null) {
  // peer.sessionId, peer.mode, peer.currentWave, peer.ageHours are populated.
  // Fire the Promotion AUQ — do NOT silently overwrite.
  // ... AUQ logic per parallel-aware-auq.md ...
}
```

## Cross-References

- **Discovery layer:** `scripts/lib/session-discovery.mjs` (`discoverActiveSessions`, `findWorktrees`) — shipped in P1.1 #569
- **Classification:** `scripts/lib/exclusivity-matrix.mjs` (`EXCLUSIVITY_MATRIX`, `classifyMode`) — shipped in P1.1 #569
- **Lock integration:** `scripts/lib/session-lock.mjs:acquire()` extended in P1.2 #570 — accepts pre-computed `activeSessions[]` and returns matrix-aware reasons (`active-incompatible-exclusive`, `active-compatible-parallel`, `active-readonly-bypass`)
- **AUQ patterns:** `parallel-aware-auq.md` (three reusable AUQ blocks) — sibling file
- **Deviation logging:** `scripts/lib/state-md.mjs:appendDeviationOnDisk()`
- **Phase 1b peer-guard:** `scripts/lib/state-md-peer-guard.mjs:checkPeerStateMd()` — shipped in #588

## Idempotency

The preamble is read-only relative to repository state (no file writes unless the user picks an action). Repeated invocation produces the same outcome given the same active-session set. Safe to call multiple times in the same skill invocation if the caller wants to re-check after a wait period.

The Promotion AUQ's "Worktree anlegen" path (P3.1) creates a new sibling worktree and is NOT idempotent — re-running after promotion discovers the new worktree as an active session (which is intended behavior).

## See Also

- `bootstrap-gate.md` — sibling Phase-0 gate (HARD; orthogonal layer)
- `.claude/rules/parallel-sessions.md` — PSA-001 through PSA-006 (behavioural rules complementing this mechanical layer)
- "Parallel-Aware Sessions" (#568; archived in the private Meta-Vault) § 3 P1 + § 3.A P1 — acceptance criteria this preamble satisfies
