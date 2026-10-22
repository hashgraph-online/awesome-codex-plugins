---
title: Peak-End Rule
impact: LOW
tags: experience, endings, success, errors, emotion, flows
---

**Rule**: People judge an experience mostly by its most intense moment and its ending, not by its average. Make the end of key flows good, and soften the worst moments — errors, waits, and failures.

**Evidence**: Kahneman, Fredrickson, Schreiber & Redelmeier 1993, "When more pain is preferred to less: adding a better end" (*Psychological Science*) — people preferred a longer cold-water trial that ended less painfully. Redelmeier & Kahneman 1996 (*Pain*) — patients' memories of colonoscopy and lithotripsy tracked the peak and final moments of pain, not the duration.

### When Building

- **Good endings** — a clear success screen after checkout, sign-up, or publishing: what happened, what happens next, and the obvious next action
- **Soften the worst moments** — errors that explain and offer a way forward, failures that keep the user's work, waits with progress (`rules/system-status.md`, `rules/microcopy.md`); reassurance and tone at moments of risk are in `rules/emotional-design.md`
- **Leave on a positive note** — cancellation and account deletion confirm calmly and keep the door open; no guilt trips
- **Small moments of delight** where they fit the brand — a completion animation, a personal touch on a milestone — sparingly, so they stay special

### When Auditing

- Flows that end abruptly (back to a list with no confirmation) after significant effort
- Error and failure states that are generic or lose data
- Success screens with no next step
- Offboarding flows that shame or obstruct

### Incorrect

```tsx
onSuccess={() => router.replace("/orders")}
```

### Correct

```tsx
onSuccess={(order) => router.replace(`/orders/${order.id}/confirmed`)}
// Confirmed screen: "Order placed — arrives Thu 14 Mar", tracking link, "Continue shopping"
```

### Why This Matters

Users decide whether to come back based on how the experience felt, and memory compresses it to its peaks and its end. A frustrating error or a flat ending can outweigh an otherwise smooth flow.

### Alternatives

A strong ending does not fix a broken middle — the peak counts too, and the worst moment is often mid-flow. Delight belongs only after the basics work; animation timing and craft belong to an animation skill.
