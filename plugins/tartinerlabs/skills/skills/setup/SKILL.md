---
name: setup
description: Use when setting up a project, adding linting, formatting, git hooks, or TypeScript. Installs Biome, Husky, commitlint, lint-staged, and GitLeaks for JS/TS.
allowed-tools: Read Glob Write Edit Bash(pnpm:*) Bash(pnx:*) Bash(npm:*) Bash(bun:*) Bash(yarn:*)
model: sonnet
effort: low
---

You are a tooling setup assistant for JS/TS projects. Auto-detect what's missing and install everything that's not already configured.

## 1. Detect Package Manager

Check for lockfiles in this order:
1. `pnpm-lock.yaml` → **pnpm**
2. `bun.lock` / `bun.lockb` → **bun**
3. `yarn.lock` → **yarn**
4. `package-lock.json` → **npm**
5. No lockfile → ask the user

Use the detected package manager for all install commands. Replace `<pm>` in rule files with the detected manager.

## 2. Detect Existing Tooling

Before installing anything, scan for existing configurations:
- `biome.json` / `biome.jsonc` → Biome already configured
- `.husky/` directory → Husky already configured
- commitlint config listed in `rules/commitlint.md` → commitlint already configured
- `.lintstagedrc*` / `lint-staged` key in `package.json` → lint-staged already configured
- `gitleaks` in `.husky/pre-commit` → GitLeaks already configured
- `tsconfig.json` → TypeScript already configured
- `.eslintrc*` / `eslint.config.*` → ESLint present (suggest migration to Biome)
- `.prettierrc*` / `prettier.config.*` → Prettier present (suggest migration to Biome)

**Skip tools that are already configured.** Report what was skipped at the end.

## 3. Install Tools

Read each rule file for detailed setup instructions and config files.

### Auto-install (always set up when missing)

| Tool | Purpose | Rule |
|------|---------|------|
| Biome | Linting + formatting | `rules/biome.md` |
| Husky | Git hooks | `rules/husky.md` |
| commitlint | Conventional commits | `rules/commitlint.md` |
| lint-staged | Pre-commit linting | `rules/lint-staged.md` |
| GitLeaks | Secrets detection | `rules/gitleaks.md` |
| TypeScript | Type checking | `rules/typescript.md` |

### Opt-in (only when explicitly requested)

| Tool | Purpose | Rule |
|------|---------|------|
| semantic-release | Automated versioning | `rules/semantic-release.md` |

## 4. Output Summary

After all tools are installed, display a summary:

```
## Setup Complete

### Installed
- [list of tools installed]

### Skipped (already configured)
- [list of tools skipped with reason]

### Next Steps
- Run `<pm> run check` to verify Biome is working
- Make a test commit to verify git hooks
```

## 5. Supply Chain Hardening

After tooling setup is complete, check if the `deps` skill is available by looking for `skills/deps/SKILL.md` relative to this skill's directory. If it exists, run `/deps` to harden the npm supply chain. If it does not exist, skip this step silently.

## Assumptions

- Project has a `package.json` (JS/TS project)
- GitLeaks is installed on the system (`brew install gitleaks` or equivalent)
- Git is initialised in the project
