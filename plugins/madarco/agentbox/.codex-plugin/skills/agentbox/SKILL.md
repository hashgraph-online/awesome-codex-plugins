---
name: agentbox
description: "Spin up isolated sandboxes (\"boxes\") for coding agents, run them in parallel, queue background runs, and push commits safely through the host relay. Use when the user wants to run Codex / Claude Code / OpenCode in a sandbox, start more boxes, attach to a running box, or otherwise operate the `agentbox` CLI on their host machine."
---

# AgentBox (host-side)

You are operating on the **user's host machine** (laptop / dev workstation), not inside a box. Use the `agentbox` CLI to provision isolated sandboxes for coding agents and to attach to them.

Requires the CLI: `npm -g install @madarco/agentbox` then `agentbox install` (one-time). Needs Docker for local boxes; cloud providers are optional.

## What AgentBox is, in one paragraph

AgentBox spins up one isolated sandbox per agent run — a local Docker container (default), a Hetzner VPS (`--provider hetzner`), a Vercel Sandbox (`--provider vercel`), an E2B sandbox (`--provider e2b`), or a Daytona cloud sandbox (`--provider daytona`). Each box has its own `/workspace`, but the host's `.git/` is shared, so commits made inside the box land on the host immediately. The agent inside the box has **no host credentials** — `git push`, opening host URLs, capturing checkpoints, and other host-side operations flow through a small host process called the **relay** that runs alongside the CLI.

## Core commands

- `agentbox create` — provision a box and stop (ready, nothing launched). Flags: `-n <name>`, `--provider docker|hetzner|vercel|e2b|daytona`, `--attach`, `-w <path>`, `--snapshot <ref>`.
- `agentbox codex` — provision a box and launch **Codex** inside it, in a detachable tmux session. (`agentbox claude` / `agentbox opencode` launch those agents instead.)
- `agentbox codex attach <box>` — re-attach your terminal to a running agent session.
- `agentbox shell <box>` — open an interactive shell inside a box.
- `agentbox dashboard` — box list plus the selected box's live agent session; quickly switch between agents.

## Run agents in parallel

```sh
agentbox codex            # box 1, attaches your terminal
# Ctrl+a d to detach (the agent keeps running)
agentbox codex            # box 2
agentbox dashboard        # switch between boxes
```

## Access a box

- `agentbox url <box>` — open the box's web app on a host URL tunnel.
- `agentbox screen <box>` — open the box's in-box browser via noVNC.
- `agentbox code <box>` — open the box in VS Code / Cursor (Dev Containers).

## Lifecycle & sync

- `agentbox stop <box>` / `agentbox start <box>` — preserves the upper volume (node_modules included).
- `agentbox pause <box>` / `agentbox unpause <box>` — freeze / resume in under a second.
- `agentbox checkpoint` — capture / list warm box state to start new boxes from in <1s.
- `agentbox download <box>` — sync a box's `/workspace` back to the host (gitignore-aware).
- `agentbox destroy <box>` — destroy a box and discard its upper volume.

`<box>` is optional almost everywhere — it defaults to the current project's box, or use its short index (`1`, `2`, …), name, or id prefix. Run `agentbox <command> --help` for options.

Full docs: https://agent-box.sh/docs
