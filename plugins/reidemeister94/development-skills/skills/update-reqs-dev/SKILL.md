---
name: update-reqs-dev
description: "Use when user wants to update requirements-dev.in with latest PyPI versions while preserving version patterns"
user-invocable: true
---

# Update Dev Requirements

Updates `requirements-dev.in` with latest package versions from PyPI while preserving version specifier patterns.

## How It Works

For each package in `requirements-dev.in`:

1. **Parse the version pattern** to understand the "fixed part":
   - `pytest==8.*` → fixed: `8`, wildcard at minor level
   - `ruff==0.*` → fixed: `0`, wildcard at minor level
   - `pytest-cov==7.*` → fixed: `7`, wildcard at minor level

2. **Query PyPI** for the latest version

3. **Update while preserving pattern**:
   - `pytest==8.*` with latest `8.4.0` → `pytest==8.*` (already allows 8.x)
   - `ruff==0.*` with latest `0.9.2` → `ruff==0.*` (already allows 0.x)

## Execution Steps

1. Read `requirements-dev.in` from the current project
2. For each line with a package version:
   - Skip git dependencies (lines with `@` or `git+`)
   - Parse package name and version pattern
   - Fetch latest version from PyPI: `curl -s https://pypi.org/pypi/{package}/json | jq -r .info.version`
   - Calculate new version with same pattern depth
3. Show diff of proposed changes
4. Apply changes after user confirmation

## Version Pattern Rules

| Original | Latest on PyPI | Result |
|----------|----------------|--------|
| `pkg==1.2.*` | `1.5.3` | `pkg==1.5.*` |
| `pkg==1.*` | `2.3.0` | `pkg==2.*` |
| `pkg==1.2.3` | `1.5.3` | `pkg==1.5.3` |

## Skip These Lines

- Git dependencies: `pkg @ git+https://...`
- Comments: Lines starting with `#`
- Empty lines
- Extras without version: `pkg[extra]`

## Example Output

```
Checking requirements-dev.in for updates...

Package          Current    Latest     Status
pytest           8.*        8.4.0      OK (already matches)
ruff             0.*        0.9.2      OK (already matches)
commitizen       4.*        4.5.0      OK (already matches)

Apply updates? [y/N]
```
