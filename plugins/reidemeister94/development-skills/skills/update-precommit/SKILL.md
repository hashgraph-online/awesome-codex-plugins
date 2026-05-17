---
name: update-precommit
description: "Use when user wants to update .pre-commit-config.yaml hooks to their latest versions from GitHub"
user-invocable: true
---

# Update Pre-commit Hooks

Updates `.pre-commit-config.yaml` with latest hook versions from GitHub while preserving the existing tag format.

## How It Works

For each repo entry in `.pre-commit-config.yaml`:

1. **Extract the GitHub repo URL and current `rev` tag**
2. **Query GitHub API** for the latest release/tag
3. **Update `rev`** to the latest tag, preserving the prefix format (e.g., `v` prefix)

## Execution Steps

1. Read `.pre-commit-config.yaml` from the current project root
2. For each `repo:` entry:
   - Skip `local` repos or non-GitHub URLs
   - Parse the repo URL to get `owner/repo`
   - Fetch the latest tag via GitHub API: `https://api.github.com/repos/{owner}/{repo}/releases/latest` → extract `tag_name`
   - If `gh` CLI is available, prefer: `gh api repos/{owner}/{repo}/releases/latest --jq .tag_name`
   - If no release exists, fall back to tags endpoint: `https://api.github.com/repos/{owner}/{repo}/tags` → first entry's `name`
   - Compare current `rev` with latest tag
3. Show diff of proposed changes
4. Apply changes after user confirmation

## Tag Format Rules

Preserve the existing tag format:
- If current rev is `v4.6.0` and latest is `v5.0.0` → use `v5.0.0`
- If current rev is `'v0.9.3'` (quoted) and latest is `v0.10.0` → use `'v0.10.0'` (preserve quotes)

## Skip These Entries

- `repo: local` (local hooks)
- Non-GitHub URLs
- `repo: meta`

## Example Output

```
Checking .pre-commit-config.yaml for updates...

Repo                                        Current      Latest       Status
pre-commit/pre-commit-hooks                 v5.0.0       v5.0.0       OK
commitizen-tools/commitizen                 v4.8.0       v4.10.1      UPDATE → v4.10.1
charliermarsh/ruff-pre-commit               v0.11.0      v0.14.10     UPDATE → v0.14.10

Apply updates? [y/N]
```
