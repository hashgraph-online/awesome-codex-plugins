---
name: continuity-loop
description: "Own the unattended renewal spine: renewal ticks, the two-tick stall rule, and escalation for NTM panes coordinated over MCP Agent Mail."
---

# continuity-loop (Codex)

Codex-native entry point for the `continuity-loop` operator skill.

The AgentOps source skill `../../skills/continuity-loop/SKILL.md` is the source
of truth for domain behavior: the tick contract, the two-tick stall rule,
lane-state semantics in `.agents/continuity/state.json`, and the escalation
path over Agent Mail. Read it first, then use `prompt.md` for the Codex
runtime profile.

## Codex Runtime Contract

- Use Codex plus the local shell. Do not invoke Claude Code as an executor.
- This skill is a contract, not a scheduler: tick firing is owned by host
  timing (cron, systemd user timers); never spawn a daemon from this skill.
- Load only the relevant source references or scripts for the task.
- Verify command syntax from local `--help` or checked-in references before acting.
- Return concrete evidence: commands run, files touched, exit codes, and any remaining blocker.
