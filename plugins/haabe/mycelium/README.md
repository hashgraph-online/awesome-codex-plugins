# Mycelium plugin

This folder is the plugin form of [Mycelium](https://github.com/haabe/mycelium): the skills, hooks,
engine, schemas and scripts Claude Code loads when you install it. It also runs on Codex, Cursor and
opencode; see [install paths](https://github.com/haabe/mycelium/blob/main/docs/install-paths.md).

## Install

```
/plugin marketplace add haabe/mycelium
/plugin install mycelium@haabe-mycelium
```

Then run `/mycelium:start` in your project. [Get started](https://github.com/haabe/mycelium/blob/main/docs/get-started.md) walks through it.

## What it adds

- **Skills** under `skills/`, invoked as `/mycelium:<name>`.
- **Hooks** registered in `hooks/hooks.json`, which Claude Code runs on its own events. Some can
  refuse a tool call; the rest warn or log. [`hooks/README.md`](hooks/README.md) describes each one.
- No agents, no MCP servers, no binaries.

It does not edit your project's own files (CLAUDE.md, README.md, LICENSE). Its state goes in a
`.claude/` folder in your project, which the hooks create on first use. `/mycelium:setup` offers an
`AGENTS.md` at your project root. Everything it runs, reads, writes and connects to is stated in
[`PRIVACY.md`](https://github.com/haabe/mycelium/blob/main/PRIVACY.md).

## Logs in your project

In a project that uses Mycelium (one with `.claude/canvas/` or `.claude/diamonds/`, which
`/mycelium:start` creates), the hooks keep logs in `.claude/state/`. They hold the paths of files the
agent opened and changed, names from its web searches, which guard rules fired, and that a command
failed. Its exit code and program name, never the command or its output. A command is kept only if
you set `MYCELIUM_LEDGER_TRIGGER=on`, and then with obvious secrets masked. Activity logs keep 90 days
(`MYCELIUM_LOG_RETENTION_DAYS` changes it, `0` keeps all). Any hook that finds the folder without an
ignore file writes one. In a project without Mycelium the hooks do nothing at all. Every log, and what
one line holds, is listed in
[`PRIVACY.md`](https://github.com/haabe/mycelium/blob/main/PRIVACY.md#the-logs-the-hooks-keep).

## Network activity

Mycelium sends nothing to its author or to any service the author runs. The same list, in more
detail, is in [`PRIVACY.md`](https://github.com/haabe/mycelium/blob/main/PRIVACY.md).

**One automatic call, to GitHub.** If your project has a `.github/workflows/` directory and the
GitHub CLI (`gh`) is installed and logged in, a hook (`ci-signal.sh`) asks GitHub for the result of
the latest CI run on your current branch, at session start and occasionally when a response ends, so
a failed build is reported in the session that caused it. It uses `gh`'s own login, sends only the
repository and branch name, is rate-limited, and does nothing without workflows, `gh` or a login.
Turn it off with `MYCELIUM_CI_SIGNAL=off`.

**Everything else runs only when you start it:**

- `/mycelium:setup`: installs PyYAML from PyPI, if you accept.
- `/mycelium:metrics-pull`: fetches metrics from the sources you confirmed in `/mycelium:metrics-detect`
  (for example GitHub, Plausible or Stripe), using the credentials you set up for each, and asks
  Hacker News's search API (hn.algolia.com) for mentions of your repository by name. Credentials are
  never written to logs, snapshots or reports.
- `/mycelium:canvas-health`: requests each link cited in your canvas and docs, at most once every
  14 days, to check it still resolves. No credentials are sent.
- `/mycelium:theory-fidelity`: uses your agent's own web search and fetch tools to check sources.
- `/mycelium:canvas-sync`: runs `git pull` on your repository.
- `/mycelium:a11y-check`: may suggest tools (`npx axe`, `lighthouse`, `pa11y`) for you to run; it
  does not run them.

## Architecture cut

| Lives in the plugin (versioned, replaced on update) | Lives in your project (state, yours, committed) |
|---|---|
| `skills/` | `.claude/canvas/*.yml` |
| `hooks/` | `.claude/diamonds/` |
| `engine/`, `harness/` | `.claude/memory/`, `.claude/harness/decision-log.md` |
| `schemas/` | `.claude/evals/` |
| `scripts/` | `.claude/jit-tooling/active-metrics.yml` |

`/mycelium:setup` creates the project-state folders from templates shipped with the plugin.

## Local testing

From the `haabe/mycelium` repo:

```
claude --plugin-dir ./plugins/mycelium
```

Then `/mycelium:ping` should return `MYCELIUM_PLUGIN_LOAD_OK`.

## Sources

- [Claude Code plugins reference](https://code.claude.com/docs/en/plugins-reference)
- [Plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
