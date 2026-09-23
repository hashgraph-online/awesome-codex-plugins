# Independent review

Use a separate reviewer when requested or when a complex change, authorization
boundary, migration, or data-integrity risk warrants additional coverage.
Keep self-review and relevant checks sufficient for ordinary small changes
unless repository policy requires more. Delegation must be available and
authorized; otherwise report the missing review and follow the task's existing
completion requirements.

## Separate the context

A fresh session using the same model can provide a separate review perspective.
It does not provide model diversity or eliminate shared blind spots. A
different model or provider is optional, subject to availability and the
user's execution and data-sharing permissions.

Give the reviewer a compact packet:

```text
Requested behavior and acceptance criteria:
Applicable repository instructions:
Base revision:
Reviewed revision or immutable snapshot identifier:
Diff and relevant source/test access:
Commands already run and their actual outcomes:
Known unverified checks:
Review scope and explicit budget, if any:
```

Keep the builder's conversation, self-review, proposed verdict, and preferred
conclusions out of the packet. Supply required domain facts and source access
so independence does not become an under-informed review. A full-history fork
does not meet this context separation; use a fresh context when the host
supports one and report any unavoidable history inheritance.

The reviewer must not edit the builder's files, commit, merge, or publish.
Use read-only access or an isolated checkout with no authority to change the
candidate. Tests that write temporary artifacts need an authorized disposable
environment. Do not keep changing the candidate while it is being reviewed.

## Review and disposition

Ask for actionable findings with file/line, violated requirement or failure
scenario, impact, and supporting evidence. Report uncertainty and missing
context explicitly. An empty findings list is not proof of correctness.

The builder evaluates each finding as confirmed, rejected with evidence,
duplicate, or unresolved. Fix confirmed consequential defects, and run checks
affected by the fix. Do not accept a recommendation solely because another
agent made it. A material disagreement needs an additional probe or human
decision under the existing task contract.

Record the exact revision reviewed. A new commit or working-tree edit makes
that verdict stale for the new candidate. Re-review the delta and affected
interactions; expand to the full diff when the fix changes broad assumptions.
The final handoff names the last reviewed revision and any uncovered changes.
Review completion grants no merge authority.

## Measure whether it helped

Use the optional independent-review section of the measured task receipt.
Record reviewer identity/model, context separation, revisions, finding
dispositions, elapsed time, reported tokens/cost, and human adjudication time.
Count all review attempts, including failed or abandoned ones. Keep unavailable
values unknown and include reviewer usage once in the overall task totals.

Compare confirmed catches and reduced human correction against extra time,
tokens, and false alarms on comparable tasks. Label builder-confirmed findings
separately from test- or human-validated findings. Same-model independence and
review pass rates alone do not establish an efficiency or quality gain.

## Inspiration

Community workflow informed by Code Mower's
[independent, revision-bound review architecture](https://github.com/codemower-ai/code-mower/blob/ad4ba6129dc90922cba63e20ea0715e424356b79/docs/architecture.md)
and [reviewer calibration policy](https://github.com/codemower-ai/code-mower/blob/ad4ba6129dc90922cba63e20ea0715e424356b79/docs/lane-promotion-policy.md).
These are instructions and evidence conventions; runtime enforcement depends
on the host. No Code Mower installation is required.
