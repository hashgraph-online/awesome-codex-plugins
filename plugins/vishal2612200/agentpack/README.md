# AgentPack

<p align="center">
  <img src="docs/assets/agentpack-symbol.png" alt="AgentPack symbol: a compact map pack for coding agents" width="180">
</p>

<p align="center">
  <strong>Your agent starts cold. AgentPack hands it the map.</strong>
</p>

<p align="center">
  <em>Ranked repo context for Codex, Claude Code, Cursor, Windsurf, Copilot, Cline, Kiro, OpenCode, MCP, CI, and markdown workflows.</em>
</p>

<p align="center">
  <a href="https://deepwiki.com/vishal2612200/agentpack"><img src="https://deepwiki.com/badge.svg" alt="Ask DeepWiki"></a>
  <a href="https://github.com/vishal2612200/agentpack"><img alt="AgentPack" src="docs/assets/agentpack-badge.png"></a>
  <a href="https://github.com/vishal2612200/agentpack"><img alt="AgentPack review" src="docs/assets/agentpack-review-badge.png"></a>
  <a href="https://pypi.org/project/agentpack-cli/"><img alt="PyPI version" src="https://img.shields.io/pypi/v/agentpack-cli.svg?cacheSeconds=300"></a>
  <a href="https://pepy.tech/projects/agentpack-cli"><img alt="PyPI downloads" src="https://static.pepy.tech/personalized-badge/agentpack-cli?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads"></a>
  <a href="https://www.npmjs.com/package/@vishal2612200/agentpack"><img alt="npm version" src="https://img.shields.io/npm/v/@vishal2612200/agentpack.svg?cacheSeconds=300"></a>
  <a href="https://www.npmjs.com/package/@vishal2612200/agentpack"><img alt="npm downloads" src="https://img.shields.io/npm/dm/@vishal2612200/agentpack.svg"></a>
  <a href="https://github.com/vishal2612200/agentpack/releases/latest"><img alt="Release evidence" src="https://img.shields.io/github/v/release/vishal2612200/agentpack?label=release%20evidence"></a>
  <a href="https://github.com/vishal2612200/agentpack/actions/workflows/publish.yml"><img alt="PyPI trusted publishing" src="https://img.shields.io/badge/PyPI-trusted%20publishing-blue"></a>
  <a href="https://github.com/vishal2612200/agentpack/actions/workflows/publish-npm.yml"><img alt="npm provenance" src="https://img.shields.io/badge/npm-provenance-blue"></a>
  <a href="https://hol.org/registry/plugins/agentpack%2Fagentpack"><img alt="HOL trust score" src="https://img.shields.io/endpoint?url=https%3A%2F%2Fhol.org%2Fapi%2Fregistry%2Fbadges%2Fplugin%3Fslug%3Dagentpack%252Fagentpack%26metric%3Dtrust%26style%3Dflat"></a>
  <a href="https://hol.org/registry/plugins/agentpack%2Fagentpack"><img alt="HOL security score" src="https://img.shields.io/endpoint?url=https%3A%2F%2Fhol.org%2Fapi%2Fregistry%2Fbadges%2Fplugin%3Fslug%3Dagentpack%252Fagentpack%26metric%3Dsecurity%26style%3Dflat"></a>
  <a href="https://github.com/vishal2612200/agentpack/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/vishal2612200/agentpack/actions/workflows/ci.yml/badge.svg"></a>
  <a href="https://www.gnu.org/licenses/agpl-3.0.en.html"><img alt="License: AGPL v3" src="https://img.shields.io/badge/License-AGPL%20v3-blue.svg"></a>
</p>

<p align="center">
  <code>local preflight</code>
  <code>ranked files</code>
  <code>skill routing</code>
  <code>warm cache</code>
  <code>tests + commands</code>
  <code>receipts</code>
  <code>no cloud index</code>
</p>

---

