# Session Orchestrator

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-3.12.0-blue.svg)](CHANGELOG.md)
[![Tests](https://img.shields.io/badge/tests-10%2C000%2B-brightgreen.svg)](docs/telemetry/telemetry-claims.md)

Turn ad-hoc agent sessions into a repeatable loop with verification gates — loop engineering for software work. You design the loop (`research → plan → execute in waves → close`); Session Orchestrator runs it on top of your existing agent, with the guards, telemetry, and cross-session memory that keep a long agent run honest. Inter-wave reviews catch regressions before they ship; carryover issues mean loose ends get tracked, not lost.

Works with **Claude Code, Codex CLI, Cursor IDE, and [Pi](docs/pi-setup.md)** — the same skills and commands across all four, with platform-adapted hooks and enforcement (see [Platform support](#platform-support)). Community plugin (MIT, community-maintained) for solo devs and small teams.

## A session in three commands

```text
/session feature    # research + Q&A — inspect git, issues, history, then agree on scope
/go                 # execute in five typed waves (fixed roles), with a quality gate between each
/close              # verify every item, commit cleanly, file carryover issues for the rest
```

That is the whole loop. `/plan` and `/evolve` extend it (see [Lifecycle](#lifecycle-at-a-glance)), but you can start with just these three.

## Install

> **Prerequisite:** Node.js 24 or later (`node --version`). v3.x runs as ES modules and needs a real Node runtime. [Install Node.js](https://nodejs.org/).

The two paths below differ only by **install mechanism**, not capability or tier: Claude Code pulls from the plugin marketplace; every other platform clones the repo. The same skills and commands ship to all four.

### Claude Code (plugin marketplace)

Run these two slash commands **inside** Claude Code (not in a shell):

```text
/plugin marketplace add Kanevry/session-orchestrator
/plugin install session-orchestrator@kanevry
```

Then install Node dependencies **once** (hooks import `zx`) and restart Claude Code:

```bash
cd "$(claude plugin dir session-orchestrator 2>/dev/null || echo ~/.claude/plugins/session-orchestrator)"
npm install
```

### Codex CLI, Cursor IDE & Pi (git clone)

```bash
git clone https://github.com/Kanevry/session-orchestrator.git ~/Projects/session-orchestrator
cd ~/Projects/session-orchestrator && npm install
node scripts/codex-install.mjs                          # Codex CLI
node scripts/cursor-install.mjs /path/to/your/project   # Cursor IDE
node scripts/pi-install.mjs    /path/to/your/project --settings-only   # Pi
```

Setup guides: [Codex](docs/codex-setup.md) · [Cursor IDE](docs/cursor-setup.md) · [Pi](docs/pi-setup.md). Per-IDE notes on `CLAUDE.md` vs `AGENTS.md`: [instruction-file-resolution](skills/_shared/instruction-file-resolution.md).

## Quick Start

Add a `## Session Config` section to your project's `CLAUDE.md` (Claude Code and Cursor IDE) or `AGENTS.md` (Codex CLI and Pi) — see [instruction-file-resolution](skills/_shared/instruction-file-resolution.md) for which file each platform reads. The smallest valid config is seven fields:

```yaml
## Session Config

test-command: npm test
typecheck-command: npm run typecheck
lint-command: npm run lint
agents-per-wave: 6
waves: 5
persistence: true
enforcement: warn
```

Everything else is opt-in. See [`docs/session-config-template.md`](docs/session-config-template.md) for the full template and [`docs/session-config-reference.md`](docs/session-config-reference.md) for the canonical type and default reference.

## What you get

- **43 skills** for the session lifecycle (start, plan, execute, close, evolve), discovery, vault sync, MCP authoring, debugging, brainstorming, plan grilling, persona panels, cross-repo dispatch, learning→rule reconciliation, audits, and more
- **23 slash commands** (`/session`, `/go`, `/close`, `/discovery`, `/plan`, `/grill`, `/evolve`, `/autopilot`, `/dispatcher`, `/reconcile`, `/test`, `/debug`, …)
- **14 typed subagents** (code-implementer, test-writer, security-reviewer, session-reviewer, qa-strategist, architect-reviewer, …)
- **10 hook event types** enforcing scope, blocking destructive commands, gating templates-first, capturing telemetry — full on Claude Code; experimental, post-hoc, or bridged on the other platforms ([Platform support](#platform-support))
- **10,000+ vitest tests** run on every commit ([telemetry methodology](docs/telemetry/telemetry-claims.md))

Full component inventory: [`docs/components.md`](docs/components.md).

## Lifecycle at a glance

```mermaid
flowchart TD
    A["/plan [feature|retro]"] -->|optional, defines WHAT| B["/session [type]"]
    B -->|research + Q&A| C["/go"]
    C -->|5 waves with quality gates| D["/close"]
    D -->|verifies + commits| E["/evolve [analyze]"]
    E -->|extracts cross-session learnings| B
    style C fill:#1f6feb,color:#fff
    style D fill:#238636,color:#fff
```

`/plan` is optional — you can create issues manually and jump straight to `/session`. `/evolve` runs deliberately after 5+ sessions, not automatically.

## How it works

Most agentic-coding tools jump straight into writing code. Session Orchestrator adds a structured loop on top: research first, agree on scope, then execute in five typed waves with verification gates between them.

```mermaid
flowchart LR
    W1["1·Discovery<br/>read-only audit"] --> G1{Gate}
    G1 --> W2["2·Impl-Core<br/>primary code"]
    W2 --> G2{Gate}
    G2 --> W3["3·Impl-Polish<br/>integration, edges"]
    W3 --> G3{Gate}
    G3 --> W4["4·Quality<br/>simplify + tests"]
    W4 --> G4{Full Gate}
    G4 --> W5["5·Finalization<br/>commit + close"]
    style G4 fill:#d29922,color:#000
```

When you type `/session feature`:

1. **Phase analysis runs in parallel** — git state, open issues, recent commits, SSOT freshness, resource health, and prior-session memory are all inspected, then distilled into a structured Session Overview with a recommendation, not a wall of raw data.
2. **You agree on scope** — through a tool-rendered picker (Claude Code) or a numbered list (Codex / Cursor / Pi). The orchestrator has an opinion and tells you what it would do.
3. **The plan is decomposed into five waves** — Discovery (read-only), Impl-Core, Impl-Polish, Quality, Finalization. Each wave has a defined purpose and a deliverable; agent counts scale by session type.
4. **`/go` executes** — agents work in parallel within a wave. A session-reviewer audits the output between waves on eight dimensions; only findings at confidence ≥ 80 reach you.
5. **`/close` ships it** — every planned item is verified, quality gates run full, and unfinished work becomes carryover issues. Files are staged individually, so parallel sessions can't stomp each other.

Two complementary commands round out the loop: **`/plan`** runs *before* a session when you need a PRD or retrospective; **`/evolve`** runs occasionally to surface patterns across sessions and feed them back at the next start.

The system is markdown-driven config plus a thin Node runtime — skills, commands, and agents are Markdown with YAML frontmatter; `scripts/lib/*.mjs` and `hooks/*.mjs` handle dispatch, validation, and telemetry. Everything is plain text: if something goes wrong, you can read every file and see what happened.

## Why this design

- **Five typed waves, not one big batch.** Discovery first, so implementers start with shared context. Impl-Core before Impl-Polish, so architecture lands before integrations. Quality runs a *simplification pass* on AI-generated code **before** tests are written — otherwise tests pin the AI patterns into place.
- **Inter-wave reviews, not just end-of-session.** Catching regressions between waves — not only at the end — stops a bad pattern from propagating into later work; the confidence floor filters speculative criticism so only high-signal findings reach you.
- **State persists across crashes.** `STATE.md` records wave progress and deviations; the next `/session` offers to resume from the last completed wave.
- **Hooks enforce, not just warn.** A pre-Bash guard blocks destructive shell commands, and pre-Edit scope enforcement blocks writes outside an agent's allowed paths — in main sessions and subagent waves alike (specifics in [Safety](#safety)). This hard enforcement is full on Claude Code; it degrades to experimental / post-hoc / bridged on Codex CLI, Cursor IDE, and Pi (see [Platform support](#platform-support)).
- **Cross-session learning is opt-in and inspectable.** Every session writes a record; after 5+ sessions `/evolve analyze` extracts confidence-scored patterns you can read and prune. Nothing is hidden.
- **VCS dual support, no lock-in.** Auto-detects GitLab or GitHub from your remote and drives the full lifecycle for both.

## Recent highlights (v3.12.0)

Every release is additive and backward-compatible. Highlights of the v3.12.0 line:

- **Gated session handover** — `/close` collects carryover candidates and routes them through an operator-triaged alignment gate instead of filing them scattered across phases; a new `## Open Questions` STATE.md channel carries a wave agent's unresolved questions across the session boundary, surfaced as a forced-read at the next session-start.
- **Fail-loud wave dispatch** — small-batch `Agent()` dispatch by default (large fan-outs drop calls silently), planned-vs-started dispatch verification with re-dispatch, and git-diff edit-persistence evidence before any agent's `done` is accepted.
- **Curated public docs** — 68 process records moved to the operator's private vault behind a sensitivity gate; three permanent guards (docs-parity drift check, docs-staleness probe, epic-close PRD archive routine) keep the public tree user-facing.
- **Session-lock reliability** — heartbeat-first liveness ends the live-session-hijack incident class, a lock reaper sweeps orphaned registry claims, and STATE.md writes are size-guarded.
- **Portable hooks** — all hook commands route through a node-resolver shim, fixing per-tool-call failures on nvm/volta/asdf/Homebrew setups where hook shells never source `~/.zshrc`.

Previous line (v3.11.0): self-healing session ledger, learning-store backup + expiry sweep, hardened CI mirror, tier-aware rule loading.

Full version history: [CHANGELOG.md](CHANGELOG.md).

## Comparison

| Capability | Session Orchestrator | Manual `CLAUDE.md` | Other orchestrators |
|---|---|---|---|
| Session lifecycle (start → plan → execute → close) | Full, automated | Manual | Partial |
| Typed waves with quality gates | 5 roles, progressive verification | None | Batch execution |
| Session persistence and crash recovery | `STATE.md` plus memory files | None | Partial |
| Scope and command enforcement hooks | PreToolUse with strict / warn / off | None | None |
| Circuit breaker and spiral detection | Per-agent, with recovery | None | Partial |
| Cross-session learning | Confidence-scored learnings | None | None |
| VCS integration (GitLab + GitHub) | Dual, auto-detected | Manual CLI | Usually GitHub only |
| Session close with carryover | Verified, with issue creation | Manual | Partial |

The design goal is engineering quality: every wave exits verified, every unfinished issue gets a carryover ticket, every session closes with a clean commit. A detailed head-to-head vs. [maestro-orchestrate](https://github.com/josstei/maestro-orchestrate) is in [`docs/components.md`](docs/components.md#comparison-vs-maestro-orchestrate).

## Platform support

| Feature | Claude Code | Codex CLI | Cursor IDE | Pi |
|---|---|---|---|---|
| All 23 commands | Native slash commands | Native plugin commands | Rules-based (.mdc) | Prompt templates |
| Parallel agents | Agent tool | Multi-agent roles | Sequential only | Sequential (parallel planned) |
| Session persistence | `.claude/STATE.md` | `.codex/STATE.md` | `.cursor/STATE.md` | `.pi/STATE.md` |
| Scope enforcement | PreToolUse hooks | Hooks (experimental) | `afterFileEdit` (post-hoc) | `tool_call` bridge |
| AskUserQuestion | Native tool | Numbered-list fallback | Numbered-list fallback | Numbered-list fallback |
| Quality gates | Full | Full | Full | Full |

All platforms share the same skills, commands, hooks, and scripts; platform-specific adaptation lives in `scripts/lib/platform.mjs`. **OS:** macOS and Linux are first-class and run in CI (`ubuntu-latest`, `macos-latest`). Windows runs natively (all paths via `path.join`, tmp via `os.tmpdir()`) but is **not** covered by CI — treat it as best-effort and run smoke tests locally when changing OS-sensitive code. Cursor and Pi have known event-coverage caveats — see [`docs/cursor-setup.md`](docs/cursor-setup.md) and [`docs/pi-setup.md`](docs/pi-setup.md).

## Troubleshooting

**"'node' not found on the hook PATH — plugin hooks are skipped."** The harness executes hook commands via `/bin/sh -c` with its own PATH — that shell does not source `~/.zshrc`/`~/.bashrc`, so Node installed via Homebrew (`/opt/homebrew/bin`), nvm, volta, or asdf can be invisible to hooks even though `node` works fine in your terminal. All hook commands route through [`hooks/run-node.sh`](hooks/run-node.sh), which resolves Node via `$SO_NODE_BIN` → PATH → well-known install dirs → nvm and degrades gracefully when nothing is found: hooks are skipped with **one** warning per 6 hours instead of a shell error on every tool call. Fixes, in order of preference: launch the harness from a shell where `node` resolves; export `SO_NODE_BIN=/abs/path/to/node`; or install Node 24+ to a standard location.

## Safety

`hooks/pre-bash-destructive-guard.mjs` blocks destructive shell commands (`git reset --hard`, `rm -rf`, `git push --force`, and more) in the main session *and* in subagent waves. Policy lives in `.orchestrator/policy/blocked-commands.json`. Bypass per session only for intentional maintenance:

```yaml
allow-destructive-ops: true
```

The rule source of truth is [`.claude/rules/parallel-sessions.md`](.claude/rules/parallel-sessions.md) (PSA-003), vendored to consumer repos via `/bootstrap`.

## Development

```bash
git clone https://github.com/Kanevry/session-orchestrator.git && cd session-orchestrator
npm install
npm test          # vitest
npm run lint      # ESLint v10 + Prettier
npm run typecheck # node --check on every .mjs file
```

`.npmrc` ships with `ignore-scripts=true` (supply-chain defence), so Husky git hooks don't auto-wire on install — run `npx husky` once after cloning. `git commit` then runs gitleaks → owner-privacy scan → lint-staged → commitlint. CI re-runs everything, plus more.

Contributor docs: [Plugin Architecture (v3)](docs/plugin-architecture-v3.md) · [CONTRIBUTING.md](CONTRIBUTING.md) · [agent authoring spec](agents/AGENTS.md).

## Support & scope

Session Orchestrator is provided **as-is** — a community project with no SLA, no commercial support contract, and no guaranteed response time. Maintenance is best-effort.

- Questions, ideas, show-and-tell → [GitHub Discussions](https://github.com/Kanevry/session-orchestrator/discussions)
- Bugs and feature requests → [Issues](https://github.com/Kanevry/session-orchestrator/issues)

What it is **not**:

- **Not an official product of any agent vendor.** An independent, community-maintained project — not affiliated with, endorsed by, or sponsored by Anthropic, OpenAI, Cursor, or any agent it integrates with. (It is distributed through the Claude Code plugin marketplace, but is not an Anthropic product.)
- **Not a replacement** for Claude Code / Codex CLI / Cursor / Pi. It is a workflow layer that runs *on top of* your existing agent — you still need one of those installed.
- **Not a hosted service.** Runs locally — no server, account, or cloud component.
- **No guarantee that telemetry numbers transfer to your repo.** Reported test counts and metrics describe *this* repository under its own conditions ([details](docs/telemetry/telemetry-claims.md)). Your results will vary by stack, project size, and configuration.

## Documentation

- [docs/ Router](docs/README.md) — living reference vs. public decision history vs. active work documents; what moved to the private Meta-Vault and why
- [User Guide](docs/USER-GUIDE.md) — installation, config reference, workflow walkthrough, FAQ
- [Components & Reference](docs/components.md) — full skill/command/agent/hook inventory, repository anatomy, comparisons
- [Plugin Architecture (v3)](docs/plugin-architecture-v3.md) — contributor guide, layering, hook anatomy, testing
- [Migration to v3](docs/migration-v3.md) — upgrade path from v2.x, known issues, rollback
- [Telemetry claims](docs/telemetry/telemetry-claims.md) — how reported metrics are measured, and why they may not transfer
- [Example Configs](docs/examples/) — Session Config examples for Next.js, Express, Swift
- [CHANGELOG.md](CHANGELOG.md) — version history

We follow [Conventional Commits](https://www.conventionalcommits.org/) — see [CONTRIBUTING.md](CONTRIBUTING.md).

## Learn the method behind it

This plugin is a methodology turned into code. If you want the reasoning behind it — why execution runs in waves, why every wave ends at a verification gate, how to make an autonomous loop that actually finishes — those playbooks are taught hands-on at **[agenticbuilders.at](https://agenticbuilders.at)**:

- **[Multi-Agent Orchestration](https://agenticbuilders.at/orchestrierung)** — leading several agents in coordinated waves: when parallelism pays, briefing subagents cleanly, turning failures into firm gates.
- **[Loop Engineering](https://agenticbuilders.at/loop-engineering)** — designing autonomous loops that finish verifiably: done-conditions, verification gates, kill-switches.

The plugin is free and MIT. The courses are for going deeper, not a requirement for using it.

## Links

- [Homepage](https://gotzendorfer.at/en/session-orchestrator) · [Privacy Policy](https://gotzendorfer.at/en/session-orchestrator/privacy)

## License

[MIT](LICENSE)
