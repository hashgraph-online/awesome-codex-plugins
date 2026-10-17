---
name: iteration
description: 'Use this skill whenever the question is *how* to develop a design — through one big push or through repeated cycles of build, test, learn, refine. Trigger when planning a design process, scoping an MVP, deciding between waterfall and iterative delivery, planning research cadence, or reviewing why a project drifted from its original vision. Iteration is one of the foundational principles in ''Universal Principles of Design'' (Lidwell, Holden, Butler 2003) — and one of the most-violated by teams that try to ship "perfect" first versions.'
---

# Iteration

Iteration is the practice of repeatedly cycling through design, build, test, and refine — using each cycle's output to inform the next. The core insight: design problems rarely yield to single passes of careful planning. They yield to cycles, where each pass uncovers issues invisible to the prior pass. The teams that internalize iteration consistently outperform those that try to plan the perfect solution up front.

## Definition (in our own words)

A design that emerges through iteration is built by repeating a small set of operations: design something; build a version of it; test it (with users, with data, with a critical eye); learn what worked and what didn't; refine; design the next version. Each cycle reveals problems that couldn't be predicted from the inside of the previous cycle. The total work to reach a good design through iteration is usually less than the work to reach the same quality through up-front planning, because iteration converges on what users actually need rather than what you predicted they would need.

## Origins and research lineage

