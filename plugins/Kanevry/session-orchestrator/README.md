# Session Orchestrator

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-5.10.0-blue.svg)](CHANGELOG.md)
[![npm](https://img.shields.io/npm/v/session-orchestrator.svg)](https://www.npmjs.com/package/session-orchestrator)

**Give your agents a working rhythm.**

Your coding agents get an agreed plan, a check after each round of changes and a handover to the next session. On their own, coding agents drift from the plan, overwrite each other's files and call work done before it is checked; Session Orchestrator closes those gaps.

You type three commands:

- **`/session`** reads your repository, your open issues and the last session, proposes what to work on, and waits for your correction.
- **`/go`** runs the agreed work in waves of parallel agents. After each implementation wave your tests and typecheck run, and failures become fix tasks for the next wave. The full test, typecheck and lint gate runs before `/close` commits.
- **`/close`** checks every planned item against what actually happened, commits, and files the rest as issues for next time.

Session Orchestrator is a free, MIT-licensed workflow plugin for **Claude Code, Codex CLI, Cursor IDE, or [Pi](docs/pi-setup.md)**. It runs on your machine and writes plain text into your repository. No account, no server, nothing to sign up for.

[![Session Orchestrator: Plan, Go, Close, with an illustration of an agent workshop under human direction](site/og.png)](https://session-orchestrator.com)

```mermaid
flowchart LR
    S["/session"] --> G["/go"]
    G --> Q{"quality gate"}
    Q -- "fails" --> G
    Q -- "passes" --> C["/close"]
```

Longer explanation, with examples and screenshots: **[session-orchestrator.com](https://session-orchestrator.com)** ([auf Deutsch](https://session-orchestrator.com/de)).

[User guide](docs/USER-GUIDE.md) · [Install & upgrade](docs/install.md) · [Changelog](CHANGELOG.md)

## Install

You need **Node.js 24 or later**, a git repository, and one of the four agents below. Full requirements, upgrade path and uninstall: [docs/install.md](docs/install.md).

| Platform | Install |
|---|---|
| **Claude Code** | `/plugin marketplace add Kanevry/session-orchestrator` then `/plugin install session-orchestrator@kanevry`, then [install its Node dependencies once](docs/install.md#claude-code-install-the-node-dependencies-once). |
| **Codex CLI** | `git clone` the repo, `npm install`, then `node scripts/codex-install.mjs` ([guide](docs/codex-setup.md)). |
| **Cursor IDE** | `git clone` the repo, `npm install`, then `node scripts/cursor-install.mjs /path/to/your/project` ([guide](docs/cursor-setup.md)). |
| **Pi** | `pi install npm:session-orchestrator` ([guide](docs/pi-setup.md)). |

After a clone-based install (Codex CLI, Cursor IDE, or contributing), run `npx husky` once: `.npmrc` sets `ignore-scripts=true` (SEC-020), which skips the `prepare` script that would otherwise activate the git hooks.

## Quick Start

**1. Run `/bootstrap` once in your project.** It creates the minimum structure and writes `.orchestrator/bootstrap.lock`. `/session` refuses to start until that file exists.

**2. Add a Session Config** to your project's instruction file — `CLAUDE.md` on Claude Code and Cursor, `AGENTS.md` on Codex CLI and Pi ([which file each platform reads](skills/_shared/instruction-file-resolution.md)). These seven fields are enough:

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

The first three are the commands the quality gate runs: tests and typecheck after each implementation wave, all three after the Quality wave and before `/close` commits — use whatever your project actually uses. Everything else is opt-in: [full template](docs/session-config-template.md) · [every key, its type and default](docs/session-config-reference.md).

**3. Run the loop.**

```text
/session feature    # read the repo, propose scope, wait for your correction
/go                 # execute in waves, check between each
/close              # verify, commit, file the rest as issues
```

On Codex the same three are `$session-orchestrator:session feature`, `$session-orchestrator:go`, `$session-orchestrator:close` ([Codex usage](docs/codex-setup.md#usage)). `/plan` and `/evolve` extend the loop; you can start with just these three.

In headless Claude Code (`claude -p`), `/session` and `/plan` are reserved terminal-only built-in names and the bare form is refused; use `/session-orchestrator:session` and `/session-orchestrator:plan` there. Every other command keeps its bare form.

## What you get

Each item: what it does for you, then how it works.

| You get | How |
|---|---|
| **Know what to work on.** Every session starts from the real state of your project, not from a prompt you rewrite. | `/session` reads git, open issues, recent commits and the last session record, recommends one scope and waits for your correction. `/plan`, `/brainstorm` and `/grill` help while an idea is still vague. |
| **Errors stop at the next check.** A broken test is found right after the work that caused it, not after more work is built on top. | `/go` checks each wave with your tests and typecheck and turns failures into fix tasks; lint and the full suite run before the commit. `/close` checks every planned item against what happened. `/debug` looks for the root cause before a fix. |
| **Agents keep to their files.** Parallel agents do not overwrite each other, and destructive commands do not slip through. | Each agent gets a declared list of files it may change; overlapping lists are rejected before dispatch. A guard blocks 12 destructive command patterns (hard reset, `rm -rf`, force-push, `DROP TABLE`, …) and warns on 4. Hooks on Claude Code, bridges on Cursor and Pi, instructions only on Codex. |
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

**What it writes into your repository**, and nothing else — all of it plain text, all of it local:

```text
.orchestrator/bootstrap.lock        # written by /bootstrap, the gate for every later run
.orchestrator/current-session.json  # which session owns this working copy right now
.orchestrator/session.lock          # heartbeat lock; stops two sessions colliding in one checkout
.orchestrator/host.json             # host-local identity for peer-session detection
.orchestrator/metrics/*.jsonl       # append-only session, learning, event and subagent records
.orchestrator/steering/             # stable product/tech/structure context injected each session
.claude/STATE.md                    # wave progress and deviations (harness-specific directory)
```

The plugin is **51 skills, 30 slash commands, 14 typed subagents and 29 hook files across 10 event types**. A slash command is a skill whose frontmatter says `user-invocable: true` (28 of them) or one of the two remaining `commands/*.md` files (`/session`, `/templates-ack`) — one definition per name, so nothing is listed twice in the `/` picker. Skills, commands and agents are Markdown with YAML frontmatter; the code that dispatches, validates and records runs in `scripts/lib/*.mjs` and `hooks/*.mjs`. There is no build step and no compiled artifact — when a session does something you did not expect, you can open the file that decided it. Full inventory: [`docs/components.md`](docs/components.md).

## Why it is built this way

- **The wave order is deliberate.** Discovery runs first so every implementer starts from the same picture of the code. Impl-Core runs before Impl-Polish so the structure exists before anything integrates against it. The Quality wave simplifies generated code *before* tests are written — write the tests first and they assert whatever the model produced, so changing it later means rewriting the tests too.
- **Checks run after each implementation wave, not only at the end.** A mistake caught after wave 2 costs one wave. The same mistake found at `/close` has already been copied into every wave after it. Findings below the configured confidence threshold are not shown to you.
- **A crash does not lose the session.** `STATE.md` records which wave finished and what deviated from the plan. The next `/session` offers to continue from the last completed wave.
- **Two sessions in one working copy is treated as a real risk.** Two people, or two of your own sessions, in the same checkout share one git index, one filesystem and one `STATE.md`, and neither can see the other's uncommitted work. A heartbeat session lock, per-agent file-scope manifests, and the PSA rules in [`.claude/rules/parallel-sessions.md`](https://github.com/Kanevry/session-orchestrator/blob/main/.claude/rules/parallel-sessions.md) exist for exactly that case.
- **Guards run where the harness supports them, and the table below says where it does not.** A destructive-command policy — 12 rules block, 4 warn — and file-scope enforcement run as real hooks on Claude Code, as bridges on Cursor and Pi, and as instructions only on Codex. Details: [`docs/components.md`](docs/components.md#other-surfaces).
- **What it learns is opt-in and readable.** Every session appends a record. After 5 or more sessions, `/evolve analyze` proposes patterns with a confidence score; you read them and delete the ones you disagree with. Nothing is applied without you.
- **GitLab and GitHub, both fully.** It detects which one your remote points at and drives issues and merge/pull requests for either.

How this compares to other orchestrators, with measured results kept separate from unmeasured claims: [`docs/components.md` § Comparisons](docs/components.md#comparisons).

## Platform support

| Feature | Claude Code | Codex CLI | Cursor IDE | Pi |
|---|---|---|---|---|
| All 30 commands | Native slash commands | Generated skills (`$session-orchestrator:<name>`) | Native `.cursor/commands` slash commands | Prompt templates |
| Parallel agents | Agent tool | Multi-agent roles | Sequential only | Sequential (parallel planned) |
| Session persistence | `.claude/STATE.md` | `.codex/STATE.md` | `.cursor/STATE.md` | `.pi/STATE.md` |
| Scope enforcement | Active PreToolUse hook; blocking in `strict`, reporting in `warn` | Instructions only; no compatible `apply_patch` handler | `preToolUse` + `beforeShellExecution` bridge; scope blocking requires `strict`; `afterFileEdit` is post-hoc | `tool_call` bridge; scope blocking requires `strict` |
| Destructive-command guard | Active PreToolUse hook applies policy severity | Instructions only; no handler wired | `beforeShellExecution` bridge for supported commands | `tool_call` bridge for supported commands |
| AskUserQuestion | Native tool | Numbered-list fallback | Numbered-list fallback | Numbered-list fallback |
| Quality gates | Full | Full | Full | Full |

All four platforms share the same skills, commands and scripts; only the hooks differ, because each harness fires different events. Codex leaves its `PreToolUse` handlers empty because these guards do not yet match its tool names and edit payloads ([why](docs/codex-setup.md#why-our-pretooluse-guards-stay-unwired--the-reason-corrected)). Cursor and Pi have known event-coverage limits — see [`docs/cursor-setup.md`](docs/cursor-setup.md) and [`docs/pi-setup.md`](docs/pi-setup.md).

## Recent highlights (v5.10.0)

Highlights of the v5.10.0 line:

- **Scope checks follow the agent checkout.** Isolated agents use verified coordinator manifests, with grants applied to their own checkout (#1504).
- **Release privacy checks inspect the published archive.** Host-specific rules stay in protected local configuration, and the release publishes the bytes it checked (#1530).
- **Remote push gates verify the pushed commit.** A matching receipt is required; unavailable hosts permit fallback (#1532).
- **Sessions retain their host.** Mirrored notes and the board show the originating machine, while legacy records remain supported (#1054).
- **Clearer gate results and host-aware drift checks.** Colored test counts and complete failure output survive capture; narrow foreign-host prefixes can be configured explicitly (#937, #1534, #1535).

Full changes and upgrade notes: [CHANGELOG.md](CHANGELOG.md).

## Documentation

- [User guide](docs/USER-GUIDE.md) — config reference, a walkthrough of one session, troubleshooting, FAQ
- [Install, upgrade, uninstall](docs/install.md) — requirements, per-harness setup, migration paths
- [Components & reference](docs/components.md) — every skill, command, agent and hook; the guards; comparisons
- [Telemetry](docs/telemetry.md) — what stays on your machine, what the optional anonymous telemetry would send, and every switch that turns it off
- [Contributing](https://github.com/Kanevry/session-orchestrator/blob/main/CONTRIBUTING.md) · [Plugin architecture](docs/plugin-architecture-v3.md) · [docs/ router](docs/README.md)

## Running many sessions at once

session-orchestrator makes one session reliable. When several sessions run in parallel across repositories, a lead session can coordinate them: who runs next, what each may do, one queue for your decisions, one stop for everything. That is the sibling project [lead-session-orchestrator](https://session-orchestrator.com/lead) ([GitHub](https://github.com/Kanevry/lead-session-orchestrator), npm `lead-session-orchestrator`). Each works alone; together they use the shared fleet contract in `skills/_shared/fleet-protocol.md`.

## Scope and support

Provided **as-is**: a community project, best-effort maintenance, no SLA. Questions and ideas go to [Discussions](https://github.com/Kanevry/session-orchestrator/discussions), bugs to [Issues](https://github.com/Kanevry/session-orchestrator/issues).

It is **not** an official product of any agent vendor — independent and community-maintained, not affiliated with, endorsed by or sponsored by Anthropic, OpenAI, Cursor or any agent it integrates with, and distributed through the Claude Code plugin marketplace without being an Anthropic product. It does **not replace** your agent; it runs on top of one, and you still need it installed. It is built for **one operator**: the parallel-session machinery protects your own concurrent sessions, not a shared team workspace.

The reasoning behind the method is taught at [agenticbuilders.at](https://agenticbuilders.at). The plugin is free and MIT; the courses go deeper and are not required to use it.

## License

[MIT](LICENSE) · [Privacy policy](https://session-orchestrator.com/datenschutz) · [npm](https://www.npmjs.com/package/session-orchestrator)
