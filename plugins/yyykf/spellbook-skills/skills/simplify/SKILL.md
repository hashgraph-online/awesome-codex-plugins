---
name: simplify
description: Review changed code for reuse, quality (simplification), efficiency, and altitude (root-cause depth), then fix issues found. Spawns four parallel review agents and aggregates findings into fixes. Cleanup only — not for bug hunting or merge-readiness review.
---

# Simplify: Code Review and Cleanup

## Overview

Review all changed files for reuse, quality, efficiency, and altitude. Fix any issues found.

**Core principle:** Identify changes -> Spawn four review agents in parallel -> Fix issues.

**Announce at start:** "I'm using the simplify skill to review changed code for reuse, quality, efficiency, and altitude."

## Prerequisites

- A git repository with uncommitted changes or commits not yet on the upstream/default branch.

## Workflow

### Phase 1: Identify Changes

If the user passed a PR number, branch name, or file path, review that target instead (for a PR, `gh pr diff <number>`).

Otherwise run `git diff @{upstream}...HEAD` (if there is no upstream, `git diff main...HEAD` against the default branch, or `git diff HEAD~1`) to see what this branch changed. If there are uncommitted changes, or the range diff is empty, also run `git diff HEAD` and include the working-tree changes — this skill often runs before the commit.

If there are no git changes at all, review the most recently modified files that the user mentioned or that were edited earlier in this conversation.

Save the full diff output — it will be passed to each review agent.

### Phase 2: Spawn Four Review Agents in Parallel

Launch all four agents concurrently in a single message. Pass each agent the full diff as context.

| Agent | Role |
|-------|------|
| `code-reuse-reviewer` | Finds duplicated logic and missed existing utilities |
| `code-quality-reviewer` | Finds unnecessary complexity and hacky patterns that hurt maintainability (simplification) |
| `code-efficiency-reviewer` | Finds performance and resource issues |
| `code-altitude-reviewer` | Finds symptom patches and special cases that should be fixed at the root cause |

For Codex, if the Spellbook reviewer agent roles are available, use the namespaced role names:

| Codex Agent Role | Role |
|------------------|------|
| `spellbook-code-reuse-reviewer` | Finds duplicated logic and missed existing utilities |
| `spellbook-code-quality-reviewer` | Finds unnecessary complexity and hacky patterns that hurt maintainability (simplification) |
| `spellbook-code-efficiency-reviewer` | Finds performance and resource issues |
| `spellbook-code-altitude-reviewer` | Finds symptom patches and special cases that should be fixed at the root cause |

**Invocation example (Claude Code):**

Use the Agent tool four times in a single message, each with the corresponding `subagent_type`:
- `code-reuse-reviewer`
- `code-quality-reviewer`
- `code-efficiency-reviewer`
- `code-altitude-reviewer`

Pass each agent a prompt like:
> Review the following diff for [reuse/quality/efficiency/altitude] issues.
>
> ```diff
> <full diff here>
> ```

**Invocation example (Codex):**

If the namespaced role names are available in the `spawn_agent` tool, launch all four agents concurrently with the corresponding `agent_type`:
- `spellbook-code-reuse-reviewer`
- `spellbook-code-quality-reviewer`
- `spellbook-code-efficiency-reviewer`
- `spellbook-code-altitude-reviewer`

Pass each agent the same full diff.

**For platforms without named agent support:** run the four reviews sequentially using each agent's checklist from their definitions.

### Phase 3: Fix Issues

Wait for all four agents to complete. Dedup findings that point at the same line or mechanism, then fix each remaining issue directly. Skip any finding whose fix would change intended behavior, require changes well outside the reviewed diff, or that you judge to be a false positive — note the skip and move on; do not argue with the finding.

### Phase 4: Summary

Briefly summarize what was fixed and what was skipped (or confirm the code was already clean).

## Notes

- This is a cleanup pass, not a formal code review — it does not hunt for correctness bugs. After this skill, use a dedicated review skill or process when merge readiness needs to be judged.
- Keep fixes small and local — preserve behavior exactly.
- Run the narrowest practical verification for the touched area when possible.
