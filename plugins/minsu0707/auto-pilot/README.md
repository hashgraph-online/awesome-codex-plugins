# Auto Pilot

<p align="center">
  <img src="./assets/auto-pilot.png" alt="Auto Pilot mascot" width="260" />
</p>

> Ask once. Lock the brief. Keep shipping.

The mascot was created with inspiration from the hero icon style introduced by the creator of [oh-my-codex](https://github.com/Yeachan-Heo/oh-my-codex).

![GitHub stars](https://img.shields.io/github/stars/minsu0707/auto-pilot?style=flat-square)
![GitHub last commit](https://img.shields.io/github/last-commit/minsu0707/auto-pilot?style=flat-square)
![GitHub repo size](https://img.shields.io/github/repo-size/minsu0707/auto-pilot?style=flat-square)
![License](https://img.shields.io/github/license/minsu0707/auto-pilot?style=flat-square)

English | [한국어](./README.ko.md) | [日本語](./README.ja.md)

## Install in One Line

Stable `v0.1.1` currently expects `curl`, `tar`, and `python3` and keeps the published slash-command entry point:

```bash
curl -fsSL https://raw.githubusercontent.com/minsu0707/auto-pilot/v0.1.1/install.sh | bash
```

To preview the next release line on `develop`, install it explicitly:

```bash
curl -fsSL https://raw.githubusercontent.com/minsu0707/auto-pilot/develop/install.sh | env -u NO_COLOR bash
```

Use `v0.1.1` for the currently published release. Use `develop` only when you intentionally want unreleased behavior for testing. When the next stable tag is created, update the stable install URL, run examples, and baked-in stable ref together.

## Run in Codex

### Stable `v0.1.1`

```text
/auto-pilot:autopilot Build a budgeting app for freelancers
```

Use `/auto-pilot:autopilot` as the stable public entry point.
Restart Codex once after installation so the slash command is loaded.
Install once, then route to intake for new projects and resume automatically for existing ones.
After restart, you can also use the natural-language shortcut `Build a budgeting app for freelancers ap`.

### Preview on `develop`

```text
$auto-pilot Build a diary app my friend Dohyeon would love
```

Use `$auto-pilot` only if you installed from `develop`.
After restart, you can also use the natural-language shortcut `Build a diary app my friend Dohyeon would love ap`.

The sections below describe the current repository workflow on `main`, including features that will ship in the next stable release.

## What It Is

Auto Pilot is a Codex plugin for turning a short product request into a resumable execution workflow.

- Ask for the minimum important inputs once
- Save a reusable project contract
- Keep shipping until a real human-only blocker appears
- Resume later from saved state instead of rediscovering context

## Why It Exists

Short prompts are convenient, but they are usually too weak for long autonomous work.

Auto Pilot closes that gap by adding:

- one-question-at-a-time intake
- explicit definition of done
- a default blocker policy
- resumable project state

The goal is simple: less babysitting, more forward motion.

## Core Features

- Converts a short project request into a structured intake session
- Uses a `1. Question` / `Questions remaining: N` interaction pattern
- Inserts an upfront integration setup phase when auth or managed services need env values
- Writes `autopilot/state.json`, `autopilot/blockers.json`, `autopilot/secrets-status.json`, and `docs/next.md` as the initial runtime contract
- Writes `docs/spec.md` and `docs/progress.md` once setup is complete
- Adds `docs/design.md` for user-facing projects so UI work starts from a concrete design brief instead of generic defaults
- Keeps enough state for the next Codex session to resume from where it stopped
- Keeps design research scoped to a brief and a curated reference stack instead of pretending broad web research already happened
- Keeps canonical plugin code, docs, and installer logic at the repository root

## Quick Start

These CLI examples are for plugin development or local debugging.
Run them from the Auto Pilot repository root or the installed plugin directory.
If you are using Auto Pilot inside Codex, prefer `$auto-pilot` or `/auto-pilot:autopilot` and ignore this CLI section.

Start a new intake session:

```bash
./scripts/autopilot start \
  --workspace /tmp/my-project \
  --prompt "Build a diary app my friend Dohyeon would love"
```

Answer the current question:

```bash
./scripts/autopilot answer \
  --workspace /tmp/my-project \
  --text "Teenagers who want a cozy, private diary they can decorate every day"
```

Check the current mode and status:

```bash
./scripts/autopilot status \
  --workspace /tmp/my-project
```

If the project needs upfront integration env values, submit them in one payload:

```bash
./scripts/autopilot secrets \
  --workspace /tmp/my-project \
  --text 'GOOGLE_CLIENT_ID=...'
```

After the final answer, Auto Pilot follows one of two paths.

If setup is already complete, or no upfront env values are needed, it generates:

- `docs/spec.md`
- `docs/progress.md`
- `docs/next.md`
- `docs/design.md` for user-facing projects
- `autopilot/state.json`
- `autopilot/blockers.json`
- `autopilot/secrets-status.json`

If required env values are still missing, it moves into `setup-secrets` and writes:

- `docs/next.md`
- `autopilot/state.json`
- `autopilot/blockers.json`
- `autopilot/secrets-status.json`
- `.env.example`

If setup is still pending, that project still counts as an existing Auto Pilot project because `autopilot/state.json` already exists.

## How It Works

1. A short prompt starts intake.
2. Auto Pilot asks one question at a time.
3. The answers are normalized into a project contract.
4. If required env values are missing, Auto Pilot pauses in a single `setup-secrets` phase and asks for them in one consolidated payload.
5. User-facing projects also get a `docs/design.md` brief built from the selected theme, vibe, and design direction.
6. Runtime state is created for future execution and resume.
7. Codex can continue from saved files instead of rediscovering context.

## Repository Layout

- `docs/01-product-brief.md`: product overview
- `docs/02-prd.md`: functional requirements and operating model
- `docs/03-plugin-spec.md`: plugin structure and state model
- `docs/04-mvp-roadmap.md`: MVP implementation sequence
- `docs/05-how-it-works.md`: visual walkthrough of intake, state, and resume flow
- `docs/06-usage-guide.md`: detailed install, run, resume, CLI, and team-usage guide
- `docs/i18n/*`: localized README files
- `assets/auto-pilot.png`: mascot image
- `.codex-plugin/plugin.json`: Codex plugin manifest
- `commands/autopilot.md`: secondary plugin command entry point
- `skills/auto-pilot/SKILL.md`: main orchestration skill
- `skills/autopilot-intake/SKILL.md`: one-question-at-a-time intake skill
- `skills/autopilot-resume/SKILL.md`: resume skill
- `scripts/autopilot`: recommended CLI entry point
- `scripts/autopilot.py`: Python backend for the CLI wrapper
- `scripts/*.py`: intake, answer recording, and status scripts
- `templates/*.json`: state templates
- `install.sh`: canonical installer
- `uninstall.sh`: canonical uninstaller

## Current Status

This repository root is the canonical plugin root, docs home, and installer home.

For end users, the recommended flow is the one-line installer, one Codex restart, then `$auto-pilot` inside Codex.
For a fuller walkthrough, start with `docs/06-usage-guide.md`.
