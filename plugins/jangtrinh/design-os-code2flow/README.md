# DESIGN:OS Code2Flow (`design-os-code2flow`)

**Local-first AST codebase-to-user-flow mapper and 11-heuristic UX gap auditor across 7 frontend and mobile frameworks.**

Statically analyze Next.js, React Router, TanStack Router, Expo Router, SwiftUI, Flutter, and Jetpack Compose repositories to generate Mermaid user-flow graphs and catch dead-end screens, missing error boundaries, and unguarded auth routes.

**design-os-code2flow is free** to use and modify. Source-available under PolyForm Shield 1.0.0. It runs locally and works with Claude Code, Codex, Gemini CLI and Antigravity.

<p align="center">
  <img src="docs/images/cover.png" alt="DESIGN:OS Code2Flow — 2:1 Axonometric Technical Architecture" width="840">
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-PolyForm_Shield_1.0.0-202020?style=flat-square&labelColor=202020&color=444444" alt="PolyForm Shield 1.0.0 License"></a>
  <img src="https://img.shields.io/badge/Claude_Code_%C2%B7_Codex_%C2%B7_Gemini_%C2%B7_Antigravity-skill-202020?style=flat-square&labelColor=202020&color=444444" alt="Compatible agents">
  <a href="commands/doctor.md"><img src="https://img.shields.io/badge/diagnostics-%2Fdoctor-202020?style=flat-square&labelColor=202020&color=444444" alt="Doctor command"></a>
  <a href="https://jangtrinh.github.io/design-os-code2flow/"><img src="https://img.shields.io/badge/live_docs-GitHub_Pages-202020?style=flat-square&labelColor=202020&color=444444" alt="Live GitHub Pages"></a>
  <a href="https://buymeacoffee.com/jangtrinh"><img src="https://img.shields.io/badge/Buy_Me_a_Coffee-FFDD00?style=flat-square&logo=buy-me-a-coffee&logoColor=black" alt="Buy Me a Coffee"></a>
</p>

<p align="center">
  <a href="#quickstart">Quickstart</a> · <a href="#what-it-makes">What it makes</a> · <a href="#installation">Install</a> · <a href="#how-it-works">How it works</a> · <a href="#commands--diagnostics">Commands</a> · <a href="#quality-bar--limitations">Limits</a>
</p>

---

## Why this exists

Product teams rarely keep user-flow diagrams in sync with production code, and AI agents frequently ship screens with missing loading states, dead-end routes, or unauthenticated pages. **`design-os-code2flow`** parses your actual source files locally to extract the real route graph and audit it against 11 structural UX heuristics.

| Dimension | Generic AI / Manual Workflow | DESIGN:OS Code2Flow (`DESIGN:OS`) |
| :--- | :--- | :--- |
| **Source of Truth** | Outdated Figma flowcharts that drifted from code months ago | Directly extracted from live route files, AST navigation calls, and layouts |
| **Framework Coverage** | Single-framework scripts that break on mobile or monorepos | Unified analyzer for Next.js, React Router, TanStack, Expo, SwiftUI, Flutter & Compose |
| **UX Defect Detection** | Manual QA clicking through every screen after deployment | Automated 11-heuristic static audit (dead ends, missing error/loading states, auth leaks) |
| **Privacy & Speed** | Uploading proprietary source code to third-party SaaS scanners | 100% local execution in milliseconds with zero network calls |
| **Privacy & Telemetry** | Opaque cloud telemetry or unverified third-party APIs | **Zero telemetry** — 100% local execution ([`PRIVACY.md`](PRIVACY.md) audited) |

---

## Quickstart

### 1. Install the plugin or CLI

**In Claude Code:**

```text
/plugin marketplace add jangtrinh/design-os-code2flow
/plugin install design-os-code2flow@design-os-code2flow
```

**Or from your terminal (Codex, Gemini CLI, Antigravity, OpenCode, or standalone CLI):**

```bash
git clone https://github.com/jangtrinh/design-os-code2flow.git
cd design-os-code2flow
npm test
```

### 2. Ask in plain English

Open your project in your AI coding agent and describe what you need:

> "Scan this Next.js App Router repository with code2flow, generate the Mermaid user-flow diagram, and list all high-severity UX gaps."

> "Audit our SwiftUI navigation stack for dead-end screens, missing loading/error states, and unguarded destructive actions."

> "Export a JSON + Markdown user-flow topology report for our PR review gate."

### 3. Verify your setup

```bash
python3 scripts/self_check.py
```

---

## What it makes

