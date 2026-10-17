# Iteration: research, history, and method reference

A reference complementing the `iteration` SKILL.md with deeper context on iterative methods.

## Research lineage

- **Henry Petroski**, *The Evolution of Useful Things* (1992) and *To Engineer Is Human* (1985). Central thesis: useful designs evolve through accumulated failure and refinement. The forks, paperclips, and bridges we use today exist in their current form because of generations of iteration.
- **Eric Ries**, *The Lean Startup* (2011). Translated iteration into product-management vocabulary: minimum viable product, build-measure-learn loop, validated learning, pivot vs. persevere.
- **Tom Kelley & David Kelley**, *Creative Confidence* (2013). IDEO's design-thinking process: empathize, define, ideate, prototype, test, repeat.
- **Jeff Sutherland & Ken Schwaber**, *Scrum* (1995 onward). Time-boxed iterations with retrospectives.
- **Boyd's OODA loop** (military strategy, 1960s onward) — observe, orient, decide, act, repeat. Faster cycle wins.
- **Continuous delivery / DevOps** (Humble & Farley, *Continuous Delivery*, 2010). Iteration shrunk to the smallest reliable increment.

## Iteration cycle frequencies

Cycles in different contexts:

| Context | Cycle length |
|---|---|
| Hardware product (cars, appliances) | Months to years |
| Industrial software | Quarters |
| Consumer software | Weeks |
| Startup MVP | Days to weeks |
| Continuous delivery | Hours to minutes |
| User research | Days to weeks |

Faster cycles enable more learning per unit time but demand more discipline (each cycle must produce value).

## The "build-measure-learn" loop (Lean Startup)

Three steps:

1. **Build** the smallest thing that tests a hypothesis.
2. **Measure** the result quantitatively (metrics, data).
3. **Learn** from the measurement — confirm or reject the hypothesis.

Then either persevere (the hypothesis is right; iterate further) or pivot (the hypothesis is wrong; try a different direction).

The trap: building something *without* a clear hypothesis to test. The build wastes time; the measurement isn't meaningful; the learning is post-hoc rationalization.

## Sutherland's "Spiral" model (1986)

Predates Scrum; describes iterative development with each loop:

1. Determine objectives.
2. Identify and resolve risks.
3. Develop and test.
4. Plan the next iteration.

The risk-driven framing — early iterations focus on the highest-risk unknowns — is enduringly useful.

## Common iteration anti-patterns from research

- **The waterfall trap**: gathering all requirements up front; designing fully; building fully; testing only at the end. Catches issues too late.
- **The "iterate forever" trap**: cycles that never converge because there's no clear end criterion.
- **The "iteration without measurement" trap**: cycles that produce changes but no evidence of whether the changes helped.
- **The "iteration without learning" trap**: cycles that make changes but don't update the team's mental model of what works.

## Cross-domain examples

### Manufacturing: Toyota's kaizen

Continuous incremental improvement. Each shift makes small changes; over decades, the cumulative improvement is enormous. Toyota's quality and efficiency advantages derive from kaizen as much as from any specific innovation.

### Open-source software

Linux, Wikipedia, the modern web stack: all built through tens of thousands of small iterations by many contributors. The aggregate quality far exceeds what any single team could produce.

### Scientific method

Science *is* iteration: hypothesize, experiment, observe, refine. The accumulated knowledge of human civilization is the output of millions of cycles.

### Architecture and urban design

Frank Lloyd Wright sketched dozens of revisions before committing to a building. Cities themselves iterate over generations — neighborhoods adapt, streets repurpose, buildings replace.

## Resources

- **Petroski, H.** *To Engineer Is Human* (1985); *The Evolution of Useful Things* (1992).
- **Ries, E.** *The Lean Startup* (2011).
- **Humble, J. & Farley, D.** *Continuous Delivery* (2010).
- **Beck, K.** *Test-Driven Development by Example* (2002) — iteration at the code level.
- **Knapp, J.** *Sprint* (2016) — five-day design-sprint method.