<p align="center">
  <img src="docs/assets/agentpack-demo.gif" alt="Terminal demo: AgentPack refreshes context, routes a task, recommends skills, checks review output, records learning, inspects advisory memory timeline rows, then runs a focused test." width="840">
</p>

<p align="center">
  <a href="docs/assets/agentpack-demo.mp4">MP4 demo</a>
</p>

You know the pattern. You ask an agent to fix one bug. It `rg`s half the repo, opens the wrong files, misses the test, then rediscovers the architecture you already had.

AgentPack does the repo-orientation pass first.

```text
agentpack route --task "fix auth token expiry"
-> files that probably matter
-> why those files, and why common candidates were skipped
-> skills and rules that fit the task
-> tests that probably prove it
-> rules, commands, warnings
-> compact context before the agent edits
```

AgentPack is not another coding agent. It is the local context engine you put in front of the agents you already use.

## The Pitch

```text
Without AgentPack: agent explores first, edits later.
With AgentPack:    agent starts near the right files.
```

No cloud index. No embeddings. No model calls for scan/rank/pack. Just local repo analysis, ranked context, and receipts for what got included or skipped.

It is not a repo dump. It is not a generic memory app. It is not a promise that your agent will be right.

It is a preflight map: likely files, likely tests, the right local skill or rule, commands, warnings, and a compact pack your agent can inspect before touching code.

The first run builds local summaries and repo signals. Later runs reuse that cache, so agents do less repeat discovery and spend more of their budget on the actual change.

## What We Are Solving

AgentPack exists because developer-agent work has three recurring failure modes:

- **Cold-start drift**: every new chat repeats repo discovery, burns tokens, and may anchor on the wrong files.
- **Session collision**: two chats in the same repo can accidentally share stale task context and continue old work.
- **Context inflation**: agents ask for full repo context when a task, delta, or one related file would be enough.

The direction is a local developer control plane, not another autonomous agent.
`quickstart`, `start`, `next`, and `doctor` are the human-facing loop.
MCP `readiness()`, `get_context()`, `get_delta_context()`, and route/explain
tools are the agent-facing loop. Both read the same task/session/context/token
state, so AgentPack can answer "what now?" consistently across Codex, Claude,
Cursor, Windsurf, Antigravity, and generic agents.

The long-term vision is a practical second brain for development: local memory,
review evidence, AST/symbol structure, task history, and observer signals that
help the next agent orient faster. The shipped memory graph records task-start
maps, node refs, episodes, procedures, and memory edges under `.agentpack/`;
`agentpack memory --timeline` shows timestamps, hashes, confidence, stale-path
checks, and visible reasons. It remains advisory by design. Source files,
diffs, tests, runtime evidence, and PR review stay the source of truth.

## Quick Start

```bash
pipx install agentpack-cli
agentpack --version
```

Inside your repo:

```bash
agentpack quickstart
agentpack start "fix auth token expiry"
agentpack next
agentpack doctor --agent auto
```

Then give `.agentpack/context.md` to your agent, or let MCP-capable agents call AgentPack tools directly.
Core onboarding is `quickstart`, `start`, `next`, and `doctor`. `next` is the
single "what now?" command: it checks setup, task/session state, context
freshness, thread overlap, and token guidance. Use `route`, `pack`, and
`benchmark` when you need deeper inspection or measurement. Everything else is
an advanced workflow or release/diagnostic helper.

For one-shot use without installing:

```bash
pipx run --spec agentpack-cli agentpack route --task "fix auth token expiry"
```

For JavaScript/TypeScript projects, npm wrapper is available:

```bash
npx @vishal2612200/agentpack --version
npx @vishal2612200/agentpack quickstart
npx @vishal2612200/agentpack start "fix auth token expiry"
npx @vishal2612200/agentpack next
```

## Release Trust

Install surfaces intentionally point at the same local CLI:

- PyPI publishes `agentpack-cli` through GitHub Actions trusted publishing.
- npm publishes `@vishal2612200/agentpack` with npm provenance.
- GitHub Releases include release-check, benchmark, wheel verification, and registry evidence.
- HOL registry badges track packaged Codex plugin trust and security signals.

