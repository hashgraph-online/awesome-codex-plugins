# Doc default mode — code/API docs, code-maps, coverage/validate

> **Provenance:** This is the default-mode workflow **moved verbatim** out of
> `skills/doc/SKILL.md` (generic-craft trim).
> Steps 1-7 below — grep for undocumented functions, stamp function/class markdown,
> compute coverage, write a report — are frontier-trivial: a capable model does them
> correctly with no skill payload. The skill's durable value is the references-led
> `--mode=readme` and `--mode=oss` modes, which stay in `SKILL.md`.
> This file is retained so the default mode still has a full spec to follow.

Given a Doc command and target:

## Step 1: Detect Project Type

```bash
# Check for indicators
ls package.json pyproject.toml go.mod Cargo.toml 2>/dev/null

# Check for existing docs
ls -d docs/ doc/ documentation/ 2>/dev/null
```

Classify as:
- **CODING**: Has source code, needs API docs
- **INFORMATIONAL**: Primarily documentation (wiki, knowledge base)
- **OPS**: Infrastructure, deployment, runbooks

## Step 2: Execute Command

**discover** - Find undocumented features:
```bash
# Find public functions without docstrings (Python)
grep -r "^def " --include="*.py" | grep -v '"""' | head -20

# Find exported functions without comments (Go)
grep -r "^func [A-Z]" --include="*.go" | head -20
```

**coverage** - Check documentation coverage:
```bash
# Count documented vs undocumented
TOTAL=$(grep -r "^def \|^func \|^class " --include="*.py" --include="*.go" | wc -l)
DOCUMENTED=$(grep -r '"""' --include="*.py" | wc -l)
echo "Coverage: $DOCUMENTED / $TOTAL"
```

**gen [feature]** - Generate documentation:
1. Read the code for the feature
2. Understand what it does
3. Generate appropriate documentation
4. Write to docs/ directory

**all** - Update all documentation:
1. Run discover to find gaps
2. Generate docs for each undocumented feature
3. Validate existing docs are current

## Step 3: Generate Documentation

When generating docs, include:

**For Functions/Methods:**
```markdown
## function_name

**Purpose:** What it does

**Parameters:**
- `param1` (type): Description
- `param2` (type): Description

**Returns:** What it returns

**Example:**
```python
result = function_name(arg1, arg2)
```

**Notes:** Any important caveats
```

**For Classes:**
```markdown
## ClassName

**Purpose:** What this class represents

**Attributes:**
- `attr1`: Description
- `attr2`: Description

**Methods:**
- `method1()`: What it does
- `method2()`: What it does

**Usage:**
```python
obj = ClassName()
obj.method1()
```
```

## Step 4: Create Code-Map (if requested)

**Write to:** `docs/code-map/`

```markdown
# Code Map: <Project>

## Overview
<High-level architecture>

## Directory Structure
```
src/
├── module1/     # Purpose
├── module2/     # Purpose
└── utils/       # Shared utilities
```

## Key Components

### Module 1
- **Purpose:** What it does
- **Entry point:** `main.py`
- **Key files:** `handler.py`, `models.py`

### Module 2
...

## Data Flow
<How data moves through the system>

## Dependencies
<External dependencies and why>
```

## Step 5: Validate Documentation

Check for:
- Out-of-date docs (code changed, docs didn't)
- Missing sections (no examples, no parameters)
- Broken links
- Inconsistent formatting

## Step 6: Write Report

**Write to:** `.agents/doc/YYYY-MM-DD-<target>.md`

```markdown
# Documentation Report: <Target>

**Date:** YYYY-MM-DD
**Project Type:** <CODING/INFORMATIONAL/OPS>

## Coverage
- Total documentable items: <count>
- Documented: <count>
- Coverage: <percentage>%

## Generated
- <list of docs generated>

## Gaps Found
- <undocumented item 1>
- <undocumented item 2>

## Validation Issues
- <issue 1>
- <issue 2>

## Next Steps
- [ ] Document remaining gaps
- [ ] Fix validation issues
```

## Step 7: Report to User

Tell the user:
1. Documentation coverage percentage
2. Docs generated/updated
3. Gaps remaining
4. Location of report

## Key Rules

- **Detect project type first** - approach varies
- **Generate meaningful docs** - not just stubs
- **Include examples** - always show usage
- **Validate existing** - docs can go stale
- **Write the report** - track coverage over time

## Commands Summary

| Command | Action |
|---------|--------|
| `discover` | Find undocumented features |
| `coverage` | Check documentation coverage |
| `gen [feature]` | Generate docs for specific feature |
| `all` | Update all documentation |
| `validate` | Check docs match code |

## Examples

### Generating API Documentation

**User says:** `/doc gen authentication`

**What happens:**
1. Agent detects project type by checking for `package.json` and finding Node.js project
2. Agent searches codebase for authentication-related functions using grep
3. Agent reads authentication module files to understand implementation
4. Agent generates documentation with purpose, parameters, returns, and usage examples
5. Agent writes to `docs/api/authentication.md` with code samples
6. Agent validates generated docs match actual function signatures

**Result:** Complete API documentation created for authentication module with working code examples.

### Checking Documentation Coverage

**User says:** `/doc coverage`

**What happens:**
1. Agent detects Python project from `pyproject.toml`
2. Agent counts total functions/classes with `grep -r "^def \|^class "`
3. Agent counts documented items by searching for docstrings (`"""`)
4. Agent calculates coverage: 45/67 items = 67% coverage
5. Agent writes report to `.agents/doc/2026-02-13-coverage.md`
6. Agent lists 22 undocumented functions as gaps

**Result:** Documentation coverage report shows 67% coverage with specific list of 22 functions needing docs.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Coverage calculation inaccurate | Grep pattern doesn't match all code styles | Adjust pattern for project conventions. For Python, check for `async def` and class methods. For Go, check both `func` and `type` definitions. |
| Generated docs lack examples | Missing context about typical usage | Read existing tests to find usage patterns. Check README for code samples. Ask user for typical use case if unclear. |
| Discover command finds too many items | Low existing documentation coverage | Prioritize by running `discover` on specific subdirectories. Focus on public API first, internal utilities later. Use `--limit` to process in batches. |
| Validation shows docs out of sync | Code changed after docs written | Re-run `gen` command for affected features. Consider adding git hook to flag doc updates needed when code changes. |
