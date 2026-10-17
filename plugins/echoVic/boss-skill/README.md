# boss-skill

[![skills.sh](https://skills.sh/b/echovic/boss-skill)](https://skills.sh/echovic/boss-skill)
[![CodeRabbit Pull Request Reviews](https://img.shields.io/coderabbit/prs/github/echoVic/boss-skill?utm_source=oss&utm_medium=github&utm_campaign=echoVic%2Fboss-skill&labelColor=171717&color=FF570A&link=https%3A%2F%2Fcoderabbit.ai&label=CodeRabbit+Reviews)](https://coderabbit.ai)
[![G-Star Incubation](https://img.shields.io/badge/G--Star-Incubation-C71D23)](https://atomgit.com/echoVic/boss-skill)
[![AtomGit Mirror](https://img.shields.io/badge/AtomGit-Mirror-1F6FEB)](https://atomgit.com/echoVic/boss-skill)
[![Boss trust badge](https://img.shields.io/endpoint?url=https%3A%2F%2Fhol.org%2Fapi%2Fregistry%2Fbadges%2Fplugin%3Fslug%3Dechovic%252Fboss%26metric%3Dtrust%26style%3Dflat)](https://hol.org/registry/plugins/echovic%2Fboss)

**Languages / 语言 / 言語 / 언어 / Idiomas / Langues:** [English](./README.md) · [中文](./README.zh-CN.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · [Português](./README.pt-BR.md)

![boss-skill promo](https://raw.githubusercontent.com/echoVic/boss-skill/main/boss-skill-promo.png)

> This project is part of the AtomGit G-Star Incubation Program. GitHub is the canonical repository; AtomGit provides an automatically synchronized mirror for faster access in China. Please submit issues and pull requests on [GitHub](https://github.com/echoVic/boss-skill).
>
> GitHub: <https://github.com/echoVic/boss-skill> · AtomGit mirror: <https://atomgit.com/echoVic/boss-skill>

**Boss is an auditable agent-team workflow for coding agents.** It turns one coding agent into a structured engineering team: PM, Architect, UI Designer, Tech Lead, Scrum Master, Frontend, Backend, QA, and DevOps. Unlike prompt-only agent teams, Boss adds runtime state, append-only events, quality gates, deterministic evals, hooks, and replayable artifacts.

Boss works with Claude Code, Codex, OpenClaw, Antigravity, and Hermes.

## Why Boss

Prompt-only orchestration can sound organized, but it usually cannot prove that the plan was followed, tests were run, gates passed, or state was not hallucinated. Boss is built around evidence:

- **Zero-network by default**: no telemetry, no phone-home, no remote LLM proxy. The only network surface is an opt-in loopback preview server bound to `127.0.0.1`. A source-level [network-boundary test](./test/runtime/network-boundary.test.ts) fails CI if anyone reintroduces an outbound client. See [PRIVACY.md](./PRIVACY.md).
- **No shell injection**: wave verification runs through structured `argv` (`waves.json`), never through a shell. Cloning a malicious repository cannot smuggle commands via `tasks.md`.
- **Event-sourced runtime**: pipeline state is appended to `.boss/<feature>/.meta/events.jsonl` and projected into read-only execution state.
- **Verifiable gates**: QA, deployment, and final checks run as real commands whose verdicts are recorded as events. `boss gate final` and `boss doctor` fail when a completed stage carries a failed gate. Enforcement still relies on the orchestrating agent honoring the protocol; the CLI makes the verdict checkable, not unavoidable.
- **Replayable artifacts**: PRDs, architecture docs, task lists, QA reports, deploy reports, and summaries live under `.boss/<feature>/`.
- **Deterministic evals**: captured transcripts can be scored without calling a real LLM.
- **Agent-friendly CLI**: commands support JSON output, `--describe`, dry runs, bounded fields, and structured errors.
- **Self-verifiable**: run `boss doctor` to confirm the resolved runtime, install locations, event-stream health, and network boundary — the zero-network claim is auditable, not just asserted.

## Use One Role Or The Whole Team

Boss is not a single monolithic command. You can run one role against an existing project, or run the full pipeline from idea to delivery.

| Command | What it does | Use when |
| --- | --- | --- |
| `/boss` | Full 4-stage pipeline | You want to go from idea to shippable work |
| `/boss:plan` | PM + Architect planning | You want PRD and architecture before implementation |
| `/boss:review` | Tech Lead review | You need a read-only code, PR, or design review |
| `/boss:qa` | QA plus gates | You need verifiable test evidence |
| `/boss:ship` | DevOps build and deployment checks | You are ready to ship |
| `/boss:extend` | Custom agent, pack, or gate | You want to adapt Boss for your team |
| `/boss:upgrade` | Update Boss Skill and re-merge hooks | You want the latest marketplace version and hook config |

## Quick Start

### 1. Install

Boss is a skill you install into your coding agent — not a tool that installs other skills. Distribution is marketplace-only: no npm package, no global binary. The skill ships with its own CLI (`skill/cli/`), which hooks and the agent invoke through `node`.

**Claude Code — plugin marketplace (recommended; hooks come wired):**

```text
/plugin marketplace add echoVic/boss-skill
/plugin install boss@boss-skill
```

**Codex — plugin marketplace:**

```bash
codex plugin marketplace add echoVic/boss-skill
```

Then open the plugin browser (`/plugins`) and install **boss**.

**Any agent — via the `skills` CLI ([vercel-labs/skills](https://github.com/vercel-labs/skills), skills.sh):**

```bash
npx skills add echoVic/boss-skill
```

It discovers `boss` from the repo, prompts for target agent / scope (project vs global) / install method, and records a `skills-lock.json` you can commit. Boss ships a single skill root, so the picker shows just `boss` — its internal methodologies travel with it.

For Codex and other copy-based installs, wire up the Boss hooks with the bundled CLI:

```bash
node <installed-skill>/cli/bin/boss.mts install
```

### 2. Try It On A Project You Already Have

The lowest-cost first run is a single role against existing code. It reads, it does not write:

```
/boss:review
```

You get `tech-review.md` under `.boss/<feature>/` with risks, findings and severity. Nothing else in your repo is touched.

Want verifiable test evidence instead? `/boss:qa` runs the tests and the gates, and writes `qa-report.md`.

### 3. Run The Full Pipeline

Inside your coding agent:

```text
/boss Build a local personal todo app --roles core --skip-deploy
```

- `--roles core` uses PM, Architect, Dev, and QA.
- `--skip-deploy` stops after implementation and test evidence.

### 4. Inspect Results

Boss ships its own CLI inside the skill — no npm install, no PATH setup. In the snippets below, `<skill>` is the directory that contains `SKILL.md` (for Claude Code plugin installs: `<plugin-root>/skill`; for copied installs, e.g. `~/.codex/skills/boss`).

```bash
node <skill>/cli/bin/boss.mts status todo-app --json
node <skill>/cli/bin/boss.mts runtime inspect-pipeline todo-app
```

Expected artifact layout:

```text
.boss/todo-app/
├── design-brief.md
├── prd.md
├── architecture.md
├── tasks.md
├── qa-report.md
└── .meta/
    ├── events.jsonl
    ├── execution.json
    └── workflow-plan.json
```

## When To Use Boss

| Good fit | Poor fit |
| --- | --- |
| New features that need requirements, design, implementation, tests, and delivery evidence | One-line fixes or tiny local edits |
| API, full-stack, UI, or medium-sized product work | Pure code reading or explanation |
| Work where `.boss/<feature>/` artifacts are valuable | Tasks with a complete existing spec where you only need a quick patch |
| Teams that want repeatable gates and audit trails | Work that does not need coordination or review evidence |

Rule of thumb: if you do not need a traceable `.boss/` folder, you probably do not need the full `/boss` pipeline. Use a single role or let your coding agent edit directly.

## No CLI Fallback

The CLI ships inside the skill, so a marketplace install always carries it. When `node` is unavailable or the CLI cannot be located, the workflow degrades to Markdown artifacts under `.boss/<feature>/` instead of the event stream. The CLI is the auditability upgrade: event sourcing, replayable resume, deterministic evals, runtime gates, and structured diagnostics.

Boss does not mean "install once and get guaranteed autonomous delivery." It provides a runtime workflow and evidence gates; the active coding agent still has to follow the Boss protocol.

## Installation Details

Marketplace installs copy (or link) the whole `skill/` directory. The CLI ships as TypeScript source at `<skill>/cli/bin/boss.mts` and is executed directly by Node.js `>=22.18` (native type stripping) — there is no build step, no npm package, and no global `boss` binary. Hooks reference it by full path.

Useful commands (run through the bundled CLI):

```bash
node <skill>/cli/bin/boss.mts install --dry-run
node <skill>/cli/bin/boss.mts uninstall
node <skill>/cli/bin/boss.mts path
node <skill>/cli/bin/boss.mts --version
```

Auto-detected targets for `boss install`:

| Agent | Detection | Install method |
| --- | --- | --- |
| OpenClaw | `~/.openclaw/` | Copy to `~/.openclaw/skills/boss/` and inject metadata |
| Codex | `~/.codex/` | Copy to `~/.codex/skills/boss/`, inject metadata, merge hooks |
| Antigravity | `~/.gemini/antigravity/` | Copy to Antigravity skills directory and inject metadata |
| Hermes | `~/.hermes/` | Copy to `~/.hermes/skills/boss/` and inject metadata |
| Claude Code | Always available | Plugin marketplace (see Quick Start) |

## Platform Support

Boss targets Node.js `>=22.18` and runs on Linux, macOS, and Windows. The CLI ships inside
the skill as TypeScript source that Node executes directly (native type stripping — no build
step), shells out only through `spawnSync` with explicit argument arrays (never
`shell: true`), and resolves `npm`/`npx` to their `.cmd` variants on Windows, so there is
no POSIX-only assumption in the core pipeline.

Two capabilities depend on optional external tools and degrade gracefully when they are
absent:

- **WIP checkpoints** (stash/commit/branch) require `git` and a git working tree. Outside a
  repository, or without `git` on `PATH`, checkpointing is silently skipped — the pipeline
  is unaffected.
- **Legacy hand-written `gate.sh` plugins** are executed via `bash`. On Windows without a
  bash in `PATH` these will fail to launch; prefer the cross-platform Node gate entry
  (`gate.js` / `gate.mjs`) for portable plugins.

Run `boss doctor` to see the resolved runtime environment (Node version, platform, and
whether `git` is available) alongside install and event-stream health.

## Commands

Common slash commands:

```text
/boss Build a todo app
/boss Add authentication to this existing project --skip-ui
/boss Build an API service --skip-deploy --quick
/boss Continue the previous task --continue-from 3
/boss Lightweight mode --roles core --hitl-level off
/boss:upgrade
```

Common options:

| Option | Meaning |
| --- | --- |
| `--roles <preset>` | `full` for all 9 roles, or `core` for PM/Architect/Dev/QA |
| `--skip-ui` | Skip UI design |
| `--skip-deploy` | Skip deployment |
| `--quick` | Skip confirmation and requirement clarification nodes |
| `--template` | Initialize `.boss/templates/` and pause |
| `--continue-from <1-4>` | Resume from a pipeline stage |
| `--hitl-level <level>` | Human-in-the-loop mode: `auto`, `interactive`, or `off` |

Boss CLI commands:

```bash
boss --help
boss doctor                              # install, runtime and per-feature health
boss status FEATURE
boss continue FEATURE
boss gate FEATURE                        # one quality gate
boss gate final FEATURE                  # release gate (subcommand comes first)
boss qa attack FEATURE
boss project init FEATURE
boss design preview FEATURE
boss packs detect
boss runtime inspect-pipeline FEATURE
boss runtime generate-summary FEATURE
boss runtime rebuild-state FEATURE       # rebuild execution.json from events.jsonl
```

`execution.json` is a projection, not a source of truth: if it is ever unreadable, `boss runtime rebuild-state` regenerates it from the event stream.

Agent-facing `boss` commands use these common options where applicable; run `--describe` on a command for its exact JSON schema:

- `--json`: structured output; non-TTY stdout defaults to JSON
- `--describe`: JSON command schema
- `--dry-run`: structured action plan for writes or risky operations
- `--json-input=<json|->`: JSON input payload
- `--fields=<a,b>` and `--limit=<n>`: bounded output
- `--yes`: required only for high-risk non-interactive commands that need an extra confirmation

Structured errors are written to stderr as `{"error":{...}}` and include `code`, `message`, `input`, `retryable`, and `suggestion`. Domain conditions carry their own codes rather than a generic failure — `retry_budget_exhausted`, `invalid_state_transition`, `run_id_mismatch`, `feedback_budget_exhausted`, `gate_not_found`, `workflow_plan_mismatch`, `state_unreadable`, `pipeline_not_initialized`, `invalid_usage` — and each `suggestion` names the next command to run.

## Workflow

Boss follows a four-stage workflow:

```text
User request
  -> requirement clarification
  -> Stage 1: PM, Architect, UI Designer
  -> Stage 2: Tech Lead, Scrum Master
  -> Stage 3: Frontend, Backend, QA, gates
  -> Stage 4: DevOps, deployment checks, summary
```

The full role set:

| Role | Responsibility |
| --- | --- |
| PM | Requirement discovery, PRD, hidden needs, edge cases |
| Architect | System architecture, technical design, APIs |
| UI Designer | UI/UX spec plus renderable design JSON |
| Tech Lead | Technical review, risk assessment |
| Scrum Master | Task breakdown and acceptance criteria |
| Frontend | UI implementation and frontend tests |
| Backend | API, storage, backend tests |
| QA | Test execution, bug reports, verification evidence |
| DevOps | Build, deployment, health checks |

## Runtime And Quality Gates

Boss has two layers of quality control:

- **Hard constraints** verified by code and CI: runtime events, protected `execution.json`, hooks, install matrix tests, harness scenarios, and Vitest coverage.
- **Agent protocol constraints** guided by the skill bundle: DAG dispatch, progressive reference loading, test evidence, and gate discipline.

Built-in gates:

| Gate | Timing | Checks |
| --- | --- | --- |
| Gate 0 | After development, before QA | TypeScript, lint, basic compile checks |
| Gate 1 | After QA, before deployment | Test evidence, no P0/P1 bugs, E2E expectations |
| Gate 2 | Before web deployment | Lighthouse and API latency targets when applicable |

Hooks are controlled by environment variables:

| Variable | Values |
| --- | --- |
| `BOSS_HOOK_PROFILE` | `minimal`, `standard`, `strict` |
| `BOSS_DISABLED_HOOKS` | Comma-separated hook IDs |

Runtime state is backed by `.boss/<feature>/.meta/workflow-plan.json` and `.boss/<feature>/.meta/execution.json`. The workflow definition records `workflowHash`, `packHash`, and artifact DAG hashes. Runtime resume uses `boss runtime resume <feature> --from-run <run-id>` to reload the plan, compare node inputs, and materialize `execution.workflow.nextNodeIds` for the next schedulable nodes. `GateEvaluated` / `WaveVerified` events update workflow node status when gates and evidence waves complete.

## Security-Sensitive Surfaces

Boss intentionally keeps the published plugin manifest small: it declares only bundled skills and omits MCP servers, app manifests, and asset references unless those companion files exist. Codex hooks are installed by the `boss-skill install` flow, not by the marketplace manifest.

The npm package excludes local development agent settings such as `.claude/settings.json` and `.claude/settings.local.json`. Publishable plugin metadata lives under `.claude-plugin/`, `.codex-plugin/`, and `.agents/plugins/marketplace.json`.

Release provenance lives in `.agents/plugins/provenance.json`. It pins the repository HTTPS URL, immutable source commit SHA, publisher identity, and SHA-256 digests for plugin manifests and security-sensitive components. Verify it with:

```bash
npm run provenance:verify
```

Publisher verification is external to the package. For the HOL registry, claim the plugin with the repository owner's GitHub account at `https://hol.org/guard/plugins`. The public trust card is available at `https://hol.org/registry/plugins/echovic%2Fboss/embed`.

Security-sensitive behavior to review before publishing or installing:

- `boss-skill install` may write to agent configuration directories such as `~/.codex/skills/boss/` and merge Boss-managed entries into `~/.codex/hooks.json`.
- Hook entries execute `boss hooks run ...`, which dispatches scripts from `scripts/hooks/`.
- Runtime plugins under `.boss/plugins/<name>/plugin.json` can register gate or reporter hooks; review project-local plugins before enabling them.
- Use `BOSS_HOOK_PROFILE=minimal` or `BOSS_DISABLED_HOOKS=<ids>` when you need to reduce hook behavior in a sensitive environment.

Boss is local-first and makes no outbound network requests by default; the only network
surface is the opt-in, loopback-only `boss design preview` server. See [PRIVACY.md](PRIVACY.md)
for the full data and network boundary.

## Pipeline Artifacts

```text
.boss/<feature>/
├── design-brief.md
├── prd.md
├── architecture.md
├── ui-spec.md
├── ui-design.json
├── tech-review.md
├── tasks.md
├── qa-report.md
├── deploy-report.md
├── summary-report.md
└── .meta/
    ├── events.jsonl
    ├── execution.json
    └── workflow-plan.json
```

Run this in an interactive environment to preview a generated UI design:

```bash
boss design preview <feature>
```

Artifacts are grouped by lifetime rather than listed flat. The summary report and `boss status` separate **product assets** (`prd.md`, `architecture.md`, `ui-spec.md`, `ui-design.json` — maintained across iterations) from **run records** (`tech-review.md`, `tasks.md`, `qa-report.md`, `deploy-report.md` — superseded by the next round) and **derived views** (the `.html` companions). When an upstream product asset is regenerated, `boss status` names the run records that no longer match it.

## Evals

Boss evals score captured fixtures without starting a real LLM:

```bash
npm run evals
npm run evals:release
```

The release eval includes release-evidence and pipeline-compliance checks. It verifies runtime command usage, artifact recording, avoidance of direct `execution.json` edits, and workflow scheduling fields.

See [test/evals/README.md](./test/evals/README.md).

## Development

Requirements:

- Node.js >= 22.18 (runs the `.mts` CLI source directly)
- `jq` for shell-based test helpers

Setup:

```bash
git clone https://github.com/echoVic/boss-skill.git
cd boss-skill
npm install
npm run typecheck
npm test
```

Useful scripts:

```bash
npm run typecheck   # tsc only checks the .mts source — there is no build output
npm test
npm run test:skills
npm run test:harness
npm run test:install-matrix
npm run evals
```

## Repository Layout

```text
boss-skill/
├── skill/                      # Skill bundle installed into coding agents (self-contained)
│   ├── cli/                    # CLI + runtime source (.mts, run directly — no build)
│   ├── scripts/                # Hook runtime (dispatcher + hook scripts)
│   └── assets/                 # Built-in DAGs, pipeline packs, plugin schema
├── test/                       # Vitest, harness, eval, hook, and install tests
├── docs/superpowers/           # Historical specs, plans, and reports
├── examples/                   # Example projects
├── .claude-plugin/             # Claude Code plugin manifest + marketplace
├── .codex-plugin/              # Codex plugin manifest + marketplace
├── .agents/plugins/            # Repo-scoped plugin marketplace + provenance
├── tsconfig.json               # Typecheck-only config (no emit)
└── package.json                # Private dev workspace (never published)
```

Important source areas:

- `skill/cli/` contains the CLI and runtime TypeScript source (`.mts`), executed directly by Node `>=22.18`. Edit these files directly — there is no build step and no generated copy.
- `skill/assets/` contains built-in DAGs, pipeline packs, plugin schema, and plugins.
- `skill/scripts/` contains the hook runtime (`lib/run-with-flags.js`) and hook scripts.
- `skill/SKILL.md` is the main agent-facing orchestration entry.
- `skill/agents/` contains the role prompts.
- `skill/commands/` contains slash commands.
- `skill/templates/` contains artifact templates.

## Release

Use the release script so version numbers stay synchronized across package metadata and skill/plugin manifests:

```bash
npm run release -- patch
npm run release -- minor
npm run release -- major
npm run release -- 4.1.0
npm run release -- 4.1.0 --dry-run
```

The release script checks for a clean worktree, runs the full verification chain, syncs versions, verifies consistency, creates a commit and tag, and pushes. Release is the git tag: marketplaces read the repository — there is no npm publish step and no build step.

See [CONTRIBUTING.md](./CONTRIBUTING.md).

## Design

Boss is inspired by BMAD: Breakthrough Method of Agile AI-Driven Development. The project adapts that idea into an auditable runtime for agentic software work.

Read more in [DESIGN.md](./DESIGN.md) and `skill/references/bmad-methodology.md`.

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=echoVic/boss-skill&type=Date)](https://star-history.com/#echoVic/boss-skill&Date)

## License

MIT
