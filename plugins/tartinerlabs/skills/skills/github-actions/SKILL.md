---
name: github-actions
description: Use when adding CI/CD, creating workflows, auditing GitHub Actions, or fixing action pinning. Creates and audits workflows for SHA pinning and permissions.
allowed-tools: Read Glob Grep Edit Write Bash(gh:*)
model: sonnet
effort: high
context: fork
agent: general-purpose
---

## Mode Detection

Determine the mode based on context:
- **Create mode**: No `.github/workflows/` directory exists, or user explicitly asks to create/add a workflow
- **Audit mode**: `.github/workflows/*.yml` files exist, or user explicitly asks to audit/review/fix workflows

---

## Create Mode

### 1. Detect Project Type

Scan for project indicators:
- `package.json` → Node.js/JS/TS
- `go.mod` → Go
- `requirements.txt` / `pyproject.toml` / `setup.py` → Python
- `Cargo.toml` → Rust
- `Gemfile` → Ruby

### 2. Detect Package Manager (JS/TS projects)

- `pnpm-lock.yaml` → pnpm
- `bun.lock` / `bun.lockb` → bun
- `yarn.lock` → yarn
- `package-lock.json` → npm

### 3. Generate Workflow

Apply all rules from the `rules/` directory when generating workflows. Read each rule file for detailed requirements and examples.

### 4. Workflow Template

Adapt this CI template to the detected project type and package manager (replace `<pm>` with the detected package manager):

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 'lts/*'
          cache: '<pm>'
      - run: <pm> install --frozen-lockfile
      - run: <pm> check
      - run: <pm> test
      - run: <pm> build
```

---

## Audit Mode

### 1. Scan Workflows

Read all files in `.github/workflows/*.yml` and audit against every rule in the `rules/` directory.

### 2. Report Format

```
## GitHub Actions Audit Results

### HIGH Severity
- `.github/workflows/ci.yml:15` - `codecov/codecov-action@v4` → pin to commit SHA

### MEDIUM Severity
- `.github/workflows/ci.yml` - Missing concurrency group → add concurrency block

### Summary
- High: X
- Medium: Y
- Low: Z
- Files scanned: N
```

### 3. Auto-Fix

After reporting, apply fixes. Look up commit SHAs for pinning using `gh api`.

---

## Rules

Read individual rule files for detailed checks and examples:

| Rule | Severity | File |
|------|----------|------|
| Action pinning | HIGH | `rules/action-pinning.md` |
| Permissions | HIGH | `rules/permissions.md` |
| Concurrency | MEDIUM | `rules/concurrency.md` |
| Node version | MEDIUM | `rules/node-version.md` |
| Caching | MEDIUM | `rules/caching.md` |
| Triggers | LOW | `rules/triggers.md` |
| Matrix strategy | LOW | `rules/matrix.md` |

---

## Assumptions

- GitHub CLI (`gh`) is available for looking up action commit SHAs
- The project is hosted on GitHub
