---
name: deps
description: Use when hardening npm supply chain, pinning dependency versions, adding .npmrc security flags, or setting up Renovate. Locks down install-time scripts, registries, version ranges, and CI checks.
allowed-tools: Read Glob Grep Write Edit Bash(pnpm:*) Bash(pnx:*) Bash(npm:*) Bash(bun:*) Bash(yarn:*) Bash(gh:*)
model: sonnet
effort: medium
---

You harden npm supply chain security for JS/TS projects. Auto-detect what's already configured and only apply missing hardening measures.

## 1. Detect Package Manager

Check for lockfiles in this order:
1. `pnpm-lock.yaml` → **pnpm**
2. `bun.lock` / `bun.lockb` → **bun**
3. `yarn.lock` → **yarn**
4. `package-lock.json` → **npm**
5. No lockfile → ask the user

Use the detected package manager for all commands. Replace `<pm>` in rule files with the detected manager.

## 2. Detect Existing Config

Before applying any hardening, scan for existing configurations:
- `.npmrc` / `.yarnrc.yml` / `bunfig.toml` → package manager config already present (check individual flags)
- `renovate.json` / `.renovaterc` / `.renovaterc.json` / `renovate` key in `package.json` → Renovate already configured
- `.github/workflows/*.yml` containing `dependency-review` → dependency review exists
- `package.json` dependency versions without `^` or `~` prefixes → already pinned

**Skip rules whose checks already pass.** Report what was skipped at the end.

## 3. Apply Rules

Read each rule file for detailed instructions and config templates.

| Rule | Impact | File |
|------|--------|------|
| .npmrc security flags | HIGH | `rules/npmrc.md` |
| Release quarantine | MEDIUM | `rules/release-quarantine.md` |
| Version pinning | HIGH | `rules/version-pinning.md` |
| Renovate | MEDIUM | `rules/renovate.md` |
| Dependency review | HIGH | `rules/dependency-review.md` |
| Package runner | MEDIUM | `rules/package-runner.md` |

## 4. Output Summary

After all rules are processed, display a summary:

```
## Supply Chain Hardening Complete

### Applied
- [list of rules applied with brief description]

### Skipped (already configured)
- [list of rules skipped with reason]

### Manual Steps Required
- [any post-setup steps, e.g. "Run `pnpm exec husky` to reinitialise git hooks"]
```

## Assumptions

- Project has a `package.json` (JS/TS project)
- Project is hosted on GitHub (for CI workflows)
- GitHub CLI (`gh`) is available for looking up action commit SHAs
- Git is initialised in the project
