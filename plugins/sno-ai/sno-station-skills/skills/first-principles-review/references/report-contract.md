# Report Contract

Write one Markdown report with exactly one `PRD Handoff` section and exactly one JSON block.
Use the sections below in this order. Every section needs substantive content. The report must
contain no `?` character; put surviving choices under
`Owner Decisions` as declarative open decisions, then ask them one at a time in chat.

````markdown
# First-Principles Review: <subject>

## Scope and Boundary
<input, hash when applicable, output boundary, bounded and non-exhaustive statement>

## Research Receipt
<sources read, finding from each, and verified/inference/unknown status>

## True Outcome
<implementation-independent user or system outcome>

## Constraint and Assumption Analysis
<each claim classified as hard constraint, owner preference, or inherited assumption>

## Premise Ledger
<each load-bearing premise, evidence state, challenge applied, and result>

## Alternatives
<only materially distinct alternatives and why each differs>

## Primary Recommendation
**Disposition:** PROCEED|REFRAME|SIMPLIFY|REPLACE|SPLIT|TEST-FIRST|STOP

<one primary direction and comparison with the current proposal>

## Falsifiers
<observable evidence that would overturn the recommendation>

## Owner Decisions
<declarative list of unresolved product choices, or `None.`>

## PRD Handoff

```json
<handoff object>
```
````

The handoff object has exactly these required top-level fields. Extra fields are allowed when
they add evidence rather than a second interpretation.

```json
{
  "true_problem": "non-empty implementation-independent outcome",
  "constraints": [
    {
      "claim": "non-empty",
      "classification": "hard constraint | owner preference | inherited assumption",
      "evidence": "non-empty source or explicit unknown",
      "state": "evidence-backed | unproven | inherited | falsified"
    }
  ],
  "premises": [
    {
      "claim": "non-empty load-bearing premise",
      "state": "evidence-backed | unproven | inherited | falsified",
      "challenge": "non-empty challenge applied",
      "result": "non-empty result"
    }
  ],
  "selected_direction": {
    "disposition": "PROCEED | REFRAME | SIMPLIFY | REPLACE | SPLIT | TEST-FIRST | STOP",
    "recommendation": "non-empty",
    "falsifiers": ["one or more observable overturning conditions"],
    "split_outcomes": ["at least two independently buildable outcomes when disposition is SPLIT"]
  },
  "rejected_alternatives": [
    {"name": "non-empty", "reason": "non-empty"}
  ],
  "experiments": ["next evidence-producing action"],
  "acceptance_implications": ["requirement or acceptance consequence"],
  "open_owner_decisions": ["declarative decision statement"],
  "research_receipt": [
    {"source": "non-empty", "finding": "non-empty", "status": "verified | inference | unknown"}
  ],
  "calibration": {
    "verified_facts": ["fact"],
    "inferences": ["inference"],
    "unknowns": ["unknown"]
  }
}
```

`rejected_alternatives`, `open_owner_decisions`, the three calibration arrays, and
`selected_direction.split_outcomes` may be empty. `split_outcomes` must contain at least two
items for `SPLIT` and must be empty otherwise. All other arrays must be non-empty. A report with
no research or no challenged premise is invalid.