Every deliverable produced by `design-os-code2flow` is backed by a deterministic verification gate rather than freehand AI guesswork.

<p align="center">
  <img src="docs/images/cover.png" alt="DESIGN:OS Code2Flow Output Specimen" width="840"><br>
  <sub>Prompt: <code>"Scan this Next.js App Router repository with code2flow, generate the Mermaid user-flow diagram, and list all high-severity UX gaps."</code></sub>
</p>

| Deliverable / Mode | Best for | Output Format | Verification Gate |
| :--- | :--- | :--- | :--- |
| **Mermaid User-Flow Graph** | Visualizing every route, modal, redirect, and navigation edge in the codebase | `Mermaid (.mmd / Markdown)` | `100% route discovery parity` |
| **11-Heuristic UX Audit Report** | Flagging dead ends, orphan screens, missing error boundaries, and auth gaps | `Markdown + JSON Diagnostics` | `Exit code gate for CI/CD` |
| **Programmatic AST SDK** | Embedding route-graph extraction and UX auditing inside custom agent workflows | `TypeScript / ESM SDK` | `npm test suite PASS` |

---

## Installation

Choose the setup that matches your AI coding agent. Every option installs the same canonical skill (`skills/design-os-code2flow/SKILL.md`) and `/doctor` diagnostic suite.

### Claude Code

Run these two commands inside Claude Code:

```text
/plugin marketplace add jangtrinh/design-os-code2flow
/plugin install design-os-code2flow@design-os-code2flow
```

### OpenAI Codex

Install to your personal Codex skills directory:

```bash
git clone https://github.com/jangtrinh/design-os-code2flow.git /tmp/design-os-code2flow
mkdir -p ~/.codex/skills/design-os-code2flow ~/.codex/prompts
cp -R /tmp/design-os-code2flow/skills/design-os-code2flow/* ~/.codex/skills/design-os-code2flow/
cp /tmp/design-os-code2flow/prompts/doctor.md ~/.codex/prompts/design-os-code2flow-doctor.md
rm -rf /tmp/design-os-code2flow
```

### Gemini CLI & Google Antigravity

```bash
git clone https://github.com/jangtrinh/design-os-code2flow.git /tmp/design-os-code2flow
mkdir -p ~/.gemini/skills/design-os-code2flow
cp -R /tmp/design-os-code2flow/skills/design-os-code2flow/* ~/.gemini/skills/design-os-code2flow/
rm -rf /tmp/design-os-code2flow
```

### OpenCode, Cursor, Windsurf & Other Agent Harnesses

```bash
git clone https://github.com/jangtrinh/design-os-code2flow.git /tmp/design-os-code2flow
mkdir -p ~/.agents/skills/design-os-code2flow
cp -R /tmp/design-os-code2flow/skills/design-os-code2flow/* ~/.agents/skills/design-os-code2flow/
rm -rf /tmp/design-os-code2flow
```

<details>
<summary>Verify or uninstall</summary>

**Verify installation:**

```bash
python3 scripts/self_check.py
```

Or run `/doctor` inside Claude Code / Codex to inspect installed skill paths, plugin manifests, and gate health.

**Uninstall:**

```bash
rm -rf ~/.claude/skills/design-os-code2flow ~/.codex/skills/design-os-code2flow ~/.gemini/skills/design-os-code2flow ~/.agents/skills/design-os-code2flow
```

</details>

---

## Usage & Prompt Cookbook

Once installed, `skills/design-os-code2flow/SKILL.md` activates automatically when your prompt matches its domain triggers. Browse [`docs/cookbook.md`](docs/cookbook.md) for copy-paste prompt recipes.

**Generate & Scaffold**

```text
"Scan this Next.js App Router repository with code2flow, generate the Mermaid user-flow diagram, and list all high-severity UX gaps."
```

**Audit & Verify**

```text
"Audit our SwiftUI navigation stack for dead-end screens, missing loading/error states, and unguarded destructive actions."
```

**Export & Automate**

```text
"Export a JSON + Markdown user-flow topology report for our PR review gate."
```

---

## Commands & Diagnostics

| Command | Environment | What it does |
| :--- | :--- | :--- |
| `/doctor` | Claude Code / Codex | Read-only diagnostic check of installed skill paths, plugin manifests, and runtime prerequisites |
| `python3 scripts/self_check.py` | Terminal / CI | Deterministic offline verification of manifests, skill contracts, and governance files |
| `node bin/code2flow.mjs audit .` | Terminal / CI | Scan a frontend or mobile repository, emit Mermaid user-flow diagrams, and run the 11-heuristic UX gap audit |

