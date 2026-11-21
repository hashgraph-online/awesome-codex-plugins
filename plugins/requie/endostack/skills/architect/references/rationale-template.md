# Sketch and rationale template

## The sketch

Write usage first and derive types from it. A small change produces one file of new types and signatures. A larger change produces a module map plus the type definitions for each module. Bodies raise not-implemented. Hard logic is TODO pseudocode. Doc comments state purpose and invariants.

## The rationale

About one page. Use sentence-case headings in this order. Cite a principle by name for each decision instead of re-explaining it.

### Problem

The goal, and what about the current system makes the right structure non-obvious. List the constraints found during grounding: types to interoperate with, callers that must keep working, invariants that cross the boundary.

### Caller's usage

Written before the types. The quickstart a consumer would read, and three or four real call sites. The types must match this section. When they conflict, change the types.

### Shape

In this order:

1. The data structures.
2. How data moves through the signatures.
3. The key decisions.
4. Which invariants the types enforce.
5. Where validation happens.
6. Trust boundaries: each boundary, who controls the input that crosses it, the single module that parses it, where authorization is checked, and which modules hold credentials or privileged access.
7. What is deliberately left out.
8. An explicit assessment of interface depth: how small the public surface is relative to what it hides.

### Synthesis decision

Supplied by arena's synthesis note: which candidate was the base and why, what each other candidate contributed, and what was turned down.

### Accepted tradeoffs

One bullet each, phrased as giving up one thing to get another. Include anything a later reader might take for an accident, for example "Validation runs twice on the admin path; we accept the cost to keep one parser."

### Alternatives

Required. At least one concrete structure you rejected, and why it lost, judged on interface depth and trust-boundary placement. If the constraints left only one viable structure, say so and say which constraint ruled the others out. These are rejected design directions. Do not list the losing arena candidates here, and do not list cosmetic variants.

### Open questions and risks

Phrased as questions the human can answer, for example "Should expired sessions be rejected at the gateway or in each service?"

### Next step

One sentence naming what to code first.