- **Lidwell, Holden & Butler** (2003) distinguished two types of iteration: *design iteration* (the planned, expected refinement during the design phase) and *development iteration* (the unplanned, costly rework during build that indicates inadequate design). The first is good; the second is a failure of the first.
- **Henry Petroski**, *The Evolution of Useful Things* (Knopf, 1992) and *To Engineer Is Human* (St. Martin's, 1985). Petroski's central thesis: useful objects evolve through accumulated failure and refinement, not through a single brilliant design moment. Successful designs encode many cycles of iteration.
- **Eric Ries**, *The Lean Startup* (Crown Business, 2011). Translated iteration into product-management vocabulary: minimum viable product, build-measure-learn loop, validated learning. Influential across software product design.
- **Tom Kelley & David Kelley** at IDEO, *Creative Confidence* (Crown Business, 2013) and earlier IDEO publications. Codified design thinking as an iterative discovery process: empathize → define → ideate → prototype → test → repeat.
- **Boyd's OODA loop** (military strategy, applied to design) — observe, orient, decide, act, then repeat. The faster the loop, the better the outcomes.
- **Modern agile / continuous-delivery practice** — Scrum, Kanban, XP, DevOps all encode iteration as a structural commitment. Releases shrink; feedback cycles tighten.

## Why iteration matters

A first design is built on assumptions. Some assumptions are right; some are wrong. The wrong ones can only be discovered by exposing the design to reality — to users, to use cases, to edge cases the designer didn't anticipate. The longer the design avoids contact with reality, the more wrong assumptions accumulate; the bigger and more painful the eventual correction.

Iteration shortens the gap between assumption and verification. Each cycle exposes a few wrong assumptions; the next cycle corrects them. After several cycles, the design is largely correct because the assumptions have been replaced by observations. Without iteration, the design is shipped on assumptions still mostly untested.

The cost of iteration vs. up-front planning:

- **Up-front planning** is cheap to start (no implementation cost) but expensive to revise (entrenched specifications, sunk cost, political resistance).
- **Iteration** is expensive to start (each cycle requires building) but cheap to revise (each cycle is small).

For complex products with significant unknowns, iteration usually wins.

## Design iteration vs. development iteration

The book's distinction matters in practice:

### Design iteration

Planned cycles during the design phase — sketching, prototyping, testing, refining. Each cycle is intentional and produces learnings.

Healthy design iteration:

- Cycles measured in days to weeks.
- Low-fidelity prototypes early, higher-fidelity later.
- User feedback at each cycle.
- Explicit criteria for "done with this cycle."

### Development iteration

Unplanned rework during the build phase, usually because the design wasn't iterated enough during design. The team builds something, discovers it doesn't work, partially rebuilds, discovers the rebuild has its own problems, etc.

Development iteration is costly because building is more expensive than designing. Reduce it by iterating more thoroughly during design.

The principle: spend cheap iteration cycles (design, prototype) to avoid expensive iteration cycles (build, rebuild).

## When to apply

- **Whenever the design has significant unknowns.** New product categories, new user segments, new technologies — anything where you can't predict the right answer.
- **In MVP design.** The MVP is a vehicle for iteration; it ships not because it's "done" but because shipping enables the next iteration.
- **In any project where the cost of wrong assumptions is high.** Iteration tests assumptions cheaply.
- **When stakeholders disagree.** Iteration replaces argument with evidence.

## When NOT to over-apply

- **In safety-critical systems.** The cost of "iterating" on aircraft control software is human lives. Use iteration during design and prototype; lock down before deployment.
- **For decisions with high switching cost.** Some decisions (database schema, API design that external partners depend on) are expensive to revise. Iterate intensely during design; commit deliberately.
- **When the ground truth is well-known.** A standard CRUD form for a familiar use case may not need many cycles. Iteration is investment in discovery; if you already know the answer, skip the discovery.

## The iteration cycle

A workable cycle:

### 1. Define the question

What are you trying to learn or decide in this cycle? "How do users discover the new feature?" or "Which onboarding flow has higher completion?" Specific questions yield specific answers.

### 2. Build the cheapest thing that answers the question

The MVP for *this cycle*. A sketch, a clickable prototype, a coded version, an A/B test — whichever is cheapest and still answers the question.

### 3. Expose it to reality

Users (research session, beta cohort), data (analytics on a partial release), or a critical reviewer (design critique, code review). The design must encounter something outside the design team.

### 4. Observe and learn

What happened? What surprised you? What confirmed assumptions; what disconfirmed?

### 5. Decide the next cycle

Based on learnings, what's the next question? Refine, replace, or keep.

The full cycle should take days to weeks for most software design — fast enough that learnings stay fresh; slow enough that real building can happen.

## Worked examples

### Example 1: a new feature on an existing product

A team wants to add a new analytics dashboard. Iteration cycle:

- **Cycle 1**: paper sketches, internal review. Cheap; surfaces obvious structural questions.
- **Cycle 2**: clickable Figma prototype, 5 user interviews. Reveals which widgets users find valuable; which they ignore.
- **Cycle 3**: coded version, beta with 10% of users. Reveals real-world performance issues; surfaces edge cases.
- **Cycle 4**: refined version, full release with feature flag and monitoring. The dashboard is now mostly correct.

Each cycle costs more than the last; each replaces more assumptions with evidence.

### Example 2: a complete product redesign

A team redesigns a product. Without iteration: 18 months of design and rebuild; ship; users hate it; emergency rollback or "v2" project.

With iteration:

- **Phase 1** (3 months): redesign one critical flow. Ship behind a feature flag; A/B test. Refine based on data.
- **Phase 2** (3 months): redesign the next critical flow. Repeat.
- **Phase 3** (3 months): adopt the new design system across surfaces that haven't been redesigned. Cosmetic-only.

Total: 9 months, with each phase de-risked by data. Far better outcome than the 18-month bang.

### Example 3: API design

An API exposed to external developers can't be casually iterated — each version becomes a contract. But internal iteration before exposure can be intense:

- **Cycle 1**: design the API on paper; review with 3 internal teams.
- **Cycle 2**: implement a prototype; integrate from 1 internal client.
- **Cycle 3**: expose to 3 internal clients; gather feedback.
- **Cycle 4**: refine; release as `v1` to external partners.

The pre-release cycles are cheap; the post-release iteration is expensive.

### Example 4: an onboarding flow

The team wants to improve sign-up completion. Iteration:

- **Cycle 1**: instrument current flow; identify drop-off step. (Discovery.)
- **Cycle 2**: hypothesize fix; build A/B test variant. Run for 2 weeks.
- **Cycle 3**: analyze; ship winner; identify next drop-off step.
- **Cycle 4**: repeat.

Each cycle is data-driven and cheap. The cumulative improvement after 6–12 cycles often exceeds what any single redesign could achieve.

## Cross-domain examples

### Industrial product design

The development of any complex industrial product (a new car, an appliance, a medical device) involves dozens of prototype iterations — clay models, foam mockups, 3D-printed parts, working prototypes, pilot production. Each iteration reveals issues invisible at the previous fidelity.

### Architecture

Frank Lloyd Wright's process: many sketches, sometimes hundreds, before settling on a design. The Guggenheim went through years of iterative revision before construction.

### Software open-source

Open-source projects iterate continuously through patches, pull requests, and releases. Linux, the modern web stack, and every major open-source product evolved through tens of thousands of iteration cycles.

### Manufacturing (Toyota Production System)

Toyota's "kaizen" — continuous small improvements — is iteration applied to manufacturing process. Each shift makes small changes; over decades, the cumulative improvement is enormous.

### Scientific method

Science *is* iteration: hypothesize, experiment, observe, refine. The same loop applied to design produces similar accumulating quality.

## Anti-patterns

- **The big-bang ship.** A design developed in isolation for months, shipped without iteration, fails on contact with reality.
- **No iteration criteria.** Cycles without explicit "what are we trying to learn?" go on indefinitely without converging.
- **Cycles too long.** Quarterly cycles in a product that should be iterating weekly or daily. Learnings stale; the team forgets the previous cycle's context.
- **Cycles too short.** Daily redesigns that don't give the previous version time to be evaluated. Whiplash, no learning.
- **Iteration without measurement.** Cycles that produce changes but no evidence of whether the changes helped. Pure motion, no progress.
- **Skipping the "expose to reality" step.** Design cycles that stay inside the design team. Useful for some questions; useless for "does this work for users?"
- **Confusing prototypes with products.** A prototype is an iteration vehicle; a product is what survives multiple iterations. Treating prototypes as products produces brittle, unfinished work.

## Heuristics

1. **The "what would surprise us?" check.** Before each cycle, predict what will happen. After, compare. Surprises are the value of iteration.
2. **The cycle-time metric.** How long from "we have an idea" to "we have evidence about the idea"? Shorter is usually better.
3. **The fidelity ladder.** Are you using the cheapest fidelity that answers the question? Don't build a coded prototype when a sketch would do.
4. **The "stop iterating" criteria.** Define explicitly when iteration ends and shipping begins. Otherwise iteration can become procrastination.

## Related principles

- **`prototyping`** — the technique iteration relies on.
- **`development-cycle`** — the larger-scale iteration of requirement → design → develop → test.
- **`life-cycle`** — products iterate at the version-release cadence as well as within designs.
- **`factor-of-safety`** — both principles acknowledge the inevitability of unknowns.
- **`weakest-link`** — iteration finds the weakest link by exposing the design to stress.
- **`uncertainty-principle`** — observation changes the observed; iteration's instrumentation has its own effects.

## Sub-aspect skills

- **`iteration-design-vs-development`** — distinguishing healthy design iteration from costly development rework.
- **`iteration-prototype-fidelity`** — picking the right fidelity for each cycle's question.

## Closing

Iteration is the principle that separates teams who ship good products from teams who ship the products they planned. The teams that internalize "we will be wrong about something; let's find out which something cheaply" consistently outperform teams that try to be right the first time. Build the next cycle into every project plan.
