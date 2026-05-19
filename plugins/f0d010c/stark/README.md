# stark

[![Release](https://img.shields.io/github/v/release/f0d010c/stark?style=for-the-badge&label=release&labelColor=111111&color=ff6b4a)](https://github.com/f0d010c/stark/releases)
[![License](https://img.shields.io/badge/license-Apache--2.0-8b5cf6?style=for-the-badge&labelColor=111111)](LICENSE)
[![Platforms](https://img.shields.io/badge/platforms-Web%20%7C%20Windows%20%7C%20Apple%20%7C%20Android-14b8a6?style=for-the-badge&labelColor=111111)](README.md)
[![Made for Agents](https://img.shields.io/badge/made%20for-AI%20coding%20agents-0ea5e9?style=for-the-badge&labelColor=111111)](README.md)

UI/UX design plugin for AI coding agents.
It routes UI and UX requests to focused skills, asks the right product-flow / platform / track / direction questions first, then helps agents ship usable interfaces instead of template clones.

Stark keeps compatibility notes for multiple agent environments, while Codex installs use the Codex manifest and shared skill folders.

## Why this exists

AI design output often defaults to the same web-shaped answer: React, Tailwind, shadcn, Inter, purple gradients, centered hero, three cards, CTA strip.
That is wrong for native apps, and it is boring on the web.

`stark` pushes Codex toward the right product and design idiom before code:

- UX maps product flows, states, IA, forms, onboarding, dashboards, and repeated-use ergonomics before pixels.
- UX produces a compact decision brief that platform skills must preserve during implementation.
- Contextual UX briefs cover agent runs, operational dashboards, activation onboarding, checkout/upgrade, and editor/canvas tools.
- UI produces a visual decision brief for surface type, hierarchy, density, component grammar, motion budget, and state visuals.
- Product quality checks force specific jobs, proof surfaces, complete states, scan speed, and one memorable anchor before code.
- Creative direction turns "make it creative" into a concrete world, metaphor, material language, repeated motif, forbidden defaults, and one tasteful risk.
- Interaction guidance chooses CSS, Motion, GSAP, native scroll CSS, Lenis, command palettes, split panes, timelines, or no motion by surface and product job.
- Web implementation tracks choose static HTML/CSS/JS, Vite + React, Next, Astro, or the existing stack by interaction needs and dependency risk.
- Cinematic landing guidance separates key art from page design, then defines typography, art direction, section rhythm, and motion choreography before code.
- Asset planning chooses icons, screenshots, references, typography, generated UI mocks, and optional GPT/Codex image generation before implementation.
- Reference analysis extracts structure from shipped products, Mobbin/Figma screens, docs, and screenshots without copying visual identity.
- Web asks for an aesthetic direction first.
- Windows asks whether the app should be system-like WinUI, branded WinUI, Tauri, or Electron.
- Apple asks whether the app should be strict SwiftUI, branded SwiftUI, React Native, Flutter, or desktop web shell.
- Android asks whether the app should be Compose, branded Compose, React Native, Flutter, or Compose Multiplatform.
- Cross-platform work gets explicit fidelity warnings.
- Token work uses W3C DTCG design tokens and export scripts.

## Install In Codex

Use this repository as a Codex plugin source.
In this source repo, the Codex manifest lives at:

```text
.codex-plugin/plugin.json
```

For local testing, point Codex at this folder or install it through the Codex plugin flow once it is pushed to a GitHub repository.
After installation, restart or reload Codex so the skills are indexed.
Marketplace mirrors may place the same manifest under their bundled plugin folder, such as `plugins/f0d010c/stark/.codex-plugin/plugin.json`.

## Use

Use natural language.
Codex should trigger the matching skill automatically:

```text
Design a landing page for a type foundry that does not look like generic SaaS.
Make a Win11 app shell with NavigationView and Mica.
Build an iOS 26 settings screen with Liquid Glass.
Create a Compose Material 3 Expressive workout screen.
Improve the onboarding UX for this app so users reach first value faster.
Design the empty, loading, error, and success states for this dashboard.
Translate this iOS settings screen into a Windows app.
Audit this React hero section for UX problems and AI design slop.
Export these DTCG tokens to Tailwind and SwiftUI.
```

If the target is ambiguous, `design-router` asks which platform to use instead of defaulting to web.

## Slash Command Mapping

The Claude version included slash commands.
Codex uses skills and natural-language routing instead.

| Claude command | Codex equivalent |
|---|---|
| `/stark ux <brief>` | `Use stark ux-design for <brief>` or ask for UX / product flow help |
| `/stark web <brief>` | `Use stark web-design for <brief>` or simply ask for a web UI |
| `/stark windows <brief>` | Ask for a Windows / WinUI / Fluent UI |
| `/stark apple <brief>` | Ask for an iOS / macOS / SwiftUI UI |
| `/stark android <brief>` | Ask for Android UI; Stark should ask which Android track to use |
| `/stark auto <brief>` | Ask normally; `design-router` decides or asks one question |
| `/stark-audit <file>` | `Audit <file> with stark for UX problems and AI design slop` |
| `/stark-assets <brief>` | `Use stark assets to plan the visual assets before building` |
| `/stark-reference <brief>` | `Use stark reference analysis before designing from shipped examples` |
| `/stark-translate apple windows <file>` | `Translate this Apple UI to Windows using stark` |

## What's Inside

```text
stark/
  .codex-plugin/plugin.json      Codex plugin manifest
  skills/
    design-router/               UX and platform dispatcher
    ux-design/                   flows, states, IA, forms, onboarding, dashboards
  references/ui-patterns/         surface taxonomy, creative direction, implementation tracks, visual hierarchy, responsive containment, asset selection, reference analysis, motion budget, interaction techniques, cinematic landing system, UI audit rubric, product quality bar
  references/ux-patterns/         contextual product-flow briefs
    web-design/                  6 web aesthetic directions
    windows-design/              WinUI / branded WinUI / Tauri / Electron
    apple-design/                SwiftUI / RN / Flutter / desktop shells
    android-design/              Compose / RN / Flutter / CMP
    cross-platform-design/       idiom translation and fidelity warnings
    design-tokens/               DTCG token generation and export
  references/                    design philosophy, platform docs, web patterns
  assets/                        token bundles, font pairs, screenshot gallery
  scripts/                       platform detection and token export helpers
  commands/                      legacy Claude slash-command docs
```

## Web Directions

`web-design` asks for one direction before generating code:

1. Editorial Swiss revival
2. Tactile brutalism
3. Type-as-hero
4. Glow + grain
5. Industrial monospace
6. Active bento

Each direction has its own typography, palette, layout grammar, motion language, copy voice, reference apps, and ban list.

## Product Quality Bar

For "make this better" work, Stark now pushes agents to answer five practical questions before code:

- What specific job does this surface serve?
- What proof does the UI show instead of only claiming value?
- Which empty/loading/error/permission/success states exist?
- How fast can a returning user scan status, owner, risk, and next action?
- What is the one memorable visual anchor?

That keeps generated output closer to a real product and farther from generic demo furniture.

## Interaction Decisions

Stark includes product-facing motion and interaction guidance:

- CSS transitions for simple hover/focus/disclosure feedback.
- Motion for React when component state, layout continuity, sheets, modals, or route/detail transitions matter.
- GSAP ScrollTrigger only for complex timeline or pinned storytelling.
- Native scroll-driven CSS for lightweight progress and reveal effects.
- Lenis only when scroll feel is part of a brand/editorial surface.
- No animation when stability, reading, copying, comparing, or recovery matters more.

The interaction brief also makes agents state the motion budget, reduced-motion behavior, and rejected techniques.

Stark explicitly knows about Motion/motion.dev. It should choose Motion for React component state, layout continuity, sheets, modals, command palettes, and route/detail transitions. It should choose GSAP only for complex timeline or pinned-scroll storytelling, and CSS/native APIs for simpler interactions.

## Cinematic Landing Pages

For launch pages, editorial scroll stories, immersive brand pages, and campaign-style websites, Stark treats the hero image as only one part of the system.

The agent should define:

- key art: one dominant object, scene, product proof, or specimen that carries the first viewport
- page system: typography, palette, layout rhythm, recurring motif, and section sequence
- choreography: reveal order, pinned moments, parallax depth, gallery transitions, and reduced-motion behavior
- restraint: fewer sections, fewer type choices, no unrelated card grids, and no motion added to hide weak composition

This is the difference between a good-looking hero screenshot and a page that stays coherent after the first scroll.

## Creative Direction

For high-craft work, Stark asks agents to define a world before code:

- visual metaphor
- material language
- typography personality
- layout grammar
- motion voice
- repeated motif
- forbidden defaults
- one tasteful risk
- restraints that keep the risk coherent

This pushes agents away from random decoration and toward a specific art direction that can survive across the full page or app.

## Web Implementation Tracks

React is supported as a first-class path, especially for stateful, componentized, animated, or app-like web surfaces.

Stark still asks whether React is actually needed:

- static HTML/CSS/JS for simple pages and lightweight effects
- Vite + React for advanced interactive sites, product demos, dashboards, command palettes, inspectors, and reusable components
- Next for app/marketing hybrids, SEO, routing, server data, and auth
- Astro for content-heavy or editorial sites with islands of interactivity

The stack brief includes dependency risk notes so agents do not add npm packages just for decoration, especially during active supply-chain incidents.

## Screenshot Gallery

The repo keeps proof as screenshots instead of full generated app folders, so the plugin stays small and installable.

| Project | Desktop | Mobile |
|---|---|---|
| Operator Console | <img src="assets/screenshots/operator-console/desktop.png" alt="Operator Console desktop screenshot" width="360"> | <img src="assets/screenshots/operator-console/mobile.png" alt="Operator Console mobile screenshot" width="180"> |
| BuildDesk | <img src="assets/screenshots/builddesk/desktop.png" alt="BuildDesk desktop screenshot" width="360"> | <img src="assets/screenshots/builddesk/mobile.png" alt="BuildDesk mobile screenshot" width="180"> |
| Artifact Labs | <img src="assets/screenshots/artifact-labs-site/desktop.png" alt="Artifact Labs desktop screenshot" width="360"> | <img src="assets/screenshots/artifact-labs-site/mobile.png" alt="Artifact Labs mobile screenshot" width="180"> |
| Ops Dashboard | <img src="assets/screenshots/ops-dashboard/desktop.png" alt="Ops Dashboard desktop screenshot" width="360"> | <img src="assets/screenshots/ops-dashboard/mobile.png" alt="Ops Dashboard mobile screenshot" width="180"> |
| CRM v2 | <img src="assets/screenshots/crm-v2/desktop.png" alt="CRM v2 desktop screenshot" width="360"> | <img src="assets/screenshots/crm-v2/mobile.png" alt="CRM v2 mobile screenshot" width="180"> |

Screenshot folders live under `assets/screenshots/<project>/`.

## Native Tracks

`stark` does not silently turn every app into a website.

- Windows: system-like WinUI 3, branded WinUI 3, Tauri 2, Electron
- Apple: strict SwiftUI, branded SwiftUI, React Native, Flutter, Tauri / Electron for macOS
- Android: Compose strict, branded Compose, React Native, Flutter, Compose Multiplatform
- Cross-platform: Tauri, React Native, Flutter, Compose Multiplatform, Uno, Avalonia, MAUI with explicit tradeoffs

## Helper Scripts

```bash
python scripts/detect_platform.py --text "Build a Settings screen for Win11 with Mica"
python scripts/token_export.py --input assets/tokens/fluent-2.json --target winui --output Resources.xaml
```

## Review Contract

Stark keeps a small tested helper-script surface. Runtime bundle scope, local-only files, token-export guarantees, and change policy are documented in `docs/review-contract.md`.

## Test

Run SkillForge against the plugin:

```bash
npx agent-skillforge lint . --format text
npx agent-skillforge smoke .
python -m unittest discover -s tests
```

These commands use `npx`; no repo-local package install is required.

Manual smoke prompts:

```text
Design a developer-tool landing page in the industrial monospace direction.
Improve the trial onboarding UX for a B2B analytics dashboard.
Audit src/components/Hero.tsx for UX and web anti-slop issues.
Translate this Apple settings screen to Windows using stark.
```

## Compatibility

This repo is intentionally multi-agent shaped:

- Codex reads `.codex-plugin/plugin.json` and `skills/*/SKILL.md`.
- Other agent environments can reuse the same skill text and command notes from source.

The skill content is shared so fixes improve both surfaces.

## License

Apache 2.0. See `LICENSE` and `NOTICE`.
