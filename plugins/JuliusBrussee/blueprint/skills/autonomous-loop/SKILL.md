---
name: autonomous-loop
description: |
  How Cavekit's autonomous execution loop works — state machine, stop hook,
  completion sentinel, lock, budgets, iteration cap. Read this skill any time
  you are about to run /ck:make, debug a stuck session, or write a new command
  that needs the loop. Trigger phrases: "how does the loop work", "stop hook",
  "autonomous", "completion sentinel", "why is the session looping".
---

# Autonomous Loop

The loop lets a single `/ck:make` invocation run dozens of agent iterations
without user intervention, while still respecting per-task budgets, session
budgets, and explicit user-approval gates.

## Architecture

```
┌─────────────────┐  Stop event   ┌────────────────────┐
│  Claude Code    │──────────────▶│   stop-hook.sh     │
│   session       │               │  (.cavekit/loop    │
└─────────────────┘               │   active?)         │
        ▲                         └─────────┬──────────┘
        │                                   │ route()
        │ next prompt injected              ▼
        │                         ┌────────────────────┐
        │                         │ cavekit-tools.cjs  │
        │                         │  routeDecision()   │
        │                         │  + status-block    │
        │                         │  + backprop-       │
        │                         │    directive       │
        │                         └─────────┬──────────┘
        │                                   │
        └───────── {decision:"block",       │
                    reason:<next prompt>} ◀─┘
```

## Files the loop touches

All under `<project>/.cavekit/`:

| File                            | Writer                | Purpose                                      |
|---------------------------------|-----------------------|----------------------------------------------|
| `.loop.json`                    | setup-loop            | Sentinel; stop-hook no-ops without it.       |
| `.loop.lock`                    | stop-hook (heartbeat) | Single-writer lock. PID + hostname + ts.     |
| `state.md`                      | cavekit-tools         | `phase`, `current_task`, `iteration`.        |
| `token-ledger.json`             | token-monitor hook    | Session + per-task token tallies.            |
| `task-status.json`              | commands              | Authoritative task registry.                 |
| `.progress.json`                | progress-tracker      | Zero-context UI snapshot.                    |
| `.auto-backprop-pending.json`   | auto-backprop hook    | Flag file from failed tests.                 |
| `history/backprop-log.md`       | backprop skill        | Append-only trace log.                       |
| `capabilities.json`             | discover command      | MCP + CLI tool detection.                    |

## Lifecycle

1. **Setup** — `/ck:make` calls:
   ```
   node "${CLAUDE_PLUGIN_ROOT}/scripts/cavekit-tools.cjs" setup-loop
   ```
   This writes `.loop.json` (activating the stop hook) and resets `state.md`.

2. **Work** — the agent does one wave of task execution per iteration.

3. **Stop fires** — Claude Code's Stop event triggers `stop-hook.sh`. The hook:
   - reads stdin for `session_id` and `transcript_path`
   - acquires / refreshes the lock
   - scans the last 20 transcript lines for `<promise>CAVEKIT COMPLETE</promise>`
   - if sentinel found → teardown + exit silently
   - else → asks `routeDecision()` for the next prompt
   - prepends the backprop directive if the flag file exists
   - returns `{"decision":"block","reason":<next prompt>}`

4. **Repeat** — Claude Code treats `decision:block` + `reason:...` as a new
   user message, so the session continues.

5. **Teardown** — one of:
   - completion sentinel detected
   - max-iterations reached (`CAVEKIT_MAX_ITERATIONS`)
   - session budget exhausted (`CAVEKIT_BUDGET_EXHAUSTED`)
   - lock stolen by another session (`CAVEKIT_LOCK_CONFLICT`)
   - user interrupt (hook returns no output; session stops normally)

## Completion sentinel

To end the loop cleanly, emit exactly:

```
<promise>CAVEKIT COMPLETE</promise>
```

The hook searches for this literal in the last 20 transcript lines. Put it on
its own line at the very end of the final message. Do not wrap it in code
fences or paraphrase it — the search is a literal substring match.

## Terminal sentinels

When `routeDecision()` cannot safely continue, it returns one of these
strings instead of a prompt:

| Sentinel                     | Meaning                               |
|------------------------------|---------------------------------------|
| `CAVEKIT_LOOP_DONE`          | All tasks complete. Hook exits silent.|
| `CAVEKIT_MAX_ITERATIONS`     | Iteration cap hit. Loop halted.       |
| `CAVEKIT_BUDGET_EXHAUSTED`   | Session budget exhausted.             |
| `CAVEKIT_LOCK_CONFLICT`      | Another session owns the lock.        |

The hook translates each into a short user-facing message before returning.

## Lock protocol

The lock is a JSON file (`.loop.lock`) with `{owner, pid, host, heartbeat_at}`.

- **Owner tag**: `session:<session_id>`.
- **Heartbeat**: every Stop invocation refreshes `heartbeat_at`.
- **Stale**: > 5 minutes since last heartbeat. A new session may steal a stale
  lock.
- **Conflict**: non-owner with fresh lock → returns `CAVEKIT_LOCK_CONFLICT`.

Never delete `.loop.lock` while a session might be active. Use
`cavekit-tools release-lock --owner <tag>` instead.

## Debugging a stuck loop

```bash
# Inspect current state
node "${CLAUDE_PLUGIN_ROOT}/scripts/cavekit-tools.cjs" status

# Who holds the lock?
cat .cavekit/.loop.lock

# What would the router do right now?
node "${CLAUDE_PLUGIN_ROOT}/scripts/cavekit-tools.cjs" route

# Drop the loop entirely (safe after a crash)
node "${CLAUDE_PLUGIN_ROOT}/scripts/cavekit-tools.cjs" teardown-loop
```

Turn on debug logging by exporting `CAVEKIT_DEBUG=1`. The hook will write to
`.cavekit/.debug.log`.

## What not to do

- Do **not** hand-edit `state.md`'s `phase` field while a loop is active. The
  hook assumes single-writer semantics and will overwrite you.
- Do **not** set your own stop hook that also blocks. Multiple blocking hooks
  race, and Claude Code picks one arbitrarily.
- Do **not** emit the completion sentinel unless every task in the registry is
  truly `complete`. The hook trusts the sentinel and tears down immediately.
