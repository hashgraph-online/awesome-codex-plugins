<div align="center">

# AgentOps

[![GitHub stars](https://img.shields.io/github/stars/boshu2/agentops?style=social)](https://github.com/boshu2/agentops/stargazers)

### Autonomous code validation for coding agents

Coding agents declare "done" on code that is still wrong. AgentOps catches that. Before a change counts as done, something that didn't write it has to check it: a different model, or a test that actually runs. **No verdict = not done.** It sits on top of the agent you already use (Claude Code, Codex, Cursor, OpenCode).

</div>

---

## Install

Pick your runtime, then type `/quickstart` in the agent.

```bash
# Claude Code
claude plugin marketplace add boshu2/agentops
claude plugin install agentops@agentops-marketplace

# Codex CLI (macOS/Linux/WSL) — OpenCode: install-opencode.sh
curl -fsSL https://raw.githubusercontent.com/boshu2/agentops/main/scripts/install-codex.sh | bash
# Codex CLI (Windows):
irm https://raw.githubusercontent.com/boshu2/agentops/main/scripts/install-codex.ps1 | iex

# Gemini / Antigravity
curl -fsSL https://raw.githubusercontent.com/boshu2/agentops/main/scripts/install-agy.sh | bash

# Other skills-compatible agents (Cursor, etc.)
npx skills@latest add boshu2/agentops --cursor -g
```

The `ao` CLI is optional but recommended (bookkeeping, retrieval, the release gate):

```bash
brew tap boshu2/agentops https://github.com/boshu2/homebrew-agentops && brew install agentops   # macOS
# Windows: irm https://raw.githubusercontent.com/boshu2/agentops/main/scripts/install-ao.ps1 | iex
# Or release binaries / build from source (cli/README.md).
```

Installs hookless. The only hard requirement is an agent runtime and `git`; everything else degrades gracefully. Dependencies: [docs/dependencies.md](docs/dependencies.md) · Day-2 ops (update, backup, recovery): [docs/install-day2-ops.md](docs/install-day2-ops.md).

---

## What you get

<!-- agentops:claim:AOP-CLAIM-README-FACTORY-CONTEXT -->
<!-- agentops:claim:AOP-CLAIM-README-COMPETITIVE-MEMORY -->

- **A validation membrane.** Tests, gates, `/pre-mortem`, `/validate`, and `/council` prove or reject the work before you trust it. No verdict, not done.
- **A bookkeeper that outlives the session.** Work is tracked as beads, and every verdict is bound into a hash-chained provenance ledger: tamper-evident, grep-able, and portable across sessions and models. The record is the proof a change was actually checked — not a memory of one.
- **An evidence trail that's yours.** Every run, decision, and verdict lands in `.agents/` in your repo: grep-able, diff-able, portable to whatever model wins next quarter. AgentOps adds no hosted control plane and no telemetry; the corpus lives in your repo, not on our servers. Apache-2.0.
- **It runs on the agent you already pay for.** Claude Code, Codex, Cursor, OpenCode. Same skills, same corpus.

```text
> /validate --mixed   # the agent reported this PR done

[membrane] evidence sealed → fresh-context judges, Claude Code + Codex CLI
[claude/judge-1] REFUTE  /login has no rate limit — claimed "covered", isn't
[codex/judge-1]  REFUTE  token-bucket refill lacks jitter under burst
[claude/judge-2] PASS    redis integration follows the repo pattern
Verdict: HOLD — not done. Fix /login limit + refill jitter, then re-verify.
Recorded as a proof artifact — no verdict, not done.
```

<!-- agentops:claim:AOP-CLAIM-README-FIRST-VALIDATED -->
Already installed? Ask your agent `/quickstart`, or run `/rpi "a small goal"` to take one change through discovery, build, and validation end to end. The evidence lands in `.agents/`.

---

The rest is below the fold for anyone who wants the detail.

## Skills

Every skill works alone; flows compose them. Full catalog: [docs/SKILLS.md](docs/SKILLS.md) · [Skill Router](docs/SKILL-ROUTER.md).

| Skill | Use it when |
|---|---|
| `/quickstart` | you want the fastest setup check and next action |
| `/research` | you need codebase context and prior learnings before changing code |
| `/pre-mortem` | you want to pressure-test a plan before building |
| `/rpi` | you want discovery, build, validation, and bookkeeping in one flow |
| `/council` | you want independent judges (optionally Claude and Codex) to return one verdict |
| `/validate` | you want a code-quality and risk review before shipping |
| `/evolve` | a goal-driven improvement loop that runs without mutating source |

## The `ao` CLI

Repo-native control plane behind the skills. Full reference: [CLI commands](cli/docs/COMMANDS.md).

<!-- agentops:claim:AOP-CLAIM-README-EVOLVE-AUTONOMOUS -->

```bash
ao quick-start            # set up AgentOps in a repo
ao search "query"         # search history and local knowledge
ao lookup --query "topic" # retrieve curated learnings
ao context assemble       # build a task briefing
ao gate check --fast      # the release gate — verify before you push
ao compile                # rebuild the corpus
ao metrics health         # flywheel health
```

<!-- agentops:claim:AOP-CLAIM-README-AUTONOMOUS-FLYWHEEL -->
The whole loop runs in a plain session. No daemon, no scheduler, no cloud. For always-on work, it can hand each task to a background runner instead. Details: [docs/3.0.md](docs/3.0.md) · [operating loop](docs/architecture/operating-loop.md).

## The honest version

**Proven:** independent verification that records a verdict, and a durable, tamper-evident record of it. A change isn't done until something that didn't write it checks it, and that verdict is bound into the provenance ledger. No verdict, not done.

**Still measuring:** whether the accumulated corpus makes the next session measurably better. We won't claim it until the numbers say so ([ADR-0004](docs/adr/ADR-0004-corpus-moat-unproven-position-on-the-system.md), [ADR-0011](docs/adr/ADR-0011-escape-corpus-compounding-unproven-structural-starvation.md)).

AgentOps proves the work. It doesn't write the code; your agent still does that, and the cross-checks cost tokens. The `.agents/` folder is plain markdown your agents keep up as they go.

When the labs ship their own version of this, your `.agents/` folder comes with you. It's in your repo, in plain markdown, Apache-2.0.

---

[What 3.0 is](docs/3.0.md) · [docs index](docs/documentation-index.md) · [newcomer guide](docs/newcomer-guide.md) · [architecture](docs/ARCHITECTURE.md) · [FAQ](docs/FAQ.md) · built on the [12-factor doctrine](https://12factoragentops.com).

Contributing: [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) (agents: read [AGENTS.md](AGENTS.md), track work with `br`). License: Apache-2.0.
