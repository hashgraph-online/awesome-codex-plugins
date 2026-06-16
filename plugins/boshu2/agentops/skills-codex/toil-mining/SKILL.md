---
name: toil-mining
description: "Mine usage history (session archaeology, rtk analytics, shell history) for repeated toil, score frequency x pain, and emit ranked automation candidates."
---

# toil-mining (Codex)

Codex-native entry point for the `toil-mining` operator skill.

The AgentOps source skill `../../skills/toil-mining/SKILL.md` is the source of
truth for domain behavior: the evidence sources, clustering and scoring rules,
the machine-echo filter, and the ranked candidate handoff to
automation-shape-routing. Read it first, then use `prompt.md` for the Codex
runtime profile.

## Codex Runtime Contract

- Use Codex plus the local shell. Do not invoke Claude Code as an executor.
- Headless or scheduled dispatch uses `codex exec` (or the local llama lane), never `claude -p`.
- Read evidence sources read-only; never rewrite or prune session archives,
  analytics DBs, or shell history.
- Load only the relevant source references or scripts for the task.
- Verify command syntax from local `--help` or checked-in references before acting.
- Return concrete evidence: commands run, files touched, exit codes, and any remaining blocker.
