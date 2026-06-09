---
name: complexity
description: "Run complexity."
---
# Complexity Skill

**YOU MUST EXECUTE THIS WORKFLOW. Do not just describe it.**

Analyze code complexity to identify refactoring targets.

## Execution Steps

Given `$complexity [path]`:

### Step 1: Determine Target

**If path provided:** Use it directly.

**If no path:** Use current directory or recent changes:
```bash
git diff --name-only HEAD~5 2>/dev/null | grep -E '\.(py|go)$' | head -10
```

### Step 2: Detect Language

```bash
# Check for Python files
ls *.py **/*.py 2>/dev/null | head -1 && echo "Python detected"

# Check for Go files
ls *.go **/*.go 2>/dev/null | head -1 && echo "Go detected"
```

### Step 3: Run Complexity Analysis

**For Python (using radon):**
```bash
# Check if radon is installed
which radon || pip install radon

# Run cyclomatic complexity
radon cc <path> -a -s

# Run maintainability index
radon mi <path> -s
```

**For Go (using gocyclo):**
```bash
# Check if gocyclo is installed
which gocyclo || go install github.com/fzipp/gocyclo/cmd/gocyclo@latest

# Run complexity analysis
gocyclo -over 10 <path>
```

### Step 4: Interpret Results

**Cyclomatic Complexity Grades:**

| Grade | CC Score | Meaning |
|-------|----------|---------|
| A | 1-5 | Low risk, simple |
| B | 6-10 | Moderate, manageable |
| C | 11-20 | High risk, complex |
| D | 21-30 | Very high risk |
| F | 31+ | Untestable, refactor now |

### Step 5: Identify Refactor Targets

List functions/methods that need attention:
- CC > 10: Should refactor
- CC > 20: Must refactor
- CC > 30: Critical, immediate action

### Step 6: Write Complexity Report

**Write to:** `.agents/complexity/YYYY-MM-DD-<target>.md`

```markdown
# Complexity Report: <Target>

**Date:** YYYY-MM-DD
**Language:** <Python/Go>
**Files Analyzed:** <count>

## Summary
- Average CC: <score>
- Highest CC: <score> in <function>
- Functions over threshold: <count>

## Refactor Targets

### Critical (CC > 20)
| Function | File | CC | Recommendation |
|----------|------|-----|----------------|
| <name> | <file:line> | <score> | <how to simplify> |

### High (CC 11-20)
| Function | File | CC | Recommendation |
|----------|------|-----|----------------|
| <name> | <file:line> | <score> | <how to simplify> |

## Refactoring Recommendations

1. **<Function>**: <specific suggestion>
   - Extract: <what to extract>
   - Simplify: <how to simplify>

## Next Steps
- [ ] Address critical complexity first
- [ ] Create issues for high complexity
- [ ] Consider refactoring sprint
```

### Step 7: Report to User

Tell the user:
1. Overall complexity summary
2. Number of functions over threshold
3. Top 3 refactoring targets
4. Location of full report
5. Run `$refactor <function>` to address critical complexity targets

## See Also

- [refactor](../refactor/SKILL.md) — Safe, verified refactoring for complexity targets

## Key Rules

- **Use the right tool** - radon for Python, gocyclo for Go
- **Focus on high CC** - prioritize 10+
- **Provide specific fixes** - not just "refactor this"
- **Write the report** - always produce artifact

## Quick Reference

**Simplifying High Complexity:**
- Extract helper functions
- Replace conditionals with polymorphism
- Use early returns
- Break up long functions
- Simplify nested loops

## Examples

### Analyzing Python Project

**User says:** `$complexity src/`

**What happens:**
1. Agent detects Python files in `src/` directory
2. Agent checks for radon installation, installs if missing
3. Agent runs `radon cc src/ -a -s` for cyclomatic complexity
4. Agent runs `radon mi src/ -s` for maintainability index
5. Agent identifies 3 functions with CC > 20, 7 functions with CC 11-20
6. Agent writes detailed report to `.agents/complexity/2026-02-13-src.md`
7. Agent recommends extracting nested conditionals in `process_request()` function

**Result:** Complexity report identifies `process_request()` (CC: 28) as critical refactor target with specific extraction recommendations.

### Finding Refactor Targets in Go Module

**User says:** `$complexity`

**What happens:**
1. Agent checks recent changes with `git diff --name-only HEAD~5`
2. Agent detects Go files, verifies gocyclo installation
3. Agent runs `gocyclo -over 10 ./...` on project
4. Agent finds `HandleWebhook()` function with complexity 34
5. Agent writes report with recommendation to extract validation logic
6. Agent reports top 3 targets: HandleWebhook (34), ProcessBatch (22), ValidateInput (15)

**Result:** Critical function identified for immediate refactoring with actionable extraction plan.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Tool not installed (radon/gocyclo) | Missing dependency | Agent auto-installs: `pip install radon` for Python or `go install github.com/fzipp/gocyclo/cmd/gocyclo@latest` for Go. Verify install path in $PATH. |
| No complexity issues found | Threshold too high or genuinely simple code | Lower threshold: try `gocyclo -over 5` or check if path includes actual implementation files vs tests. |
| Report shows functions without recommendations | Generic analysis without codebase context | Read the high-CC functions to understand structure, then provide specific refactoring suggestions based on actual code patterns. |
| Mixed language project | Multiple languages in target path | Run analysis separately per language: `$complexity src/python/` then `$complexity src/go/`, combine reports manually. |

## Local Resources

### scripts/

- `scripts/validate.sh`


