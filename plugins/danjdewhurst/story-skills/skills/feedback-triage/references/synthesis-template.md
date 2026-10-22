# Synthesis Template

Write the round synthesis to `feedback/round-{N}/synthesis.md` only after
every expected reader file for the round is collected. The synthesis is the
decision record: which notes become revision work, which are adjudicated,
and which are declined with a recorded reason. `readiness` is one of
`ready`, `needs-revision`, or `not-ready`.

```yaml
---
round: {N}
readers:
  - {reader-1-kebab}
  - {reader-2-kebab}
readiness: needs-revision
# source: simulated   # only when the round is a reader-panel round
---

# Synthesis — Round {N}

## Readiness Verdict

**{ready | needs-revision | not-ready}** — {one sentence: why}

- `ready`: no blocking or major convergent issues; proceed to the next
  stage (next round, or export).
- `needs-revision`: convergent or adjudicated issues require a revision
  pass before the next round. Lists the revision plan below.
- `not-ready`: structural problems (broken premise, failed arc, pervasive
  confusion) require developmental rework, not a polish pass.

## Convergent Findings (≥2 readers agree)

| Finding | Readers | Chapters | Canon check | Action |
|---------|---------|----------|-------------|--------|
| {One-line finding} | {a, b} | {Ch N} | {verified / setup-gap} | {Fix planned} |

Convergent findings are the strongest signal: two independent readers
tripping on the same spot means the manuscript, not the reader, is at fault.
These become revision items by default.

## Divergent Findings (readers disagree)

| Finding | For (readers) | Against (readers) | Adjudication | Action |
|---------|---------------|-------------------|--------------|--------|
| {One-line finding} | {a} | {b} | {Which side, and why — cite canon, craft, or intent} | {Fix / decline} |

Adjudication rules:

- Check both sides against the bible and the premise. Canon and theme
  outrank taste.
- A 2-vs-1 split is convergent (see above), not divergent.
- When genuinely 1-vs-1 with no canon tiebreak, prefer the reader whose
  overall verdict was more positive — they engaged more deeply — or ask the
  user. Record who decided.

## Single-Reader Findings

| Finding | Reader | Severity | Weight | Action |
|---------|--------|----------|--------|--------|
| {One-line finding} | {a} | {major/minor} | {accept / investigate / decline} | {...} |

Weigh single-reader findings by specificity: a specific, locatable note
("the alibi in Ch 9 contradicts the timeline") outranks a vague one ("the
middle dragged"). Specific + canon-verifiable = investigate or accept.
Vague + taste-based = usually decline.

## Declined with Reason

| Finding | Reader(s) | Reason for declining |
|---------|-----------|----------------------|
| {One-line finding} | {a} | {e.g. contradicts premise; outside genre contract; reader wanted a different book} |

Every declined finding needs a recorded reason. "The author disagrees" is
not a reason. Reasons reference canon, premise, genre contract, or craft
principle.

## Revision Plan

Numbered, actionable items for the revision pass, each with file targets:

1. {What changes} — targets: {chapter/scene/entity files}
2. ...

Hand this plan to the `revision-continuity` skill for execution.
```

## Synthesis checklist

- [ ] Every expected reader file for the round is collected (no synthesis
      on a partial set — see the discipline rule in `SKILL.md`)
- [ ] Each finding appears in exactly one category
- [ ] Every convergent finding has an action (fix or explicitly deferred)
- [ ] Every divergent finding has a recorded adjudication with a reason
- [ ] Every declined finding has a recorded reason (not just disagreement)
- [ ] The readiness verdict matches the findings (blocking convergent
      issues cannot coexist with `ready`)
- [ ] The revision plan lists concrete file targets for each item
- [ ] A simulated round is labelled `source: simulated`, sorts its
      findings as single-reader, and does not treat `ready` as ready to
      submit or publish (see "Simulated rounds" in `SKILL.md`)
