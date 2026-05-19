<div align="center">

# AgentOps

[![GitHub stars](https://img.shields.io/github/stars/boshu2/agentops?style=social)](https://github.com/boshu2/agentops/stargazers)

### The SDLC control plane for agentic software development.

From agent opinions to engineering verdicts.

<!-- agentops:claim:AOP-CLAIM-README-FACTORY-CONTEXT -->
**AgentOps is the SDLC control plane for coding agents.** It takes the software-engineering practices teams already understand - Agile/XP, BDD/Gherkin, DDD, hexagonal architecture, TDD, CI/CD, SRE, ADRs, provenance, and durable knowledge - and compiles them into dense, verifiable context for LLM agents under token scarcity.

It is not a packet generator; packets are one artifact. AgentOps keeps the books for coding agents, then compiles that record into context for your software factory. It captures what agents tried, what worked, what failed, what was validated, and what should constrain the next run.

*AgentOps is the shovel. Start digging.*

> AgentOps is not a coding harness. The labs are building those, and they will keep getting better. AgentOps sits on top of whichever harness you already use — Claude Code, Codex, Cursor, OpenCode — and turns your business, codebase, and team practices into a context library those agents mix and match from. Mix and match Claude, Codex, or any model at every phase. Lives in `.agents/` in your repo. Runs on your hardware. Evolves with the models.

*AgentOps was used to develop AgentOps. As of 2026-05-04, this repo's `.agents/` directory contained ~1,842 learnings, ~186 patterns, ~80 planning rules, and ~3,867 cited decisions captured by the system on itself across thousands of phase transitions. Re-run anytime: `bash scripts/corpus-stats.sh`. Independent 3-judge audit (2026-05-06) confirmed parity with Anthropic Managed Agents on rubric authoring, separate-context grading, and iterate-until-pass.*

</div>

---

## Install

Pick the runtime you use.

**Claude Code**

```bash
claude plugin marketplace add boshu2/agentops
claude plugin install agentops@agentops-marketplace
```

**Codex CLI on macOS, Linux, or WSL**

```bash
curl -fsSL https://raw.githubusercontent.com/boshu2/agentops/main/scripts/install-codex.sh | bash
```

Codex installs hookless by default. To opt into native Codex hooks, run:

```bash
curl -fsSL https://raw.githubusercontent.com/boshu2/agentops/main/scripts/install-codex.sh | bash -s -- --with-hooks
```

**Codex CLI on Windows PowerShell**

```powershell
irm https://raw.githubusercontent.com/boshu2/agentops/main/scripts/install-codex.ps1 | iex
```

**OpenCode**

```bash
curl -fsSL https://raw.githubusercontent.com/boshu2/agentops/main/scripts/install-opencode.sh | bash
```

**Other skills-compatible agents**

```bash
npx skills@latest add boshu2/agentops --cursor -g
```

Restart your agent after install. Then type `/quickstart` in your agent chat.

The `ao` CLI is optional but recommended — repo-native bookkeeping, retrieval, health checks, and terminal workflows.

**macOS**

```bash
brew tap boshu2/agentops https://github.com/boshu2/homebrew-agentops
brew install agentops
ao version
```

**Windows PowerShell**

```powershell
irm https://raw.githubusercontent.com/boshu2/agentops/main/scripts/install-ao.ps1 | iex
ao version
```

You can also install from [release binaries](https://github.com/boshu2/agentops/releases) or [build from source](cli/README.md). Troubleshooting: [docs/troubleshooting.md](docs/troubleshooting.md). Configuration: [docs/ENV-VARS.md](docs/ENV-VARS.md).

---

## See It Work

**The problem:** Coding agents are useful, but most teams still run them like isolated chat sessions. Every session starts cold. Prior attempts, warnings, decisions, and fixes scatter across chats, commits, and memory — so agents repeat mistakes, miss edge cases, and leave no reviewable proof trail.

**What AgentOps does:** It compiles the engineering practices teams already trust — XP, BDD/Gherkin, DDD, TDD — into the workflow your agents actually run. Intent is broken into bounded slices, each slice gets a first failing test and a write scope, and every phase boundary is a gate that records evidence.

**One loop: intent in, verified change out — across Claude and Codex**

```text
$ ao rpi "add rate limiting to /login"
[research/claude]    found 3 prior auth changes in .agents/decisions/
[plan/claude]        proposed: token bucket, 5/min per IP, Redis-backed
[pre-mortem/codex]   WARN: Redis unreachable case unhandled
[implement/codex]    wrote middleware/ratelimit.go, 2 tests
[validate/claude]    go test ./... PASS, gate: WARN — missing jitter
[recorded]           .agents/runs/2026-05-07-rate-limit/
```

Research, plan, pre-mortem, implement, validate — each boundary is a gate, not a suggestion, and each leaves a file-backed trace. Mix models per phase: Claude discovers, Codex implements, a fresh Claude validates, all in one loop with state preserved across boundaries.

And when you want a second opinion before shipping: `/council --mixed`

```text
> /council --mixed validate this PR

[council] evidence packet sealed -> 6 judges across Claude Code and Codex CLI
[claude/judge-1] WARN - rate limiting missing on /login endpoint
[claude/judge-2] PASS - Redis integration follows middleware pattern
[codex/judge-1]  WARN - token bucket refill lacks jitter under burst
[codex/judge-2]  PASS - backoff bounds match retry policy
Consensus: WARN - fix /login rate limit and add refill jitter before shipping
Recorded: .agents/council/<run-id>/verdict.md
```

The point is not a bigger prompt. The point is a repo that remembers what was tried, what worked, what failed, and what should constrain the next run.

---

## SDLC Control Plane, CDLC Mechanism

People know the SDLC. They do not need a new acronym before they understand the problem. Publicly, AgentOps is an **SDLC control plane for agentic software development**.

Inside that control plane is the **Context Development Life Cycle (CDLC)**: the lifecycle for the context agents consume. DevOps made delivery operational for human teams. AgentOps makes context operational for agent teams.

Every token should carry one of six payloads: **intent, boundary, evidence, decision, constraint, or next action**. If it carries none of those, it probably does not belong in the prompt.

The narrow waist is deliberately small:

| Practice | What AgentOps uses it for |
|---|---|
| **BDD / Gherkin** | Dense intent in observable behavior terms |
| **DDD** | Shared names, bounded contexts, and a vocabulary humans and agents can both use |
| **Hexagonal architecture** | Ports and adapters that keep runtime, tool, and vendor details outside the core loop |
| **TDD** | A local executable done condition for each slice |

Everything else plugs into that waist: CI/CD repeats the proof, SRE/DORA measures fitness, ADRs and provenance preserve why-memory, wikis and ratchets preserve durable learning, and Agile/XP keeps work in small vertical slices instead of speculative waterfall plans.

Atomic process is the rule: one behavior, one bounded context, one first failing test, one write scope, one acceptance proof, and one learning only when it changes future behavior.

That waist is executable, not advisory. `GOALS.md` declares intent as directives; `/scenario` and `ao goals render` turn each directive into behavioral acceptance examples — exportable as Gherkin `.feature` files; `ao rpi phased --domain <name>` builds inside one bounded context with a declared read scope; and `ao goals measure` scores whether the result actually satisfies the spec. Intent, behavior, build, and validation stay linked end to end — the executable-spec chain.

---

<!-- agentops:claim:AOP-CLAIM-README-FACTORY-CONTEXT -->

## What AgentOps Gives You

Four layers. Each solves a different problem. All four compound.

| Layer | Problem | What changes |
|-------|---------|--------------|
| **Bookkeeping** | Agents forget what they tried, why they changed course, and what evidence mattered | `.agents/` captures run packets, handoffs, findings, citations, decisions, verdicts, retros, and post-mortems. *The work leaves a trace.* |
| **Context Compiler** | Every session starts from zero | `ao context assemble` builds phase-scoped packets. `ao lookup` retrieves decay-ranked knowledge on demand. Skills and execution packets make context explicit; hooks are optional adapters. *Your agent starts loaded, not cold.* |
| **Validation Gates** | Agents ship confident garbage | `/pre-mortem`, `/vibe`, `/council` — multi-model consensus validates plans before build and code before commit. Gates block, not advise. *Three fresh judges catch what one agent can't.* |
| **Knowledge Flywheel** | Lessons disappear between sessions | `/forge` extracts learnings from the bookkeeping trail. `ao flywheel close-loop` scores and promotes. `/evolve` fixes the worst gap autonomously. `/dream` compounds overnight. *Session 15 starts with everything session 1 learned.* |

All state lives in local `.agents/` — plain text you can grep, diff, and review. No AgentOps-managed telemetry or hosted control plane. Runtime-neutral across Claude Code, Codex CLI, Cursor, and OpenCode.

<!-- agentops:claim:AOP-CLAIM-README-COMPETITIVE-MEMORY -->

### Why not just use Notion or Confluence?

| Notion / Confluence | AgentOps `.agents/` |
|---|---|
| Written for humans; agents can't traverse it efficiently | LLM Wiki of Markdown — agents read it natively |
| Lives in SaaS, not your repo | Lives in `.agents/` next to the code |
| Not version-controlled with your code | Diffable, branchable, mergeable |
| No decay ranking, no retrieval scoring | `ao lookup` and `ao context assemble` return bounded, cited context |
| No validation gates, no automated capture | Sessions write to it automatically; councils validate it |
| Doesn't compound; you maintain it manually | Daemon defrags, evolves, and compounds it overnight |
| Read-only artifact | Writes itself: agents that use it also produce it |

`.agents/` is a wiki both humans and agents read: agents traverse the markdown natively, and you can open the same directory as an Obsidian vault — `[[wikilinks]]` resolve and every entry diffs in git. Maintenance is mechanical, not voluntary: the agents that consume the wiki also produce it.

More: [docs/wiki-for-agents.md](docs/wiki-for-agents.md) · [docs/trust-factory.md](docs/trust-factory.md).

---

## Why Context Needs a Lifecycle

DevOps proved that disciplined systems around indeterministic workers produce reliable output. SRE proved it again with SLOs and error budgets. Kubernetes proved it for infrastructure with control loops. Coding agents are the next indeterministic worker class. Same playbook. New substrate.

Every primitive software engineering already gave us has a counterpart in the agent world:

| Software Engineering | Coding-Agent World |
|---|---|
| Source code | Context (corpus, planning rules, learnings) |
| SDLC | CDLC (Context Development Life Cycle) |
| Libraries (Maven, npm, crates.io) | Context libraries (the `.agents/` corpus) |
| Compilers | Context compilers (`ao compile` → wiki) |
| Code review | Multi-model councils |
| CI/CD | Validation gates (`/vibe`, `/pre-mortem`) |
| Postmortems | Automated postmortems (`/post-mortem` → learnings) |
| Runbooks | Skills + planning rules |
| Software factories | Software factory daemon (`ao daemon`) |
| Markdown / Git / Linux (open primitives) | LLM Wiki of Markdown |
| Open-source corpus | Your private corpus (`.agents/` in your repo) |

Major engineering organizations are reorganizing around feeding their agents the right context — restructuring teams, building internal context platforms, hiring "context engineering" leads. AgentOps is that pattern for solo developers and small teams: an SDLC control plane whose core job is context compilation. Same playbook. Same asset class. Different scale.

LLMs are engines. Context is fuel. You can't tune the engine — that's the model vendor's job. But you can engineer the fuel. The CDLC is how the SDLC control plane does that work. Full treatment: [docs/cdlc.md](docs/cdlc.md).

---

## Quick Start

Inside a repo, use the path that matches what you are trying to do.

<!-- agentops:claim:AOP-CLAIM-README-FIRST-VALIDATED -->

| Path | Run | Done when |
|------|-----|-----------|
| **First repo setup** | `ao quick-start`, then `/quickstart` | AgentOps reports repo readiness and a next action |
| **First validated change** | `/rpi "a small goal"` | Discovery, implementation, validation, and learning closeout leave evidence in `.agents/` |
| **Review something now** | `/council validate this PR` or `/vibe recent` | You get a consolidated verdict and an evidence record in `.agents/` before shipping |

New project? Use the guided CLI seed first:

```bash
ao quick-start     # Canonical
ao quickstart      # Stable alias
```

That command applies the repeatable core seed: `.agents/`, `GOALS.md`, AgentOps instructions, starter knowledge, and readiness guidance. Use `/bootstrap` after that when you want the product/operations layer: `PRODUCT.md`, `README.md`, `PROGRAM.md`/`AUTODEV.md`, and optional hooks.

Already installed? Ask your agent for the next action:

```text
/quickstart
```

If you installed the CLI, check your local setup:

```bash
ao doctor
ao demo
```

The demo path shows the 3.0 product loop: visible domain/practice packet,
bounded task context, mixed Claude/Codex council verdict, tracked follow-up
work, and the optional scheduled compounding lane.
For the exact first-session command path, see
[AgentOps 3.0 First-Value Path](docs/first-value-path.md). For copy, gist,
and launch-post language, see the
[AgentOps 3.0 Explainer Kit](docs/agentops-3-explainer-kit.md). For launch
video planning, see the
[AgentOps 3.0 YouTube Starter Series](docs/agentops-3-youtube-starter-series.md).
For the evidence loop behind PMF claims, see
[AgentOps 3.0 PMF Evidence Loop](docs/agentops-3-pmf-evidence-loop.md).

Full catalog: [docs/SKILLS.md](docs/SKILLS.md) · Unsure what to run? [Skill Router](docs/SKILL-ROUTER.md)

---

## Skills

Every skill works alone. Flows compose them when you want more structure.

| Skill | Use it when |
|-------|-------------|
| `/quickstart` | You want the fastest setup check and next action |
| `/council` | You want independent judges — optionally across Claude and Codex — to evaluate one evidence packet and return a consolidated verdict |
| `/research` | You need codebase context and prior learnings before changing code |
| `/pre-mortem` | You want to pressure-test a plan before implementation |
| `/implement` | You want one scoped task built and validated |
| `/rpi` | You want discovery, build, validation, and bookkeeping in one flow |
| `/vibe` | You want a code-quality and risk review before shipping |
| `/evolve` | You want a goal-driven improvement loop with regression gates |
| `/dream` | You want overnight knowledge compounding that never mutates source code |

Full reference: [docs/SKILLS.md](docs/SKILLS.md).

---

## The `ao` CLI

The `ao` CLI is the repo-native control plane behind the skills. It handles retrieval, health checks, compounding, goals, and terminal workflows.

<!-- agentops:claim:AOP-CLAIM-README-EVOLVE-AUTONOMOUS -->

```bash
ao quick-start                            # Set up AgentOps in a repo
ao doctor                                 # Check local health
ao demo                                   # See the council-first value path
ao search "query"                         # Search session history and local knowledge
ao lookup --query "topic"                 # Retrieve curated learnings and findings
ao context assemble                       # Build a task briefing
ao rpi phased "fix auth startup"          # Run the phased lifecycle from the terminal
ao evolve --max-cycles 1                  # Run one autonomous improvement cycle
ao overnight setup                        # Prepare private Dream runs
ao metrics health                         # Show flywheel health
```

Full reference: [CLI Commands](cli/docs/COMMANDS.md).

---

## Two ways to use it: hand agents and the software factory

| Surface | When to use it | What it looks like | Operator role |
|---------|---------------|-------------------|---------------|
| **Hand agents** (skills surface) | Active work, exploration, high-stakes decisions, ambiguous scope | `/research`, `/plan`, `/pre-mortem`, `/council`, `/rpi` invoked from chat | Driving — agents respond, you steer |
| **Software factory** (daemon) | Vetted, well-defined work; overnight compounding; bulk processing | `ao schedule` + `ao daemon` running dream / evolve / compile / defrag / forge unattended; mix-and-match councils per phase | Operator — you set cadence and quality bars; the factory runs |

**Hand agents** — when you're driving. Skills (`/rpi`, `/council`, `/pre-mortem`, `/vibe`) work in chat. Different rigor levels available — light skills for exploratory work, full RPI loop for everything that should be tracked, council validation before shipping.

<!-- agentops:claim:AOP-CLAIM-README-AUTONOMOUS-FLYWHEEL -->

**Software factory** — when work is vetted and ready. The `ao daemon` runs scheduled jobs against your local subscription on your hardware. Mix and match models per phase: Claude for discovery, Codex for implementation, a fresh Claude for validation, an open-weights local model for overnight defrag. Run Dream overnight, then Evolve in the morning against a fresher corpus.

→ [scheduling reference](docs/scheduling.md) · [example schedules](examples/schedules/).

---

## Docs

| Topic | Where |
|-------|-------|
| Published site | [boshu2.github.io/agentops](https://boshu2.github.io/agentops/) |
| Start navigating | [Docs index](docs/documentation-index.md) |
| New contributor orientation | [Newcomer guide](docs/newcomer-guide.md) |
| Working with `.agents/` | [Operator guide](docs/agents-operator-guide.md) |
| Full skill catalog | [Skills](docs/SKILLS.md) |
| CLI reference | [CLI commands](cli/docs/COMMANDS.md) |
| Architecture | [Architecture](docs/ARCHITECTURE.md) |
| FAQ | [FAQ](docs/FAQ.md) |

AgentOps is built on the 12-factor doctrine — see [12factoragentops.com](https://12factoragentops.com).

---

## What if the labs ship this natively?

They will. Anthropic's Managed Agents is the first move; others will follow. That's fine — the value isn't in this tool. It's in the corpus you build with it.

AgentOps is bridge infrastructure. Your `.agents/` directory is plain markdown in your repo. If a frontier vendor ships native equivalents in 12 months, your corpus carries forward. If we get acquired or change direction, your corpus is yours. If you outgrow the tool entirely, fork it, customize it, replace it — the corpus is what matters.

Open source forever. Built so you own the asset, not the tool.

---

## Contributing

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md). Agent contributors should also read [AGENTS.md](AGENTS.md) and use `bd` for issue tracking.

## License

Apache-2.0 · [Docs](docs/documentation-index.md) · [CLI Reference](cli/docs/COMMANDS.md)
