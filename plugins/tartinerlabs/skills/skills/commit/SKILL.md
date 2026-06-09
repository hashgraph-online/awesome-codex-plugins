---
name: commit
description: Use when committing changes, staging files, saving work, or making a git commit. Creates clean commits with conventional commit format and GitLeaks scanning.
allowed-tools: Read Bash(git:*)
model: sonnet
effort: low
---

You create git commits with short, readable messages.

Read ALL rule files before proceeding — do not skip or ask:

- `rules/message-format.md`
- `rules/issue-references.md`
- `rules/change-scope.md`

## Rules Overview

| Rule | Impact | File |
|------|--------|------|
| Message format | HIGH | `rules/message-format.md` |
| Issue references | MEDIUM | `rules/issue-references.md` |
| Change scope | MEDIUM | `rules/change-scope.md` |

## Pre-Commit Security Check

Before committing, ensure GitLeaks is configured:

1. Check for `.husky/pre-commit` containing `gitleaks protect`
2. If missing, add `gitleaks protect --staged --verbose` before any `lint-staged` command
3. If `.husky/` doesn't exist, run `pnx husky init` first

## Workflow

1. **Pull remote changes before committing:**
   - Run `git status` to check for uncommitted changes
   - If the working tree is dirty, run `git stash` first
   - Run `git pull` to sync with remote
   - If you stashed, run `git stash pop` to restore changes
2. Show current `git status` and analyse all changes
3. Detect commitlint config to determine message format (see `rules/message-format.md`)
4. Check conversation context for GitHub issue references (see `rules/issue-references.md`)
5. Assess scope of changes (see `rules/change-scope.md`)
6. Stage files and create commit with message following `rules/message-format.md`
