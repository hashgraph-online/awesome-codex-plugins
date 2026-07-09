# Vibe Report Formats

## Output Files

| File | Purpose |
|------|---------|
| `reports/vibe-report.json` | Full JSON findings |
| `reports/vibe-junit.xml` | CI integration (JUnit XML) |
| `.agents/assessments/{date}-vibe-validate-{target}.md` | Knowledge artifact |

---

## Vibe Report Markdown Template

> Used by Step 7 in SKILL.md. Write to `.agents/council/YYYY-MM-DD-vibe-<target>.md`.

```markdown
---
id: council-YYYY-MM-DD-vibe-<target-slug>
type: council
date: YYYY-MM-DD
---

# Vibe Report: <Target>

**Files Reviewed:** <count>

## Complexity Analysis

**Status:** Completed | Skipped (<reason>)

| File | Score | Rating | Notes |
|------|-------|--------|-------|
| src/auth.py | 15 | C | Consider breaking up |
| src/utils.py | 4 | A | Good |

**Hotspots:** <list files with C or worse>
**Skipped reason:** <if skipped, explain why - e.g., "radon not installed">

## Council Verdict: PASS / WARN / FAIL

| Judge | Verdict | Key Finding |
|-------|---------|-------------|
| Error-Paths | ... | ... (with spec — code-review preset) |
| API-Surface | ... | ... (with spec — code-review preset) |
| Spec-Compliance | ... | ... (with spec — code-review preset) |
| Judge 1 | ... | ... (no spec — 2 independent judges) |
| Judge 2 | ... | ... (no spec — 2 independent judges) |
| Judge 3 | ... | ... (no spec — 2 independent judges) |

## Shared Findings
- ...

## CRITICAL Findings (blocks ship)
- ... (findings that indicate correctness, security, or data-safety issues)

## INFORMATIONAL Findings (include in PR body)
- ... (style suggestions, minor improvements, suppressed/downgraded items)

## Concerns Raised
- ...

## All Findings

> Included when `--deep` or `--sweep` produces a sweep manifest. Lists ALL findings
> from explorer sweep + council adjudication. Grouped by category if >20 findings.

| # | File | Line | Category | Severity | Description | Source |
|---|------|------|----------|----------|-------------|--------|
| 1 | ... | ... | ... | ... | ... | sweep / council |

## Recommendation

For performance-sensitive code, run `/perf profile <target>` to identify optimization opportunities.

<council recommendation>

## Decision

[ ] SHIP - Complexity acceptable, council passed
[ ] FIX - Address concerns before shipping
[ ] REFACTOR - High complexity, needs rework
```

---

## JSON Report Structure

```json
{
  "summary": {
    "critical": 0,
    "high": 2,
    "medium": 5,
    "low": 1,
    "total": 8
  },
  "prescan": [
    {
      "id": "P4",
      "pattern": "Invisible Undone",
      "severity": "HIGH",
      "file": "services/auth/main.py",
      "line": 42,
      "message": "TODO marker"
    }
  ],
  "semantic": [
    {
      "id": "FAITH-001",
      "category": "docstrings",
      "severity": "HIGH",
      "file": "services/auth/main.py",
      "function": "validate_token",
      "message": "Docstring claims validation but no raise/return False"
    }
  ]
}
```

---

## JUnit XML Format

For CI integration:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<testsuites name="vibe-validate" tests="8" failures="7" errors="1">
  <testsuite name="prescan" tests="3" failures="3">
    <testcase name="P4-services/auth/main.py:42" classname="prescan.invisible_undone">
      <failure message="TODO marker" type="HIGH"/>
    </testcase>
  </testsuite>
  <testsuite name="semantic" tests="5" failures="4">
    <testcase name="FAITH-001-validate_token" classname="semantic.docstrings">
      <failure message="Docstring mismatch" type="HIGH"/>
    </testcase>
  </testsuite>
</testsuites>
```

---

## Assessment Artifact Format

Saved to `.agents/assessments/`:

```yaml
---
date: 2025-01-03
type: Assessment
assessment_type: vibe-validate
scope: recent
target: HEAD~1..HEAD
status: PASS_WITH_WARNINGS
severity: HIGH
findings:
  critical: 0
  high: 2
  medium: 5
  low: 1
  total: 8
tags: [assessment, vibe-validate, validation, recent]
---

# Vibe Validation: recent

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 2 |
| MEDIUM | 5 |
| LOW | 1 |

## Critical Findings

None.

## High Findings

1. **P4** `services/auth/main.py:42` - TODO marker
2. **FAITH-001** `validate_token()` - Docstring mismatch

## Recommendations

1. Complete or remove TODO at services/auth/main.py:42
2. Update validate_token() docstring to match implementation
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success, no CRITICAL findings |
| 1 | Argument/usage error |
| 2 | CRITICAL findings detected |
| 3 | HIGH findings detected (no CRITICAL) |
