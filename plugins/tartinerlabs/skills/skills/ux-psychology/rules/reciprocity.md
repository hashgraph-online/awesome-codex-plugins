---
title: Reciprocity
impact: MEDIUM
tags: onboarding, sign-up, gradual-engagement, permissions, value-first
---

**Rule**: People respond to receiving something by giving something back. Deliver value before you ask for sign-up, permissions, data, or payment — and at the moment you ask, say what the user gets in return.

**Evidence**: Cialdini, *Influence* (1984) — reciprocity as a principle of compliance. Regan 1971 (*Journal of Experimental Social Psychology*) — people who received an unsolicited favour bought more raffle tickets from the giver. Wroblewski 2008, "Sign Up Forms Must Die" (*A List Apart*) and *Web Form Design* — gradual engagement: let people use the product before requiring an account.

### When Building

- **Value before account** — let people try the core action first (a lesson, a sample project, a calculation, a preview) and ask for an account when they want to save it
- **Value before permission** — ask for notifications after the user has seen why they are useful; ask for location when they tap "Find nearby" (`references/mobile.md`)
- **State the benefit at the ask** — "Create an account to keep your progress", "Allow notifications to know when your order ships" — the user's gain, not the product's need
- **Free tier or trial that delivers real value**, not a crippled demo
- **Ask for the minimum** — every field and permission is a cost to the user; ask for more later, when it is needed

### When Auditing

- Sign-up walls before any product value is shown (where the product allows a preview)
- Permission prompts at first launch
- Asks that explain the product's need ("We need your location") rather than the user's benefit
- Onboarding that collects data before showing the product

### Incorrect

```tsx
// First launch
useEffect(() => { Notifications.requestPermissionsAsync(); }, []);
```

### Correct

```tsx
// After the user places their first order
<Prompt
  title="Know when your order ships?"
  primary={{ label: "Turn on notifications", onPress: requestPermission }}
  secondary={{ label: "Not now", onPress: dismiss }}
/>
```

### Why This Matters

Asking before giving puts all the cost on the user before they know whether it is worth it, so many leave. Giving first earns the ask, and a permission requested when its benefit is obvious is easier to say yes to than one requested on launch.

### Alternatives

Some products genuinely need an account first — banking, health records, multi-user workspaces, anything with private data. Then make sign-up minimal and still state what the user gets. Gifts engineered to create a sense of obligation ("we gave you this, now you owe us") are manipulation (`rules/deceptive-patterns.md`).
