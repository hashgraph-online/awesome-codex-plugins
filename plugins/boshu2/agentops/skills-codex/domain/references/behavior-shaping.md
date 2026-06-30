---
name: Behavior Shaping
kind: concept
status: draft
see-also: [slice, primitive, citation, context-density-rule, anti-pattern]
---
# Behavior Shaping

Building agent capability is **operant conditioning, not specification**. You cannot compile a behavior into a non-deterministic model; you can only shape it through observable examples and reinforcement. This is the ubiquitous-language register for that frame — the fourth domain axis alongside DDD (vocabulary), Hexagonal (structure), and Gherkin (acceptance).

Doctrine: [`docs/architecture/behavior-shaping-environment.md`](../../../docs/architecture/behavior-shaping-environment.md).

## The ABC register

Operant conditioning runs on **Antecedent → Behavior → Consequence**. Every working term maps to one of the three:

| Term | Meaning | In this repo |
|---|---|---|
| **Antecedent** | the environment arranged *before* the behavior so the agreed one is the likely one — the highest-leverage lever | `CLAUDE.md`/`AGENTS.md`, `ao lookup`, `GOALS.md`, the corpus, skill `consumes` |
| **Discriminative stimulus** | the cue that signals *which* behavior to emit | skill trigger, the intent/issue, the loop's current move |
| **Behavior** | a discrete, observable, composable action — added, never rewritten | a `.feature` scenario / bead `## Scenarios` (one Given/When/Then) |
| **Reinforcement** | a consequence that strengthens the behavior | passing gates (`/validate`, `validation`, CI green), merge; the **ratchet** locks it permanently |
| **Extinction / Stop** | a consequence that weakens or removes the behavior | hook denial, halt-check STOP/kill marker, revert; deleting a scenario or gate |
| **Shaping** | reinforcing successive approximations toward the target | red→green iteration; the `/evolve` loop run continuously |

## When to use

- When extending a [Primitive](primitive.md), name the **behavior** (a scenario), its **antecedent** (what context makes it likely), and its **reinforcer** (which gate proves it). A behavior with no consequence drifts.
- Prefer **add-and-shape** over big top-down design: add a scenario and reinforce it to green, rather than rewriting prose. Behaviors compose; designs collide.
- To remove a behavior, use **extinction** (delete its cue and reward), not a comment that says "don't."

## Relationship to other entries

- A [Slice](slice.md) demonstrates exactly one Behavior cutting vertically through Primitives.
- A [Primitive](primitive.md) is reinforced into reliability through gates (its consequences).
- An [Anti-Pattern](anti-pattern.md) is a behavior to keep extinguished — documented with the cost of letting it recur.
- The [Context Density Rule](context-density-rule.md) governs what crosses a phase boundary: the antecedent for the next behavior.
