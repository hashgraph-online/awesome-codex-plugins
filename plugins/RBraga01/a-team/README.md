<p align="center">
  <img src="assets/ATeam_full.png" alt="A Team logo" width="200">
</p>

 # A Team — A Complete Engineering Team in One Folder v1.1.0

Not a marketplace of agents you configure. A pre-configured, pre-enforced engineering team of 25 specialists — with a lead orchestrator, hard quality gates, and a Pipeline Auditor that verifies work was actually done, not just reported. Drop one folder into any project and it's operational from the first keystroke. Works on Claude Code, Codex CLI, Cursor, and OpenCode.

> **Born from the community.** A Team was built by studying, using, and needing to personalise several excellent open-source agent projects. The architecture combines the best patterns from each into a single, portable baseline. See [Acknowledgments](#acknowledgments) for the projects that made this possible.

**[→ Visual overview & live demo](https://rbraga01.github.io/a-team/)**

**Domain packs** — install any alongside A Team:
- **[builder-ai](https://github.com/RBraga01/builder-ai)** — LLM engineering quality (evals, RAG, prompt versioning, safety)
- **[builder-design](https://github.com/RBraga01/builder-design)** — AI UI design (states, streaming, accessibility, tokens)
- **[builder-product](https://github.com/RBraga01/builder-product)** — Product quality gates (PRD, metrics, research synthesis, AI validation)
- **[builder-growth](https://github.com/RBraga01/builder-growth)** — Growth & messaging (positioning, copy, experiments, retention)

---

## What It Does

A Team turns any AI coding assistant into a structured, self-enforcing engineering team. Instead of one general-purpose model trying to do everything, you get:

- **25 specialist agents**, each with a defined scope, model tier, and tool set
- **18 workflow skills** that gate what can happen and when
- **A lead orchestrator** that manages daily task flow, dispatch, and state
- **Hard enforcement hooks** that inject mandatory checks at session start and after every file edit
- **A pipeline auditor** that verifies agents actually ran required checks — not just claimed they did

The infrastructure is stateless by design. Every agent derives its context from files, not memory. Sessions can be interrupted and resumed without drift.

---

## Installation

Pick the method that fits your setup. All methods install the same files into your project directory.

### Option A — One-liner (recommended)

**Mac / Linux / WSL:**
```bash
bash <(curl -fsSL https://raw.githubusercontent.com/RBraga01/a-team/main/install.sh)
```

**Windows PowerShell:**
```powershell
irm https://raw.githubusercontent.com/RBraga01/a-team/main/install.ps1 | iex
```

To install into a specific directory, pass the path as an argument:
```bash
bash <(curl -fsSL https://raw.githubusercontent.com/RBraga01/a-team/main/install.sh) /path/to/project
```

---

### Option B — GitHub CLI

```bash
# Clone the repo (shallow, only latest commit)
gh repo clone RBraga01/a-team -- --depth 1

# Copy the infrastructure into your project
cp -r a-team/.claude  your-project/
cp -r a-team/skills   your-project/
cp -r a-team/hooks    your-project/
cp -r a-team/templates your-project/
cp    a-team/INIT_TEMPLATE.md your-project/INIT.md

# Clean up
rm -rf a-team
```

---

### Option C — Git (no GitHub CLI)

```bash
# Sparse clone — downloads only the necessary directories, not the full repo
git clone --filter=blob:none --sparse --depth 1 \
  https://github.com/RBraga01/a-team.git

cd a-team
git sparse-checkout set .claude skills hooks templates INIT_TEMPLATE.md

# Copy into your project
cp -r .claude skills hooks templates ../your-project/
cp INIT_TEMPLATE.md ../your-project/INIT.md

cd .. && rm -rf a-team
```

**Windows (PowerShell equivalent):**
```powershell
git clone --filter=blob:none --sparse --depth 1 `
  https://github.com/RBraga01/a-team.git

cd a-team
git sparse-checkout set .claude skills hooks templates INIT_TEMPLATE.md

Copy-Item -Recurse .claude,skills,hooks,templates ..\your-project\
Copy-Item INIT_TEMPLATE.md ..\your-project\INIT.md

cd .. ; Remove-Item a-team -Recurse -Force
```

---

### Option D — Download ZIP (no git required)

1. Go to [github.com/RBraga01/a-team](https://github.com/RBraga01/a-team)
2. Click **Code → Download ZIP**
3. Extract and copy `.claude/`, `skills/`, `hooks/`, `templates/` into your project root
4. Copy `INIT_TEMPLATE.md` as `INIT.md`

---

## Adding A Team to an Existing Project

If the project is already in progress, use `cp -rn` (no-clobber) when copying the folders so your existing files are not overwritten:

```bash
cp -rn a-team/.claude    ./
cp -rn a-team/skills     ./
cp -rn a-team/hooks      ./
cp -rn a-team/templates  ./
cp     a-team/INIT_TEMPLATE.md ./INIT.md
```

Then fill out `INIT.md` to describe **what already exists** — languages, frameworks, current test coverage, known technical debt. The orchestrator uses this to prune irrelevant agents; accuracy here matters more than on a greenfield project.

After running `/orchestrate init`, review `.agent-sync/TEAM.md` before doing any work. Restore any agent that was incorrectly pruned. Start the first session with `/orchestrate morning` to let the orchestrator read the repo state before touching anything.

> **Note:** If you already have a `.claude/settings.json`, do not let the install overwrite it — merge the A Team permissions manually to preserve your existing configuration.

---

## Quick Start

After installing, three steps to get the full team operational:

### 1. Fill out INIT.md

Open `INIT.md` and tick the checkboxes for your project:
- Primary languages (Go, Python, Kotlin, Swift, etc.)
- Tech stack (database, infra, CI/CD)
- Compliance scope (GDPR, PCI-DSS, etc.)
- Which AI platforms are active (Claude Code, Codex, Cursor, OpenCode)

Takes about 5 minutes.

### 2. Initialize the team

```
/orchestrate init
```

The orchestrator reads `INIT.md`, prunes irrelevant agents and skills, and generates:
- `.agent-sync/TEAM.md` — permanent record of the active roster
- `.agent-sync/ROUTING.md` — task routing table + file claims table

### 3. Start working

Every subsequent session, the `using-a-team` meta-skill is injected automatically via the `SessionStart` hook. No manual setup needed per session.

> **Tip:** Run `/orchestrate morning` to kick off the daily task cycle, or just start working — the enforcement hooks fire automatically on every session start and every file edit.

---

## Folder Layout

```
A Team/
├── README.md                  ← This file
├── CLAUDE.md                  ← Project overview loaded by Claude Code
├── AGENTS.md                  ← Agent roster & command reference
├── INIT_TEMPLATE.md           ← Template for project-specific init doc
│
├── .claude/
│   ├── settings.json          ← Permissions, hooks, worktree config
│   ├── agents/                ← 25 agent profiles (name, model, tools, instructions)
│   ├── commands/              ← Slash commands (/orchestrate, /plan, /quality-gate, …)
│   └── rules/                 ← Coding and workflow standards loaded by all agents
│
├── skills/                    ← 18 workflow skill modules
│   ├── using-a-team/          ← Meta-skill: mandatory trigger map
│   ├── verification-before-completion/
│   ├── test-driven-development/
│   ├── systematic-debugging/
│   ├── brainstorming/
│   ├── subagent-driven-development/
│   ├── using-git-worktrees/
│   ├── executing-plans/
│   ├── writing-plans/
│   ├── dispatching-parallel-agents/
│   ├── finishing-a-development-branch/
│   └── writing-skills/
│
├── hooks/
│   └── session-start.md       ← Injected at every session start
│
├── .cursor-plugin/            ← Cursor IDE integration
├── .codex-plugin/             ← Codex CLI integration
├── .opencode/                 ← OpenCode integration
│
└── tests/                     ← Harness test suite for A Team itself
```

---

## Initialization in Detail

### INIT.md

The project's scope declaration. The orchestrator reads it once to decide which agents and skills are relevant. Fill it out before running `/orchestrate init`.

Key sections:
- **Primary programming languages** — controls which language-specialist agents survive pruning
- **Tech stack** — controls database-reviewer, e2e-runner, etc.
- **Communication tools** — controls chief-of-staff
- **Scope boundaries** — autonomous loops, E2E tests, documentation needs
- **Special constraints** — domain-specific guardrails enforced across all agents

### Pruning

The orchestrator deletes agent files and skill folders that don't apply to the declared scope. A Python-only project loses `go-reviewer`, `rust-reviewer`. A project with no E2E requirement loses `e2e-runner`. The workspace is leaner and agents no longer encounter context that doesn't apply to them.

After pruning, `.agent-sync/TEAM.md` records what was kept and why. This file is the source of truth for the active roster.

### ROUTING.md

Generated during init. Two sections:

1. **Task routing table** — maps task types to agents based on the declared stack (e.g., all `.py` changes route to `python-reviewer`).
2. **File Claims table** — starts empty; populated at dispatch time to prevent parallel agents from colliding on the same source files.

---

## The Session Lifecycle

### Session Start (automatic)

The `SessionStart` hook fires `cat skills/using-a-team/SKILL.md` at the beginning of every session. This injects the mandatory trigger map into context before any work begins.

The `PostToolUse` hook fires after every `Write` or `Edit`, reminding: use `code-reviewer` before committing, use `verification-before-completion` before claiming done.

### Session Start Checklist (enforced by the meta-skill)

1. Is `INIT.md` present? If not → fill it out first.
2. Is `.agent-sync/TEAM.md` present? If not → run `/orchestrate init` first.
3. What is the current task? → identify which skills and agents apply before starting.

---

## Agent Roster (25)

### Core Engineering

| Agent | Tier | Role | When to use |
|-------|------|------|-------------|
| **orchestrator** | T1 · opus-4-8 | Lead — reads INIT.md, prunes team, manages daily cycle | `/orchestrate` |
| **architect** | T1 · opus-4-8 | System design, ADRs, tech decisions | Architectural questions |
| **planner** | T2 · sonnet-4-6 | Implementation plans before coding | New features |
| **code-reviewer** | T2 · sonnet-4-6 | Code quality, security, maintainability | After every code change |
| **security-reviewer** | T2 · sonnet-4-6 | OWASP Top 10, secrets, injection | Auth, API, input, DB code |
| **tdd-guide** | T2 · sonnet-4-6 | RED → GREEN → REFACTOR enforcement | New features, bug fixes |
| **refactor-cleaner** | T2 · sonnet-4-6 | Dead code, duplication | Code maintenance |
| **build-error-resolver** | T2 · sonnet-4-6 | Build and type failures (minimal diffs only) | Build broken |
| **e2e-runner** | T2 · sonnet-4-6 | End-to-end test flows | Critical user journeys |
| **debugger** | T2 · sonnet-4-6 | Root-cause investigation (Phase 1 before fix) | Any bug |

### Language & Platform Specialists

All language specialists run at **T2 · sonnet-4-6** (or platform equivalent).

| Agent | Language / Platform | Trigger |
|-------|---------------------|---------|
| **database-reviewer** | PostgreSQL | SQL, migrations, schema changes |
| **go-reviewer** | Go | All `.go` file changes |
| **python-reviewer** | Python | All `.py` file changes |
| **rust-reviewer** | Rust | All `.rs` file changes |
| **kotlin-reviewer** | Kotlin / Android | All `.kt` changes, Jetpack Compose, Coroutines |
| **swift-reviewer** | Swift / iOS | All `.swift` changes, SwiftUI, Combine, ARC |
| **flutter-reviewer** | Flutter / Dart | All `.dart` changes, Riverpod/Bloc, null safety |

### Operational

| Agent | Tier | Purpose |
|-------|------|---------|
| **chief-of-staff** | T2 · sonnet-4-6 | Email, Slack, Calendar triage |
| **loop-operator** | T2 · sonnet-4-6 | Autonomous loop safety |
| **doc-updater** | T3 · haiku-4-5 | Codemaps, README, post-feature docs |
| **harness-optimizer** | T3 · haiku-4-5 | Pipeline auditor — detects rule evasion, blocks merge |
| **infra-reviewer** | T2 · sonnet-4-6 | Terraform, Docker, K8s, CI/CD — IaC safety and security |
| **compliance-reviewer** | T2 · sonnet-4-6 | GDPR, COPPA, PCI-DSS, SOC2, HIPAA — configured per project scope |
| **ai-reviewer** | T2 · sonnet-4-6 | LLM code — prompt injection, tool call safety, token cost, hallucination handling |
| **performance-profiler** | T3 · haiku-4-5 | Systematic profiling — baseline, locate bottleneck, validate improvement |

---

## Skill Library (18)

Skills are instruction modules that agents must consult before acting. Hard-gate skills cannot be skipped. Workflow skills define process.

### Hard Gates

| Skill | Rule |
|-------|------|
| **using-a-team** | Injected every session. If a skill or agent applies, it must be used. |
| **verification-before-completion** | Must run the actual command and read the actual output before claiming done. Cleans up workspace log/trace files after verification passes. |
| **test-driven-development** | Write the failing test before writing the implementation. No exceptions. |
| **systematic-debugging** | Phase 1 (reproduce and isolate) must complete before any fix is proposed. |
| **brainstorming** | Design session required before writing any new feature or component. |

### Workflow Skills

| Skill | Use case |
|-------|---------|
| **using-git-worktrees** | Create an isolated worktree before starting any development work |
| **subagent-driven-development** | Execute a plan by dispatching fresh subagents per task, with two-stage review |
| **executing-plans** | Run a written plan step-by-step in the current session |
| **writing-plans** | Create structured implementation plans from a spec |
| **dispatching-parallel-agents** | Launch 2+ independent tasks simultaneously |
| **finishing-a-development-branch** | Wrap up a branch before merge (coverage, review, changelog) |
| **writing-skills** | Create new A Team skills via TDD |
| **api-contract-first** | Hard gate — OpenAPI/protobuf contract before any API endpoint |
| **incident-response** | Workflow — production incident playbook (detect → contain → resolve → post-mortem) |
| **data-migration** | Hard gate — schema changes need rollback plan and dry-run before production |
| **performance-audit** | Workflow — baseline → profile → single change → measure delta |

---

## Mandatory Skill Trigger Map

If any of these situations apply, the corresponding skill or agent is not optional:

| You are about to… | Required first |
|-------------------|---------------|
| Write a new feature or component | `brainstorming` skill |
| Start any development work | `using-git-worktrees` skill |
| Write any code | `test-driven-development` skill |
| Debug a bug | `debugger` agent (Phase 1 first) |
| Claim anything is "done" | `verification-before-completion` skill |
| Write or modify code | `code-reviewer` agent afterward |
| Touch auth, API, input, DB | `security-reviewer` agent afterward |
| Change `.go` / `.py` / `.rs` files | language-specific reviewer agent |
| Merge a branch | `harness-optimizer` audit → `/quality-gate` |

**Rationalization red flags** — these thoughts mean a mandatory step is being skipped:
- "This change is too small to need a review"
- "I'll write the test after I confirm it works"
- "The tests were passing before so they're probably still passing"
- "The plan is in my head, I don't need to write it down"

---

## The Orchestrator Daily Cycle

The orchestrator operates as a stateless machine. It never assumes what happened in a prior session — it derives all state from files.

### `/orchestrate morning`

1. Reads `TASKS.md` — selects up to 3 tasks for today respecting `depends_on` constraints.
2. Assigns each task to the correct agent using `ROUTING.md`.
3. Writes `DAILY.md` Sections 1 + 2 (intent + execution plan).
4. **Presents the plan. Stops. Waits for explicit human approval.**
5. On approval: dispatches the first wave — all tasks with no dependencies.

### `/orchestrate tick` (after each async task completes)

1. Reads `DAILY.md` + all `.agent-sync/results/*.json`.
2. Marks completed tasks `[x]` with commit hash and test summary.
3. Adds ambiguous decisions to the Veto Buffer (Section 3).
4. Dispatches newly unblocked PENDING tasks.

### `/orchestrate report` (end of day)

1. Processes remaining results.
2. Compiles Evening Telemetry — tasks complete, commits, tests, veto items, proposed first task tomorrow.

### Veto Buffer

Every ambiguous autonomous decision gets a Veto Buffer entry: context, choice made, branch it's isolated on, action options. Only a human resolves Veto Buffer items. The orchestrator never resolves them.

---

## File Lock Protocol

Prevents parallel agents from colliding on the same source files before either merges.

### How it works

When the orchestrator dispatches an agent, it writes a row to the `## File Claims` table in `ROUTING.md` for each source file that agent will modify:

```
| File | Agent | Task | Status |
| src/auth/login.ts | code-reviewer | TASK-004 | in-progress |
```

Before dispatching a second agent, the orchestrator reads the table. If any target file is `in-progress` by a different agent, the new task is added to PENDING with a `depends_on` — not dispatched in parallel.

### Path normalization (worktree safety)

Because each parallel agent runs inside its own worktree directory (e.g., `../project-task-001/`), the same file appears at a different absolute path in every worktree. All paths written to or read from the File Claims table must be **relative to the git repository root** — never absolute, never worktree-local.

```bash
# Normalize from any worktree before every read or write
REPO_ROOT=$(git worktree list --porcelain | awk 'NR==1 {print $2}')
RELATIVE=$(realpath --relative-to="$REPO_ROOT" "$ABSOLUTE_PATH")
```

Without this, agent A locks `../project-task-001/src/auth/login.ts` while agent B looks up `src/auth/login.ts` — the lock is invisible to B and the collision happens anyway.

When a task completes without blockers, its File Claims rows are released. The next agent can then claim those files.

The `code-reviewer` also checks the File Claims table before starting any review. If a file it needs to review is claimed by a different active agent, it blocks and reports rather than proceeding.

**Scope:** source files only (`.ts`, `.kt`, `.py`, `.go`, `.rs`, etc.). Config files, docs, and test fixtures are not claimed.

---

## Pipeline Audit (harness-optimizer)

The harness-optimizer runs as a pipeline auditor before any branch merge. It reads terminal command history and task result files to verify agents actually ran required checks — not just reported that they did.

### What it checks

1. **verification-before-completion compliance** — For every completed task, the history must contain an actual test or build command (`npm test`, `pytest`, `go test ./...`, etc.) run after the last code change. If not → `EVASION`.

2. **code-reviewer compliance** — For every task that modified source files, a code-reviewer result must exist in `.agent-sync/results/`. If not → `EVASION`.

3. **File Claim hygiene** — If any File Claim row is still `in-progress` for a task already marked done in DAILY.md → `STALE CLAIM`.

### On evasion

The auditor writes `.agent-sync/AUDIT.md` with a `BLOCK MERGE` verdict. The orchestrator reads this file before dispatching `finishing-a-development-branch`. If it contains `BLOCK MERGE`, the branch cannot be finished — the failing tasks are routed back to their original agents for re-execution with proper compliance.

---

## Coding Standards (`.claude/rules/`)

All agents enforce these rules. Key principles with examples:

**Immutability**
```js
// [INVALID] — mutates in place
user.verified = true

// [VALID] — returns new copy
return { ...user, verified: true }
```

**Early returns** (max 4 nesting levels)
```js
// [INVALID] — nested conditionals
if (user) { if (user.active) { if (user.role === 'admin') { doWork() } } }

// [VALID] — early returns
if (!user) return
if (!user.active) return
if (user.role !== 'admin') return
doWork()
```

**Error handling — never silent**
```ts
// [INVALID]
try { await send() } catch (_) {}

// [VALID]
try { await send() } catch (err) { logger.error('send failed', { err }); throw err }
```

Full standards: `.claude/rules/coding-style.md`, `security.md`, `testing.md`, `orchestration.md`.

---

## Multi-CLI Integration

A Team is designed to run on one CLI or several simultaneously. Each platform reads from its own manifest but all agents share the same definitions and state directory.

### What each platform loads

| Platform | Agents | Skills | Rules | Hooks | Commands |
|----------|--------|--------|-------|-------|----------|
| **Claude Code** | `.claude/agents/` | `skills/` | `.claude/rules/` | `settings.json` hooks | `.claude/commands/` |
| **Codex CLI** | `.claude/agents/` (via agentsPath) | `skills/` | `.claude/rules/` | `onSessionStart` hook | — |
| **Cursor** | `.claude/agents/` (via agentsPath) | `skills/` | `.claude/rules/` | `onSessionStart` hook | — |
| **OpenCode** | — | `skills/` | — | — | `.opencode/commands/` |

### Running multiple CLIs on the same project

All CLIs share `.agent-sync/` (DAILY.md, ROUTING.md, TEAM.md, results/). This means:

- The orchestrator's state is visible regardless of which CLI triggered it.
- File Claims are written once and honoured by any CLI reading ROUTING.md.
- Hooks are **not** propagated across platforms — configure `onSessionStart` in each plugin manifest separately (already done in `.codex-plugin/` and `.cursor-plugin/`).

### Platform-specific behaviour

**Claude Code** is the primary platform. It has the full hook system (`SessionStart`, `PostToolUse`), slash commands, and native sub-agent dispatch via the `Agent` tool.

**Codex CLI** loads agents and skills from the same paths as Claude Code. It does not support `PostToolUse` hooks — the session-start reminder is injected but mid-session enforcement relies on the agents' own rules, not hooks.

**Cursor** loads agents and skills. Its rule injection depends on the `.cursor-plugin/` manifest's `rulesPath`. Slash commands are not available; use the skill invocation pattern instead.

**OpenCode** has command aliases in `.opencode/commands/` mapping to the same workflows. It does not have native agent or hook support — skills are invoked manually.

---

## Command Reference

```
/orchestrate init       Read INIT.md, prune team, generate TEAM.md + ROUTING.md
/orchestrate morning    Plan today's tasks (requires human approval before dispatch)
/orchestrate tick       Process completed task results, dispatch unblocked tasks
/orchestrate report     End-of-day telemetry

/plan                   Create implementation plan
/feature                Full feature workflow: brainstorm → plan → implement → review
/code-review            Review staged/recent changes
/security-review        Security audit
/debug                  Systematic root-cause debugging
/build-fix              Fix build errors (minimal diffs only)
/e2e                    Run end-to-end test suite
/refactor               Find and remove dead code
/quality-gate           Full pre-merge check (code + security + audit)
```

---

## Acknowledgments

A Team was built by studying the architecture and workflow patterns of the following open-source projects. No code or prompt text was copied verbatim — only concepts, patterns, and structural ideas were adapted and re-implemented from scratch.

| Project | What it informed |
|---------|-----------------|
| [Superpowers](https://github.com/obra/superpowers) | Skill-based methodology, TDD enforcement, subagent-driven development, and Git Worktree isolation patterns |
| [tick-md](https://github.com/Purple-Horizons/tick-md) | Logical task-state management using Markdown files and atomic Git commits as the state machine |
| [Switchman](https://github.com/switchman-dev/switchman) | Concurrent agent coordination and file-level conflict detection across parallel agent workspaces |
| [Armory](https://github.com/Mathews-Tom/armory) | Headless automated test suite for validating the semantic effectiveness of rules and prompts |
| [BMad Cursor Master Workflow Agent and Rules](https://github.com/BuildSomethingAI/cursor-custom-agents-rules-generator) | Short, density-focused rule files with mandatory [VALID]/[INVALID] code examples for LLM pattern replication |
| [claude-skills](https://github.com/alirezarezvani/claude-skills) | Modular skill library architecture with native tool integrations |
| [Pi-DCP](https://github.com/PSU3D0/pi-dcp) | Token optimization via hooks that prune redundant command history and debug logs from agent context |
| [GitAgent (Open GAP)](https://github.com/open-gitagent/opengap) | Agent identity standardization through structured files and framework-agnostic state contracts |

## License

MIT — see [LICENSE](LICENSE). You are free to use, modify, and distribute A Team in any project, commercial or otherwise, as long as the copyright notice is retained.

## Adding a New Agent

1. Create `.claude/agents/<name>.md` with the frontmatter (`name`, `description`, `allowedTools`, `model`) and instructions.
2. Add the agent to `.agent-sync/TEAM.md` (active roster).
3. Add a routing rule in `.agent-sync/ROUTING.md`.
4. Add the trigger condition to `skills/using-a-team/SKILL.md`.
5. Add a session-start check to `hooks/session-start.md` if the agent has a mandatory trigger.

## Adding a New Skill

Use the `/writing-skills` meta-skill. It walks through spec, TDD, and validation of the new skill before it is added to the library. After creation, register the trigger in `using-a-team/SKILL.md`.
