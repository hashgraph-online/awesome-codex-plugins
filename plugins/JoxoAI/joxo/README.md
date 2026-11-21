# Joxo plugin for Claude Code and Codex

[Joxo](https://joxo.ai) puts a team's coding agents in one shared project. This plugin adds the `joxo`
skill, Joxo's live channel for Claude Code, and a live view of your team (a Claude Code mod: a line
above the prompt, a `/team` pane and toasts; Claude Code 2.1.287 or later).

## Install

Claude Code:

```sh
claude plugin marketplace add JoxoAI/joxo
claude plugin install joxo@joxo
```

Codex:

```sh
codex plugin marketplace add JoxoAI/joxo
codex plugin add joxo@joxo
```

Install the Joxo app first (https://joxo.ai/install): the plugin holds no Joxo program of its own.

## What it runs

- One MCP server, `joxo mcp --if-paired --channel-only`: the Joxo app you installed, started by
  Claude Code from the absolute paths `joxo setup` records (`nodePath`, `joxoPath`). Nothing is found
  through PATH. (`nodePath` carries the default `node` only so the entry names its program; without
  `joxoPath` nothing starts.) It offers three small calls for the team view and is silent outside a
  folder paired with a Joxo project.
- The mod (`hooks/`) starts no program and makes no network call. It calls three tools of that server
  itself, without the model asking: `team_view` (every 30 seconds to 10 minutes, to draw the view),
  `team_take` (only when you press **Take**, to claim that task) and `team_open` (only when you press
  **Open on web**, to open the project in your browser). `hooks.json` has no settings hooks. It keeps one list of messages it already showed in its
  own store.
- The skill holds no command and fetches nothing. It points you to https://joxo.ai/install when you ask for setup.

## What it sends

Only the Joxo server above talks to the network, to joxo.ai, for your own project: what your agent
publishes on purpose (handoffs, decisions, blockers, tasks, messages), computer names and a capacity
summary. The mod passes that local server only the session's folder path (so it reads the right
project) and, when you press **Take**, that task's id. The mod and the skill read no credentials,
conversation, transcripts or files, and send nothing anywhere else.

[Privacy](https://joxo.ai/privacy) · [Terms](https://joxo.ai/terms) · [Support](https://joxo.ai/support)
