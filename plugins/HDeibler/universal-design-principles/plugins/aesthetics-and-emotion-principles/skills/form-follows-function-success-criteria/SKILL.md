---
name: form-follows-function-success-criteria
description: 'Use this skill when the team is in a form-vs-function debate and needs to step back to define what "success" actually means for the design. Trigger when stakeholders disagree about visual treatment, when a design feels off and no one can articulate why, or when reviewing a design against an unclear brief. Sub-aspect of `form-follows-function`; read that first.'
---

# Defining success criteria explicitly

The book's reframe of form-follows-function: instead of asking "what should be omitted?", ask "what's critical to this design's success?". Then weigh form and function against those criteria. The discipline is making success criteria explicit rather than assuming.

## Common implicit success criteria

Without explicit criteria, teams default to assumed criteria — often without alignment:

- Designer assumes: visual elegance.
- Engineer assumes: implementation simplicity.
- Product manager assumes: feature completeness.
- Marketing assumes: brand differentiation.
- Stakeholder assumes: stakeholder approval.

When the assumed criteria differ, every design decision becomes contentious. Explicit criteria make decisions defensible.

## Naming success criteria

For a given design, candidates include:

- **User performance** (speed, accuracy, error rate).
- **User satisfaction / preference.**
- **Business outcomes** (conversion, retention, revenue).
- **Brand differentiation** (does this look unmistakably like us?).
- **Accessibility / inclusion.**
- **Implementation simplicity / cost.**
- **Long-term maintainability.**
- **Aesthetic / emotional response.**

Most designs serve multiple criteria; the question is which dominate when they conflict.

## A team exercise

For a design in dispute:

1. **List the criteria** the design should serve.
2. **Rank them** by priority for this specific surface.
3. **For each candidate design choice**, evaluate against the top 2–3 criteria.
4. **Pick the choice** that does best on top criteria; accept trade-offs on lower ones.

This conversation surfaces hidden disagreements about what the design is *for*. Resolving those usually resolves the surface debates.

## Worked example

A landing-page hero section is in dispute. Designer wants minimalist (one headline, one CTA); marketing wants rich (headline, deck, three feature bullets, social proof, primary + secondary CTA).

Without explicit criteria, the debate is irresolvable. Each side has a defensible position.

With explicit criteria:

- **Conversion rate**: rich variants tend to convert better in A/B tests for new visitors. Marketing's position favored.
- **Brand differentiation**: minimalist often differentiates better in cluttered spaces. Designer's position favored.
- **Mobile experience**: minimalist tends to perform better on small screens. Designer's position favored.

If conversion rate is the dominant criterion, marketing wins this round; ship rich and A/B test. If brand differentiation is dominant, designer wins. The criteria choice resolves the debate.

## When form genuinely competes with function

Some legitimate trade-offs:

- **Visual polish vs. load time** — animations, large images cost performance.
- **Brand differentiation vs. convention adherence** — distinctive design departs from familiar patterns.
- **Aesthetic minimalism vs. discoverability** — fewer visible elements = harder to find features.
- **Custom vs. native components** — custom looks distinctive but is more expensive and risks accessibility.

Each trade-off should be made deliberately, with success criteria informing the choice.

## Anti-patterns

- **Implicit criteria.** Each team member assumes different criteria; debates are unresolvable.
- **All-criteria-must-be-served.** Trying to optimize for everything produces designs that serve nothing well.
- **Designer-as-arbiter.** "I'm the designer, so I get to decide" — without explicit criteria, this is unconvincing.
- **Stakeholder-as-arbiter.** "The CEO likes it" — same problem.

## Heuristics

1. **The criteria-naming exercise.** Before designing, list and rank success criteria. Get team alignment.
2. **The trade-off-explicitness check.** When trading off, name what's being sacrificed. "We're sacrificing brand differentiation for convention adherence."
3. **The dominant-criterion test.** When stuck, ask: which criterion matters most for *this surface* (not in general)? That answer often resolves.

## Related sub-skills

- **`form-follows-function`** (parent).
- **`form-follows-function-as-axiom`** — the descriptive interpretation.
- **`hierarchy-of-needs`** (interaction) — Maslow-derived ordering of design needs.
- **`flexibility-usability-tradeoff`** — explicit trade-off framing.
