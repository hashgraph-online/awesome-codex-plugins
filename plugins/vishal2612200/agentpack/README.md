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
  <a href="https://pypi.org/project/agentpack-cli/"><img alt="PyPI version" src="https://img.shields.io/pypi/v/agentpack-cli.svg"></a>
  <a href="https://pepy.tech/projects/agentpack-cli"><img alt="PyPI downloads" src="https://static.pepy.tech/personalized-badge/agentpack-cli?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads"></a>
  <a href="https://www.npmjs.com/package/@vishal2612200/agentpack"><img alt="npm version" src="https://img.shields.io/npm/v/@vishal2612200/agentpack.svg"></a>
  <a href="https://www.npmjs.com/package/@vishal2612200/agentpack"><img alt="npm downloads" src="https://img.shields.io/npm/dm/@vishal2612200/agentpack.svg"></a>
  <a href="https://hol.org/registry/plugins/agentpack%2Fagentpack"><img alt="HOL trust score" src="https://img.shields.io/endpoint?url=https%3A%2F%2Fhol.org%2Fapi%2Fregistry%2Fbadges%2Fplugin%3Fslug%3Dagentpack%252Fagentpack%26metric%3Dtrust%26style%3Dflat"></a>
  <a href="https://hol.org/registry/plugins/agentpack%2Fagentpack"><img alt="HOL security score" src="https://img.shields.io/endpoint?url=https%3A%2F%2Fhol.org%2Fapi%2Fregistry%2Fbadges%2Fplugin%3Fslug%3Dagentpack%252Fagentpack%26metric%3Dsecurity%26style%3Dflat"></a>
  <a href="https://github.com/vishal2612200/agentpack/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/vishal2612200/agentpack/actions/workflows/ci.yml/badge.svg"></a>
  <a href="https://opensource.org/licenses/MIT"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-yellow.svg"></a>
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

You know the pattern. You ask an agent to fix one bug. It `rg`s half the repo, opens the wrong files, misses the test, then rediscovers the architecture you already had.

AgentPack does the repo-orientation pass first.

