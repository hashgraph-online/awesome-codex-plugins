<p align="center">
  <img src="assets/logo/stark-mark.svg" alt="stark logo" width="96" height="96">
</p>

# stark

[![Release](https://img.shields.io/github/v/release/f0d010c/stark?style=for-the-badge&label=release&labelColor=111111&color=ff6b4a)](https://github.com/f0d010c/stark/releases)
[![License](https://img.shields.io/badge/license-Apache--2.0-8b5cf6?style=for-the-badge&labelColor=111111)](LICENSE)
[![Platforms](https://img.shields.io/badge/platforms-Web%20%7C%20Windows%20%7C%20Apple%20%7C%20Android-14b8a6?style=for-the-badge&labelColor=111111)](README.md)
[![Made for Agents](https://img.shields.io/badge/made%20for-AI%20coding%20agents-0ea5e9?style=for-the-badge&labelColor=111111)](README.md)

UI/UX design plugin for AI coding agents.

Stark helps agents choose the right product flow, platform idiom, visual direction, motion, assets, and design-token strategy before writing code. The goal is simple: fewer generic template clones, more usable product-specific interfaces.

## What It Does

- Plans UX flows, IA, onboarding, checkout, forms, dashboards, states, recovery paths, and repeated-use ergonomics.
- Routes UI work across web, Windows, Apple, Android, and cross-platform stacks.
- Forces non-generic decisions: desktop archetypes, concept seeds, layout sketches, design recipes, and anti-default rewrites.
- Chooses frontend tracks and motion tools by job: static HTML, Vite React, Next, Astro, CSS, Motion, GSAP, native scroll CSS, Lenis, or no motion.
- Plans assets and references without copying shipped products.
- Generates, audits, and exports W3C DTCG tokens to Tailwind, CSS, Compose, SwiftUI, and WinUI.

## Install In Codex

Use this repository as a Codex plugin source. The Codex manifest lives at:

```text
.codex-plugin/plugin.json
```

After installation, restart or reload Codex so the skills are indexed.

## Use

Ask naturally:

```text
Design a landing page for a type foundry that does not look like generic SaaS.
Make a Win11 app shell with NavigationView and Mica.
Build an iOS 26 settings screen with Liquid Glass.
Create a Compose Material 3 Expressive workout screen.
Improve the onboarding UX so users reach first value faster.
Design the empty, loading, error, and success states for this dashboard.
Translate this iOS settings screen into a Windows app.
Audit this React hero section for UX problems and AI design slop.
Export these DTCG tokens to Tailwind and SwiftUI.
```

If the platform is ambiguous, Stark asks which target to use instead of silently defaulting to web.

## Screenshot Gallery

The repo keeps proof as screenshots instead of full generated app folders, so the plugin stays small and installable.

| Project | Desktop | Mobile |
|---|---|---|
| Operator Console | <img src="assets/screenshots/operator-console/desktop.png" alt="Operator Console desktop screenshot" width="360"> | <img src="assets/screenshots/operator-console/mobile.png" alt="Operator Console mobile screenshot" width="180"> |
| BuildDesk | <img src="assets/screenshots/builddesk/desktop.png" alt="BuildDesk desktop screenshot" width="360"> | <img src="assets/screenshots/builddesk/mobile.png" alt="BuildDesk mobile screenshot" width="180"> |
| Artifact Labs | <img src="assets/screenshots/artifact-labs-site/desktop.png" alt="Artifact Labs desktop screenshot" width="360"> | <img src="assets/screenshots/artifact-labs-site/mobile.png" alt="Artifact Labs mobile screenshot" width="180"> |

## Tracks

| Area | Stark covers |
|---|---|
| UX | flows, IA, state design, onboarding, checkout, dashboards, forms, recovery |
| Web | landing pages, apps, dashboards, docs, React/Vite/Next/Astro, motion, assets |
| Windows | WinUI 3, branded Fluent, Tauri, Electron, Mica/Acrylic, desktop archetypes |
| Apple | SwiftUI, Liquid Glass, HIG, iOS/iPadOS/macOS/watchOS/visionOS, desktop shells |
| Android | Compose, Material 3 Expressive, React Native, Flutter, Compose Multiplatform |
| Cross-platform | Tauri, Electron, React Native, Flutter, CMP, Uno, Avalonia, MAUI |
| Tokens | W3C DTCG, Tailwind, CSS variables, Compose, SwiftUI, WinUI |

## What's Inside

```text
stark/
  .codex-plugin/plugin.json      Codex plugin manifest
  skills/                        routing, UX, web, platform, cross-platform, tokens
  references/                    design, platform, UX, web, and UI-pattern guidance
  assets/logo/                   Stark logo SVGs
  assets/screenshots/            curated screenshot proof
  assets/tokens/                 DTCG token bundles
  scripts/                       platform detection and token export helpers
  docs/                          usage, review contract, roadmap, public-readiness notes
```

## Useful Docs

- [Codex usage](docs/codex-usage.md)
- [Review contract](docs/review-contract.md)
- [Next-level design roadmap](docs/next-level-design-roadmap.md)
- [Design quality measurement](docs/design-quality-measurement.md)
- [Reference governance](docs/reference-governance.md)
- [Public plugin readiness](docs/public-plugin-readiness.md)
- [Logo usage](assets/logo/README.md)

## Helper Scripts

```bash
python scripts/detect_platform.py --text "Build a Settings screen for Win11 with Mica"
python scripts/token_export.py --input assets/tokens/fluent-2.json --target winui --output Resources.xaml
```

## Test

```bash
npx agent-skillforge lint . --format text
npx agent-skillforge smoke .
python -m unittest discover -s tests
```

CI also runs marketplace lint, token export smoke checks, and public-readiness checks.

## Compatibility

- Codex reads `.codex-plugin/plugin.json` and `skills/*/SKILL.md`.
- Other SKILL.md-compatible agent environments can reuse the same skill text and references.

## License

Apache 2.0. See `LICENSE` and `NOTICE`.
