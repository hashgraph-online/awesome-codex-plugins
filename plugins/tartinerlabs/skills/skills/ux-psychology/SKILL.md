---
name: ux-psychology
description: Use when designing, building, or reviewing a screen, flow, or page — landing and marketing pages, onboarding, sign-up, navigation, forms, settings, dashboards, tables, pricing, checkout, empty states, error messages, permission prompts — or when a UI feels confusing, cluttered, or slow. Applies UX psychology (Hick, Fitts, cognitive load, Gestalt, defaults, reciprocity) to web/SaaS, Apple platforms (iOS, iPadOS, macOS, visionOS, watchOS, tvOS), Android, and React Native/Expo apps. Not for visual styling, colour, or animation tuning.
license: MIT
allowed-tools: Read Glob Grep
compatibility: Any UI project; detects the platform — web/SaaS and React Native/Expo first-class, Apple platforms (SwiftUI/UIKit/AppKit) well supported, native Android (Compose) best-effort
metadata:
  short-description: UX psychology for screens and flows.
---

You apply how people perceive, decide, and remember to the UI being built or reviewed. Every rule cites the research it rests on and says when it does not apply — these are strong predictions about people, not laws, so a rule that does not fit the product is set aside, not forced.

## 1. Pick the Mode

Decide from the request; do not ask.

- **Build mode** — the task creates or changes UI. Apply the rules as constraints while writing the code. Stay quiet about them: mention a principle only when it changed a decision, in one line (e.g. "kept one primary button — von Restorff"). No report.
- **Audit mode** — the user asks to review, audit, or critique the UX, or asks why users drop off, get confused, or don't convert. Produce the report in Step 4.

## 2. Detect the Platform

Read the manifest as prose and load **only** the matching guides:

| Platform | Detected by | Load |
|---|---|---|
| **Web / SaaS** (apps, landing and marketing pages) | `package.json` with a web framework (Next.js, Vite, Remix, Astro, Nuxt, SvelteKit, …), or HTML templates | `references/web.md` |
| **React Native / Expo** | `package.json` with `expo` or `react-native` | `references/mobile.md` + `references/cross-platform.md` |
| **Apple (iPhone, iPad, Mac, Vision Pro, Watch, TV)** | `*.xcodeproj`, `Package.swift` with an app target | `references/apple.md`, plus `references/mobile.md` for iPhone and iPad |
| **Android (Compose)** | `build.gradle(.kts)` with Compose | `references/mobile.md` + `references/android.md` |

React Native/Expo: add `references/apple.md` or `references/android.md` only when the change behaves differently per OS (back navigation, sheets, pickers, haptics, system dialogs). Expo web output also loads `references/web.md`. For a landing, marketing, or launch page, also load `references/landing-pages.md`. A monorepo with several apps loads the guide for the app being touched. For another UI stack (Flutter, Kotlin Multiplatform), use `references/cross-platform.md` and the closest native guide.

## 3. Rules

Each rule file has a **When building** constraint and a **When auditing** check. Read a rule when the screen in front of you involves what its "Applies to" column names.

