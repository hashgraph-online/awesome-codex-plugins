<div align="center">

# AgentOps

[![GitHub stars](https://img.shields.io/github/stars/boshu2/agentops?style=social)](https://github.com/boshu2/agentops/stargazers)

### Autonomous code validation for coding agents

Coding agents can produce plausible code that is still wrong. AgentOps helps answer the two questions that decide whether you can trust the work: **is the code right, and is the agent output proven enough to grant more autonomy?** It sits on top of the agent you already use (Claude Code, Codex, Cursor, OpenCode) and adds the validation membrane, evidence trail, and repo-local corpus that make that judgment repeatable.

</div>

---

## See it work

<div align="center">

![The AgentOps loop in Claude Code: /discovery builds a bead graph, /crank fans sub-agents out in waves, /validate --mixed gets a Claude + Codex verdict](docs/assets/hero.gif)

<sub><code>/discovery</code> → bead graph · <code>/crank</code> → sub-agents in waves · <code>/validate --mixed</code> → real Claude + Codex verdict. Live sessions. <a href="docs/assets/hero.mp4">MP4</a></sub>

</div>

AgentOps breaks intent into bounded slices, gives each a failing test and a write scope, and makes every phase boundary a gate that records evidence. The agent starts loaded with prior decisions and learnings instead of cold:

```text
> /council --mixed validate this PR

[council] evidence sealed → 6 judges across Claude Code + Codex CLI
[claude/judge-1] WARN  rate limiting missing on /login
[codex/judge-1]  WARN  token bucket lacks jitter under burst
[claude/judge-2] PASS  redis integration follows pattern
Consensus: WARN, fix /login limit + refill jitter before shipping
Recorded → .agents/council/<run-id>/verdict.md
```

---

## What you get

<!-- agentops:claim:AOP-CLAIM-README-FACTORY-CONTEXT -->

The center is validation: prove the agent output, keep the proof, and use that record to decide how much autonomy the next run earns. The supporting layers all stay local in `.agents/` (no telemetry, no hosted control plane):

| Layer | The problem | What AgentOps adds |
|---|---|---|
| **Validation membrane** | agent output can look correct while being wrong | tests, local gates, `/pre-mortem`, `/vibe`, `/council`, and pawl verdicts prove or reject the work |
| **Evidence trail** | "looks good" does not survive handoff | `.agents/` captures runs, decisions, findings, citations, verdicts, retros, and closeout proof |
| **Context compiler** | validators and implementers start cold | `ao context assemble` builds phase-scoped packets; `ao lookup` retrieves decay-ranked knowledge |
| **Knowledge ratchet** | lessons vanish between sessions | `/forge` mines learnings, `/evolve` reconciles, and durable lessons become constraints before more autonomy is granted |

The corpus is an LLM wiki of markdown. Agents read it natively and write to it as they work, so it maintains itself instead of becoming another doc you keep up by hand. Why that beats Notion or Confluence: [docs/wiki-for-agents.md](docs/wiki-for-agents.md). The full theory (context as the lifecycle, the CDLC): [docs/cdlc.md](docs/cdlc.md).

<!-- agentops:claim:AOP-CLAIM-README-COMPETITIVE-MEMORY -->

---

## Install

Pick your runtime, then type `/quickstart` in the agent.

```bash
# Claude Code
claude plugin marketplace add boshu2/agentops
claude plugin install agentops@agentops-marketplace

# Codex CLI (macOS/Linux/WSL).  OpenCode: install-opencode.sh
curl -fsSL https://raw.githubusercontent.com/boshu2/agentops/main/scripts/install-codex.sh | bash
# Codex CLI (Windows):
irm https://raw.githubusercontent.com/boshu2/agentops/main/scripts/install-codex.ps1 | iex

# Gemini / Antigravity
curl -fsSL https://raw.githubusercontent.com/boshu2/agentops/main/scripts/install-agy.sh | bash

# Other skills-compatible agents
npx skills@latest add boshu2/agentops --cursor -g
```

The `ao` CLI is optional but recommended (bookkeeping, retrieval, health, the loops):

```bash
brew tap boshu2/agentops https://github.com/boshu2/homebrew-agentops && brew install agentops   # macOS
# Windows: irm https://raw.githubusercontent.com/boshu2/agentops/main/scripts/install-ao.ps1 | iex
# Or release binaries / build from source (cli/README.md).
```

Installs hookless: skills and the `ao` CLI guide the workflow, and the local cockpit gate is the release authority. GitHub Actions are an optional/manual backstop, not the routine shipping path. The only hard requirement is an agent runtime and `git`; everything else degrades gracefully. Full dependency matrix: [docs/dependencies.md](docs/dependencies.md). Day-2 install, update, backup, permission, recovery, and escalation paths are in [docs/install-day2-ops.md](docs/install-day2-ops.md).

---

## Quick start

<!-- agentops:claim:AOP-CLAIM-README-FIRST-VALIDATED -->

| You want to… | Run | Done when |
|---|---|---|
| set up a repo | `ao quick-start`, then `/quickstart` | AgentOps reports readiness and a next action |
| ship one validated change | `/rpi "a small goal"` | discovery, build, validation, and learnings all leave evidence in `.agents/` |
| review something now | `/council validate this PR` · `/vibe recent` | a consolidated verdict and a record before you ship |

Already installed? Ask your agent: `/quickstart`. Or run `ao doctor` and `ao demo`. First-session walkthrough: [docs/first-value-path.md](docs/first-value-path.md).

---

## Skills

Every skill works alone; flows compose them. Full catalog: [docs/SKILLS.md](docs/SKILLS.md), unsure where to start? [Skill Router](docs/SKILL-ROUTER.md).

| Skill | Use it when |
|---|---|
| `/quickstart` | you want the fastest setup check and next action |
| `/research` | you need codebase context and prior learnings before changing code |
| `/pre-mortem` | you want to pressure-test a plan before building |
| `/rpi` | you want discovery, build, validation, and bookkeeping in one flow |
| `/council` | you want independent judges (optionally Claude and Codex) to return one verdict |
| `/validate` | you want a code-quality and risk review before shipping |
| `/evolve` | a goal-driven improvement loop that compounds knowledge without mutating source |

---

## The `ao` CLI

Repo-native control plane behind the skills. Full reference: [CLI commands](cli/docs/COMMANDS.md).

<!-- agentops:claim:AOP-CLAIM-README-EVOLVE-AUTONOMOUS -->

```bash
ao quick-start            # set up AgentOps in a repo
ao search "query"         # search history and local knowledge
ao lookup --query "topic" # retrieve curated learnings
ao context assemble       # build a task briefing
ao rpi phased "fix X"     # run the phased loop from the terminal
ao compile                # rebuild the corpus
ao metrics health         # flywheel health
```

<!-- agentops:claim:AOP-CLAIM-README-AUTONOMOUS-FLYWHEEL -->

**In session vs. out of session.** The whole loop runs in a plain session: no daemon, no scheduler, no cloud (the sovereignty floor). For always-on work, the same loop opts into a swappable substrate (an NTM tmux swarm, MCP via `ao mcp serve`, or managed-agents) that dispatches a whole `ao rpi` per ready bead. Details: [docs/3.0.md](docs/3.0.md); component routing: [docs/architecture/component-map.md](docs/architecture/component-map.md).

---

## Honest limitations

- **It doesn't write code.** It wraps Claude Code / Codex / Cursor / OpenCode with bookkeeping, gates, and a corpus; the harness still writes it.
- **No hosted control plane or telemetry.** Everything lives in your repo; there's no cross-team dashboard unless you commit `.agents/`.
- **Multi-model councils cost tokens.** Six judges per PR isn't free; running them on a substrate makes the cost predictable, not zero.
- **The corpus needs hygiene.** `ao defrag` and `ao maturity` keep it healthy; neglected, it rots like any markdown vault.
- **There are many skills.** `/quickstart` and the [Skill Router](docs/SKILL-ROUTER.md) exist so you don't have to learn them all up front; current inventory is generated from `skills/**/SKILL.md`.

**What if the labs ship this natively?** They will. The durable value is the `.agents/` corpus you build, not the tool that builds it: plain markdown in your repo, it carries forward to whatever ships next, stays forkable, and is Apache-2.0 with no lock-in.

---

## Docs & contributing

[What 3.1 adds](docs/3.1.md) · [What 3.0 is](docs/3.0.md) · [component map](docs/architecture/component-map.md) · [docs index](docs/documentation-index.md) · [newcomer guide](docs/newcomer-guide.md) · [architecture](docs/ARCHITECTURE.md) · [FAQ](docs/FAQ.md) · built on the [12-factor doctrine](https://12factoragentops.com).

Contributing: [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) (agents: read [AGENTS.md](AGENTS.md), track work with `br`). License: Apache-2.0.