---

## How it works

1. **Intent Routing** — Your AI agent matches your request against `skills/design-os-code2flow/SKILL.md` frontmatter triggers.
2. **Progressive Context Loading** — Only the entry-point `SKILL.md` router loads initially; detailed recipes and scripts load on demand.
3. **Deterministic Execution** — Domain scripts and contracts execute locally with reproducible inputs and outputs.
4. **Gate Verification** — `scripts/self_check.py` and domain verifiers (`npm test`) validate the artifact before completion.
5. **Zero-Telemetry Delivery** — Verified files are written directly to your workspace with zero external network calls.

```text
User Prompt / CLI Invocation
            │
            ▼
┌───────────────────────────────────────────────┐
│ skills/design-os-code2flow/SKILL.md
│ Progressive disclosure router & hard rules    │
└───────────┬───────────────────────────────────┘
            │ loads on demand
            ▼
┌───────────────────────────────────────────────┐
│ node bin/code2flow.mjs audit .
│ Deterministic build & contract enforcement    │
└───────────┬───────────────────────────────────┘
            │ verifies
            ▼
┌───────────────────────────────────────────────┐
│ python3 scripts/self_check.py + /doctor       │
│ Zero-telemetry local verification gate        │
└───────────────────────────────────────────────┘
```

### What loads when

`design-os-code2flow` uses progressive context disclosure so your agent's context window stays fast and focused:

| File | Loaded when |
| :--- | :--- |
| `skills/design-os-code2flow/SKILL.md` | Always (~100–150 lines) — routing rules, triggers, and execution workflow |
| `docs/cookbook.md` | When selecting multi-step prompt recipes or domain patterns |
| `commands/doctor.md` / `prompts/doctor.md` | Only when running `/doctor` diagnostics |
| `llms.txt` | When indexed by AI answer engines, RAG pipelines, or repo crawlers |

---

## File structure

```text
design-os-code2flow/
├── .claude-plugin/
│   ├── plugin.json                 # Claude Code plugin manifest
│   └── marketplace.json            # Claude Code marketplace catalog
├── .codex-plugin/
│   └── plugin.json                 # OpenAI Codex plugin & interface manifest
├── .agents/
│   └── plugins/marketplace.json    # Cross-agent local plugin registry
├── .factory-plugin/
│   ├── plugin.json                 # Factory / Droid plugin manifest
│   └── marketplace.json            # Factory marketplace metadata
├── skills/
│   └── design-os-code2flow/
│       └── SKILL.md                # Canonical agent skill entrypoint
├── commands/
│   └── doctor.md                   # /doctor diagnostic slash command
├── prompts/
│   └── doctor.md                   # Codex diagnostic prompt mirror
├── scripts/
│   └── self_check.py               # Deterministic repository & skill self-check
├── docs/
│   ├── cookbook.md                 # Copy-paste prompt recipes by job
│   └── llms.txt                    # GEO / LLM discovery index
├── PRIVACY.md                      # Zero-telemetry & local-first privacy commitment
├── SECURITY.md                     # Vulnerability disclosure & security policy
├── CONTRIBUTING.md                 # Contribution workflow & verification rules
├── CODE_OF_CONDUCT.md              # Contributor Covenant code of conduct
├── CHANGELOG.md                    # Release history
├── llms.txt                        # Root LLM indexing manifest
├── LICENSE                         # PolyForm Shield 1.0.0
└── README.md
```

---

## Quality bar & Limitations

### It's working if...

- `python3 scripts/self_check.py` prints `ok: design-os-code2flow self-check passed (design-os-code2flow)` and exits `0`.
- `npm test` passes with zero contract or test regressions.
- Your AI coding agent loads `skills/design-os-code2flow/SKILL.md` automatically when given any prompt from [`docs/cookbook.md`](docs/cookbook.md).
- Network traffic during execution remains zero (guaranteed by [`PRIVACY.md`](PRIVACY.md)).

### When not to use

- Pure backend microservices or CLI tools with no screen/route navigation graph.
- Visual pixel-level contrast or typography inspection (pair with `design-os` or `design-os-figma-plugin`).
- Runtime profiling of database query latency.

---

## DESIGN:OS Ecosystem

`design-os-code2flow` is one of the 13 source-available engines in the **`DESIGN:OS`** ecosystem:

