# Build When Missing

Use this when quality is discussed but not measured. Pattern sources include `QUALITY_SCORE.md`, generated quality reports, harness baseline files, and scheduled gardening commands.

## Equivalent Artifacts

- Existing quality dashboards, generated reports, static-analysis summaries, or debt baselines may already satisfy the quality role.
- Record the chosen artifacts under `Detected Mapping` before creating default score files.
- Use `templates/quality-report.md` only when no equivalent quality report exists.

## Minimum Files

- `QUALITY_SCORE.md`, `docs/quality/QUALITY_SCORE.md`, or an explicitly mapped equivalent quality summary.
- `docs/generated/quality-report.md` or a mapped generated report path.
- Optional JSON report under `docs/generated/` or `artifacts/`.
- Baseline or threshold file under `scripts/baselines/` or `scripts/harness-baselines/`.

## Bootstrap Steps

1. Map existing quality reports, dashboards, and baselines.
2. Choose four to eight automatically collectible metrics tied to structural risk only if the mapped surface lacks them.
3. Separate blocking gates from informational metrics.
4. Create thresholds or baselines so historical debt is visible but new degradation fails.
5. Generate a Markdown report for humans and JSON only if scripts need trend data.
6. Define a gardening cadence that lowers thresholds or removes allowlist entries gradually.

## Validation

- Run the report generator or manual collection command.
- Confirm every finding includes path, metric, current value, threshold, and suggested action.
- Confirm new degradation can be detected without forcing full historical cleanup.

## Do Not Include

- A single aggregate score that hides critical risk.
- Metrics that cannot be collected repeatably.
- One-off refactor plans presented as ongoing quality governance.
