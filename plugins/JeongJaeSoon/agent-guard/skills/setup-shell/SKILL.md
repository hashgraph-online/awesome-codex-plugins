---
name: setup-shell
description: Install or refresh Agent Guard's plugin-local shell integration. Use when the user explicitly asks to enable or update shell command masking, or when a shell-integration warning directs them to rerun setup-shell.
---

# Set Up Agent Guard Shell

Install or refresh Agent Guard shell command masking without making the user
locate the versioned plugin-cache binary.

## Workflow

1. Explain that this changes the user's shell rc and is separate from plugin
   hook setup.
2. Resolve `../../bin/agent-guard` relative to this skill directory and confirm
   that it is executable. Use that plugin-local binary even if another
   `agent-guard` is on `PATH`; do not install or update a standalone copy.
3. Tell the user that `setup-shell` will update the managed block in their shell
   rc with command wrapping enabled by default. Obtain host approval for the
   home-directory write before running:

   ```sh
   "<plugin-local-agent-guard>" setup-shell
   ```

4. On success, report the rc path from the command output and tell the user to
   restart the shell and any agent sessions launched from that shell.
5. If the approved write is blocked by the host sandbox, relay the exact error.
   Do not retry the same blocked write, choose another rc, or edit the rc by
   hand. Show the exact plugin-local command for the user to run directly in a
   terminal, wait for confirmation, and then report the required restarts.

Use `setup-shell --no-command-wrapping` only when the user explicitly requests
the persistent opt-out. `AGENT_GUARD_COMMAND_WRAPPING=off` is the runtime-only
opt-out.
