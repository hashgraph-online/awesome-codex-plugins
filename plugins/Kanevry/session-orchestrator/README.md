<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Kanevry/session-orchestrator/main/site/brand/a3-terminalmodule/mark-on-dark.svg">
  <img src="https://raw.githubusercontent.com/Kanevry/session-orchestrator/main/site/brand/a3-terminalmodule/mark-on-light.svg" alt="Session Orchestrator logo: a person at a workbench with three terminal modules" width="64" align="left" hspace="12">
</picture>

# Session Orchestrator

**Your coding agents get an agreed plan, a check after each round of changes and a handover to the next session.**

A free, MIT-licensed workflow plugin for people running Claude Code, Codex CLI, Cursor IDE or Pi on a git repository. It runs on your machine and writes plain text into your repository: no account, no server.

**[Website](https://session-orchestrator.com)** ([Deutsch](https://session-orchestrator.com/de)) · **[Commands](https://session-orchestrator.com/commands)** · **[User guide](docs/USER-GUIDE.md)** · [Changelog](CHANGELOG.md)

> **Beta:** 15 free seats in the agenticbuilders Pass for Session Orchestrator users. You learn to get real work done with Claude Code and agents. In return you tell me for 14 days what helped. Want a seat? [agenticbuilders.at/so](https://agenticbuilders.at/so#beta)

[![Tests](https://github.com/Kanevry/session-orchestrator/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/Kanevry/session-orchestrator/actions/workflows/test.yml)
[![Version](https://img.shields.io/badge/version-5.16.0-blue.svg)](CHANGELOG.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Website](https://img.shields.io/badge/website-session--orchestrator.com-blue)](https://session-orchestrator.com)

<br clear="left">

## Install

You need Node.js 24 or later and a git repository. In Claude Code:

```text
/plugin marketplace add Kanevry/session-orchestrator
/plugin install session-orchestrator@kanevry
```

Codex CLI, Cursor IDE, Pi, upgrade and uninstall: [docs/install.md](docs/install.md).

## How it works

- **`/session`** reads your repository, your open issues and the last session, proposes what to work on, and waits for your correction. Nothing changes in your code until you agree.
- **`/go`** runs the agreed work in waves: rounds of parallel agents, each with its own list of files. Your tests and typecheck run after each wave; failures become fix tasks for the next one.
- **`/close`** runs the full test, typecheck and lint gate, checks every planned item against what happened, commits, and files the rest as GitLab or GitHub issues.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Kanevry/session-orchestrator/main/docs/img/lifecycle-dark.svg">
  <img src="https://raw.githubusercontent.com/Kanevry/session-orchestrator/main/docs/img/lifecycle-light.svg" width="720" alt="Flow: /bootstrap once per repo, then /session proposes a scope; once you agree, /go runs waves of agents with tests and typecheck after each, the full gate runs test, typecheck and lint, and /close commits and files the rest as issues; the next session resumes from there.">
</picture>

| Without it | With it |
|---|---|
| You paste your working rules into every session | `/session` reads git, issues and the last session first |
| Two agents edit the same file | Each agent gets a declared file list; overlaps are rejected |
| "Done" before the tests ran | Tests and typecheck run after each wave |
| A crash loses the plan | Progress is written down after each wave; the next `/session` offers to resume |

## First session

1. **Run `/bootstrap --fast --no-interview` once in your project.** It adds a short config block to your instruction file (`CLAUDE.md` or `AGENTS.md`).
2. **Set the three gate commands** in that block to what your project uses, for example `test-command: npm test`, `typecheck-command: npm run typecheck`, `lint-command: npm run lint`. Every other key is optional ([reference](docs/session-config-reference.md)).
3. **Run `/session feature`** and describe the task. Correct the proposed scope, then run **`/go`** and, when the work is done, **`/close`**.

On Codex and in headless Claude Code (`claude -p`) some command names differ: [Codex](docs/codex-setup.md#usage) · [headless](docs/install.md#headless-claude-code-claude--p-two-commands-need-the-namespaced-form).

## What do you want to do?

| Situation | Type | You get |
|---|---|---|
| A new project idea | `/plan new` | Research, decisions, a PRD and issues (works out of the box; uses your [baseline](docs/USER-GUIDE.md#plan-mode) when configured) |
| A feature that is not clear yet | `/plan feature` | A bounded plan with acceptance criteria |
| A feature that is clear | `/session feature`, then `/go`, then `/close` | The agreed change, checked, committed, leftovers as issues |
| A big or unclear change | `/session deep` | It looks first, then builds |
| Tidy up | `/session housekeeping` | A short maintenance pass |
| Look back on a phase | `/plan retro` | What worked, what to change |
| The same mistakes keep coming back | `/evolve`, then `/reconcile` | Lessons you approve become rules |

All 31 commands, by situation: [session-orchestrator.com/commands](https://session-orchestrator.com/commands)

## It learns, with your yes

`/evolve` suggests lessons from your own session records; `/reconcile` turns the ones you approve into rule files that later sessions load. It never trains a model and never changes itself without your approval ([how it works](docs/USER-GUIDE.md#17-cross-session-learning)).

## Add-on: lead-session-orchestrator

Running three or four sessions side by side? [lead-session-orchestrator](https://session-orchestrator.com/lead) adds one lead session above them that decides which one goes next and puts their questions into one queue for you. It is a separate npm package; details and caveats: [docs/install.md](docs/install.md#add-on-lead-session-orchestrator).

---

[User guide](docs/USER-GUIDE.md) · [Install](docs/install.md) · [Components](docs/components.md) · [Telemetry](docs/telemetry.md) (off unless you turn it on) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Issues](https://github.com/Kanevry/session-orchestrator/issues) · [MIT](LICENSE) · [Privacy](https://session-orchestrator.com/datenschutz) · [npm](https://www.npmjs.com/package/session-orchestrator) · [All docs](docs/README.md)

Provided as-is: a community project with best-effort maintenance and no SLA. Independent, and not affiliated with or endorsed by Anthropic, OpenAI or Cursor. The method is taught at [agenticbuilders.at](https://agenticbuilders.at); the plugin is free and does not need the courses.
