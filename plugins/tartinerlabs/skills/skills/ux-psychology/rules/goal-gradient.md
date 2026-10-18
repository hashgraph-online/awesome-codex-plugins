---
title: Goal Gradient & Endowed Progress
impact: LOW
tags: progress, steppers, checklists, onboarding, motivation
---

**Rule**: Effort increases as people get closer to a goal, and progress they already have pulls them forward. Show progress, and count real steps already done.

**Evidence**: Hull 1932 (*Psychological Review*) — the goal-gradient hypothesis. Kivetz, Urminsky & Zheng 2006, "The Goal-Gradient Hypothesis Resurrected" (*Journal of Marketing Research*) — coffee-card members bought more often as they neared a free coffee. Nunes & Drèze 2006, "The Endowed Progress Effect: How Artificial Advancement Increases Effort" (*Journal of Consumer Research*) — car-wash cards needing 8 stamps were completed by 19% of customers, versus 34% for 10-stamp cards that came with 2 already stamped, though both needed 8 more washes.

### When Building

- **Show progress in multi-step flows** — "Step 2 of 4", a stepper, or a progress bar, so the end is visible
- **Count real completed steps** — "Account created ✓" as step 1 of a setup checklist; the user really did it, and starting partly done makes finishing more likely
- **Keep the remaining steps few** — break long flows into sections and show progress per section
- **Celebrate completion** briefly and show what is now unlocked (`rules/peak-end.md`)
- **Setup checklists** for SaaS onboarding — short, with done items checked and the next one highlighted

### When Auditing

- Multi-step flows with no indication of length or position
- Progress bars that jump backwards or stall at the end
- Setup checklists that start at zero when the user has already done real steps
- Checklists longer than a handful of items

### Incorrect

```tsx
<Text>Complete your profile</Text>
```

### Correct

```tsx
<Checklist
  items={[
    { label: "Create account", done: true },
    { label: "Add your first project", done: false },
    { label: "Invite a teammate", done: false },
  ]}
/>
```

### Why This Matters

Visible, achievable progress keeps people going through setup and onboarding — the stage where most products lose them.

### Alternatives

Progress must be real: a bar that starts at 30% for nothing, or invented steps to look "almost done", is deceptive (`rules/deceptive-patterns.md`). For short flows (one or two screens), a progress indicator adds clutter without benefit.