| Rule | Impact | Applies to | File |
|---|---|---|---|
| Deceptive patterns | CRITICAL | urgency, cancellation, consent, upsells, pricing | `rules/deceptive-patterns.md` |
| Error prevention & recovery | HIGH | forms, destructive actions, input formats, exits | `rules/error-prevention.md` |
| Cognitive load | HIGH | multi-step flows, dense screens, information overload, interruptions, anything to remember | `rules/cognitive-load.md` |
| System status & micro-feedback | HIGH | any action, loading, saving, async work | `rules/system-status.md` |
| Jakob's law & consistency | HIGH | navigation, platform conventions, repeated patterns | `rules/jakobs-law.md` |
| Fitts's law | HIGH | buttons, touch targets, toolbars, destructive actions | `rules/fitts-law.md` |
| Signifiers | HIGH | anything tappable/clickable, gestures, hover | `rules/signifiers.md` |
| Microcopy | HIGH | button labels, errors, empty states, confirmations | `rules/microcopy.md` |
| Hick's law | MEDIUM | menus, plan pickers, settings, option lists | `rules/hicks-law.md` |
| Gestalt grouping | MEDIUM | layout, forms, cards, lists | `rules/gestalt-grouping.md` |
| von Restorff (primary action) | MEDIUM | screens with several actions, CTAs | `rules/von-restorff.md` |
| Progressive disclosure | MEDIUM | advanced options, settings, onboarding | `rules/progressive-disclosure.md` |
| Scanning & attention | MEDIUM | content pages, nav order, banners, announcements | `rules/scanning.md` |
| Defaults & pre-filling | MEDIUM | forms, settings, sign-up, checkout | `rules/defaults.md` |
| Reciprocity | MEDIUM | onboarding, sign-up walls, permission and payment asks | `rules/reciprocity.md` |
| Commitment | MEDIUM | onboarding, sign-up, multi-step setup | `rules/commitment.md` |
| Social proof | MEDIUM | landing, pricing, sign-up | `rules/social-proof.md` |
| Emotional design | MEDIUM | payment, irreversible actions, errors, waits, first run, success, offboarding | `rules/emotional-design.md` |
| Goal gradient & endowed progress | LOW | steppers, progress bars, setup checklists | `rules/goal-gradient.md` |
| Peak-end | LOW | flow endings, success and error moments | `rules/peak-end.md` |
| Aesthetic-usability | LOW | first impressions, landing pages, polish vs function trade-offs, test sessions | `rules/aesthetic-usability.md` |

`rules/deceptive-patterns.md` overrides every other rule: when a persuasion rule (defaults, reciprocity, commitment, social proof, goal gradient) would work against the user's interest, it is a deceptive pattern, not a technique.

## 4. Build Mode

**New product or flow, nothing built yet** — settle these before the first screen, from the request and the codebase (ask only for what neither answers):

1. Who the user is and their one to three main tasks — for a landing or marketing page, why they would care to buy
2. The one primary action of each screen
3. The navigation pattern the platform expects (tab bar, sidebar, stack)
4. How dense the information should be (glanceable consumer app vs expert tool)
5. Where people will drop off — first run, empty states, sign-up and permission asks
6. Where the user will feel exposed — paying, deleting, sending, granting access — and how they should feel at the end (`rules/emotional-design.md`)

Then build with the rules as constraints.

**Existing UI** — follow the conventions already in the codebase (internal consistency is part of `rules/jakobs-law.md`), and apply the rules to the part being changed. Do not redesign screens nobody asked about.

## 5. Audit Mode

1. Scope: the files, screens, or flows named; otherwise every user-facing screen. In Claude Code, hand a whole-app or multi-screen audit to the `ux-audit` agent when it is available, so the files it reads stay out of the main context.
2. Map each screen's job and primary action from its code before judging it.
3. Check each screen against the rules whose "Applies to" matches it, and the platform guide.
4. Report, grouped by impact (CRITICAL first):

```
### HIGH — Fitts's law
- app/(tabs)/settings.tsx:42 — "Delete account" sits 8pt from "Save" → move it to a separate section at the bottom, behind a confirmation
```

End with the counts per impact, then this limit, stated plainly: these principles predict problems but cannot confirm them. Recommend checking the top findings with 3–5 real users per distinct user type, and testing again after fixing.

Fix nothing in audit mode unless asked; when asked, fix in impact order.

## Boundaries

- **Visual styling** (colour palettes, type scales, spacing systems) and **animation timing** (easing, springs, duration) are out of scope — defer to the `visual-design` skill when it is available, and to an animation skill when one is installed. This skill decides *whether* an action needs feedback; those decide how it looks and moves.
- **Accessibility** overlaps where noted (target size, colour-only signals, focus, input purpose); when the `accessibility` skill is available, apply it alongside this one while building UI, and use it for full WCAG audits.
