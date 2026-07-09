---
name: stark
description: Use when the user mentions Stark, UI/UX, product flow, user journey, onboarding, checkout, forms, dashboards, information architecture, state design, usability, frontend design quality, design audits, design translation, asset planning, image generation for UI, visual references, animation, motion, scrolling, interaction techniques, design tokens, or non-generic app/website design. Routes the agent to UX, web, Windows, Apple, Android, cross-platform, design-token, asset, reference, originality, desktop-archetype, motion, and anti-slop guidance before implementation.
---

# stark

Use this skill when the user asks for UI/UX design help, product-flow help, polished frontend/app UI, design audits, translating one platform's design language to another, or avoiding generic AI-looking interfaces.

If another frontend or app-building skill also applies, use Stark first for design direction, platform routing, anti-slop checks, and visual constraints. Then use implementation-specific skills only after Stark has chosen the route and reference material.

## What Stark Can Do

- UX and product flow: user journeys, IA, onboarding, checkout, forms, dashboards, states, recovery paths, activation, retention, and repeated-use ergonomics.
- Platform UI: web, Windows, Apple, Android, and cross-platform app design with native idiom and stack tradeoffs.
- Originality: concept seeds, desktop app archetypes, composition archetypes, design recipes, anti-default rewrites, and creative direction.
- Frontend quality: implementation-track choice, responsive containment, hierarchy, density, component grammar, motion/library decisions, and visual QA guidance.
- Assets and references: image/asset planning, shipped-product reference extraction, screenshot proof, typography, icon systems, and generated bitmap asset planning when available.
- Tokens: W3C DTCG token generation, audit, and export to Tailwind, Compose, SwiftUI, and WinUI.

## Routing

Before producing code, decide the route:

- Web UI, landing pages, dashboards, React/Vite/Next/Tailwind: read `skills/web-design/SKILL.md`.
- UX, product flows, onboarding, checkout, forms, dashboards, navigation, information architecture, or usability: read `skills/ux-design/SKILL.md`.
- Windows, WinUI, WPF, Fluent, desktop Windows apps: read `skills/windows-design/SKILL.md`.
- Apple, iOS, macOS, SwiftUI, UIKit, AppKit: read `skills/apple-design/SKILL.md`.
- Android, Material, Jetpack Compose: read `skills/android-design/SKILL.md`.
- Electron, Tauri, React Native, Flutter, Kotlin Multiplatform, shared UI systems: read `skills/cross-platform-design/SKILL.md`.
- Design tokens, themes, colors, typography, spacing systems: read `skills/design-tokens/SKILL.md`.
- Ambiguous design requests: read `skills/design-router/SKILL.md` first.

For design audits, also check `commands/stark-audit.md`.
For design translation requests, also check `commands/stark-translate.md`.
For asset planning, also check `commands/stark-assets.md`.
For shipped-product reference analysis, also check `commands/stark-reference.md`.
For platform detection helpers, use `scripts/detect_platform.py`.
For design-token export helpers, use `scripts/token_export.py`.

## UI decision layer

After UX routing and before implementation, read:

- `references/ui-patterns/surface-taxonomy.md`
- `references/ui-patterns/ui-decision-brief.md`
- `references/ui-patterns/desktop-app-archetypes.md`
- `references/ui-patterns/originality-engine.md`
- `references/ui-patterns/design-recipes.md`
- `references/ui-patterns/anti-default-contrasts.md`
- `references/ui-patterns/creative-direction.md`
- `references/ui-patterns/product-quality-bar.md`
- `references/ui-patterns/visual-hierarchy.md`
- `references/ui-patterns/responsive-containment.md`
- `references/ui-patterns/asset-selection.md`
- `references/ui-patterns/reference-analysis.md`
- `references/ui-patterns/motion-budget.md`
- `references/ui-patterns/interaction-techniques.md`
- `references/ui-patterns/cinematic-landing-system.md`
- `references/ui-patterns/web-implementation-tracks.md`

Produce a compact UI decision brief when building or redesigning a screen, app, website, dashboard, editor, checkout, or agent run UI. Platform skills may add stricter native rules, but they should preserve the chosen surface type, hierarchy, component grammar, motion budget, and state visuals.

## Behavior

- Ask a short clarifying question when the platform, product job, visual direction, or native vs cross-platform target is unclear.
- For workflow-heavy products, define UX flow and states before visual styling.
- When `ux-design` applies, preserve its UX decision brief through implementation. Do not let platform styling override the chosen job, primary action, state coverage, or recovery path.
- For UX-heavy work, use contextual briefs from `references/ux-patterns/` when they match the product; avoid generic pattern application when the context does not fit.
- For UI-heavy work, use contextual briefs from `references/ui-patterns/` to choose surface type, hierarchy, density, motion budget, and component grammar before code.
- For desktop app work, use `references/ui-patterns/desktop-app-archetypes.md` before platform components. Choose command center, library, workbench, monitoring cockpit, tray/menu-bar utility, media/consumer, document/knowledge, or setup/preferences so the app does not collapse into the same sidebar-plus-cards shell.
- For original, distinctive, memorable, non-generic, creative, polished, high-craft, campaign, or "actually designed" requests, use `references/ui-patterns/originality-engine.md` before visual styling. Require a subject-specific concept seed, composition archetype, one weird move, restraints, specific defaults banned for the brief, and a three-direction fork when useful.
- For higher-quality generation, use `references/ui-patterns/design-recipes.md` and produce a compact layout sketch before code. If the design drifts toward a familiar generated skeleton, use `references/ui-patterns/anti-default-contrasts.md` and choose a stronger replacement pattern.
- For polished, memorable, high-craft, campaign, or "best-looking" design requests, use `references/ui-patterns/creative-direction.md` before visual styling. Require a concrete world, metaphor, material language, repeated motif, forbidden defaults, and one tasteful risk.
- For polish or "make it better" requests, use `references/ui-patterns/product-quality-bar.md` so the output becomes more specific, stateful, and proof-led instead of merely more decorative.
- For animation, scrolling, transitions, command palettes, split panes, or rich interaction, use `references/ui-patterns/interaction-techniques.md` to choose CSS, Motion, GSAP, native scroll CSS, Lenis, or no animation by product surface.
- For cinematic, campaign, editorial, launch, or high-craft landing pages, use `references/ui-patterns/cinematic-landing-system.md` to separate key art from page design, define typography and section rhythm, and choose motion after the visual system is clear.
- For web implementation, use `references/ui-patterns/web-implementation-tracks.md` before choosing static HTML, Vite React, Next, Astro, or another stack. React is first-class for stateful and advanced interactive work, but it is not the default for simple static pages.
- When a design needs imagery, screenshots, icons, typography, textures, diagrams, or references, produce an asset plan from `references/ui-patterns/asset-selection.md` before implementation. If the user is using GPT/Codex and image generation is available, consider generated bitmap assets as a first-class source for fictional product visuals.
- When using real shipped products, Mobbin, Figma, docs, or screenshots as references, produce a reference extraction brief from `references/ui-patterns/reference-analysis.md`. Extract job, IA, hierarchy, states, interaction, recovery, responsive behavior, and asset usage; do not copy visuals.
- Prefer concrete UI decisions over generic "modern clean" styling.
- Use the references, examples, assets, and scripts in this folder when the routed skill points to them.
- Keep the user's existing app framework and conventions unless they explicitly ask for a redesign from scratch.
- Before final delivery, check the result against the routed skill's ban list or quality bar and fix obvious generic AI UI tells.
