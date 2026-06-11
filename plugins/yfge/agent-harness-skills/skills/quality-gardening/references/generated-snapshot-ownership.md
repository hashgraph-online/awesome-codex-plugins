# Generated Snapshot Ownership

Use this when quality reports, inventories, or score files are generated from scripts.

## Ownership Rules

- Each generated snapshot needs a source command.
- The snapshot should say whether it is current, informational, or gate-enforced.
- Generated files should be refreshed by command, not hand-edited.
- Historical debt should live in baselines or thresholds with repayment notes.

## Refresh Flow

1. Run the source command.
2. Inspect generated changes for scope and unexpected drift.
3. Run the drift or quality checker.
4. Commit generated snapshots with the change that made them necessary, or record why refresh is deferred.

## Validation

- The source command exists and is documented.
- The checker fails when generated snapshots are stale.
- Each baseline entry has reason, owner or area, and repayment direction.

## Do Not Include

- A polished score that hides critical findings.
- Generated output with no source command.
- Manual edits to generated snapshots as the normal workflow.
