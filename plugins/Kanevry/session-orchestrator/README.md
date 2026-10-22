# Session Orchestrator

Give your coding agents an agreed plan, checks after each round of changes and a handover that lets the next session continue where you stopped.

[![npm](https://img.shields.io/npm/v/session-orchestrator.svg)](https://www.npmjs.com/package/session-orchestrator)
[![Release](https://img.shields.io/github/v/release/Kanevry/session-orchestrator)](https://github.com/Kanevry/session-orchestrator/releases/latest)
[![Tests](https://github.com/Kanevry/session-orchestrator/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/Kanevry/session-orchestrator/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-5.13.0-blue.svg)](CHANGELOG.md)

<a href="https://session-orchestrator.com"><img src="site/og.png" width="400" alt="Session Orchestrator: Plan, Go, Close, with an illustration of an agent workshop under human direction (AI-generated)"></a>

## Who it is for

- **You use a coding agent on a git repository:** Claude Code, Codex CLI, Cursor IDE or [Pi](docs/pi-setup.md). Session Orchestrator runs on top of it; it does not replace it.
- **You want that agent to follow a plan you agreed to,** with your checks run after each round of changes and a handover for the next session.
- **You work as one operator,** possibly in several sessions at once. It keeps your own concurrent sessions apart; it is not built for a shared team workspace.

## Prerequisites

Node.js 24 or later, a git repository and one of Claude Code, Codex CLI, Cursor IDE or Pi. Optional: `glab` or `gh` for issues and merge requests, Bash and `jq` for the shell MCP server. Full matrix and platform notes: [docs/install.md](docs/install.md#requirements).

## Install

In Claude Code:

```text
/plugin marketplace add Kanevry/session-orchestrator
/plugin install session-orchestrator@kanevry
```

| Platform | Install |
|---|---|
| **Claude Code** | The two commands above, then [check its Node dependencies once](docs/install.md#claude-code-check-the-node-dependencies) (current Claude Code installs them for you). |
| **Codex CLI** | `git clone` the repo, `npm install`, then `node scripts/codex-install.mjs` ([guide](docs/codex-setup.md)). |
| **Cursor IDE** | `git clone` the repo, `npm install`, then `node scripts/cursor-install.mjs /path/to/your/project` ([guide](docs/cursor-setup.md)). |
| **Pi** | `npm install -g --ignore-scripts @earendil-works/pi-coding-agent`, then `pi install npm:session-orchestrator` ([guide](docs/pi-setup.md)). |

Full requirements, upgrade path and uninstall: [docs/install.md](docs/install.md).

Contributing? Run `npx husky` once after cloning: `.npmrc` sets `ignore-scripts=true`, so git hooks are not activated by `npm install`. The same applies after a clone-based install for Codex CLI or Cursor IDE.

Optional, Claude Code only: `/plugin install so-hud@kanevry` adds a status line for the running session and protection gates that refuse secret-printing commands and ask before pushes to `main`, merges, releases, publishes and deploys ([mods/so-hud](mods/so-hud/README.md), [docs/mods.md](docs/mods.md)).

## Quickstart: see the plan before the work starts

Once the plugin is installed ([Install](#install)), open your project and run:

```text
/bootstrap --fast --no-interview
```

Check the Session Config written by `/bootstrap` and set its test, typecheck and lint commands to your project's actual commands. Then run `/session feature` and describe a task you want done: the agent reads the repository and presents a scope for you to correct before implementation starts. That is the first result to inspect.

Once you agree to the plan:

```text
/go                 # run the agreed work, checking each implementation wave
/close              # verify the result, commit and file remaining work as issues
```

[Codex setup](docs/codex-setup.md) · [Cursor setup](docs/cursor-setup.md) · [Pi setup](docs/pi-setup.md) · [User guide](docs/USER-GUIDE.md)

## What it does

On their own, coding agents drift from the plan, overwrite each other's files and call work done before it is checked; Session Orchestrator closes those gaps.

You type three commands:

- **`/session`** reads your repository, your open issues and the last session, proposes what to work on, and waits for your correction.
- **`/go`** runs the agreed work in waves of parallel agents. After each implementation wave your tests and typecheck run, and failures become fix tasks for the next wave. The full test, typecheck and lint gate runs before `/close` commits.
- **`/close`** checks every planned item against what actually happened, commits, and files the rest as issues for next time.

Session Orchestrator is a free, MIT-licensed workflow plugin for **Claude Code, Codex CLI, Cursor IDE, or [Pi](docs/pi-setup.md)**. It runs on your machine and writes plain text into your repository. There is no account and no server.

```mermaid
flowchart LR
    B["/bootstrap<br/>once per repo"] --> S["/session<br/>reads repo, proposes scope"]
    S --> A{"you agree?"}
    A -- no --> S
    A -- yes --> W1["wave 1"] --> Q1["tests + typecheck"] --> W2["wave 2 ..."]
    W2 --> F["full gate<br/>test, typecheck, lint"]
    F --> C["/close<br/>verify, commit, file the rest as issues"]
    C -. next session resumes from STATE.md .-> S
```

Longer explanation, with an example session: **[session-orchestrator.com](https://session-orchestrator.com)** ([auf Deutsch](https://session-orchestrator.com/de)).

[User guide](docs/USER-GUIDE.md) · [Install & upgrade](docs/install.md) · [Changelog](CHANGELOG.md)

## First session

**1. Run `/bootstrap` once in your project.** It creates the minimum structure, writes `.orchestrator/bootstrap.lock` and adds a Session Config. `/session` refuses to start until the lock exists. For a setup without the interview, `/bootstrap --fast --no-interview` skips the tier question and the personal-preferences interview; run that interview later with `/bootstrap --owner-reset`.

**2. Check the Session Config** that `/bootstrap` wrote into your project's instruction file; `CLAUDE.md` on Claude Code and Cursor, `AGENTS.md` on Codex CLI and Pi ([which file each platform reads](skills/_shared/instruction-file-resolution.md)). Add it by hand only if the block is missing. These seven fields are enough:

```yaml
## Session Config

test-command: npm test
typecheck-command: npm run typecheck
lint-command: npm run lint
agents-per-wave: 6
waves: 5
persistence: true
enforcement: warn
```

The first three are the commands the quality gate runs: tests and typecheck after each implementation wave, all three after the Quality wave and before `/close` commits; use whatever your project actually uses. Everything else is opt-in: [full template](docs/session-config-template.md) · [every key, its type and default](docs/session-config-reference.md).

**3. Run `/session feature`, `/go`, then `/close`** as shown in the quickstart above.

On Codex the same three are `$session-orchestrator:session feature`, `$session-orchestrator:go`, `$session-orchestrator:close` ([Codex usage](docs/codex-setup.md#usage)). `/plan` and `/evolve` extend the loop; you can start with just these three.

In headless Claude Code (`claude -p`), `/session` and `/plan` are reserved terminal-only built-in names and the bare form is refused; use `/session-orchestrator:session` and `/session-orchestrator:plan` there. Every other command keeps its bare form.

## What you get

| Without it | With it |
|---|---|
| You paste your working rules into every session | `/session` reads git, issues and the last session first |
| Two agents edit the same file | Each agent gets a declared file list; overlaps are rejected |
| "Done" before the tests ran | Tests and typecheck run after each implementation wave |
| A crash loses the plan | `STATE.md` records each wave; the next `/session` offers to resume |

Each item: what it does for you, then how it works.

| You get | How |
|---|---|
| **Know what to work on.** Every session starts from the real state of your project, not from a prompt you rewrite. | `/session` reads git, open issues, recent commits and the last session record, recommends one scope and waits for your correction. `/plan`, `/brainstorm` and `/grill` help while an idea is still vague. |
| **Errors stop at the next check.** A broken test is found right after the work that caused it, not after more work is built on top. | `/go` checks each wave with your tests and typecheck and turns failures into fix tasks; lint and the full suite run before the commit. `/close` checks every planned item against what happened. `/debug` looks for the root cause before a fix. |
| **Agents keep to their files.** Parallel agents do not overwrite each other, and destructive commands do not slip through. | Each agent gets a declared list of files it may change; overlapping lists are rejected before dispatch. A guard blocks 12 destructive command patterns (hard reset, `rm -rf`, force-push, `DROP TABLE`, …) and warns on 4. Hooks on Claude Code, bridges on Cursor and Pi, Bash hooks on Codex (its file-scope guard stays instruction-only). |
| **Pick up where you stopped.** A crash or a second session in the same folder does not cost you the work. | `STATE.md` (a progress file in your repo) records each finished wave, and the next `/session` offers to resume. A session lock with a heartbeat keeps two sessions apart in one checkout. `/close` files what is left as GitLab or GitHub issues. |
| **It improves with your sessions.** Patterns from your own work become rules, once you approve them. | Every session appends a record. `/evolve` proposes learnings with a confidence score, `/reconcile` drafts rules from them; you approve or delete each one. Optional mirror into a Markdown notes vault. |
| **Audit, test and review on demand.** Find problems you did not ask about, and show the app works. | A discovery scan at `/close` turns confirmed findings into issues. `/test` drives web and macOS flows end to end, `/ux-grill` audits a running web app, `/test-audit` removes tests that catch nothing. `/repo-audit` and `/harness-audit` score a repository against a checklist, and `/persona-panel` has several reviewer personas read the same output in parallel. |
| **Longer runs, more repositories.** | `/autopilot` chains sessions and stops on any of 10 kill-switches. `/dispatcher` recommends the next free repository and claims it once you confirm, and `/portfolio` summarises issues, MRs and CI across the repositories registered in your notes vault. |

## How it works

When you type `/session feature`:

1. **It reads the project.** Git state, open issues, recent commits, documentation, host resources and the records of previous sessions become a Session Overview with one recommendation.
2. **You correct the scope.** Nothing is implemented until you agree to the plan.
3. **The work is split into waves.** The session type decides how many: housekeeping 1, feature 3, deep 5, the ultradeep profile 7. Each wave gets a purpose, a list of file paths it may write to, and a result that can be checked.
4. **`/go` runs it.** Agents whose file scopes do not overlap run at the same time on Claude Code and Codex; Cursor and Pi run them one after another. After each implementation wave your tests and typecheck run, and failures become fix tasks for the next wave. The full test, typecheck and lint gate runs after the Quality wave.
5. **`/close` checks and records.** It compares the plan against what happened, runs the full quality gate, commits file by file, and opens issues for whatever was not finished.

**What it writes into your repository**, and nothing else; all of it plain text, all of it local:

```text
.orchestrator/bootstrap.lock        # written by /bootstrap, the gate for every later run
.orchestrator/current-session.json  # which session owns this working copy right now
.orchestrator/session.lock          # heartbeat lock; stops two sessions colliding in one checkout
.orchestrator/host.json             # host-local identity for peer-session detection
.orchestrator/metrics/*.jsonl       # append-only session, learning, event and subagent records
.orchestrator/steering/             # stable product/tech/structure context injected each session
.claude/STATE.md                    # wave progress and deviations (harness-specific directory)
```

The plugin is **51 skills, 30 slash commands, 14 typed subagents and 29 hook files across 10 event types**. A slash command is a skill whose frontmatter says `user-invocable: true` (28 of them) or one of the two remaining `commands/*.md` files (`/session`, `/templates-ack`); one definition per name, so nothing is listed twice in the `/` picker. Skills, commands and agents are Markdown with YAML frontmatter; the code that dispatches, validates and records runs in `scripts/lib/*.mjs` and `hooks/*.mjs`. There is no build step and no compiled artifact; when a session does something you did not expect, you can open the file that decided it. Full inventory: [`docs/components.md`](docs/components.md).

## Why it is built this way

- **The wave order is deliberate.** Discovery runs first so every implementer starts from the same picture of the code. Impl-Core runs before Impl-Polish so the structure exists before anything integrates against it. The Quality wave simplifies generated code *before* tests are written; write the tests first and they assert whatever the model produced, so changing it later means rewriting the tests too.
- **Checks run after each implementation wave, not only at the end.** A mistake caught after wave 2 costs one wave. The same mistake found at `/close` has already been copied into every wave after it. Findings below the configured confidence threshold are not shown to you.
- **A crash does not lose the session.** `STATE.md` records which wave finished and what deviated from the plan. The next `/session` offers to continue from the last completed wave.
- **Two sessions in one working copy is treated as a real risk.** Two people, or two of your own sessions, in the same checkout share one git index, one filesystem and one `STATE.md`, and neither can see the other's uncommitted work. A heartbeat session lock, per-agent file-scope manifests, and the PSA rules in [`.claude/rules/parallel-sessions.md`](https://github.com/Kanevry/session-orchestrator/blob/main/.claude/rules/parallel-sessions.md) exist for exactly that case.
- **Guards run where the harness supports them, and the table below says where it does not.** A destructive-command policy (12 rules block, 4 warn) and file-scope enforcement run as real hooks on Claude Code and as bridges on Cursor and Pi. On Codex the destructive-command policy runs as a `PreToolUse` Bash hook, while file-scope enforcement stays instruction-only. Details: [`docs/components.md`](docs/components.md#other-surfaces).
- **What it learns is opt-in and readable.** Every session appends a record. After 5 or more sessions, `/evolve analyze` proposes patterns with a confidence score; you read them and delete the ones you disagree with. Nothing is applied without you.
- **GitLab and GitHub, both fully.** It detects which one your remote points at and drives issues and merge/pull requests for either.

How this compares to other orchestrators, with measured results kept separate from unmeasured claims: [`docs/components.md` § Comparisons](docs/components.md#comparisons).

## Platform support

| Feature | Claude Code | Codex CLI | Cursor IDE | Pi |
|---|---|---|---|---|
| All 30 commands | Native slash commands | Generated skills (`$session-orchestrator:<name>`) | Native `.cursor/commands` slash commands | Prompt templates |
| Parallel agents | Agent tool | Multi-agent roles | Sequential only | Sequential |
| Session persistence | `.claude/STATE.md` | `.codex/STATE.md` | `.cursor/STATE.md` | `.pi/STATE.md` |
| Scope enforcement | Active PreToolUse hook; blocking in `strict`, reporting in `warn` | Instructions only; no compatible `apply_patch` handler | `preToolUse` + `beforeShellExecution` bridge; scope blocking requires `strict`; `afterFileEdit` is post-hoc | `tool_call` bridge; scope blocking requires `strict` |
| Destructive-command guard | Active PreToolUse hook applies policy severity | Active PreToolUse `Bash` hook; deny honoured (codex-cli 0.160.1, 2026-10-20) | `beforeShellExecution` bridge for supported commands | `tool_call` bridge for supported commands |
| AskUserQuestion | Native tool | Numbered-list fallback | Numbered-list fallback | Numbered-list fallback |
| Quality gates | Full | Full | Full | Full |

All four platforms share the same skills, commands and scripts; only the hooks differ, because each harness fires different events. On Codex the Bash guards run as `PreToolUse` hooks; the file-scope guards stay unwired because Codex edits through `apply_patch`, which they do not read ([why](docs/codex-setup.md#which-pretooluse-guards-run-on-codex--the-reason-corrected)). Cursor and Pi have known event-coverage limits; see [`docs/cursor-setup.md`](docs/cursor-setup.md) and [`docs/pi-setup.md`](docs/pi-setup.md).

## Recent highlights (v5.13.0)

Highlights of the v5.13.0 line:

- **so-hud guards the session.** The optional mod now checks commands before they run: it refuses commands that would print a secret, also behind pipes, groups, `read` and redirects, and asks before pushes to `main`, merges, releases, publishes and deploys. A band above the prompt lets you pick how strict it is.
- **Every agent names its model and effort.** No agent inherits the session model any more. On Codex the agents use `gpt-6.1-sol`; change the `model` line in `.codex-plugin/agents/*.toml` if you have no access to it.
- **Pre-push on a merge-request branch.** When no remote host can run the gate, a push to a branch other than main runs a local partial gate, and the MR pipeline runs the full suite. Main and tags keep the full gate.
- **Learnings from a second host.** A host set to the inbox role appends its learnings to a separate file, and the writer host takes them over, so two machines no longer rewrite the same `learnings.jsonl`.

Everything else: [CHANGELOG.md](CHANGELOG.md).

## Documentation

- [User guide](docs/USER-GUIDE.md): config reference, a walkthrough of one session, troubleshooting, FAQ
- [Install, upgrade, uninstall](docs/install.md): requirements, per-harness setup, migration paths
- [Components & reference](docs/components.md): every skill, command, agent and hook; the guards; comparisons
- [Telemetry](docs/telemetry.md): what stays on your machine, what the optional anonymous telemetry would send, and every switch that turns it off
- [Contributing](https://github.com/Kanevry/session-orchestrator/blob/main/CONTRIBUTING.md) · [Plugin architecture](docs/plugin-architecture-v3.md) · [docs/ router](docs/README.md)

## Running many sessions at once

session-orchestrator makes one session reliable. When several sessions run in parallel across repositories, a lead session can coordinate them: who runs next, what each may do, one queue for your decisions, one stop for everything. That is the sibling project [lead-session-orchestrator](https://session-orchestrator.com/lead) (npm `lead-session-orchestrator`). Each works alone; together they use the shared fleet contract in `skills/_shared/fleet-protocol.md`.

## Scope and support

Provided **as-is**: a community project, best-effort maintenance, no SLA. Questions and ideas go to [Discussions](https://github.com/Kanevry/session-orchestrator/discussions), bugs to [Issues](https://github.com/Kanevry/session-orchestrator/issues).

Independent and community-maintained. Not affiliated with or endorsed by Anthropic, OpenAI or Cursor. It runs on top of your coding agent and does not replace it. Built for one operator: the parallel-session protection covers your own sessions, not a shared team workspace.

The reasoning behind the method is taught at [agenticbuilders.at](https://agenticbuilders.at). The plugin is free and MIT; the courses go deeper and are not required to use it.

## License

[MIT](LICENSE) · [Privacy policy](https://session-orchestrator.com/datenschutz) · [npm](https://www.npmjs.com/package/session-orchestrator)
