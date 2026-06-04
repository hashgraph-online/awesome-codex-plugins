<div align="center">

# AgentOps

[![GitHub stars](https://img.shields.io/github/stars/boshu2/agentops?style=social)](https://github.com/boshu2/agentops/stargazers)

### The SDLC control plane for agentic software development.

AgentOps sits on top of the coding harness you already use (Claude Code, Codex, Cursor, OpenCode) and adds the parts an engineering team would notice missing: a record of what was tried, gates between phases, and a corpus of learnings that survives the next session. State lives in `.agents/` next to your code, and you can mix Claude, Codex, or any model per phase.

*This repo was built with AgentOps. As of 2026-05-04 its `.agents/` held ~1,842 learnings, ~186 patterns, ~80 planning rules, and ~3,867 cited decisions captured during development. Re-run anytime: `bash scripts/corpus-stats.sh`.*

**New here? Start with [what AgentOps 3.0 is](docs/3.0.md) — the hookless-first CDLC north star.**

</div>

---

## See It Work

Most teams run coding agents as isolated chat sessions. Prior attempts, warnings, decisions, and fixes scatter across chats, commits, and human memory, so the same mistakes recur and nothing leaves a reviewable trail.

AgentOps breaks intent into bounded slices, gives each slice a first failing test and a write scope, and makes every phase boundary a gate that records evidence.

**A skill loads the corpus before writing a line of code:**

```text
> /research add rate limiting to /login

[research] loading context from .agents/...
[corpus]   3 prior auth decisions cited
            - .agents/decisions/2026-04-12-session-tokens.md
            - .agents/decisions/2026-03-08-rate-limit-policy.md
            - .agents/decisions/2026-02-19-redis-as-state-store.md
[corpus]   2 planning rules apply: rate-limit-jitter, redis-fallback-paths
[corpus]   1 learning:  2026-03-08 — token bucket without jitter caused thundering-herd at 5/min
[findings] middleware/auth.go owns /login; no rate limiting present
[findings] internal/cache already wires Redis with a fallback path
[plan]     token bucket, 5/min per IP, Redis-backed, jittered per 2026-03-08 learning
[recorded] .agents/runs/2026-05-08-rate-limit/research.md
```

Skills run in the harness you already use (Claude Code, Codex, Cursor, OpenCode). The corpus is the differentiator: the agent starts loaded with prior decisions, planning rules, and learnings instead of starting cold. From here, `/implement` or `/rpi` carries the same context into the build phase.

For a second opinion before shipping, `/council --mixed`:

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

AgentOps installs hookless — workflow is guided by skills + the `ao` CLI, and CI is the authoritative gate. If you want runtime hooks, author your own with the `hooks-authoring` skill.

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

The `ao` CLI is optional but recommended: repo-native bookkeeping, retrieval, health checks, and terminal workflows.

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

### Requirements

AgentOps degrades gracefully — skills check for a tool before using it. The only hard requirement is **a coding-agent runtime plus `git`**; everything else is optional and adds capability.

| Tool | Class | Purpose | Required? |
|------|-------|---------|-----------|
| `claude` / `codex` / `opencode` | Agent runtime | The harness AgentOps sits on top of | **Required** (one of) |
| `git` | Required | Version control — `.agents/` state lives next to your code | **Required** |
| `ao` | Required (recommended) | The AgentOps CLI: bookkeeping, retrieval, health, the loops | Recommended |
| `bd` (beads) + Dolt backend | Tracking | Git-native issue tracking (the mandatory task surface) | Optional |
| `ntm` / `ao agent` | Orchestration | Out-of-session substrate that runs whole `ao rpi`/`ao evolve` loops (NTM tmux swarm, MCP via `ao mcp serve`, or managed-agents) | Optional (out-of-session) |
| `gh` | PR / CI | Open PRs, query CI status | Optional |
| `go` | Build-from-source | Build `cli/bin/ao` from source (`go 1.26`) | Optional |
| `jq`, `rg`/ripgrep, `curl`, `openssl`, `sha256sum`, `tmux`, `cass` | Utilities | JSON parsing, search, downloads, hashing, sessions, history | Optional |

Full purpose / required-vs-optional / fallback-if-absent for every tool: **[docs/dependencies.md](docs/dependencies.md)**.

---

## Why context is the lifecycle

Coding agents are non-deterministic workers. Engineering already has a long history of getting reliable output from non-deterministic workers: disciplined process around them, with checks at the boundaries. The same primitives map across:

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
| Software factories | The in-session loop (`/rpi`, `/evolve`); out-of-session runs on a swappable substrate (NTM + MCP + managed-agents) |
| Markdown / Git / Linux (open primitives) | LLM Wiki of Markdown |
| Open-source corpus | Your private corpus (`.agents/` in your repo) |

You can't tune the model; that's the vendor's job. You can engineer the context you feed it. AgentOps treats that engineering as a Context Development Life Cycle (CDLC), with the same discipline DevOps brought to delivery.

The narrow waist is small on purpose:

| Practice | What AgentOps uses it for |
|---|---|
| **BDD / Gherkin** | Dense intent in observable behavior terms |
| **DDD** | Shared names, bounded contexts, and a vocabulary humans and agents can both use |
| **Hexagonal architecture** | Ports and adapters that keep runtime, tool, and vendor details outside the core loop |
| **TDD** | A local executable done condition for each slice |

Everything else plugs into that waist: CI/CD repeats the proof, SRE/DORA measures fitness, ADRs and provenance preserve why-memory, wikis and ratchets preserve durable learning, and Agile/XP keeps work in vertical slices. The atomic unit is one behavior, one bounded context, one failing test, one write scope, and one acceptance proof. A new learning is added only when it would change a future run.

The waist is executable. `GOALS.md` declares intent as directives; `/scenario` and `ao goals render` turn each directive into Gherkin acceptance examples; `ao rpi phased --domain <name>` builds inside one bounded context with a declared read scope; `ao goals measure` scores whether the result satisfies the spec. Intent, behavior, build, and validation stay linked end-to-end.

Full treatment: [docs/cdlc.md](docs/cdlc.md).

---

<!-- agentops:claim:AOP-CLAIM-README-FACTORY-CONTEXT -->

## What AgentOps Gives You

Four layers that compound:

| Layer | Problem | What changes |
|-------|---------|--------------|
| **Bookkeeping** | Agents forget what they tried, why they changed course, and what evidence mattered | `.agents/` captures run packets, handoffs, findings, citations, decisions, verdicts, retros, and post-mortems |
| **Context Compiler** | Every session starts cold | `ao context assemble` builds phase-scoped packets; `ao lookup` retrieves decay-ranked knowledge on demand; skills and execution packets make context explicit; runtime hooks are deliberately custom, not the default path |
| **Validation Gates** | Agents ship confident garbage | `/pre-mortem`, `/vibe`, `/council`: multi-model consensus validates plans before build and code before commit; gates block, not advise |
| **Knowledge Flywheel** | Lessons disappear between sessions | `/forge` extracts learnings from the bookkeeping trail, `ao flywheel close-loop` scores and promotes them, `/evolve` runs a bounded reconciliation loop, `/dream` prepares compounding runs |

All state lives in local `.agents/`: plain text you can grep, diff, and review. No AgentOps-managed telemetry or hosted control plane. Runtime-neutral across Claude Code, Codex CLI, Cursor, and OpenCode.

<!-- agentops:claim:AOP-CLAIM-README-COMPETITIVE-MEMORY -->

### Why not just use Notion or Confluence?

| Notion / Confluence | AgentOps `.agents/` |
|---|---|
| Written for humans; agents can't traverse it efficiently | LLM Wiki of Markdown; agents read it natively |
| Lives in SaaS, not your repo | Lives in `.agents/` next to the code |
| Not version-controlled with your code | Diffable, branchable, mergeable |
| No decay ranking, no retrieval scoring | `ao lookup` and `ao context assemble` return bounded, cited context |
| No validation gates, no automated capture | Sessions write to it automatically; councils validate it |
| Doesn't compound; you maintain it manually | The loop compounds it as a side effect of use: `/evolve`, `/compile`, `ao defrag`, `ao maturity` |
| Read-only artifact | Writes itself: agents that use it also produce it |

`.agents/` is a wiki both humans and agents read. Open it as an Obsidian vault; `[[wikilinks]]` resolve and every entry diffs in git. Maintenance happens as a side effect of use: the agents that consume the wiki also write to it.

More: [docs/wiki-for-agents.md](docs/wiki-for-agents.md) · [docs/trust-factory.md](docs/trust-factory.md).

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

That command applies the repeatable core seed: `.agents/`, `GOALS.md`, AgentOps instructions, starter knowledge, and readiness guidance. Use `/bootstrap` after that when you want the product/operations layer: `PRODUCT.md`, `README.md`, `PROGRAM.md`/`AUTODEV.md`, and optional custom hook guidance for runtimes where you deliberately author your own hooks.

Already installed? Ask your agent for the next action:

```text
/quickstart
```

If you installed the CLI, check your local setup:

```bash
ao doctor
ao demo
```

`ao demo` walks the product loop end-to-end: domain/practice packet, bounded task context, mixed Claude/Codex council verdict, tracked follow-up work, and the optional substrate-backed compounding lane. First-session walkthrough: [docs/first-value-path.md](docs/first-value-path.md).

Full catalog: [docs/SKILLS.md](docs/SKILLS.md) · Unsure what to run? [Skill Router](docs/SKILL-ROUTER.md)

---

## Skills

Every skill works alone. Flows compose them when you want more structure.

| Skill | Use it when |
|-------|-------------|
| `/quickstart` | You want the fastest setup check and next action |
| `/council` | You want independent judges (optionally across Claude and Codex) to evaluate one evidence packet and return a consolidated verdict |
| `/research` | You need codebase context and prior learnings before changing code |
| `/pre-mortem` | You want to pressure-test a plan before implementation |
| `/implement` | You want one scoped task built and validated |
| `/rpi` | You want discovery, build, validation, and bookkeeping in one flow |
| `/vibe` | You want a code-quality and risk review before shipping |
| `/evolve` | You want a goal-driven improvement loop with regression gates |
| `/dream` | You want bounded knowledge compounding that never mutates source code |

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
ao evolve --max-cycles 1                  # Run one bounded improvement cycle
ao compile                                # Rebuild the corpus (Mine → Grow → Defrag → Lint)
ao metrics health                         # Show flywheel health
```

Full reference: [CLI Commands](cli/docs/COMMANDS.md).

---

## Two ways to use it: in session and out of session

| Surface | When to use it | What it looks like | Operator role |
|---------|---------------|-------------------|---------------|
| **In session** (the AgentOps product) | All active work — exploration, high-stakes decisions, ambiguous scope, and the full loop | `/research`, `/plan`, `/pre-mortem`, `/council`, `/rpi`, `/evolve`, `/crank` invoked from a session; zero AgentOps-managed always-on infrastructure | Driving or on the loop; you steer, agents run the loop |
| **Out of session** (a substrate's job) | Vetted, well-defined work; always-on; queue-driven dispatch | The same loop run by a swappable orchestration substrate — an NTM tmux swarm, MCP (`ao mcp serve`), or managed-agents (`ao agent`) — each dispatching a whole `ao rpi` loop per ready bead | Operator: set cadence and quality bars on the substrate; it runs the loop |

**In session** is the AgentOps product. The whole loop — `rpi` (inner), `evolve` (outer), `crank`/`swarm` (in-session agent teams), the skills runtime, and the `.agents/` corpus — runs in a plain session with no daemon, no scheduler, and no cloud. Skills run from a session with rigor levels to match the work: light skills for exploration, the full RPI loop for anything that should be tracked, council validation before you ship. This is the zero-dependency sovereignty floor.

<!-- agentops:claim:AOP-CLAIM-README-AUTONOMOUS-FLYWHEEL -->

**Out of session** is delegated. AgentOps deleted its standalone daemon, scheduler, and overnight runner ([ADR-0009](docs/adr/ADR-0009-daemon-deletion-in-session-only.md)) — it has no core to protect, so always-on opts into a swappable orchestration substrate instead. The reference substrate is the trio AgentOps actually runs on, none of it AgentOps-owned: **NTM** (a local tmux swarm whose workers each run `ao rpi <bead>` as the operator or a lead agent slings ready beads), **MCP** via `ao mcp serve` (exposes the `ao` tool surface to any MCP-aware harness), and **managed-agents** via `ao agent` (hosted, scheduled drivers). In every case the substrate dispatches a whole loop as one unit; it never drives the loop's insides. Mount Olympus (full-custom Rust) is the other reference implementation of the same loop — it keeps its own daemon because, unlike AgentOps, it is a sovereign product.

→ [What 3.0 is (north star)](docs/3.0.md) · [the canonical loop model](docs/architecture/canonical-loop-model.md) · [running the loop out of session](docs/3.0.md).

---

## Docs

| Topic | Where |
|-------|-------|
| **What 3.0 is (north star)** | [docs/3.0.md](docs/3.0.md) |
| Published site | [boshu2.github.io/agentops](https://boshu2.github.io/agentops/) |
| Start navigating | [Docs index](docs/documentation-index.md) |
| New contributor orientation | [Newcomer guide](docs/newcomer-guide.md) |
| Working with `.agents/` | [Operator guide](docs/agents-operator-guide.md) |
| Full skill catalog | [Skills](docs/SKILLS.md) |
| CLI reference | [CLI commands](cli/docs/COMMANDS.md) |
| Architecture | [Architecture](docs/ARCHITECTURE.md) |
| FAQ | [FAQ](docs/FAQ.md) |

AgentOps is built on the 12-factor doctrine; see [12factoragentops.com](https://12factoragentops.com).

---

## Limitations

- **AgentOps doesn't generate code.** It sits on top of Claude Code, Codex, Cursor, or OpenCode and adds bookkeeping, gates, and a corpus; the harness still does the writing.
- **No hosted control plane, no telemetry.** Every artifact lives in your repo. There's no shared dashboard across team members unless you commit `.agents/`; most operators do, but it's a choice.
- **Multi-model councils and Dream compounding runs cost tokens or local compute.** Running six judges across Claude and Codex on every PR isn't free; running them on a substrate (an NTM swarm or managed-agents) makes the cost predictable, not zero.
- **The `.agents/` corpus needs hygiene.** It grows over time. `ao defrag`, `ao maturity`, and `/dream` keep it healthy, but a neglected corpus rots like any other markdown vault.
- **There are a lot of skills.** Around eighty as of 2026-05-20. `/quickstart` and the [Skill Router](docs/SKILL-ROUTER.md) exist because nobody learns them all up front.

---

## What if the labs ship this natively?

They will. Anthropic's Managed Agents is the first move and others will follow. The durable value is the `.agents/` corpus you build, not the tool that builds it. That corpus is plain markdown in your repo: it carries forward to whatever ships next, survives if AgentOps changes direction, and is forkable if you outgrow it. Apache-2.0, no telemetry, no hosted control plane.

---

## Contributing

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md). Agent contributors should also read [AGENTS.md](AGENTS.md) and use `bd` for issue tracking.

## License

Apache-2.0 · [Docs](docs/documentation-index.md) · [CLI Reference](cli/docs/COMMANDS.md)
