---
name: iteration-design-vs-development
description: 'Use this skill when reviewing where in the project lifecycle iteration is happening — desirable iteration during design vs. costly rework during development. Trigger when a project keeps slipping due to "design changes during build," when scoping how much design work to do before engineering begins, or when retrospectives reveal that issues were caught too late. Sub-aspect of `iteration`; read that first.'
---

# Design iteration vs. development iteration

The book makes a useful distinction: *design iteration* is the planned cycles that happen during the design phase; *development iteration* is the unplanned rework during build that means design wasn't iterated enough up front. The first is healthy; the second is expensive.

## Why the distinction matters

Cost per iteration cycle rises sharply as the project moves from design to development to deployment:

```
Sketch / wireframe       1x cost
Interactive prototype    3-5x
Coded MVP                10-30x
Production-shipped       50-200x
Production-deployed-to-customers  200-1000x
```

A change discovered during sketch costs a few hours; the same change discovered after deployment to customers can cost weeks of engineering, customer-trust damage, and emergency response.

The principle: do as much iteration as possible at the cheapest fidelities. By the time the design moves to engineering, the fundamental questions should be answered.

## Healthy design iteration

Cycles measured in days to weeks; outputs include:

- Sketches and wireframes
- Interactive prototypes (Figma, Framer, code prototypes)
- User interviews and usability tests
- Design critiques
- Stakeholder reviews
- Refined specifications

Each cycle has explicit purpose and known criteria for completion.

## Costly development iteration

Symptoms:

- "We need to refactor that whole module — turns out the design didn't work."
- "Engineering says they can't build it as designed."
- "We discovered a fundamental issue in QA."
- "We shipped, users complained, we're rolling back."

Each is evidence that design iteration didn't catch what it should have.

## Causes of excess development iteration

- **Insufficient design iteration.** Skipping prototyping; rushing past user testing.
- **Engineering-design isolation.** Designers and engineers don't talk during design; engineering discovers issues during build.
- **Untested assumptions.** "I think users will want X" untested until users encounter X in production.
- **Premature high fidelity.** Polishing pixels before structure is right. The pixels then have to be re-done.
- **Spec-and-throw.** Designers spec without engineering input; engineering builds; result doesn't match the spec's intent.

## Reducing development iteration

### Bring engineering into design earlier

Pair designers with engineers during early design phases. Engineers see implementation issues that designers miss; designers see UX issues that engineers miss. Catching either early is cheap.

### Prototype with the same primitives as production

A Figma prototype is fast but doesn't reveal performance issues, accessibility issues, or implementation complexity. A code prototype using your actual component library reveals those issues at the design phase, when they're cheap.

### Test with users at low fidelity

Paper prototypes and clickable wireframes catch most fundamental issues. The fancier the prototype, the more users react to the prototype's polish rather than its structure.

### Define "done with design" criteria

Don't move to development until specific questions are answered. "Users can complete the core task in the prototype" is a clearer gate than "design looks good."

### Maintain feedback channels during build

Engineers building the design should be able to flag issues quickly to designers. Async tools (Slack, design-review channels, weekly syncs) preserve this without slowing engineering.

## When development iteration is unavoidable

Some projects unavoidably need development iteration:

- **Performance-discovered issues** (the design is correct but real data revealed scale problems).
- **Cross-browser bugs** (the design is correct but rendering differs).
- **Accessibility findings during audit.**
- **Stakeholder feedback after seeing the build.**

For these, the goal isn't zero development iteration; it's *minimizing* it. A well-designed project has few surprises during build.

## Worked example: a feature that went well

A team designs a new dashboard:

- **Week 1**: sketches, structural review.
- **Week 2**: clickable Figma prototype, 5 user interviews. Surfaces that one widget is misunderstood; redesign.
- **Week 3**: refined prototype, engineering pairing session. Engineers identify a data-fetching constraint; design adapts.
- **Week 4**: design handoff with documented edge cases.
- **Week 5–6**: engineering build. Two minor design tweaks during build (acceptable rework).
- **Week 7**: ship. Beta cohort happy.

The 4 weeks of design iteration prevented what would have been 4–8 weeks of development rework if the team had skipped to engineering.

## Worked example: a project that went poorly

The same team rushes a feature:

- **Week 1**: high-fidelity Figma mockup of the "final design."
- **Week 2–4**: engineering build.
- **Week 5**: QA finds the user can't complete the core task. Major redesign.
- **Week 6–10**: rebuild. Ships.
- **Week 11**: users report it's confusing. Patch ships.
- **Week 12+**: ongoing churn.

The "saved" 3 weeks of design iteration cost 8+ weeks of development iteration plus user-trust damage.

## Heuristics

1. **The "where did we discover this issue?" retrospective.** After each project, list the issues that were discovered. For each, ask where it could have been caught cheaply. Patterns emerge.
2. **The fidelity-vs-question check.** For each design decision, ask: what's the cheapest prototype that answers this? Use that.
3. **The engineering-pairing audit.** Across recent projects, was engineering involved during design? Projects where they weren't usually had more development iteration.

## Related sub-skills

- **`iteration`** (parent).
- **`iteration-prototype-fidelity`** — picking the right fidelity for each cycle.
- **`prototyping`** — the technique that enables design iteration.
- **`weakest-link`** — early iteration finds the weakest link cheaply.