| Engine | Live Docs | Repository | Layer |
| :--- | :--- | :--- | :--- |
| **DESIGN:OS CLI** | [jangtrinh.github.io/design-os](https://jangtrinh.github.io/design-os/) | [`jangtrinh/design-os`](https://github.com/jangtrinh/design-os) | `cli` |
| **Knowledge Builder** | [jangtrinh.github.io/design-os-knowledge-builder](https://jangtrinh.github.io/design-os-knowledge-builder/) | [`jangtrinh/design-os-knowledge-builder`](https://github.com/jangtrinh/design-os-knowledge-builder) | `compiler` |
| **Figma Plugin & CLI** | [jangtrinh.github.io/design-os-figma-plugin](https://jangtrinh.github.io/design-os-figma-plugin/) | [`jangtrinh/design-os-figma-plugin`](https://github.com/jangtrinh/design-os-figma-plugin) | `plugin` |
| **SVG Animation Engine** | [jangtrinh.github.io/design-os-svg-animation](https://jangtrinh.github.io/design-os-svg-animation/) | [`jangtrinh/design-os-svg-animation`](https://github.com/jangtrinh/design-os-svg-animation) | `engine` |
| **3D Blender Agent** | [jangtrinh.github.io/design-os-3d-blender](https://jangtrinh.github.io/design-os-3d-blender/) | [`jangtrinh/design-os-3d-blender`](https://github.com/jangtrinh/design-os-3d-blender) | `3d / cad` |
| **OPAH ONE Drone** | [jangtrinh.github.io/design-os-drone-showcase](https://jangtrinh.github.io/design-os-drone-showcase/) | [`jangtrinh/design-os-drone-showcase`](https://github.com/jangtrinh/design-os-drone-showcase) | `hardware` |
| **GitHub Pages Engine** | [jangtrinh.github.io/design-os-github-page](https://jangtrinh.github.io/design-os-github-page/) | [`jangtrinh/design-os-github-page`](https://github.com/jangtrinh/design-os-github-page) | `pages` |
| **Apple Design OS** | [jangtrinh.github.io/design-os-apple](https://jangtrinh.github.io/design-os-apple/) | [`jangtrinh/design-os-apple`](https://github.com/jangtrinh/design-os-apple) | `swiftui` |
| **Agent Teacher** | [jangtrinh.github.io/design-os-pedagogy](https://jangtrinh.github.io/design-os-pedagogy/) | [`jangtrinh/design-os-pedagogy`](https://github.com/jangtrinh/design-os-pedagogy) | `pedagogy` |
| **Origami CAD** | [jangtrinh.github.io/design-os-origami](https://jangtrinh.github.io/design-os-origami/) | [`jangtrinh/design-os-origami`](https://github.com/jangtrinh/design-os-origami) | `packaging` |
| **Voice UX Architecture** | [jangtrinh.github.io/design-os-voice-ux](https://jangtrinh.github.io/design-os-voice-ux/) | [`jangtrinh/design-os-voice-ux`](https://github.com/jangtrinh/design-os-voice-ux) | `voice-ai` |
| **Code2Flow** | [jangtrinh.github.io/design-os-code2flow](https://jangtrinh.github.io/design-os-code2flow/) | [`jangtrinh/design-os-code2flow`](https://github.com/jangtrinh/design-os-code2flow) | `ast / audit` |
| **Generative UI** | [jangtrinh.github.io/design-os-generative-ui](https://jangtrinh.github.io/design-os-generative-ui/) | [`jangtrinh/design-os-generative-ui`](https://github.com/jangtrinh/design-os-generative-ui) | `runtime` |

---

## Contributing, Governance & License

- **Contributing**: See [`CONTRIBUTING.md`](CONTRIBUTING.md) for pull request guidelines and verification gates (`python3 scripts/self_check.py`).
- **Code of Conduct**: Governed by [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).
- **Security & Privacy**: Zero telemetry — see [`SECURITY.md`](SECURITY.md) and [`PRIVACY.md`](PRIVACY.md).
- **Changelog & LLM Index**: Track releases in [`CHANGELOG.md`](CHANGELOG.md) and machine-readable index in [`llms.txt`](llms.txt).
- **License**: [PolyForm Shield 1.0.0](LICENSE) © [Jang Trinh](https://github.com/jangtrinh). Free to use and modify, including for paid client work; you may not resell it or build a competing product from it.

---

If `design-os-code2flow` saves you time, a star on GitHub helps other engineers and AI agents find it.

<p align="left">
  <a href="https://buymeacoffee.com/jangtrinh">
    <img src="https://img.shields.io/badge/Buy_Me_a_Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black" alt="Buy Me a Coffee">
  </a>
</p>
