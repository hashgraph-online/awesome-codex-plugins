# Write-Time Quality Enforcement

> Catch code quality issues at edit time, not review time. Hook-based, zero-config.

## Problem

Current quality enforcement happens at `/vibe` time (review). This means:
- Workers produce 100 lines of code before learning the style is wrong
- Agents disable linter rules instead of fixing violations
- Formatting inconsistencies accumulate across a wave
- Debug logging makes it to commit

## Solution: PostToolUse Quality Hooks

Run lightweight quality checks after every file edit, format automatically when possible, and block config tampering.

### Architecture

```
Agent edits file.go
  │
  ├── PostToolUse hook fires
  │   ├── Auto-format (gofmt, black, prettier)
  │   ├── Fast lint check (go vet, ruff check --select=E)
  │   └── Config protection (block linter config edits)
  │
  ├── If violations found:
  │   ├── WARN: "3 lint issues in file.go: <summary>"
  │   └── Agent fixes before continuing
  │
  └── If config tampered:
      ├── BLOCK (exit 2): "Blocked: editing linter config"
      └── Agent must fix code, not config
```

### What to Auto-Fix (No Blocking)
- **Formatting**: gofmt, black, prettier — run silently, rewrite file
- **Import sorting**: goimports, isort — run silently
- **Trailing whitespace**: strip on save

### What to Warn (Non-Blocking)
- **Lint violations**: Show inline, let agent fix
- **Debug logging**: Flag `fmt.Println`, `console.log`, `print(` in non-test files
- **TODO comments**: Flag, suggest `ao beads exec create` instead

### What to Block (Exit 2)
- **Linter config edits**: `.golangci.yml`, `.eslintrc`, `ruff.toml`, `pyproject.toml` lint sections
- **Test disabling**: Commenting out test functions, adding `t.Skip()` without justification
- **CI config weakening**: Removing checks from CI pipeline files

### Config Protection Rules

Agents sometimes "fix" lint violations by weakening the linter:

```yaml
# BLOCKED: Agent tried to add this to .golangci.yml
linters:
  disable:
    - errcheck   # <- This disables a critical check
```

**Rule:** If an agent edits a linter/formatter config file, the hook blocks with:
```
"Blocked: Editing linter configuration. Fix the code instead of disabling the rule.
If the rule is genuinely wrong, explain why and the user can approve."
```

### Model-Tiered Delegation

When a lint violation is too complex for the current worker:

| Violation Type | Tier | Action |
|---------------|------|--------|
| Formatting | Auto-fix | Just run formatter |
| Import organization | Auto-fix | Just run import sorter |
| Simple lint (unused var) | Haiku | Quick inline fix |
| Logic lint (error handling) | Sonnet | Contextual fix |
| Type system issue | Opus | Deep reasoning fix |

### Implementation Notes

This pattern is documented as a reference for future hook implementation. Current AgentOps hooks (`hooks/hooks.json`) can implement this via:

1. **PreToolUse:Edit** — Check if target file is a config file → block if linter config
2. **PostToolUse:Edit** — Run formatter on edited file → warn on lint violations
3. **PostToolUse:Write** — Same as Edit, plus check for debug logging patterns

### Integration with /vibe

Write-time quality reduces `/vibe` review burden:
- Formatting violations: eliminated (auto-fixed at write time)
- Simple lint: mostly eliminated (fixed or blocked at write time)
- Complex logic: still caught by `/vibe` council (appropriate level)

Target: reduce vibe findings by 40-60% through write-time enforcement.
