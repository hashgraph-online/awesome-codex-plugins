---
name: operationalize
description: "Distill rich gathered context (research output, recon reports, big learnings) into evidence-anchored rules and route each rule to its automation shape."
---

# operationalize (Codex)

Codex-native entry point for the `operationalize` operator skill.

The AgentOps source skill `../../skills/operationalize/SKILL.md` is the source
of truth for domain behavior: the distillation discipline, the rule-packet
format under `.agents/operationalize/`, and the routing handoffs to
skill-builder, workflow-builder, hooks, gates, beads, or playbooks. Read it
first, then use `prompt.md` for the Codex runtime profile.

## Codex Runtime Contract

- Use Codex plus the local shell. Do not invoke Claude Code as an executor.
- Distill-and-route only: emit the rule packet plus handoff stubs; never build
  the routed automations inline from this skill.
- Load only the relevant source references or scripts for the task.
- Verify command syntax from local `--help` or checked-in references before acting.
- Return concrete evidence: commands run, files touched, exit codes, and any remaining blocker.
