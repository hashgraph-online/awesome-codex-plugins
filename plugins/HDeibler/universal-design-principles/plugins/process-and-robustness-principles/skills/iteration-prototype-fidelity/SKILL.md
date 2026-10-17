---
name: iteration-prototype-fidelity
description: 'Use this skill when picking the appropriate prototype fidelity for an iteration cycle — sketches vs. wireframes vs. clickable Figma vs. code prototypes vs. production beta. Trigger when planning a research session, when a project is over- or under-investing in prototypes, or when the prototype fidelity is mismatched to the question being asked. Sub-aspect of `iteration`; read that first.'
---

# Picking the right prototype fidelity

Each prototype fidelity is a tool with a cost and a use. Sketches are nearly free but answer only structural questions. Code prototypes cost more but answer performance and behavior questions. The discipline is matching fidelity to the question being asked — not always going lowest, not always going highest.

## The fidelity ladder

From cheapest to most expensive:

### 1. Paper sketches

A pen and paper. Cost: 5–30 minutes per option. Answers:

- Does this layout structure make sense?
- Are the right elements present?
- What's the rough information architecture?

Doesn't answer:

- How does it feel to interact with this?
- Does the typography work?
- Are colors right?

When to stop here: structural questions only; very early discovery.

### 2. Wireframes (low-fidelity digital)

Boxy, monochrome, no real content. Cost: 1–4 hours per screen. Answers:

- Layout proportions on screen.
- Reading order and hierarchy.
- Information grouping.

Doesn't answer:

- Visual style.
- Interaction feel.
- Real-content edge cases.

When to stop here: when structure is the question; before visual design begins.

### 3. Mockups (high-fidelity static)

Real fonts, colors, content; static image. Cost: 4–16 hours per screen. Answers:

- Visual style.
- Polish and brand fit.
- Stakeholder alignment ("does this look right?").

Doesn't answer:

- Interaction.
- Edge cases.
- Performance.

Common misuse: building high-fidelity mockups before structure is settled. The mockups become anchors that prevent structural changes.

### 4. Clickable prototypes (Figma, Framer, ProtoPie)

Mockups linked together with click-throughs. Cost: 1–3 days per major flow. Answers:

- Does the interaction sequence make sense?
- Where do users get confused?
- Are the affordances clear?

Doesn't answer:

- Real-content edge cases.
- Performance.
- Cross-device behavior.

Sweet spot for most user research; cheap enough to revise, real enough to test.

### 5. Code prototypes

Working code with real or seeded data, but not production-ready. Cost: 1–3 weeks. Answers:

- Performance.
- Cross-device behavior.
- Real-data edge cases.
- Implementation complexity.

Doesn't answer:

- Long-term scale issues.
- Production reliability.

Useful when implementation has unknowns or when performance is a concern.

### 6. Production beta

Shipped to a small percentage of real users. Cost: high (full implementation). Answers:

- Real usage at scale.
- Bug rates.
- Long-term retention.
- Real edge cases.

Doesn't answer (well):

- Counterfactual: would users have liked the alternative more?

When to use: late-stage validation; gradual rollout.

## Picking the right fidelity for each question

A useful rule: pick the **cheapest fidelity that answers the question**.

| Question | Recommended fidelity |
|---|---|
| Does the IA make sense? | Sketches or wireframes |
| Is the visual style right? | High-fidelity mockup |
| Does the flow work for users? | Clickable prototype + 5 interviews |
| Will the load time be acceptable? | Code prototype with seeded data |
| Will users adopt it? | Production beta with measurement |

Going higher than needed wastes time. Going lower means you don't get the answer.

## When to stay low fidelity longer

Counterintuitively, low fidelity is often better for user research:

- **Users critique the prototype's polish, not its structure.** A high-fidelity mockup gets feedback like "I don't love this blue" instead of "I don't understand what this page is for." The polish distracts.
- **Low fidelity invites criticism.** Users feel comfortable suggesting changes to a sketch; they hesitate to challenge a polished mockup.
- **Low fidelity is faster to revise.** You can make 5 sketch variations in the time it takes to make 1 mockup variation.

For early-stage user research, sketches and wireframes often outperform high-fidelity prototypes despite "feeling unprofessional."

## When to go high fidelity earlier

A few cases where polish matters:

- **Stakeholder buy-in.** Some stakeholders only react meaningfully to high-fidelity mockups. Build them for those reviews.
- **Brand-perception research.** Testing whether a design feels like the brand requires polish.
- **Competitive comparison.** Comparing your design's appeal to a competitor's polished product needs comparable polish.

## Anti-patterns

- **Pixel-perfect early.** Polishing visual details before structure is settled. The pixels then have to be redone.
- **Test with the prototype that was easy to build.** Using a Figma prototype to test load-time performance, or a code prototype to test layout structure. Wrong fidelity for the question.
- **Skip prototyping entirely.** "We're agile, we'll just build it." Then iterate expensively in production.
- **Production-quality prototypes.** Building prototypes to production code quality. Defeats the cost advantage of prototyping.
- **Treating prototypes as products.** Shipping a prototype as the product because it "works." Usually missing edge cases, accessibility, performance.

## Worked example: layered prototyping for a new feature

A team designs a new collaboration feature.

- **Week 1**: paper sketches; internal review. Decide structural concept.
- **Week 2**: wireframes; design crit. Refine information architecture.
- **Week 3**: clickable Figma prototype; 5 user interviews. Discover one critical flow is confusing; redesign.
- **Week 4**: refined Figma prototype; 5 more interviews. Confirm the redesign works.
- **Week 5–6**: code prototype with real data. Surface a performance issue; design adapts.
- **Week 7–10**: production build. Ship to 10% beta.
- **Week 11–12**: full release.

Each cycle uses the cheapest fidelity that answers the cycle's question.

## Heuristics

1. **The "what question is this prototype answering?" check.** Before building the prototype, name the question. Pick the fidelity that answers it.
2. **The "could a sketch have caught this?" retrospective.** When issues are discovered late, ask whether earlier prototyping at lower fidelity would have caught them.
3. **The user-reaction signal.** If users critique your prototype's visual polish, you're at too high fidelity for the question. Drop down.

## Related sub-skills

- **`iteration`** (parent).
- **`iteration-design-vs-development`** — moving up the fidelity ladder is part of moving from design to development.
- **`prototyping`** — the broader technique.
- **`factor-of-safety`** — prototypes are a form of designing-with-margin.
