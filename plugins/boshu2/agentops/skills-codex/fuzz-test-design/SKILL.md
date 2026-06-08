---
name: fuzz-test-design
description: "Run fuzz test design."
---

# fuzz-test-design (Codex)

Codex-native entry point for the `fuzz-test-design` operator skill.

The AgentOps source skill `../../skills/fuzz-test-design/SKILL.md` is the source of truth
for domain behavior, commands, examples, references, and output expectations.
Read it first, then use `prompt.md` for the Codex runtime profile.

## Codex Runtime Contract

- Use Codex plus the local shell. Use Codex and the local shell as the executor; avoid non-Codex runtime shells.
- Load only the relevant source references or scripts for the task.
- Prefer structured command surfaces when the source skill exposes them.
- Verify command syntax from local `--help` or checked-in references before acting.
- Return concrete evidence: commands run, files touched, exit codes, and any remaining blocker.
