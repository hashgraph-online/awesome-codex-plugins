---
title: Package Runner
impact: MEDIUM
tags: supply-chain, runner, security, pnpm, bun, npm
---

**Rule**: Use the package runner that matches the project's package manager so ephemeral package executions go through the same store, registry config, and integrity pipeline as regular installs.

### Runner Mapping

| Detected PM | Native runner | Replace these mismatches |
|-------------|---------------|--------------------------|
| pnpm | `pnx` | `npx`, `bunx` → `pnx` |
| bun | `bunx` | `npx` → `bunx` |
| npm | `npx` | `bunx` → `npx` |
| yarn (v2+) | `yarn dlx` | `npx`, `bunx` → `yarn dlx` |
| yarn (v1) | `npx` | `bunx` → `npx` (yarn v1 has no `dlx`) |

Detect yarn version: `.yarnrc.yml` present → v2+; only `.yarnrc` or neither → v1.

### Detection

Scan for mismatched runners across:
- `package.json` (`scripts`, `prepare`, `postinstall`, etc.)
- `.github/workflows/*.yml`
- Shell scripts (`**/*.sh`)
- `Makefile`
- Markdown docs (`README.md`, `CLAUDE.md`, `docs/**/*.md`) — flag but do not auto-rewrite (see Tradeoff)

Skip if no mismatches are found.

### Fix

Apply rewrites using the mapping above. Auto-rewrite `package.json`, workflows, shell scripts, and Makefiles.

For markdown documentation files, **report** occurrences and suggest updating, but ask before rewriting — docs may intentionally use `npx` as a universal example for readers not using this project's package manager.

### Tradeoff

- In CI, ensure the package manager is installed before any step using its runner (e.g., `pnpm/action-setup` before `pnx`, or `oven-sh/setup-bun` before `bunx`).
- Public-facing docs that teach general users may intentionally use `npx` as the lowest-common-denominator. Review these manually.

### Why This Matters

Using a foreign runner (e.g., `npx` in a pnpm project) bypasses the project's store integrity, `.npmrc` registry lockdown, and audit pipeline. A typosquatted or compromised package run via `npx` can execute even in a project with pinned deps, a locked registry, and full audit CI. Matching the runner to the package manager closes this bypass lane and ensures all package executions — installed or ephemeral — go through the same security controls.
