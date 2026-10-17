# Preference Signals

Use this reference when deciding what can be learned from a writing loop.

## What to Extract From

Extract preferences only from these sources:

**Strong (promote after two or more):**
- User approves a plan after review
- User rejects a plan with a concrete reason
- User accepts a proposed edit
- User rejects a proposed edit
- User undoes an accepted edit
- User manually rewrites generated output to change style, voice, or structure
- User explicitly declares a standing preference
- User repeats the same correction across tasks

Manual rewrites are strong signals only when the rewrite changes how something
sounds or is structured — not when it corrects a fact, date, citation, name, or
domain error. When the reason is ambiguous, ask: "Did you rewrite to change the
style, or to fix something that was wrong?"

**Medium (record; do not promote alone):**
- User asks for a narrower or broader scope
- User changes tone, length, or structure after seeing a draft
- User asks to preserve or remove a section
- User selects one version from two or more candidates
- User adjusts a proposal without accepting or rejecting it outright

## What to Discard

Discard these for preference learning:
- Unreviewed model-generated text
- User says "good" or "bad" without a reason
- User edits for a one-off constraint
- User changes a fact, date, citation, or domain error
- User accepts a draft without reviewing alternatives
- Constraints copied from the prompt
- Domain requirements that must not become personal preferences
- Current-task constraints ("this time", "for this memo", storage mode, tone,
  length, or detail level) unless the user explicitly declares a standing
  preference for future work

## Constraint vs. Preference

A constraint applies to one artifact ("for this memo, use short sentences").
A preference applies to future artifacts ("I always prefer short sentences in memos").
Do not convert a constraint into a preference unless the user explicitly says it
applies in future work. When unsure, ask.

## Promotion Guidance

Promote a preference when:

- It appears in two or more strong signals
- It is explicitly stated by the user as a standing preference, not merely as a
  constraint for the current artifact
- It improves a measurable outcome such as acceptance rate, clarity, or reduced rewrites

Keep as a note when:

- It appears once
- It conflicts with another signal
- It may be artifact-specific but the scope is not clear

Discard or archive when:

- Newer evidence contradicts it
- It causes repeated rejected edits
- It is too vague to guide future writing
- It only applies to a single temporary requirement

## Scoping Rules

Prefer narrow scope first:

- `coding-plan/planning`
- `report/critique`
- `fiction/revision`
- `documentation/drafting`

Promote to global only when the same preference repeats across artifact types.

Examples:

```text
Rule: Lead with the recommendation before background.
Applies to: report/planning
Evidence: Two accepted report revisions moved conclusions earlier.
Confidence: high
```

```text
Rule: Use concrete file paths and commands in implementation plans.
Applies to: coding-plan/planning
Evidence: User rejected vague tasks and accepted a plan with exact files and tests.
Confidence: high
```

```text
Rule: Preserve restrained tone during emotional scenes.
Applies to: fiction/revision
Evidence: User accepted two edits reducing melodramatic phrasing.
Confidence: medium
```

## Conflict Handling

When signals conflict:

- Prefer explicit user statements over inferred patterns.
- Prefer recent evidence over old evidence.
- Prefer repeated strong decisions over one isolated decision.
- Prefer artifact-specific rules over global rules.
- Ask before applying a rule if confidence is low or the scope is unclear.

## Decision Log Template

```text
Decision Log
- Accepted: [change] because [reason]
- Rejected: [change] because [reason]
- Adjusted: [change] to [new direction]
- Manual rewrite observed: [summary — was this a style change or a fact correction?]

Candidate Preferences
- [rule], applies-to [artifact-type/stage], confidence [low|medium|high], evidence [summary]
```
