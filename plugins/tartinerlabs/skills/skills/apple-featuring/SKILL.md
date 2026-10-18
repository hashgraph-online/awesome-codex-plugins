---
name: apple-featuring
description: Use when preparing an Apple platform app for App Store featuring or the Apple Design Awards — readiness reviews before a launch or major update, featuring nominations in App Store Connect, nomination timing and pitch, choosing an ADA category, or asking how to get an app noticed by Apple. Covers iOS, iPadOS, macOS, visionOS, watchOS, and tvOS apps and games. Not for general UX reviews (use ux-psychology).
license: MIT
allowed-tools: Read Glob Grep
compatibility: Apple platform apps and games distributed on the App Store; reviews the codebase, plus App Store metadata (screenshots, descriptions) when it is in the repo or provided
metadata:
  short-description: App Store featuring and Apple Design Award readiness.
---

You help an Apple platform app get noticed by Apple: App Store featuring, and the Apple Design Awards (ADA). Be honest about the limits — Apple publishes no checklist for featuring and no public entry process or rubric for the ADA. Everything here raises the odds; nothing guarantees selection.

## 1. What the User Needs

Decide from the request; ask only when it is unclear.

| Request | Do |
|---|---|
| "Is my app ready?" / readiness review | Steps 2–4, then the report |
| "How do I nominate?" / timing | `references/nomination.md` only |
| "Which ADA category fits?" | `references/criteria.md`, then Step 3 |
| "Write the nomination pitch" | Step 2, then the pitch section of `references/nomination.md` |

## 2. Understand the App

From the codebase, README, and App Store metadata if present: what the app does, for whom, its platforms, its signature interaction (the one thing it does better than anything else in its category), and whether it is an app or a game. Ask the user only for what the code cannot show — the audience, the competition, and the planned launch or update date.

## 3. Map to Apple's Criteria

Read `references/criteria.md`. For each of Apple's seven featuring considerations, note where the app is strong and where it is weak. Then rank the six ADA categories by fit — a strong candidate targets one category and is the best in its genre at that category's description, not average at all six. Games also get Apple's game-specific considerations.

## 4. Readiness Review

Work through `references/readiness.md`: first-launch impression, platform fit, accessibility, localization, quality, and the product page. When the `ux-psychology` skill is available, use it for depth on the UX findings rather than repeating its rules here.

## 5. Report

```
## Featuring readiness — <App>

Strongest fit: <ADA category> — <one sentence on why>
Signature interaction: <what to lead the pitch with>

### Blocking (fix before nominating)
- <finding> → <fix>

### Strengthen
- <finding> → <fix>

### Nomination plan
- Type: App Launch | App Enhancements | New Content
- Submit by: <publish date minus at least 3 weeks>
- Supporting links: <demo video, TestFlight public link, press kit, …>
- Helpful Details: <accessibility, inclusivity, what is unique about the app or team>
```

End with what cannot be judged from the code (uniqueness against competitors, delight, real-world impact) and the limit stated plainly: Apple's selection is editorial and not public.

## Boundaries

- **Facts change.** Apple revises its featuring process and award categories, and its own pages have disagreed (two weeks vs three weeks of lead time). When a date or rule matters, tell the user to confirm it on Apple's current pages, linked in the references.
- **No gaming the system.** No fake reviews, incentivised ratings, or misleading screenshots — they breach the App Store Review Guidelines and undermine the trust featuring depends on.
- **UX depth** belongs to `ux-psychology`; platform conventions to its `apple.md` guide; a full accessibility audit is a separate job.
