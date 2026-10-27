---
title: Commitment & Consistency
impact: MEDIUM
tags: onboarding, foot-in-the-door, small-steps, sign-up, setup
---

**Rule**: People who take a small step are more likely to take the next one. Start flows with a small, easy, meaningful step — not the hardest question.

**Evidence**: Freedman & Fraser 1966 (*Journal of Personality and Social Psychology*) — the foot-in-the-door effect: people who agreed to a small request were far more likely to agree to a larger one later. Cialdini, *Influence* (1984) — commitment and consistency as a principle of compliance.

### When Building

- **Easy first step** — open onboarding and sign-up with the simplest, most engaging question (a goal, a name, a preference), not payment details or a long form
- **Each step a real step** — every action should move the user toward their own goal, so continuing is consistent with what they already chose
- **Sequence by effort** — light questions first, heavier ones (payment, verification, invites) once the user is invested and sees the value (`rules/reciprocity.md`)
- **Reflect choices back** — "You're learning Spanish for travel" on the next screen reinforces the commitment and personalises the flow
- **Save partial progress** so an interrupted user resumes rather than restarts

### When Auditing

- Flows that open with the hardest or most sensitive ask
- Multi-step setup that discards earlier answers if the user leaves
- Onboarding questions whose answers visibly change nothing
- Commitments the user cannot easily reverse later

### Incorrect

```tsx
// Onboarding step 1 of 5
<CardDetailsForm />
```

### Correct

```tsx
// Step 1: one tap, about the user's goal
<ChoiceList title="What do you want to get done first?" options={goals} />
```

### Why This Matters

The first step sets whether a user enters the flow at all. A small, meaningful start gets people moving; a heavy one loses them before they have seen any value.

### Alternatives

When a heavy step is unavoidable early (identity verification for a bank), say upfront how long the whole flow takes. Never use small commitments to escalate users into something they would not agree to if asked directly — that is manipulation (`rules/deceptive-patterns.md`).
