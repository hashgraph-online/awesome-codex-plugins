---
title: Aesthetic-Usability Effect
impact: LOW
tags: polish, perception, trust, usability-testing
---

**Rule**: Attractive interfaces are perceived as easier to use and more trustworthy — which also hides real usability problems. Polish what works; never use polish to cover what doesn't.

**Evidence**: Kurosu & Kashimura 1995 (CHI) — users rated more attractive ATM layouts as easier to use, even with identical functionality. Tractinsky, Katz & Ikar 2000, "What is beautiful is usable" (*Interacting with Computers*) — perceived aesthetics influenced perceived usability before and after use. Lindgaard, Fernandes, Dudek & Brown 2006 (*Behaviour & Information Technology*) — judgements of a web page's visual appeal form within 50 ms and largely agree with judgements after longer viewing. Tuch et al. 2012 (*International Journal of Human-Computer Studies*) — pages with low visual complexity and high prototypicality (looking like a typical site of their kind) were rated most appealing, with effects visible within 17–50 ms. Both measured appeal, not trust or usability.

### When Building

- **Function first** — get the flow, labels, and feedback right; then polish
- **Consistent, tidy presentation** — alignment, spacing, and a consistent component set build trust, especially on payment and sign-up screens
- **Polish the moments of trust** — pricing, checkout, permission asks, and first run are where a rough look costs the most
- **The first screen sets the judgement** — the landing page's top section and an app's first screen are judged at a glance; keep them visually simple and close to the familiar layout for their category (`rules/jakobs-law.md`)
- Visual styling decisions themselves (colour, type, spacing systems) are out of this skill's scope

### When Auditing

- Inconsistent or broken-looking UI on trust-critical screens (checkout, sign-up, settings that handle money or data)
- First screens that are visually busy, or depart from the layout users expect for the category without a clear gain
- Polished screens hiding functional problems: unclear labels, missing feedback, dead ends — check function before praising looks
- Test plans that ask "do you like it?" instead of observing whether people complete the task

### Incorrect

```tsx
// Usability test question
"How do you like the new checkout design?"
```

### Correct

```tsx
// Task-based test
"Buy the blue shirt in size M and have it delivered to your work address."
```

### Why This Matters

Users forgive minor problems in an attractive product and distrust a rough one — so polish raises perceived quality. But in testing, that same forgiveness masks problems that will hurt users who are less patient.

### Alternatives

Internal tools and early prototypes can skip polish entirely when the goal is to learn whether the flow works. Polish never substitutes for fixing a broken flow — judge usability by task success, not by how the screen looks.
