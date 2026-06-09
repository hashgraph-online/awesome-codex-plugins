# HOTL Plugin for Codex, Claude Code, and Cline

**HOTL (Human-on-the-Loop)** is an AI coding workflow plugin and skill pack for **Codex**, **Claude Code**, and **Cline**. It keeps implementation work grounded in a design, an executable workflow, review checkpoints, and verification evidence.

Use HOTL for feature work, refactors, and risky changes where "just start coding" is too loose. It stays out of the way for code questions, debugging, and obvious one-line fixes.

Adapter templates are also available for Cursor and GitHub Copilot.

## Table of Contents

- [Why HOTL](#why-hotl)
- [Quick Start](#quick-start)
- [First HOTL Run](#first-hotl-run)
- [The HOTL Workflow](#the-hotl-workflow)
- [When To Use It](#smart-task-routing)
- [Commands & Usage](#commands--usage)
- [Skills Overview](#skills-overview)
- [Updating](#updating)
- [Supported Tools](#supported-tools)
- [Automation Templates](#automation-templates)
- [Repository Structure](#repository-structure)
- [Contributing](#contributing)

## Why HOTL

Most AI coding sessions fail in predictable ways: code starts before requirements are clear, plans skip verification, risky changes execute without review, and the agent claims success without evidence.

HOTL prevents all four by enforcing structured workflows for implementation tasks while staying out of the way for code questions, quick fixes, and debugging.

If someone searches for a "HOTL plugin" or a "Human-on-the-Loop AI coding workflow", this repo is the main project: it contains the canonical HOTL skills, workflow templates, and installation docs for Codex, Claude Code, and Cline.

## Quick Start

Pick the install path for the tool you use. Codex users should prefer plugin install; native skills are only for older Codex builds or local HOTL development.

### Claude Code

```text
/plugin marketplace add yimwoo/hotl-plugin
/plugin install hotl@hotl-plugin
```

### Codex

Recommended plugin install for both Codex CLI and Codex app users:

```bash
git clone https://github.com/yimwoo/hotl-plugin /tmp/hotl-plugin
bash /tmp/hotl-plugin/install.sh --codex-plugin
```

Restart Codex, then install or enable HOTL from the plugin directory.

Codex CLI:

```text
codex
/plugins
```

In the plugin browser, switch to **Local Plugins**, open **HOTL**, and select
`Install plugin`. If HOTL is installed but disabled, press `Space` to enable it.

Codex app: open **Plugins**, switch to **Local Plugins**, and install HOTL. The CLI and app share the same Codex plugin configuration when they use the same Codex profile.

Plugin install does not automatically remove an older native-skills install. If both are present, Codex may discover duplicate HOTL sources. See [`docs/README.codex.md`](docs/README.codex.md) for the recommended migration path.

Native skills fallback for older Codex builds or local HOTL development: clone to `~/.codex/hotl` and symlink `~/.agents/skills/hotl` to its `skills/` directory. In that mode, `~/.codex/hotl` is the stable channel and should track `origin/main`. Full guide: [`docs/README.codex.md`](docs/README.codex.md).

### Cline

```bash
curl -fsSL https://raw.githubusercontent.com/yimwoo/hotl-plugin/main/install-cline.sh | bash
```

Full guide: [`docs/README.cline.md`](docs/README.cline.md)

## First HOTL Run

After install, start with a design request. HOTL will choose the right workflow stage and save durable artifacts in the project.

| Tool | Try this |
| --- | --- |
| Codex | `@hotl brainstorm this feature before coding: <your feature>` |
| Claude Code | `/hotl:brainstorm <your feature>` |
| Cline | `brainstorm this feature before coding: <your feature>` |

Typical outputs:

- Design doc: `docs/designs/YYYY-MM-DD-<slug>-design.md`
- Executable workflow: `docs/plans/YYYY-MM-DD-<slug>-workflow.md`
- Execution state and reports: `.hotl/state/` and `.hotl/reports/`

## The HOTL Workflow

Implementation tasks follow eight phases:

| Phase | What happens |
| --- | --- |
| **Brainstorm** | Clarify requirements. Compare approaches. Define intent, verification, and governance contracts. Save a design doc in `docs/designs/`. |
| **Write Workflow** | Use `writing-plans` to generate `docs/plans/YYYY-MM-DD-<slug>-workflow.md` with steps, verification, loop conditions, and gates. |
| **Lint** | Self-check built into planning. Structural lint runs automatically in execution preflight. |
| **Branch** | Resolve an execution root. Default is a git worktree on `hotl/<slug>`; `worktree: false` stays in the current checkout and may switch/create the target branch; `worktree: host` keeps the current feature branch exactly as provided by Codex or another host tool. Non-HOTL dirty files and protected-branch host mode hard-fail unless explicitly allowed. |
| **Execute** | Run the plan in loop, manual, or subagent mode. |
| **Review** | Review findings are checked against the codebase and HOTL contracts before acting. |
| **Verify** | Run tests, lint, and verify commands. No green light without proof. |
| **Finish** | Decide what happens to the execution branch/worktree: merge back, publish/PR, keep, or discard. HOTL records that disposition so execution history stays understandable later. |

Here is what a real HOTL feature-delivery session can look like:

```text
Execution Summary

| Step                                          | Status             | Iterations |
|-----------------------------------------------|--------------------|------------|
| Step 1: Add feature flag and config wiring    | Done               | 1          |
| Step 2: Add backend endpoint for saved views  | Done               | 2          |
| Step 3: Add database migration and model      | Done               | 1          |
| Step 4: Build saved views panel UI            | Done               | 3          |
| Step 5: Connect UI to API state flow          | Done               | 2          |
| Step 6: Add analytics + audit logging         | Done               | 1          |
| Step 7: Add unit tests for reducers/hooks     | Done (28/28)       | 2          |
| Step 8: Add API integration tests             | Done (12/12)       | 2          |
| Step 9: Add e2e coverage for create/apply     | Done (6/6)         | 3          |
| Step 10: Run lint and typecheck               | Done               | 2          |
| Step 11: Run full test suite                  | Done (46/46)       | 1          |
| Step 12: Human review and acceptance          | Approved           | 1          |

9 files modified, 1 migration added, 3 new test files. Unit, integration, and e2e suites all passing.
```

Every step has a verify command. If verification fails, execution stops and reports instead of silently claiming success.

**Resumable execution:** HOTL persists state in `.hotl/state/` so interrupted runs can pick up where they stopped. Resume is verify-first: HOTL re-checks the last step before advancing. State persistence and resumable execution require [`jq`](https://jqlang.github.io/jq/) — install it with `brew install jq` (macOS), `apt-get install jq` (Linux), or `scoop install jq` (Windows). Without `jq`, HOTL still works but runs without state files or durable reports. For the deeper execution model, see [`docs/how-it-works.md`](docs/how-it-works.md) and [`docs/workflow-format.md`](docs/workflow-format.md).

## Smart Task Routing

HOTL does not force ceremony on every task. It routes by intent:

| What you're doing | What HOTL does |
| --- | --- |
| Asking a question ("how does this work?") | Just answers — no workflow |
| Quick fix (typo, config, one-liner) | Fixes it, verifies, reports back |
| Debugging ("why is this failing?") | Structured debugging — no brainstorm needed |
| Building something new | Full workflow: brainstorm, write workflow, execute, verify |

## Commands & Usage

### Claude Code

| Command | What it does |
| --- | --- |
| `/hotl:brainstorm` | Design the change before coding and save a design doc |
| `/hotl:write-plan` | Create `docs/plans/YYYY-MM-DD-<slug>-workflow.md` from the approved design |
| `/hotl:loop` | Run the workflow with autonomous loop execution |
| `/hotl:execute-plan` | Run the workflow with manual checkpoints |
| `/hotl:subagent-execute` | Run the workflow with delegated subagent execution |
| `/hotl:resume` | Resume an interrupted workflow run |
| `/hotl:pr-review` | Review a PR across multiple dimensions |
| `/hotl:check-update` | Check if a newer HOTL version is available |
| `/hotl:setup` | Generate adapter files for other tools |

### Codex

There is no `/hotl:*` command syntax in Codex. Instead, describe the task in natural language with `@hotl`, or force a specific skill with `$hotl:brainstorming`, `$hotl:writing-plans`, or `$hotl:pr-reviewing`. Plain text like `hotl:brainstorming` is not a reliable user-facing invocation form in Codex. In the picker, Codex may display these skills as `Hotl:brainstorming`-style labels. For setup and prompt examples, see [`.codex/INSTALL.md`](.codex/INSTALL.md) and [`docs/README.codex.md`](docs/README.codex.md).

## Skills Overview

| Category | Skills | What they do |
| --- | --- | --- |
| Design & Planning | `brainstorming`, `writing-plans`, `document-review` | Clarify requirements, define contracts, write design docs, and create executable workflows |
| Execution | `loop-execution`, `executing-plans`, `subagent-execution`, `resuming`, `dispatch-agents` | Run workflows with verification, retries, persistence, and delegation |
| Finish | `finishing-a-development-branch` | Close the execution lifecycle intentionally: merge back, publish for review, keep, or discard the execution checkout |
| Quality & Review | `pr-reviewing`, `code-review`, `requesting-code-review`, `receiving-code-review`, `verification-before-completion` | Review changes and require evidence before completion. Both `code-review` and `pr-reviewing` reference shared [review checklists](docs/checklists/) for SOLID/architecture, security, performance/boundary conditions, and removal/simplification heuristics. |
| Dev Practices | `tdd`, `systematic-debugging`, `skill-authoring` | Apply test-first development, structured debugging, and disciplined skill/prompt authoring workflows |
| Setup | `setup-project`, `using-hotl` | Generate adapter files and establish HOTL operating context |

For detailed descriptions and phase mappings, see the [full skills reference](docs/skills.md).

Want to create or modify HOTL skills? Use `skill-authoring` first, then see [Authoring Skills vs Agents](docs/authoring-skills-vs-agents.md).

## Updating

```bash
curl -fsSL https://raw.githubusercontent.com/yimwoo/hotl-plugin/main/update.sh | bash
```

Covers Claude Code, Codex (both native-skills and plugin source checkout), and Cline. Skips tools that are not installed. In Claude Code, you can also run `/hotl:check-update`. For backup behavior, manual checks, and `--force-codex`, see [Updating HOTL](docs/updating.md).

## Supported Tools

| Tool | Integration |
| --- | --- |
| Claude Code | Plugin — commands, skills, and hooks |
| Codex | Plugin install (recommended) or native skill discovery |
| Cline | Global rules plus local HOTL skill files |
| Cursor | Adapter templates via `/hotl:setup` |
| GitHub Copilot | Adapter templates via `/hotl:setup` |

## Automation Templates

HOTL includes optional Codex automation and GitHub Actions review templates in
[`docs/codex-automations-and-ci.md`](docs/codex-automations-and-ci.md). They are
not active by default; copy them into a target project only after testing the
prompt manually.

## Repository Structure

```text
skills/          HOTL skills (loaded by Skill tool or native discovery)
commands/        Claude Code slash command definitions
hooks/           SessionStart hook for Claude Code
workflows/       Workflow templates (feature, bugfix, refactor)
cline/rules/     Global rules for Cline
adapters/        Templates for AGENTS.md, Cursor, Copilot, and other tools
scripts/         Utility scripts including document-lint.sh
docs/            Published user-facing docs, setup guides, and references
docs/contracts/  Output contracts (PR review, code review, execution report)
docs/checklists/ Reusable review heuristics
```

Repo-local work-product docs such as `docs/designs/`, `docs/plans/`, `docs/research/`, `docs/reviews/`, and `docs/requirements/` are intentionally gitignored in this repo so releases only ship end-user documentation.

## Contributing

Run the smoke tests:

```bash
bats test/smoke.bats
```

Bug reports and feature requests: [github.com/yimwoo/hotl-plugin/issues](https://github.com/yimwoo/hotl-plugin/issues)
