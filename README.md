<p align="center">
  <br>
  <img width="80" src="https://cdn.rawgit.com/sindresorhus/awesome/d7305f38d29fed78fa85652e3a63e154dd8e8829/media/badge.svg" alt="Awesome">
  <br>
</p>

<h1 align="center">Awesome Codex Plugins</h1>

<p align="center">A curated list of awesome OpenAI Codex plugins, skills, and resources.</p>

<p align="center">
  <a href="https://hol.org/registry/plugins">
    <img src="assets/awesome-codex-plugins-hol.png" alt="Awesome Codex Plugins by HOL" width="960" height="540">
  </a>
</p>

<p align="center">
  <a href="#contributing"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome"></a>
  <a href="https://opensource.org/licenses/Apache-2.0"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="License"></a>
  <a href="https://hol.org/registry/plugins"><img src="https://img.shields.io/badge/Browse-Registry-green" alt="Browse Registry"></a>
</p>

<p align="center">
  OpenAI <a href="https://openai.com/academy/codex-plugins-and-skills/">documents plugins and skills for Codex</a>, packaging skills, MCP servers, and app integrations into shareable, installable bundles across the Codex app, CLI, and IDE extensions.
</p>

<br>

## Contents

- [Start Here](#start-here)
- [Official Plugins](#official-plugins)
- [Community Plugins](#community-plugins)
- [Plugin Development](#plugin-development)
- [Guides & Articles](#guides--articles)
- [Related Projects](#related-projects)

---

## Start Here

New plugin workflow:

1. Create with `$plugin-creator`
2. Validate with [`plugin-scanner`](https://github.com/hashgraph-online/hol-guard)
3. Gate PRs with the [HOL scanner GitHub Action](https://github.com/hashgraph-online/ai-plugin-scanner-action)
4. Ship or submit with confidence

Quick preflight:

```bash
pipx run plugin-scanner lint .
pipx run plugin-scanner verify .
```

This repo publishes a Codex repo marketplace at `.agents/plugins/marketplace.json`. The marketplace points at mirrored installable plugin bundles under `./plugins/`, so a clone of this repo can act as a curated plugin source in Codex.

### Use this marketplace in Codex

Install plugins directly from this curated list by pointing Codex at the repo marketplace:

**CLI:**
```bash
# Add this repo as a marketplace source (one-time setup)
codex plugin marketplace add \
  'https://github.com/hashgraph-online/awesome-codex-plugins.git' \
  --ref 'main' \
  --sparse '.agents/plugins' \
  --sparse 'plugins'

# Then browse and install (the marketplace name is derived from the repo name)
codex plugin list --source awesome-codex-plugins
codex plugin install <plugin-name> --source awesome-codex-plugins
```

Do not use the raw `marketplace.json` URL with `codex plugin marketplace add`.
The Codex marketplace command clones a Git repository, so a raw GitHub file URL is
treated like a repo URL and fails with `remote: 404: Not Found`.

**Desktop App / IDE Extension:**
1. Open Codex settings → Plugins → Next to search plugins input click on menu and select → `+Add More...` 
<img width="1462" height="466" alt="image" src="https://github.com/user-attachments/assets/ae15f505-58a8-4199-bb7b-56a07b670b10" />


2. Add this URL:
   ```
   https://github.com/hashgraph-online/awesome-codex-plugins.git
   ```
   <img width="1974" height="1064" alt="image" src="https://github.com/user-attachments/assets/ffbae59f-41ae-4ee3-9d52-864273ecdcb3" />

3. The curated plugin list appears as an available marketplace source.

Each plugin entry includes a `source.path` pointing at a mirrored bundle under `./plugins/` in this repo, so installations are fast and reproducible without hitting upstream repos at install time.

## Official Plugins

<details>
<summary>Curated by OpenAI — available in the built-in Codex Plugin Directory</summary>

- Box - Access and manage files.
- Cloudflare - Manage Workers, Pages, DNS, and infrastructure.
- Figma - Inspect designs, extract specs, and document components.
- GitHub - Review changes, manage issues, and interact with repositories.
- Gmail - Read, search, and compose emails.
- Google Drive - Edit and manage files in Google Drive.
- Hugging Face - Browse models, datasets, and spaces.
- Linear - Create and manage issues, projects, and workflows.
- Notion - Create and edit pages, databases, and content.
- Sentry - Monitor errors, triage issues, and track performance.
- Slack - Send messages, search channels, manage conversations.
- Vercel - Deploy, preview, and manage Vercel projects.

</details>

## Community Plugins

Third-party plugins built by the community. [PRs welcome](#contributing)!

### Development & Workflow

<!-- pinned -->

- [Aegis](https://github.com/GanyuanRan/Aegis) - An agentic skills framework & software development methodology that works: planning, TDD, debugging, and collaboration workflows.
- [Agentizer](https://github.com/Humiris/wwa-transform) - Turn any website into an AI-powered agentfront with split-pane
- [AgentOps](https://github.com/boshu2/agentops) - DevOps layer for coding agents with flow, feedback, and memory that compounds between sessions.
- [Antigravity Workspace Template](https://github.com/study8677/antigravity-workspace-template) - Multi-agent codebase knowledge graph generator with context-aware planning and automatic scope management — turns codebases into coherent agent workspaces.
- [Archcore](https://github.com/archcore-ai/plugin) - Gives coding agents the architecture, rules, and prior decisions of the repo via skills, hooks, and MCP — so new changes land where the project says they belong across Claude Code, Cursor, and Codex CLI.
- [Bring Your AI Migration Auditor](https://github.com/unitedideas/bringyour-mcp) - Read-only Codex plugin for auditing Claude Code to Codex migrations before Codex edits code. Checks AGENTS.md/CLAUDE.md scope, hooks, MCP config, skills, secret references, and validation notes.
- [Brooks Lint](https://github.com/hyhmrright/brooks-lint) - AI code reviews grounded in six classic engineering books — decay risk diagnostics with book citations, severity labels, and four analysis modes (PR review, architecture audit, tech debt, test quality).
- [Changelog Forge](./plugins/mturac/changelog-forge) - Conventional commits → CHANGELOG section + semver bump.
- [Claude Code for Codex](https://github.com/sendbird/cc-plugin-codex) - Reverse of OpenAI's official Claude-hosted plugin: use Claude Code from Codex for reviews, rescue tasks, tracked background jobs, and hook-powered review gates.
- [Claude Code Harness](https://github.com/dadwadw233/claude-code-harness) - Harness blueprint skill for turning vague agent ideas into concrete designs for request assembly, control loops, memory, permissions, recovery, and extension planes.
- [Claude Code Skills](https://github.com/alirezarezvani/claude-skills) - 223 production-ready skills, 23 agents, and 298 Python tools across 9 domains — engineering, marketing, product, compliance, and more.
- [Claude Octopus](https://github.com/nyldn/claude-octopus) - Multi-LLM orchestration dispatching to 8 providers (Codex, Gemini, Copilot, Qwen, Perplexity, OpenRouter, Ollama, OpenCode) with Double Diamond workflows, adversarial review, and safety gates.
- [Codebase Recon](https://github.com/yujiachen-y/codebase-recon-skill) - Analyze git history to understand a codebase before reading any code — auto-scales by repo size and cross-references hotspots with bug magnets to surface high-risk files, bus factor, and team momentum.
- [Codex Agenteam](https://github.com/yimwoo/codex-agenteam) - Specialist AI agents (researcher, PM, architect, developer, QA, reviewer) orchestrated as a configurable team pipeline.
- [Codex Multi Auth](https://github.com/ndycode/codex-multi-auth) - Multi-account OAuth manager for the official Codex CLI with switching, health checks, and recovery tools.
- [Codex Reviewer](https://github.com/schuettc/codex-reviewer) - Second-pass review of Claude-driven plans and implementations.
- [Codex rg Guard](https://github.com/Rycen7822/codex-rg-guard) - Budgeted `rg`/`grep` replacement for Codex that narrows broad searches before they waste model context.
- [Commit Narrator](./plugins/mturac/commit-narrator) - Generate semantic commit message from staged diff, including the *why*.
- [Deps Doctor](./plugins/mturac/deps-doctor) - Multi-ecosystem dependency audit (npm, pip, cargo, go) in one report.
- [Development Skills](https://github.com/reidemeister94/development-skills) - Three-tier triage (PASS_THROUGH / LIGHT / FULL 4-phase) development workflow for Codex and Claude Code with language auto-detection (Python, Java, TypeScript, Swift, frontend) and a staff-reviewer subagent for fresh-eyes review on every change.
- [ejentum-mcp](https://github.com/ejentum/ejentum-mcp) - MCP server exposing reasoning, code, anti-deception, and memory harness tools for Codex.
- [Env Lint](./plugins/mturac/env-lint) - `.env` vs `.env.example` key parity — never prints values.
- [Flaky Detector](./plugins/mturac/flaky-detector) - Run a test command N times, report per-test flakiness %.
- [Frappe Agent](https://github.com/Dkm0315/frappe-agent) - Frappe and ERPNext coding, customization, bench, and review intelligence for Codex.
- [GrayMatter](https://github.com/ValkyrLabs/GrayMatter) - Durable memory and shared graph state for Codex and OpenClaw agents, with live ValkyrAI schema awareness.
- [HOL Guard Plugin](https://github.com/hashgraph-online/hol-guard-plugin) - AI antivirus workflow for Codex, Claude Code, Cursor, Gemini, OpenCode, MCP servers, skills, and plugin release checks with local approvals and receipts.
- [HOTL Plugin](https://github.com/yimwoo/hotl-plugin) - Human-on-the-Loop AI coding workflow plugin for Codex, Claude Code, and Cline with structured planning, review, and verification guardrails.
- [Personal Data Protection](https://github.com/AltByteSG/personal-data-protection-skill) - Engineer-facing personal-data-protection compliance reference — Singapore PDPA, Thailand PDPA, Indonesia UU PDP, Malaysia PDPA (Act 709 + 2024 Amendments), Philippines DPA — organised by where in the stack each obligation lands, with checklists, breach-response runbook, and a developer-view divergence table across all five.
- [PR Storyteller](./plugins/mturac/pr-storyteller) - PR title + body + test plan from commits and diff vs base branch.
- [Praxis](https://github.com/ouonet/praxis) - Intent-driven workflow skills for coding agents: describe what done looks like, not the steps. Triage-first design keeps token costs low across design, TDD, debug, review, and release.
- [Project Autopilot](https://github.com/AlexMi64/codex-project-autopilot) - Turn an idea into a structured project workflow with planning, execution, verification, and handoff.
- [Registry Broker](https://github.com/hashgraph-online/registry-broker-codex-plugin) - Delegate tasks to specialist AI agents via the HOL Registry, plan, find, summon, and recover sessions.
- [Secret Guard](./plugins/mturac/secret-guard) - Pre-commit secret scanner using pattern and entropy detection.
- [Session Orchestrator](https://github.com/Kanevry/session-orchestrator) - Session orchestration for Claude Code, Codex, and Cursor IDE — structured planning, wave-based execution, VCS integration (GitLab + GitHub), quality gates, and clean session close-out with issue tracking.
- [Spec-Driven Development](https://github.com/Habib0x0/spec-driven-plugin) - Three-phase Requirements → Design → Tasks workflow for Claude Code and Codex — EARS notation acceptance criteria, autonomous execution loop, cross-spec dependencies, and post-implementation acceptance testing.
- [Standup Generator](./plugins/mturac/standup-gen) - Daily standup notes from git activity across repos.
- [Stark](https://github.com/f0d010c/stark) - UI/UX design plugin for AI coding agents with product-flow routing, platform-native interface guidance, asset planning, and shipped-reference analysis before code.
- [tailtest](https://github.com/avansaber/tailtest-codex) - Hook-powered test generation -- detects files changed during an agent turn and instructs Codex to write and run tests automatically. Zero config, 8 languages.
- [Tandem Workflow Architect](https://github.com/frumu-ai/tandem-codex-plugin) - Plan Tandem workflows in Codex, then validate, preview, and run them through the governed Tandem engine.
- [Tartiner Labs](https://github.com/tartinerlabs/skills) - Agent skills for git workflows, GitHub automation, security audits, code refactoring, and project tooling.
- [Team Skills Platform](https://github.com/Colin4k1024/tsp) - Role-based team delivery framework — Tech Lead-orchestrated 8-role system with 195+ skills, 27 specialist agents, 80+ commands, hooks, and ECC harness for Claude Code, Codex, and OpenCode.
- [Test Gap](./plugins/mturac/test-gap) - Find lines in your diff lacking test coverage (Cobertura, lcov, coverage.json).
- [TODO Harvest](./plugins/mturac/todo-harvest) - TODO/FIXME/HACK scan with `git blame` author + age.
- [Tool Advisor](https://github.com/dragon1086/claude-skills) - Read-only meta-skill that scans your MCP servers, skills, plugins, and CLI tools, then suggests up to three ranked approaches (Methodical / Fast / Deep) with a copy-paste Quick Action table.
- [Unity Agent Workflows](https://github.com/AUN-PN/unity-agent-workflows) - Codex plugin and skill for Unity 2D agents that enforces "No proof, no edit" workflows with runtime-owner proof, Teach structure maps, and validation gates.
- [Universal Design Principles](https://github.com/HDeibler/universal-design-principles) - Cross-agent UX and product-design marketplace with a root Codex collection plugin, five focused plugin bundles, and 137 Agent Skills for design review, accessibility, layout, interaction, cognition, and product polish.
- [VibePortrait](https://github.com/dadwadw233/VibePortrait) - Developer personality portrait generator — analyzes AI conversation history to produce MBTI type (16 color themes), capability radar, developer rating, 3-dimension famous match, and a persona skill that lets any AI "think like you".
- [Writer's Loop](https://github.com/xxsang/writers-loop) - Structured AI writing workflow for planning, critique, revision, translation, style distillation, and opt-in local preference learning.
### Tools & Integrations

- [Agent Message Queue](https://github.com/avivsinai/agent-message-queue) - File-based inter-agent messaging with co-op mode, cross-project federation, and orchestrator integrations.
- [Agent Vision](https://github.com/zfifteen/agent-vision) - macOS-only local camera plugin for explicit snapshots, streaming controls, and file-backed image input.
- [Apple Productivity](https://github.com/matk0shub/apple-productivity-mcp) - Local Apple Calendar and Reminders tooling for macOS with Codex plugin adapters.
- [AxonFlow](https://github.com/getaxonflow/axonflow-codex-plugin) - Runtime governance for Codex with policy enforcement on terminal commands, advisory checks for non-terminal tools via skills, PII/secret detection, and compliance-grade audit trails. Self-hosted via Docker.
- [Bitbucket CLI](https://github.com/avivsinai/bitbucket-cli) - Manage Bitbucket repos, PRs, branches, issues, webhooks, and pipelines for Data Center and Cloud.
- [Call-E](https://github.com/CALLE-AI/call-e-integrations) - Plan, run, and inspect Call-E phone call workflows from Codex through the calle CLI.
- [Canvas Apps Plugin Codex](https://github.com/Ratnam-Mishra/canvas-apps-plugin-codex) - Build and edit Microsoft Power Apps Canvas Apps using natural language and Canvas Authoring MCP server.
- [Chrome DevTools](https://github.com/win4r/chrome-devtools-codex-plugin) - One-click Codex plugin wrapper for chrome-devtools-mcp.
- [Codex Be Serious](https://github.com/lulucatdev/codex-be-serious) - Enforce formal, textbook-grade written register across all agent output.
- [Codex Mem](https://github.com/2kDarki/codex-mem) - Automatically capture, compress, and inject session context back into future Codex sessions.
- [Codex Obsidian](https://github.com/greg-asher/codex-obsidian) - Local Obsidian note and vault workflows through the official desktop `obsidian` CLI.
- [Codex SEO](https://github.com/BestLemoon/codex-seo) - Full-stack SEO audits, Google API workflows, backlinks analysis, reporting, and optional MCP extensions for Codex.
- [Codex Usage Tracker](https://github.com/douglasmonsky/codex-usage-tracker) - Track aggregate Codex token usage from local session logs with MCP tools for summaries, session detail, CSV export, and dashboard generation.
- [Context Pack](https://github.com/Rothschildiuk/context-pack) - Generate compact first-pass repository briefings for coding agents before deeper exploration.
- [Data Product Builder for dbt](https://github.com/entropy-data/dataproduct-builder-dbt) - Full data-product lifecycle on dbt for Entropy Data: scaffold, audit, and integrate projects with ODCS, ODPS, OpenLineage, and GitHub Actions.
- [Dodo Payments](https://github.com/dodopayments/dodo-agent-plugin) - Payments integration for checkouts, subscriptions, and billing with live API and documentation MCP servers with browser OAuth.
- [Education Agent Skills](https://github.com/GarethManning/education-agent-skills) - 131 evidence-based education skills for curriculum design, lesson planning, and assessment, with transparent evidence ratings and MCP server.
- [Flow Studio Power Automate](https://github.com/ninihen1/power-automate-mcp-skills) - Debug, build, and operate Power Automate flows via FlowStudio MCP with action-level inputs and outputs.
- [GH Project](https://github.com/zfifteen/gh-project-plugin) - Create GitHub repositories from Codex with inferred defaults, native menus, explicit confirmation, and deterministic local cloning.
- [Jenkins CLI](https://github.com/avivsinai/jenkins-cli) - GitHub CLI-style interface for Jenkins controllers with jobs, pipelines, runs, logs, artifacts, credentials, and nodes.
- [Kachilu Browser](https://github.com/kachilu-inc/kachilu-browser) - Anti-bot-aware browser automation for AI agents with MCP tools, CAPTCHA-aware workflows, and WSL2 Windows browser support.
- [KiCad Happy](https://github.com/aklofas/kicad-happy) - KiCad EDA skills for schematic analysis, PCB layout review, component sourcing, BOM management, and manufacturing preparation.
- [Langfuse Observability](https://github.com/avivsinai/langfuse-mcp) - Query traces, debug exceptions, analyze sessions, and manage prompts via MCP tools.
- [Launch Fast](https://github.com/BlockchainHB/launchfast_codex_plugin) - Official Launch Fast plugin adapter for rapid SaaS deployment.
- [Mobazha](https://github.com/mobazha/mobazha-skills) - Decentralized e-commerce skills — deploy self-hosted stores, import products from Shopify/Amazon, configure custom domains and Telegram bots, set up Tor privacy, and manage your store via MCP.
- [MorningAI](https://github.com/octo-patch/MorningAI) - AI news tracking skill that monitors 80+ entities across 6 sources (Reddit, HN, GitHub, Hugging Face, arXiv, X) and generates scored daily reports with infographics and message digests.
- [OC ChatGPT Multi Auth](https://github.com/ndycode/oc-chatgpt-multi-auth) - Codex setup skill and OpenCode plugin for ChatGPT Plus/Pro OAuth, GPT-5/Codex presets, and multi-account failover.
- [OpenProject](https://github.com/varaprasadreddy9676/team-codex-plugins) - Team collaboration via OpenProject integration.
- [OrgX](https://github.com/useorgx/orgx-codex-plugin) - MCP access and initiative-aware skills for organizational workflows.
- [PANews Agent Toolkit](https://github.com/panewslab/skills) - Crypto and blockchain news discovery, authenticated creator publishing workflows, and page-to-Markdown reading.
- [PapersFlow](https://github.com/papersflow-ai/papersflow-codex-plugin) - Paper discovery, citation verification, graph exploration, and DeepScan analysis.
- [prompt-to-asset](https://github.com/MohamedAbdallah-14/prompt-to-asset) - Route image-generation prompts to 30+ models (DALL-E, Stable Diffusion, Flux, Midjourney, and more) through a single MCP interface. Install: `npm install -g prompt-to-asset`.
- [Remotion Plugin](https://github.com/tim-osterhus/codex-remotion-plugin) - Build parameterized Remotion videos in Codex with the official Remotion docs MCP, composition scaffolding, and a data-driven launch-video workflow.
- [ru-text](https://github.com/talkstream/ru-text) - Russian text quality — ~1,040 rules for typography, info-style, editorial, UX writing, and business correspondence.
- [Rust Reverse Engineering](https://github.com/jingjing2222/rust-reverse-engineering-skill) - Reverse engineer Rust binaries and libraries: triage targets, demangle symbols, recover crate namespaces, and map panic, unwind, async, and FFI paths.
- [SeparateWeb Capture](https://github.com/AUN-PN/SeparateWeb) - Give Codex eyes on real webpages with full-page screenshots, UI crops, and JSON manifests for frontend visual QA.
- [sitemd](https://github.com/sitemd-cc/sitemd) - Build websites from Markdown via MCP — 22 tools for creating pages, generating content, validating, running SEO audits, configuring settings, and deploying static sites to Cloudflare Pages.
- [Synta MCP](https://github.com/Synta-ai/n8n-mcp-codex-plugin-synta) - Build, edit, validate, and self-heal n8n workflows with Synta MCP tools and Codex-ready workflow guidance.
- [Task Scheduler](https://github.com/6Delta9/task-scheduler-codex-plugin) - OpenAI Codex plugin and local MCP server for turning task lists into realistic schedules with blocked dates, capacity overrides, overflow tracking, and markdown planning output.
- [TokRepo Search](https://github.com/henu-wang/tokrepo-codex-plugin) - Search and install AI assets from TokRepo with a bundled skill and MCP server for Codex.
- [unslop](https://github.com/MohamedAbdallah-14/unslop) - Strip AI writing patterns from text output — removes filler phrases, hedging language, and generic constructs to produce cleaner written content. Install: `npm install -g unslop`.
- [Upwork Autopilot](https://github.com/klajdikkolaj/upwork-autopilot) - Controlled Upwork job search, qualification, and proposal submission sessions through a dedicated Chrome profile.
- [Yandex Direct](https://github.com/nebelov/yandex-direct-for-all) - GitHub-ready Codex plugin bundle for Yandex Direct, Wordstat, Metrika, and Roistat.


## Plugin Development

### Getting Started

- [Official Docs: Agent Skills](https://developers.openai.com/codex/skills) - The skill authoring format.
- [Official Docs: Build Plugins](https://developers.openai.com/codex/plugins/build) - Author and package plugins.
- [Plugin Structure](https://developers.openai.com/codex/plugins/build#create-a-plugin-manually) - `.codex-plugin/plugin.json` manifest format.

### Plugin Anatomy

```
my-plugin/
├── .codex-plugin/
│   └── plugin.json          # Required: name, version, description, skills path
├── skills/
│   └── my-skill/
│       ├── SKILL.md          # Required: skill instructions + metadata
│       ├── scripts/          # Optional: executable scripts
│       └── references/       # Optional: docs and templates
├── apps/                     # Optional: app integrations
└── mcp.json                  # Optional: MCP server configuration
```

### Plugin Creator

Use the built-in skill to scaffold a new plugin:

```
$plugin-creator
```

### Publishing

Currently no self-serve marketplace submission. Plugins are distributed via local marketplaces (`~/.agents/plugins/marketplace.json`), repo marketplaces (`$REPO_ROOT/.agents/plugins/marketplace.json`), or GitHub repos by pointing a marketplace source at a repo. OpenAI has stated third-party marketplace submissions are coming soon.

For this curated list, the machine-readable source of truth is the generated repo marketplace at `.agents/plugins/marketplace.json`. We keep the README for humans and `plugins.json` as a compatibility export for existing automation.

## Validate Before You Ship

After scaffolding with `$plugin-creator`, use [`plugin-scanner`](https://github.com/hashgraph-online/hol-guard) as your quality gate before publishing, review, or distribution.

For skill/plugin authoring workflows, [Codex SkillForge](https://github.com/f0d010c/skillforge) provides an ESLint-style CLI and GitHub Action for scaffolding, linting, smoke-testing, and packaging Codex skills/plugins before publishing.

### Local Preflight

```bash
pipx run plugin-scanner lint .
pipx run plugin-scanner verify .
```

### PR Gate (GitHub Actions)

```yaml
- uses: hashgraph-online/ai-plugin-scanner-action@v1
  with:
    plugin_dir: "."
    fail_on_severity: high
```

### Submission Preflight

Use scanner outputs as evidence for maintainers/reviewers:

- Structural lint results
- Publish-readiness verification output
- SARIF/findings for CI and code scanning

The score is best used as a quick trust signal and triage summary (not the only readiness signal).

## Guides & Articles

- [Codex Plugins, Visually Explained](https://adithyan.io/blog/codex-plugins-visual-explainer) - Visual walkthrough by @adithyan.
- [Codex Plugins: Slack, Figma, Google Drive](https://arstechnica.com/ai/2026/03/openai-brings-plugins-to-codex-closing-some-of-the-gap-with-claude-code/) - Ars Technica feature deep dive.
- [Codex v0.117.0 Plugin Walkthrough](https://reddit.com/r/codex/) - Reddit explainer.
- [OpenAI's Codex Gets Plugins](https://thenewstack.io/openais-codex-gets-plugins/) - The New Stack ecosystem overview.

## Related Projects

- [agentskills.io](https://agentskills.io) - Open agent skills standard.
- [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills#readme) - Cross-agent skill library (Claude, Codex, Cursor, Gemini).
- [awesome-ai-plugins](https://github.com/hashgraph-online/awesome-ai-plugins) - Umbrella list covering Codex, Claude Code, Gemini CLI, and MCP servers.
- [awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code#readme) - Claude Code resources.
- [awesome-coding-agents](https://github.com/e2b-dev/awesome-ai-agents#readme) - Curated list of AI coding agents.
- [awesome-mcp-servers](https://github.com/wong2/awesome-mcp-servers#readme) - MCP server directory.
- [EchoCoding](https://github.com/launsion-boop/EchoCoding) - Voice-enabled audio layer for coding agents with ambient soundscapes, event-driven SFX, and optional cloud TTS/ASR interaction.
- [Emdash Skills](https://github.com/megabytespace/claude-skills) - 14-category autonomous product-building OS for AI coding tools with 94 reference docs, 18 agents, and cross-tool support (Claude Code, Codex, Cursor, Copilot, 30+ more).
- [HOL Plugin Registry](https://hol.org/registry/plugins) - Browse plugins with scanner-backed security analysis and trust scores.

## Plugin Trust Scores

Every plugin in this list is automatically ingested by the [HOL Plugin Registry](https://hol.org/registry/plugins), which runs each through the [`plugin-scanner`](https://github.com/hashgraph-online/hol-guard) to produce a trust score and security analysis.

Each plugin gets a detailed breakdown across six factors:

- **Installability** - Can the plugin be installed and run without errors?
- **Maintenance** - Is the repo actively maintained with clear documentation?
- **MCP Posture** - How securely are MCP servers configured?
- **Plugin Security** - Does the manifest follow security best practices?
- **Provenance** - Can the publisher's identity be verified?
- **Publisher Quality** - Does the publisher have a track record of quality releases?

You can embed a trust badge in your plugin's README:

```
[![Plugin Name on HOL Registry (Trust Score)](https://img.shields.io/endpoint?url=https%3A%2F%2Fhol.org%2Fapi%2Fregistry%2Fbadges%2Fplugin%3Fslug%3DOWNER%252FREPO%26metric%3Dtrust%26style%3Dfor-the-badge%26label%3DPlugin+Name)](https://hol.org/registry/plugins/OWNER%2FREPO)
```

Replace `OWNER%2FREPO` with your plugin's GitHub owner and repo name (URL-encoded slash). Metrics available: `trust`, `security`. Styles: `flat`, `flat-square`, `plastic`, `for-the-badge`, `social`.

## Plugin Quality

If you received a scanner report on your repo, check the [Scanner Guide](SCANNER_GUIDE.md) for setup instructions, common fixes, and CI setup.


## Contributing

Contributions welcome! Please read the [contribution guidelines](CONTRIBUTING.md) first.

To add a plugin:

1. Fork this repo
2. Add your entry to the appropriate section following the existing format
3. Submit a PR

**Requirements:**

- Plugin must have a public GitHub repository
- Must include `.codex-plugin/plugin.json`
- Must be functional and well-documented
 
