<p align="center">
  <img src="assets/logo/stark-mark.svg" alt="Stark logo" width="96" height="96">
</p>

# Stark

[![CI](https://github.com/f0d010c/stark/actions/workflows/ci.yml/badge.svg)](https://github.com/f0d010c/stark/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/f0d010c/stark)](https://github.com/f0d010c/stark/releases)
[![License](https://img.shields.io/badge/license-Apache--2.0-8b5cf6)](LICENSE)

Design direction for AI coding agents—grounded in product behavior, platform idiom, and rendered evidence.

Stark routes UI work across web, Windows, Apple, Android, cross-platform, UX, and design tokens. It makes the agent choose the product object, user flow, visual language, states, responsive behavior, motion ownership, and proof strategy before generating code.

## Why Stark

Most weak generated interfaces fail before the first CSS rule: they choose a generic structure, decorate it, and call the result polished. Stark changes that sequence.

1. Route the request to the correct platform and surface.
2. Load a small, relevant reference bundle.
3. Write a compact decision brief.
4. Build in the repository's existing stack.
5. Inspect rendered evidence.
6. Repair the highest-impact failure and re-check it.

The runtime uses two core references and at most two conditional references per task. The full library remains available as a catalog without flooding the agent's context.

## Install

### Codex

Install this repository as a plugin, then invoke Stark naturally:

```text
Use Stark to redesign this dashboard around incident triage.
```

The Codex manifest is at `.codex-plugin/plugin.json`.

### Claude Code

Add the repository as a plugin marketplace source:

```text
/plugin marketplace add f0d010c/stark
/plugin install stark@stark
```

The compatibility manifest is at `.claude-plugin/plugin.json`.

## Examples

```text
Use Stark to design a React analytics dashboard for returning operators.
Prioritize scan speed, realistic states, keyboard use, and mobile replacement.
```

```text
Use Stark to redesign this SwiftUI onboarding flow.
Preserve native conventions and prove recovery from denied permissions.
```

```text
Use Stark to audit this landing page for generic structure, weak proof,
typography, accessibility, responsive behavior, and unnecessary libraries.
```

## Capabilities

| Area | What Stark decides |
|---|---|
| UX | Flows, information architecture, first value, states, recovery, repeated-use ergonomics |
| Web | Surface type, stack, composition, typography, copy, assets, responsive behavior, motion |
| Native | Windows, Apple, and Android idioms, controls, navigation, density, materials, accessibility |
| Cross-platform | Shared versus platform-owned behavior for Electron, Tauri, React Native, Flutter, and CMP |
| Design systems | Tokens, component APIs, variants, state galleries, themes, density, drift checks |
| Audit and QA | Usability, accessibility, visual quality, runtime behavior, repair priority, re-check evidence |
| Motion | Choreography, ownership, fallbacks, reduced motion, performance budgets, acceptance frames |

## Included tools

- Platform detector: `python scripts/detect_platform.py --text "Build a WinUI settings app"`
- Token exporter: `python scripts/token_export.py --input assets/tokens/fluent-2.json --target winui --output Resources.xaml`
- Deterministic plugin archive: `npm run pack:plugin`
- Repository checks: `npm run check`

Token export targets are `css`, `tailwind`, `swiftui`, `compose`, and `winui`.

## Repository map

```text
SKILL.md                 Main router and context budget
skills/                  Platform and task-specific skills
references/              Narrow decision and implementation references
commands/                Explicit Stark modes
assets/                  Tokens, fonts, logo, and curated proof
scripts/                 Detector, token exporter, packaging, validation
evals/                   Trigger and design-quality evaluation cases
tests/                   Behavioral and repository-health tests
```

## Development

Requires Python 3.12+ and Node.js 20+.

```bash
npm ci
npm run check
npm run pack:plugin
```

`npm run check` runs unit tests, strict marketplace lint, smoke prompts, local-link checks, context-budget checks, secret hygiene, line-ending checks, and archive validation.

See [CONTRIBUTING.md](CONTRIBUTING.md), [reference governance](docs/reference-governance.md), and the [review contract](docs/review-contract.md).

## Scope

Stark is a prompt-and-reference plugin, not a component library. It works with the user's existing frontend or native stack and does not require a runtime dependency in generated applications.

The project can be distributed through npm in the future, but the current package is intentionally marked private while an install/doctor CLI and npm-specific user value are designed. The plugin archive remains the canonical artifact.

## License

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
