---
name: account-rotation
description: Switch a caller-selected coding-agent
---
# Account rotation — credential adapter

Choose the credential tool from both host and agent family, perform only the
explicit account switch, and report the identity observed by the matching
runtime.

Verifying identity through the target runtime works because the runtime is the
only party whose opinion matters: credential files can be swapped perfectly
and still authenticate as the old account in an already-running process.

Named failure mode — **stale-process identity**: declaring the rotation done
while every live session still holds the previous account's tokens in memory.

Anti-pattern: confirming a switch by diffing credential file bytes.
Corrective: ask the matching runtime who it is now, and report whether a new
process is required for the answer to hold.

## Boundary

- On macOS with Claude credentials, use the operator's `claude-acct` route.
- For Codex, Gemini, Linux, or WSL file-backed credentials, use `caam`.
- Verify account identity through the target runtime; token bytes are not account
  identity.
- Existing processes retain credentials already loaded in memory. Rotation
  affects a new process.
- This skill does not restart work, resume a task, select a pane, move repository
  state, or decide what happens after the switch.

Return the host, agent family, selected tool, requested account/profile, observed
identity/status, command exit code, and whether a new process is required.
