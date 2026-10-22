---
title: Jakob's Law & Consistency
impact: HIGH
tags: conventions, consistency, platform, mental-models, navigation
---

**Rule**: Users spend most of their time in other products and expect yours to work the same way. Follow platform and category conventions, and be consistent within your own product.

**Evidence**: Nielsen 2000, "End of Web Design" (NN/g) — the origin of Jakob's law: users spend most of their time on other sites. Nielsen's heuristics #2 (match between system and the real world) and #4 (consistency and standards) — external consistency with platforms and internal consistency within the product.

### When Building

- **Platform conventions** — use the OS's navigation, back behaviour, dialogs, and pickers (`references/apple.md`, `references/android.md`); on the web, the patterns users already know (logo links home, cart top-right, search at the top)
- **Category conventions** — a checkout looks like checkouts users have used; a calendar like calendars
- **Internal consistency** — the same action has the same name, icon, and position everywhere; the same component behaves the same way on every screen
- **Match the user's world** — their words, their order of steps, their units and formats (dates and currencies per locale)
- **In an existing codebase**, reuse the components and patterns already there before introducing new ones

### When Auditing

- Custom controls replacing standard ones (custom back buttons, custom pickers, custom scrollbars) without a clear gain
- The same action labelled or placed differently across screens ("Remove" here, "Delete" there; save top-right on one screen, bottom on another)
- Several components for the same job (three button styles for primary actions)
- Icons used with a meaning other than the common one

### Incorrect

```tsx
// Settings: "Remove member" bottom-left; Billing: "Delete card" top-right
```

### Correct

```tsx
// Both use the same <DestructiveAction label="Remove …" /> in the same position
```

### Why This Matters

Every unfamiliar pattern costs learning time and a chance of error. Users don't admire novel navigation — they get lost in it, and blame the product.

### Alternatives

Break a convention when the improvement is large and teachable — pull-to-refresh and swipe actions were once novel. Do it deliberately, give the new pattern a visible signifier (`rules/signifiers.md`), and test it with users who have never seen it.
