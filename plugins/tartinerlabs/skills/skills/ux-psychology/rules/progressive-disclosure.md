---
title: Progressive Disclosure
impact: MEDIUM
tags: complexity, advanced-options, settings, onboarding, teslers-law
---

**Rule**: Show what most people need first; put advanced and rare options one deliberate step away. Complexity cannot be removed, only moved — move it to the system or to later, not onto the user.

**Evidence**: Nielsen 2006, "Progressive Disclosure" (NN/g) — deferring advanced features improves learnability, efficiency, and error rates, provided the initial set contains what most users need. Tesler's law of conservation of complexity, from Larry Tesler's interview in Saffer, *Designing for Interaction* (2006) — every process has irreducible complexity; the question is who handles it.

### When Building

- **Decide the first layer from usage** — what most users need on most visits; everything else behind "Advanced", "More options", a disclosure, or a details screen
- **One level deep** — a second layer of hidden options inside the first is where things get lost
- **Label the door clearly** — "Advanced settings" or "More filters (3 active)", so people know what is behind it and whether it is in use
- **Absorb complexity in the system** — smart defaults, inference (country from locale, timezone from device), and sensible automation before asking the user (`rules/defaults.md`)
- **Onboarding** teaches only what is needed for the first task; the rest is discovered in context later

### When Auditing

- Every option shown at once on a create or settings screen
- Frequently used controls hidden behind "More" or a second click
- Hidden options that are active with no indication on the collapsed state
- Disclosure nested two or more levels deep

### Incorrect

```tsx
<CreateProjectForm fields={allTwentyFields} />
```

### Correct

```tsx
<CreateProjectForm fields={[name, template]} />
<Disclosure label="Advanced settings">
  <AdvancedFields />
</Disclosure>
```

### Why This Matters

A first screen with everything on it overwhelms newcomers and slows experts who must scan past rarely used options. Disclosure lets one screen serve both — if the split matches real usage.

### Alternatives

Hiding what users frequently need costs more than showing it. Expert tools often benefit from everything visible (dense toolbars, full filter panels). When usage data is missing, show more and measure rather than hiding by guesswork.
