<p align="center">
  <a href="https://github.com/MedAdemBHA/docflow">
    <img src="assets/banner.png" alt="docflow banner" width="100%">
  </a>
</p>

# docflow

[![CI](https://github.com/MedAdemBHA/docflow/actions/workflows/ci.yml/badge.svg)](https://github.com/MedAdemBHA/docflow/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/MedAdemBHA/docflow?style=flat&logo=github&label=stars)](https://github.com/MedAdemBHA/docflow/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/MedAdemBHA/docflow?style=flat&logo=github&label=forks)](https://github.com/MedAdemBHA/docflow/network/members)
[![Last commit](https://img.shields.io/github/last-commit/MedAdemBHA/docflow?style=flat)](https://github.com/MedAdemBHA/docflow/commits/main)
[![GitHub issues](https://img.shields.io/github/issues/MedAdemBHA/docflow?style=flat)](https://github.com/MedAdemBHA/docflow/issues)

**docflow gives your AI coding assistant a memory.** It creates a small set of Markdown
files in your project — a place for *what* the product does, *how* it's built, *why*
choices were made, and *what shipped each month*. Every time you start a session, your
assistant reads the latest of these automatically, so it already knows the project
instead of guessing. No database, no service to run — just text files and a few small
Bash scripts.

> Status: early MVP developer tool. This is not a document approval, e-signature, or workflow-analytics SaaS.

## Words you'll see (one line each)

- **ADR** — a short note recording a decision and *why* you made it.
- **Scaffold** — create the starter folders and files for you, automatically.
- **Spec** — a description of how something works.
- **Changelog** — a monthly log of what shipped.

Full glossary: [docs/references/glossary.md](docs/references/glossary.md).

## Start here

1. Install the plugin (see [Claude Code](#claude-code) below).
2. Open your project and type **`/docflow:doctor`**. It looks at your repo and tells you
   the one command to run next.
3. Run that command. Done.

You don't have to choose between setup paths yourself — `doctor` decides. (If you want to:
`init` for an empty repo, `adopt` if docs already exist, `repair` to refresh an existing
docflow setup.)

## Two ways to use it

Every docflow capability works **two ways** — pick whichever feels natural:

- **Type a command:** `/docflow:check`, `/docflow:doctor`, `/docflow:validate`, …
- **Just ask in plain English:** "is docflow set up here?", "where's the spec for X?",
  "add this to the changelog" — the matching skill triggers automatically.

## What It Does

- Creates a 7-folder documentation taxonomy for product behavior, implementation, decisions, references, plans, reviews, and changelog history.
- Audits existing repos before setup, then recommends init, adopt, or repair.
- Adds a monthly append-only changelog so agents and humans can see what shipped recently.
- Auto-loads the docs map and newest changelog into each session via a read-only `SessionStart` hook.
- Works in Claude Code (commands + skills + hook), Codex (manifest + skills), and any agent via the scaffolded `AGENTS.md`.
- Keeps everything as plain Markdown plus small Bash scripts.

## Demo

Example scaffold output is committed under [examples/basic-repo](examples/basic-repo/).

Minimal flow:

```bash
bash scripts/scaffold.sh --target /path/to/repo --docs-root docs --project "My App"
cd /path/to/repo
find docs -maxdepth 2 -type f | sort
CLAUDE_PROJECT_DIR="$PWD" bash /path/to/docflow/hooks/docflow-context.sh
```

Expected result:

- `docs/README.md` becomes the human-readable documentation index.
- `docs/INDEX.md` becomes the compact path-to-purpose map agents read first.
- `docs/changelog/` holds monthly shipped-work memory.
- `AGENTS.md` tells Codex and other repo-aware agents where to start.

## The 7 Categories

| Folder | Answers | Naming |
|--------|---------|--------|
| `product-spec/` | What a feature does for users | `NN-topic.md` |
| `specs/` | How it is built | `(mmm-yy)-topic.md` |
| `decisions/` | Why a choice was made | `NNNN-title.md` |
| `references/` | Rules, conventions, cheat sheets | `topic.md` |
| `plans/` | Roadmap and work status | `(mmm-yy)-name.md`, `upcoming/*` |
| `reviews/` | Quality, audits, known bugs | `(mmm-yy)-topic.md`, `bugs/` |
| `changelog/` | What shipped by month | `(mmm-yy).md` |

Full naming rules ship in [templates/NAMING.md](templates/NAMING.md).

## Agent Setup

Use this section to install docflow for each agent. Replace `/path/to/docflow` with your local clone path, for example `/Users/Adem/Desktop/migration/docflow`.

Recommended setup flow in any repo:

1. Run doctor first.
2. If the repo has no docs, run init.
3. If the repo already has docs, run adopt.
4. If docflow already exists, run repair.

### Claude Code

Claude Code has native plugin support.

Install from a local checkout inside Claude Code:

```bash
/plugin marketplace add /path/to/docflow
/plugin install docflow
```

Or from GitHub:

```bash
/plugin marketplace add https://github.com/MedAdemBHA/docflow
/plugin install docflow
```

Verify:

```bash
/plugin list
/plugin details docflow@docflow
```

Use in a target repo:

| Need | Command | What it does |
|------|---------|--------------|
| Check readiness | `/docflow:check` | Shows one status and the exact next command |
| Inspect docs state | `/docflow:doctor` | Read-only scan; recommends init, adopt, or repair |
| New repo docs | `/docflow:init` | Creates the docs tree only when no meaningful docs exist |
| Existing docs | `/docflow:adopt` | Adds docflow around current user-authored docs without rewriting them |
| Fix generated docs helpers | `/docflow:repair` | Regenerates `INDEX.md`, installs helpers, reports link/placeholders |
| Validate docs before completion | `/docflow:validate` | Fails on blocking doc issues and reports metadata/update-log cleanup warnings |
| Find the right doc | `/docflow:router` | Routes a question to one doc before reading code |
| Write a doc | `/docflow:author` | Creates a doc in the right folder with the right name |
| Record shipped work | `/docflow:changelog` | Adds an entry to the monthly changelog |
| Plan a feature | `/docflow:feature-plan <msg>` | Creates or updates `plans/features/(mmm-yy)-<slug>.md` |
| Describe product behavior | `/docflow:product-spec <msg or code path>` | Creates or updates `product-spec/` WHAT docs |
| Draft from code signals | `/docflow:scan` | Generates spec/roadmap drafts from code, TODOs, and git churn |

All commands are namespaced as `/docflow:<name>` — type `/docflow:` to see them all.

Examples:

```bash
/docflow:feature-plan add team comments to documents
/docflow:product-spec src/features/comments
```

After updating a local plugin, run `/reload-plugins` in Claude Code before testing new commands.

The Claude plugin also installs a read-only `SessionStart` hook. On new sessions it prints the docs map and newest valid changelog month when the repo has `docflow.json`.

### Codex

This repository includes a Codex plugin manifest at [.codex-plugin/plugin.json](.codex-plugin/plugin.json), but there is no public Codex marketplace entry yet.

Use it today as a local/native marketplace source:

```bash
codex plugin marketplace add /path/to/docflow
```

Enable the plugin in `~/.codex/config.toml` if your Codex build does not add an enabled plugin entry automatically:

```toml
[plugins."docflow@docflow"]
enabled = true
```

If your Codex CLI rejects `service_tier = "default"`, start Codex with:

```bash
codex -c 'service_tier="fast"'
```

Use in a target repo:

```text
Use the doctor skill to inspect this repo.
Use the init skill to initialize docflow in this repo.
```

If docs already exist:

```text
Use the adopt skill to adopt this repo into docflow.
```

For maintenance:

```text
Use the repair skill to regenerate the docs map and check links.
```

Only after `docflow` is published to a Codex marketplace does this command become a ready-to-run install step:

```bash
codex plugin add docflow@<marketplace-name>
```

### Gemini

Gemini does not use the Claude/Codex plugin manifests in this repository. Use docflow by scaffolding repo-level guidance files:

```bash
bash /path/to/docflow/scripts/scaffold.sh --target /path/to/repo --docs-root docs --project "Project Name"
```

Then open the target repo in Gemini and tell it to read:

```text
Read GEMINI.md, then follow AGENTS.md before making changes.
```

The scaffolded `GEMINI.md` points back to `AGENTS.md`, which routes Gemini to `docs/README.md`, `docs/INDEX.md`, and the changelog.

### Cursor

Cursor does not use the Claude/Codex plugin manifests in this repository. Use the scaffolded `.cursorrules` and `AGENTS.md`:

```bash
bash /path/to/docflow/scripts/scaffold.sh --target /path/to/repo --docs-root docs --project "Project Name"
```

Then open the target repo in Cursor. `.cursorrules` points Cursor to `AGENTS.md`, and `AGENTS.md` tells it how to route questions through the docs tree.

### Direct Script Fallback

For any agent or editor, the reliable setup path is the scaffold script:

```bash
bash /path/to/docflow/scripts/docflow-doctor.sh --target /path/to/repo
bash /path/to/docflow/scripts/scaffold.sh --target /path/to/repo --docs-root docs --project "Project Name"
cd /path/to/repo
bash scripts/check-links.sh docs
CLAUDE_PROJECT_DIR="$PWD" bash /path/to/docflow/hooks/docflow-context.sh
```

Expected output:

- `docs/` contains the 7-category doc tree.
- `docflow.json` points agents to the docs root and changelog.
- `AGENTS.md`, `GEMINI.md`, and `.cursorrules` exist at repo root.
- The context hook prints the docs map and skips placeholder changelog files.

Use these script commands for existing repos:

```bash
bash /path/to/docflow/scripts/docflow-adopt.sh --target /path/to/repo --docs-root docs --project "Project Name"
bash /path/to/docflow/scripts/docflow-repair.sh --target /path/to/repo
bash /path/to/docflow/scripts/docflow-validate.sh --target /path/to/repo
```

## Trust And Safety

docflow asks users to install an AI-agent plugin and run Bash. That deserves explicit proof.

- Read [SECURITY.md](SECURITY.md) before installing.
- CI runs `shellcheck` on scripts and hooks.
- CI runs [scripts/test-scaffold.sh](scripts/test-scaffold.sh), covering idempotency, special-character project names, JSON validity, link checks, and hook behavior.
- The Claude `SessionStart` hook is read-only and prints truncated docs context only.

Run checks locally:

```bash
bash scripts/test-scaffold.sh
for t in tests/*.sh; do bash "$t"; done
shellcheck scripts/*.sh hooks/*.sh tests/*.sh
```

## Repository Layout

```text
docflow/
├── .claude-plugin/          # Claude plugin manifest
├── .codex-plugin/           # Codex plugin manifest
├── .github/workflows/       # CI
├── commands/                # Claude slash commands
├── examples/basic-repo/     # Filled example output
├── hooks/                   # SessionStart context hook
├── repo-templates/          # AGENTS.md, GEMINI.md, .cursorrules
├── scripts/                 # doctor, adopt, repair, scaffold, map, generators, tests
├── skills/                  # doctor/check/init/adopt/repair/validate/router/author/changelog
└── templates/               # generic docs skeletons
```

## Agent Support

| Agent | Support level | How it works |
|-------|---------------|--------------|
| Claude Code | Primary | Slash commands, skills, and read-only `SessionStart` context hook |
| Codex | Manifest + repo guidance | Codex plugin manifest, skills, and scaffolded `AGENTS.md` |
| Gemini / Cursor | Repo guidance | Scaffolded `GEMINI.md` and `.cursorrules` point back to `AGENTS.md` |

The portable product is the docs tree and workflow. The plugin runtime is agent-specific.

## Typical Workflow

1. Run doctor to inspect the repo.
2. Run init for empty docs, adopt for existing docs, or repair for existing docflow.
3. Fill `docs/README.md` and `product-spec/00-overview.md`.
4. Write ADRs, specs, plans, and reviews using the category templates.
5. Append shipped work to the current monthly changelog.
6. Run repair after adding or renaming docs.

## GitHub Packaging Checklist

Before presenting this as a polished public tool:

- Add GitHub description: `Documentation memory for AI coding agents`.
- Add topics: `claude-code`, `codex`, `documentation`, `changelog`, `adr`, `ai-agents`, `developer-tools`.
- Publish the next tagged release from a passing CI commit.
- Add a short terminal recording or GIF of install, scaffold, and context loading.
- Verify and document the public Codex install path.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Documentation

This repo dogfoods its own docs system. Browse the knowledge base at [docs/README.md](docs/README.md) — start with [docs/INDEX.md](docs/INDEX.md) for the full `path → purpose` map.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

MIT - see [LICENSE](LICENSE).
