# Suede AI Ship Copy Skills: Phases and Thresholds

## The graph

Twelve phases, parallel wherever the edges are not real. This is the logical DAG;
the script's twelve `phase()` labels fold **Claim audit** into `Gaps` and **Collision
check** into `Outline`, and split **Review and refute** and **Gate and handoff** into
two each. When narrating live progress use the script's labels: there is no phase
called "Claim audit" in `/workflows`.

1. **Intake**: sources, the requester's own statements transcribed into the
   permitted set untouched, the currently published text captured verbatim, voice
   references drawn from shipped copy, protected strings, the surface's hard
   limits, hazards. Manifest only.
2. **Research**: five blind lenses: product truth, audience, market, voice,
   surface law. Each searches a different way because one angle never finds
   everything. Every fact carries a `file:line`, URL, sha, or timestamp.
3. **Gaps**: a completeness critic names what went unread, then one bounded fill
   round (first 2 gaps; the rest ride to the handoff as unread).
4. **Claim audit**: the load-bearing skeptic, pointed only at agent output. Every
   agent-generated fact is opened against its source and returns `holds`,
   `overstated`, `unsourceable`, or `stale`. Dropped claims leave the set;
   overstated ones are narrowed to what the source supports. The requester's
   givens are not in this list and a verdict returned against one is discarded
   unread. **Nothing downstream may assert a claim outside the permitted set:
   surviving agent claims plus every given.**
5. **Angles**: three postures generated blind to each other: problem-first,
   outcome-first, wedge. Each declares whether a competitor could publish its
   headline verbatim, which is a failing grade rather than a formatting field.
6. **Outline**: the planner judges the three angles, grafts the best of the
   runners-up, and writes a section map: one message per section, citations drawn
   only from the surviving claims, an observable acceptance question per section.
   High effort by design. Then a red team. One revision round follows **only** if the
   red team returned a fatal objection or two serious ones; otherwise the map stands
   and the objections ride to the handoff. Do not narrate a revision that did not run.
7. **Collision check**: a pure function, no agent. Duplicate message ownership,
   a citation outside the claim set, a protected string assigned zero or twice, or
   budgets over the ceiling all halt the run.
8. **Draft**: one writer per section, in parallel. Each sees its neighbours' jobs
   so transitions are possible, and never their text. A fact outside its citation
   list becomes `[AUTHOR: supply X]`, never an invention.
9. **Assemble**: a barrier. Transitions written, repetition cut, one voice,
   budget enforced, placeholders and protected strings preserved byte-exact.
10. **Review and refute**: four lenses on the whole piece (cold read, assertion
    audit, conversion, slop). Findings aimed at a given are dropped by a pure
    function first, then two independent verifiers take each surviving blocker or
    major, refute by default. **Both must fail to refute** for a finding to
    survive; unanimity, not majority, because rewriting a line that was fine has a
    real cost in a short piece.
11. **Polish**: one reviser for confirmed blockers (prose has no file-level
    disjointness, so parallel editors of one string produce a conflict with no
    merge tool), then Suede Slop Stop scored out of 50, then the graphic spec and
    the channel package in parallel.
12. **Gate and handoff**: deterministic checks (open placeholders, missing
    protected strings, house-style dash violations, word count, fields over limit) run in the script
    where no agent can argue with them, then a read-only publish-readiness verifier
    for drift, truth at the source, rights, and reversibility. Drift and truth-at-the-source
    are scoped to agent-generated claims; the rights check is scoped to third-party material,
    so a customer result you supplied cannot come back as a permissions risk wearing a
    rights label. Then the evidence record.

## Thresholds

Every gate in this workflow resolves to a number or a command:

| Check | Threshold |
|---|---|
| Requester's own claims audited | Never. 0 reach the audit. They reach the refute and gate prompts only as named out-of-scope context, never as a target |
| Claim may be asserted | Present in the permitted set (surviving agent claims + every given). Anything else is `[AUTHOR: supply X]` |
| Finding survives review | 2 of 2 verifiers fail to refute it |
| Findings refuted per run | First 4 blockers/majors; the remainder are logged, never silently dropped |
| Gap fills | First 2; the rest are reported as unread |
| Sections | 3-5 preferred, 7 ceiling |
| Slop Stop score | 35/50 or the piece is `REVISE`; advisory score only |
| Channel field | `chars <= limit` per field, counted and reported individually |
| Word count | `<= wordBudget × 1.1` when a budget was supplied; unenforced when it was not |
| Em-dash violations | 0 in newly written prose when `houseStyle.emDashes` is `avoid`; permitted when `allow`. Protected strings and givens are exempt |
| Open placeholders | 0, or Status is "ready for author", never "reviewed" |
| Placeholders vanished since draft | 0. A placeholder the assembler or deslop pass resolved away is a fabrication |
| Stalled sections | 0. A writer returning `blocked`, `needs-context`, or nothing leaves a hole in the piece |

The six rows from Channel field through Stalled sections are **hard gates**:
any one fails and `hardMechanical` forces `copyVerdict: hold`.
Two more hard gates have no row because they are
liveness rather than quality: a channel-package agent or a deslop agent that
returned nothing also forces `hold`.

The preceding rows describe claim scope, review, and planning constraints.
The Slop Stop score alone only moves the verdict to `ship-with-caveats`, never to
`hold`. Do not report a 22/50 score as a hold.
