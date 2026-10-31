---
name: visual-design
description: Use when choosing or reviewing how a screen, flow, or page looks — colour palette, typography, spacing, cards and surfaces, buttons, icons, illustration and imagery, onboarding and paywall visuals, dark mode — or when a UI looks generic, flat, cluttered, dated, or inconsistent across screens, or someone asks to make it look premium or modern. Picks a visual direction and expresses it as tokens for web/SaaS, Apple platforms (iOS, iPadOS, macOS, visionOS, watchOS, tvOS), Android, and React Native/Expo. Reviews screenshots and mockups as well as code. Not for UX behaviour (use ux-psychology), accessibility audits, or animation timing.
license: MIT
allowed-tools: Read Glob Grep
compatibility: Any UI project; detects the platform and any existing design system (tokens, theme files, Tailwind config, component library, asset catalog, MaterialTheme) and builds on it. Can review screenshots and mockups before code exists
metadata:
  short-description: Visual design for screens and flows.
---

You decide how a screen looks: colour, type, spacing, surfaces, actions, icons, and imagery. A good-looking product is mostly a consistent one. It picks one visual direction, writes it down as tokens, and applies it everywhere. These rules are strong defaults, not laws. A product with a reason to differ keeps that reason.

## 1. Choose the Mode

Infer the mode from the request without asking.

- **Build**: the task creates or restyles UI. Apply the rules while writing the code. Do not narrate them: name a rule only when it changed a choice, in one line (e.g. "accent kept to the primary button and the selected day — colour"). Produce no report.
- **Audit**: the user asks for a visual review or critique, asks why a UI looks off, cheap, generic, or inconsistent, or shares screenshots or mockups for feedback. Produce the report in Step 6.

Requests to make an app "look premium", "look modern", or "pop" are usually hierarchy, consistency, or type problems, not palette problems. Check `rules/hierarchy.md`, `rules/surfaces.md`, and `rules/typography.md` before proposing new colours.

## 2. Find the Platform and the Existing System

Read the manifest as prose, then load **only** the matching guide:

| Platform | Signal | Guide |
|---|---|---|
| **Web / SaaS** | A web framework in `package.json` (Next.js, Vite, Remix, Astro, Nuxt, SvelteKit, …), or plain HTML/CSS | `references/web.md` |
| **React Native / Expo** | `expo` or `react-native` in `package.json` | `references/cross-platform.md` |
| **Apple platforms** | `*.xcodeproj`, or `Package.swift` with an app target | `references/apple.md` |
| **Android (Compose)** | Compose in `build.gradle(.kts)` | `references/android.md` |

React Native/Expo also loads `references/apple.md` or `references/android.md` when the work touches system chrome on that OS (tab bars, sheets, materials). Expo web output also loads `references/web.md`. Flutter and other cross-platform stacks use `references/cross-platform.md`.

Then look for a design system already in place:
- Token or theme files, CSS custom properties, or a Tailwind theme
- A component library (shadcn/ui, HeroUI, MUI, Chakra, Tamagui, NativeWind)
- Colour sets in an asset catalog, or a `MaterialTheme`
- A design document (`DESIGN.md`, a style guide, or brand guidelines)

**An existing system wins.** Use its tokens and components, and apply the rules only where it says nothing. When the user asks for a redesign, propose updating the design document first, so later work does not follow the old rules.

## 3. Settle a Direction (New Products or Redesigns)

Choose one direction before the first screen. Mixing directions is the most common reason a UI looks unconsidered.

| Direction | Neutrals | Accent | Type | Imagery | Depth |
|---|---|---|---|---|---|
| **Restrained** | Near-white or near-black, barely tinted | One, on two or three elements per screen | One sans; large tabular numbers | None; the data is the hero | Layering and blur, few cards |
| **Product showcase** | Tinted toward the accent | One, plus a dark ink button | Heavy sans headline, one accented word | Real interface pieces, rotated and overlapping | Large radii, soft shadows |
| **Character-led** | Warm paper | Two to four soft tints, each with a meaning | Friendly or rounded sans, handwritten notes | One mascot with a pose per state | Flat, almost no shadow |
| **Editorial** | Paper or cream | One or two, muted | Display serif, italic for emphasis | Sparse line drawings or photography | Almost none; type carries it |

