<div align="center">
  <img src="docs/assets/logo.svg" width="96" alt="Herdr Codex Subagents logo">
  <h1>Herdr Codex Subagents</h1>
  <p>Open a read-only Herdr pane for every Codex subagent and close it when the work is done.</p>
</div>

<p align="center">
  <a href="https://github.com/arvkonstantin/herdr-codex-subagents/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/arvkonstantin/herdr-codex-subagents/actions/workflows/ci.yml/badge.svg"></a>
  <a href="https://codecov.io/gh/arvkonstantin/herdr-codex-subagents"><img alt="Coverage" src="https://codecov.io/gh/arvkonstantin/herdr-codex-subagents/graph/badge.svg"></a>
  <a href="https://github.com/arvkonstantin/herdr-codex-subagents/actions/workflows/codeql.yml"><img alt="CodeQL" src="https://github.com/arvkonstantin/herdr-codex-subagents/actions/workflows/codeql.yml/badge.svg"></a>
  <a href="https://github.com/arvkonstantin/herdr-codex-subagents/actions/workflows/dependency-review.yml"><img alt="Dependency review" src="https://github.com/arvkonstantin/herdr-codex-subagents/actions/workflows/dependency-review.yml/badge.svg"></a>
  <a href="https://hol.org/guard"><img alt="HOL Guard" src="https://img.shields.io/endpoint?url=https%3A%2F%2Fhol.org%2Fapi%2Fregistry%2Fbadges%2Fguard%2Farvkonstantin%2Fherdr-codex-subagents%3Fstyle%3Dflat-square"></a>
  <a href="https://scorecard.dev/viewer/?uri=github.com/arvkonstantin/herdr-codex-subagents"><img alt="OpenSSF Scorecard" src="https://api.scorecard.dev/projects/github.com/arvkonstantin/herdr-codex-subagents/badge"></a>
  <a href="https://github.com/arvkonstantin/herdr-codex-subagents/releases"><img alt="Release" src="https://img.shields.io/github/v/release/arvkonstantin/herdr-codex-subagents?display_name=tag&sort=semver"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/github/license/arvkonstantin/herdr-codex-subagents"></a>
</p>

<p align="center">
  <a href="https://github.com/arvkonstantin/herdr-codex-subagents/stargazers"><img alt="Stars" src="https://img.shields.io/github/stars/arvkonstantin/herdr-codex-subagents?style=social"></a>
  <a href="https://github.com/arvkonstantin/herdr-codex-subagents/forks"><img alt="Forks" src="https://img.shields.io/github/forks/arvkonstantin/herdr-codex-subagents?style=social"></a>
  <a href="https://github.com/arvkonstantin/herdr-codex-subagents/issues"><img alt="Issues" src="https://img.shields.io/github/issues/arvkonstantin/herdr-codex-subagents"></a>
  <a href="https://github.com/arvkonstantin/herdr-codex-subagents/pulls"><img alt="Pull requests" src="https://img.shields.io/github/issues-pr/arvkonstantin/herdr-codex-subagents"></a>
  <a href="https://github.com/arvkonstantin/herdr-codex-subagents/graphs/contributors"><img alt="Contributors" src="https://img.shields.io/github/contributors/arvkonstantin/herdr-codex-subagents"></a>
  <img alt="Last commit" src="https://img.shields.io/github/last-commit/arvkonstantin/herdr-codex-subagents">
  <img alt="Commit activity" src="https://img.shields.io/github/commit-activity/m/arvkonstantin/herdr-codex-subagents">
  <img alt="Repository size" src="https://img.shields.io/github/repo-size/arvkonstantin/herdr-codex-subagents">
  <img alt="Primary language" src="https://img.shields.io/github/languages/top/arvkonstantin/herdr-codex-subagents">
  <img alt="Languages" src="https://img.shields.io/github/languages/count/arvkonstantin/herdr-codex-subagents">
</p>

<p align="center">
  <img src="docs/assets/herdr-subagents-demo.png" alt="Herdr showing three Codex subagents working in parallel">
</p>

## Installation

Add this repository as a Codex plugin marketplace, then install the plugin:

```bash
codex plugin marketplace add arvkonstantin/herdr-codex-subagents
codex plugin add herdr-codex-subagents@herdr-codex-subagents
```

Start a new Codex session inside Herdr. Open `/hooks`, review the five plugin hooks, and trust them.

For a local checkout, replace the GitHub repository in the first command with its absolute path.

## What it does

- Keeps the parent in the left half and tiles subagent viewers in the right half without moving focus.
- Streams a compact view of each subagent's local Codex rollout.
- Reopens the matching viewer when Codex interacts with an existing subagent.
- Tracks the exact `agent_id` to `pane_id` relationship and closes the matching pane on completion.
- Does nothing outside a Herdr-managed pane.

The subagent remains owned by the original Codex process. The new pane only runs a viewer; it does
not start another Codex instance.

## How it works

```text
1 viewer    parent | A

2 viewers   parent | A
                   | B

4 viewers   parent | A | C
                   | B | D
```

The viewer renders assistant updates, shell commands, file changes, MCP calls, and terminal status.
The first viewer takes the right half. Further viewers split that half breadth-first, alternating
down and right at each level. Concurrent hook processes serialize state changes with a file lock.
`PostToolUse` resolves successful `send_message` and `followup_task` calls from the parent rollout,
so reused agents get a fresh viewer without keeping idle panes open. Session hooks clean up tracked
viewers after a session ends or before a parent pane is reused.

## Requirements

- [Herdr](https://herdr.dev) with the `pane split`, `pane run`, and `pane close` commands.
- Codex CLI with lifecycle hooks and native subagents. Tested with Codex CLI `0.153.4`.
- Python `3.10` or newer.
- Linux or macOS.

## Safety and privacy

The plugin activates only when `HERDR_ENV=1` and the parent pane can be resolved. Splits use
`--no-focus`, and cleanup refuses to close a pane whose ID matches the parent. Rollout files are read
locally and are never modified or transmitted.

## Configuration

The plugin works without configuration. To change how long a viewer remains visible after a terminal
rollout event, set `HERDR_SUBAGENT_CLOSE_GRACE` to a duration in seconds. The default is `0.35`.

Codex supplies `PLUGIN_ROOT` and `PLUGIN_DATA`. `CODEX_HOME` is respected when set and otherwise
defaults to `~/.codex`.

## Troubleshooting

- No pane appears: start Codex inside Herdr and trust the plugin hooks through `/hooks`.
- After upgrading, restart Codex and trust any newly added plugin hook through `/hooks`.
- A viewer is waiting: the child rollout is created asynchronously and will be attached when it appears.
- A stale viewer remains after a crash: start a new Codex session in the same parent pane to clean it up.
- Diagnostics are written to `plugin.log` in the Codex-provided `PLUGIN_DATA` directory.

When reporting a bug, include any relevant version information. Do not attach rollout files or
credentials.

## Development

The runtime has no third-party dependencies. Development uses [uv](https://docs.astral.sh/uv/):

```bash
uv sync --extra dev
uv run ruff check .
uv run pytest --cov --cov-report=term-missing
```

Tests use a fake Herdr client and never touch the developer's active session. Coverage must remain at
or above 90%.

Herdr Codex Subagents is an independent community project and is not affiliated with OpenAI or
Herdr. See [Contributing](CONTRIBUTING.md), [Security](SECURITY.md), the
[Code of Conduct](CODE_OF_CONDUCT.md), and the [MIT License](LICENSE).
