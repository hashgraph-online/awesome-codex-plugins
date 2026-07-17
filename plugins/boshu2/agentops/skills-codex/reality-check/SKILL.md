---
name: reality-check
description: Compare a claimed state with observable
---
# Reality Check

Compare an explicit claim with observable evidence. Cite every confirmed or
missing behavior with a file, command result, or artifact. Separate:

- confirmed behavior;
- concrete gap;
- incomplete evidence;
- changed assumptions.

## Vision-coverage audit

When the claim is a completion or status claim, audit it against the stated
goals, not against what happens to exist. Enumerate every goal in the vision,
plan, or intent source and give each a disposition: confirmed with evidence,
concrete gap, or unverifiable. The audit is complete only when every stated
goal carries a disposition; full coverage of the built surface alone proves
nothing about completion. The named failure mode is built-world bias:
auditing only the code that exists, so goals nobody started never surface as
gaps.

## Frozen question variants

When the same check runs across multiple passes or sessions, freeze the exact
question wording before the first pass and ask it identically in every pass;
record the frozen wording in the report. A pass that answers a reworded
question starts a new baseline — comparing it against earlier passes is the
drifting-rubric failure mode, and its answer does not count as a repeated
measurement.

## Ambition-escalation checkpoint

When invoked during planning, compare the currently planned scope against the
originally stated goal. Planned work that cannot be traced to a stated goal
is reported as an escalation gap, exactly like a missing behavior. Reality
Check reports the escalation; the caller decides whether the ambition or the
stated goal changes.

## Boundary

Return the report to the caller. Plan may use concrete gaps to refine the
existing bead or caller intent. Reality Check does not create work, schedule,
claim, implement, validate, retry, or deliver.
