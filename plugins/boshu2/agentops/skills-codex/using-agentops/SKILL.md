---
name: using-agentops
description: "Run using agentops."
---
# AgentOps Operating Model

AgentOps is the operational layer for coding agents.

Publicly, it gives you four things:

- **Bookkeeping** — captured learnings, findings, and reusable context
- **Validation** — plan and code review before work ships
- **Primitives** — single skills, hooks, and CLI surfaces
- **Flows** — named compositions like `$research`, `$validate`, and `$rpi`

Technically, AgentOps acts as a context compiler: raw session signal becomes reusable knowledge, compiled prevention, and better next work.

## Core Flow: RPI

```
Research → Plan → Implement → Validate
    ↑                            │
    └──── Knowledge Flywheel ────┘
```

### Research Phase

```bash
$research <topic>      # Deep codebase exploration
ao search "<query>"    # Search existing knowledge
ao search "<query>" --cite retrieved  # Record adoption when a search result is reused
ao lookup <id>         # Pull full content of specific learning
ao lookup --query "x"  # Search knowledge by relevance
```

**Output:** `.agents/research/<topic>.md`

### Plan Phase

```bash
$pre-mortem <spec>     # Simulate failures (error/rescue map, scope modes, prediction tracking)
$plan <goal>           # Decompose into trackable issues
```

**Output:** Beads issues with dependencies

### Implement Phase

```bash
$implement <issue>     # Single issue execution
$crank <epic>          # Autonomous epic loop (uses swarm for waves)
$swarm                 # Parallel execution (fresh context per agent)
```

**Output:** Code changes, tests, documentation

### Validate Phase

```bash
$vibe [target]         # Code validation (finding classification + suppression + domain checklists)
$post-mortem           # Validation + streak tracking + prediction accuracy + retro history
$post-mortem --quick   # Quick-capture a single learning (folded the retired $retro)
```

**Output:** `.agents/learnings/`, `.agents/patterns/`

## Phase-to-Skill Mapping

| Phase | Primary Skill | Supporting Skills |
|-------|---------------|-------------------|
| **Discovery** | `$discovery` | `$brainstorm`, `$research`, `$plan`, `$pre-mortem` |
| **Implement** | `$crank` | `$implement` (single issue), `$swarm` (parallel execution) |
| **Validate** | `$validate` | `$vibe`, `$post-mortem`, `$forge` |

**Choosing the skill:**
- Use `$implement` for **single issue** execution. **Now defaults to TDD-first** — writes failing tests before implementing. Skip with `--no-tdd`.
- Use `$crank` for **autonomous epic execution** (loops waves via swarm until done). Auto-generates file-ownership maps to prevent worker conflicts.
- Use `$discovery` for the **discovery phase only** (brainstorm → search → research → plan → pre-mortem).
- Use `$validate` for the **validation phase only** (vibe → post-mortem → forge).
- Use `$rpi` for **full lifecycle** — delegates to `$discovery` → `$crank` → `$validate`.
- Use `$ratchet` to **gate/record progress** through RPI.

## Start Here (12 starters)

These are the skills every user needs first. Everything else is available when you need it.

| Skill | Purpose |
|-------|---------|
| `$quickstart` | Guided onboarding — run this first |
| `$research` | Deep codebase exploration |
| `$council` | Multi-model consensus review + finding auto-extraction |
| `$vibe` | Code validation (classification + suppression + domain checklists) |
| `$rpi` | Full RPI lifecycle orchestrator (`$discovery` → `$crank` → `$validate`) |
| `$implement` | Execute single issue |
| `$post-mortem --quick` | Quick-capture a single learning into the flywheel |
| `$status` | Single-screen dashboard of current work and suggested next action |
| `$goals` | Maintain GOALS.yaml fitness specification |
| `$push` | Atomic test-commit-push workflow |
| `$flywheel` | Knowledge flywheel health monitoring (σ×ρ > δ/100) |

## Advanced Skills (when you need them)

