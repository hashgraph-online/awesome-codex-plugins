# Checkpoints

Use these formats when the user wants a disciplined loop or when preference
learning matters.

## Gate Rule

Every checkpoint is a mandatory pause. Do not proceed until the user replies
explicitly. If the response is ambiguous (e.g., "looks good"), ask: "Does that
mean approve, or would you like changes?"

**Fast draft exception**: when the user clearly asked for a draft and waived
questions, skip the Plan Checkpoint and proceed directly to Draft. All other
checkpoints still apply.

**Checkpoint pressure override**: when the user asks to bypass, ignore, or
override a known Plan Checkpoint, do not treat that as fast draft permission.
Present the plan, explain that fast draft only waives blocking questions, and
stop at `PLAN CHECKPOINT`.

## Question Gate

Ask questions only when the answer changes the plan.

If a current request conflicts with an older preference, output this before
questions:

```text
Preference Handling
- Current instruction: [what controls this task]
- Prior preference: [older rule, kept scoped to artifact/stage]
- Decision: current explicit instruction wins for this task.
- Storage: no durable preference change; do not archive the older preference without repeated contradictory evidence.
```

```text
QUESTION GATE
I need these answers before planning:
1. [blocking question]
2. [blocking question]

Reply with answers, or say "skip" and I will continue with stated assumptions.
```

If questions are skipped:

```text
ASSUMPTIONS
- [assumption]
- [assumption]

Skipped questions are weak signals; they will not become strong preferences.
```

If the user asked for a draft and waived questions without trying to bypass a
known checkpoint, use this fast path. Output all sections and draft without
pausing:

```text
Frame
- Artifact type: [type]
- Audience: [audience]
- Goal: [goal]
- Constraints: [constraints]

Assumptions
- [assumption]

Skipped questions are weak signals; they will not become strong preferences.

Plan
1. [structure]
2. [structure]

Draft
[draft text]

Learning Status
No reusable preference learned; no reviewed decisions were collected.
```

## Plan Checkpoint

Output this block and wait. Do not draft until the user replies.

```text
PLAN CHECKPOINT
[plan]

Reply "approve" to draft, or describe what to change.
```

Plan decisions:

- `approve`: record `plan_approved`, then draft.
- `change/reject/revise`: record `plan_revision_requested`, revise only the criticized elements, reissue the full plan and checkpoint.
- `skip approval`: draft, but mark plan-learning confidence as low.

## Revision Proposal

Output one proposal at a time when precision matters. Wait for the user's
decision before moving to the next proposal.

```text
REVISION PROPOSAL [1/N]: [short title]
Change size: [sentence | paragraph | section | scene | whole artifact]
Location: [target text or location]
Revision: [replacement or instruction]
Reason: [why this improves the artifact]
Risk: [what might be lost]

Reply "apply", "reject", or "adjust: [instruction]".
```

Decision meanings:

- `apply`: accepted edit; strong positive signal.
- `reject`: rejected edit; strong negative signal.
- `adjust`: partial signal; preserve the user's direction.
- `undo`: negative signal for the previously applied edit.

## Session Close

Output after all proposals are resolved. Do not list learned preferences if
there were no review decisions — state what evidence is still missing instead.

```text
SESSION COMPLETE
Applied: [N]
Rejected: [N]
Adjusted: [N]
Unresolved: [N]

Learned Preferences:
- [rule, applies-to artifact-type/stage, evidence, confidence]
```
