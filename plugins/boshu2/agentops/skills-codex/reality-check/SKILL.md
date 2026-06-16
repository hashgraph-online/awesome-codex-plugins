---
name: reality-check
description: "Mid-epic strategic drift audit: code is ground truth, README/PRODUCT.md/plan docs are the measuring stick; emit a cited gap report and a routing decision."
---

# reality-check (Codex)

Codex-native entry point for the `reality-check` operator skill.

The AgentOps source skill `../../skills/reality-check/SKILL.md` is the source
of truth for domain behavior: the audit procedure, the gap-report format under
`.agents/reality-check/`, the citation requirements, and the routing of every
bridge through discovery and beads-workflow. Read it first, then use
`prompt.md` for the Codex runtime profile.

## Codex Runtime Contract

- Use Codex plus the local shell. Do not invoke Claude Code as an executor.
- Audit-only: never patch code, edit beads, or rewrite vision docs inline from
  this skill.
- Load only the relevant source references or scripts for the task.
- Verify command syntax from local `--help` or checked-in references before acting.
- Return concrete evidence: commands run, files touched, exit codes, and any remaining blocker.