| Skill | Purpose |
|-------|---------|
| `$compile` | Active knowledge intelligence — Mine → Grow → Defrag cycle |
| `$inject` | Operationalize a mature `.agents` corpus into beliefs, playbooks, briefings, and gap surfaces (folded the retired `$knowledge-activation`) |
| `$brainstorm` | Structured idea exploration before planning |
| `$discovery` | Full discovery phase orchestrator (brainstorm → search → research → plan → pre-mortem) |
| `$plan` | Epic decomposition into issues |
| `$pre-mortem` | Failure simulation (error/rescue, scope modes, temporal, predictions) |
| `$post-mortem` | Validation + streak tracking + prediction accuracy + retro history |
| `$bug-hunt` | Root cause analysis |
| `$release` | Pre-flight, changelog, version bumps, tag |
| `$crank` | Autonomous epic loop (uses swarm for each wave) |
| `$swarm` | Fresh-context parallel execution (Ralph pattern) |
| `$evolve` | Goal-driven fitness-scored improvement loop |
| `$autodev` | PROGRAM.md autonomous development contract setup and validation |
| `$dream` | Interactive Dream operator surface for setup, bedtime runs, and morning reports |
| `$doc` | Documentation generation — repo docs (default), gold-standard README (`--mode=readme`), OSS doc packs (`--mode=oss`) |
| `$post-mortem --quick` | Quick-capture a learning (folded the retired `$retro`) |
| `$validate` | Full validation phase orchestrator (vibe → post-mortem → forge) |
| `$ratchet` | Brownian Ratchet progress gates for RPI workflow |
| `$forge` | Mine transcripts for knowledge — decisions, learnings, patterns |
| `$security` | Repository security scanning and release gating, plus the composable binary/prompt-surface suite — static analysis, dynamic tracing, offline redteam, policy gating |
| `$hooks-authoring` | Author and validate AgentOps runtime hooks |
| `$system-tuning` | Restore system responsiveness via safe, ordered process cleanup and agent-swarm hygiene |
| `$skill-auditor` | Two-pass audit of an existing SKILL.md against the unified template (15 checks) |
| `$skill-builder` | Scaffold or absorb new SKILL.md files against the unified template |

## Expert Skills (specialized workflows)

| Skill | Purpose |
|-------|---------|
| `$grafana-platform-dashboard` | Build Grafana platform dashboards from templates/contracts |
| `$swarm` | Parallel Codex agent execution (folded the retired `$codex-team`) |
| `$openai-docs` | Official OpenAI docs lookup with citations |
| `$reverse-engineer-rpi` | Reverse-engineer a product into feature catalog and specs |
| `$pr-research` | Upstream repository research before contribution |
| `$pr-implement` | Fork-based PR implementation |
| `$validate --mode=pr` | PR-specific validation and isolation checks (folded the retired `$pr-validate`) |
| `$pr-prep` | PR preparation and structured body generation |
| `$ship-loop` | Bot-paired internal-PR fast-lane cycle |
| `$complexity` | Code complexity analysis |
| `$product` | Interactive PRODUCT.md generation |
| `$handoff` | Session handoff for continuation |
| `$recover` | Post-compaction context recovery |
| `$session-bootstrap` | Universal init prompt — every agent runs this first (soc-vuu6.25) |
| `$trace` | Trace design decisions through history |
| `$provenance` | Trace artifact lineage to sources |
| `$beads` | Issue tracking operations |
| `$heal-skill` | Detect and fix skill hygiene issues |
| `$converter` | Convert skills to Codex/Cursor formats |

**To update installed skills:** re-run the install one-liner — `bash <(curl -fsSL https://raw.githubusercontent.com/boshu2/agentops/main/scripts/install.sh)`. (There is no `$update` skill; skill refresh is an install-script concern.)

## Knowledge Flywheel

Every `$post-mortem` promotes learnings and patterns into `.agents/` so future `$research` starts with better context instead of zero.

Inspect, lint, and triage the `.agents/` write surface contract via `ao agents inspect | lint | doctor` (`doctor` rolls up inspect + lint + orphan/stray-dir report; `--strict` fails on orphans).

## Runtime Modes

AgentOps has several runtime modes. Do not assume hook automation exists everywhere.

