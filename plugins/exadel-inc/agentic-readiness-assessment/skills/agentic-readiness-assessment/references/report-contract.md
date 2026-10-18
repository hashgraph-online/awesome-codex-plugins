# Report Contract

Use this reference only while assembling the report.

## Run and Scope

The YAML block has the top-level keys listed in `SKILL.md`, in that order. `raw_total` and `applicable_maximum` are integers; `normalized_score` is `round(raw_total / applicable_maximum * 100)`.

```yaml
gates:
  setup:
    anchor: 2
    score: <earned area score>
  deliverable:
    anchor: 3
    score: <earned area score>
  verification:
    anchor: <4, 5, or 6>
    score: <earned area score>
  probe:
    result: <pass|fail|not attempted>
```

Each gate score equals its anchor area’s earned score.

## Scorecard and findings

Each area score is `earned/max`; `N/A` uses `N/A`. Add exactly one line after the scorecard: `Negative controls: none` or `Negative controls: F-nn, F-nn`.

Start What to Fix with:

```markdown
| ID | Priority / Owner | Problem and blocked capability | Fix and target | Verify |
| --- | --- | --- | --- | --- |
```

Each indexed `F-nn` has one matching `### F-nn` record with the nine fields specified in `SKILL.md`.
