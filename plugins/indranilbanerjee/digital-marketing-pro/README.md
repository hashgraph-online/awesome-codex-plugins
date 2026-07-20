# Digital Marketing Pro

> **Your agency just signed a 50-brand client. The previous agency left no playbook. Three brands are bleeding budget, two have stale positioning, one is launching in a regulated jurisdiction next month. Where do you start?**

Run `/digital-marketing-pro:engagement` against each brand. Same 12-Part Strategy Flow, same Four Core Documents, same 61-step structure — auditable across the entire portfolio in ~60 minutes per brand on Claude Opus 4.8. No more inconsistent depth between brands. No more "what did the last agency do?" mysteries. No more compliance gaps in regulated jurisdictions.

Open-source AI marketing plugin — **158 skills, 24 specialist agents, EU AI Act Article 50 ready, Cowork team-persistent**. Built for marketing agencies, in-house teams running 50–200 brands, and consultancies. Installs on **Claude Code** (CLI + IDE), **Anthropic Cowork**, **OpenAI Codex**, **Cursor 2.5+**, **GitHub Copilot CLI**, **Google Antigravity 2.0**, **Hermes Agent**, and **OpenClaw** + 35+ Agent Skills platforms. Created by [Indranil Banerjee](https://indranil.in) · [LinkedIn](https://www.linkedin.com/in/askneelnow/) · [X](https://x.com/askneelnow).

[![Version](https://img.shields.io/badge/version-3.15.1-blue.svg)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/indranilbanerjee/digital-marketing-pro?style=flat&logo=github&color=yellow)](https://github.com/indranilbanerjee/digital-marketing-pro/stargazers)
[![Forks](https://img.shields.io/github/forks/indranilbanerjee/digital-marketing-pro?style=flat&logo=github&color=blue)](https://github.com/indranilbanerjee/digital-marketing-pro/network/members)
[![Issues](https://img.shields.io/github/issues/indranilbanerjee/digital-marketing-pro?logo=github)](https://github.com/indranilbanerjee/digital-marketing-pro/issues)
[![Last commit](https://img.shields.io/github/last-commit/indranilbanerjee/digital-marketing-pro?logo=github)](https://github.com/indranilbanerjee/digital-marketing-pro/commits/main)
[![Tests](https://img.shields.io/badge/tests-207%2F207%20passing-brightgreen.svg)](tests/)
[![Platforms](https://img.shields.io/badge/platforms-8%20native%20%2B%2035%20Agent%20Skills-success.svg)](#works-on-40-agent-harnesses-via-the-agent-skills-open-standard)
[![Cowork](https://img.shields.io/badge/cowork-team%20persistent-purple.svg)](#supported-surfaces-v3151)
[![EU AI Act](https://img.shields.io/badge/EU%20AI%20Act-Article%2050%20ready-darkred.svg)](skills/context-engine/compliance-rules.md)

> 🆕 **Just shipped — v3.15.1 (July 12, 2026):** Self-containment patch — removed every cross-plugin capability reference from skills. Visual-production handoffs, C2PA signing, workflow resume, and publish-dir checks are all DMP-native paths now; install DMP alone and every documented capability works. [Read what's new →](#whats-new) · [Full changelog →](CHANGELOG.md)
>
> <sub>Previously — **v3.15.0 (July 7, 2026):** The **Reliability & Truth** release — a full-repo audit fixed ~200 findings in one pass. Connectors are honestly opt-in (the shipped `.mcp.json` is empty; fictional npm packages purged), all 18 execution skills carry a uniform typed-approval gate (closes issue #6), the Tessl review workflow moved to the `tessl review` CLI (closes issue #8), agents consolidated 25 → 24, C2PA gained the Article 50 `--ai-disclosure` assertion, and a new doc-vs-argparse contract linter + state-layer tests grew the suite from 123 to 207 passing. [Read what's new →](#whats-new) · [Full changelog →](CHANGELOG.md)</sub>

```bash
# Install — one line
/plugin marketplace add indranilbanerjee/neels-plugins
/plugin install digital-marketing-pro@neels-plugins
```

> If this saves you time, [give it a star ⭐](https://github.com/indranilbanerjee/digital-marketing-pro/stargazers) — it's the single thing that helps other marketers find it.

---

## Who this is for

| If you're a... | Run this | What you get |
|---|---|---|
| 🏢 **Marketing agency** managing 50–200 brands | `/digital-marketing-pro:engagement` per brand, then `/digital-marketing-pro:cowork-setup` for team Drive persistence | Same 12-Part Strategy Flow audited across every brand. New-hire onboarding goes from 6 weeks to 6 hours. Per-brand AI cost rollup via `:agency-dashboard`. |
| 👔 **In-house marketing team** (B2B SaaS · e-commerce · fintech · healthtech) | `/digital-marketing-pro:engagement` once to anchor strategy, then `:content-engine` + `:campaign-plan` for ongoing work | A single canonical strategy doc, monthly stakeholder reports via `:performance-report`, content + campaigns that tie back to the strategy instead of drifting. |
| 🚀 **Marketing automation builder** (n8n · Zapier · Make · Pipedream · custom) | `/digital-marketing-pro:doctor` to see what's wired, `:execute-action` to fire real API calls | 8 verified HTTP connectors executing end-to-end (Slack · HubSpot · Klaviyo · SendGrid · Brevo · Customer.io · Mailchimp · Ahrefs); 25 OAuth connectors via MCP manifest. Stdlib only, no third-party deps. |
| 💼 **Solo consultant** or freelance marketer | `/digital-marketing-pro:engagement` per client | 50–60 canonical files per client engagement in ~60 minutes for $15–40 of API spend. Same depth on every project. Installs on Codex / Cursor / Copilot CLI / Antigravity if you don't live in Claude. |
| 📈 **Growth team** / product marketer | `:funnel-architect` → `:analytics-insights` → `:attribution-model` → `:churn-risk` → `:cohort-analysis` | Journey design + measurement + retention + churn — all aligned to the strategy document, not isolated outputs. MMM + incrementality testing baked in. |
| 🛡 **Compliance-led marketer** (EU · UK · India · Brazil · California) | `/digital-marketing-pro:check` before publishing anything | C2PA content provenance, EU AI Act Article 50 disclosure, GDPR + CCPA + DPDPA + LGPD across 16 jurisdictions, deepfake disclosure clauses on every AI creative brief. |

---

## How does this compare?

| | **Digital Marketing Pro** | Anthropic Marketing (official) | Composio Marketing | claude-seo (community) |
|---|---|---|---|---|
| Skills count | **158** | ~7 | ~12 | 25 SEO-only sub-skills |
| Specialist agents | **24** | 0 | 0 | 18 SEO-only |
| Has a methodology | **Yes — 12-Part Strategy Flow (61 explicit steps)** | No | No | No |
| Multi-brand / agency support | **Yes — per-brand state, brand-switch, agency-dashboard** | No | No | No |
| EU AI Act Article 50 ready | **Yes — C2PA + deepfake disclosure + 16 jurisdictions** | No | No | Partial |
| Cowork team persistence | **Yes — Drive MCP routing (v3.12.0)** | Cowork-native | Composio cloud | n/a |
| Real API execution | **Yes — 8 connectors live, 25 manifest-ready** | OAuth via plugin | OAuth via Composio | Optional DataForSEO / Firecrawl |
| 6-platform AEO/GEO audit | **Yes — incl. Google AI Mode (May 2026)** | No | No | Yes (AEO + GEO) |
| Cross-platform install | **8 native — CC + Cowork + Codex + Cursor + Copilot CLI + Antigravity + Hermes + OpenClaw** | Cowork only | Cowork + Codex | CC + Codex |
| Tests | **207 stdlib unittest** | unknown | unknown | 271 incl. SSRF/DNS coverage |
| License | **MIT — no telemetry, no seats** | Proprietary | Proprietary | MIT |
| Maintainer responsiveness | Direct via [@askneelnow](https://linkedin.com/in/askneelnow) | Anthropic queue | Composio queue | Community |

---

## Get started in 5 minutes (non-developer path)

**Are you a marketer, agency owner, or content lead who doesn't live in a terminal?** Here's the fastest path:

1. **Open [Anthropic Cowork](https://claude.com/cowork)** in your browser (no installation, no terminal, no command line). Sign up free if you don't have an account.
2. **Click your profile menu → Settings → Plugins → Add Marketplace.** Paste: `indranilbanerjee/neels-plugins`
3. **Find "Digital Marketing Pro" in the list → click Install.**
4. **Type in chat:** *"Let's set up a brand for ACME Corp"* — Claude will walk you through brand setup (voice, audience, jurisdiction, competitors).
5. **Then ask:** *"Run a full marketing engagement for ACME"* — and watch ~50–60 strategy documents get produced over the next ~60 minutes.

That's it. You never touched a command line. Your team Drive will hold the outputs. Re-open Cowork tomorrow and pick up where you left off.

**If you're more technical**, see [Quick start](#quick-start) below for the Claude Code CLI install (one terminal command).

**For team usage (agencies running 50+ brands)**, also run `/digital-marketing-pro:cowork-setup` once so brand state persists across Cowork sessions via your team's Google Drive.

---

## Why Digital Marketing Pro

Most AI marketing tools generate isolated outputs — a campaign brief here, an email there. No canonical sequence, no shared state, no enforced structure. Result: inconsistent depth, missed dependencies, outputs that don't compound.

**DM Pro runs every brand through the same 12 parts, producing the same files in the same order, with explicit dependency rules between them.** That's the whole product. Everything else — the 158 skills, 24 agents, May–June 2026 compliance updates, Cowork persistence — exists to make that 12-Part Flow ship cleanly for real agencies on real client work.

| What this gives you that ad-hoc prompts don't | Why it matters |
|---|---|
| **Canonical 12-Part Strategy Flow** producing the Four Core Documents (61 explicit steps) | Every engagement looks the same, so handoffs work and quality is auditable |
| **Two-Views Model** (v1 unbiased + v2 client-validated) | You never lose the original market view when the client pushes back |
| **Decision Matrix** — maps validation responses to re-runs | Stops over-running (wasted hours) and under-running (broken strategy) |
| **Living Project Instruction File** — single source of truth per engagement | All skills read it first; corrections propagate automatically |
| **EU AI Act Article 50 readiness** built in | C2PA provenance signing, deepfake disclosure, draft-guidelines table in compliance |
| **6-platform AEO/GEO audit** (incl. Google AI Mode) | The first marketing plugin to treat AI Mode as a distinct surface from AI Overviews |

---

## What you get in 60 minutes

Run `/digital-marketing-pro:engagement` and the plugin produces a full brand-strategy engagement in roughly 60 minutes on Opus 4.8 — **~50–60 canonical files** organized by part:

- **Part 1** — Stone-vs-Opinion intake (what the client knows for certain vs what they believe)
- **Part 2** — External market research (unbiased, no client docs)
- **Part 3** — Four Core Documents — 61 explicit steps across Business & SBU Analysis, Segmentation Framework, Brand Positioning & Communications, DMFlow
- **Part 4** — Competitive + Customer + Market analysis (4 unbiased docs)
- **Part 5** — Client Validation Document — the one true stop
- **Part 6** — Selective v2 re-runs per Decision Matrix
- **Part 7** — Preparation documents (campaign architecture, KPI tree, content pillars, approval chains)
- **Part 8** — **Growth Plan + 12-month Yearly Planner** (the flagship deliverable)
- **Part 9** — Channel-strategy fan-out (up to 17 channel docs in 7 families)
- **Part 10** — Execution artefacts (ad copy, post copy, headlines, CTAs)
- **Part 11** — AI creative briefs (with Nano Banana Pro / Veo 3.1 / Gemini Omni model guidance and C2PA + deepfake-disclosure clauses)
- **Part 12** — Continuous improvement loop

Cost: roughly **$15–40 in Claude API spend** for a full 12-part engagement using Opus 4.8. The plugin itself is MIT-licensed and free.

---

## Quick start

### 1. Install on Claude Code (canonical)

```bash
/plugin marketplace add indranilbanerjee/neels-plugins
/plugin install digital-marketing-pro@neels-plugins
```

`/plugin` commands work in **Claude Code** (CLI + IDE at [claude.com/code](https://claude.com/code)) and **Anthropic Cowork**. In the standard Claude chat app (browser `claude.ai` OR the installed Claude Desktop app) plugins still install and run, but management is via the **Plugins** UI button at the bottom of the chat — not via `/plugin` slash commands. See the [Updating](#updating) section for the recovery procedure if you accidentally try a slash command in the chat UI.

### 2. Turn on auto-update (recommended)

Third-party marketplaces have auto-update **OFF by default** in Claude Code — no banner tells you when a new version ships. Fix it once:

Open `/plugin` → **Marketplaces** tab → find `neels-plugins` → toggle **Enable auto-update**. Done — future releases pull at session start; `/reload-plugins` applies mid-session without restart.

### 3. Set up your first brand

```
/digital-marketing-pro:brand-setup
```

Interactive brand profiling — voice, audience, channels, industry, target jurisdictions, competitors, goals. Quick mode (5 questions) or full mode (17 questions). Optional: `/digital-marketing-pro:import-guidelines` to bulk-load existing brand guidelines, SOPs, or templates.

### 4. Run a full engagement, or jump straight to a workflow

```
/digital-marketing-pro:engagement           # full 12-Part Strategy Flow (~60 min)
```

Or jump straight to one workflow:

```
/digital-marketing-pro:campaign-plan        # multi-channel campaign with budget, timeline, KPIs
/digital-marketing-pro:seo-audit            # technical + content + E-E-A-T + AI visibility audit
/digital-marketing-pro:content-engine       # blog / ad / email / social / landing / video drafts
/digital-marketing-pro:competitor-analysis  # multi-dimensional deep-dive
/digital-marketing-pro:performance-report   # trends + anomalies + recommendations
/digital-marketing-pro:email-sequence       # subject lines, copy, timing, segmentation
/digital-marketing-pro:check                # pre-publish quality gate (hallucination + voice + claims)
/digital-marketing-pro:status               # unified brand snapshot
/digital-marketing-pro:resume               # resume an interrupted long workflow (engagement / campaign-plan / etc.)
/digital-marketing-pro:output-folder        # open the user-visible ~/Documents/DigitalMarketingPro/ folder
```

### 5. Find your output

```
~/.claude-marketing/<brand-slug>/
├── brand-profile.json           ← brand voice, audience, guardrails, jurisdictions
├── engagements/
│   └── <engagement-slug>/
│       ├── 01-client-inputs/    ← Part 1 Stone-vs-Opinion intake
│       ├── 02-research/         ← Part 2 external market research
│       ├── 03-four-core/        ← Part 3 Four Core Documents (61 steps)
│       ├── 04-analysis/         ← Part 4 competitive / customer / market
│       ├── 05-validation/       ← Part 5 Client Validation Document
│       ├── 06-v2-reruns/        ← Part 6 selective v2 re-runs
│       ├── 07-prep/             ← Part 7 internal operating layer
│       ├── 08-growth-plan/      ← Part 8 Growth Plan + Yearly Planner
│       ├── 09-channels/         ← Part 9 channel-strategy fan-out
│       ├── 10-execution/        ← Part 10 ad copy / post copy / headlines / CTAs
│       ├── 11-creative-briefs/  ← Part 11 AI creative instructions
│       ├── 12-improvement/      ← Part 12 continuous improvement loop
│       └── PROJECT_INSTRUCTIONS.md  ← Living Project Instruction File
└── insights/                    ← cross-engagement learnings
```

See the [Multi-Brand & Agency Guide](docs/multi-brand-guide.md) for the multi-client switching workflow.

---

## Real workflows you'd actually run

### 🆕 New-client onboarding (agency, week 1)
```
/digital-marketing-pro:brand-setup "ACME Corp"        # interactive: voice, audience, channels, jurisdiction
/digital-marketing-pro:competitor-analysis            # multi-dimensional deep-dive on top 5 competitors
/digital-marketing-pro:engagement                     # full 12-Part Strategy Flow (~60 min on Opus 4.8)
/digital-marketing-pro:check  engagements/.../03-four-core/*.md   # pre-publish gate before client review
```
Output: ~50–60 canonical files. Cost: $15–40 in API spend. Time saved: ~3 weeks of senior-strategist labor.

### 📊 Quarterly business review (in-house, last week of quarter)
```
/digital-marketing-pro:performance-report   --period=Q2-2026
/digital-marketing-pro:attribution-report   --period=Q2-2026 --model=data-driven
/digital-marketing-pro:competitor-monitor   --since=2026-04-01
/digital-marketing-pro:continuous-improvement-loop --quarter=Q2-2026
```
Output: stakeholder-ready Q2 review with anomalies, attribution shift, competitor moves, and next-quarter recommendations.

### 🎯 SEO sprint (any audience, 1 week)
```
/digital-marketing-pro:seo-plan                       # 4-pillar scorecard; weakest pillar drives the theme
/digital-marketing-pro:keyword-cluster  seeds.csv     # SERP-overlap clustering into pillar+spokes
/digital-marketing-pro:backlink-gap  acme.com competitor1.com competitor2.com
/digital-marketing-pro:content-engine                 # draft the top 3 pillar pages
/digital-marketing-pro:check  drafts/*.md             # hallucination + brand voice + claims gate
/digital-marketing-pro:seo-drift  baseline.csv current.csv     # 30 days later, what moved
```

### 🤖 Marketing automation flow (builders)
```
/digital-marketing-pro:doctor                         # which actions are live vs need connector setup
/digital-marketing-pro:execute-action --action diagnostic --execute            # GA4 + GSC pull
/digital-marketing-pro:execute-action --action audit-current --execute         # workflow state check
/digital-marketing-pro:execute-action --action enable-automation --confirm     # Klaviyo flow activate
```
Output: real API calls fired against your stack with audit logging at `~/.claude-marketing/{brand}/executions/`. Combine with n8n / Make / Zapier for human-in-the-loop approval gates.

### 🛡 Pre-publish compliance gate (every campaign)
```
/digital-marketing-pro:check  campaign.md --full      # hallucination + voice + claims + jurisdictions
/digital-marketing-pro:c2pa-metadata  hero.png        # sign image with provenance for EU Article 50
```

### 🎨 AI creative brief with EU disclosure (every AI-generated asset)
```
/digital-marketing-pro:ad-creative                # ad concepts + copy with EU/FTC disclosure clauses
/digital-marketing-pro:influencer-creator         # FTC + EU deepfake clauses baked in
```

---

## Supported surfaces (v3.15.1)

| Platform | Install command | Manifest path | Status |
|---|---|---|---|
| **Claude Code** CLI + IDE extensions | `/plugin install digital-marketing-pro@neels-plugins` | `.claude-plugin/plugin.json` | Full support (canonical) |
| **Anthropic Cowork** | Plugins UI → Add marketplace → `indranilbanerjee/neels-plugins` → Install | same `.claude-plugin/` files | Full support — no `/plugin` slash commands in Cowork (UI-only) |
| **OpenAI Codex** CLI + IDE + App | `codex plugin marketplace add indranilbanerjee/neels-plugins` then `codex plugin install digital-marketing-pro@neels-plugins` | `.codex-plugin/plugin.json` (published OpenAI schema) | Full skills + MCP support |
| **Cursor 2.5+** | In any Cursor Agent chat: `/add-plugin digital-marketing-pro@https://github.com/indranilbanerjee/digital-marketing-pro` | `.cursor-plugin/plugin.json` (published Cursor JSON Schema) | Full skills + agents + commands support |
| **GitHub Copilot CLI** | `copilot plugin marketplace add indranilbanerjee/neels-plugins` then `copilot plugin install digital-marketing-pro@neels-plugins` | `.github/plugin/plugin.json` (Copilot CLI also recognizes `.claude-plugin/plugin.json` as fallback) | Full skills + MCP support; subagents need `.agent.md` extension (open issue); custom slash commands not yet supported in Copilot CLI |
| **Google Antigravity 2.0** CLI + IDE | `agy plugin install https://github.com/indranilbanerjee/digital-marketing-pro` | `gemini-extension.json` (at repo root, per Google's reference pattern) | Full skills + hooks support; subagents need `/agent` CLI spawning; slash commands fold into skills via `agy plugin import gemini` |
| **Hermes Agent** (Nous Research) — Desktop + CLI on macOS / Windows / Linux | `hermes plugins install indranilbanerjee/digital-marketing-pro` | `plugin.yaml` + `__init__.py` at repo root (Hermes native spec) | Native plugin — adapter walks `skills/` at register time and exposes all 158 skills via `ctx.register_skill()`. Targets Hermes Desktop v0.15.2+ (public preview June 2 2026). |
| **OpenClaw** (formerly Clawdbot / Moltbot) | `openclaw plugins install git:github.com/indranilbanerjee/digital-marketing-pro` | `openclaw.plugin.json` at repo root (also auto-detects `.claude-plugin/plugin.json` as Claude-compatible bundle) | Native plugin via `openclaw.plugin.json`; `skills` field points at `./skills`. Also installable via ClawHub marketplace (submission pending). |

**Why this works:** Agent Skills became an open standard in December 2025 (donated to the Agentic AI Foundation; adopted by **41+ agent products** by June 2026 — see ["Works on 40+ agent harnesses"](#works-on-40-agent-harnesses-via-the-agent-skills-open-standard) below). All 158 SKILL.md files in DM Pro are platform-portable as written. The sibling manifests are thin platform-specific wrappers around the same `skills/` directory — no skill duplication, no maintenance fork. The pattern is borrowed from Google's reference repo [`gemini-cli-extensions/data-agent-kit-starter-pack`](https://github.com/gemini-cli-extensions/data-agent-kit-starter-pack).

**Minimum Claude Code version: 2.1.157** (declared via `requiredMinimumVersion` in plugin.json — landed in Claude Code v2.1.163, June 4 2026). Older Claude Code builds will be told to upgrade rather than load DMP with missing features.

---

## Works on 40+ agent harnesses (via the Agent Skills open standard)

Beyond the 8 surfaces above where we ship a native manifest, DMP's 158 `SKILL.md` files work out-of-the-box on any agent that adopted the [Agent Skills open standard](https://agentskills.io) (Anthropic-published Dec 2025, 41+ adopters as of June 2026). On each platform below, point it at our `skills/` folder and all 158 marketing skills are immediately discoverable. No platform-specific manifest needed.

**Tier 1 — verified-compatible platforms with explicit Agent Skills install paths:**

| Platform | Vendor | Install hint |
|---|---|---|
| [Goose](https://block.github.io/goose) | Block (Square) | `goose skills install github.com/indranilbanerjee/digital-marketing-pro/skills` |
| [OpenHands](https://openhands.dev) | Open Hands (cloud agents) | Mount this repo's `skills/` via the OpenHands skills config |
| [OpenCode](https://opencode.ai) | sst | `opencode skills import github:indranilbanerjee/digital-marketing-pro` |
| [Junie](https://junie.jetbrains.com) | JetBrains | Drop `skills/` into your project; Junie auto-discovers |
| [Gemini CLI](https://geminicli.com) | Google | `gemini skills add github:indranilbanerjee/digital-marketing-pro` |
| [Roo Code](https://roocode.com) | Roo Code Inc. | VS Code → Roo settings → Skills → import from URL |
| [Cline](https://github.com/cline/cline) / [Windsurf](https://windsurf.com) | open-source VS Code agents | Same Agent Skills import flow as Roo |
| [Kiro](https://kiro.dev) | Kiro | Spec-driven dev with Agent Skills support |
| [Amp](https://ampcode.com) | Sourcegraph | `amp skills add github:indranilbanerjee/digital-marketing-pro` |
| [Letta](https://letta.com) | Letta | Stateful-agents platform — skills load via the Letta SDK |
| [Mux](https://mux.coder.com) | Coder | Browser-based parallel cloud agents |
| [Factory](https://factory.ai) | Factory | "Droid" agents read Agent Skills bundles |
| [Workshop](https://workshop.ai) | Workshop | Multi-LLM cross-platform agent |
| [Tabnine](https://tabnine.com) | Tabnine | Enterprise context-aware AI agent |
| [Emdash](https://emdash.sh) | General Action | Parallel git-worktree agents |
| [Superconductor](https://superconductor.com) | Superconductor | Multiplayer cloud agents |
| [Ona](https://ona.com) | Ona | Background cloud-agent fleet |
| [Mistral Vibe](https://github.com/mistralai/mistral-vibe) | Mistral AI | `mistral-vibe skills install ...` |
| [VT Code](https://github.com/vinhnx/vtcode) | open-source | LLM-native code agent |
| [Qodo](https://qodo.ai) | Qodo | Code integrity agent |
| [Piebald](https://piebald.ai) | Piebald | Desktop agentic dev |
| [Autohand Code CLI](https://autohand.ai) | Autohand | ReAct terminal agent |
| [pi](https://github.com/badlogic/pi-mono) | open-source | Minimal terminal harness |
| [Command Code](https://commandcode.ai) | Command Code | Coding-taste-learning agent |
| [TRAE](https://trae.ai) | ByteDance | Adaptive AI IDE |
| [Firebender](https://firebender.com) | Firebender | Android-native agent |
| [bub](https://bub.build) | Bub | Channel-native agent framework |
| [fast-agent](https://fast-agent.ai) | evalstate | ACPX + Skills development |
| [nanobot](https://nanobot.wiki) | HKUDS | Ultra-light personal agent (Slack / Discord / Telegram / WeChat) |
| [Vita](https://vita-ai.net) | Vita | Virtual-desktop autonomous workers |
| [Snowflake Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code) | Snowflake | Data-platform agent |
| [Databricks Genie Code](https://docs.databricks.com/aws/en/assistant/skills) | Databricks | Data-engineering agent |
| [Laravel Boost](https://laravel.com/docs/12.x/boost#agent-skills) | Laravel | Laravel-specific agent skills layer |
| [Spring AI](https://spring.io/blog/2026/01/13/spring-ai-generic-agent-skills) | Spring | Java/Spring AI applications |
| [Agentman](https://agentman.ai) | Agentman | Healthcare revenue-cycle agents |
| [Google AI Edge Gallery](https://github.com/google-ai-edge/gallery) | Google | On-device mobile LLM agent |

**Quick test on any Tier-1 platform:**

```bash
# 1. Clone the skills folder (or point your platform at the GitHub raw URL)
git clone --depth=1 https://github.com/indranilbanerjee/digital-marketing-pro.git
# 2. Point your agent's skills-config at ./digital-marketing-pro/skills
# 3. Try: "Run a competitor analysis on stripe.com"
# Your agent picks /digital-marketing-pro:competitor-analysis automatically.
```

**Why we don't ship per-platform manifests for these:** the Agent Skills standard says agents discover by walking a directory tree for `SKILL.md` files — no manifest required. Shipping 35 extra wrapper manifests would create maintenance overhead with zero added value.

If you run into a platform-specific install snag, file a [GitHub issue](https://github.com/indranilbanerjee/digital-marketing-pro/issues) — we'll add platform-specific docs as users report patterns.

---

## The 12-Part Engagement Methodology

| Part | Name | Output |
|------|------|--------|
| 1 | Client Inputs | Stone vs Opinion intake (what client knows for certain vs what they believe) |
| 2 | External Research | Unbiased market research (no client docs used) |
| 3 | **Four Core Documents** | 61 explicit steps — Business & SBU (18), Segmentation (15), Brand Positioning (19), DMFlow (9) |
| 4 | Competitive + Customer + Market | 4 unbiased analysis documents (4.1–4.4) |
| 5 | **Client Validation Document** | The one true stop — client accepts/rejects/edits each finding |
| 6 | Selective v2 Re-runs | Subset of Part 3 + Part 4 docs re-run per the Decision Matrix |
| 7 | Preparation Documents | Internal operating layer (campaign architecture, KPI tree, content pillars, asset inventory, approval chains) |
| 8 | **Growth Plan + Yearly Planner** | The flagship 11-section client-facing strategy + 12-month operational calendar |
| 9 | Channel Strategy Fan-out | Up to 17 channel docs grouped into 7 families |
| 10 | Execution Artefacts | Ad copy, post copy, headlines, CTAs |
| 11 | AI Creative Instructions | Visual asset briefs with C2PA + EU Article 50 clauses |
| 12 | **Continuous Improvement Loop** | Quarterly briefs feeding signals back into product/offering decisions |

**Key architectural concepts:**
- **Two-Views Model** — Every engagement carries v1 (unbiased market view) and v2 (client-validated view) after Part 5. Operating decisions reference v2; ideation references both. v1 is never deleted.
- **Stone vs Opinion** — Every fact captured at intake is tagged with confidence. Stone = client knows for certain. Opinion = client believes (becomes a research question, not ground truth).
- **Decision Matrix** — Maps client validation responses to which v1 documents need v2 re-runs. Prevents over- and under-re-running.
- **Update-Back Rule** — Live operations surface corrections → source documents get versioned (v2.1, v2.2 …) → Living Project Instruction File propagates the change to all downstream skills.
- **Living Project Instruction File** — Single source of truth per engagement. All skills read it first.

15+ strategic-framework reference documents in `skills/context-engine/` support the methodology (Five Digital Markets, Channel Families, In-Market vs Out-Market, Multi-Dimensional Decision Framework, Unit Economics, Actionable Persona Format, B2B Decision-Making Unit, Three-Scenario Forecasting, 30/60/90-Day Framework, Reporting Cadence, Fixed vs Variable Budget, Competitor 3-Question Output, India Market Context, and more).

---

## What's new

DM Pro is updated against the **actual current marketing ecosystem state** — June 2026 platform refresh, Google I/O 2026, the active broad core algorithm update, EU AI Act draft implementing guidelines, Meta platform expansions, and the latest AI image/video model landscape. No "trained on 2024 data" surprises in your client outputs.

**v3.15.1 — Self-containment patch (July 12)**
Removed every cross-plugin capability reference from the skill surface: `ad-creative` and the engagement's Part 11 hand visual production to your own tooling (design team, AI generators, or connected design platforms) instead of naming a sibling plugin; `launch-campaign` C2PA signing and checkpoint-resume route through DMP's own `c2pa-metadata` and `/digital-marketing-pro:resume`; `validate-profile` checks DMP's own publish dir (`$DIGITAL_MARKETING_PRO_PUBLISH_DIR` / `~/Documents/DigitalMarketingPro/`); the EU compliance reference docs are DMP-centric. DMP is fully standalone — no other plugin is ever required for any documented capability. Cross-promo links in this README stay; capability delegation is gone.

**v3.15.0 — Reliability & Truth (July 7)**
A full-repo audit (orchestration, agents, skills, scripts, docs/manifests) surfaced ~200 findings, all fixed in one pass. One shared workspace-root/slugify/atomic-write helper (`_common.py`) ends the storage split-brain; connectors are honestly opt-in (the shipped `.mcp.json` is empty, fictional npm packages purged, memory backends demoted to "only if connected"); all 18 execution skills carry a uniform `## Execution gate` and flip to `disable-model-invocation: false` (**closes issue #6**); the Tessl workflow moves to the `tessl review` CLI + `.github/tessl-rubric.yml` (**closes issue #8**); `competitor-intelligence` merges into `competitive-intel` (**25 → 24 agents**); `embed-c2pa.py` gains the EU AI Act Article 50 `--ai-disclosure` assertion; and a new `check_skill_contracts.py` doc-vs-argparse linter + state-layer tests grow the suite **123 → 207 passing**. Every fabricated capability, stale count, and phantom flag is fixed or labeled.

**v3.14.1 — README sync + test-infra extension (June 28)**
Patch release fixing 4 stale references in this README that escaped the v3.14.0 ship: the Cowork badge anchor, the `## Supported surfaces` heading, a second internal anchor, and the missing v3.13.1 + v3.14.0 entries in this very section. Plus extended `tests/test_release_consistency.py` to lock the Supported-surfaces heading to the canonical version + verify all anchor links to `#supported-surfaces-v…` match — so this drift class can never reach a release again. No runtime change.

**v3.14.0 — June 2026 market-refresh sweep (June 28)**
Comprehensive ecosystem-change audit against primary vendor docs. Every claim verified against Anthropic / OpenAI / Google AI / Google Ads / EU Commission primary sources before any code change.

- **Meta Graph API bumped v20.0 → v24.0** in `scripts/connector_resolver.py` (4 callsites). All pre-v24 Meta Marketing API calls were scheduled to fail 2026-06-09 — our v20 hits would have started returning HTTP 400/410. Affected: campaigns / posts / feed / campaign-updates endpoints.
- **Model registry rebuilt to 47 entries** verified against [platform.claude.com](https://platform.claude.com/docs/en/about-claude/model-deprecations), [developers.openai.com](https://developers.openai.com/api/docs/deprecations), [ai.google.dev/gemini-api/docs/deprecations](https://ai.google.dev/gemini-api/docs/deprecations). New active flagships: **Claude Opus 4.8** (now Anthropic's recommended), **GPT-5.5 family**, **gpt-image-2**, **Gemini 3.1 Pro Preview**, **Gemini 3.1 Flash-Lite**, **Veo 3.1 Preview**, **Nano Banana Pro (GA gemini-3-pro-image)**, **Nano Banana 2 (GA gemini-3.1-flash-image with video-to-image)**. Newly deprecated: **full GPT-5 family** + **o3 family** (shutdown 2026-12-11), **Gemini 2.5 family** (shutdown 2026-10-16), **Imagen 4** (2026-06-15). Newly retired and routed to replacements automatically: **Gemini 2.0 family** (shutdown 2026-06-01), **Gemini 3 preview image variants** (shutdown 2026-06-25), **Veo 2.0/3.0/3.0-Fast** (shutdown 2026-06-30).
- **Resolver now auto-rewrites `retired` model IDs** to their `replacement_id` unconditionally (was previously only `deprecated` status). Means cached config pointing at dead model IDs gets routed to a working replacement instead of HTTP 404. New test `test_retired_falls_forward_unconditionally` covers this.
- **`python scripts/resolve_model.py --check-params <file>` scanner** flags any Python file passing `temperature` / `top_p` / `top_k` near Claude Opus 4.7+ targets (those return HTTP 400). Pre-flight scan of all 3 plugins' `scripts/*.py` was clean.
- **18 aliases re-pointed.** `latest-text-anthropic` → claude-opus-4-8, `latest-text-openai` → gpt-5.5, `latest-image-photoreal-google` → gemini-3-pro-image (Imagen 4 was deprecated path), `latest-video-google` → veo-3.1-generate-preview, `latest-image-google` → gemini-3-pro-image (was retired preview ID).
- **Google Ads API v24.1 + v24.2 documented** in `skills/paid-advertising/google-ads.md`. v24.1 added 4 new experiment types (`ADOPT_AI_MAX`, `ADOPT_BROAD_MATCH_KEYWORDS`, `OPTIMIZE_ASSETS`, `PMAX_REPLACEMENT_SHOPPING`) + `mobile_device_platform` segment. v24.2 added `GENERATE_LANDING_PAGE_TEXT` asset automation + first-class Local Services Ads (`AssetGroup.google_local_services_info`) + beta `MultiPartyAuthReview` for regulated verticals.
- **EU AI Act Code of Practice second-draft refresh** in `skills/context-engine/eu-code-of-practice.md`. Section 1 (Providers) now consolidates around two-layered marking (secured metadata required + watermarking required); C2PA explicitly satisfies the metadata layer. Section 2 (Deployers) dropped the AI-generated-vs-AI-assisted taxonomy entirely in favor of design + placement requirements for icons/labels/disclaimers on deepfakes + text publications on matters of public interest. Added operational readiness checklist for 2026-08-02 Article 50 applicability date.
- **Google I/O 2026 additions**: `skills/aeo-audit/SKILL.md` adds callout for **Google Information Agents** (AI Pro/Ultra subscriber feature launching summer 2026) as future 7th probe target alongside ChatGPT/Perplexity/AI Mode/AI Overviews/Gemini/Copilot. `skills/local-seo/SKILL.md` adds **2026 priority section** for Google **Agentic Booking expansion** to local services / home repair / beauty / pet care with three opt-in requirements (GBP scheduling integration, `AvailabilityFeed` structured data, Service-catalog price transparency).
- **EvoLink vendor support** added to model curator (via community PR merged during this release): multi-provider API gateway aggregating DeepSeek/Doubao/MiniMax through a single API key. 3 new aliases (`latest-text-evolink`, `latest-balanced-evolink`, `latest-fast-evolink`).
- **`docs/MODEL-CURATOR.md` refresh** with current alias resolutions + new § "Parameter compatibility — Claude Opus 4.7 and later" explaining the HTTP 400 risk.

Test count: 114 → **120**. Native platforms unchanged at 8.

**v3.13.1 — Test infrastructure hardening + user-friendliness polish (June 9)**
Triggered by user push-back: "you have the testing infrastructure, so test everything properly and make sure everything works awesomely."

- **Tests expanded 70 → 114** with three new test modules: `test_release_consistency.py` (25 tests) catches version drift / README badge staleness / CHANGELOG out-of-sync / install commands going missing / critical sections going missing / broken anchor links; `test_hermes_edge_cases.py` (10 tests) for adapter resilience under bad ctx / None / SDK surface drift; plus assorted top-ups.
- **Troubleshooting section** added to README covering common install issues for all 8 native platforms (Claude Code / Cowork / Codex / Cursor / Copilot CLI / Antigravity / Hermes / OpenClaw).
- **5-minute non-developer install path** added to README for marketers who don't want to read 60K of docs to get started.

**v3.13.0 — Multi-harness expansion: native Hermes + OpenClaw + 40 Agent Skills platforms (June 9)**
Verified-real native manifests for two more agent harnesses, plus documented compatibility with 35 additional platforms via the Agent Skills open standard. Every claim verified against primary sources (the Hermes plugin docs at [hermes-agent.nousresearch.com](https://hermes-agent.nousresearch.com/docs/guides/build-a-hermes-plugin), the OpenClaw manifest spec at [docs.openclaw.ai](https://docs.openclaw.ai/plugins/manifest), the Agent Skills client showcase at [agentskills.io](https://agentskills.io)).

- **Hermes Agent (Nous Research)** — native plugin via `plugin.yaml` + `__init__.py` at repo root. The Python adapter walks our `skills/` directory at register-time and exposes all 158 marketing skills to Hermes via `ctx.register_skill()`. Defensive coding throughout — no Hermes runtime dependencies; uses stdlib only; degrades gracefully if the Hermes API surface differs from spec. Tested against Hermes Desktop v0.15.2 (public preview June 2 2026). Install: `hermes plugins install indranilbanerjee/digital-marketing-pro`.
- **OpenClaw (formerly Clawdbot / Moltbot)** — native manifest via `openclaw.plugin.json` at repo root. Points OpenClaw at `./skills` for direct discovery. OpenClaw also auto-detects our existing `.claude-plugin/plugin.json` as a Claude-compatible bundle, so the native manifest is for first-class discoverability + ClawHub marketplace eligibility. Install: `openclaw plugins install git:github.com/indranilbanerjee/digital-marketing-pro`.
- **40+ Agent Skills platforms documented** — Goose (Block) · OpenHands · OpenCode · Junie (JetBrains) · Gemini CLI · Roo Code · Kiro · Amp · Letta · Mux (Coder) · Factory · Workshop · Tabnine · Mistral Vibe · Emdash · Superconductor · Ona · VT Code · Qodo · Piebald · Autohand Code CLI · pi · Command Code · TRAE (ByteDance) · Firebender · bub · fast-agent · nanobot (HKUDS) · Vita · Snowflake Cortex Code · Databricks Genie Code · Laravel Boost · Spring AI · Agentman · Google AI Edge Gallery. All read SKILL.md files from a directory tree — point any of them at our `skills/` folder and 158 marketing skills are immediately discoverable.
- **70-test stdlib suite** (up from 49) — 21 new tests cover the Hermes adapter (plugin.yaml schema validation, `__init__.py` import smoke test, `register(ctx)` against mock context with all 158 skills, graceful degradation when ctx surface differs from spec) and the OpenClaw manifest (id + configSchema required, skills field points at `./skills`, no hooks, no unexpected fields). Run with `python tests/run_all.py`.
- **Zero impact on existing platforms** — `plugin.yaml`, `__init__.py`, and `openclaw.plugin.json` are at the repo root but Claude Code only reads `.claude-plugin/plugin.json`, Cowork only reads the same path, Codex only reads `.codex-plugin/`, etc. Each platform reads its own manifest path and ignores the others — same pattern that's been working since v3.8.0 (May 2026). `__init__.py` is never executed by Claude Code (it doesn't auto-execute Python files). MCP auto-connects, hooks, skill descriptions — none change.

Skill count: 158 unchanged. Test count: 49 → **70**. Native platforms: 6 → **8**. Documented Agent Skills coverage: 6 → **41+**.

**v3.12.0 — Cowork persistence, fallback models, model-freshness, tests (June 8)**
Research-grounded hardening pass. Verified GitHub issue [#51398](https://github.com/anthropics/claude-code/issues/51398) — `${CLAUDE_PLUGIN_DATA}` is NOT persistent across Anthropic Cowork sessions, contrary to the docs. Solution shipped:

- **New `/digital-marketing-pro:cowork-setup` skill + command.** Detects the Cowork sandbox, verifies a Drive MCP, creates the canonical Drive folder layout (`<root>/_brands/`, `_runs/`, `_plans/`), and persists the routing config so brand profiles survive across sessions. Mirrors the ContentForge `cf-cowork-setup` pattern that's been battle-tested with agency users. Includes multi-team isolation via per-team folder names.
- **`fallbackModel` ready out of the box.** `settings.json.example` ships with a 3-model resilience chain (Sonnet 4.7 → Sonnet 4.6 → Haiku 4.5) using the `fallbackModel` setting from Claude Code v2.1.152 (May 27 2026). When the primary model is overloaded or a non-retryable API error fires, Claude Code transparently swaps to the next model.
- **`requiredMinimumVersion: 2.1.157` declared.** Users on older Claude Code builds get a clear upgrade message instead of silent feature gaps. Landed in Claude Code v2.1.163 (June 4 2026).
- **Model-registry freshness check in `/digital-marketing-pro:doctor`.** Wires `resolve_model.registry_age_days()` into the doctor output. Severity bands: `ok` (<60 days), `warn` (60-119), `urgent` (>=120). When stale, the doctor prints the exact `refresh_models.py` invocation. Directly addresses "what if a new model drops between releases."
- **Cowork+Drive routing status in `/digital-marketing-pro:doctor`.** Reports `urgent` when Cowork is detected but `cowork-setup` hasn't run, so users see the brand-state-vanishes-at-session-end risk before it bites.
- **`disable-model-invocation: true` on 5 true side-effect commands** (`execute-action`, `cowork-setup`, `resume`, `check`, `output-folder`). Removes their descriptions from the model's listing — saves the per-session description budget and prevents Claude from auto-running them on a hunch.
- **Fixed 3 "Read all" eager-load anti-patterns** in `growth-plan`, `client-validation-document`, `continuous-improvement-loop`. Replaced with grep-first + targeted-Read patterns that respect the per-skill 5K-token auto-compaction budget.
- **Added Context efficiency callouts** to 3 more top-heaviest skills (`seo-plan`, `content-engine`, `analytics-insights`) — now 16 of the top-16 heaviest skills have explicit context-efficiency guidance.
- **CI line-count guard** (`scripts/skill-line-check.py`) keeps every SKILL.md under the documented 500-line guideline. Current state: heaviest is `four-core-documents` at 368 lines, all 158 skills under threshold.
- **Test suite (stdlib unittest, 49 tests)** covering `resolve_model.py`, `drive-sync-state.py`, `plugin-metadata.py`, `skill-line-check.py`, `connector_resolver.py`. Drive-sync tests run against a tempdir HOME so they never touch the real `~/.claude-marketing/`. Run with `python tests/run_all.py`.

Skill count: 157 → **158** (`cowork-setup` added). 192/192 skills still pass Codex `[a-z0-9-]+` regex.

**v3.10.0 — June 2026 platform refresh (June 4)**
Six discrete updates triggered by real platform changes April–early June 2026, every claim verified against primary sources:
- **New skill `/digital-marketing-pro:gsc-ai-performance`** for the Google Search Console **AI Performance Report** rolled out 3 June 2026 (UK first, combined AI Overviews + AI Mode impressions/pages/countries/devices/dates, no click data, new in-Search-Console opt-out toggle). New `scripts/gsc-ai-performance.py` reads exported CSV; API path returns "not yet supported by Google" with a recheck date stamp.
- **New reference doc** `skills/context-engine/eu-code-of-practice.md` for the **EU Code of Practice on AI-generated content** (page dated 22 May 2026, voluntary, WG1 providers + WG2 deployers, final code targeted May–June 2026, AI Act Article 50 applicable 2 August 2026).
- **`aeo-geo` + `aeo-audit`** updated with Google's official position — no `llms.txt` needed, no AI-specific schema needed, standard Search eligibility = AI Features eligibility (AI Optimization Guide updated 15 May 2026). Plus Google-Extended directive, AI Overview → AI Mode follow-up flow, Personal Intelligence to ~200 countries / 98 languages, AI Information Agents for AI Pro/Ultra summer 2026.
- **`c2pa-metadata`** — C2PA Content Credentials 2.3 (released 9 Feb 2026: live video, plain text, OGG Vorbis, large AVI, EXIF) + C2PA Spec 2.4 `c2pa.ai-disclosure` assertion (April 2026) for Article 50 deployer compliance.
- **`paid-advertising` + `google-ads.md`** — Google Ads API **v24** (22 April 2026) breaking changes: `videos`+`logo_images` mandatory in `DemandGenVideoResponsiveAdInfo` + `VideoResponsiveAdInfo`, `Campaign.video_brand_safety_suitability` moved to Customer level, `CallAd`/`CallAdInfo` removed. v23.1 added `text_guidelines.term_exclusions` + `messaging_restrictions` for AI-generated PMax/Search assets.
- **`analytics-insights` + `attribution-report`** — GA4 added **AI Assistant** default channel group on 13 May 2026 (`Medium=ai-assistant` for ChatGPT/Gemini/Claude referral traffic).

Skill count: 153 → **154**. 191/191 skills still pass Codex `[a-z0-9-]+` regex.

**v3.9.0 — Distribution & context-efficiency polish (May 27)**
Trimmed install-UI descriptions to ~150 chars across all 5 platform manifests + 4 marketplaces (was 600–2000 chars). Rewrote READMEs pain-first. Added platform-skill GitHub topics (`cursor-plugin`, `copilot-cli-plugin`, `gemini-cli-extension`, `google-antigravity`) for cross-platform discoverability. Inserted context-efficiency callouts in the 10 heaviest skills (grep-before-read, `${CLAUDE_PLUGIN_DATA}` directory-list-before-open, offset+limit on partial reads).

**v3.8.0 — Real native manifests for 5 surfaces (May 27)**
Ships verified-real manifests for OpenAI Codex (`.codex-plugin/plugin.json` per the published OpenAI schema), Google Antigravity 2.0 (`gemini-extension.json` at repo root per Google's `gemini-cli-extensions/data-agent-kit-starter-pack` reference), Cursor 2.5+ (`.cursor-plugin/plugin.json` per the verified Cursor JSON Schema), and GitHub Copilot CLI (`.github/plugin/plugin.json`; Copilot also recognizes `.claude-plugin/plugin.json` as documented fallback). Adds `AGENTS.md` at root (auto-loaded by Codex + Antigravity + Copilot CLI + Cursor). All 157 skills share via the Agent Skills open standard — no duplication.

**v3.7.13 — Honest positioning (May 26)**
Removed the v3.6 / v3.7 era invented manifests for OpenAI Codex (`.codex-plugin/`), Cursor (`.cursor-plugin/`), GitHub Copilot CLI, and Google Antigravity 2.0 (`.antigravity/`). Research confirmed those manifests did not match the platforms' actual install specs (Antigravity uses `gemini-extension.json` at repo root; Codex schema we hand-rolled was invented). Supported surfaces are now accurately advertised as Claude Code + Cowork only. Multi-platform support is on the roadmap — research saved at `memory/`.

**v3.5.0 — May 2026 content modernisation (May 24)** — six discrete updates:
1. **Google AI Mode** added as a 6th first-class AEO/GEO surface (default conversational search since Google I/O on 19 May 2026, ~1B MAUs, Gemini 3.5 Flash backbone). AI Mode vs AI Overviews citations diverge 40–60% on the same query — audit both. `scripts/geo-tracker.py` PLATFORMS list now includes `ai-mode`.
2. **May 2026 broad core algorithm update** triage guidance — wait for rollout + 7–14 days settling before drawing conclusions; segment GSC data pre/in/post; Core Updates reweight existing signals, don't introduce new ones.
3. **EU AI Act Article 50 draft implementing guidelines** (8 May 2026; consultation closes 3 June; final guidelines July; enforcement 2 August 2026) — six-row clarification table covering "substantial AI manipulation", "matters of public interest", C2PA as presumption-of-compliance, deepfake visible disclosure, editorial-responsibility carve-out conditions, plus a five-point action list for brands with EU exposure.
4. **Meta platform updates** — Advantage+ Leads (global availability), Threads ads (global rollout, image-only), brand-safety inventory filters (Expanded/Moderate/Limited tiers with explicit reach cost).
5. **Gemini Omni + Nano Banana Pro + Veo 3.1** added to AI creative-brief skills with consistent C2PA-by-default and EU Article 50 disclosure clauses; influencer briefs ship with three explicit AI-tool clauses (permitted use, required platform disclosures, EU deepfake clause).
6. **Claude Code v2.1.149+ `/usage`** per-model breakdown integrated into `/digital-marketing-pro:agency-dashboard` for brand-attributable AI cost tracking.

See [CHANGELOG.md](CHANGELOG.md) for the full release history.

---

## How the SEO skills chain together

Most SEO work uses 3-5 skills in sequence rather than one mega-skill. The plugin is designed so that each skill produces numbered intermediate files (`01-...md`, `02-...md`, …, `PLAN.md`) under `${CLAUDE_PLUGIN_DATA}/{brand}/seo/{workflow}/{date}/` — downstream skills read those numbered files, not the endpoint, so you can re-run any single step without redoing the whole chain.

**Agency onboarding workflow** (week 1 of a new client engagement):

```
1. /digital-marketing-pro:brand-setup
2. /digital-marketing-pro:competitor-analysis        ← picks the right competitors for everything downstream
3. Run all in parallel:
   /digital-marketing-pro:tech-seo-audit             ← baseline technical health
   /digital-marketing-pro:aeo-audit                  ← baseline AI visibility
   /digital-marketing-pro:backlink-gap               ← link prospects (needs competitors from step 2)
   /digital-marketing-pro:gsc-ai-performance         ← GSC AI Performance Report (3 Jun 2026)
4. /digital-marketing-pro:keyword-cluster            ← pillar+spokes architecture from aeo-audit content gaps
5. /digital-marketing-pro:seo-plan                   ← DISPATCHER — reads all of the above, scores 4 pillars,
                                                       the weakest pillar drives the lead theme of Q1's roadmap
```

**Quarterly review workflow:**

```
1. /digital-marketing-pro:gsc-ai-performance         ← fresh GSC AI export
2. /digital-marketing-pro:seo-drift                  ← compare this quarter vs last (auto-classifies gainers,
                                                       losers, reshuffles, new keys, lost keys)
3. Branch by finding:
   - High decline → /digital-marketing-pro:seo-audit + /digital-marketing-pro:content-decay-scan
   - High reshuffle → /digital-marketing-pro:aeo-geo (intent realignment)
   - High growth → /digital-marketing-pro:content-engine (amplification briefs)
4. /digital-marketing-pro:seo-plan                   ← re-run dispatcher with fresh inputs;
                                                       lead theme may shift to a different pillar
```

**Content production workflow:**

```
1. /digital-marketing-pro:keyword-cluster            ← from your seed list
2. /digital-marketing-pro:content-brief              ← per pillar from the cluster plan
3. /digital-marketing-pro:content-engine             ← drafts with brand voice + fact-check + humanize + SEO checklist
4. /digital-marketing-pro:check                      ← pre-publish gate (hallucination + brand voice + structure)
5. /digital-marketing-pro:publish-blog               ← push to CMS
6. /digital-marketing-pro:c2pa-metadata              ← if EU markets are targeted and AI images accompany
```

**Backlink campaign workflow:**

```
1. /digital-marketing-pro:competitor-analysis
2. /digital-marketing-pro:backlink-gap               ← gap-vs-competitors with link-prospect priority scoring
3. /digital-marketing-pro:digital-pr                 ← consumes the prospect shortlist + outreach templates
4. /digital-marketing-pro:pr-pitch                   ← drafts individual pitches per prospect
```

Each skill has a **quality scorecard** that must pass before its `PLAN.md` is declared ready, and every heavy skill carries a **Tips & caveats** section with the common pitfalls. The `seo-plan` dispatcher uses **Confirm-Then-Dispatch** — it never silently re-runs expensive specialists, always asking explicitly with cost estimate before fanning out.

---

## Architecture — what's actually in the box

### 24 specialist agents
Marketing Strategist · Brand Guardian · Content Creator · Email Specialist · Social Media Manager · PR Outreach · SEO Specialist · CRO Specialist · Analytics Analyst · Marketing Scientist · Market Intelligence · Influencer Manager · CRM Manager · Growth Engineer · Journey Orchestrator · Agency Operations · Performance Monitor · Quality Assurance · Memory Manager · Execution Coordinator · Intelligence Curator · Localization Specialist · Media Buyer · Competitive Intel

Each agent has scoped responsibilities, explicit input/output contracts, and reads the Living Project Instruction File before acting.

### 158 skills
Skills are invoked by description match through the Skill tool, addressable as `/digital-marketing-pro:<skill-name>` from chat. Coverage: brand setup, content production (blog / ad / email / social / landing / video / PR / case study), SEO / AEO / GEO audits (6 platforms incl. Google AI Mode), competitor monitoring, campaign planning, channel-specific strategies, attribution, churn risk, lifecycle journeys, intelligence reports, eval framework, knowledge management, multi-brand operations, regional configuration, C2PA content provenance, **Cowork+Drive team persistence**.

### 18 top-level commands
| Command | What it does |
|---|---|
| `/digital-marketing-pro:brand-setup` | Set up a new brand profile (voice, audience, competitors, compliance) |
| `/digital-marketing-pro:engagement` | Run the full 12-Part Strategy Flow |
| `/digital-marketing-pro:campaign-plan` | Generate a multi-channel campaign plan with budget, timeline, KPIs |
| `/digital-marketing-pro:seo-audit` | Comprehensive SEO audit — technical, on-page, content, E-E-A-T, AI visibility |
| `/digital-marketing-pro:content-engine` | Draft blog, ad copy, emails, social, landing pages, video scripts |
| `/digital-marketing-pro:performance-report` | Performance report with trends, anomaly detection, recommendations |
| `/digital-marketing-pro:competitor-analysis` | Multi-dimensional competitive analysis (content, SEO, ads, social, pricing) |
| `/digital-marketing-pro:email-sequence` | Complete email sequences (subject lines, copy, timing, segmentation) |
| `/digital-marketing-pro:check` | Pre-publish quality gate (hallucination + brand voice + structure + claims) |
| `/digital-marketing-pro:status` | Unified brand snapshot (profile, engagements, insights, compliance) |
| `/digital-marketing-pro:resume` | Resume an interrupted long workflow from the last checkpoint |
| `/digital-marketing-pro:output-folder` | Print + open the visible output folder for a brand |
| `/digital-marketing-pro:doctor` | Per-action readiness diagnostic (which campaign-audit / launch-campaign actions are live vs need connector setup) |
| `/digital-marketing-pro:execute-action` | Actually fire an action against its real API (stdlib `urllib`, no third-party deps). 8 verified connectors execute end-to-end; 25 OAuth-only connectors fall back to the MCP path with the manifest still returned. |
| `/digital-marketing-pro:cowork-setup` | (v3.12.0) One-shot Cowork team setup — wires DMP through a Drive MCP so brand state survives across Cowork sessions |
| `/digital-marketing-pro:keyword-cluster` | Pillar + spokes content cluster from seed keywords with SERP-overlap clustering and 4-gate quality scorecard |
| `/digital-marketing-pro:backlink-gap` | Competitor backlink gap audit with priority scoring (DR + overlap + traffic + topical) |
| `/digital-marketing-pro:seo-drift` | Snapshot-vs-snapshot drift with auto-classification (growth/decline/reshuffle/stable/new/lost) |

Plus **140 additional skills** addressable via `/digital-marketing-pro:<skill-name>` — `:competitor-monitor`, `:churn-risk`, `:autopilot-status`, `:agency-dashboard`, `:aeo-audit`, `:geo-monitor`, `:c2pa-metadata`, `:client-onboarding`, `:journey-design` … see `/digital-marketing-pro:help` after install for the full list, or browse `skills/` in the repo.

### 86 Python scripts (optional)
Plugin works fully without Python — all marketing knowledge, frameworks, agent capabilities, and skills work out of the box via the 169 reference knowledge files.

| Mode | Size | Adds |
|---|---|---|
| **Knowledge-only** (default) | 0 MB | All 158 skills + 24 agents + 169 reference files |
| **Lite** (`pip install nltk textstat`) | ~15 MB | Brand-voice scoring, content quality scoring, readability analysis |
| **Full** (`pip install -r scripts/requirements.txt`) | ~50 MB | Competitor scraping, QR generation, AI visibility API checking, GEO tracking, C2PA signing |

### 14 HTTP MCP connectors
Notion · Slack · Canva · Figma · HubSpot · Amplitude · Ahrefs · SimilarWeb · Klaviyo · Google Calendar · Gmail · Stripe · Asana · Webflow

These are an **opt-in catalog** — the shipped `.mcp.json` is empty (`{"mcpServers":{}}`), so nothing auto-connects; enable only the ones you need. All HTTP, all Cowork-compatible. For services without first-party HTTP MCPs (Google Sheets, Drive, Salesforce, etc.), see `.mcp.json.connectors-reference` for **Pipedream / Composio / Zapier / Make.com** aggregator paths.

For the extended stdio catalog (Google Ads, Meta Ads, GA4, GSC, Brevo, etc. via npx, Claude Code only — not Cowork-compatible; verify each npm package exists before use, npx runs remote code): `cp .mcp.json.example .mcp.json`. See [CONNECTORS.md](CONNECTORS.md) and [Integrations Guide](docs/integrations-guide.md).

---

## Resumable workflows + visible output folder (v3.7.7+)

Two user-team complaints from the v3.7.5 cycle drove this release: "dm pro is taking too long to process" (the 60-minute engagement that breaks midway loses 30+ minutes of work on restart) and the general "where did my 50 deliverable files save?" confusion (everything was landing under the Windows-hidden `~/.claude-marketing/` dotfolder).

**Fix 1 — Resumable workflows.** Every long-running DMP workflow now writes per-part checkpoints to disk so an interrupted session can resume from the next un-checkpointed part instead of restarting from Part 1. Covered workflows: `engagement` (12-Part Strategy Flow), `campaign-plan`, `content-engine`, `seo-audit`, `competitor-analysis`, `campaign-audit` (v3.7.5), `launch-campaign` (v3.7.5), plus a `custom` slot for any other long flow. Resume with:

```
/digital-marketing-pro:resume                              # auto-pick latest in-progress run
/digital-marketing-pro:resume engagement                   # filter to a workflow
/digital-marketing-pro:resume engagement <run-id>          # pick a specific run
```

**Fix 2 — Visible output folder.** Every artifact a workflow produces is now copied to TWO locations: the internal tracking copy under `~/.claude-marketing/{brand}/output/{workflow}/...` (system-of-record), and a user-visible published copy under `~/Documents/DigitalMarketingPro/{brand}/{workflow}/{YYYY-MM}/{filename}` (visible in Windows Explorer / macOS Finder by default). Override the visible root with `DIGITAL_MARKETING_PRO_PUBLISH_DIR=/path` (e.g. a Dropbox share for the team). Reveal the folder any time with:

```
/digital-marketing-pro:output-folder                       # opens ~/Documents/DigitalMarketingPro/{brand}/
/digital-marketing-pro:output-folder <brand> <workflow>    # drill down
```

**Implementation:** `scripts/checkpoint-manager.py` (per-step storage + atomic writes, stdlib only) + `scripts/output-publisher.py` (dual-copy publish + `where` + `open` subcommands), mirroring the ContentForge dual-copy pattern. The engagement/checkpoint state machine ships tests in `tests/test_engagement_state.py` + `tests/test_checkpoint_roundtrip.py`; a fuller 5-scenario end-to-end simulation (clean 12-part run / interrupt-resume / parallel workflows / quality-gate fail / all-workflows-accepted) was used during development but is a dev tool, not shipped in the repo.

---

## Connector-aware action resolver (v3.7.10+)

The `campaign-audit` and `launch-campaign` skills depend on 14 actions that map to real marketing APIs (Google Ads, Meta Marketing, LinkedIn, TikTok, HubSpot, Salesforce, Klaviyo, Mailchimp, Customer.io, Gmail, Cision, Muckrack, Slack, Google Calendar, Ahrefs, Similarweb, SEMrush, Google Search Console). v3.7.5–v3.7.7 shipped these actions as honest stubs that always returned `status: stub_implementation` regardless of which connectors the user had. v3.7.10 introduces a resolver that probes the live state and resolves each action to one of three modes per call:

| mode | what it means |
|------|---------------|
| `real` | runs end-to-end with no external API (currently only `arm-watchdog` which writes a watchdog config to `~/.claude-marketing/{brand}/watchdogs/`) |
| `manifest_ready` | a matching connector is configured — the response includes the exact HTTP request manifest (method, URL, headers, body template, auth pattern) for the orchestrator (Claude via MCP) to execute. Write/launch ops set `approval_required: true`. |
| `stub_unconfigured` | no matching connector is configured — the response includes the manual fallback PLUS copy-paste `.mcp.json` snippet, env-var list, and a Cowork-compatibility note |

Check what's live in your environment any time:

```
/digital-marketing-pro:doctor                              # full readiness table
/digital-marketing-pro:doctor --summary                    # one-line counts
/digital-marketing-pro:doctor --action inventory --channel google_ads  # drill in
```

**Test coverage:** the resolver's action layer ships tests in `tests/test_connector_resolver.py`. A fuller 27-scenario development harness (14 actions × unconfigured / configured / local-execution variants) was used while building this out, but it is a dev tool and is not shipped in the repo.

**Implementation:** `scripts/_connector_registry.py` (catalog of 33 connectors, 11 categories, `is_connector_configured()` probe) + `scripts/connector_resolver.py` (`ACTION_SPECS` map + per-action manifest builders + local executors) + `scripts/action-doctor.py` (the doctor command's underlying script).

### v3.7.11 — actions can actually fire HTTP requests from Python

The v3.7.10 resolver returned a manifest of "what would be sent." v3.7.11 adds `scripts/connector_executor.py` (stdlib `urllib.request`, no third-party deps) that takes that manifest and **actually executes** the request against the real API. Public CLI: `/digital-marketing-pro:execute-action`.

**Executes end-to-end from Python (8 connectors, verified vendor docs):**

| Connector | Env var | What it can fire |
|-----------|---------|---|
| Slack | `SLACK_BOT_TOKEN` | `POST chat.postMessage` (with `body.ok` post-check) |
| HubSpot | `HUBSPOT_PRIVATE_APP_TOKEN` | `GET /automation/v4/flows`, `POST /marketing/v3/campaigns` |
| Klaviyo | `KLAVIYO_PRIVATE_KEY` | `GET /api/flows`, `PATCH /api/flows/{id}` (vnd.api+json) |
| SendGrid | `SENDGRID_API_KEY` | `POST /v3/mail/send` (202 success) |
| Brevo | `BREVO_API_KEY` | `POST /v3/smtp/email` (lowercase `api-key:` header) |
| Customer.io | `CUSTOMERIO_APP_API_KEY` | `POST /v1/send/email` (App API key only) |
| Mailchimp | `MAILCHIMP_API_KEY` | `GET /3.0/automations` (Basic auth, dc from suffix) |
| Ahrefs | `AHREFS_API_KEY` | `GET /v3/site-explorer/metrics` |

**Requires the MCP path (25 OAuth-only connectors):** Google Ads, Meta Marketing, LinkedIn Marketing, LinkedIn Publishing, TikTok Ads, Twitter/X, Gmail, Google Calendar, Google Analytics, Google Search Console, Meta Graph, Salesforce, Pipedrive, Zoho CRM, Buffer, Hootsuite, Cision, Muckrack, Amplitude, Similarweb, SEMrush, Moz, Intercom, Canva, Figma. For all of these, the resolver still returns `manifest_ready` so you can see the exact HTTP shape Claude's MCP tool will send — Python just can't execute the OAuth flow itself.

**Safety gates:** read ops auto-execute with `--execute`; write ops require both `--execute --confirm`; missing env vars block with `setup_hint_credential`; unresolved `{VAR}` placeholders block before the request fires. Every fired call logs to `~/.claude-marketing/{brand}/executions/`.

**Test coverage:** end-to-end HTTP send-and-receive for the 8 connectors (Slack `body.ok` post-check, Klaviyo vnd.api+json, Brevo lowercase header, Mailchimp Basic, plus the safety gates and data substitution) was validated during development against a stdlib `http.server` mock. That mock harness is a dev tool and is not shipped in the repo; the shipped suite covers the resolver layer via `tests/test_connector_resolver.py`.

---

## Model curator — no hardcoded model ids (v3.7.4+)

Frontier models change every ~6 weeks. Hardcoding `claude-sonnet-4-5-20250929` or `gemini-2.0-flash` across dozens of scripts means a provider deprecation silently 404s, the user blames the plugin, and the maintainer has to grep three repos. So we don't hardcode.

- **`scripts/model_registry.json`** — single source of truth for every model id used by the plugin, with vendor, tier, modality, status, and `replacement_id` for deprecated entries.
- **`scripts/resolve_model.py`** — Python module + CLI. Resolves human aliases (`latest-balanced-anthropic`, `latest-fast-anthropic`, `latest-text-openai`, `latest-vision-google`, `latest-image-google`, `latest-video-google`) to concrete ids at call time. Deprecated ids passed via `--model` auto-fall-forward to their replacement (with a stderr warning).
- **`scripts/refresh_models.py`** — polls Anthropic / OpenAI / Google / Evolink list endpoints with your API keys and reports drift versus the registry (NEW models in the provider catalog, STALE models in the registry).

Every script that calls a provider model now accepts `--model` (or `--openai-model` / `--anthropic-model` for `scripts/ai-visibility-checker.py`) and the value is validated against the registry. See [`docs/MODEL-CURATOR.md`](docs/MODEL-CURATOR.md) for the full alias map, curation policy, and worked examples.

```bash
python scripts/resolve_model.py --alias latest-balanced-anthropic    # -> claude-sonnet-4-6
python scripts/resolve_model.py --check gemini-2.0-flash              # -> deprecated (use gemini-3.5-flash)
python scripts/resolve_model.py --list --vendor anthropic --status current
python scripts/refresh_models.py                                      # drift report (needs API keys)
```

---

## Compliance — 16 jurisdictions, EU AI Act Article 50 ready

DM Pro carries jurisdiction-specific compliance rules that auto-apply when a brand declares its target markets. Coverage:

🇪🇺 EU (GDPR + AI Act Article 50) · 🇺🇸 US Federal (CAN-SPAM) · 🇺🇸 California (CCPA/CPRA) · US 20+ state privacy laws · 🇨🇦 Canada (CASL + PIPEDA) · 🇧🇷 Brazil (LGPD) · 🇬🇧 UK (UK GDPR + PECR) · 🇦🇺 Australia (Privacy Act + Spam Act) · 🇸🇬 Singapore (PDPA) · 🇨🇳 China (PIPL) · 🇮🇳 India (DPDPA) · 🇯🇵 Japan (APPI) · 🇰🇷 South Korea (PIPA) · 🇸🇦 Saudi Arabia (PDPL) · 🇦🇪 UAE (Federal Decree-Law No. 45) · 🇹🇭 Thailand (PDPA)

**EU AI Act Article 50 readiness (applicable 2 August 2026):**
- C2PA content-provenance signing via `/digital-marketing-pro:c2pa-metadata` (end-to-end tested against c2pa-python 0.32 — 75-byte test PNG → 42,818-byte signed PNG with `manifest_embedded_and_verified=true`)
- Pre-publish gate (`/digital-marketing-pro:check`) treats missing C2PA on AI-flagged assets in EU campaigns as CRITICAL → BLOCKED
- Draft implementing guidelines (8 May 2026) added as `compliance-rules.md` §1.1b.i with six-row clarification table + five-point action list
- Production cert guide at `docs/c2pa-production-cert-guide.md` covers the four CAI-recognised authorities (Adobe Content Credentials, Truepic, Numbers Protocol, Microsoft Azure Confidential Ledger)

**Other May 2026 regulatory updates baked in:**
- NY synthetic-performer disclosure law (live June 2026, $1K–$5K per violation, $10K repeat) — applies to synthetic influencers + AI endorsements
- FTC May 2026 endorsement guidance — synthetic influencers, AI testimonials, AI-edited creator content
- CJEU March 2026 ruling — pseudonymized cookie IDs are personal data when re-identification is feasible
- CCPA Jan 2026 ADMT amendments + AI-derived sensitive data classification
- DPDP Phase II preparation — consent manager registration opens Nov 2026

---

## AEO / GEO — May 2026 reality

The search landscape pivoted hard in 2025–2026:
- Google AI Overviews appear on ~55% of all Google searches (Seer Interactive, Sept 2025); organic CTR on AI Overview queries dropped ~61% (1.76% → 0.61%); ~58% of Google searches are now zero-click
- **Google AI Mode** became the default conversational search experience for opted-in users at I/O 2026 (19 May 2026), backed by Gemini 3.5 Flash — ~1B MAUs
- ChatGPT search reaches ~883M MAU; Perplexity heavily skews citations to Reddit (47% of factual cites); Wikipedia drives 48% of ChatGPT citations

DM Pro's AEO/GEO skills (`/digital-marketing-pro:aeo-audit`, `:geo-monitor`, `:entity-audit`) reflect this:
- **6-platform audit standard** — ChatGPT, Perplexity, Google AI Mode, Google AI Overviews, Gemini, Microsoft Copilot (was 5 — AI Mode added May 2026)
- Schema strategy refresh — Google's March 2026 core update demoted FAQ/Review/HowTo schema on non-primary pages. Skills emphasise entity-rich JSON-LD (Article + Organization + Person + Product) and produce an **LLMs.txt** companion file
- Citation tracking across all 6 surfaces, with Profound / Otterly / Conductor AgentStack integration paths in the connectors layer
- **Share of AI Voice** as a first-class metric in `/digital-marketing-pro:performance-report`

---

## Channel guidance — May 2026 updates baked in

- **LinkedIn (March 2026 algorithm shift):** external links and engagement bait penalized ~60%. New **Depth Score** measures dwell time. Followers no longer guarantee reach. Skills optimize for relevance and Depth Score.
- **Email:** Apple MPP affects ~64% of B2C opens — open rate is functionally dead as a primary KPI. **DMARC + RFC 8058 one-click POST unsubscribe** mandatory; non-compliant bulk mail to Gmail/Yahoo/Microsoft gets permanent 550 rejections. Spam threshold tightened to <0.10%.
- **TikTok (post Jan 22 2026 USDS Joint Venture closing):** US data + algorithm under USDS LLC; ByteDance retains <20%. AI-generated creators require disclosure label; AI content excluded from Creator Rewards Program; daily shoppable-post limits effective May 11 2026.
- **Meta Advantage+ Leads** (global as of May 2026), **Threads ads** (global, image-only), **brand-safety inventory tiers** (Expanded/Moderate/Limited — Limited costs ~30% reach).
- **WhatsApp** per-message pricing (since 1 July 2025) — India marketing template ≈ USD 0.0118 per message; 72-hour free service window from CTWA ads or Page CTAs.
- **Third-party cookies — deprecation cancelled.** First-party data is the strategic priority. The `attribution-model` skill defaults to first-party + MMM + incrementality stack.
- **Sora dependency note:** OpenAI consumer Sora app discontinued April 26 2026; Sora API September 24 2026. AI creative briefs default to **Veo 3.1, Kling v3.0 Pro, Runway Gen-4, Gemini Omni**.

---

## Documentation

| Guide | Description |
|---|---|
| [Getting Started](docs/getting-started.md) | Installation, first brand setup, first marketing task — with worked examples |
| [Brand Guidelines](docs/brand-guidelines.md) | Importing voice guides, restrictions, channel styles, templates, agency SOPs |
| [Multi-Brand & Agency Guide](docs/multi-brand-guide.md) | Multi-brand corporations and agency multi-client workflows |
| [Strategy & KPI Mapping](docs/strategy-and-kpis.md) | Business objectives → KPI frameworks → campaign strategy → measurement loop |
| [Integrations Guide](docs/integrations-guide.md) | MCP setup for GA4, HubSpot, Google Ads, Meta, and more |
| [Engagement Methodology](docs/engagement-methodology.md) | Deep-dive on the 12-Part Strategy Flow |
| [Competitor Intelligence](docs/competitor-intelligence.md) | Setting up competitors, running analysis, responding to competitive moves |
| [Claude Interfaces](docs/claude-interfaces.md) | What works in Claude Code, Cowork, Desktop, claude.ai |
| [C2PA Production Cert Guide](docs/c2pa-production-cert-guide.md) | Acquiring a CAI-recognised signing certificate for EU production deployment |
| [Architecture](docs/architecture.md) | Technical deep-dive for contributors and power users |
| [Testing Guide](TESTING-GUIDE.md) | Per-phase test checklist for plugin contributors |

Two PDF references at the repo root: `DM_Strategy_Complete_Learning_Guide.pdf` (full methodology) and `DM_Strategy_Flow_v3_2_Visualization_v1_23Apr26.pdf` (one-page visual map).

---

## FAQ

**Q: How does this compare to LangChain marketing templates / CrewAI marketing crews / general AI marketing tools?**
Those are frameworks. DM Pro is a **packaged, opinionated methodology** with explicit dependency rules between every output. You can build something like it in LangChain or CrewAI — at the cost of months of engineering. DM Pro ships it.

**Q: Which Claude interface should I use?**

| | Claude Code | Claude Cowork | Claude Desktop (no Cowork) | claude.ai web |
|-|:-:|:-:|:-:|:-:|
| Full plugin support | yes | yes | partial | no |
| Brand memory | yes | yes | no | no |
| MCP integrations | all | HTTP only | HTTP only | no |
| Document creation (Excel, PPT) | no | yes | no | no |
| Recommended for | Terminal workflows + scripting | Visual desktop workflows | Quick content | One-off questions |

**Q: How much does a full engagement cost in API spend?**
Roughly **$15–40** for a complete 12-part engagement using Opus 4.8 across ~50–60 documents. Track per-brand consumption via Claude Code v2.1.149+ `/usage` (now integrated into `/digital-marketing-pro:agency-dashboard`).

**Q: Can I run multiple brands in parallel?**
Yes. Each brand has its own `~/.claude-marketing/<brand-slug>/` directory and Python script state. Switch with `/digital-marketing-pro:switch-brand`.

**Q: What if I only want a campaign plan, not the full methodology?**
Skip to `/digital-marketing-pro:campaign-plan`. Every individual surface (campaign / SEO / content / competitor / email / report) is independently runnable. The full engagement is the canonical path, not the only path.

**Q: Will this work on Codex / Cursor / Copilot CLI / Antigravity?**
Yes — verified-real native manifests ship for all 8 surfaces (CC, Cowork, Codex, Cursor, Copilot CLI, Antigravity, Hermes Agent, OpenClaw). See [Supported surfaces](#supported-surfaces-v3151) above for per-platform install commands.

**Q: I run my team on Anthropic Cowork. Does brand state persist between sessions?**
Yes — but you need to run `/digital-marketing-pro:cowork-setup` once per team first (v3.12.0). Cowork's per-session filesystem is ephemeral, and `${CLAUDE_PLUGIN_DATA}` is too ([open issue #51398](https://github.com/anthropics/claude-code/issues/51398)). The setup wizard routes brand profiles + plans + reports through a Google Drive MCP so everything survives across sessions and is shared across the team. Multi-team isolation via per-team folder names.

**Q: What happens when a new Claude / OpenAI / Google model ships? Do I need to update the plugin?**
No — the plugin uses a shared model curator (`scripts/resolve_model.py`) that resolves aliases (`latest-balanced-anthropic`, `latest-text-google`, etc.) at call time. When a model is deprecated, the curator auto-falls-forward to the replacement. `/digital-marketing-pro:doctor` reports registry age and severity (`ok` <60d / `warn` 60-119d / `urgent` ≥120d); when stale it prints the exact `python scripts/refresh_models.py` invocation to poll the provider APIs for drift. Plus `settings.json.example` ships a `fallbackModel` chain so Claude Code transparently swaps models on overload.

**Q: Is this an Anthropic product?**
No — independent open-source plugin built by [Indranil Banerjee](https://indranil.in). MIT-licensed. Runs on Claude Code + Cowork.

**Q: I found a compliance rule that looks out of date.**
[File an issue](https://github.com/indranilbanerjee/digital-marketing-pro/issues) with the citation. Privacy and AI law change quarterly — DM Pro is actively maintained against the May 2026 reality but enforcement actions and amendments keep coming.

---

## Troubleshooting

Common install + first-run issues across all 8 supported platforms, with the fix.

### Claude Code + Cowork

**"/plugin isn't available in this environment"**
You're in the standard Claude chat app (browser `claude.ai` or the Claude Desktop app). The `/plugin` slash command only works in **Claude Code** (the dev CLI/IDE at [claude.com/code](https://claude.com/code)) and **Anthropic Cowork**. Everywhere else, plugins install via the UI: click the **Plugins** button at the bottom of the chat. See [Updating](#updating) for the full recovery procedure.

**"Plugin installed but slash commands not showing"**
Run `/reload-plugins` (Claude Code) or restart the Cowork chat session. If still missing, the installed version may be older than v2.1.157 — your Claude Code build needs to be on **v2.1.157 or newer** (DMP declares `requiredMinimumVersion: 2.1.157` in plugin.json). Run `claude --version` and update via `npm install -g @anthropic-ai/claude-code`.

**"Brand profile vanishes between Cowork sessions"**
Cowork's filesystem is per-session ephemeral — `~/.claude-marketing/` AND `${CLAUDE_PLUGIN_DATA}` both reset at session end ([open issue #51398](https://github.com/anthropics/claude-code/issues/51398)). Fix: run `/digital-marketing-pro:cowork-setup` once per team — it routes brand state through a Google Drive MCP so profiles survive across sessions and your whole team sees them. See [v3.12.0 release notes](#whats-new) for the why-and-how.

**"`/digital-marketing-pro:doctor` says urgent (model registry stale)"**
The model registry hasn't been refreshed for 60+ days — frontier models shift every ~6 weeks so deprecated IDs may start 404-ing. Fix: `ANTHROPIC_API_KEY=... OPENAI_API_KEY=... GEMINI_API_KEY=... EVOLINK_API_KEY=... python scripts/refresh_models.py`. The script polls each provider's `/v1/models` endpoint and reports drift versus our registry.

### OpenAI Codex / Cursor / GitHub Copilot CLI / Antigravity

**"Skills install but commands not discovered"**
These platforms read SKILL.md by description match — invoke via natural language (*"Run a competitor analysis on stripe.com"*) rather than typing a slash command. Slash commands (`/digital-marketing-pro:<name>`) are a Claude Code convention; on other surfaces the agent picks up the skill from intent.

**"Codex says skill name failed regex check"**
Codex enforces `[a-z0-9-]+` on skill names. All 158 DMP skill names pass this regex (verified in the test suite). If you see this error, it's likely a personal skill you added — rename it to lowercase + hyphens only.

**"Cursor `/add-plugin` returns 'plugin not found'"**
Use the full Git URL form: `/add-plugin digital-marketing-pro@https://github.com/indranilbanerjee/digital-marketing-pro`. Cursor's marketplace integration is fastest, but the Git URL form always works.

### Hermes Agent

**"`hermes plugins install ...` finishes but no skills appear"**
The plugin needs to be enabled after install: `hermes plugins enable digital-marketing-pro`. Then verify with `hermes plugins list`. If the adapter's `register()` returned silently with no skills, run the audit: `cd ~/.hermes/plugins/digital-marketing-pro && python __init__.py` — it'll print the discovered skill count + first 5 skills, confirming the clone got the full `skills/` tree.

**"register_skill error in Hermes logs"**
Check Hermes version: this plugin targets **v0.15.2+**. Run `hermes --version`. Older builds may have a different `ctx` API surface — the adapter degrades gracefully (logs an error, doesn't crash) but won't register skills. Upgrade Hermes to the latest public preview.

### OpenClaw

**"OpenClaw can't find the plugin manifest"**
Use the `git:` install scheme: `openclaw plugins install git:github.com/indranilbanerjee/digital-marketing-pro`. If you used another scheme and it failed, the fallback is: `cd ~/.openclaw/plugins && git clone https://github.com/indranilbanerjee/digital-marketing-pro && openclaw plugins enable digital-marketing-pro`.

**"OpenClaw uses Claude bundle but loses some features"**
OpenClaw auto-detects our `.claude-plugin/plugin.json` as a Claude-compatible bundle, but the native `openclaw.plugin.json` gives first-class discoverability. Both load the same 158 skills from `./skills`. Verify with `openclaw plugins inspect digital-marketing-pro --runtime --json`.

### General (any platform)

**"Tests in `tests/` fail when I `git clone` locally"**
Run `python tests/run_all.py` from the repo root. All 207 tests are stdlib-only — no `pip install` needed. If they fail, the most likely cause is a Python version mismatch (DMP supports Python 3.8+) or a clone that omitted some `skills/` subdirectories. Try `git clone --depth=1` again.

**"`/digital-marketing-pro:doctor` shows my action as stub_unconfigured"**
That action needs an MCP connector configured. Run `python scripts/connector-status.py --action setup-guide --name <connector-name>` for the exact setup snippet. Add it to your `.mcp.json` under `mcpServers`, restart your agent, and the action becomes `manifest_ready`. See [Connector-aware action resolver](#connector-aware-action-resolver-v3710) for the full readiness model.

**"Where do my brand files actually go?"**
Run `/digital-marketing-pro:output-folder` — it prints the active output directory and (on local Claude Code) opens it in your OS file manager. Default: `~/.claude-marketing/<brand-slug>/` for working state + `~/Documents/DigitalMarketingPro/<brand>/` for finished deliverables. Both configurable via `output-folder`.

**Still stuck?** [Open an issue](https://github.com/indranilbanerjee/digital-marketing-pro/issues) with the exact error message + platform name + version. We respond within a few days.

---

## Updating

> **If you see "/plugin isn't available in this environment"** — you're in the standard **Claude chat app** (browser OR installed desktop app). The `/plugin` slash command is **only** supported in two environments: **Claude Code** (the developer CLI / IDE at [claude.com/code](https://claude.com/code), `npm install -g @anthropic-ai/claude-code`) and **Anthropic Cowork**. Everywhere else — `claude.ai` web chat, the Claude Desktop app, mobile — plugins are managed through the UI, not slash commands.
>
> The plugin IS installed (your DM Pro skills work); only the management command is unavailable. Fix:
>
> 1. **In the chat UI** — click the **Plugins** button at the bottom of the chat → **Manage plugins** → find Digital Marketing Pro → look for Update / Refresh / Remove. If no Update button, **Remove** then **Add plugin** → re-install from `indranilbanerjee/neels-plugins`. The re-pull fetches the latest version.
> 2. **For slash-command management** — switch to Claude Code (CLI or IDE) or Cowork. The plugin runs identically across every Anthropic surface; you're choosing where to type management commands.
>
> Once you're in Claude Code or Cowork, the rest of this section applies.

```
/plugin marketplace update neels-plugins
/plugin uninstall digital-marketing-pro@neels-plugins
/plugin install digital-marketing-pro@neels-plugins
/reload-plugins
```

`/plugin marketplace update` only refreshes the catalog — the uninstall + reinstall is what actually pulls the new version. `/reload-plugins` applies the change without restart.

If a version stays the same but content changed (fast-iteration debugging):
```
rm -rf ~/.claude/plugins/cache/neels-plugins
/plugin install digital-marketing-pro@neels-plugins
/reload-plugins
```

---

## Neelverse Marketing Suite

DM Pro is part of a three-plugin suite by [Indranil Banerjee](https://indranil.in) — share the same brand profiles, install together, designed to chain:

| Plugin | What it does |
|---|---|
| **Digital Marketing Pro** (this plugin) | End-to-end engagement methodology — 12-Part Flow, Four Core Documents, Two-Views Model |
| [ContentForge](https://github.com/indranilbanerjee/contentforge) | Publication-ready content via 10-phase pipeline, fact-checker, 35-pattern AI-detection humanizer, .docx export with C2PA signing |
| [SocialForge](https://github.com/indranilbanerjee/socialforge) | Social media calendar with AI image (Vertex AI Nano Banana Pro) + video (WaveSpeed Kling v3.0 Pro) generation, C2PA signing |

```
/plugin marketplace add indranilbanerjee/neels-plugins
/plugin install digital-marketing-pro@neels-plugins
/plugin install contentforge@neels-plugins
/plugin install socialforge@neels-plugins
```

---

## Star history

[![Star History Chart](https://api.star-history.com/svg?repos=indranilbanerjee/digital-marketing-pro&type=Date)](https://star-history.com/#indranilbanerjee/digital-marketing-pro&Date)

If DM Pro saves your team time, [⭐ star the repo](https://github.com/indranilbanerjee/digital-marketing-pro/stargazers) — it's the single most useful thing you can do to help other marketing teams discover it.

---

## About the maintainer

DM Pro is built and maintained by **[Indranil Banerjee](https://indranil.in)** — a digital marketing practitioner shipping engagement methodology as code. The 12-Part Strategy Flow comes from real client engagements across consumer DTC, B2B SaaS, regulated industries (health, finance), and agency multi-brand portfolios.

- 🌐 **Website:** [indranil.in](https://indranil.in)
- 💼 **LinkedIn:** [linkedin.com/in/askneelnow](https://www.linkedin.com/in/askneelnow)
- 🐦 **X / Twitter:** [@askneelnow](https://x.com/askneelnow)
- 💻 **GitHub:** [@indranilbanerjee](https://github.com/indranilbanerjee)
- 📦 **Other plugins:** [ContentForge](https://github.com/indranilbanerjee/contentforge) · [SocialForge](https://github.com/indranilbanerjee/socialforge)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/indranilbanerjee/digital-marketing-pro/discussions)
- 🐛 **Bug reports:** [GitHub Issues](https://github.com/indranilbanerjee/digital-marketing-pro/issues)

**Why this plugin exists:** Most AI marketing tools generate isolated outputs that don't compose. The 12-Part Strategy Flow encodes the canonical sequence a real engagement actually needs — Stone-vs-Opinion intake, Four Core Documents, Client Validation, Two-Views Model, Decision Matrix, Growth Plan + Yearly Planner, channel fan-out, execution artefacts, creative briefs, continuous improvement loop. Once it's a plugin, every engagement looks the same, handoffs work, and quality is auditable. That's the whole product.

If DM Pro saves your team time, [⭐ star the repo](https://github.com/indranilbanerjee/digital-marketing-pro/stargazers) — it's the single most useful thing you can do to help other marketing teams discover it. Sharing on **LinkedIn** ([linkedin.com/in/askneelnow](https://www.linkedin.com/in/askneelnow)) or **X** ([@askneelnow](https://x.com/askneelnow)) helps too — tag me, I'll re-share.

---

## Contributing

PRs welcome — especially on compliance rules (privacy and AI law change fast), industry profiles, and channel-specific updates. See [CONTRIBUTING.md](CONTRIBUTING.md) for the contribution workflow, [`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md) for the PR checklist, and [TESTING-GUIDE.md](TESTING-GUIDE.md) for per-phase test checklists. All contributors are expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md). Security issues: please use [Private Security Advisories](https://github.com/indranilbanerjee/digital-marketing-pro/security/advisories/new) per [SECURITY.md](SECURITY.md) — do not file public issues for vulnerabilities.

---

## License

MIT — see [LICENSE](LICENSE). Free to use commercially.

---

## Release notes

**v3.8.0 (2026-05-27)** — Real native manifests for 5 surfaces. Ships verified-real `.codex-plugin/plugin.json` (per the published OpenAI schema), `gemini-extension.json` (at repo root, per Google's `gemini-cli-extensions/data-agent-kit-starter-pack` reference pattern), `.cursor-plugin/plugin.json` (per the verified Cursor 2.5+ JSON Schema), and `.github/plugin/plugin.json` (verified GitHub Copilot CLI schema; Copilot also recognizes `.claude-plugin/plugin.json` as documented fallback). Adds `AGENTS.md` at root (auto-loaded by Codex + Antigravity + Copilot + Cursor agent context chains). All 157 skills share via the Agent Skills open standard — no skill duplication. Replaces the v3.6/v3.7 era invented manifests correctly removed in v3.7.13. Pre-flight verified: 190/190 skills pass the Codex `[a-z0-9-]` regex AND the SKILL.md frontmatter `name` field matches each folder.

**v3.7.13 (2026-05-26)** — Honest positioning. Removed v3.6 / v3.7 era invented manifests (`.codex-plugin/`, `.cursor-plugin/`, `.antigravity/`) + `docs/cross-platform-install.md`. Research confirmed they did not match the platforms' actual install specs. Zero functional changes; the plugin behaved identically in Claude Code + Cowork.

**v3.7.1 (2026-05-24)** — Polish + discoverability pass. README rewritten for organic GitHub/AI-engine discoverability with social-proof badges, install matrix at the top, outcome-focused "What you get in 60 minutes" section, AEO/GEO/compliance keyword density, maintainer block with [indranil.in](https://indranil.in), and ⭐ CTAs. Stale asset counts swept across multiple docs. plugin.json description corrected to 69 scripts (was 71). No functional changes; no breaking changes.

**v3.5.0 (2026-05-24)** — May-2026-ecosystem modernisation pass. Six discrete updates: (1) Google AI Mode as 6th AEO/GEO surface; (2) May 2026 broad core algorithm update triage; (3) EU AI Act Article 50 draft implementing guidelines (8 May; 3 June consultation; 2 Aug enforcement); (4) Meta Advantage+ Leads global + Threads ads + brand-safety filters; (5) Gemini Omni + Nano Banana Pro + Veo 3.1 in creative briefs; (6) Claude Code v2.1.149+ `/usage` per-brand cost tracking in agency dashboard.

**v3.4.1 (2026-05-17)** — Audit & corrections pass on v3.4.0. C2PA script rewritten against the real c2pa-python 0.32 API (Builder + Signer.from_info), end-to-end tested. Unified ads MCP entries corrected. Parallel-dispatch speedup claim softened from flat 6× to honest 4–6× parallelism / ~50–80% wall-clock reduction.

**v3.4.0 (2026-05-16)** — C2PA content-provenance for EU AI Act Article 50 compliance (`scripts/embed-c2pa.py`, `/digital-marketing-pro:c2pa-metadata`, pre-publish gate integration). Unified ads-platform MCPs added. Explicit parallel subagent dispatch in `engagement-workflow` + 4 multi-dimensional commands. Anthropic Software Directory submission packet at `SUBMISSION.md`.

**v3.3.0 (2026-05-15)** — May 2026 modernization sweep. Privacy & compliance updates (EU AI Act, DPDP Phase II, NY synthetic-performer law, FTC May 2026 endorsement guidance, CCPA ADMT, CJEU pseudonymized-cookie ruling). Channel guidance updates (LinkedIn algorithm shift, email DMARC + RFC 8058, TikTok USDS, WhatsApp per-message pricing, schema refresh + LLMs.txt, Sora deprecation). AEO/GEO modernization.

**v3.2.x (May 2026)** — `/dm:` → `/digital-marketing-pro:` namespace sweep (~600 references); manifest install format fix; hook-removal gap closure (`/check`, `/status`, embedded hallucination checks, opt-in `auto_save_insights`).

**v3.1.0 (May 2026)** — Removed all global hooks. Prior `SessionStart` and `PreToolUse mcp_.*` matchers were firing across every project regardless of context. Hook config preserved as reference at `hooks/hooks-reference.example.json`.

**v3.0.0 (April 2026)** — 12-Part Engagement Methodology. Four Core Documents (61 explicit steps). Two-Views Model. Decision Matrix. Update-Back Rule. Living Project Instruction File.

**Earlier versions:** see [CHANGELOG.md](CHANGELOG.md) for v2.7 and earlier.

---

<sub>Made with care by [Indranil Banerjee](https://indranil.in) · Powered by Anthropic Claude · MIT-licensed · [⭐ Star the repo](https://github.com/indranilbanerjee/digital-marketing-pro) if it helps you</sub>