```text
agentpack route --task "fix auth token expiry"
-> files that probably matter
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

It is not a repo dump. It is not a second brain. It is not a promise that your agent will be right.

It is a preflight map: likely files, likely tests, the right local skill or rule, commands, warnings, and a compact pack your agent can inspect before touching code.

The first run builds local summaries and repo signals. Later runs reuse that cache, so agents do less repeat discovery and spend more of their budget on the actual change.

## Quick Start

```bash
pipx install agentpack-cli
agentpack --version
```

Inside your repo:

```bash
agentpack init --yes
agentpack route --task "fix auth token expiry"
agentpack task set "fix auth token expiry"
agentpack pack --task auto
```

Then give `.agentpack/context.md` to your agent, or let MCP-capable agents call AgentPack tools directly.

For one-shot use without installing:

```bash
pipx run --spec agentpack-cli agentpack route --task "fix auth token expiry"
```

For JavaScript/TypeScript projects, npm wrapper is available:

```bash
npx @vishal2612200/agentpack --version
npx @vishal2612200/agentpack init --yes
npx @vishal2612200/agentpack task set "fix auth token expiry"
npx @vishal2612200/agentpack pack --task auto
```

## Quick Demo

Route task first:

```bash
agentpack route --task "fix billing webhook retry handling"
```

AgentPack returns likely files, tests, rules, commands, and warnings without changing source files.
It also recommends matching skills or agent rules when the task points at a known workflow, framework, language, or repo convention.

Build context pack next:

```bash
agentpack task set "fix billing webhook retry handling"
agentpack pack --task auto
```

AgentPack writes local context under `.agentpack/`, including selected files, omitted-file receipts, freshness checks, and token stats.
It reuses cached file summaries and snapshot metadata so repeated packs do not start from zero.

## What AgentPack Gives Your Agent

- ranked files for current task
- skill and rule routing for current task
- likely tests and commands
- repo rules and agent instructions
- compact context pack under budget
- cached summaries for faster repeated orientation
- omitted-file receipts for review
- freshness warnings when task or git state changes
- local benchmark data when selected context misses real changed files

## Proof So Far

AgentPack's current public benchmark checks one narrow thing: whether selected context overlaps with files actually changed in historical commits.

Current scoped result:

| Signal | Result | Developer meaning |
|---|---:|---|
| Public commit cases | 108 | real historical file-selection checks |
| Average recall | 66.0% | did AgentPack include files that mattered? |
| Token precision | 51.1% | how much of pack was useful instead of noise? |
| Pack p50 | 315 tokens | typical compact starting context |
| Pack p95 | 1,137 tokens | larger but still bounded starting context |

Source: [`benchmarks/results/2026-06-14-public.md`](benchmarks/results/2026-06-14-public.md). Benchmark guide: [`docs/benchmarking.md`](docs/benchmarking.md).

This is useful but not magic. It says AgentPack often gets meaningful files into a small pack. It does not claim every agent finishes faster or writes better code. Agent success A/B benchmarks should report task success, tool calls, token cost, and time-to-first-correct-file.

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

Inside Codex:

```text
@agentpack-route fix auth token expiry
@agentpack-pack fix auth token expiry
@agentpack-review focus on backward compatibility
```

The Codex plugin calls the local AgentPack engine. Codex setup enables the
local `agentpack@local` bundle so commands like `@agentpack-review` match the
installed CLI version. Verify with `agentpack doctor --agent codex` after
upgrades.

The review flow prepares a local two-stage PR review bundle: preflight metadata,
a runbook, stage prompts, and branch-scoped understanding/findings JSON files.
It does not replace `gh pr view`, `git diff`, direct code reads, or tests.

AgentPack does not upload code and does not turn AgentPack into a coding agent.

See [`docs/agent-plugins.md`](docs/agent-plugins.md) and [`docs/codex-plugin.md`](docs/codex-plugin.md).

## How AgentPack Compares

| Tool type | What it does | AgentPack difference |
|---|---|---|
| Repo dumpers | Dump selected or all files | AgentPack ranks files by task |
| Coding agents | Edit code | AgentPack prepares context before editing |
| IDE search | Finds files on demand | AgentPack pre-routes before agent starts |
| Skills/rules | Change agent behavior | AgentPack routes the matching skill or rule for the task |
| Cache warmers | Speed repeated scans | AgentPack reuses summaries and snapshots inside the context workflow |

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

Do not use AgentPack when:

- repo is tiny
- question is one-shot and read-only
- you already know exact files to edit
- you need autonomous coding, not context preparation
- native IDE search is already enough for task

## How It Works

AgentPack scans repo locally, builds and reuses file summaries, indexes local skills and rules, combines filename, git, config, dependency, summary, and benchmark signals, ranks likely files for task, then renders a compact context pack.

It can expose the same workflow through CLI, markdown files, MCP tools, hooks, plugins, and CI.

Deep dive: [`docs/architecture.md`](docs/architecture.md), [`docs/how-agentpack-works.md`](docs/how-agentpack-works.md), and [`docs/commands.md`](docs/commands.md).

## Trust And Privacy

- local-first by default
- no cloud indexing
- no embeddings or API calls for scan, rank, pack, stats, or benchmark
- generated files live under `.agentpack/`
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

Alpha: `0.3.25`.

Works, tested, and used in real sessions. Python and JavaScript/TypeScript have strongest support. APIs may change before 1.0.

Platform support targets macOS, Linux, and Windows PowerShell with Git for Windows. `cmd.exe` and bare Git setups are not supported yet.

Name note: PyPI package is `agentpack-cli`, npm package is `@vishal2612200/agentpack`, and command is `agentpack`. This project is unrelated to AgentPack dataset papers or other repos with the same name.

## License

MIT
