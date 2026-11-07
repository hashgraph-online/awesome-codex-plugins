# Agent Parallelism

Use this rule when the commit mode of `hyper-git` is active and the dirty tree is complex enough that Claude Code or Codex subagents can reduce analysis time without touching git state.

## When To Delegate

Spawn parallel read-only agents only when at least one condition is true:

- multiple repositories are in scope
- multiple logical commit groups are likely
- the diff is large enough that grouping, safety review, and message drafting can run independently
- the user explicitly asks to use parallel agents

Do not spawn agents for a single obvious one-file or one-group commit; coordination overhead is usually slower than direct execution.

## Safe Agent Lanes

| Lane | Responsibility | Inputs | Output | Edit/stage/commit? |
|------|------|------|------|------|
| Repo Mapper | Map repositories/worktree roots, staged/unstaged/untracked files, and ownership boundaries | `git-fast.sh inspect` output, `git diff --name-only` | repo/file map, linked-worktree context, and ambiguity list | no |
| Grouping Critic | Propose logical commit groups and flag unrelated files or secrets | status, file list, diff summaries | group plan with confidence and exclusions | no |
| Message Drafter | Draft English Conventional Commit subjects/bodies | group plan and diff summaries | message candidates with rationale | no |
| Safety Verifier | Check secrets, destructive operations, protected branch, detached HEAD, upstream/push risk | status, branch/upstream output, script diff | pass/block report | no |
| Main Integrator | Resolve conflicts between lanes, stage, commit, push, and report | all lane outputs | actual commits and push summary | yes |

## Hard Boundaries

- Subagents may inspect files, run read-only commands, and propose decisions.
- Subagents must not run `git add`, `git commit`, `git push`, `git reset`, `git rebase`, `git clean`, or `git restore`.
- Same-repository staging and commit must remain single-owner because the git index and staged set are shared.
- Push waits until every intended commit group succeeds.
- The main integrator owns final grouping, message selection, staging, commit execution, and push.

## Runtime Notes

- Claude Code: use task-specific subagents for independent lanes and coordinate results through the lead agent.
- Codex: use native/project-local subagents when available for bounded read-only lanes.
- Project-local agent definitions may be added later under `.claude/agents/` or `.codex/agents/`, but this skill must not depend on home/global agent directories.
- If the runtime cannot spawn subagents, use the same lane checklist manually in the main context.

## Delegation Prompt Templates

Use these templates as copy-ready prompts. Replace bracketed fields with the current inspect output or file list. Every lane is read-only.

### Repo Mapper

```text
Read-only hyper-git commit-mode repo mapping. Do not edit, stage, commit, push, or restore files.
Input: [paste git-fast inspect output and optional git diff --name-only].
Return: repositories/worktree roots in scope, staged/unstaged/untracked files by repo, linked-worktree context if present, ownership boundaries, and ambiguity list.
```

### Grouping Critic

```text
Read-only hyper-git commit-mode grouping review. Do not edit, stage, commit, push, or restore files.
Input: [paste status, file list, and focused diff summaries].
Return: proposed logical commit groups, files included in each group, exclusions, confidence, and any secret/unrelated-change concerns.
```

### Message Drafter

```text
Read-only hyper-git commit-mode commit message drafting. Do not edit, stage, commit, push, or restore files.
Input: [paste final or candidate group plan and diff summary].
Return: English Conventional Commit subject/body candidates for each group, with rationale: imperative subjects, lowercase after the colon, no trailing period, at most 72 characters, no fabricated issue footers, and no sign-off or attribution trailers unless requested.
```

### Safety Verifier

```text
Read-only hyper-git commit-mode safety verification. Do not edit, stage, commit, push, or restore files.
Input: [paste branch/upstream/status output, changed file list, and changed hyper-git script diff if this run modifies scripts].
Return: pass/block verdict for secrets, destructive git operations, protected branch force-push risk, detached HEAD, upstream risk, and missing validation.
```

## Conflict Resolution

| Conflict | Resolution |
|------|------|
| Grouping Critic and Message Drafter disagree | prefer the grouping evidence; rewrite message after final group selection |
| Safety Verifier reports a blocker | stop mutation and report the blocker |
| Repo Mapper finds repo boundary mismatch | re-run focused inspect before staging |
| Agent output is stale after edits/hooks | refresh status and revalidate before push |

## Sources

> No external sources were used. Content checked 2026-09-22.

This rule set is authored in this package from repository practice. It makes no external claim, so no external source is cited.
