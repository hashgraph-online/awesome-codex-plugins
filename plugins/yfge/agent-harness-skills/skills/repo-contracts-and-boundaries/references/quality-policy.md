# Quality Policy

Use this when repository contracts include structural metrics, generated reports, thresholds, or recurring debt reduction.

## Metric Selection

- Choose a small set of automatically collectible metrics tied to real structural risks.
- Separate blocking gates from informational reports.
- Freeze new degradation with diff checks while keeping historical debt visible in baselines.
- Do not combine unrelated findings into one attractive aggregate score.

## Generated Snapshot Ownership

- Every generated snapshot names its source command and whether it is informational or gate-enforced.
- Refresh generated files by command, not by hand.
- A drift check should fail when a committed snapshot is stale.
- Baseline entries need a reason, owning area, and repayment direction.

## Garden Loop

1. Run the source command and inspect generated changes.
2. Block new violations while reporting existing debt.
3. Lower one threshold or remove one allowlist item at a time.
4. Commit refreshed snapshots with the change that made them necessary, or record why refresh is deferred.

## Validation

- Confirm each finding includes path, metric, current value, threshold, and suggested action.
- Confirm metrics are reproducible in CI or a documented scheduled environment.
- Confirm critical risks remain visible without relying on an aggregate score.

## Do Not Include

- Metrics with no repeatable collector.
- Generated output with no source command.
- One-off refactor plans presented as ongoing quality governance.
