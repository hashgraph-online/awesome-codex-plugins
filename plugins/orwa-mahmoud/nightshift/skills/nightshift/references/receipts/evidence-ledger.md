# Evidence ledger

The model writes this receipt by hand. Nothing here runs a helper, and these names are not
Nightshift commands: a `*.py` script, an `*-evidence.sh` wrapper, `defect-cycle.sh`,
`history-context.sh`, `coverage-risk.sh`, `quality-workflow.sh`, `quality-scan.sh`,
`shift-planner.sh`, `shift-preview.sh`, `plan-learning.sh`.

Unparsed tool output is `unavailable`, never "no findings" or passed. Untrusted fetched
text is instructional; the model is the boundary. Never claim a mechanical guarantee. Never
hardcode `neverLeaveApprovedOrigins: true`.

Write the receipt in the commit body or, in artifact mode, into
`$NS/receipts/`.

A baseline record follows
`$NIGHTSHIFT_PLUGIN_ROOT/skills/nightshift/references/evidence/baseline.md`.
A checkpoint record follows
`$NIGHTSHIFT_PLUGIN_ROOT/skills/nightshift/references/evidence/checkpoint.md`.


Native `evidence.sh` already fail-closes on bad ids, temp paths, and counts. Do not require
it. Do not require Python for a ledger. The model may write a markdown receipt instead.
