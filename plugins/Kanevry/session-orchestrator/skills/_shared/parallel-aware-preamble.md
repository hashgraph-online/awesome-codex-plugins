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

## Identity Binding for `findPeers` (#1085)

`mySessionId` / `callerSessionId` is a **hint for the caller's original
surface**, not a license to turn an attribution label into ownership. A native
raw id self-excludes on the discovered lock/registry surface directly. Given a
semantic hint, `findPeers` may translate it to a concrete local raw id only when
both proofs hold: `current-session.json` has the same semantic label **and** its
raw `session_id` exactly equals the readable local lock's raw `session_id`.

On a missing, malformed, or mismatched binding, `findPeers` must map nothing and
leave the discovered lock visible. The STATE.md surface always receives the
original hint and therefore compares STATE.md `session` as the attribution label
it is; it is never rewritten to a raw id. This guarded translation is only
self-exclusion for discovery, not lock/registry ownership and not a continuity
bridge across a host rotation that changes both values.

**What the binding does not prove.** Both files it reads are repo-global, so the
check establishes that they are mutually CONSISTENT — not that they describe
*this* process. Semantic labels are routinely shared between simultaneously live
sessions, and when a foreign live session wrote both files last under a label
equal to this hint, its raw id is filtered out and the peer disappears from the
result. Measured 2026-08-21: with a null hint the foreign peer is returned, with
the colliding semantic hint `peers` is empty. Treat a quiet `findPeers` result as
weaker evidence than a git or filesystem signal, and prefer passing the native
raw id whenever the caller has one. Closing this needs a per-process ownership
proof; see #1091.

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

  // GH#67: a registry-sourced peer whose lock is SUPERSEDED (a LIVE lock at
  // this repoRoot is owned by a DIFFERENT raw session_id) is likely a
  // finished-but-still-fresh task on a platform without SessionEnd. It stays
  // visible in `active` (never a filter — the lock is advisory, #1085
  // contract), but it is not eligible to trigger the Promotion AUQ. Split it
  // out as advisory before the parallelPeer lookup.
  const supersededPeers = classifiedActive.filter((e) => e.lockSuperseded === true);
  const promotionEligible = classifiedActive.filter((e) => e.lockSuperseded !== true);

  const parallelPeer = callerClass === 'parallel-ok'
    ? promotionEligible.find((e) => e._class === 'parallel-ok' && e.sessionId !== callerSessionId)
    : null;
  if (parallelPeer) {
    return { outcome: 'PROMOTION_OFFER', callerClass, parallelPeer, active: classifiedActive };
  }

  return { outcome: 'PASS_THROUGH', callerClass, active: classifiedActive, advisory: supersededPeers };
}
```

## Outcome Handling

The skill consuming the preamble translates the outcome:

| Outcome | Action |
|---------|--------|
| `PASS_THROUGH` | Continue immediately. No AUQ. Pre-P1.3 behavior. |
| `EXCLUSIVE_BLOCKED` | Fire Exclusive-Conflict AUQ from `parallel-aware-auq.md`. Block until user response. On "Abbrechen": exit cleanly. On "Andere Session beenden": surface to user (preamble does NOT kill other session). On "Warten": pause Phase 0; re-run preamble on user retry. |
| `PROMOTION_OFFER` | Fire Promotion AUQ from `parallel-aware-auq.md`. On "Worktree anlegen": call `enterWorktree({ ..., rawSessionId, reason: 'worktree-promotion' })` from worktree-pipeline.mjs (see parallel-aware-auq.md outcome-handling) — since #1170 this ONE call also releases the source root: it calls `leaveSourceRoot({ repoRoot, sessionId: rawSessionId, semanticSessionId, reason })` from `session-transition.mjs` internally, on BOTH success exits, so no separate call is made here. `rawSessionId` is the RAW physical `session_id` from this root's `.orchestrator/session.lock` (`readLock({ repoRoot })`), never the semantic label and never `current-session.json` (may describe a peer, #863). The promotion is a process boundary, not a live migration (#1069): the old root is deregistered and its lock released BEFORE the new worktree's own Phase 1.2 acquires — never both roots owning at once. The return value's `left` field carries the outcome; `leaveSourceRoot()` never throws, so on `left.ok !== true` `enterWorktree` itself emits the stderr WARN `enterWorktree: leaveSourceRoot: <reason>` and the promotion continues regardless. On "Manuell": append Deviation (`Worktree-Auto-Promotion declined; running in-place alongside session_id=<peer.sessionId>`) and continue. On "Abbrechen": exit. |

**Superseded-lock advisory (GH#67).** A `discovered` peer with `lockSuperseded: true` never fires the Promotion AUQ — it is downgraded to the `advisory` array on the `PASS_THROUGH` result instead (see the `runParallelAwarePreamble` reference above), because a live lock at this repoRoot is owned by a different raw session_id and the entry is likely a finished-but-still-fresh task on a platform without SessionEnd, not a live collision (#1085 advisory-lock contract — the entry is never filtered, only downgraded). The consuming skill prints ONE advisory line per entry: `parallel-aware: registry entry <sessionId> (last heartbeat <N> min ago) is superseded by this root's live lock <lockOwnerId> — likely a finished task on a platform without SessionEnd (GH#67); still counted for PSA-001 awareness`, then continues. `lockSuperseded: false` with `lockOwnerId: null` means "no live lock here" — distinct from "own lock". The same session id remains PSA-002-relevant if it also shows up in STATE.md (`source: 'state-md'`, handled unchanged by Phase 1.2.1/Phase 1b below).

## Phase 1b Peer-Guard (defense-in-depth)

After Phase 0.5 (parallel-aware preamble) and Phase 1.2 (session-lock acquire), session-start Phase 1b initializes STATE.md. Before overwriting, the guard MUST run — via `findPeers(repoRoot, { mySessionId })` consuming the `state-md`-sourced subset (which delegates internally to `scripts/lib/state-md-peer-guard.mjs:checkPeerStateMd()`).

If `findPeers` yields a `state-md`-sourced peer (non-null), fire the Worktree-Promotion AUQ from `parallel-aware-auq.md`. This catches races where the preamble's lock-based detection missed an active peer (e.g., a session whose lock was force-deleted but STATE.md is still status:active).

The guard is a SOFT-GATE — operator can override, but the warning is mandatory.

### Guard decision tree (for Phase 1b callers)

```
findPeers(repoRoot, { mySessionId }) → peer = peers.find((p) => p.source === 'state-md') →
  peer === null  →  safe to write STATE.md; continue Phase 1b normally.
  peer !== null  →  fire Promotion AUQ (parallel-aware-auq.md "Promotion" block).
                    On "Worktree anlegen": enterWorktree(..., rawSessionId) — releases
                                           the source root internally (#1170; no
                                           separate leaveSourceRoot call needed)
                                           → continue in sibling (process boundary,
                                             old root released before the new acquire).
                    On "Manuell": appendDeviationOnDisk() + continue in-place.
                    On "Abbrechen": exit cleanly.
```

### Integration reference

```js
import { findPeers } from '../../scripts/lib/peer-discovery.mjs';

// Inside Phase 1b, before writing STATE.md. Preserve the original
// attribution-label hint for the STATE.md surface; findPeers guards any
// semantic→raw translation for discovered peers internally.
const { peers } = await findPeers(repoRoot, { mySessionId: callerSessionHint });
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
