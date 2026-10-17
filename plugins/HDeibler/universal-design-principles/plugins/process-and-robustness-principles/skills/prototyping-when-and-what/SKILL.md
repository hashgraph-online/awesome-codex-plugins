---
name: prototyping-when-and-what
description: 'Use this skill when deciding what to prototype, what fidelity to use, and when to stop prototyping and ship. Trigger when planning research, scoping a design phase, or facing pressure to "stop prototyping and just build it." Sub-aspect of `prototyping`; read that first.'
---

# Picking what and when to prototype

Prototyping has costs (time, opportunity, sometimes confusion). Picking the right thing to prototype, at the right fidelity, at the right moment, is how teams get the benefits without the costs.

## What to prototype

Three categories of question prototypes answer well:

### Risky assumptions

Things you're not sure will work. The riskier the assumption, the more valuable the prototype.

- "Users will understand this new flow" — prototype + user test.
- "This algorithm will be fast enough at production scale" — throwaway performance prototype.
- "Customers will pay for this feature" — concierge MVP or smoke test.

### Disputed decisions

When stakeholders disagree, prototypes resolve faster than discussion.

- Designer vs. engineering on flow complexity.
- PM vs. design on feature scope.
- Marketing vs. design on visual direction.

### High-investment decisions

When the cost of being wrong is high — time, money, brand — invest in prototyping to reduce risk.

- New product launches.
- Architectural changes.
- Brand redesigns.

## What NOT to prototype

- **Well-understood patterns.** Don't prototype the placement of a Save button on a CRUD form.
- **Decisions you'd make the same way regardless of the prototype's outcome.** If you'd ship the favorite anyway, prototyping the alternative is wasted.
- **Things you can't act on.** Prototyping a feature you won't have engineering to build is theater.

## Picking fidelity

The fidelity-to-question match (covered more in `iteration-prototype-fidelity`):

| Question | Fidelity |
|---|---|
| "Does this structure make sense?" | Sketch / wireframe |
| "Is this visual direction right?" | Mockup |
| "Does the flow work for users?" | Clickable prototype |
| "Will it be fast enough?" | Code prototype |
| "Will users adopt it at scale?" | Production beta |

Going higher than necessary wastes time and risks anchoring stakeholders.

## When to stop prototyping

A common failure: indefinite prototyping that never ships. Signals it's time to stop:

- The current iteration is producing diminishing returns.
- The remaining unknowns are best resolved by real users in production.
- Stakeholders are reviewing prototypes that look final.
- The next "iteration" is essentially the build phase.

The discipline: define explicit "good enough to ship" criteria before starting to prototype. When the criteria are met, ship.

## Communication with stakeholders

Stakeholders often see polished prototypes as nearly-finished products. The artificial reality problem in stakeholder form.

Communication patterns:

- **Label fidelity explicitly.** "This is a low-fidelity prototype" prefacing demos.
- **Name what's not yet built.** "The visual style is placeholder; the interaction is what we're testing."
- **Set expectations for the timeline.** "From here to production is X weeks."

Without this framing, stakeholders form unrealistic expectations.

## Common patterns

### Spike + commit

Pre-engineering: a 1–3 day technical spike to validate feasibility. Then commit to building if the spike succeeds.

### Test-then-design

Pre-design: usability test of competitor products or prior versions to gather data; then design informed by the data.

### Prototype-then-spec

Pre-spec: build a prototype; specifications come from what the prototype reveals. The spec describes the working prototype rather than predicting it.

### Continuous prototyping (modern agile)

Each sprint produces something testable. Each release prototypes the next. The line between prototype and product blurs.

## Anti-patterns

- **Prototyping without a question.** Building because "we should make a prototype" rather than to answer something specific.
- **Endless iteration.** Prototyping past the point of diminishing returns; never shipping.
- **Production-quality prototypes.** Building prototypes to production code quality; the cost of throwaway evaporates.
- **Stakeholder confusion.** Showing polished prototypes without framing; stakeholders think it's done.
- **Fidelity creep.** Starting low-fi; gradually polishing; ending with a high-fi prototype that took as long as the actual product would have.

## Heuristics

1. **The "cheapest fidelity" rule.** Pick the cheapest fidelity that answers the question.
2. **The "what would change?" check.** Before building a prototype, ask: if the prototype reveals X, what will I do? If Y, what? If you can't name actions, the prototype isn't worth building.
3. **The disposability check.** If you'd be sad to throw the prototype away, you over-invested.
4. **The stakeholder-framing audit.** Is everyone clear this is a prototype? If not, expectations will diverge from reality.

## Related sub-skills

- **`prototyping`** (parent).
- **`prototyping-concept-throwaway-evolutionary`** — picking the kind.
- **`iteration`** — prototypes power iteration.
- **`iteration-prototype-fidelity`** — fidelity selection in detail.
- **`80-20-rule`** — prototype the 20% that matters most.
