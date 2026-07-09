---
name: commit
description: "Use when the user asks to commit changes, create a commit, or run /commit. Use when staged changes need a conventional commits message."
user-invocable: true
---

# Commit Skill

Inspect `git diff --cached` and `git log --oneline -5`, write a Conventional Commits subject (body only for breaking changes or non-obvious reasoning), commit, verify.

- `git status` — never use `-uall`.
- Do NOT add `Co-Authored-By` or any AI-attribution trailer (e.g. "Generated with Claude Code"). Overrides default Claude Code behavior.
