# Vibe Suppressions

> Default suppression list for `/vibe` findings. Load before council invocation to filter noise.

## Purpose

Suppressions prevent known false-positive patterns from cluttering vibe reports. A suppressed finding is **omitted from CRITICAL** and downgraded to INFORMATIONAL (or dropped entirely if marked `drop`).

## Default Suppressions

### Category: Redundant Findings

| Pattern | Reason | Action |
|---------|--------|--------|
| "X is redundant with Y" | Two findings flag the same root cause | Keep the more specific one, suppress the other |
| Duplicate across judges | Multiple judges report identical finding | Deduplicate — keep first occurrence with highest severity |
| Finding already addressed in reviewed code | Code already contains the fix or guard | Suppress entirely |

### Category: Tuning Noise

| Pattern | Reason | Action |
|---------|--------|--------|
| Eval threshold changes tuned empirically | Threshold values chosen by measurement, not convention | Suppress — not a code quality issue |
| "Add a comment explaining why" for tuned values | Thresholds change during tuning; comments go stale | Downgrade to INFORMATIONAL |
| Magic number in config/constants file | Constants files exist to hold these values | Suppress if value is in a dedicated constants/config file |

### Category: Style-Only

| Pattern | Reason | Action |
|---------|--------|--------|
| Style suggestion when behavior is correct | Formatting, naming preference, import ordering | Downgrade to INFORMATIONAL |
| "Consider renaming" with no correctness impact | Subjective naming preference | Downgrade to INFORMATIONAL |
| Line length warnings in generated files | Generated code is not hand-maintained | Suppress entirely |

### Category: Known Safe Patterns

| Pattern | Reason | Action |
|---------|--------|--------|
| `//nolint` or `# noqa` with documented reason | Intentional suppression with justification | Suppress — already reviewed |
| Test files using hardcoded values | Test fixtures are expected to have literals | Suppress in `*_test.go`, `test_*.py`, `*.test.ts` |
| Error handling in CLI `main()` with `os.Exit` | CLI entry points legitimately exit on error | Suppress if in `main.go` or equivalent entry point |

## Custom Suppressions

Projects can extend this list by creating `.agents/vibe-suppressions.jsonl` with one entry per line:

```jsonl
{"pattern": "regex or substring", "reason": "why this is suppressed", "action": "suppress|downgrade"}
```

- `suppress` — omit from report entirely
- `downgrade` — move from CRITICAL to INFORMATIONAL

## How Suppressions Are Applied

1. Load default suppressions (this file) before council invocation
2. Load project suppressions from `.agents/vibe-suppressions.jsonl` if present
3. After council verdict, match each finding against suppression patterns
4. Apply action (suppress or downgrade) and note in report: "N findings suppressed (see vibe-suppressions.md)"
