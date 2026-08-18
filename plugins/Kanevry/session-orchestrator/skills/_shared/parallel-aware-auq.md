# Parallel-Aware AUQ Templates

> Three reusable AskUserQuestion blocks for the parallel-aware preamble (`parallel-aware-preamble.md`).
> Consumed by: autopilot, session-start, session-plan, wave-executor, session-end (5 orchestrator entry-points).

## When to fire which AUQ

Driven by the preamble's outcome (see `parallel-aware-preamble.md` § Outcome Handling):

| Preamble outcome | AUQ to fire |
|------------------|-------------|
| `EXCLUSIVE_BLOCKED` | Exclusive-Conflict AUQ (below) |
| `PROMOTION_OFFER` | Worktree-Promotion AUQ (below) |
| `PASS_THROUGH` | No AUQ |

The third variant — **Always-OK Pass-Through** — fires no AUQ; documented here only for completeness so callers don't reinvent it.

## Exclusive-Conflict AUQ (PRD §3 P1 row 2)

Fires when an `exclusive`-class session (`bootstrap`, `housekeeping`, `memory-cleanup`) is already active in the worktree-family AND the caller is NOT `always-ok`-class.

### Claude Code (AskUserQuestion)

```js
AskUserQuestion({
  questions: [{
    question: `An exclusive session is active in this repository (mode=${blockingSession.mode}, started ${ageHours}h ago, host=${blockingSession.host}, pid=${blockingSession.pid}, worktree=${blockingSession.worktreePath}). This blocks all other modes. How should I proceed?`,
    header: "Parallel-Exclusive",
    multiSelect: false,
    options: [
      { label: "Warten (Recommended)", description: "Wait for the exclusive session to finish. The preamble will not retry automatically — re-run the command after the other session closes." },
      { label: "Andere Session beenden", description: "I will close the other session myself, then re-run this command. The preamble surfaces but does NOT terminate the other session." },
      { label: "Abbrechen", description: "Exit cleanly. No STATE.md initialization, no lock acquired." },
    ],
  }],
});
```

### Codex CLI / Cursor IDE / Pi fallback (numbered Markdown list)

```
Parallel-Exclusive conflict — an exclusive session is active in this repository.
  Mode: <blockingSession.mode>
  Started: <ageHours>h ago (host=<host>, pid=<pid>)
  Worktree: <blockingSession.worktreePath>
This blocks all other modes.

1. Warten (Recommended) — wait for the exclusive session to finish; re-run after it closes.
2. Andere Session beenden — I will close the other session myself.
3. Abbrechen — exit cleanly without initializing STATE.md.

Reply with the number of your choice.
```

### Outcome handling

- **Warten** → exit Phase-0 cleanly with stderr note `parallel-aware: waiting on exclusive session_id=<id>`. No retry loop.
- **Andere Session beenden** → exit Phase-0 cleanly with stderr note `parallel-aware: deferred to operator — exclusive session_id=<id>`. No automatic termination.
- **Abbrechen** → exit Phase-0 immediately. No file writes.

## Worktree-Promotion AUQ (PRD §3 P1 row 3)

Fires when the caller is `parallel-ok`-class AND another `parallel-ok` session is active in the SAME worktree (i.e., main worktree collision).

### Claude Code (AskUserQuestion)

```js
AskUserQuestion({
  questions: [{
    question: `A compatible parallel session is active in this worktree (mode=${parallelPeer.mode}, started ${ageHours}h ago, pid=${parallelPeer.pid}). You can either: (a) auto-promote to a sibling worktree to run isolated, or (b) run in-place alongside the existing session (file conflicts likely). How should I proceed?`,
    header: "Worktree-Promo",
    multiSelect: false,
    options: [
      { label: "Worktree anlegen + starten (Recommended)", description: "Create a sibling git worktree at ../<repo-name>-<semantic-session-id>/ and start the new session there. Isolates file edits; recommended for parallel deep/feature sessions. Calls enterWorktree() from scripts/lib/autopilot/worktree-pipeline.mjs." },
      { label: "Manuell — in-place daneben", description: "Run in the current worktree alongside the existing session. File conflicts possible; PSA-001/002/004 discipline required. A Deviation is logged." },
      { label: "Abbrechen", description: "Exit cleanly. No STATE.md initialization." },
    ],
  }],
});
```

### Codex CLI / Cursor IDE / Pi fallback (numbered Markdown list)

```
Worktree-Promotion offer — a compatible parallel session is active in this worktree.
  Peer mode: <parallelPeer.mode>
  Started: <ageHours>h ago (pid=<pid>)

1. Worktree anlegen + starten (Recommended) — create sibling worktree and start isolated session.
2. Manuell — in-place daneben — run alongside (file conflicts possible, Deviation logged).
3. Abbrechen — exit cleanly.

Reply with the number of your choice.
```

### Outcome handling

- **Worktree anlegen + starten** → invoke `enterWorktree({ basePath, sessionId, branch, repoRoot })` from `scripts/lib/autopilot/worktree-pipeline.mjs`. The helper creates a sibling worktree at `<basePath>/<repo-name>-<sessionId>/`, runs idempotency + boundary checks, and logs a WARN line to stderr on fresh creation. Once the worktree exists, exit the current preamble flow — the new worktree's own session-start runs from scratch (Phase 1 onwards). On failure (`WorktreeBoundaryError` or `git worktree add` non-zero exit), emit a stderr warning `parallel-aware: enterWorktree failed: <error>; falling back to Manuell` and proceed via the Manuell path.
- **Manuell** → append a Deviation via `appendDeviationOnDisk()`:
  `Worktree-Auto-Promotion declined; running in-place alongside session_id=<peer.sessionId>, mode=<peer.mode>, pid=<peer.pid>. PSA-001/PSA-002/PSA-004 discipline applies.`
  Continue Phase-0.
- **Abbrechen** → exit Phase-0 immediately. No file writes.

## Always-OK Pass-Through (no AUQ)

Fires when the caller's mode is in the `always-ok` class (`discovery`, `evolve`, `plan`, `repo-audit`, `portfolio`). The preamble returns `PASS_THROUGH` immediately regardless of other active sessions. No AUQ, no Deviation, no latency penalty.

```js
// Conceptual — there is NO AUQ for this case.
// The preamble returns { outcome: 'PASS_THROUGH', callerClass: 'always-ok', active }.
// The caller skill continues to Phase 1 unconditionally.
```

PRD §3 P1 row 5 specifies this is a hard guarantee — read-only modes never produce an interrupt.

## See Also

- `parallel-aware-preamble.md` — the preamble that fires these AUQs
- `.claude/rules/ask-via-tool.md` — AUQ-001 through AUQ-005 (always use the tool, not prose)
- `.claude/rules/parallel-sessions.md` — PSA-001/PSA-002 (overlap-check discipline)
- "Parallel-Aware Sessions" (#568; archived in the private Meta-Vault) § 3 P1 — Gherkin rows 2, 3, 5 that these AUQs satisfy
