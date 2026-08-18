---
name: commit
description: "Create a user-requested Conventional Commit from the staged changes."
user-invocable: true
---

# Commit Skill

Inspect `git diff --cached` and `git log --oneline -5`, write a Conventional Commits subject (body only for breaking changes or non-obvious reasoning), commit, verify.

- `git status` — never use `-uall`.
- Do NOT add `Co-Authored-By` or any AI-attribution trailer (e.g. "Generated with Claude Code"). Overrides default Claude Code behavior.
