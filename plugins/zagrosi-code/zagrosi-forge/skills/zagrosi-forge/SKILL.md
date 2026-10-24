---
name: zagrosi-forge
description: Take a software request through the appropriate Forge workflow, from a brief or existing plan to verified code. Use for end-to-end feature work, fixes, or continuing Forge work in Codex or Claude Code.
allowed-tools:
  - Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/zagrosi_skills.py" team status *)
  - Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/zagrosi_skills.py" status *)
  - Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/zagrosi_skills.py" next-section *)
  - Bash(python "${CLAUDE_PLUGIN_ROOT}/scripts/zagrosi_skills.py" team status *)
  - Bash(python "${CLAUDE_PLUGIN_ROOT}/scripts/zagrosi_skills.py" status *)
  - Bash(python "${CLAUDE_PLUGIN_ROOT}/scripts/zagrosi_skills.py" next-section *)
  - Bash(py -3 "${CLAUDE_PLUGIN_ROOT}/scripts/zagrosi_skills.py" team status *)
  - Bash(py -3 "${CLAUDE_PLUGIN_ROOT}/scripts/zagrosi_skills.py" status *)
  - Bash(py -3 "${CLAUDE_PLUGIN_ROOT}/scripts/zagrosi_skills.py" next-section *)
---

# Forge

For a Git target, check `team status --target-dir "{target_dir}"` with Forge’s
helper before work or resume.
Follow [team coordination](references/collaboration.md) when configured or unavailable;
reuse the same task across phases and delegated agents.

Resolve absolute `plugin_root`: the plugin directory two levels above this skill's
folder, containing `scripts/zagrosi_skills.py`; never the target repo. Claude Code
substitutes it when loading this skill: `${CLAUDE_PLUGIN_ROOT}`. Literal text there
means the file was read directly: derive the path; no such shell variable exists.
Run every helper command, including returned argv arrays, with the exact prefix
`python3 "{plugin_root}/scripts/zagrosi_skills.py"` (Python 3.11+; `python` or
`py -3` on Windows); host pre-approvals match that text.

Choose the shortest route that completes the user's request. Inspect repository
instructions, the working tree, relevant callers/tests, and any existing Forge
artifacts before creating new ones. Preserve unrelated work.

## Route once

| Starting point | Load |
|---|---|
| Several independent products or planning units | [Project](../zagrosi-project/SKILL.md), then each ready unit |
| Feature, bug, or coherent change without an admitted plan | [Plan](../zagrosi-plan/SKILL.md), then Implement |
| Unfinished or unadmitted plan | [Plan](../zagrosi-plan/SKILL.md); finish its existing contract |
| Admitted plan or interrupted implementation | [Implement](../zagrosi-implement/SKILL.md); resume persisted progress |
| Simplify a repository or remove accumulated bad code | [Cleanup](../zagrosi-cleanup/SKILL.md) |

Load a phase by invoking its skill, such as `zagrosi-forge:zagrosi-plan`, where the
host supports skill invocation; otherwise read and follow its `SKILL.md`.

For a small change, keep one compact section; do not split it into a project.
Use `lean` unless the user requests `standard`/`deep` or material risk warrants
more investigation. Explain a depth change briefly. Every depth preserves the
same behavior, ownership, and verification obligations. [State-first](../zagrosi-implement/references/state-first.md)
lean is opt-in: use it only when the user asks or `status.json` already exists.

An implementation request authorizes moving through planning and implementation;
continue without asking again at each phase. A plan, audit, or review-only request
stops at that deliverable. Ask only about unresolved decisions that materially
affect the result. Existing user authorization governs commits and publication.

## Quality and review

Apply the shared [engineering standard](../zagrosi-implement/references/engineering.md)
throughout. Repair encountered bad code within the task's execution path, with
before/after behavioral checks. Before delivery, review the changed code and
relevant callers once for unnecessary complexity and regressions. Record broader
debt separately instead of expanding a completed PR indefinitely.

When the user requests multiple providers/models, or another provider's perspective
addresses a concrete risk, use [provider reviews](references/providers.md).
Keep one primary writer and consolidate findings into the existing review.
Never substitute another provider/model silently or treat reviewer agreement as
proof that tests pass.

Finish with the result, actual verification, remaining limitations, and the saved
artifact location. Distinguish code completion, PR/CI state, and deployment.