Planned hardening: attach release checksums, publish an SBOM, and add SLSA-style provenance once the release artifact pipeline can produce them automatically.

## Proof So Far

AgentPack's current public benchmark checks one narrow thing: whether selected context overlaps with files actually changed in historical commits. Treat it as evidence for a ranked starting map, not proof that any agent will finish every task faster or better.

| Signal | Result | Developer meaning |
|---|---:|---|
| Public commit cases | 107 | real historical file-selection checks |
| Average recall | 67.2% | did AgentPack include files that mattered? |
| Token precision | 50.6% | how much of pack was useful instead of noise? |
| Pack p50 | 315 tokens | typical compact starting context |
| Pack p95 | 1,137 tokens | larger but still bounded starting context |

Source: [`benchmarks/results/2026-07-06-public.md`](benchmarks/results/2026-07-06-public.md). Benchmark guide: [`docs/benchmarking.md`](docs/benchmarking.md).

This is useful but not magic. It says AgentPack often gets meaningful files into a small pack. It does not replace source inspection, tests, runtime evidence, or review. Agent success A/B benchmarks should report task success, tool calls, token cost, validation quality, and time-to-first-correct-file.

E2E outcome proof is tracked separately in [`benchmarks/results/e2e-ab-status.md`](benchmarks/results/e2e-ab-status.md). Do not treat file-selection results as task-success or cost-savings proof.

Memory feedback has its own guardrail: compare ranking with memory off/on using
`agentpack eval --memory-ab`. Timestamped memory can explain or boost context,
but it is not task-success proof.

## Current Release Snapshot

Current package line: `0.3.39`.

- Public release gate: 107 historical commit cases, 67.2% average recall, and 50.6% token precision.
- Ranking/runtime: ranked carrier compaction now keeps lower-action support files tighter without dropping the release benchmark below target.
- Language context: Rust symbol extraction covers free functions, `impl`/`trait` methods, and `struct`/`enum`/`trait` declarations, with the regex-based limits documented in [`docs/limitations.md`](docs/limitations.md).
- Automation confidence: scoped `mypy` coverage now spans `src/agentpack/analysis/`, and JSON-output smoke tests cover scriptable `route`, `next`, and release-check flows.
- Guard behavior: generated fallback and repair guidance use global task context unless thread mode is explicit, avoiding stale ambient Codex task state.
- Plugin distribution: the Codex plugin now uses the README symbol as its `composerIcon`/`logo`, and the packaged plugin scanner path reports `100/A` with zero local findings.

## New Contributors