| Mode | When it applies | Start path | Closeout path | Guarantees |
|------|-----------------|------------|---------------|------------|
| `substrate` (out-of-session) | A swappable orchestration substrate available out-of-session: an NTM tmux swarm, MCP (`ao mcp serve`), or managed-agents (`ao agent`) | The operator or a lead agent runs `bd ready` and dispatches a whole loop per bead (`ao rpi <bead>`); cron / managed triggers run maintenance | The substrate owns the merge gate (CI-green is the signal) and triggers the knowledge-flywheel feedback | The substrate orchestrates *whole* `ao rpi` loops — it never sees the loop's insides; the seam is substrate → `ao` as a subprocess. There is no in-CLI `runtime=gc` executor. Codex skills still chain `$skill` invocations for lead orchestration. See [docs/3.0.md](https://github.com/boshu2/agentops/blob/main/docs/3.0.md). |
| `codex-hookless-fallback` | Codex Desktop / Codex CLI without hook surfaces | `ao codex start` or `ao codex ensure-start` | `ao codex stop` or `ao codex ensure-stop` | Explicit startup context, citation tracking, transcript fallback, and close-loop metrics without hooks |
| `manual` | Codex cannot resolve repo/runtime state automatically | `ao inject` / `ao lookup` | `ao forge transcript` + `ao flywheel close-loop` | Works everywhere, but lifecycle actions are operator-driven |

Codex skill orchestration default is `$skill` chaining. Inside a Codex skill,
invoke peer skills such as `$rpi`, `$discovery`, `$crank`, `$validate`,
`$evolve`, `$plan`, and `$pre-mortem` directly. Use `ao rpi` or
similar lifecycle wrapper commands only when the user explicitly asks for a
terminal wrapper or when documenting a non-skill runtime path. Operational CLI
commands such as `ao lookup`, `ao goals measure`, `ao ratchet`, and
`ao codex ensure-start` remain valid substrate calls.

In Codex hookless mode, entry skills such as `$rpi`, `$research`, `$implement`,
`$status`, `$recover`, and `$discovery` should ensure the start path once per
thread. Dedicated closeout skills such as `$validate`, `$post-mortem`, and
`$handoff` should ensure the stop path once per thread.

## Issue Tracking

This workflow uses beads for git-native issue tracking:

```bash
bd ready              # Unblocked issues
bd show <id>          # Issue details
bd close <id>         # Close issue
bd vc status          # Inspect Dolt state if needed (JSONL auto-sync is automatic)
```

## Examples

### Startup Context Loading

1. The first entry skill in a Codex thread should run `ao codex ensure-start`, which records startup once per thread and skips duplicate startup automatically.
2. AgentOps inspects `.agents/`, runs safe close-loop maintenance, syncs MEMORY.md, and writes `.agents/ao/codex/startup-context.md`.
3. Surfaced learnings, patterns, and findings are cited as `retrieved`.
4. Use `ao lookup` for automatic citations during work, or `ao search --cite retrieved|reference|applied` when a search result is adopted.
5. End the session through `$validate`, `$post-mortem`, or `$handoff`, which ensure `ao codex ensure-stop` once for the current thread, then verify loop health with `ao codex status` when needed.

**Result:** In hookless Codex mode, the agent still gets prior context, citations, and closeout without hidden hooks.

### Workflow Reference During Planning

**User says:** "How should I approach this feature?"

**What happens:**
1. Agent references this skill's RPI workflow section
2. Agent recommends Research → Plan → Implement → Validate phases
3. Agent suggests `$research` for codebase exploration, `$plan` for decomposition
4. Agent explains `$pre-mortem` for failure simulation before implementation
5. User follows recommended workflow with agent guidance

**Result:** Agent provides structured workflow guidance based on this meta-skill, avoiding ad-hoc approaches.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Skill not loaded | Startup path not run | Run `ao session bootstrap`, then `ao inject` / `ao lookup`; for Codex lifecycle recovery, run `ao codex ensure-start` or `ao codex start` explicitly |
| Outdated skill catalog | This file not synced with actual skills/ directory | Update skill list in this file after adding/removing skills |
| Wrong skill suggested | Natural language trigger ambiguous | User explicitly calls skill with `/skill-name` syntax |
| Workflow unclear | RPI phases not well-documented here | Read full workflow guide in README.md or docs/ARCHITECTURE.md |

## Local Resources

### scripts/

- `scripts/validate.sh`
