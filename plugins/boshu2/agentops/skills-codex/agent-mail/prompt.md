# Codex Execution Profile -- agent-mail

MCP Agent Mail for multi-agent coordination side-channel work. Use when agents need file leases, lane notifications, inboxes, acknowledgements, or conflict prevention. Keep durable work state, evidence, and closure in BR/beads; Agent Mail carries leases and pings.

## Steps

1. Read `../../skills/agent-mail/SKILL.md` and identify the exact task path, trigger, or command family that applies.
2. Load only the source `references/*` or `scripts/*` files needed for that path.
3. Confirm live command syntax with local `--help`, repo docs, or the source skill's evidence before running state-changing commands.
4. Execute with Codex-native tools: local shell, `rg`, `apply_patch`, repo scripts, and AgentOps/ACFS binaries as directed by the source skill.
5. Capture machine-checkable evidence: command, exit code, affected paths, validation output, and the BR/bead state updated for durable record.
6. If the source skill is still being upgraded by the Claude lane, do not rewrite it. Report the missing source-side contract and keep this Codex wrapper intact.

## Guardrails

- Do not use Claude Code, `claude -p`, or Claude-only tools as the executor from Codex.
- Do not invent command flags. Verify with `--help` or checked-in references.
- Do not treat mail threads as the source of truth for work status; reconcile conflicts in BR/beads first.
- Do not broaden scope beyond the requested operator action.
- Do not land source files into `~/dev/agentops`; staged generation belongs under `$HOME/acfs` until the orchestrator lands the batch.
- Keep backstage/operator terminology out of client-facing artifacts.
