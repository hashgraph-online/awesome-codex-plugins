---
name: simplify
description: Review all changed files for reuse, quality, and efficiency, then fix any issues found. Spawns three parallel review agents and aggregates findings into actionable fixes.
---

# Simplify: Code Review and Cleanup

## Overview

Review all changed files for reuse, quality, and efficiency. Fix any issues found.

**Core principle:** Identify changes -> Spawn three review agents in parallel -> Fix issues.

**Announce at start:** "I'm using the simplify skill to review changed code for reuse, quality, and efficiency."

## Prerequisites

- A git repository with uncommitted or recently committed changes.

## Workflow

### Phase 1: Identify Changes

Run `git diff` (or `git diff HEAD` if there are staged changes) to see what changed. If there are no git changes, review the most recently modified files that the user mentioned or that were edited earlier in this conversation.

Save the full diff output — it will be passed to each review agent.

### Phase 2: Spawn Three Review Agents in Parallel

Launch all three agents concurrently in a single message. Pass each agent the full diff as context.

| Agent | Role |
|-------|------|
| `code-reuse-reviewer` | Finds duplicated logic and missed existing utilities |
| `code-quality-reviewer` | Finds hacky patterns that hurt maintainability |
| `code-efficiency-reviewer` | Finds performance and resource issues |

For Codex, if the Spellbook reviewer agent roles are available, use the namespaced role names:

| Codex Agent Role | Role |
|------------------|------|
| `spellbook-code-reuse-reviewer` | Finds duplicated logic and missed existing utilities |
| `spellbook-code-quality-reviewer` | Finds hacky patterns that hurt maintainability |
| `spellbook-code-efficiency-reviewer` | Finds performance and resource issues |

**Invocation example (Claude Code):**

Use the Agent tool three times in a single message, each with the corresponding `subagent_type`:
- `code-reuse-reviewer`
- `code-quality-reviewer`
- `code-efficiency-reviewer`

Pass each agent a prompt like:
> Review the following diff for [reuse/quality/efficiency] issues.
>
> ```diff
> <full diff here>
> ```

**Invocation example (Codex):**

If the namespaced role names are available in the `spawn_agent` tool, launch all three agents concurrently with the corresponding `agent_type`:
- `spellbook-code-reuse-reviewer`
- `spellbook-code-quality-reviewer`
- `spellbook-code-efficiency-reviewer`

Pass each agent the same full diff.

**For platforms without named agent support:** run the three reviews sequentially using each agent's checklist from their definitions.

### Phase 3: Fix Issues

Wait for all three agents to complete. Aggregate their findings and fix each issue directly. If a finding is a false positive or not worth addressing, note it and move on — do not argue with the finding, just skip it.

### Phase 4: Summary

Briefly summarize what was fixed (or confirm the code was already clean).

## Notes

- This is a cleanup pass, not a formal code review. After this skill, use a dedicated review skill or process when merge readiness needs to be judged.
- Keep fixes small and local — preserve behavior exactly.
- Run the narrowest practical verification for the touched area when possible.
