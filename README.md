<p align="center">
  <br>
  <img width="80" src="https://cdn.rawgit.com/sindresorhus/awesome/d7305f38d29fed78fa85652e3a63e154dd8e8829/media/badge.svg" alt="Awesome">
  <br>
</p>

<h1 align="center">Awesome Codex Plugins</h1>

<p align="center">A curated list of awesome OpenAI Codex plugins, skills, and resources.</p>

<p align="center">
  <a href="https://hol.org/registry/plugins">
<img width="1672" height="941" alt="image" src="https://github.com/user-attachments/assets/9e063332-fd6c-4196-a8cb-e6880f8c06d1" />

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
- [Claim Your Plugin](#claim-your-plugin)
- [Plugin Trust Scores](#plugin-trust-scores)
- [Plugin Quality](#plugin-quality)
- [Contributing](#contributing)
---

## Start Here

New plugin workflow:

1. Create with `$plugin-creator`
2. **Validate with [`plugin-scanner`](https://github.com/hashgraph-online/hol-guard)** — **Required: score ≥ 80, no high/critical findings**
3. **Gate PRs with the [HOL scanner GitHub Action](https://github.com/hashgraph-online/ai-plugin-scanner-action)** — **Required for listing**
4. Ship or submit with confidence

### Quick preflight

```bash
pipx run plugin-scanner lint .
pipx run plugin-scanner verify .
```

### Scanner Requirements (Mandatory for This List)

All plugins submitted to **Awesome Codex Plugins** must pass the HOL AI Plugin Scanner:

| Requirement  | Threshold                                      |
| ------------ | ---------------------------------------------- |
| **Score**    | ≥ 80 / 130                                     |
| **Severity** | No critical or high findings                   |
| **CI**       | Scanner must run in your repo's GitHub Actions |

See the full guide: [`SCANNER_GUIDE.md`](./SCANNER_GUIDE.md)  
See contributing requirements: [`CONTRIBUTING.md`](./CONTRIBUTING.md)

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

- [A Team](https://github.com/RBraga01/a-team) - Universal multi-agent infrastructure with 25 specialist agents, 16 enforced workflow skills, and a lead orchestrator for Claude Code, Codex CLI, Cursor, and OpenCode.
- [Aegis](https://github.com/GanyuanRan/Aegis) - An agentic skills framework & software development methodology that works: planning, TDD, debugging, and collaboration workflows.
- [Agent Deck](https://github.com/not-so-fat/agent-deck) - One MCP for context management: bind self-improving playbooks, MCP tools, and API keys to the session.
- [Agent Guard](https://github.com/JeongJaeSoon/agent-guard) - Real-time secret-leak guardrails for AI coding agents (Claude Code, Codex), Git hooks, and CI.
- [Agent Harness Skills](https://github.com/yfge/agent-harness-skills) - Designs agent-ready repository harnesses with entrypoints, validation surfaces, runtime evidence, delivery records, and atomic commit guidance.
- [Agent Workflow System](https://github.com/1139030773-cmd/agent-workflow-system) - 一套中文AI工作流系统：7个协作技能 + 行为规范宪法 + 会话恢复机制，模糊目标→可执行任务，全生命周期引导。Codex & Claude Code 双平台，新手友好。
- [Agentizer](https://github.com/Humiris/wwa-transform) - Turn any website into an AI-powered agentfront with split-pane
- [AgentOps](https://github.com/boshu2/agentops) - DevOps layer for coding agents with flow, feedback, and memory that compounds between sessions.
- [AgentPack](https://github.com/vishal2612200/agentpack) - Ranks repo context for Codex with likely files, skill recommendations, agent rules, commands, warnings, and compact task-focused packs before editing.
- [Agentry Observability](https://github.com/fr33dr4g0n/agentry-public) - Agent-native product analytics, error logging, and deploy attribution for coding agents through one HTTP API.
- [AgiFlow](https://github.com/AgiFlow/ai-plugin) - Project management workflows for AI coding agents with planning, grooming, task execution, review, and AgiFlow MCP integration.
- [AIBoarding](https://github.com/gustavo-meilus/aiboarding) - Generate, maintain, compress, and audit standard AI-agent onboarding files with AGENTS.md, CLAUDE.md, drift tracking, and lifecycle hooks.
- [Alcove](https://github.com/epicsagas/alcove) - Local-first MCP server for private project docs with hybrid BM25+vector search, tree-sitter code indexing, and automated linting for team-wide documentation standards.
- [Anchor](https://github.com/biefan/anchor) - Engineering discipline pack for Claude Code & Codex CLI with task-scope locking, anti-drift braking, condition-based codex review, project-CLAUDE.md pitfall writeback, and PreToolUse hooks that block irreversible bash patterns.
- [Antigravity Workspace Template](https://github.com/study8677/antigravity-workspace-template) - Multi-agent codebase knowledge graph generator with context-aware planning and automatic scope management — turns codebases into coherent agent workspaces.
- [Archcore](https://github.com/archcore-ai/plugin) - Gives coding agents the architecture, rules, and prior decisions of the repo via skills, hooks, and MCP — so new changes land where the project says they belong across Claude Code, Cursor, and Codex CLI.
- [ArmorCodex](https://github.com/armoriq/armorCodex) - Intent-based security for Codex with MCP plan registration, policy gating, CSRG cryptographic proofs, and audit logging on `bash` and `apply_patch`.
- [BABOK Analyst](https://github.com/GSkuza/BABOK_ANALYST) - BABOK v3 business analysis agent with 16 MCP tools, a 9-stage pipeline, and human-in-the-loop approval gates.
- [BGS Modding Superpowers](https://github.com/BB-84C/bgs-modding-superpowers) - Agentic Bethesda Game Studio modpack curation toolkit with MCP-driven xEdit conflict audit, MO2 control plane, BA2/BSA and Papyrus tooling, and skills for setup, dev-log, and release-changelog workflows.
- [Boss](https://github.com/echoVic/boss-skill) - BMAD pipeline plugin that orchestrates a full requirements-to-deploy workflow across nine specialist agents with an auditable runtime DAG and quality gates, for Claude Code, Codex, OpenClaw, and Antigravity.
- [Bring Your AI Migration Auditor](https://github.com/unitedideas/bringyour-mcp) - Read-only Codex plugin for auditing Claude Code to Codex migrations before Codex edits code. Checks AGENTS.md/CLAUDE.md scope, hooks, MCP config, skills, secret references, and validation notes.
- [Brooks Lint](https://github.com/hyhmrright/brooks-lint) - AI code reviews grounded in six classic engineering books — decay risk diagnostics with book citations, severity labels, and four analysis modes (PR review, architecture audit, tech debt, test quality).
- [Casefile](https://github.com/x4cc3/casefile) - Persistent security case tracking for bug bounties, CTFs, and security audits.
- [Changelog Forge](./plugins/mturac/changelog-forge) - Conventional commits → CHANGELOG section + semver bump.
- [Claude Code Codex Plugin](https://github.com/davidq888/claude-code-codex-plugin) - Security-focused Codex plugin that connects to the local Claude Code CLI through MCP with login, status checks, safe-mode prompts, and no credential storage.
- [Claude Code for Codex](https://github.com/sendbird/cc-plugin-codex) - Reverse of OpenAI's official Claude-hosted plugin: use Claude Code from Codex for reviews, rescue tasks, tracked background jobs, and hook-powered review gates.
- [Claude Code Harness](https://github.com/dadwadw233/claude-code-harness) - Harness blueprint skill for turning vague agent ideas into concrete designs for request assembly, control loops, memory, permissions, recovery, and extension planes.
- [Claude Code Skills](https://github.com/alirezarezvani/claude-skills) - 223 production-ready skills, 23 agents, and 298 Python tools across 9 domains — engineering, marketing, product, compliance, and more.
- [Claude Octopus](https://github.com/nyldn/claude-octopus) - Multi-LLM orchestration dispatching to 8 providers (Codex, Gemini, Copilot, Qwen, Perplexity, OpenRouter, Ollama, OpenCode) with Double Diamond workflows, adversarial review, and safety gates.
- [Clean Room](https://github.com/whit3rabbit/clean-room-skill) - Spec-first clean-room workflow for authorized source analysis, behavioral specs, role separation, and verification without replacement code.
- [Codebase Recon](https://github.com/yujiachen-y/codebase-recon-skill) - Analyze git history to understand a codebase before reading any code — auto-scales by repo size and cross-references hotspots with bug magnets to surface high-risk files, bus factor, and team momentum.
- [CodeTruss](https://github.com/DeliriumPulse/codetruss-plugins) - Local-first acceptance gate that checks coding-agent scope, sensitive surfaces, deterministic analyzers, and repository verification from immutable Git snapshots, then writes signed receipts before the PR.
- [Codex Agenteam](https://github.com/yimwoo/codex-agenteam) - Specialist AI agents (researcher, PM, architect, developer, QA, reviewer) orchestrated as a configurable team pipeline.
- [Codex Multi Auth](https://github.com/ndycode/codex-multi-auth) - Multi-account OAuth manager for the official Codex CLI with switching, health checks, and recovery tools.
- [Codex Process Jobs](https://github.com/joelfarthing/codex-process-jobs) - Run long local builds, tests, benchmarks, and inference jobs as durable detached processes with tracked status, bounded results, and completion delivery across Codex surfaces.
- [Codex Reviewer](https://github.com/schuettc/codex-reviewer) - Second-pass review of Claude-driven plans and implementations.
- [Codex rg Guard](https://github.com/Rycen7822/codex-rg-guard) - Budgeted `rg`/`grep` replacement for Codex that narrows broad searches before they waste model context.
- [Codex Skin Pack Installer](https://github.com/ChannelerH/codex-skin-packs) - Codex plugin and Skill that stages verified desktop skin packs from GitHub releases, validates files, and keeps restore guidance visible.
- [Codex TUI Proof](https://github.com/bnc4vk/codex-tui-proof) - Visually validate real local terminal UIs in Codex's in-app browser with screenshots and session evidence.
- [Commit Narrator](./plugins/mturac/commit-narrator) - Generate semantic commit message from staged diff, including the _why_.
- [debt-ops](https://github.com/bcanfield/agentic-tech-debt) - Catches AI-introduced tech debt at write-time: hooks log every deferral to a registry in your repo and a review skill ranks paydown by file churn.
- [Deps Doctor](./plugins/mturac/deps-doctor) - Multi-ecosystem dependency audit (npm, pip, cargo, go) in one report.
- [Designer Skill](https://github.com/Pythoughts-labs/designer-skill) - Plug-and-play MCP that gives your agent UI superpowers. One install: design skill + MCP server, zero config.
- [Dev Skills](https://github.com/Jason-chen-coder/dev-skills) - Team workflow skills for specs, plans, TDD, debugging, verification, review, branch finishing, and design context.
- [Development Skills](https://github.com/reidemeister94/development-skills) - Three-tier triage (PASS_THROUGH / LIGHT / FULL 4-phase) development workflow for Codex and Claude Code with language auto-detection (Python, Java, TypeScript, Swift, frontend) and a staff-reviewer subagent for fresh-eyes review on every change.
- [Ditto](https://github.com/ohad6k/ditto) - Mines selected evidence from local coding-agent sessions into private work, design, and writing profiles for Codex, Claude Code, and GitHub Copilot.
- [Docflow](https://github.com/MedAdemBHA/docflow) - Lightweight documentation memory for AI coding agents that scaffolds a 7-category docs tree, runs readiness checks, validates docs before finishing, and keeps a monthly changelog across Claude Code and Codex.
- [ejentum-mcp](https://github.com/ejentum/ejentum-mcp) - MCP server exposing reasoning, code, anti-deception, and memory harness tools for Codex.
- [Env Lint](./plugins/mturac/env-lint) - `.env` vs `.env.example` key parity — never prints values.
- [Epic Harness](https://github.com/epicsagas/epic-harness) - Auto-trigger quality skills + self-evolving agent harness — orbit (spec-to-ship), evolve (skill mutation), team (multi-agent), TDD, check, ship, simplify, debug, perf, secure.
- [Espresso](https://github.com/mirkobozzetto/espresso) - Full token-saving stack in one plugin - output compression, global rules, RTK hook, Caveman ultra, GitNexus config. Detects existing setup, installs only what's missing. Works on Claude Code and Codex.
- [Flaky Detector](./plugins/mturac/flaky-detector) - Run a test command N times, report per-test flakiness %.
- [Frappe Agent](https://github.com/Dkm0315/frappe-agent) - Frappe and ERPNext coding, customization, bench, and review intelligence for Codex.
- [GCF Proxy](https://github.com/blackwell-systems/gcf-codex-plugin) - Save 71% on MCP tool call tokens by wrapping any server with GCF encoding, with session stats hook and setup skill.
- [Generative Media Skills](https://github.com/SamurAIGPT/Generative-Media-Skills) - 13 skills for image, video, and audio generation using 100+ models - FLUX, Midjourney v7, Veo3, Kling 3.0, Suno, and HunyuanVideo via muapi.ai.
- [GrayMatter](https://github.com/ValkyrLabs/GrayMatter) - Durable memory and shared graph state for Codex and OpenClaw agents, with live ValkyrAI schema awareness.
- [Hera Agent Godot](https://github.com/NotNull92/hera-agent-godot) - Drives a live Godot 4.x editor through the low-token Hera CLI — scene, node, and signal edits, play control, and runtime QA with verifiable compact JSON output, with the companion addon published on the official Godot Asset Store.
- [Hera Agent Unity](https://github.com/NotNull92/hera-agent-unity) - Controls and verifies a live Unity Editor through a low-token CLI, with scene, asset, Inspector, Play Mode, test, screenshot, and runtime C# workflows for Codex and other coding agents.
- [HOL Guard Plugin](https://github.com/hashgraph-online/hol-guard-plugin) - AI antivirus workflow for Codex, Claude Code, Cursor, Gemini, OpenCode, MCP servers, skills, and plugin release checks with local approvals and receipts.
- [Honcho](https://github.com/plastic-labs/codex-honcho) - Persistent cross-session memory for Codex powered by Honcho — lifecycle hooks capture each session and inject relevant context back at session start, so Codex remembers your preferences, projects, and decisions across restarts.
- [HOTL Plugin](https://github.com/yimwoo/hotl-plugin) - Human-on-the-Loop AI coding workflow plugin for Codex, Claude Code, and Cline with structured planning, review, and verification guardrails.
- [Krypton](https://github.com/jturntdev/krypton) - Goal-based planning and proof gate for Codex and Claude Code that turns requests into ownership, cutover, review-gate, and acceptance-evidence plans.
- [LLM Transpile](https://github.com/epicsagas/llm-transpile) - Auto-compress .md, .html, and .txt files via PostToolUse hook, cutting context usage by up to 40% with zero workflow change.
- [LVTD Skills](https://github.com/LVTD-LLC/skills) - Reusable Agent Skills for Codex, Claude Code, and compatible clients, covering Django, Rust, Cookiecutter, SEO, traction, product marketing, and nonfiction publishing workflows.
- [Maestro](https://github.com/mbanderas/maestro) - Opt-in local multi-CLI fusion engine and orchestration doctrine that fans a prompt across model CLIs, then judges and synthesizes one grounded answer.
- [MailAgent](https://github.com/Alex0nder/MailAgent) - Temporary inboxes for Codex — OTP, magic links, signup QA, simulate-first autotests (23 MCP tools).
- [memi](https://github.com/sarveshsea/memi) - Interface understanding and design-system memory for Codex, Claude Code, Cursor, and MCP agents with UI audits, Tailwind token extraction, shadcn registry workflows, and a bundled Codex plugin.
- [Ontoly](https://github.com/0xsarwagya/ontoly-codex-plugin) - Deterministic Software Graph workflows for Codex: architecture review, dependency analysis, request tracing, configuration analysis, and impact analysis.
- [Open Dynamic Workflows](https://github.com/Suraj1235/open-dynamic-workflows) - Local-first MIT dynamic multi-agent workflows for Codex, OpenCode, Antigravity, Cursor, and VS Code with a daemon, MCP bridge, Codex skills, OpenCode plugin, and bring-your-own-model support.
- [Personal Data Protection](https://github.com/AltByteSG/personal-data-protection-skill) - Engineer-facing personal-data-protection compliance reference — Singapore PDPA, Thailand PDPA, Indonesia UU PDP, Malaysia PDPA (Act 709 + 2024 Amendments), Philippines DPA — organised by where in the stack each obligation lands, with checklists, breach-response runbook, and a developer-view divergence table across all five.
- [PR Storyteller](./plugins/mturac/pr-storyteller) - PR title + body + test plan from commits and diff vs base branch.
- [Praxis](https://github.com/ouonet/praxis) - Intent-driven workflow skills for coding agents: describe what done looks like, not the steps. Triage-first design keeps token costs low across design, TDD, debug, review, and release.
- [Project Autopilot](https://github.com/AlexMi64/codex-project-autopilot) - Turn an idea into a structured project workflow with planning, execution, verification, and handoff.
- [Quality Engineering Skills](https://github.com/RBraga01/Quality-Engineering-Skills) - 22 structured quality engineering skills for automotive and manufacturing: ISO 9001, IATF 16949, AIAG-VDA FMEA, VDA 6.3, PPAP, APQP, SPC, MSA.
- [RAG Reviewer](https://github.com/mimfort/rag_for_git) - Agentic PR review: hybrid RAG + code graph via MCP, review skills for Codex.
- [Registry Broker](https://github.com/hashgraph-online/registry-broker-codex-plugin) - Delegate tasks to specialist AI agents via the HOL Registry, plan, find, summon, and recover sessions.
- [Reviewable HTML Workbench](https://github.com/u-ichi/reviewable-html-workbench) - Generate reviewable HTML documents, serve previews, collect inline review comments, and feed review outcomes back into agent workflows.
- [River Review](https://github.com/s977043/river-review) - Versioned Skill Registry of code-review skills driven by a perspective-based review agent (code, security, performance, architecture, testing, adversarial) that verifies findings against the diff.
- [RoadmapSmith](https://github.com/PapiScholz/roadmapsmith) - Evidence-backed ROADMAP.md workflows for AI coding agents with validation, sync, and roadmap generation across any tech stack.
- [Runtype Skills](https://github.com/runtypelabs/skills) - Supercharge your coding agent for AI product development — build, deploy, and operate agents, flows, tools, and surfaces on Runtype's managed edge runtime.
- [Sealos](https://github.com/labring/sealos-skills) - Deploy apps to Sealos Cloud from Codex with readiness checks, Dockerfile generation, Compose conversion, image builds, and rollout updates.
- [Secret Guard](./plugins/mturac/secret-guard) - Pre-commit secret scanner using pattern and entropy detection.
- [Session Orchestrator](https://github.com/Kanevry/session-orchestrator) - Session orchestration for Claude Code, Codex, and Cursor IDE — structured planning, wave-based execution, VCS integration (GitLab + GitHub), quality gates, and clean session close-out with issue tracking.
- [Simple Man](https://github.com/Maksim-Burtsev/simple-man) - High-compression communication mode for Codex agents that removes filler while preserving search, validation, and implementation effort.
- [Spec-Driven Development](https://github.com/Habib0x0/spec-driven-plugin) - Three-phase Requirements → Design → Tasks workflow for Claude Code and Codex — EARS notation acceptance criteria, autonomous execution loop, cross-spec dependencies, and post-implementation acceptance testing.
- [spec-superflow](https://github.com/MageByte-Zero/spec-superflow) - Spec-first workflow with nine skills, auditable recovery commands, guarded workflow-path recommendations, Node 20 support, and evidence-based review gates.
- [Spellbook Skills](https://github.com/yyykf/spellbook-skills) - Practical Claude Code and Codex skills for worktrees, PR/MR automation, review cleanup, YApi lookup, and Java DDD guidance.
- [Staff Engineer Mode](https://github.com/sirmarkz/staff-engineer-mode) - Routes engineering design, delivery, reliability, security, operations, and maintenance prompts to focused staff-level specialist guidance for AI coding agents.
- [Standup Generator](./plugins/mturac/standup-gen) - Daily standup notes from git activity across repos.
- [Stark](https://github.com/f0d010c/stark) - UI/UX design plugin for AI coding agents with product-flow routing, platform-native interface guidance, asset planning, and shipped-reference analysis before code.
- [Superloopy](https://github.com/beefiker/superloopy) - Evidence-gated Codex loop harness with specialist skills, including near-pixel authorized website cloning backed by screenshots, assets, build output, and visual QA.
- [Superpipelines](https://github.com/gustavo-meilus/superpipelines) - Design and run write/review-isolated multi-agent AI pipelines across Codex, Claude Code, OpenCode, Cursor, Windsurf, and Cline.
- [tailtest](https://github.com/avansaber/tailtest-codex) - Hook-powered test generation -- detects files changed during an agent turn and instructs Codex to write and run tests automatically. Zero config, 8 languages.
- [Tandem Workflow Architect](https://github.com/frumu-ai/tandem-codex-plugin) - Plan Tandem workflows in Codex, then validate, preview, and run them through the governed Tandem engine.
- [Tartiner Labs](https://github.com/tartinerlabs/skills) - Agent skills for git workflows, GitHub automation, security audits, code refactoring, and project tooling.
- [Team Skills Platform](https://github.com/Colin4k1024/tsp) - Role-based team delivery framework — Tech Lead-orchestrated 8-role system with 195+ skills, 27 specialist agents, 80+ commands, hooks, and ECC harness for Claude Code, Codex, and OpenCode.
- [Test Gap](./plugins/mturac/test-gap) - Find lines in your diff lacking test coverage (Cobertura, lcov, coverage.json).
- [TODO Harvest](./plugins/mturac/todo-harvest) - TODO/FIXME/HACK scan with `git blame` author + age.
- [token-optimizer](https://github.com/ooples/token-optimizer-mcp) - Cut token usage 60-90% with caching, compression, and smart file tools — diff-only re-reads, paths-only search, out-of-context stashing, and a per-tool savings report for Codex and Claude Code.
- [Tool Advisor](https://github.com/dragon1086/claude-skills) - Read-only meta-skill that scans your MCP servers, skills, plugins, and CLI tools, then suggests up to three ranked approaches (Methodical / Fast / Deep) with a copy-paste Quick Action table.
- [Tree Ring Memory](https://github.com/TerminallyLazy/tree-ring-memory-codex-plugin) - Local-first memory lifecycle guidance for Codex agents with recall, evidence-backed lessons, privacy-safe memory capture, audit, consolidation, and explicit forgetting.
- [UIZZE](https://github.com/samuelbushi/uizze) - STOP UI SLOP. Gives Codex 800,000+ real web and iOS screens, a product-specific design contract, and a hard finish gate before generic UI ships; connect it at https://uizze.com.
- [Unforgit](https://github.com/MiguelMedeiros/unforgit-codex-plugin) - Git-backed repository memory for Codex and other coding agents via MCP, with durable local knowledge for decisions, conventions, gotchas, and playbooks.
- [Unity Agent Workflows](https://github.com/AUN-PN/unity-agent-workflows) - Codex plugin and skill for Unity 2D agents that enforces "No proof, no edit" workflows with runtime-owner proof, Teach structure maps, and validation gates.
- [Universal Design Principles](https://github.com/HDeibler/universal-design-principles) - Cross-agent UX and product-design marketplace with a root Codex collection plugin, five focused plugin bundles, and 137 Agent Skills for design review, accessibility, layout, interaction, cognition, and product polish.
- [Velith](https://github.com/epicsagas/Velith) - AI-native publishing system with a 6-phase pipeline from ideation to EPUB/PDF across 8 genres.
- [VibePortrait](https://github.com/dadwadw233/VibePortrait) - Developer personality portrait generator — analyzes AI conversation history to produce MBTI type (16 color themes), capability radar, developer rating, 3-dimension famous match, and a persona skill that lets any AI "think like you".
- [VillageSQL Skills](https://github.com/villagesql/villagesql-skills) - Skills for VillageSQL including building extensions from scratch and porting PostgreSQL extensions to VillageSQL.
- [Waggle](https://github.com/Abhigyan-Shekhar/Waggle-mcp) - Persistent graph-backed conversational memory for Codex that recalls project decisions, constraints, preferences, and outcomes across sessions.
- [Wingman](https://github.com/lsshym/wingman.ai) - Cross-platform AI coding-agent plugin for repo-local project memory, data-contract checks, and project-map discovery before agents edit code.
- [Workflow Kit](https://github.com/Le-Xuan-Thang/workflow-kit) - Full product lifecycle plugin for Claude Code, Codex CLI, and OpenCode: define Vision/Mission/Core → generate workplan → execute with mandatory cross-provider reviewer agents → synthesize deliverables → maintain, with parallel task execution, crash recovery, and AgentOps metrics.
- [Writer's Loop](https://github.com/xxsang/writers-loop) - Structured AI writing workflow for planning, critique, revision, translation, style distillation, and opt-in local preference learning.
- [Zagrosi Forge](https://github.com/zagrosi-code/zagrosi-forge) - Decompose broad project briefs into researched plans and implement sectioned work with TDD, quality gates, and traceability.

### Tools & Integrations

- [Agent Message Queue](https://github.com/avivsinai/agent-message-queue) - File-based inter-agent messaging with co-op mode, cross-project federation, and orchestrator integrations.
- [Agent Vision](https://github.com/zfifteen/agent-vision) - macOS-only local camera plugin for explicit snapshots, streaming controls, and file-backed image input.
- [Agentgram](https://github.com/jerryfane/agentgram) - Send explicit Telegram messages from Codex and local AI agents through a Telegram bot token and chat id.
- [AgentGuards](https://github.com/alelaguard/agentguards-plugins) - LLM security guardrails for Codex with enforcing hooks and MCP tools: jailbreak and prompt-injection detection, web-content scanning, data-exfiltration blocking, and destructive-command authorization.
- [Aient](https://github.com/aient-ai/aient-codex-plugin) - AI operations plugin for Codex that connects production telemetry, problem lifecycle context, and remediation workflows through Aient's MCP server.
- [Antigravity 2.0](https://github.com/comprono/antigravity-2-codex-plugin) - Local Codex bridge for Antigravity desktop with setup checks, model limit summaries, DevTools UI automation, and safe project/chat handoff.
- [Apple Productivity](https://github.com/matk0shub/apple-productivity-mcp) - Local Apple Calendar and Reminders tooling for macOS with Codex plugin adapters.
- [AutoCAD Tianzheng Tools](https://github.com/summer521521/AutoCAD_Tianzheng_plugin) - Connects Codex to AutoCAD and Tianzheng HVAC through a local MCP server for DWG-aware HVAC drawing inspection and workflow automation.
- [AxonFlow](https://github.com/getaxonflow/axonflow-codex-plugin) - Runtime governance for Codex with policy enforcement on terminal commands, advisory checks for non-terminal tools via skills, PII/secret detection, and compliance-grade audit trails. Self-hosted via Docker.
- [Bitbucket CLI](https://github.com/avivsinai/bitbucket-cli) - Manage Bitbucket repos, PRs, branches, issues, webhooks, and pipelines for Data Center and Cloud.
- [Call-E](https://github.com/CALLE-AI/call-e-integrations) - Plan, run, and inspect Call-E phone call workflows from Codex through the calle CLI.
- [Canvas Apps Plugin Codex](https://github.com/Ratnam-Mishra/canvas-apps-plugin-codex) - Build and edit Microsoft Power Apps Canvas Apps using natural language and Canvas Authoring MCP server.
- [CarsXE](https://github.com/carsxe/carsxe-codex-plugin) - Decode VINs, license plates, market value, vehicle history, recalls, liens, OBD codes, and more via the CarsXE API.
- [Chrome DevTools](https://github.com/win4r/chrome-devtools-codex-plugin) - One-click Codex plugin wrapper for chrome-devtools-mcp.
- [claude-math](https://github.com/vladimirrott/claude-math) - Emit mathematics as copy- and search-safe inline Unicode (∑, ≤, ℝ, x², matrices, set-builder) instead of LaTeX so equations stay legible in the Codex TUI, terminals, and Claude Code.
- [Codex Be Serious](https://github.com/lulucatdev/codex-be-serious) - Enforce formal, textbook-grade written register across all agent output.
- [Codex Mem](https://github.com/2kDarki/codex-mem) - Automatically capture, compress, and inject session context back into future Codex sessions.
- [Codex Obsidian](https://github.com/greg-asher/codex-obsidian) - Local Obsidian note and vault workflows through the official desktop `obsidian` CLI.
- [Codex SEO](https://github.com/BestLemoon/codex-seo) - Full-stack SEO audits, Google API workflows, backlinks analysis, reporting, and optional MCP extensions for Codex.
- [Codex Usage Tracker](https://github.com/douglasmonsky/codex-usage-tracker) - Track aggregate Codex token usage from local session logs with MCP tools for summaries, session detail, CSV export, and dashboard generation.
- [CONTAM Tools](https://github.com/summer521521/CONTAM_plugin) - Runs and inspects CONTAM airflow projects through a local MCP server with project guards, diagnostics, simulation helpers, and bridge workflows.
- [Context Pack](https://github.com/Rothschildiuk/context-pack) - Generate compact first-pass repository briefings for coding agents before deeper exploration.
- [Coolify](https://github.com/Sevi-py/coolify-codex-plugin) - Control Coolify Cloud and self-hosted Coolify instances through API-aware workflow skills and local tools.
- [Data Product Builder for dbt](https://github.com/entropy-data/dataproduct-builder-dbt) - Full data-product lifecycle on dbt for Entropy Data: scaffold, audit, and integrate projects with ODCS, ODPS, OpenLineage, and GitHub Actions.
- [Digital Marketing Pro](https://github.com/indranilbanerjee/digital-marketing-pro) - Open-source AI marketing plugin for agencies — 154 skills, 25 specialist agents, 12-Part Strategy Flow, AEO/GEO, GSC AI Performance Report, Google Ads API v24, EU AI Act Article 50 / C2PA compliance.
- [Dodo Payments](https://github.com/dodopayments/dodo-agent-plugin) - Payments integration for checkouts, subscriptions, and billing with live API and documentation MCP servers with browser OAuth.
- [Education Agent Skills](https://github.com/GarethManning/education-agent-skills) - 131 evidence-based education skills for curriculum design, lesson planning, and assessment, with transparent evidence ratings and MCP server.
- [Exa Web Search](https://github.com/zlsbksdxl/codex-exa) - Search and fetch current web sources in Codex through the official Exa MCP server with browser OAuth.
- [Feishu to Codex](https://github.com/zlsbksdxl/codex-lark) - Connect Codex to Feishu/Lark workflows for Docs, Messenger, Drive, Sheets, Base, Calendar, Tasks, Meetings, Mail, approvals, and more through the official Lark CLI.
- [Flow Studio Power Automate](https://github.com/ninihen1/power-automate-mcp-skills) - Debug, build, and operate Power Automate flows via FlowStudio MCP with action-level inputs and outputs.
- [GH Project](https://github.com/zfifteen/gh-project-plugin) - Create GitHub repositories from Codex with inferred defaults, native menus, explicit confirmation, and deterministic local cloning.
- [Hermes Tweet](https://github.com/Xquik-dev/hermes-tweet) - Hermes Agent X/Twitter plugin for read-first social research, monitoring, and approval-gated actions through Xquik.
- [Jenkins CLI](https://github.com/avivsinai/jenkins-cli) - GitHub CLI-style interface for Jenkins controllers with jobs, pipelines, runs, logs, artifacts, credentials, and nodes.
- [Kachilu Browser](https://github.com/kachilu-inc/kachilu-browser) - Anti-bot-aware browser automation for AI agents with MCP tools, CAPTCHA-aware workflows, and WSL2 Windows browser support.
- [KiCad Happy](https://github.com/aklofas/kicad-happy) - KiCad EDA skills for schematic analysis, PCB layout review, component sourcing, BOM management, and manufacturing preparation.
- [Kreuzberg](https://github.com/kreuzberg-dev/plugins) - Local document extraction for 91+ formats with skills for CLI usage, OCR, table extraction, output formats, and a local MCP server.
- [Kreuzberg Cloud](https://github.com/kreuzberg-dev/plugins) - Managed document extraction for Codex with API-key setup, presigned uploads, job tracking, webhook workflows, and usage guidance.
- [Kreuzcrawl](https://github.com/kreuzberg-dev/plugins) - Web crawling and scraping for Codex with skills for single-page scraping, site crawls, URL mapping, and headless browser fallback.
- [Langfuse Observability](https://github.com/avivsinai/langfuse-mcp) - Query traces, debug exceptions, analyze sessions, and manage prompts via MCP tools.
- [Launch Fast](https://github.com/BlockchainHB/launchfast_codex_plugin) - Official Launch Fast plugin adapter for rapid SaaS deployment.
- [LinkedIn Skills](https://github.com/sergebulaev/linkedin-skills) - Codex-ready LinkedIn marketing bundle with a native .codex-plugin manifest and 10 skills: post writing with 16 tested hook formulas, AI-tell humanizer, pre-publish audit, comment and reply drafting, hook extraction, content planning, profile optimization, engager analytics, and thread monitoring; also works in Claude Code.
- [Maestro: Costguard](https://github.com/mbanderas/costguard) - Cost auditor for Codex that flags CI/cron and cloud-spend waste via read-only provider checks, then previews and applies surgical CI workflow fixes locally without writing to provider accounts or pushing git.
- [Mantis](./plugins/deonmenezes/mantishack) - Autonomous bug bounty hunter for authorized engagements — 7-phase FSM (RECON → AUTH → HUNT → CHAIN → VERIFY → GRADE → REPORT), parallel hunter sub-agents, cryptographic scope enforcement, and BLAKE3/Ed25519 Merkle event logs.
- [MATLAB Simulink Tools](https://github.com/summer521521/MATLAB_Simulink_plugin) - Connects Codex to MATLAB and Simulink through a local MCP server for model inspection, script execution, and engineering workflow automation.
- [Mobazha](https://github.com/mobazha/mobazha-skills) - Decentralized e-commerce skills — deploy self-hosted stores, import products from Shopify/Amazon, configure custom domains and Telegram bots, set up Tor privacy, and manage your store via MCP.
- [MorningAI](https://github.com/octo-patch/MorningAI) - AI news tracking skill that monitors 80+ entities across 6 sources (Reddit, HN, GitHub, Hugging Face, arXiv, X) and generates scored daily reports with infographics and message digests.
- [Nullcost](https://github.com/johnvouros/nullcost-plugin) - Catalog-backed free-tier, free-trial, and cheap developer-tool recommendations for Codex through bundled skills and MCP tools.
- [OC ChatGPT Multi Auth](https://github.com/ndycode/oc-chatgpt-multi-auth) - Codex setup skill and OpenCode plugin for ChatGPT Plus/Pro OAuth, GPT-5/Codex presets, and multi-account failover.
- [OpenProject Codex](https://github.com/varaprasadreddy9676/openproject-codex-plugin) - OpenProject integration for Codex with project, team, work package, bulk workflow, boards, wiki, meeting, attachment, and reporting support.
- [Ophis](https://github.com/ophis-fi/skills) - Onchain token swaps for Codex via the hosted Ophis MCP server, MEV-protected and gasless, built on CoW Protocol.
- [OrgX](https://github.com/useorgx/orgx-codex-plugin) - MCP access and initiative-aware skills for organizational workflows.
- [PANews Agent Toolkit](https://github.com/panewslab/skills) - Crypto and blockchain news discovery, authenticated creator publishing workflows, and page-to-Markdown reading.
- [PapersFlow](https://github.com/papersflow-ai/papersflow-codex-plugin) - Paper discovery, citation verification, graph exploration, and DeepScan analysis.
- [PDF Monster](https://github.com/jbaehova/pdf-monster) - Analyzes PDFs as extracted text, OCR text, rendered page images, and embedded figures for coding agents.
- [plori](https://github.com/plori-ai/codex-plugin) - Create and drive plori cloud agents (each an AI agent on its own cloud computer) over plori's remote MCP server, with OAuth auto-discovery.
- [prompt-to-asset](https://github.com/MohamedAbdallah-14/prompt-to-asset) - Route image-generation prompts to 30+ models (DALL-E, Stable Diffusion, Flux, Midjourney, and more) through a single MCP interface. Install: `npm install -g prompt-to-asset`.
- [Pronounce](https://github.com/anzy-renlab-ai/pronounce) - Pronounce developer jargon out loud: an MCP server (lookup/search) and skill backed by a 1,721-entry sourced dictionary with IPA, audio, and cited pronunciations for kubectl, nginx, YAML, JWT, and more.
- [Remotion Plugin](https://github.com/tim-osterhus/codex-remotion-plugin) - Build parameterized Remotion videos in Codex with the official Remotion docs MCP, composition scaffolding, and a data-driven launch-video workflow.
- [ru-text](https://github.com/talkstream/ru-text) - Russian text quality — ~1,044 rules for typography, info-style, editorial, UX writing, and business correspondence.
- [Rust Reverse Engineering](https://github.com/jingjing2222/rust-reverse-engineering-skill) - Reverse engineer Rust binaries and libraries: triage targets, demangle symbols, recover crate namespaces, and map panic, unwind, async, and FFI paths.
- [ScrapeGraph AI](https://github.com/ScrapeGraphAI/just-scrape) - AI-powered web scraping CLI to search, scrape, extract structured JSON, crawl, and monitor web pages via the ScrapeGraph AI API.
- [SEO Dungeon](https://github.com/avalonreset/seo-dungeon) - Gamified local SEO audits that turn website issues into 16-bit dungeon battles for Codex, Claude, and Gemini CLI workflows.
- [Shots](https://github.com/hitSlop/shots) - Agent-native App Store screenshot, app icon, ASO, and localization workflows through the hosted Shots MCP server.
- [sitemd](https://github.com/sitemd-cc/sitemd) - Build websites from Markdown via MCP — 22 tools for creating pages, generating content, validating, running SEO audits, configuring settings, and deploying static sites to Cloudflare Pages.
- [SolidWorks GPT Plugin](https://github.com/Erfouni/solidworks-GPT-plugin) - Knowledge-backed SolidWorks design and validation workflows for Codex with standards lookup, CAD evidence gates, and consent-based session learning.
- [Synta MCP](https://github.com/Synta-ai/n8n-mcp-codex-plugin-synta) - Build, edit, validate, and self-heal n8n workflows with Synta MCP tools and Codex-ready workflow guidance.
- [Taisly Agent Kit](https://github.com/taisly/agent) - Publish short-form videos to TikTok, Instagram Reels, YouTube Shorts, X, and Facebook from Codex with the Taisly MCP server and bundled social media posting skill.
- [Task Scheduler](https://github.com/6Delta9/task-scheduler-codex-plugin) - OpenAI Codex plugin and local MCP server for turning task lists into realistic schedules with blocked dates, capacity overrides, overflow tracking, and markdown planning output.
- [Thermal-Fluid Research Workflow](https://github.com/hanhuark/mechanical-engineering-research-skill) - Thermal-fluid mechanical engineering research workflow for literature review, technical writing, data analysis, presentations, proposals, coding, and AI/ML tools.
- [Token Harbor](https://github.com/NickHOI/Token-Harbor) - Turn Codex token usage into Sail Power for a local-first fishing, fleet, and harbor-building companion game.
- [TokRepo Search](https://github.com/henu-wang/tokrepo-codex-plugin) - Search and install AI assets from TokRepo with a bundled skill and MCP server for Codex.
- [unslop](https://github.com/MohamedAbdallah-14/unslop) - Strip AI writing patterns from text output — removes filler phrases, hedging language, and generic constructs to produce cleaner written content. Install: `npm install -g unslop`.
- [Upwork Autopilot](https://github.com/klajdikkolaj/upwork-autopilot) - Controlled Upwork job search, qualification, and proposal submission sessions through a dedicated Chrome profile.
- [Val Town](https://github.com/val-town/plugins) - Build and deploy serverless TypeScript on Val Town from Codex — hosted MCP server plus skills for HTTP vals, cron, SQLite, email, OAuth, and React UI.
- [VidSeeds.ai](https://github.com/CarrotGamesStudios/vidseeds-mcp) - Hosted MCP connector for pre-upload video SEO, metadata optimization, AI thumbnails, and multi-platform publishing with workflow skills for Codex agents.
- [WakeWire](https://github.com/glenncalleja/wakewire) - Push events from GitHub, Gmail, Slack, and any signed webhook (Linear, Sentry, ClickUp) straight into your Codex threads as new turns — event-driven triggers instead of polling, with HMAC verification, deduplication, and a durable delivery queue.
- [X Twitter Scraper](https://github.com/Xquik-dev/x-twitter-scraper) - X/Twitter data, monitored workflows, HMAC webhooks, and MCP access through the Xquik REST API with confirmation-gated write guidance.
- [Yandex Direct](https://github.com/nebelov/yandex-direct-for-all) - GitHub-ready Codex plugin bundle for Yandex Direct, Wordstat, Metrika, and Roistat.
- [Zotero Research Tools](https://github.com/summer521521/Zotero_Research_plugin) - Connects Codex to Zotero Desktop for local-library search, citation export, collection and tag inspection, and research workflow support.

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

- [awesome-ai-plugins](https://github.com/hashgraph-online/awesome-ai-plugins) - Umbrella list covering Codex, Claude Code, Gemini CLI, and MCP servers.
- [HOL Plugin Registry](https://hol.org/registry/plugins) - Browse plugins with scanner-backed security analysis and trust scores.

## Claim Your Plugin

Verify ownership of your plugin on the [HOL Plugin Registry](https://hol.org/registry/plugins) to display a verified badge on your listing.

### How to claim

1. Go to [hol.org/guard/plugins](https://hol.org/guard/plugins) and sign in with GitHub
2. Find your plugin in the list and click **Verify Ownership**
3. Authorize the read-only GitHub connection (view your profile, email, and public org membership — no write access)
4. Once verified, your plugin listing will display a **Verified** badge

That's it. The verification confirms you are the repository owner or an organization admin. Plugins owned by organizations may require additional review.

> **Note:** You only need to verify once per plugin. If your verification needs to be reset, contact support at `support@hol.org`.

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

### HOL Guard Protection Badge

Show that your plugin repo is protected by [HOL Guard](https://hol.org/guard):

```
[![HOL Guard](https://img.shields.io/endpoint?url=https%3A%2F%2Fhol.org%2Fapi%2Fregistry%2Fbadges%2Fguard%2FOWNER%2FREPO%3Fstyle%3Dflat-square)](https://hol.org/guard)
```

The badge checks your repo for HOL Guard adoption (config files, CI workflows, dependencies) and displays `Protected` (green) or `Unprotected` (grey). To get the badge:

1. Install HOL Guard: `pipx install hol-guard && hol-guard init`
2. Or add the scanner to CI: `uses: hashgraph-online/ai-plugin-scanner-action@v1`
3. Add the badge markdown to your README (replace `OWNER%2FREPO`)

## Plugin Quality

If you received a scanner report on your repo, check the [Scanner Guide](SCANNER_GUIDE.md) for setup instructions, common fixes, and CI setup.

## Contributing

Contributions welcome! Please read the [contribution guidelines](CONTRIBUTING.md) first.

To add a plugin:

1. Set up the HOL Plugin Scanner in your plugin repo (see [CONTRIBUTING.md](CONTRIBUTING.md))
2. Fork this repo and add a single line to the appropriate section in `README.md` (alphabetical order)
3. Submit a PR with your scanner score and plugin repo URL

**You do not need to copy plugin files into this repo.** A generator fetches your bundle from your source repo and regenerates catalog files automatically.
