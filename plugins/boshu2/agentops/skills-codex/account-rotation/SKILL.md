---
name: account-rotation
description: 'Switch a caller-selected coding-agent Triggers: "switch account", "rotate coding-agent account".'
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

- Perform only the account switch the caller explicitly authorized; rotation
  mutates host credential state and is never implied by repository access.
- The credential tool is caller- or operator-selected per host and agent family;
  the names below are this operator's routes, not a universal prescription. On
  macOS with Claude credentials the route is `claude-acct` (Keychain-backed);
  file-backed Codex, Gemini, Linux, or WSL credentials use `caam`. Never use
  `caam` for macOS Claude account operations.
- Verify account identity through the target runtime; token bytes are not account
  identity.
- If neither the selected credential tool nor a runtime identity probe is
  available, report that absence as a disclosed fact and stop. Never fall back to
  diffing credential-file bytes to declare a switch done.
- Existing processes retain credentials already loaded in memory. Rotation
  affects a new process.
- This skill does not restart work, resume a task, select a pane, move repository
  state, or decide what happens after the switch.

Return the host, agent family, selected tool, requested account/profile, the
identity observed before and after the switch, whether any live runtime still
holds the previous account (a partial rotation), the command exit code, and
whether a new process is required for the new identity to hold.
