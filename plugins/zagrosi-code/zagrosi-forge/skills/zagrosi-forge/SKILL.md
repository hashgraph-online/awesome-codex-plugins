---
name: zagrosi-forge
description: Take a software request through the appropriate Forge workflow, from a brief or existing plan to verified code. Use for end-to-end feature work, fixes, or continuing Forge work in Codex or Claude Code.
---

# Forge

For a Git target, check `team status --target-dir "{target_dir}"` with Forge’s
helper before work or resume.
Follow [team coordination](references/collaboration.md) when configured or unavailable;
reuse the same task across phases and delegated agents.

Choose the shortest route that completes the user's request. Inspect repository
instructions, the working tree, relevant callers/tests, and any existing Forge
artifacts before creating new ones. Preserve unrelated work.

## Route once

| Starting point | Read and follow |
|---|---|
| Several independent products or planning units | [Project](../zagrosi-project/SKILL.md), then each ready unit |
| Feature, bug, or coherent change without an admitted plan | [Plan](../zagrosi-plan/SKILL.md), then Implement |
| Unfinished or unadmitted plan | [Plan](../zagrosi-plan/SKILL.md); finish its existing contract |
| Admitted plan or interrupted implementation | [Implement](../zagrosi-implement/SKILL.md); resume persisted progress |
| Simplify a repository or remove accumulated bad code | [Cleanup](../zagrosi-cleanup/SKILL.md) |

For a small change, keep one compact section; do not split it into a project.
Use `lean` unless the user requests `standard`/`deep` or material risk warrants
more investigation. Explain a depth change briefly. Every depth preserves the
same behavior, ownership, and verification obligations.

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

When the user requests multiple providers/models, or an independent perspective
addresses a concrete risk, use [provider reviews](references/providers.md).
Keep one primary writer and consolidate findings into the existing review.
Never substitute another provider/model silently or treat reviewer agreement as
proof that tests pass.

Finish with the result, actual verification, remaining limitations, and the saved
artifact location. Distinguish code completion, PR/CI state, and deployment.