Pick from what the product does and who uses it: a finance or data tool leans Restrained, a consumer app competing for attention leans Product showcase, a habit or wellbeing app leans Character-led, and a content- or craft-led brand leans Editorial. Then draw the direction from the product's own subject matter (its content, its domain, what it produces) so it does not look like every other app in that direction.

Write the direction down as tokens in the project's own format (`references/` shows how per platform):
- 4–6 colours: a tinted neutral scale, ink, one accent, and status colours
- 2–3 type roles: display, body, and numeric or mono if needed
- Radius, spacing, and shadow scales
- One imagery mode

Compare options on the real product (`rules/real-screenshots.md`), not on invented mockups.

**Showcase screens and daily screens differ in volume.** Onboarding, empty states, paywalls, and store assets carry the full direction: oversized headlines, rotated tiles, doodles. Home, lists, and settings use the same tokens more quietly.

## 4. Rules

Each rule file has a **When building** constraint and a **When auditing** check. Read a rule when the screen involves what its "Applies to" column names.

| Rule | Impact | Applies to | File |
|---|---|---|---|
| Hierarchy | HIGH | every screen | `rules/hierarchy.md` |
| Colour | HIGH | palettes, themes, dark mode, any colour choice | `rules/color.md` |
| Typography | HIGH | headlines, body text, numbers, font choice | `rules/typography.md` |
| Spacing & layout | HIGH | layout, alignment, multi-screen flows | `rules/spacing-layout.md` |
| Real screenshots | HIGH | comparing palettes, type, or token changes | `rules/real-screenshots.md` |
| Surfaces | MEDIUM | cards, sheets, tab bars, modals, shadows, radii | `rules/surfaces.md` |
| Actions | MEDIUM | buttons, CTAs, selection states | `rules/actions.md` |
| Imagery | MEDIUM | heroes, onboarding, empty states, widgets, store assets | `rules/imagery.md` |
| Reference designs | MEDIUM | work from shared inspiration, Dribbble or Mobbin shots | `rules/reference-designs.md` |
| Generic defaults | MEDIUM | first impressions, "looks like a template" | `rules/generic-defaults.md` |
| Iconography | LOW | icons, tab bars, toolbars | `rules/iconography.md` |
| Decoration | LOW | doodles, annotations, emoji, stickers | `rules/decoration.md` |

## 5. Build

- **New product or redesign**: settle the direction (Step 3), then build each screen with the rules as constraints.
- **Existing UI**: match what is there. Use the existing tokens and components, apply the rules to the part being changed, and leave screens nobody asked about alone.

## 6. Audit

1. **Scope**: the files, screens, or images named; otherwise every user-facing screen. Screenshots and mockups are valid input: open them with Read.
2. **Identify the direction**: name the one the product is aiming for, or the ones it is mixing. Judge every screen against that direction, not against personal taste.
3. **Check**: compare each screen with the rules whose "Applies to" matches it, plus the platform guide.
4. **Report** grouped by impact, HIGH first. Cite a file and line, or the image and the area of the screen:

```
### HIGH — Colour
- src/screens/Welcome.tsx:24 — blue button, pink badge and green chip compete
  → keep blue as the accent; move the badge and chip to tinted neutrals
```

End with the counts per impact. Change nothing in audit mode unless asked; when asked, fix in impact order.

## Boundaries

- **UX behaviour** (what a screen needs, flow order, persuasion, permission timing) belongs to `ux-psychology`. This skill decides how a primary action looks; that one decides whether it should exist.
- **Contrast ratios, text scaling, and colour-only signals** belong to the `accessibility` skill when it is installed; apply it alongside this one. This skill never trades legibility for style.
- **Motion** (easing, springs, durations) belongs to an animation skill when one is installed.
- **Copy and proofreading** are out of scope, apart from casing and length where they affect layout.
