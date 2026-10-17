---
name: dev-finish
description: Complete an implemented development branch through an authorized local commit/merge, push and PR, preservation, or discard. Inspect scope and applicable verification before delivery; respect an already selected action without repeating a menu. Does not replace implementation or review.
---

# Dev Finish

Complete the delivery action the user requested, using the actual Git state and evidence. Permission for one action does not imply permission for unrelated publication or cleanup.

## Load baseline

Read [references/dev-baseline.md](references/dev-baseline.md) before execution. Resolve paths relative to this skill directory.

## Preflight

Inspect the repository root, branch or detached HEAD, current commit, working-tree/index status, remotes, upstream, and worktrees as relevant. Preserve unrelated changes and partial staging. Do not stash, reset, or discard user work to obtain a clean tree.

Verify the files or commit to be delivered have appropriate passing checks and any required review. Existing evidence is usable when it still covers the exact relevant state; rerun affected checks after changes. `dev-verify` and `dev-code-review` may provide evidence when installed, but equivalent checks work without them.

Read the user's requested destination and existing authorization. If the action is already clear, prepare and execute it without another menu. If no finish action is specified, finish preflight first and ask for the single missing decision. Missing destination or ambiguous destructive scope requires clarification; a dirty tree alone does not.

Failures block claims of verified delivery and any repository-required gate. Resolve failures within authorized scope where possible. Preserving a branch or making an explicitly requested draft PR with disclosed failures may still be appropriate; do not label that state ready to merge.

## Commit and merge

For a requested local commit, inspect the exact intended staged diff and use a message based on those changes. Stage only authorized files or hunks; preserve unrelated index entries. When an unrelated staged change prevents forming the requested commit safely, clarify scope or use a safe isolated approach. A request for a commit does not authorize a push.

For a local merge, determine the target from the user's request, upstream/default-branch metadata, and repository conventions. A successful `merge-base` against `main` does not identify the intended destination by itself. Verify the target checkout/worktree is suitable, perform the authorized merge, and check the merged result. Resolve conflicts within scope; do not choose away another contributor's changes without understanding them.

Do not automatically `pull` or push the target as a hidden merge substep. Fetch when remote freshness is needed and permitted, then integrate only the intended changes. A merge alone does not authorize deleting branches or worktrees.

## Push and PR

Confirm the requested remote, source branch, and PR base from observed repository state. Check for an existing PR before creating a duplicate. Review the exact commits to be published, then push and create/update the PR when that action is authorized. Never force-push by default.

A requested PR normally authorizes the push needed to publish its branch; prior authorization remains valid. Use the repository's PR template, or a concise problem/change/validation description. Disclose unresolved test or review failures and use draft status when warranted. Keep the worktree available for follow-up review.

## Preserve or discard

For preservation, report branch/commit and path without changing them.

Before destructive cleanup, establish the exact branch, commits, path, uncommitted contents, and ownership. A vague "finish" request does not authorize deletion. If the user has already explicitly authorized discarding that exact work, do not require a magic confirmation word; otherwise present the concrete loss and request confirmation before deletion.

Clean up only task-owned branches/worktrees covered by authorization, after confirming required work is merged or intentionally discarded. Directory name alone does not prove ownership. Never remove a platform-managed workspace as routine cleanup; preserve it if ownership or external lifecycle requirements are unclear.

## Completion

Report the result appropriate to the action: commit hash, merge target, PR link, retained path, or exact discarded scope. Include relevant verification and any unfinished step. A tool command being launched or a PR existing is not evidence that merge or CI completed.

## Multi-Agent Note

The main agent controls Git mutations and user-facing delivery. Independent agents may review diffs or verify snapshots when delegation is permitted, but they do not independently push, merge, or delete shared work. Use `docs/multi-agent-policy.md` when this repository is available; standalone installations use the same ownership and authorization rules above.
