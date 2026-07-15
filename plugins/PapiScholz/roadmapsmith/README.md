<p align="center">
  <img src="https://raw.githubusercontent.com/PapiScholz/roadmapsmith/main/assets/roadmapsmith-logo.png" alt="RoadmapSmith logo" width="180">
</p>

<h1 align="center">RoadmapSmith</h1>

**Who this is for:** solo devs and small teams that run AI coding agents (Claude Code, Codex) at least a few hours a week and want an **auditable trail** of what the agent claims it shipped vs what actually landed in the code.

**Who this is NOT for:** (see [When NOT to use](#when-not-to-use) below).

Two commands — `init` and `update` — turn `ROADMAP.md` into a validated, evidence-backed source of truth that survives an agent saying "done!" when nothing is done.

## See it in action

The killer moment: your agent marks a task `[x]`, RoadmapSmith checks the code, and the audit disagrees.

<p align="center">
  <img src="assets/demo.gif" alt="Agent marks a task done without writing code; roadmapsmith --audit catches it and surfaces the task id" width="800">
</p>

Reproduce it locally in ~2 seconds:

```bash
bash scripts/demo/false-claim-repro.sh
```

The script sets up a throwaway repo, adds a task, flips the checkbox without writing code, and runs `update --audit`. Expected output: `checkedWithoutEvidence: 1` and the specific caught task id.

<details>
<summary>Deeper look — A/B demo (two claude-code sessions, one blind to ROADMAP.md)</summary>

<p align="center">
  <img src="assets/demo-ab.gif" alt="A/B demo: claude-code session with ROADMAP.md vs without" width="800">
</p>

Two identical `claude-code` sessions on the same worktree — one can read `ROADMAP.md`, one can't — and the results diverge on evidence, alignment, and audit-cleanliness. Full walkthrough: [`scripts/demo/README.md`](scripts/demo/README.md).

```bash
bash scripts/demo/run.sh
```

</details>

## Install

### CLI

```bash
npm install -g roadmapsmith
```

### Claude Code bundle

```bash
npx skills add PapiScholz/roadmapsmith --skill '*' -a claude-code
```

This installs the native Claude GUI slash commands (`/roadmap-init`, `/roadmap-update`). It does not install the CLI.

## When NOT to use

RoadmapSmith is opinionated tooling. It's the wrong fit if:

- **You already have Jira / Linear / Asana as source of truth.** Adding a third tracker creates drift, not clarity. Stay with what your team already trusts.
- **You don't use AI coding agents.** The killer feature is "agent claims done → validator disagrees against real files". Without an agent, a plain `TODO.md` covers 95% of the value with 5% of the overhead.
- **Your repo is >2 languages or a large monorepo.** The evidence scanner is optimized for single-primary-language repos; monorepo support is best-effort (see `pathAliases` in config).
- **You need multi-user assignment, sprints, or estimation.** RoadmapSmith is a *validation* tool, not a project-management tool. It has no concept of "assignee" or "story points".

If any of the above applies, close this tab. If none apply and you run agents daily, keep reading.

## Quick Start

New repository:

```bash
roadmapsmith init --product-name "MyApp" --primary-user "solo dev" --project-root .
```

Existing repository (import tasks from an existing file):

```bash
roadmapsmith init --import TODO.md --project-root .
```

Set up host integration files only (no ROADMAP.md creation):

```bash
roadmapsmith init --setup-only --hosts codex,claude --project-root .
```

Preview without writing:

```bash
roadmapsmith init --dry-run --project-root .
```

## Daily Flow

Refresh the roadmap with evidence-backed validation:

```bash
roadmapsmith update --project-root .
```

Add a task:

```bash
roadmapsmith update --add-task "Fix login redirect bug" --project-root .
```

Record evidence for a task:

```bash
roadmapsmith update --task <stable-id> --evidence "src/auth.js passes all tests" --project-root .
```

Check northStar alignment vs. repo state:

```bash
roadmapsmith update --check-drift --project-root .
```

Run validation audit after refresh:

```bash
roadmapsmith update --audit --project-root .
```

Preview any update without writing:

```bash
roadmapsmith update --dry-run --project-root .
```

## Command Surfaces

Two commands:

- `init` — creates ROADMAP.md, AGENTS.md, and host integration files
- `update` — refreshes ROADMAP.md with evidence-backed validation, adds tasks, records evidence, or checks drift

### init flags

| Flag | Description |
|------|-------------|
| `--product-name <name>` | Product/project name |
| `--primary-user <user>` | Primary user persona |
| `--problem-statement <text>` | Problem being solved |
| `--import <file>` | Import tasks from file (repeatable) |
| `--hosts <codex,claude>` | Host integrations to set up (default: `codex,claude`) |
| `--editor <name>` | Editor for host setup (default: `vscode`) |
| `--setup-only` | Only write host files, skip ROADMAP creation |
| `--dry-run` | Preview without writing |
| `--project-root <path>` | Project root (default: cwd) |

### update flags

| Flag | Description |
|------|-------------|
| `--add-task <text>` | Add a new task to the managed block |
| `--task <id>` | Task ID to target (use with `--evidence`) |
| `--evidence <text>` | Evidence to add to `--task` |
| `--audit` | Show validation audit after refresh |
| `--check-drift` | Check northStar alignment vs. repo state |
| `--strict` | Strict validation mode |
| `--dry-run` | Preview without writing |
| `--json` | Output in JSON format |
| `--project-root <path>` | Project root (default: cwd) |

## Verification Model

Unchecked tasks are only marked complete when evidence backs them up:

- explicit `Evidence:` lines on the task
- code, test, or artifact files that match the task text

For an evidence audit:

```bash
roadmapsmith update --audit
```

For strict mode (fails on any unverified checked task):

```bash
roadmapsmith update --strict --audit
```

## Docs

- [roadmap-skill/README.md](roadmap-skill/README.md): CLI and package contract
- [docs/release-readiness.md](docs/release-readiness.md): maintainer and release workflow
