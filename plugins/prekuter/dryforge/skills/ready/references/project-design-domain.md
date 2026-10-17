# project-design-domain.md — first-cycle foundation design (domain model)

Extract the project's **domain model** from the user. This is the **extraction** mode (knowledge
lives with the user; you must draw it out — never invent it), and the thickest first-cycle
reference, because domain knowledge is the hardest to extract systematically and the most damaging
to get wrong. The domain floor below is what the ELICIT loop must close on the domain axis once
CALIBRATE has confirmed the project's character; depth follows that character. Order is gap-driven,
not a fixed phase after technical — but domain naturally leads early in a first cycle, since the
technical decisions depend on it (`elicitation.md`).

**Floor, not ceiling.** You already know how to hold a domain conversation. This file does **not**
script it — it blocks the failure modes you fall into and lays the depth/breadth floor. The ceiling
is open: how you lead, in what order, is your judgment.

## Asymmetric depth — but domain is always deep

Spend depth where the domain is core; go light on the peripheral (don't fatigue the user). **But:**
even when CALIBRATE judged the project "small," do **not** compromise the *accuracy* of a domain rule.
A small project has *fewer* rules, not *shallower* ones — each rule still meets the depth floor below.

## Failure modes and guardrails

- **Surface-skimming.** Receiving a feature's name is the *start*, not the end. Dig until the
  feature's rules are at a verifiable level — keep pressing past the label.
- **Missing implicit rules.** Don't capture only what the user said aloud. For *every* identified
  concept, confirm its **lifecycle** (created → changes → destroyed) and its **exceptions** (what
  happens off the normal path). The unspoken rules live in those two places.
- **Accepting vagueness.** No vague modifiers ("appropriate," "suitable," "as needed") survive into
  the spec. Dig until each is concrete.
- **Implementation bleed.** Use no implementation terms in domain design. Not "how is it stored" but
  "what must happen." The domain is behavior, not mechanism-of-storage.
- **Rule fabrication.** Every rule must come from the user's words, or be one you derived and the
  user confirmed. Never bake in a rule no one stated.
- **Domain-term confusion.** Where the same word means different things in different contexts,
  distinguish and pin each meaning explicitly.

## Depth floor

- Every identified concept has all four: **what it is / what it does / what it cannot do / what
  happens when it ends.**
- Every rule is convertible to a test case (state it so a test is derivable from the rule alone).
- No vague modifier ("appropriately," "if needed") remains in the spec.
- Mechanism, not just outcome: "when condition A and condition B hold simultaneously, transition to
  state X," not "becomes state X." Each "must" paired with its "must not."

## Breadth guard (against laziness / premature closure)

Depth and breadth are independent — meeting the depth floor on the concepts you found does **not**
mean you found them all.

- Before ending domain design, **explicitly ask the user "are there other major features / entities
  / rules?"** Do not close without this confirmation.
- A satisfied depth floor with no breadth confirmation is **not** a valid close.

## Cross-validation (interactions between concepts)

Per-concept lifecycle checks don't surface the edges where two concepts *meet*. Check the
interactions and dependencies between identified concepts: when concept A changes, what is its
effect on concept B? The edge cases that bite live at those junctions — a lifecycle pass on each
concept in isolation will miss them.

## What this produces

A domain model captured at the depth/breadth floor above: entities and their relationships, state
transitions (possible and forbidden), calculation logic (input → processing → output), explicit
edge-case dispositions, and domain-term definitions. This is recorded in the handoff's Project
Foundation (`foundation-format.md`) as the **whole project's** domain — non-executable context. *This
task's* WHAT lives in `spec.md` (what `go` implements); the Foundation is read as context (no
per-entity target/context tags). `go` later turns the model into `business-rules.md`.

## Universality guard

Stack-agnostic. "Entity," "state," "rule" are domain concepts, not stack artifacts; the actual
domain is whatever the user describes, drawn out at runtime. No framework or storage technology is
named in domain design.
