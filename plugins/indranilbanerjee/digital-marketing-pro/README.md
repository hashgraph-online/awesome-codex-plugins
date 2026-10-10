# Digital Marketing Pro

> **Your agency just signed a 50-brand client. The previous agency left no playbook. Three brands are bleeding budget, two have stale positioning, one is launching in a regulated jurisdiction next month. Where do you start?**

Run `/digital-marketing-pro:engagement` against each brand. Same 12-Part Strategy Flow, same Four Core Documents, same 61-step structure — auditable across the entire portfolio in ~60 minutes per brand on Claude Opus-class models (measured on Opus 4.8; re-measure on today's Opus-class models before quoting a time). No more inconsistent depth between brands. No more "what did the last agency do?" mysteries. No more compliance gaps in regulated jurisdictions.

Open-source AI marketing plugin — **164 skills, 24 specialist agents, EU AI Act Article 50 ready, Cowork team-persistent**. Built for marketing agencies, in-house teams running 50–200 brands, and consultancies. Installs on **Claude Code** (CLI + IDE), **Anthropic Cowork**, **OpenAI Codex**, **Cursor 2.5+**, **GitHub Copilot CLI**, **Google Antigravity 2.0**, **Hermes Agent**, **OpenClaw**, and **Grok** + 35+ Agent Skills platforms. Created by [Indranil Banerjee](https://indranil.in) · [LinkedIn](https://www.linkedin.com/in/askneelnow/) · [X](https://x.com/askneelnow).

[![Version](https://img.shields.io/badge/version-3.35.2-blue.svg)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/indranilbanerjee/digital-marketing-pro?style=flat&logo=github&color=yellow)](https://github.com/indranilbanerjee/digital-marketing-pro/stargazers)
[![Forks](https://img.shields.io/github/forks/indranilbanerjee/digital-marketing-pro?style=flat&logo=github&color=blue)](https://github.com/indranilbanerjee/digital-marketing-pro/network/members)
[![Issues](https://img.shields.io/github/issues/indranilbanerjee/digital-marketing-pro?logo=github)](https://github.com/indranilbanerjee/digital-marketing-pro/issues)
[![Last commit](https://img.shields.io/github/last-commit/indranilbanerjee/digital-marketing-pro?logo=github)](https://github.com/indranilbanerjee/digital-marketing-pro/commits/main)
[![Tests](https://img.shields.io/badge/tests-613%2F613%20passing-brightgreen.svg)](tests/)
[![Platforms](https://img.shields.io/badge/platforms-9%20native%20%2B%2035%20Agent%20Skills-success.svg)](#works-on-40-agent-harnesses-via-the-agent-skills-open-standard)
[![Cowork](https://img.shields.io/badge/cowork-team%20persistent-purple.svg)](#supported-surfaces-v3352)
[![EU AI Act](https://img.shields.io/badge/EU%20AI%20Act-Article%2050%20ready-darkred.svg)](skills/context-engine/compliance-rules.md)
[![Sponsor](https://img.shields.io/badge/sponsor-%E2%9D%A4-ea4aaa?logo=githubsponsors&logoColor=white)](https://github.com/sponsors/indranilbanerjee)
[![HOL Guard](https://img.shields.io/endpoint?url=https%3A%2F%2Fhol.org%2Fapi%2Fregistry%2Fbadges%2Fplugin%3Fslug%3Dindranil-banerjee%252Fdigital-marketing-pro%26metric%3Dtrust)](https://hol.org/go/guard/indranilbanerjee21?dest=%2Fguard%2Fbilling%3Fpromo%3DGUARD20-INDRANILBANERJEE21%23upgrade&link_id=fc4b1025-e6eb-40bd-b3d7-24a8508c2fd9&utm_source=insights_share&utm_medium=affiliate_cta&utm_campaign=share20)

> 🆕 **Just shipped — v3.35.2 (October 10, 2026): every missing-package message prints the exact pinned command, and the README says what the code does.** One table pins every optional package; requirements.txt lists the same exact versions, `setup.py --install` installs from it, and every script that needs a missing package prints the tested `pip install` command (before, only C2PA did). A claim check also fixed five README passages the code contradicted: the automation examples, the OAuth connector count (28), the output-folder tree, the check row and the live-write comparison. [Read what's new →](#whats-new) · [Full changelog →](CHANGELOG.md)
>
> <sub>Previously — **v3.35.0 and v3.35.1 (October 10, 2026):** a write the plugin sends itself fires only against a single-use approval record for that exact request, created after you type `yes` (what that proves is stated plainly, and MCP-tool writes are named as outside the check); autopilot proposes by default; no script installs packages on its own; model-supplied names cannot reach files outside the plugin's folders; fetchers refuse private addresses on every redirect; C2PA signing works on the current c2pa-python. [Full changelog →](CHANGELOG.md)</sub>

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
| 🚀 **Marketing automation builder** (n8n · Zapier · Make · Pipedream · custom) | `/digital-marketing-pro:doctor` to see what's wired, `:execute-action` to fire real API calls | 8 verified HTTP connectors executing end-to-end (Slack · HubSpot · Klaviyo · SendGrid · Brevo · Customer.io · Mailchimp · Ahrefs); 28 OAuth connectors via MCP manifest. Stdlib only, no third-party deps. |
| 💼 **Solo consultant** or freelance marketer | `/digital-marketing-pro:engagement` per client | 50–60 canonical files per client engagement in ~60 minutes for $15–40 of API spend. Same depth on every project. Installs on Codex / Cursor / Copilot CLI / Antigravity if you don't live in Claude. |
| 📈 **Growth team** / product marketer | `:funnel-architect` → `:analytics-insights` → `:attribution-model` → `:churn-risk` → `:cohort-analysis` | Journey design + measurement + retention + churn — all aligned to the strategy document, not isolated outputs. MMM + incrementality testing baked in. |
| 🛡 **Compliance-led marketer** (EU · UK · India · Brazil · California) | `/digital-marketing-pro:check` before publishing anything | C2PA content provenance, EU AI Act Article 50 disclosure, GDPR + CCPA + DPDPA + LGPD across 16 jurisdictions, deepfake disclosure clauses on every AI creative brief. |

---

## How does this compare?

| | **Digital Marketing Pro** | Anthropic Marketing (official) | Composio Marketing | claude-seo (community) |
|---|---|---|---|---|
| Skills count | **164** | ~7 | ~12 | 25 SEO-only sub-skills |
| Specialist agents | **24** | 0 | 0 | 18 SEO-only |
| Has a methodology | **Yes — 12-Part Strategy Flow (61 explicit steps)** | No | No | No |
| Multi-brand / agency support | **Yes — per-brand state, brand-switch, agency-dashboard** | No | No | No |
| EU AI Act Article 50 ready | **Yes — C2PA + deepfake disclosure + 16 jurisdictions** | No | No | Partial |
| Cowork team persistence | **Yes — Drive MCP routing (v3.12.0)** | Cowork-native | Composio cloud | n/a |
| Real API execution | **Yes — 8 connectors live, 28 manifest-ready** | OAuth via plugin | OAuth via Composio | Optional DataForSEO / Firecrawl |
| 6-platform AEO/GEO audit | **Yes — incl. Google AI Mode (May 2026)** | No | No | Yes (AEO + GEO) |
| Cross-platform install | **9 native — CC + Cowork + Codex + Cursor + Copilot CLI + Antigravity + Hermes + OpenClaw + Grok** | Cowork only | Cowork + Codex | CC + Codex |
| Tests | **613 stdlib unittest** | unknown | unknown | 271 incl. SSRF/DNS coverage |
| Live-write safety | **Single-use approval record for writes it sends itself; MCP writes: typed yes + host prompt** | Host permission prompt | Host permission prompt | n/a |
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

## Try this first

Install, then ask in plain words. Each of these kinds of request reached the right skill in our trigger tests.

| You type | What happens |
|---|---|
| "set up a new brand" | The brand profile every skill reads: voice, audience, compliance |
| "build the Q3 campaign plan" | A multi-channel plan: objectives, channel mix, budget, timeline, KPIs |
| "why did our traffic drop" | A site-wide SEO audit ranked into a `PLAN.md`: technical, content, links, local |
| "how do we stack up against X" | A one-off analysis of 2-5 competitors: positioning, content, SEO, ads, pricing |
| "check this before we publish" | The scored pre-publish gate: claims, brand voice, compliance; plus an AI-tell scan |
| "how many visitors per variant" | An A/B test plan computed by script: sample size, days to run, stopping rules |

## Why Digital Marketing Pro

Most AI marketing tools generate isolated outputs — a campaign brief here, an email there. No canonical sequence, no shared state, no enforced structure. Result: inconsistent depth, missed dependencies, outputs that don't compound.

**DM Pro runs every brand through the same 12 parts, producing the same files in the same order, with explicit dependency rules between them.** That's the whole product. Everything else — the 164 skills, 24 agents, May–June 2026 compliance updates, Cowork persistence — exists to make that 12-Part Flow ship cleanly across real marketing operations.

| What this gives you that ad-hoc prompts don't | Why it matters |
|---|---|
| **Canonical 12-Part Strategy Flow** producing the Four Core Documents (61 explicit steps) | Every engagement looks the same, so handoffs work and quality is auditable |
| **Two-Views Model** (v1 unbiased + v2 client-validated) | You never lose the original market view when the client pushes back |
| **Decision Matrix** — maps validation responses to re-runs | Stops over-running (wasted hours) and under-running (broken strategy) |
| **Living Project Instruction File** — single source of truth per engagement | All skills read it first; corrections propagate automatically |
| **EU AI Act Article 50 readiness** built in | C2PA provenance signing, deepfake disclosure, final Article 50 Guidelines + Code of Practice (10 June 2026) in compliance |
| **6-platform AEO/GEO audit** (incl. Google AI Mode) | The first marketing plugin to treat AI Mode as a distinct surface from AI Overviews |

---

## What you get in 60 minutes

Run `/digital-marketing-pro:engagement` and the plugin produces a full brand-strategy engagement in roughly 60 minutes on Opus 4.8/Opus 5-class models — **~50–60 canonical files** organized by part:

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

Cost: roughly **$15–40 in Claude API spend** for a full 12-part engagement using Opus 4.8 or Opus 5 (same $5/$25 per-MTok pricing). The plugin itself is MIT-licensed and free.

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
~/.claude-marketing/brands/<brand-slug>/
├── profile.json                              ← brand voice, audience, guardrails, jurisdictions
├── insights.json                             ← cross-engagement learnings
└── engagements/
    └── <engagement-id>/
        ├── _engagement.json                  ← state: current part, completed parts, change log
        ├── living-instruction-file.md        ← Living Project Instruction File
        ├── part-01-client-inputs/            ← Part 1 Stone-vs-Opinion intake
        ├── part-02-external-research/        ← Part 2 external market research
        ├── part-03-four-core-documents/      ← Part 3 Four Core Documents (61 steps), v1/ and v2/
        ├── part-04-competitive-customer-market/  ← Part 4 analyses, v1/ and v2/
        ├── part-05-client-validation/        ← Part 5 Client Validation Document
        ├── part-06-v2-reruns/                ← Part 6 selective v2 re-runs
        ├── part-07-preparation/              ← Part 7 internal operating layer
        ├── part-08-growth-plan/              ← Part 8 Growth Plan + Yearly Planner
        ├── part-09-channel-strategy/         ← Part 9 channel-strategy fan-out
        ├── part-10-execution-artefacts/      ← Part 10 ad copy / post copy / headlines / CTAs
        ├── part-11-ai-creative-instructions/ ← Part 11 AI creative instructions
        └── part-12-continuous-improvement/   ← Part 12 continuous improvement loop
```

The workspace is `~/.claude-marketing/` unless `CLAUDE_MARKETING_HOME` or your host's plugin data folder says otherwise; user-facing deliverables are also copied to `~/Documents/DigitalMarketingPro/` (`/digital-marketing-pro:output-folder` opens it).

See the [Multi-Brand & Agency Guide](docs/multi-brand-guide.md) for the multi-client switching workflow.

---

## Real workflows you'd actually run

### 🆕 New-client onboarding (agency, week 1)
```
/digital-marketing-pro:brand-setup "ACME Corp"        # interactive: voice, audience, channels, jurisdiction
/digital-marketing-pro:competitor-analysis            # multi-dimensional deep-dive on top 5 competitors
/digital-marketing-pro:engagement                     # full 12-Part Strategy Flow (~60 min on Opus-class)
/digital-marketing-pro:check  engagements/<id>/part-03-four-core-documents/v1/*.md   # pre-publish gate before client review
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
/digital-marketing-pro:execute-action --action diagnostic --brand acme --execute         # GA4 + GSC tag/consent check (MCP path: returns the manifest)
/digital-marketing-pro:execute-action --action audit-current --brand acme --execute      # current SEO state (Ahrefs over HTTP; GSC via MCP)
/digital-marketing-pro:execute-action --action enable-automation --brand acme --execute  # email automation flow: prepares a preview + approval record
# after you type yes: approval-manager.py --brand acme --action approve --id <id>, then re-run with --approval-id <id>
```
Output: HTTP calls for the 8 executable connectors (Slack, HubSpot, Klaviyo, SendGrid, Brevo, Customer.io, Mailchimp, Ahrefs), MCP manifests for the rest; each write fires against a single-use approval record for that exact request and is logged at `~/.claude-marketing/brands/{brand}/executions/`. See [Safety and approvals](#safety-and-approvals).

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

## Safety and approvals

![How a live write gets approved: prepare builds the exact request and a pending record with a preview and sends nothing; you read the preview and type yes; the approval step marks the record approved; fire sends only if the request matches the record's hash within 15 minutes and the record is unused, otherwise it is refused. MCP-tool writes are outside this check and rely on the typed yes and your host's permission prompt.](docs/assets/approval-flow.svg)

- **Writes the plugin sends itself** (`/digital-marketing-pro:execute-action`) fire only against a single-use approval record for that exact request: the script prepares the record with a preview of the request, the skill approves it after you type `yes`, and the request must match it byte for byte within 15 minutes. The record proves the approval step ran for this request, once; it cannot prove who typed `yes`, because the agent runs every command.
- **Writes through MCP server tools** (Google Ads, Meta, LinkedIn, TikTok, Amazon and other connected servers) are outside that code check. They rely on the skill's typed-`yes` gate and your host's permission prompt.
- **Keep the gate you control.** Leave `connector_executor.py --execute` and MCP write tools out of your host's command allowlist so it asks you every time; bypass or auto-approve modes remove that check.
- **Autopilot proposes by default.** It applies a correction on its own only under a standing approval you approved: scoped, capped per day, at most 30 days. Details in [PRIVACY.md](PRIVACY.md).

### What it will never do

- **Install a package on its own.** A missing one prints the exact pinned install command.
- **Send, publish or spend without your typed `yes`** (or a standing rule you approved). Writes it sends itself also need the single-use approval record above.
- **Ask for an API key in the chat.** Connectors read keys from environment variables.
- **Connect a service you did not set up.** No MCP server ships enabled and no hooks run.
- **Remove or hide AI watermarks.** AI involvement is disclosed, with C2PA provenance where the format supports it.

## Supported surfaces (v3.35.2)

| Platform | Install command | Manifest path | Status |
|---|---|---|---|
| **Claude Code** CLI + IDE extensions | `/plugin install digital-marketing-pro@neels-plugins` | `.claude-plugin/plugin.json` | Full support (canonical) |
| **Anthropic Cowork** | Plugins UI → Add marketplace → `indranilbanerjee/neels-plugins` → Install | same `.claude-plugin/` files | Full support — no `/plugin` slash commands in Cowork (UI-only) |
| **OpenAI Codex** CLI + IDE + App | `codex plugin marketplace add indranilbanerjee/neels-plugins` then `codex plugin add digital-marketing-pro@neels-plugins` | `.codex-plugin/plugin.json` (published OpenAI schema) | Full skills + MCP support |
| **Cursor 2.5+** | In any Cursor Agent chat: `/add-plugin digital-marketing-pro@https://github.com/indranilbanerjee/digital-marketing-pro` | `.cursor-plugin/plugin.json` (published Cursor JSON Schema) | Full skills + agents + commands support |
| **GitHub Copilot CLI** | `copilot plugin marketplace add indranilbanerjee/neels-plugins` then `copilot plugin install digital-marketing-pro@neels-plugins` | `.github/plugin/plugin.json` (Copilot CLI also recognizes `.claude-plugin/plugin.json` as fallback) | Full skills + MCP support; subagents need `.agent.md` extension (open issue); skills run as `/skill-name` or by natural language |
| **Google Antigravity 2.0** CLI + IDE | `agy plugin install https://github.com/indranilbanerjee/digital-marketing-pro` | `gemini-extension.json` (at repo root, per Google's reference pattern) | Full skills + hooks support; subagents need `/agent` CLI spawning; slash commands fold into skills via `agy plugin import gemini` |
| **Hermes Agent** (Nous Research) — Desktop + CLI on macOS / Windows / Linux | `hermes plugins install indranilbanerjee/digital-marketing-pro` | `plugin.yaml` + `__init__.py` at repo root (Hermes native spec) | Native plugin — adapter walks `skills/` at register time and exposes all 164 skills via `ctx.register_skill()`. Targets Hermes Desktop v0.15.2+ (public preview June 2 2026). |
| **OpenClaw** (formerly Clawdbot / Moltbot) | `openclaw plugins install git:github.com/indranilbanerjee/digital-marketing-pro` | `openclaw.plugin.json` at repo root (also auto-detects `.claude-plugin/plugin.json` as Claude-compatible bundle) | Native plugin via `openclaw.plugin.json`; `skills` field points at `./skills`. Also installable via ClawHub marketplace (submission pending). |
| **Grok** (xAI Build CLI) | `grok plugin install indranilbanerjee/digital-marketing-pro` — or `grok plugin marketplace add indranilbanerjee/neels-plugins` then `grok plugin install digital-marketing-pro` (append `--trust` to skip the install confirmation) | `.grok-plugin/plugin.json` + `.grok-plugin/marketplace.json` ([Grok Build](https://docs.x.ai/build/features/skills-plugins-marketplaces) also reads the Claude Code manifests for compatibility; the native pair is the first-class lane) | Full skills support |

**Why this works:** Agent Skills became an open standard in December 2025 (donated to the Agentic AI Foundation; adopted by **41+ agent products** by June 2026 — see ["Works on 40+ agent harnesses"](#works-on-40-agent-harnesses-via-the-agent-skills-open-standard) below). All 164 SKILL.md files in DM Pro are platform-portable as written. The sibling manifests are thin platform-specific wrappers around the same `skills/` directory — no skill duplication, no maintenance fork. The pattern is borrowed from Google's reference repo [`gemini-cli-extensions/data-agent-kit-starter-pack`](https://github.com/gemini-cli-extensions/data-agent-kit-starter-pack).

**Recommended Claude Code version: current.** Claude Code has no plugin-level minimum-version field — `requiredMinimumVersion` is a *managed setting* that pins the host version for everyone, so a plugin cannot enforce it (DMP declared it in plugin.json from v3.12.0 to v3.31.1, where Claude Code silently stripped it; corrected in v3.32.0). Teams that want a floor set it in their own `settings.json` — see [`settings.json.example`](settings.json.example).

---

## Works on 40+ agent harnesses (via the Agent Skills open standard)

Beyond the 9 surfaces above where we ship a native manifest, DMP's 164 SKILL.md files work out-of-the-box on any agent that adopted the [Agent Skills open standard](https://agentskills.io) (Anthropic-published Dec 2025, 41+ adopters as of June 2026). On each platform below, point it at our `skills/` folder and all 164 marketing skills are immediately discoverable. No platform-specific manifest needed.

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

![The 12-part engagement: client inputs, external research, the Four Core Documents, market analyses, client validation (the one true stop), selective v2 re-runs, then preparation, the Growth Plan and Yearly Planner, channel fan-out, execution, AI creative briefs and the improvement loop that feeds the next cycle](docs/assets/engagement-flow.svg)

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

### v3.35.2 — every missing-package message prints the exact pinned command (October 10, 2026)

The never-do panel said a missing package prints the exact pinned install command; only C2PA did. Now `_common.PINNED_DEPENDENCIES` pins every optional package (each the newest release at least two weeks old that supports Python 3.10), `scripts/requirements.txt` lists the same exact pins, `setup.py --install` installs from the table, and every missing-package message prints the tested command, including two that said nothing useful before (the AI-visibility checker blamed the API key when its SDK was missing; the UTM QR note gave no command). Proved in fresh Python 3.10 and 3.13 environments. Also fixed, from a claim check of this README against the code: the automation examples (diagnostic returns an MCP manifest; audit-current is an SEO audit; approve needs `--brand`), the OAuth connector count (28, not 25), the output-folder tree (`brands/<slug>/profile.json`, `part-01-…` folders), the check row and the live-write comparison. New guards: `tests/test_pinned_dependencies.py`, connector-count and brand-path checks in `tests/test_doc_counts.py`, and `tests/test_manifest_paths.py`. 613 tests.

### v3.35.1 — C2PA signing with a prompt works on the current c2pa-python (October 10, 2026)

`embed-c2pa.py --prompt` failed to sign on c2pa-python 0.38.0, the version v3.35.0 pins, because the prompt was written as a second `c2pa.opened` action; it now rides on the created action. New `tests/test_c2pa_embed.py` (10 tests) pins v3.35.0's C2PA fixes, which had been verified by hand: no install path, pinned install command and exit 2 when a package is missing, the dev key removed even on failure, the `--verify` exit codes, and the PRIVACY.md disclosures. 585 tests.

### v3.35.0 — live writes need a matching approval record (October 10, 2026)

Answers every point of the Hermes catalog review (NousResearch/hermes-agent#132571). Writes sent by `connector_executor.py` fire only against an approval record bound by sha256 to the exact request, approved after you type `yes`, used once, inside a 15-minute window; batches get one record with an itemised preview, and routine writes can run under a capped, expiring standing approval. MCP-tool writes are outside that check and the docs say so, along with the advice to keep the executor out of your host's allowlist. Autopilot proposes by default. `embed-c2pa.py` no longer installs packages (and now signs on c2pa-python 0.38.0, where it had been failing) and gains `--verify`. `safe_child` and a validating argparse type keep model-supplied names inside the plugin's folders; fetchers check every redirect hop; PRIVACY.md lists the DigiCert timestamp and NLTK downloads. 575 tests.

Older releases are in [CHANGELOG.md](CHANGELOG.md).

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

### 164 skills
Skills are invoked by description match through the Skill tool, addressable as `/digital-marketing-pro:<skill-name>` from chat. Coverage: brand setup, content production (blog / ad / email / social / landing / video / PR / case study), SEO / AEO / GEO audits (6 platforms incl. Google AI Mode), competitor monitoring, campaign planning, channel-specific strategies, attribution, churn risk, lifecycle journeys, intelligence reports, eval framework, knowledge management, multi-brand operations, regional configuration, C2PA content provenance, **Cowork+Drive team persistence**.

### Slash commands
Every skill answers to `/digital-marketing-pro:<skill-name>`. Five more are standalone commands with no same-named skill: `engagement`, `resume`, `output-folder`, `doctor` and `execute-action`. v3.33.0 folded every command that duplicated a same-named skill into that skill, so those slash names work exactly as before and each now loads once instead of twice. The most-used:

| Slash name | What it does |
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
| `/digital-marketing-pro:execute-action` | Actually fire an action against its real API (stdlib `urllib`, no third-party deps). 8 verified connectors execute end-to-end; 28 OAuth-only or MCP-only connectors fall back to the MCP path with the manifest still returned. |
| `/digital-marketing-pro:cowork-setup` | (v3.12.0) One-shot Cowork team setup — wires DMP through a Drive MCP so brand state survives across Cowork sessions |
| `/digital-marketing-pro:keyword-cluster` | Pillar + spokes content cluster from seed keywords with SERP-overlap clustering and 4-gate quality scorecard |
| `/digital-marketing-pro:backlink-gap` | Competitor backlink gap audit with priority scoring (DR + overlap + traffic + topical) |
| `/digital-marketing-pro:seo-drift` | Snapshot-vs-snapshot drift with auto-classification (growth/decline/reshuffle/stable/new/lost) |

Every other skill works the same way — `:competitor-monitor`, `:churn-risk`, `:autopilot-status`, `:agency-dashboard`, `:aeo-audit`, `:geo-monitor`, `:c2pa-metadata`, `:client-onboarding`, `:journey-design` … see `/digital-marketing-pro:help` after install for the full list, or browse `skills/` in the repo.

### 94 Python scripts (optional)
Plugin works fully without Python — all marketing knowledge, frameworks, agent capabilities, and skills work out of the box via the 176 reference knowledge files.

| Mode | Size | Adds |
|---|---|---|
| **Knowledge-only** (default) | 0 MB | All 164 skills + 24 agents + 176 reference files |
| **Lite** (`python scripts/setup.py --install lite`) | ~15 MB | Brand-voice scoring, content quality scoring, readability analysis |
| **Full** (`python -m pip install -r scripts/requirements.txt`, exact pins) | ~50 MB | Competitor scraping, QR generation, AI visibility API checking, GEO tracking, C2PA signing |

### 14 HTTP MCP connectors
Notion · Slack · Canva · Figma · HubSpot · Amplitude · Ahrefs · SimilarWeb · Klaviyo · Google Calendar · Gmail · Stripe · Asana · Webflow

These are an **opt-in catalog** — no `.mcp.json` ships (it is gitignored), so nothing auto-connects; enable only the ones you need. All HTTP, all Cowork-compatible. For services without first-party HTTP MCPs (Google Sheets, Drive, Salesforce, etc.), see `.mcp.json.connectors-reference` for **Pipedream / Composio / Zapier / Make.com** aggregator paths.

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

**Fix 2 — Visible output folder.** Every artifact a workflow produces is now copied to TWO locations: the internal tracking copy under `~/.claude-marketing/brands/{brand}/output/{workflow}/...` (system-of-record), and a user-visible published copy under `~/Documents/DigitalMarketingPro/{brand}/{workflow}/{YYYY-MM}/{filename}` (visible in Windows Explorer / macOS Finder by default). Override the visible root with `DIGITAL_MARKETING_PRO_PUBLISH_DIR=/path` (e.g. a Dropbox share for the team). Reveal the folder any time with:

```
/digital-marketing-pro:output-folder                       # opens ~/Documents/DigitalMarketingPro/{brand}/
/digital-marketing-pro:output-folder <brand> <workflow>    # drill down
```

**Implementation:** `scripts/checkpoint-manager.py` (per-step storage + atomic writes, stdlib only) + `scripts/output-publisher.py` (dual-copy publish + `where` + `open` subcommands: internal tracking copy + user-visible published copy). The engagement/checkpoint state machine ships tests in `tests/test_engagement_state.py` + `tests/test_checkpoint_roundtrip.py`; a fuller 5-scenario end-to-end simulation (clean 12-part run / interrupt-resume / parallel workflows / quality-gate fail / all-workflows-accepted) was used during development but is a dev tool, not shipped in the repo.

---

## Connector-aware action resolver (v3.7.10+)

The `campaign-audit` and `launch-campaign` skills depend on 14 actions that map to real marketing APIs (Google Ads, Meta Marketing, LinkedIn, TikTok, HubSpot, Salesforce, Klaviyo, Mailchimp, Customer.io, Gmail, Cision, Muckrack, Slack, Google Calendar, Ahrefs, Similarweb, SEMrush, Google Search Console). v3.7.5–v3.7.7 shipped these actions as honest stubs that always returned `status: stub_implementation` regardless of which connectors the user had. v3.7.10 introduces a resolver that probes the live state and resolves each action to one of three modes per call:

| mode | what it means |
|------|---------------|
| `real` | runs end-to-end with no external API (currently only `arm-watchdog` which writes a watchdog config to `~/.claude-marketing/brands/{brand}/watchdogs/`) |
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
| Brevo | `BREVO_API_KEY` | `GET /v3/emailCampaigns` (read only, lowercase `api-key:` header; sends go through the Brevo MCP) |
| Customer.io | `CUSTOMERIO_APP_API_KEY` | `GET /v1/campaigns` (read only; sends go through the Customer.io MCP) |
| Mailchimp | `MAILCHIMP_API_KEY` | `GET /3.0/automations` (Basic auth, dc from suffix) |
| Ahrefs | `AHREFS_API_KEY` | `GET /v3/site-explorer/metrics` |

**Requires the MCP path (28 OAuth-only or MCP-only connectors):** Google Ads, Meta Marketing, LinkedIn Marketing, LinkedIn Publishing, TikTok Ads, Twitter/X, Gmail, Google Calendar, Google Analytics, Google Search Console, Meta Graph, Salesforce, Pipedrive, Zoho CRM, Buffer, Hootsuite, Cision, Muckrack, Amplitude, Similarweb, SEMrush, Moz, Intercom, Canva, Figma, plus the official ad-platform MCP servers Meta Ads AI Connectors, Google Ads MCP (read-only) and Amazon Ads MCP. For all of these, the resolver still returns `manifest_ready` so you can see the exact HTTP shape Claude's MCP tool will send — Python just can't execute the OAuth flow itself.

**Safety gates (updated in v3.35.0):** read ops auto-execute with `--execute`; write ops need a matching approved, single-use approval record (`--approval-id`), see [Safety and approvals](#safety-and-approvals); missing env vars block with `setup_hint_credential`; unresolved `{VAR}` placeholders block before the request fires. Every fired call logs to `~/.claude-marketing/brands/{brand}/executions/`.

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
python scripts/resolve_model.py --check gemini-2.0-flash              # -> retired (auto-routes to gemini-3.5-flash)
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
- Final Article 50 Guidelines + final Code of Practice on Transparency of AI-Generated Content (10 June 2026) in `compliance-rules.md` §1.1b.i with six-row clarification table + five-point action list
- Production cert guide at `docs/c2pa-production-cert-guide.md` covers the four CAI-recognised authorities (Adobe Content Credentials, Truepic, Numbers Protocol, Microsoft Azure Confidential Ledger)

**Other May 2026 regulatory updates baked in:**
- NY synthetic-performer disclosure law (live June 2026, $1K–$5K per violation, $10K repeat) — applies to synthetic influencers + AI endorsements
- FTC May 2026 endorsement guidance — synthetic influencers, AI testimonials, AI-edited creator content
- CJEU March 2026 ruling — pseudonymized cookie IDs are personal data when re-identification is feasible
- CCPA Jan 2026 ADMT amendments + AI-derived sensitive data classification
- DPDP Phase II preparation — consent manager registration opens Nov 2026

---

## AEO / GEO — what changed in 2026

The search landscape pivoted hard in 2025–2026:
- Google AI Overviews appear on ~55% of all Google searches (Seer Interactive, Sept 2025); organic CTR on AI Overview queries dropped ~61% (1.76% → 0.61%); ~58% of Google searches are now zero-click
- **Google AI Mode** became the default conversational search experience for opted-in users at I/O 2026 (19 May 2026), backed by Gemini 3.5 Flash — ~1B MAUs
- ChatGPT search reaches ~883M MAU; Perplexity heavily skews citations to Reddit (47% of factual cites); Wikipedia drives 48% of ChatGPT citations

DM Pro's AEO/GEO skills (`/digital-marketing-pro:aeo-audit`, `:geo-monitor`, `:entity-audit`) reflect this:
- **6-platform audit standard** — ChatGPT, Perplexity, Google AI Mode, Google AI Overviews, Gemini, Microsoft Copilot (was 5 — AI Mode added May 2026)
- Schema strategy refresh — Google's March 2026 core update demoted FAQ/Review/HowTo schema on non-primary pages. Skills emphasise entity-rich JSON-LD (Article + Organization + Person + Product) and offer an optional **LLMs.txt** companion (Google states it is not required for AI-features eligibility)
- Citation tracking across all 6 surfaces, with Profound / Otterly / Conductor AgentStack integration paths in the connectors layer
- **Share of AI Voice** as a first-class metric in `/digital-marketing-pro:performance-report`

---

## Channel guidance — 2026 platform changes built in

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
Roughly **$15–40** for a complete 12-part engagement using Opus 4.8 or Opus 5 (same pricing) across ~50–60 documents. Track per-brand consumption via Claude Code v2.1.149+ `/usage` (now integrated into `/digital-marketing-pro:agency-dashboard`).

**Q: Can I run multiple brands in parallel?**
Yes. Each brand has its own `~/.claude-marketing/brands/<brand-slug>/` directory and Python script state. Switch with `/digital-marketing-pro:switch-brand`.

**Q: What if I only want a campaign plan, not the full methodology?**
Skip to `/digital-marketing-pro:campaign-plan`. Every individual surface (campaign / SEO / content / competitor / email / report) is independently runnable. The full engagement is the canonical path, not the only path.

**Q: Will this work on Codex / Cursor / Copilot CLI / Antigravity?**
Yes — verified-real native manifests ship for all 9 surfaces (CC, Cowork, Codex, Cursor, Copilot CLI, Antigravity, Hermes Agent, OpenClaw, Grok). See [Supported surfaces](#supported-surfaces-v3352) above for per-platform install commands.

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

Common install + first-run issues across all 9 supported platforms, with the fix.

### Claude answers in chat instead of using a skill

Claude Code lists every installed skill in a budget of 1% of the context window. Digital Marketing Pro's 170 entries fit a 1M window in full, but on a 200k window only the names fit, so Claude can't see what each skill does. Add `"skillListingBudgetFraction": 0.05` to your Claude Code `settings.json`. You can also start any skill by name, e.g. `/digital-marketing-pro:seo-audit`.

### Claude Code + Cowork

**"/plugin isn't available in this environment"**
You're in the standard Claude chat app (browser `claude.ai` or the Claude Desktop app). The `/plugin` slash command only works in **Claude Code** (the dev CLI/IDE at [claude.com/code](https://claude.com/code)) and **Anthropic Cowork**. Everywhere else, plugins install via the UI: click the **Plugins** button at the bottom of the chat. See [Updating](#updating) for the full recovery procedure.

**"Plugin installed but slash commands not showing"**
Run `/reload-plugins` (Claude Code) or restart the Cowork chat session. If still missing, your Claude Code build may be too old for the plugin features DMP relies on — run `claude --version` and update via `npm install -g @anthropic-ai/claude-code` (DMP cannot enforce a minimum itself; see Supported surfaces).

**"Brand profile vanishes between Cowork sessions"**
Cowork's filesystem is per-session ephemeral — `~/.claude-marketing/` AND `${CLAUDE_PLUGIN_DATA}` both reset at session end ([open issue #51398](https://github.com/anthropics/claude-code/issues/51398)). Fix: run `/digital-marketing-pro:cowork-setup` once per team — it routes brand state through a Google Drive MCP so profiles survive across sessions and your whole team sees them. See [v3.12.0 release notes](#whats-new) for the why-and-how.

**"`/digital-marketing-pro:doctor` says urgent (model registry stale)"**
The model registry hasn't been refreshed for 60+ days — frontier models shift every ~6 weeks so deprecated IDs may start 404-ing. Fix: `ANTHROPIC_API_KEY=... OPENAI_API_KEY=... GEMINI_API_KEY=... EVOLINK_API_KEY=... python scripts/refresh_models.py`. The script polls each provider's `/v1/models` endpoint and reports drift versus our registry.

### OpenAI Codex / Cursor / GitHub Copilot CLI / Antigravity

**"Skills install but commands not discovered"**
These platforms read SKILL.md by description match — invoke via natural language (*"Run a competitor analysis on stripe.com"*) rather than typing a slash command. Slash commands (`/digital-marketing-pro:<name>`) are a Claude Code convention; on other surfaces the agent picks up the skill from intent.

**"Codex says skill name failed regex check"**
Codex enforces `[a-z0-9-]+` on skill names. All 164 DMP skill names pass this regex (verified in the test suite). If you see this error, it's likely a personal skill you added — rename it to lowercase + hyphens only.

**"Cursor `/add-plugin` returns 'plugin not found'"**
Use the full Git URL form: `/add-plugin digital-marketing-pro@https://github.com/indranilbanerjee/digital-marketing-pro`. Cursor's marketplace integration is fastest, but the Git URL form always works.

### Hermes Agent

**"`hermes plugins install ...` finishes but no skills appear"**
The plugin needs to be enabled after install: `hermes plugins enable digital-marketing-pro`. Then verify with `hermes plugins list`. If the adapter's `register()` returned silently with no skills, run the audit: `cd ~/.hermes/plugins/digital-marketing-pro && python __init__.py` — it'll print the discovered skill count + the first five skills, confirming the clone got the full `skills/` tree.

**"register_skill error in Hermes logs"**
Check Hermes version: this plugin targets **v0.15.2+**. Run `hermes --version`. Older builds may have a different `ctx` API surface — the adapter degrades gracefully (logs an error, doesn't crash) but won't register skills. Upgrade Hermes to the latest public preview.

### OpenClaw

**"OpenClaw can't find the plugin manifest"**
Use the `git:` install scheme: `openclaw plugins install git:github.com/indranilbanerjee/digital-marketing-pro`. If you used another scheme and it failed, the fallback is: `cd ~/.openclaw/plugins && git clone https://github.com/indranilbanerjee/digital-marketing-pro && openclaw plugins enable digital-marketing-pro`.

**"OpenClaw uses Claude bundle but loses some features"**
OpenClaw auto-detects our `.claude-plugin/plugin.json` as a Claude-compatible bundle, but the native `openclaw.plugin.json` gives first-class discoverability. Both load the same 164 skills from `./skills`. Verify with `openclaw plugins inspect digital-marketing-pro --runtime --json`.

### Grok (xAI Build CLI)

**"`grok plugin install` can't find the plugin"**
Use the direct repo form: `grok plugin install indranilbanerjee/digital-marketing-pro` — the native `.grok-plugin/` manifest pair ships in-repo, so no separate marketplace is needed. Alternatively add the marketplace first: `grok plugin marketplace add indranilbanerjee/neels-plugins` then `grok plugin install digital-marketing-pro`. Append `--trust` to skip the install confirmation. Grok also reads the Claude Code manifests for compatibility, so even a pre-3.31.0 clone loads — the native pair is what gives first-class discoverability.

### General (any platform)

**"Tests in `tests/` fail when I `git clone` locally"**
Run `python tests/run_all.py` from the repo root. All 613 tests are stdlib-only — no `pip install` needed. If they fail, the most likely cause is a Python version mismatch (DMP supports Python 3.10+) or a clone that omitted some `skills/` subdirectories. Try `git clone --depth=1` again.

**"`/digital-marketing-pro:doctor` shows my action as stub_unconfigured"**
That action needs an MCP connector configured. Run `python scripts/connector-status.py --action setup-guide --name <connector-name>` for the exact setup snippet. Add it to your `.mcp.json` under `mcpServers`, restart your agent, and the action becomes `manifest_ready`. See [Connector-aware action resolver](#connector-aware-action-resolver-v3710) for the full readiness model.

**"Where do my brand files actually go?"**
Run `/digital-marketing-pro:output-folder` — it prints the active output directory and (on local Claude Code) opens it in your OS file manager. Default: `~/.claude-marketing/brands/<brand-slug>/` for working state + `~/Documents/DigitalMarketingPro/<brand>/` for finished deliverables. Both configurable via `output-folder`.

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

If a version stays the same but content changed (fast-iteration debugging): delete the folder `~/.claude/plugins/cache/neels-plugins` (it holds only downloaded plugin copies), then:
```
/plugin install digital-marketing-pro@neels-plugins
/reload-plugins
```

---

## Neelverse Marketing Suite

DM Pro is part of a three-plugin suite by [Indranil Banerjee](https://indranil.in) — one marketplace, installed together, designed to chain (each plugin keeps its own brand setup):

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

<a href="https://www.star-history.com/?type=date&repos=indranilbanerjee%2Fdigital-marketing-pro">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=indranilbanerjee/digital-marketing-pro&type=date&theme=dark&legend=top-left&sealed_token=AqnW48iQwpZNQCx5Ncz_reoaRoDWKEEG-sZXQohHllcyAFnSDLdSJVqEoTci2Y8ognOBGCUrCY9eU3yUIW_YG7TwVhwub90B7qGh-9qlJgGjfFQQbp__puZDwereB6S-SQzbcK8B68Z-izIHjTt1DFPa5YxfuWlFF8MhrLdIEhFdU2x-cwHzmGWYYhBl" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=indranilbanerjee/digital-marketing-pro&type=date&legend=top-left&sealed_token=AqnW48iQwpZNQCx5Ncz_reoaRoDWKEEG-sZXQohHllcyAFnSDLdSJVqEoTci2Y8ognOBGCUrCY9eU3yUIW_YG7TwVhwub90B7qGh-9qlJgGjfFQQbp__puZDwereB6S-SQzbcK8B68Z-izIHjTt1DFPa5YxfuWlFF8MhrLdIEhFdU2x-cwHzmGWYYhBl" />
    <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=indranilbanerjee/digital-marketing-pro&type=date&legend=top-left&sealed_token=AqnW48iQwpZNQCx5Ncz_reoaRoDWKEEG-sZXQohHllcyAFnSDLdSJVqEoTci2Y8ognOBGCUrCY9eU3yUIW_YG7TwVhwub90B7qGh-9qlJgGjfFQQbp__puZDwereB6S-SQzbcK8B68Z-izIHjTt1DFPa5YxfuWlFF8MhrLdIEhFdU2x-cwHzmGWYYhBl" />
  </picture>
</a>

If DM Pro saves your team time, [⭐ star the repo](https://github.com/indranilbanerjee/digital-marketing-pro/stargazers) — it's the single most useful thing you can do to help other marketing teams discover it.

---

## About the maintainer

DM Pro is built and maintained by **[Indranil “Neel” Banerjee](https://indranil.in)** — a builder and systems thinker with roots in information security and a second act across growth marketing, enterprise digital operations, and AI transformation. This repository is one public implementation of a broader focus on trustworthy AI execution: preserve context, make evidence inspectable, and keep people at consequential decision points.

- 🌐 **Website:** [indranil.in](https://indranil.in)
- 💼 **LinkedIn:** [linkedin.com/in/askneelnow](https://www.linkedin.com/in/askneelnow)
- 🐦 **X / Twitter:** [@askneelnow](https://x.com/askneelnow)
- 💻 **GitHub:** [@indranilbanerjee](https://github.com/indranilbanerjee)
- 📦 **Other plugins:** [ContentForge](https://github.com/indranilbanerjee/contentforge) · [SocialForge](https://github.com/indranilbanerjee/socialforge)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/indranilbanerjee/digital-marketing-pro/discussions)
- 🐛 **Bug reports:** [GitHub Issues](https://github.com/indranilbanerjee/digital-marketing-pro/issues)

**Why this plugin exists:** Most AI marketing tools generate isolated outputs that don't compose. The 12-Part Strategy Flow encodes the canonical sequence a real engagement actually needs — Stone-vs-Opinion intake, Four Core Documents, Client Validation, Two-Views Model, Decision Matrix, Growth Plan + Yearly Planner, channel fan-out, execution artefacts, creative briefs, continuous improvement loop. Once it's a plugin, every engagement looks the same, handoffs work, and quality is auditable. That's the whole product.

If DM Pro saves your team time, [⭐ star the repo](https://github.com/indranilbanerjee/digital-marketing-pro/stargazers) — it's the single most useful thing you can do to help other marketing teams discover it. Sharing it on **LinkedIn** or **X** helps people discover the work too.

---

## Contributing

PRs welcome — especially on compliance rules (privacy and AI law change fast), industry profiles, and channel-specific updates. See [CONTRIBUTING.md](CONTRIBUTING.md) for the contribution workflow, [`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md) for the PR checklist, and [TESTING-GUIDE.md](TESTING-GUIDE.md) for per-phase test checklists. All contributors are expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md). Security issues: please use [Private Security Advisories](https://github.com/indranilbanerjee/digital-marketing-pro/security/advisories/new) per [SECURITY.md](SECURITY.md) — do not file public issues for vulnerabilities.

---

## Sponsor this project

This plugin is MIT-licensed, free to use commercially, and collects no telemetry. What
sponsorship pays for is the unglamorous half of keeping it accurate: platform-API updates
when a vendor ships a breaking version, model-registry refreshes when a model is retired,
compliance passes when regulatory guidance moves, and issue triage.

If it saves your team time, you can [sponsor the work](https://github.com/sponsors/indranilbanerjee).
Sponsors from $25/mo are listed in [SPONSORS.md](SPONSORS.md).

[![Sponsor](https://img.shields.io/badge/sponsor%20on%20GitHub-%E2%9D%A4-ea4aaa?logo=githubsponsors&logoColor=white)](https://github.com/sponsors/indranilbanerjee)

---

## License

MIT — see [LICENSE](LICENSE). Free to use commercially.

---

## Release notes

Every release, with what changed and why: [CHANGELOG.md](CHANGELOG.md).
