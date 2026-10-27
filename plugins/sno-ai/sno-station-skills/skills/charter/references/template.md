# Charter layout

One markdown file. Its path is its identity. Keep only the sections that carry content, except
`Success checks` and `Proof`, which always exist.

```markdown
---
name: <slug>
title: <what this delivers, in a few words>
status: draft            # draft | released | delivered | superseded
owner: <who owns the work>
updated: <UTC date>
---

## Owner decisions
What the owner already decided, in their terms, each with its date. Boundaries they set.
Nothing an agent inferred.

## Outcome
The requested result and who gets it. The problem it removes, with the actual evidence
behind a claim (a file, a message, a measurement), not a guess.

## Scope and non-goals
What is included, what is explicitly not, and what must keep working as it does today.
What the executor may not do without the owner: publish, send to other people, spend, delete.

## Success checks
1. What will be observed, where, and how. A check anyone can answer pass or fail.
2. ...

## Plan
(Added by the executor only when the work has dependent steps. Steps in order, who does each.)

## Proof
(Written only by `sno deliver-proof`. Never edited by hand.)

| check | result | how | exit | log | at (UTC) |
|---|---|---|---|---|---|

## Report
(Written at close by the executor: what worked, which checks ran, anything unfinished.)
```

## Notes

- The number of a success check identifies it; the Proof table refers to it. Numbers are
  unique across the whole charter, slices included. Do not renumber a released charter: add
  new checks at the end, and mark a dropped one in place by striking it through, for example
  `3. ~~old check~~ dropped`; `sno deliver-proof` does not require or accept proof for it.
- Proof logs and evidence files sit beside the charter in `<charter-basename>.proof/`.
- A big charter is sliced: under `## Success checks`, give each slice a `### <slice name>`
  heading and its own checks, numbered on from the previous slice (slice A has 1-3, slice B has
  4-6). A slice is named `<charter filename> - <slice name>`, and one executor owns one charter
  or one slice.
- Example success checks, by kind of work. A file: "the produced report opens and section 3
  states the total, which equals the independent recount in `totals.csv`." A message: "the
  customer's inbox shows the confirmation within one minute of the order." A code change: "the
  command that failed before the change now prints the expected value and exits 0."
