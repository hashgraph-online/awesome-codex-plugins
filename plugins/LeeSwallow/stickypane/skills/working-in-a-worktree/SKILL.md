---
name: working-in-a-worktree
description: Use when you work in a git worktree (your own branch beside the user's or other agents'), so your notes go in your worktree's book on the shared stickypane board and the user can tell the agents apart.
metadata:
  cases: worktree-B1
---

# Working in a worktree

```sh
stickypane worktree list                    # name, state, branch, forms waiting, path
stickypane worktree show chart              # yours: the one whose path is where you are
stickypane todo add worktrees/chart/todo "draw the axis"
stickypane log add worktrees/chart/worklog --time "axis drawn, 3 tests added"
```

Shapes: a book per worktree, `worktrees/<name>/`, in the `worktrees` tab;
in it, the same checklists, logs and forms as anywhere.

Every worktree of a repository uses one board, the main worktree's
`.sticky/`; a command run in your worktree finds it. Your book is named
after your worktree's folder (`chart` for `.claude/worktrees/chart`) and
is made at your first write into it, with an overview page,
`00-개요.md`, that the board keeps: its branch and its state.

## How

- Find your name once, at the start: the line of `stickypane worktree
  list` whose path is your working folder.
- Put every note of your task under `worktrees/<name>/`: the steps, the
  log, the forms. A note at the top of the board is everyone's.
- Do not write `00-개요.md`; the board writes it.
- Chat with your own name, the worktree's: `stickypane chat add
  worktrees/chart/chat --as chart "..."`.
- Merging the branches is the user's.
- `${CLAUDE_PLUGIN_ROOT}/rules/touching-the-board.md` applies.

## Recipes

- `references/waiting-for-the-user.md`: ask in your book, so the board shows that you wait.
- `references/two-worktrees-one-file.md`: another worktree changes a file you change.
