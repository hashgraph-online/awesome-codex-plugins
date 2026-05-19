---
name: update-reqs
description: "Use when user wants to update requirements.in with latest PyPI versions while preserving version patterns"
user-invocable: true
---

# Update Requirements

Updates `requirements.in` with latest package versions from PyPI while preserving version specifier patterns.

## How It Works

For each package in `requirements.in`:

1. **Parse the version pattern** to understand the "fixed part":
   - `fastapi==0.128.*` → fixed: `0.128`, wildcard at patch level
   - `pydantic==2.12.*` → fixed: `2.12`, wildcard at patch level
   - `commitizen==4.*` → fixed: `4`, wildcard at minor level

2. **Query PyPI** for the latest version

3. **Update while preserving pattern**:
   - `fastapi==0.128.*` with latest `0.130.0` → `fastapi==0.130.*`
   - `commitizen==4.*` with latest `4.5.0` → `commitizen==4.*` (already allows 4.x)

## Execution Steps

1. Read `requirements.in` from the current project
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
Checking requirements.in for updates...

Package          Current    Latest     Status
fastapi          0.128.*    0.130.2    UPDATE → 0.130.*
pydantic         2.12.*     2.12.1     OK (already matches)
uvicorn          0.40.*     0.41.0     UPDATE → 0.41.*
pyinnovation     (git)      -          SKIP (git dependency)

Apply updates? [y/N]
```
