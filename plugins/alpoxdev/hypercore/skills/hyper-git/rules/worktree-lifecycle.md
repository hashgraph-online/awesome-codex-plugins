# Worktree Lifecycle Rules

Use these rules when the worktree mode of `hyper-git` is active.

## 1. Repository discovery

Run from any descendant of the target repository:

```bash
git rev-parse --show-toplevel
git rev-parse --git-common-dir
git worktree list --porcelain
```

If not inside a Git repository, stop the operation and report that a repository path is required.

## 2. Task intent, naming, and paths

Default root:

```text
<repo-root>/.hyper/worktree/<folder_name>
```

Direct argument fast path:

- If the invocation is `hyper-git worktree <ARGUMENT>`, treat `<ARGUMENT>` as the create target and do not ask what worktree to create.
- Interpret the argument as a branch/task label unless it clearly denotes a PR, issue, ref, or explicit path.
- Preserve the branch/ref text for Git operations; sanitize only the folder label for `.hyper/worktree/<folder_name>`.
- Continue to ask only for unsafe, reserved, conflicting, or unmappable arguments.

Interaction language:

- Ask clarification questions in the same language as the user's request.
- For Korean users, ask in Korean only. Do not show English fallback text or generic English operation menus.
- Infer the operation from the user's wording before asking. If inference fails, ask one localized question. For Korean users, ask: "어떤 worktree 작업을 원하시나요? 생성, 목록, 열기/이동, 삭제, 정리, 복구, 잠금 중에서 알려주세요."
- If only the work intent for a new worktree is missing, ask about the work intent, not the operation. For Korean users, ask: "이 worktree에서 어떤 작업을 할 예정인가요?"

Before creating a worktree, establish what will happen there:

- If a direct `hyper-git worktree <ARGUMENT>` argument exists, it is the work intent; skip the work-intent question.
- If the user already named a branch, PR, issue, task, or concrete work item, use that context.
- If the user only says to create a worktree and the task is unclear, ask exactly one concise localized question before creating it. For Korean users, ask what work they plan to do in this worktree.
- Derive `<folder_name>` from the answer. Do not use a random timestamp or generic `worktree-1` unless the user explicitly wants that.

Naming rules:

- Prefer a short task label: `feature-auth`, `fix-login`, `review-pr-42`, `agent-docs-pass`.
- Preserve the real branch name separately from the folder name.
- Sanitize folder names with an explicit slug algorithm: lowercase the task label, replace `/`, whitespace, and shell-sensitive characters with `-`, collapse repeated separators, trim leading/trailing separators, and reject reserved labels such as `.`, `..`, `.git`, `main`, or an empty slug.
- If the sanitized slug is too generic (`worktree`, `task`, `new-worktree`), add one concrete noun from the user's stated intent before creating the folder.
- Cap very long labels to a readable length and add a numeric suffix when the target path already exists.
- Refuse paths outside the repository only when the user did not explicitly request them.
- Never create a worktree inside an existing linked worktree unless the user explicitly asks and understands the nesting risk.

Because this project’s requested convention nests worktrees under the repository, always ensure the root is ignored locally:

```bash
exclude_file="$(git rev-parse --git-path info/exclude)"
mkdir -p "$(dirname "$exclude_file")"
grep -qxF ".hyper/worktree/" "$exclude_file" 2>/dev/null || printf '\n.hyper/worktree/\n' >> "$exclude_file"
```

Prefer local excludes over editing `.gitignore` unless the user asks to commit the convention.

## 3. Create worktree

### New branch from current `HEAD`

```bash
git worktree add -b <branch> <path> HEAD
```

### New branch from a base branch

```bash
git fetch --all --prune
git worktree add -b <branch> <path> <base-ref>
```

### Existing local branch

```bash
git worktree add <path> <branch>
```

If Git reports the branch is already checked out elsewhere, list the existing worktree and open it instead of forcing a duplicate checkout.

### Existing remote branch

```bash
git fetch --all --prune
git worktree add --track -b <branch> <path> origin/<branch>
```

This creates the local tracking branch inside the new worktree without switching the current one. Do not use `git switch --track` here: it changes the user's current worktree.

### Detached review

```bash
git worktree add --detach <path> <commit-or-tag>
```

Use detached worktrees only for read-only inspection, bisect-like diagnostics, or explicit throwaway review.

After creation, verify the worktree exists and make it the active context for follow-up work. A create request that says "enter", "open", "switch", "go into it", "들어가", "이동", "전환", or equivalent Korean wording is not complete until follow-up commands run from the new path:

```bash
git -C <path> status --short --branch
# In a normal interactive shell:
cd <path> && pwd

# In persistent agent shells/sessions, actually run cd <path> there.
# In tool-only environments, run the next command with workdir=<path>, or use git -C <path>.
```

In persistent shells, tmux panes, or CLI sessions, "move into the worktree" means actually executing `cd <path>` in that active session and verifying `pwd`. In agent environments where `cd` in a subprocess cannot persist, fall back to setting the next and subsequent tool calls to `workdir=<path>` for this task, or using an equivalent tool working-directory field. Do not claim the active context moved if you only printed `cd <path>`. Report which move mechanism was used: persistent-session `cd <path>` or tool `workdir=<path>`.

## 4. Move, open, or hand off

After creation, switch the active agent context into the folder for subsequent work, then provide one or more available handoff commands:

```bash
cd <path>
pwd
code <path>
cursor <path>
tmux new-session -A -s <folder_name> -c <path>
```

For AI-agent workflows, hand off the task and boundaries explicitly:

