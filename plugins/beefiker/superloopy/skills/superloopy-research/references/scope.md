# Scope

Load this reference in Phase 0, before writing the research frame.

## Phase 0 - Scope

Write the research frame before searching:

```text
Core question: <the actual information need>
Axes (3+ orthogonal): <axis - what to search, where, why> ...
As-of: <the date the answer must be true for> · Locale: <primary market/language, or global>
Out of scope: <what does not count as an answer> · Down-rank: <aggregators and mirrors that reprint without attribution>
Minimum grade: <A-E floor for a load-bearing source> · Required measurements: <numbers the answer must carry, or none>
Intent authority: <spec, design doc, contract, or standard that defines expected truth - or none>
Codebase relevant: yes/no · External: yes/no · Browsing: yes/no · Verification likely: yes/no · Report requested: no | <format>
```

Use at least three independent axes. Good axes are by product area, code ownership, data source, standards body, competitor, failure mode, or user persona. Avoid vague roles like "web researcher". Naming what does *not* count matters as much as naming the axes: a wave with no exclusions returns volume instead of coverage, and every excluded topic is a lane you did not have to spend.

Source grades — set the floor in the frame, carry the grade on every source you cite (ladder adapted from fivetaku/insane-research, MIT):

| Grade | Source kind |
|---|---|
| A | Peer-reviewed work, standards text, audited dataset, court or regulator record |
| B | First-party documentation, filings, official changelogs, the source repository itself |
| C | Named-expert analysis, industry survey that publishes its method |
| D | Preprint, vendor blog, benchmark with no independent replication |
| E | Forum or social post, unattributed aggregator, undated listicle |

A D or E source can open a lead or add supporting context; it cannot be the load-bearing support for a high-risk claim. Then create the session directory `.superloopy/evidence/research/<timestamp>-<slug>/`; this is the evidence root every artifact lives under.

### Expected truths — when the question has an authority

Some questions have a stated intent behind them: a spec, a design doc, a contract, a standard, a ticket, the user's own description of how the system is supposed to work. For those, start from "what must be true if that intent holds?" and write the expected truths down *before* searching. Then research measures reality against them instead of asking the open-ended "what is out there", which is how an investigation drifts into describing what it happened to find.

Keep them in `expected-truths.md`, one row per expectation, in the columns the validator reads:

```text
| id | expected | source | observed | status | claim |
| --- | --- | --- | --- | --- | --- |
| T1 | <what must be true> | <where the intent says so> | <what reality showed> | violated | C1 |
```

`status` is `holds`, `violated`, or `unknown`. A `violated` row must land somewhere the reader can see — either the id of a ledger claim that now carries it, or the literal `gap`, in which case the synthesis `## Gaps` section must name the expected truth by id. `unknown` means the expectation went unmeasured, which is also a gap and must be published the same way. A diff you found and then dropped is worse than one you never looked for, because the journal implies it was handled.

Skip this when the question has no authority to measure against — open market scans, prior-art surveys, and "what are the options" questions have no expected truth to violate, and inventing one there just biases the sweep. State which case you are in as part of the frame. (Expected-truth discipline adapted from the `ulw-research` skill in code-yeongyu/lazycodex, MIT.)
