---
name: principle-experience-first
description: Use on tradeoffs in product, UX, API ergonomics, or feature scope. When the convenient build and the better result for users point different ways, choose the better result. Ship fewer capabilities that are complete rather than many that are partial.
disable-model-invocation: true
---

# Experience first

If what is convenient to build differs from what serves the person using it, build for that person. A small number of finished capabilities beats a long list of half-done ones.

## When it applies

Product, UX, API-ergonomics, and feature-scope tradeoffs. This principle sets the target. The order in which you build toward it belongs to [principle-foundational-thinking](../principle-foundational-thinking/SKILL.md).

## What to do

1. Require a justification for every feature, control, and option. Cut the ones without one.
2. Ship fewer things at higher polish.
3. Prototype design decisions in throwaway form, such as plain HTML, before writing production code. Changes there cost minutes.
4. Attend to the details users hit: transitions, alignment, spacing, feedback, and error states.
5. Keep the core loop tight. Every feature serves the central workflow or stays out of its way.
6. Define "user" broadly: the end user of a UI, the colleague importing your library, and the next maintainer. A secrets client that requires five constructor arguments to fetch one value is shaped for its implementer. Describe impact from each consumer's point of view.
7. Foundations exist to serve the experience.

Secure defaults are part of the experience. If the safe path takes extra steps, users take the unsafe one, so make the safe path the short one.

## The failure it prevents

Option sprawl, rough edges shipped because they were convenient, and APIs shaped for the implementer instead of the caller.

## Done when

Each shipped element is justified and polished from its consumer's point of view.

Related: [principle-foundational-thinking](../principle-foundational-thinking/SKILL.md), [principle-exhaust-the-design-space](../principle-exhaust-the-design-space/SKILL.md).
