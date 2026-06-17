---
name: vibing-with-ntm
description: "Run vibing with NTM."
---

# vibing-with-ntm (Codex)

Codex-native entry point for the `vibing-with-ntm` operator skill.

The AgentOps source skill `../../skills/vibing-with-ntm/SKILL.md` is the source of truth
for domain behavior, commands, examples, references, and output expectations.
Read it first, then use `prompt.md` for the Codex runtime profile.

## Codex Runtime Contract

- Use Codex plus the local shell. Do not invoke Claude Code as an executor.
- Load only the relevant source references or scripts for the task.
- Prefer robot/JSON/NDJSON command surfaces when the source skill exposes them.
- Verify command syntax from local `--help` or checked-in references before acting.
- Treat peer gate requests (`ACTION NEEDED`, `Hey! Listen!`, merge-gate,
  unblock-condition, verdict/dry-run requests) as interrupts: answer the gate
  before broad watching, and surface the result where the peer can actually read
  it.
- For fresh Claude/Codex duel requests, load `$using-atm` and use ATM panes
  (`atm spawn ... --cc=1:opus --cod=1:gpt-5.5 --no-user`), Codex goal-flow
  verification, and `atm kill` cleanup. Never use print-mode CLIs for the
  other-family pane.
- Return concrete evidence: commands run, files touched, exit codes, and any remaining blocker.
