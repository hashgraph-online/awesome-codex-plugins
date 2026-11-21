---
name: align-standards
description: "Use when the user asks to audit a project against its standards and implement the improvements they select."
argument-hint: "[focus]"
user-invocable: true
disable-model-invocation: true
---

# Align standards

Bring an existing project into line with its standards and conventions, while preserving what it does for its users.
Audit the requested focus and its dependencies, or the whole project when no focus is given.
Follow the [development loop](../../shared/development-loop.md#standards) and [engineering contract](../../shared/engineering.md).

## Audit and choose

The audit is read-only. Use the relevant existing audits and keep their findings unchanged:

- `rethink` to use critical thinking and put the whole work under the right perspective;
- `align-docs` in inspection-only mode for documentation;
- `staff-review` for code quality.

Inspect what they do not cover: tooling, delivery, CI, UI, the data model, database access, repeated or held-open work, and behavior with more than one owner.
For data and query work, read the callers, cardinality, volumes, joins, filters, indexes, and execution plans, exploring authorized databases read-only.

Give each finding its evidence and location, the applicable standard, severity, impact, effort, risk of the change, your confidence, and the proof it needs.
Group findings with one root cause into one item. Report what you inspected and what you could not cover.
Put security and data-loss risks first, then impact for the effort and risk.
Favor areas the git history shows changing often: aligning code nobody touches buys little.
Explain the proposed improvements and let the user choose. Choosing none ends the audit without edits.

## Align

The selection authorizes implementing those items through the [unattended workflow](../../shared/unattended-runs.md).
Use `align/standards-YYYY-MM-DD`, or the user's branch.
Save the roadmap of selected and remaining items in the task record, and resume from it on later runs.

Split the selected items into tranches: one area each, with one verification and one rollback.
Establish [done and verification](../create-test/SKILL.md#definition-of-done) for each tranche before changing it.
If a tranche fails its verification or review, stop and report; do not start the next one.
Surface changes to business behavior for a separate user decision, and record new findings in the roadmap instead of widening a tranche.
