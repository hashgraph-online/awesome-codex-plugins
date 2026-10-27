---
name: accessibility
description: Use when building or reviewing UI for accessibility — screen readers (VoiceOver, TalkBack), keyboard and focus, colour contrast, Dynamic Type and text scaling, reduced motion, touch targets, accessible forms, captions — or when auditing against WCAG 2.2, the European Accessibility Act, or before an App Store or production release. Covers web, Apple platforms, Android, and React Native/Expo. Not for general UX or visual styling (use ux-psychology).
license: MIT
allowed-tools: Read Glob Grep
compatibility: Any UI project; detects the platform — web and React Native/Expo first-class, Apple platforms (SwiftUI/UIKit) well supported, native Android (Compose) best-effort. Rules map to WCAG 2.2 level AA
metadata:
  short-description: Accessibility for web and mobile, mapped to WCAG 2.2.
---

You make UI usable by people with disabilities — blind and low-vision users with screen readers and magnification, keyboard and switch users, people with motor, hearing, vestibular, and cognitive disabilities. The target is WCAG 2.2 level AA, applied through each platform's own accessibility APIs.

## 1. Pick the Mode

Decide from the request; do not ask.

- **Build mode** — the task creates or changes UI. Apply the rules as constraints while writing the code: semantic elements, labels, focus, contrast, scaling. Mention a rule only when it changed a decision, in one line. No report.
- **Audit mode** — the user asks to review, audit, or check accessibility, or prepares a release. Produce the report in Step 4.

## 2. Detect the Platform

Read the manifest as prose and load **only** the matching guide:

| Platform | Detected by | Load |
|---|---|---|
| **Web** | `package.json` with a web framework, or HTML templates | `references/web.md` |
| **React Native / Expo** | `package.json` with `expo` or `react-native` | `references/cross-platform.md` |
| **Apple platforms** | `*.xcodeproj`, `Package.swift` with an app target | `references/apple.md` |
| **Android (Compose)** | `build.gradle(.kts)` with Compose | `references/android.md` |

React Native/Expo: add `references/apple.md` or `references/android.md` when behaviour differs per OS (screen reader focus, announcements, system settings). Expo web output also loads `references/web.md`. Flutter and other stacks: `references/cross-platform.md`.

## 3. Rules

Each rule file has **When building** constraints, **When auditing** checks, and the WCAG success criteria it covers. Read a rule when the UI in front of you involves what its "Applies to" column names.

| Rule | Impact | Applies to | File |
|---|---|---|---|
| Semantics, names, and roles | CRITICAL | every interactive element, custom controls, headings | `rules/semantics.md` |
| Keyboard and focus | CRITICAL | web, iPad/Mac/Android with keyboards, modals, menus | `rules/keyboard-focus.md` |
| Text alternatives | HIGH | images, icons, icon buttons, charts, maps | `rules/text-alternatives.md` |
| Contrast and colour | HIGH | text, icons, borders of controls, status colours | `rules/contrast-color.md` |
| Text scaling and reflow | HIGH | all text, layouts, fixed-height containers | `rules/text-scaling.md` |
| Forms and errors | HIGH | inputs, validation, sign-in, multi-step flows | `rules/forms.md` |
| Touch targets and gestures | HIGH | buttons, icons, drag, swipe, multi-finger gestures | `rules/targets-gestures.md` |
| Motion, flashing, and time | HIGH | animation, carousels, autoplay, timeouts | `rules/motion-time.md` |
| Announcements and status | MEDIUM | toasts, loading, live updates, async results | `rules/announcements.md` |
| Media | MEDIUM | video, audio, podcasts, animated explainers | `rules/media.md` |

## 4. Audit Mode

1. Scope: the files or screens named; otherwise every user-facing screen. In Claude Code, hand a whole-app or multi-screen audit to the `a11y-audit` agent when it is available, so the files it reads stay out of the main context.
2. Run the platform's automated checks first (listed in each platform guide) — then review by hand. Automated tools find only part of WCAG failures; most problems with names, focus order, and meaning need a person (or you, reading the code)
3. Check each screen against the rules whose "Applies to" matches it
4. Report, grouped by impact (CRITICAL first):

```
### CRITICAL — Semantics
- app/settings.tsx:58 — icon-only "trash" button has no accessible name → accessibilityLabel="Delete project" (WCAG 4.1.2)
```

End with the counts per impact and this limit, stated plainly: a code review cannot prove accessibility. Recommend testing the primary flows with the platform screen reader (VoiceOver, TalkBack, NVDA/JAWS), keyboard only, and the largest text size — and, where possible, with disabled users.

Fix nothing in audit mode unless asked; when asked, fix in impact order.

## Why It Matters

Around one in six people live with a significant disability (WHO), and accessible design helps everyone — captions in a noisy room, large targets on a moving train. It is also law in many markets: the European Accessibility Act applies to many digital products and services sold in the EU, and US courts and regulators apply the ADA to websites and apps. Both reference WCAG.

## Boundaries

- **UX psychology** (cognitive load, decisions, persuasion) belongs to `ux-psychology`; this skill covers access. They overlap at target size, colour-only signals, and clear errors — follow whichever is stricter.
- **Legal compliance** depends on jurisdiction and contract; this skill names the standards, it is not legal advice.
