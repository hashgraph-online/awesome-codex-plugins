# Tactic Scoring Rubric

Used in two places: Shortlist mode (a quick, scored set of tactics when the user is stuck) and Section 12 of the full plan. The five statuses are the same in both, so a shortlist drops into a plan without relabeling.

## Intake for Shortlist mode

Ask until these are on the record. Do not score against assumptions.

1. Stage and the one growth goal for this window.
2. Budget and team: who owns marketing work, and how many hours they have.
3. What has already been tried, with results if known.
4. Competitor tactics the user admires.

## Scoring

Score each candidate 0-3 on six dimensions. 0 means "no evidence either way," not "probably fine."

| Dimension | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| **Audience** | No evidence the ICP is reachable here | Plausible by category, unverified | ICP observed on this surface | Named communities, queries, or accounts the user can point at |
| **Stage** | Preconditions absent | One precondition missing | Preconditions met, untested | Preconditions met and a comparable move already worked |
| **Evidence** | Support is "it's popular" | Third-party case studies only | Dated first-party signal from an adjacent channel | Dated first-party result for this audience |
| **Capacity** | No owner | Owner named, no hours | Owner and hours, displaces something | Owner and hours with nothing displaced |
| **Cost** | Unknown total cost | Over the approved bounded amount | Within it, but uses most of it | Within it with headroom |
| **Risk** | No stop condition definable | Reversible only at cost, gates unchecked | Reversible, gates identified | Reversible, cheap to stop, no legal, platform, or brand exposure |

For Audience on search tactics (#1-#11, #140-#142), check real query data: Search Console, keyword tools, and what AI assistants currently answer for the category's core questions.

## Decision rule (first match wins)

1. Any dimension scored 0: **Skip** or **Conditional**, never a test this cycle. Name the zeroed dimension.
2. Total at least 14/18, Evidence at least 2, and Capacity at least 2: **Approved test**. State the test, success metric, review date, and stop condition.
3. Total at least 10 with one named blocker: **Conditional**. State the unlock condition and who can clear it.
4. Total at least 10 with no capacity in this window: **Deferred**. State the review date.
5. Total under 10, or Risk at most 1: **Skip**. State the disqualifying dimension.

A tactic already running is **Current**: score it, but do not present it as new.

**Caps.** Score at most 8 candidates; surface at most 5; at most 3 carry Approved test at once. If more clear rule 2, rank by Capacity then Cost and move the rest to Deferred. Capacity, not enthusiasm, is the binding constraint.

**Required rejection.** Every shortlist names at least one tactic that is not recommended, drawn from the record: something the user already tried or admires, or the highest-scoring candidate that still fails a dimension. Do not invent a strawman. If the user named nothing and every candidate clears, say so.

## Shortlist output

For each surfaced tactic:

- **Tactic** (library number and name): one-line description
- **Status**: Approved test / Conditional / Deferred / Skip / Current, with the six scores and total
- **Why it fits**: the evidence behind the Evidence score
- **How to start**: first 2-3 steps and the executing Suede skill
- **Measure**: success metric, review date, stop condition
- **Resources**: time, budget, skills

Close with:

**Not recommended:** [tactic], fails [dimension] because [current evidence, or the absence of it].
