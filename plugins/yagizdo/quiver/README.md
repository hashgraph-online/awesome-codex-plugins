# Quiver

[![Version](https://img.shields.io/badge/version-1.26.2-blue)](https://github.com/yagizdo/quiver/releases)

Quiver is a development lifecycle plugin for AI coding CLIs. Purpose-built skills for brainstorming, planning, execution, debugging, code review, and session handover, plus specialized agents for review and debugging. Every step leaves evidence on disk (a spec, a plan, a ledger, a report, a handover), and nothing is called done without it.

## Contents

- [Typical workflow](#typical-workflow)
- [Installation](#installation)
- [Components](#components)
- [What Do I Use?](#what-do-i-use)
  - [Building Something](#building-something)
  - [How /work runs a large plan](#how-work-runs-a-large-plan)
  - [Building a Whole Project](#building-a-whole-project)
  - [How /ship runs a project](#how-ship-runs-a-project)
  - [Implementing a Design](#implementing-a-design)
  - [Reviewing Code](#reviewing-code)
  - [Fixing a Bug](#fixing-a-bug)
  - [Committing & PRs](#committing--prs)
  - [Session Management](#session-management)
  - [Tooling & Maintenance](#tooling--maintenance)
- [Hooks](#hooks)
- [Agents](#agents)
  - [Review](#review)
  - [Research](#research)
  - [Debug](#debug)
  - [Workflow](#workflow)
- [External Dependencies](#external-dependencies)
- [Setup](#setup)
- [CLI Notes](#cli-notes)
- [Uninstall](#uninstall)
- [Contributing](#contributing)
- [License](#license)

## Typical workflow

A normal feature cycle chains these skills. Each one is self-contained and works on its own. Skip steps, reorder them, or use just the ones you need. If you hit a bug at any point, run `/hypothesis-debugging` to investigate it systematically.

1. `/brainstorm`: turn a vague idea into a validated spec by walking through clarifying questions and trade-off analysis on 2-3 design approaches.
2. `/plan`: research the codebase in parallel, then break the chosen approach into verifiable step-by-step tasks with exact file paths.
3. `/work`: execute the plan with continuous testing, branch setup, and incremental commits. Plans of 3+ tasks run as parallel subagents in separate worktrees.
4. `/commit`: generate a Conventional Commits message from staged changes and commit (optionally pushing).
5. `/create-pr`: open a GitHub pull request with an auto-generated title and description from the branch diff.
6. `/quiver:review`: dispatch review agents to check code quality, security, and architecture, then synthesize findings into one report. Runs 5 agents by default; `--deep` for the full pipeline.
7. `/handover`: save an 8-section summary of the session so the next session resumes with full context.

## Installation

Claude Code and the Codex CLI have their own plugin managers. Cursor reads Claude Code's directory, or a clone of its own. OpenCode has none, so Quiver installs there from a clone. Once it is installed, `/brainstorm` works in any session; per-CLI differences are in [CLI Notes](#cli-notes).

### Claude Code

```
/plugin marketplace add yagizdo/quiver
/plugin install quiver@quiver
```

### OpenAI Codex CLI

```text
codex plugin marketplace add yagizdo/quiver
codex plugin add quiver@quiver
```

### Cursor

Cursor reads Claude Code's plugin directory, so a Claude Code install already covers it. Run `Developer: Reload Window` and the skills are there.

Without one, clone into the directory Cursor loads plugins from:

```bash
git clone https://github.com/yagizdo/quiver.git ~/.cursor/plugins/local/quiver
```

Run `Developer: Reload Window`. Cloning on top of a Claude Code install leaves two copies on separate update schedules, so do not do both.

To update the clone, pull it:

```bash
git -C ~/.cursor/plugins/local/quiver pull
```

Then run `Developer: Reload Window` again so Cursor picks up the new version.

### OpenCode

```bash
git clone https://github.com/yagizdo/quiver.git
cd quiver
./install.sh
```

The script symlinks Quiver into every runtime it detects, and prints the install command for the ones that have their own plugin manager. After that, `git pull` in the clone updates every linked runtime. OpenCode details: [`.opencode/README.md`](.opencode/README.md)

## Components

| Component | Count |
|-----------|-------|
| Hooks | 3 |
| Skills | 22 |
| Agents | 22 |

## What Do I Use?

### Building Something

| Situation | Command | What happens |
|-----------|---------|--------------|
| I have a vague idea, not sure where to start | `/brainstorm` | Walks through clarifying questions, compares 2-3 approaches, outputs a validated spec |
| Scope is clear, need a step-by-step breakdown | `/plan` | Researches codebase in parallel, produces a task-by-task plan with file paths |
| Plan is ready, want hands-off execution | `/work` | 1-2 tasks run sequentially in your session; 3+ tasks run as parallel subagents in separate git worktrees. Progress lives in a ledger on disk that survives compaction, so re-running `/work` on the same plan resumes where it stopped |
| Want a quick second opinion on an approach | `/advise` | Gives a senior-style inline review -- no spec or plan artifact |

### How /work runs a large plan

A plan with 3+ tasks is split into execution groups by dependency and file overlap. Each group's tasks are dispatched together, one subagent per task, each in its own git worktree so parallel tasks never edit the same checkout. When a group finishes, its branches merge into the working branch before the next group starts, so later tasks build on what earlier ones landed. A merge conflict stops the run and names the files; nothing is resolved automatically.

State lives in `.claude/work/<plan-name>/`:

- `progress.md` is the ledger. Every dispatch, completion, and merge is appended there as it happens, so the run can be read back after compaction or a crash. Re-running `/work` on the same plan skips completed tasks and merges any branch that finished but never landed.
- `task-<N>-brief.md` carries one task's requirements out of the plan. The subagent reads that file instead of receiving the whole plan in its prompt.
- `task-<N>-report.md` is where the subagent writes its full account. The orchestrator opens it only when a task is blocked or failed, or when the final test run points at that task; a task that succeeded returns one status line and its report is never loaded into your session.

After the last group merges, the resolved test command runs once on the combined result. A successful run offers to delete the workspace; a blocked, failed, or cancelled run keeps it, because the surviving ledger is what makes the retry cheap.

### Building a Whole Project

| Situation | Command | What happens |
|-----------|---------|--------------|
| I want to build a project from a description without touching it myself | `/ship "<description>"` | Asks one batch of project questions, proposes a split into phases, and on your approval saves a roadmap and one file per phase under `.claude/ship/`. Builds nothing yet |
| The phases are saved, build the next one | `/ship` | Runs the next phase end to end: its questions, research, a spec and a plan written without approval prompts, the build through `/work --auto`, a build, test, and smoke check, `/quiver:review`, an automatic fix of the problems the review confirmed, and a plain-language report |
| Run a specific phase, or re-check one | `/ship <phase-id>`, `/ship --verify` | Starts or continues that phase, including one that stopped; `--verify` runs the build, test, and smoke checks again |

### How /ship runs a project

State lives in `.claude/ship/`:

- `roadmap.md` lists the phases, each with its status and what it depends on.
- `decisions.md` collects the numbered project decisions, so a later phase reads them instead of asking again.
- `phases/<id>-<slug>.md` holds one phase: its goal, scope, and done criteria, the answers you gave, where it stopped, the paths to its spec, plan, and review report, the check results, and its final report.

Every step of a phase is saved to its file before the next one starts. After `/clear`, or in a new session, `/ship` picks up where the last run stopped. When a phase's plan is large or the session is already full, `/ship` suggests moving to a fresh session before the code is written; everything is saved, so `/clear` then `/ship` continues it.

After the build and the checks, `/ship` runs `/quiver:review` on the branch. Each problem the review confirms against the code is fixed in one more `/work` round, and the branch is built, tested, and reviewed once more. A Critical problem, or a fix that would change behavior the phase spec defines, stops for your choice: fix it, leave it listed as open, or stop the phase. Problems the review could not confirm are listed in the report, not fixed.

`/ship` commits through `/work` but never pushes and never opens a pull request. The final report names `/quiver:create-pr` when you are ready.

### Implementing a Design

| Situation | Command | What happens |
|-----------|---------|--------------|
| A Figma frame is ready to become code | `/quiver:design` | Reads the selected nodes through the figma-bridge MCP, maps Figma variables onto the project's own theme tokens, and writes a self-contained plan to `.claude/plans/` |
| Want the frame built without babysitting it | `/quiver:design --auto` | Same extraction and same questions, then straight through the build with no further prompt |
| Design plan is ready, want it built pixel-accurate | `/design-build` | Implements each node against its embedded spec, gating every task on the project's build or tests under a bounded retry budget |
| Built screen does not match the design | `/design-fix` | Compares one node's box, layout, typography, fill, stroke, radius, effects, and content against the code that renders it, reports every deviation, and fixes the ones you pick |

```
/quiver:design                    # extract whatever is selected in Figma
/quiver:design 4029:12345         # extract a specific node by ID
/quiver:design --auto             # extract, then build without stopping
/quiver:design --auto --no-commit # same, and write no commit whatever the plan says
/design-build              # pick a design plan and build it
```

`--auto` removes the handoff between the two stages, not the questions that decide what gets built.

- `/quiver:design` still asks which file, which nodes, what an unmapped variable resolves to, how the build should commit and verify, and whether to overwrite a plan that already exists for the same screen. When a selection expands into many nodes and you described none of them, it also asks which of those nodes the build should implement.
- Those questions all arrive in one call. After that the run stays quiet until the build summary.
- One task still gets three attempts at its verification gate. Auto mode records a gate that is still failing and moves on rather than asking.

`--no-commit` forces `commit_strategy: none` for a single run.

- On a fresh plan it changes nothing. Not committing is already the recommended answer to `/quiver:design`'s commit question, so the flag guarantees that answer rather than overriding it.
- It earns its keep against an existing plan that carries `per-task` or `single`, because `/design-build` never re-asks that question.
- The override lasts one run and never edits the plan.
- The two flags are independent. `/design-build <plan> --no-commit` is as valid as `/quiver:design --auto --no-commit`.

`/quiver:design` is the only stage that talks to Figma.

- The plan carries every measurement, token, and layout anchor `/quiver:design` produced, so `/design-build` runs with Figma disconnected.
- The plan keeps its per-node measurement specs and its reference screenshots. Nothing in Quiver measures the built UI against them, so `/design-build` reports fidelity as `skipped -- no verifier` and the numbers stay there for whatever does the measuring. `/design-fix` compares the code against the design rather than the rendered pixels, so it needs no screenshot and no running app.
- Setup is in [External Dependencies](#external-dependencies).

### Reviewing Code

| Situation | Command | What happens |
|-----------|---------|--------------|
| About to merge, want multi-agent review | `/quiver:review` | Dispatches 5 review agents, synthesizes findings into one report |
| Want a quick senior dev sanity check | `/senior-review` | One pragmatic reviewer evaluates structure, quality, risks |
| Got a review report, not sure which findings matter | `/report-check` | Audits the report for noise, false positives, and overkill |

```
/quiver:review                    # fast review (5 agents, prompts for base branch)
/quiver:review --deep             # full pipeline: all agents + quality check + senior review
/quiver:review --base main        # review against a specific base branch
/quiver:review <PR-URL>           # review a pull request by URL
```

Pass `--comment-pr` to post the report as a PR comment. Use `--deep --with-codex` for cross-model coverage (requires `codex` CLI).

Every review, fast or deep, checks each finding against the code before it saves the report. A finding the code rules out moves to the report's Filtered Findings section with the evidence that ruled it out: file lines, command output, or a recorded project decision. Each remaining finding is marked confirmed, with its evidence, or not checked, with the reason. A branch review runs the project's tests for this only when you pass `--run-checks`, because the branch checked out may be someone else's; a review of uncommitted changes runs them without the flag, and a pull request link never runs them. A review can also be started by another skill or by a plain request such as "review my changes".

Re-review detection: if you run `/quiver:review` again on the same branch after fixing issues, it automatically detects the previous report and switches to re-review mode.

### Fixing a Bug

| Situation | Command | What happens |
|-----------|---------|--------------|
| Bug won't go away after multiple attempts | `/hypothesis-debugging` | Generates hypotheses, tests each systematically, traces root cause, proposes reviewed fix |

### Committing & PRs

| Situation | Command | What happens |
|-----------|---------|--------------|
| Changes ready to commit | `/commit` | Generates a Conventional Commits message, commits, optionally pushes |
| Branch ready for PR | `/create-pr` | Creates a GitHub pull request with auto-generated title and description |

### Session Management

| Situation | Command | What happens |
|-----------|---------|--------------|
| Ending a work session | `/handover` | Saves an 8-section summary so the next session resumes with full context |
| Starting a new session | `/load-handover` | Loads the most recent handover and highlights top priorities |
| Last handover is stale or wrong | `/handover --clear` | Shows and deletes the most recent handover file with confirmation |
| Want a clean slate | `/handover --clear-all` | Lists all handover files, confirms, then deletes everything |

### Tooling & Maintenance

| Situation | Command | What happens |
|-----------|---------|--------------|
| Want an AGENTS.md for the project | `/create-agents-md` | Analyzes project context and generates an operational checklist |

## Hooks

| Hook | Event | Description |
|------|-------|-------------|
| `pre-tool-use-guard` | PreToolUse | Classifies every Bash command before it runs -- refuses the handful that are irreversible, prompts on the destructive-but-recoverable ones, stays silent otherwise |
| `pre-compact-handover` | PreCompact | Summarizes the conversation and saves a handover before the CLI compacts context |
| `session-start-auto-dispatch` | SessionStart | Reads every skill's `when-to-use` and emits a routing block so intent matches invoke the right skill |

> To turn the guard's confirmation prompts off, add `"env": {"QUIVER_GUARD_PROMPTS": "off"}` to `~/.claude/settings.json`, or to a project's `.claude/settings.json` for that project only. The refusals for `rm -rf /` and `rm -rf ~` stay on.

> The handover hook keeps the 3 most recent handovers in `.claude/handovers/` and prunes older ones automatically. Filenames are timestamps, so sort order is lexicographic.

## Agents

Review, research, and debug agents run with the `Edit`, `Write`, `NotebookEdit`,
`WebSearch`, and `WebFetch` tools denied -- they are built to read your code and
report findings, not to change it. `Bash` stays enabled because these agents need
`git diff`, `git log`, and `git blame`, so the denial is a guardrail against
accidental edits rather than a sandbox: a shell command can still write a file or
reach the network. Four agents carry a narrower denylist: `best-practices-researcher`
keeps web access so it can check library versions against upstream release notes,
`stack-researcher` keeps it because it answers open questions from current docs
and package registries, `codex-code-reviewer` can write because it persists
the raw output of the external reviewer it wraps, and `finding-verifier` can write
inside its own git worktree so it can run a scratch check against a review finding,
then undoes every edit before it returns.

<!-- agents-start -->

### Review
<!-- agents:review-start -->

| Agent | What it catches |
|-------|-----------------|
| `architecture-strategist` (`quiver:architecture-strategist`) | Code that violates the project's own conventions and module boundaries |
| `logic-reviewer` (`quiver:logic-reviewer`) | Branches where inputs don't reach the documented output correctly |
| `waste-detector` (`quiver:waste-detector`) | Dead code, redundant utilities, unnecessary abstractions |
| `stress-tester` (`quiver:stress-tester`) | Failure scenarios: inputs, timings, and states that break the new code |
| `security-audit` (`quiver:security-audit`) | Concrete exploit paths for web, API, and mobile surfaces |
| `test-reviewer` (`quiver:test-reviewer`) | Tests that pass without proving the code works |
| `developer-experience-auditor` (`quiver:developer-experience-auditor`) | Confusing error messages, hidden debugging paths, brittle UX for humans and agents |
| `codex-code-reviewer` (`quiver:codex-code-reviewer`) | Cross-model code review via the OpenAI Codex CLI; dispatched only when `--with-codex` is passed and the `codex` CLI is installed. Uses whatever model your local codex is configured for: Quiver does not override `--model` |
| `report-checker` (`quiver:report-checker`) | Independent quality auditor for review reports -- detects noise, false positives, overkill, and findings that exist to appear thorough |
| `senior-reviewer` (`quiver:senior-reviewer`) | Language-aware senior developer review -- evaluates code through a pragmatic team lead lens with optional meta-review of other agents' findings in the pipeline |
| `finding-verifier` (`quiver:finding-verifier`) | Checks one review finding against the code and returns it confirmed, refuted, or unverifiable, with the command output or file lines that settled it |

<!-- agents:review-end -->

### Research
<!-- agents:research-start -->

| Agent | What it catches |
|-------|-----------------|
| `best-practices-researcher` (`quiver:best-practices-researcher`) | Deprecated APIs and outdated patterns versus current library docs |
| `stack-researcher` (`quiver:stack-researcher`) | Answers open technical questions before code is written, with a source for every answer |
| `project-context-analyst` (`quiver:project-context-analyst`) | Prior decisions, past bugs, and churn patterns in this area of the codebase |
| `code-locator` (`quiver:code-locator`) | Fast file:line locations for "where is X / what calls Y" without heavy mapping |
| `code-navigator` (`quiver:code-navigator`) | CodeGraph-first codebase explorer that maps files, symbols, and patterns relevant to a task |

<!-- agents:research-end -->

### Debug
<!-- agents:debug-start -->

| Agent | What it does |
|-------|--------------|
| `code-tracer` (`quiver:code-tracer`) | Traces execution paths across files to find where behavior diverges from expectation |
| `log-analyzer` (`quiver:log-analyzer`) | Parses log dumps and stack traces to extract error patterns and map them to source code |
| `regression-finder` (`quiver:regression-finder`) | Analyzes git history to find which commit introduced a bug |
| `environment-checker` (`quiver:environment-checker`) | Checks dependency versions, config files, and environment setup for mismatches |
| `fix-reviewer` (`quiver:fix-reviewer`) | Reviews every proposed fix for overengineering, workarounds, and architectural consistency |

<!-- agents:debug-end -->

### Workflow
<!-- agents:workflow-start -->

| Agent | What it does |
|-------|--------------|
| `plan-reviewer` (`quiver:plan-reviewer`) | Reviews implementation plans for logical coherence, dependency ordering, coverage completeness, and spec alignment |

<!-- agents:workflow-end -->
<!-- agents-end -->

## External Dependencies

This plugin includes a [Context7](https://context7.com) MCP server for real-time library documentation lookups. It starts automatically when the plugin is enabled (configured in `plugin.json` under `mcpServers`). No authentication required.

**Tools provided:**
- `resolve-library-id`: Find library ID for a framework/package
- `query-docs`: Get documentation for a specific library

Supports 100+ frameworks including Rails, React, Next.js, Vue, Django, Laravel, and more. Library/framework names from your codebase are sent to the service only during review agent execution (e.g., best-practices checks), not at plugin load time.

### figma-bridge (optional, for `/quiver:design` and `/design-fix`)

`/quiver:design` and `/design-fix` read Figma through the [figma-mcp-bridge](https://github.com/gethopp/figma-mcp-bridge) MCP server. It is not bundled in `plugin.json` -- the bridge also needs a Figma plugin installed by hand, so auto-starting the server alone would only get you halfway.

Add the server to your MCP config:

```json
{
  "figma-bridge": {
    "command": "npx",
    "args": ["-y", "@gethopp/figma-mcp-bridge"]
  }
}
```

The Figma plugin side is a manual import from the bridge's [releases page](https://github.com/gethopp/figma-mcp-bridge/releases), and its README carries the current steps. Leave the plugin running inside the file you are reading -- it holds the WebSocket, and closing it drops the connection mid-extraction.

`/quiver:design` and `/design-fix` only call the bridge's read tools, and `/design-fix` also runs with the bridge absent when you point it at an existing `/quiver:design` plan. `/design-build` never calls it at all. Every other Quiver skill works without it.

## Setup

Quiver writes its working files into your project: specs from `/brainstorm` in `.claude/specs/` (earlier releases used `docs/brainstorms/`), plans in `.claude/plans/`, review reports in `.claude/reports/`, handovers in `.claude/handovers/`, and `/work` progress in `.claude/work/`. They stay out of git with no setup. The first time a skill writes one of these folders in a git repository, it adds the folder to `.git/info/exclude` and prints a line saying so. That file is git's local ignore list for your clone: the folder drops out of `git status`, and no file in the repository changes.

To keep a folder in git instead, commit a file in it, or say so in the project's `CLAUDE.md` or `AGENTS.md`. The handover hook that runs before compaction cannot read those files, so for `.claude/handovers/` commit a file. A folder already listed in `.git/info/exclude` stays out of git until you delete its line there.

## CLI Notes

### Cursor

- Cursor sees a Claude Code install but not a Codex install.
- The clone at `~/.cursor/plugins/local/quiver` has to be a real directory. Cursor ignores a symlink there that points to a clone somewhere else.
- The `cursor-agent` CLI does not load plugin skills. Use the Cursor IDE.
- If no handover appears in `.claude/handovers/` after a compaction, run `/handover` yourself.

### Codex

- The handover auto-save runs before compaction once the hook is trusted. If Codex asks you to review hooks, open `/hooks` and trust Quiver's.

### OpenCode

- An earlier release added a `quiver` entry to the `plugin` array in your `opencode.json`. That entry no longer resolves: delete it, then run `./install.sh`.
- Skills do not show in the `/` autocomplete menu. Typing `/brainstorm` still runs it.

## Uninstall

On Claude Code:

```
claude plugin uninstall quiver
```

On the Codex CLI:

```text
codex plugin remove quiver@quiver
```

On Cursor, when it was cloned rather than read from a Claude Code install:

```bash
rm -rf ~/.cursor/plugins/local/quiver
```

On OpenCode, from the clone:

```bash
./install.sh --uninstall
```

That removes only the symlinks that resolve into the clone, and reports anything it declined to remove.

## Contributing

Bug fix: open a PR. New skill, agent, or hook, or a behaviour change: open an issue first. Setup, tests, and PR expectations are in [CONTRIBUTING.md](CONTRIBUTING.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
