---
name: local-files
description: "Development-file storage rule for skills that write plans, reports, specs, handovers, or work ledgers. Names the directories Quiver writes and how each one is kept out of git on first write, unless the directory is already tracked or the project says to track it."
user-invocable: false
---

# Local Development Files

Reference skill read by every skill that writes into one of the directories below, at its write step. It is never invoked and never runs a command itself: the writer applies the rule here before its own first write.

## Directories

| Directory | Written by |
|-----------|------------|
| `.claude/plans/` | `/plan`, `/quiver:design` (with `assets/` for its screenshots), `/ship` |
| `.claude/reports/` | `/quiver:review` (default location only), `/senior-review`, `/ship` |
| `.claude/specs/` | `/brainstorm`, `/ship` (one spec per phase), and `visual-companion` mockups copied beside a spec |
| `.claude/handovers/` | `/handover`, the PreCompact hook |
| `.claude/work/` | `/work` and its orchestrator |
| `.claude/ship/` | `/ship` |

A review written to a path the user chose with `--output` or `--set-output` is the user's location, not one of these, and the rule does not apply to it.

## Keep-Local Rule

Apply once per directory per run, before the first write into it. `<dir>` is the directory's path relative to the project root, with no trailing slash.

1. Outside a git repository (`git rev-parse --git-dir` fails), do nothing.
2. When `git ls-files <dir>` prints anything, or the project's instructions (`CLAUDE.md`, `AGENTS.md`, or equivalent) say to track the directory, change nothing. Tracked files mean the project chose to keep them in git.
3. Otherwise, when `git check-ignore -q <dir>/x` exits 1, the directory is not ignored yet. When the exclude file already holds the exact line `<prefix><dir>/`, change nothing and print nothing: a `.gitignore` negation such as `!<dir>/` outranks the exclude file, so `check-ignore` keeps exiting 1 after the entry is in. Otherwise append the line `<prefix><dir>/` to the file printed by `git rev-parse --git-path info/exclude`, creating the file if it is missing. `<prefix>` is what `git rev-parse --show-prefix` prints, empty at the repo top: exclude patterns are relative to the repo top, and the project root can sit below it. When the file exists and does not end in a newline, write a newline first so the new line does not join the user's last line. Append, never rewrite: the file may hold the user's own lines. Then print:

   > Keeping <dir>/ out of git (added to .git/info/exclude).

4. When `git check-ignore -q <dir>/x` exits 0, the directory is already ignored; change nothing and print nothing. Any other exit, such as 128 when `<dir>` sits behind a symbolic link, is an error rather than an answer; change nothing and print nothing.

`.git/info/exclude` lives in the shared git directory, so one entry covers every worktree, and it changes no tracked file. `git check-ignore` honors it, so a second run finds the directory ignored and stays silent.

## For Skill Authors

A skill that writes into one of these directories names this file at its write step, in one sentence: "Before the first write, apply the keep-local rule in `skills/local-files/SKILL.md`." Never restate the rule in the consumer; a copy drifts from this one with no error. A new development directory is added to the table above in the same change that adds its writer.