- branch name
- worktree path
- target files or ownership boundary
- verification command
- merge/cleanup expectation

Do not start external editor or agent commands unless the user asked for it or the current skill invocation clearly includes that action. Moving the active agent command context to the new worktree is part of creation and does not require an extra confirmation.

## 5. List and status dashboard

Use both Git’s registry and per-worktree status:

```bash
git worktree list --porcelain
git worktree list --verbose
git worktree list --porcelain | awk '/^worktree / {print substr($0, 10)}' | while IFS= read -r p; do
  printf '\n== %s ==\n' "$p"
  git -C "$p" status --short --branch || printf 'missing path (check the prunable annotation)\n'
done
```

Report:

- path
- branch or detached commit
- clean/dirty state
- locked/prunable annotations
- recommended next action

## 6. Remove safely

Before removing:

```bash
git -C <path> status --short --branch
git -C <path> log --oneline --decorate -5
```

If the user asks to delete/remove the worktree while already inside it and no path is supplied, infer the current linked worktree as the target. Save the target path before moving out, refuse the main worktree, then remove from another safe worktree:

```bash
target_path="$(git rev-parse --show-toplevel)"
git_dir="$(git rev-parse --git-dir)"
common_dir="$(git rev-parse --git-common-dir)"
main_path="$(git worktree list --porcelain | awk 'NR==1 && /^worktree / {print substr($0, 10)}')"

# If git-dir and common-dir resolve to the same directory, this is the main worktree; do not remove it.
# Also stop when Git cannot provide a distinct safe worktree to run removal from.
if [ "$(cd "$git_dir" && pwd -P)" = "$(cd "$common_dir" && pwd -P)" ] || [ -z "$main_path" ] || [ "$main_path" = "$target_path" ]; then
  echo "Refusing to remove this path as a linked worktree: $target_path" >&2
  git worktree list --porcelain >&2
  exit 1
fi

git -C "$target_path" status --short --branch
git -C "$target_path" log --oneline --decorate -5
cd "$main_path"
git worktree remove "$target_path"
```

Do not run `git worktree remove .` or `rm -rf .` from inside the target worktree. If `main_path` cannot be resolved, stop and report the target path plus `git worktree list --porcelain` output instead of guessing.

Safe removal path:

```bash
git worktree remove <path>
```

Only use force when explicitly requested or when the user has already confirmed the changes are disposable. A dirty current-worktree deletion needs the same explicit force/discard intent before `--force`:

```bash
git worktree remove --force <path>
```

Branch deletion is separate and should be explicit:

```bash
git branch -d <branch>
# use -D only when explicitly requested and disposable
```

Never delete the main worktree. For pathless requests such as a Korean "delete worktree" request from inside the main worktree, stop and ask for the linked worktree path/name instead of treating the repository root as disposable.

## 7. Prune, lock, unlock, repair

Prune only after dry run:

```bash
git worktree prune --dry-run
git worktree prune
```

Lock long-lived or externally stored worktrees:

```bash
git worktree lock --reason "<reason>" <path>
git worktree unlock <path>
```

If paths were moved manually, repair before recreating:

```bash
git worktree repair <path>
```

Move a linked worktree with Git so its registry entry follows; a locked worktree must be unlocked first:

```bash
git worktree move <path> <new-path>
```

Scripts that parse the registry use `git worktree list --porcelain -z`, because a path may contain a newline.

## 8. Issue-backed worktrees

When the worktree is for a GitHub issue and `gh` is authenticated, `gh issue develop <n> --base <base> --name <branch> --worktree <path>` creates the linked branch and the worktree in one step (`rules/issue-workflow.md`). The path still follows section 2, and the exclude, verification, and context-move checks of section 3 still apply.

## 9. Merge-back handoff

When a worktree’s task is complete:

1. Verify status is clean or intentionally staged/committed.
2. Run the project’s tests/build in that worktree.
3. Merge, rebase, or open a PR according to the project’s workflow (`rules/branch-workflow.md`).
4. Remove the worktree only after work is merged, pushed, or intentionally abandoned. For a squash or cherry-pick merge, `git branch --merged` does not prove it; confirm with `git cherry <target> <branch>` showing no `+` lines or a merged pull request.
5. Prune stale metadata with a dry run first.

## 10. Common hazards

- Nested worktrees under `.hyper/worktree/` must be ignored locally or the main worktree becomes noisy.
- Same branch cannot normally be checked out in two worktrees at once.
- Linked worktrees share Git object storage and config but have independent working files.
- Per-worktree dependency folders, ports, databases, and generated artifacts may still collide; use separate env files or ports when needed.
- Windows/WSL path portability can break if a worktree is created by one Git executable and used by another.

## Sources

> Links checked 2026-11-07.

| Claim | Source |
|---|---|
| `git worktree add`, `list`, `move`, `remove`, `prune`, `lock`, `unlock`, `repair`, `--porcelain -z`, `--detach`, and the already-checked-out-branch error this rule set builds on | <https://git-scm.com/docs/git-worktree> |
| `gh issue develop --worktree` creating an issue branch and its worktree together | <https://cli.github.com/manual/gh_issue_develop> |
| `git rev-parse --show-toplevel`, `--git-dir`, `--git-common-dir`, and `--git-path info/exclude` used by the discovery and local-exclude steps | <https://git-scm.com/docs/git-rev-parse> |
| The local-exclude file semantics that keep `.hyper/worktree/` out of status output | <https://git-scm.com/docs/gitignore> |
| Why this package prefers native Git, one task per worktree, and checks before delete | [`../references/worktree-source-survey.md`](../references/worktree-source-survey.md) |
