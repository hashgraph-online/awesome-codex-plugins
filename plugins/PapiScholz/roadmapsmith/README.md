<p align="center">
  <img src="https://raw.githubusercontent.com/PapiScholz/roadmapsmith/main/assets/roadmapsmith-logo.png" alt="RoadmapSmith logo" width="180">
</p>

<h1 align="center">RoadmapSmith</h1>

Evidence-backed roadmap workflows for AI coding agents — two commands: `init` and `update`.

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
