# Regression Eval Schemas

JSON/MD structures used by eval-regression. Full skill-creator schemas: `$SKILL_CREATOR_PATH/references/schemas.md`.

## evals.json

At `<plugin>/evals/evals.json`.

```json
{
  "skill_name": "plugin-name",
  "evals": [
    {
      "id": 1,
      "name": "descriptive-kebab-case-name",
      "category": "routing | guard-conditions | anti-rationalization | workflow-phases | language-detection",
      "tests_change": "Which behavioral aspect this tests",
      "prompt": "The user's task prompt",
      "expected_output": "Human-readable description of correct behavior",
      "files": [{ "path": "relative/path/file.ext", "content": "Eval context" }],
      "assertions": [
        {
          "name": "assertion-kebab-name",
          "type": "behavioral",
          "check": "What this verifies",
          "pass_criteria": "How to determine pass/fail from the transcript"
        }
      ]
    }
  ]
}
```

## grading.json

Per-run at `<eval-dir>/<version>/grading.json`. Field names are viewer-strict: `text`/`passed`/`evidence`, NOT `name`/`met`/`details`.

```json
{
  "expectations": [
    { "text": "What was checked", "passed": true, "evidence": "Quote/observation from transcript" }
  ],
  "summary": { "passed": 3, "failed": 1, "total": 4, "pass_rate": 0.75 }
}
```

## iteration_metadata.json

At `<workspace>/iteration-<N>/iteration_metadata.json`.

```json
{
  "iteration": 10,
  "old_version": "9.0.4",
  "new_version": "9.0.5",
  "timestamp": "2026-03-23T14:30:00Z",
  "changed_files": ["skills/core-dev/SKILL.md"],
  "evals_count": 26,
  "regression_summary": { "regressions": 0, "improvements": 2, "stable_pass": 22, "stable_fail": 2 }
}
```

## benchmark.json

From skill-creator's `aggregate_benchmark.py`; configuration names are `new_version`/`old_version`.

```json
{
  "metadata": { "skill_name": "plugin-name", "timestamp": "...", "evals_run": [1, 2, 3], "runs_per_configuration": 1 },
  "runs": [
    {
      "eval_id": 1,
      "eval_name": "eval-name",
      "configuration": "new_version",
      "run_number": 1,
      "result": { "pass_rate": 1.0, "passed": 5, "failed": 0, "total": 5 },
      "expectations": [{ "text": "...", "passed": true, "evidence": "..." }]
    }
  ],
  "run_summary": {
    "new_version": { "pass_rate": { "mean": 1.0, "stddev": 0.0, "min": 1.0, "max": 1.0 } },
    "old_version": { "pass_rate": { "mean": 0.95, "stddev": 0.05, "min": 0.9, "max": 1.0 } },
    "delta": { "pass_rate": "+0.05" }
  }
}
```

## regression-report.md

At `<workspace>/iteration-<N>/regression-report.md`.

```markdown
# Regression Report: <plugin-name>
## <old_version> -> <new_version> | <date>

## Executive Summary
- Evals: N | Assertions: N
- Regressions: 0 | Improvements: 2
- Pass rate: 95% -> 100% (delta: +5%)
- Verdict: SAFE TO COMMIT

## Regressions
| Eval | Assertion | Old | New | Evidence |

## Improvements
| Eval | Assertion | Evidence |

## Per-Eval Comparison
| # | Eval | Old | New | Status |

## Changed Files
- skills/core-dev/SKILL.md (behavioral)
```
