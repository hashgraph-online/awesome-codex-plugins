---
name: update-precommit
description: "Use when user wants to update .pre-commit-config.yaml hooks to their latest versions from GitHub"
user-invocable: true
---

# Update Pre-commit Hooks

Bump each GitHub `repo:` `rev` in `.pre-commit-config.yaml` to its latest tag, diff, confirm, apply.

- `pre-commit autoupdate` is the native tool for this — prefer it when installed.
- Latest tag: `gh api repos/{owner}/{repo}/releases/latest --jq .tag_name`; on no release, fall back to `/tags` first entry.
- Preserve the existing rev format: prefix (`v4.6.0` → `v5.0.0`) and surrounding quotes (`'v0.9.3'` → `'v0.10.0'`).