Start with [`good first issue`](https://github.com/vishal2612200/agentpack/issues?q=is%3Aissue%20is%3Aopen%20label%3A%22good%20first%20issue%22) or [`help wanted`](https://github.com/vishal2612200/agentpack/issues?q=is%3Aissue%20is%3Aopen%20label%3A%22help%20wanted%22) issues.
If this would be your first open-source contribution, use the smaller
[`first-timers-only`](https://github.com/vishal2612200/agentpack/issues?q=is%3Aissue%20is%3Aopen%20label%3A%22first-timers-only%22) queue.
Contribution setup and review expectations are in [CONTRIBUTING.md](CONTRIBUTING.md).

## Quick Demo

Start with the control-plane loop:

```bash
agentpack quickstart
agentpack start "fix billing webhook retry handling"
agentpack next
```

AgentPack writes local task/context state under `.agentpack/`, checks freshness,
and tells you the next safe action. MCP-capable agents use the same state
through `readiness()`, `get_context()`, and `get_delta_context()`.

Use route and pack when you want deeper inspection:

```bash
agentpack route --task "fix billing webhook retry handling"
agentpack pack --task auto
agentpack dashboard
```

`route` returns likely files, why-selected and why-not-selected notes, tests,
rules, commands, warnings, and matching skills without writing source files.
`pack` renders selected files, omitted-file receipts, freshness checks, token
stats, and citation provenance for packed claims.
`dashboard` opens the local context cockpit: selected and omitted files, task
map risk, likely tests, memory influence, observer signals, and next actions in
one inspectable view backed by `dashboard-data.json` and `dashboard-graph.json`.
AgentPack reuses cached file summaries and snapshot metadata so repeated packs do not start from zero.
Run `agentpack doctor` when an agent integration, MCP setup, hook, or installed CLI path looks stale.
Inspect advisory memory with `agentpack memory --timeline`; prune local history
with `agentpack memory --prune`.

## Capability Map

| Area | What AgentPack provides |
|---|---|
| Orientation | ranked files, likely tests, commands, repo rules, skills, and why/why-not receipts |
| Control plane | `next`, `status`, `guard`, MCP readiness, thread state, freshness checks, and exact repair commands |
| Token control | budgeted packs, token contracts, delta-context guidance, cached summaries, and retrieval IDs |
| Review and proof | citation-backed review artifacts, review preflight, benchmark misses, and local validation guidance |
| Advisory memory | task-start maps, node refs, episodic/procedural links, timeline/staleness checks, and observer signals below source/test evidence |
| Context cockpit | local React/Vite view of task graph, risk/tests, memory influence, replay, raw snapshot, and graph contracts |

## Current Focus

- Make `quickstart`, `start`, `next`, and `doctor` the default human loop.
- Keep `next`, `quickstart`, `status`, `guard`, and MCP readiness on one shared control-plane snapshot.
- Use token contracts to recommend full context vs delta context.
- Keep repair output explicit: what failed, why it matters, the exact command, and whether work can safely continue.
- Keep review, TOON, route explainability, and MCP troubleshooting grounded in source, diff, test, and PR evidence.
- Keep advisory memory auditable with timestamps, provenance, confidence, hashes, stale checks, and visible reasons.

## What We Want To Prove Next

AgentPack should eventually show:

- fewer agent file reads
- fewer tool calls
- faster first correct file
- lower total context cost
- equal or better task success

## Works With

- Codex
- Claude Code
- Cursor
- Windsurf
- Antigravity
- MCP tools
- CI and PR review workflows
- generic markdown-based LLM workflows

See [`docs/integrations.md`](docs/integrations.md) and [`docs/mcp-context-engine.md`](docs/mcp-context-engine.md).

### Agent And IDE Plugins

AgentPack can be used through thin plugin and IDE integration layers so agents start with ranked repo context. Codex has a packaged plugin skeleton; Cursor, Windsurf, Copilot, Cline, Kiro, OpenCode, Claude Code, Antigravity, and generic agents use the same local CLI/MCP engine through portable rules, hooks, and native integration stubs.

Canonical directory description:

```text
AgentPack is a local context engine for AI coding agents: ranked files,
tests, rules, skills, and compact task context without hosted indexing.
```

Current public placement includes PyPI, npm, GitHub Releases, GitHub Pages docs,
and HOL's plugin registry. Next distribution targets are MCP/plugin directories,
agent-tool awesome lists, and comparison pages that point back to the same
canonical docs instead of creating separate host-specific claims.

Inside Codex:

```text
@agentpack-route fix auth token expiry
@agentpack-pack fix auth token expiry
@agentpack-review focus on backward compatibility
```

The Codex plugin calls the local AgentPack engine. Codex setup enables the
local `agentpack@local` bundle so commands like `@agentpack-review` match the
installed CLI version. Verify with `agentpack doctor --agent codex` after
upgrades. Its packaged marketplace icon is the same checked-in symbol shown at
the top of this README.

The review flow prepares a local two-stage PR review bundle: preflight metadata,
a runbook, stage prompts, and branch-scoped understanding/findings JSON files.
It does not replace `gh pr view`, `git diff`, direct code reads, or tests.

AgentPack does not upload code and does not turn AgentPack into a coding agent.

See [`docs/agent-plugins.md`](docs/agent-plugins.md) and [`docs/codex-plugin.md`](docs/codex-plugin.md).

## When To Use It

Use AgentPack when:

- repo is large or split across multiple packages
- monorepo structure makes file discovery expensive
- agents repeat same discovery work across tasks
- CI or PR review needs reproducible context
- agents waste tool calls opening irrelevant files
- tasks often miss tests, config, generated rules, or repo conventions
- teams have useful skills/rules but agents do not reliably pick the right one
- repeated agent sessions keep rediscovering the same repo structure

Skip AgentPack or keep it as a light preflight when:

- repo is tiny
- question is one-shot and read-only
- you already know exact files to edit
- you need autonomous coding, not context preparation
- native IDE search is already enough for task

## Boundaries

AgentPack is closest to a local preflight and control plane:

- unlike repo dumpers, it ranks and compresses by task
- unlike coding agents, it does not edit code
- unlike IDE search, it routes before the agent starts wandering
- unlike generic skills/rules, it recommends the ones that fit the task
- unlike generic memory, its observer signals stay advisory and local

Implementation deep dives: [`docs/architecture.md`](docs/architecture.md), [`docs/how-agentpack-works.md`](docs/how-agentpack-works.md), and [`docs/commands.md`](docs/commands.md).

## Trust And Privacy

- local-first by default
- no cloud indexing
- no embeddings or API calls for scan, rank, pack, stats, or benchmark
- generated files live under `.agentpack/`
- local task/memory artifacts can include task text, paths, hashes, reasons, timestamps, and confidence
- review packs before sharing them outside your machine

Details: [`docs/privacy.md`](docs/privacy.md), [`docs/threat-model.md`](docs/threat-model.md), [`docs/data-flow.md`](docs/data-flow.md), and [`SECURITY.md`](SECURITY.md).

## Install Notes

Requires Python 3.10+ and is tested on Python 3.10-3.14. PyPI package is `agentpack-cli`; command is `agentpack`.

Use `pipx` for normal installs because many macOS/Linux Python distributions block global `pip install` with PEP 668's `externally-managed-environment` error.

Install `pipx` first if needed:

```bash
# macOS
brew install pipx

# Ubuntu/Debian
sudo apt install pipx

# Fedora
sudo dnf install pipx

# Arch
sudo pacman -S python-pipx

pipx ensurepath
```

## Docs

- [`docs/index.md`](docs/index.md): docs home
- [`docs/architecture.md`](docs/architecture.md): pipeline, data flow, package layout, and rendered-budget accounting
- [`docs/commands.md`](docs/commands.md): full CLI command reference
- [`docs/configuration.md`](docs/configuration.md): config, scoring weights, `.agentignore`, and git integration
- [`docs/integrations.md`](docs/integrations.md): agent setup, MCP workflow, hooks, and native integration status
- [`docs/agent-plugins.md`](docs/agent-plugins.md): plugin and IDE distribution layer
- [`docs/codex-plugin.md`](docs/codex-plugin.md): thin Codex plugin commands and local workflow
- [`docs/mcp-context-engine.md`](docs/mcp-context-engine.md): MCP tools and context workflow
- [`docs/benchmarking.md`](docs/benchmarking.md): quality bar, release gate, and public artifacts
- [`docs/limitations.md`](docs/limitations.md): project scope, known limits, and roadmap

## Status

Alpha: `0.3.39`.

Works, tested, and used in real sessions. Python and JavaScript/TypeScript have strongest support. APIs may change before 1.0.

Platform support targets macOS, Linux, and Windows PowerShell with Git for Windows. `cmd.exe` and bare Git setups are not supported yet.

Name note: PyPI package is `agentpack-cli`, npm package is `@vishal2612200/agentpack`, and command is `agentpack`. This project is unrelated to AgentPack dataset papers or other repos with the same name.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for setup, validation, and PR expectations.
Community behavior is covered by [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).

## License

GNU Affero General Public License v3.0
