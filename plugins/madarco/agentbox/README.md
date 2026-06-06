# AgentBox (Codex plugin)

Drive [AgentBox](https://github.com/madarco/agentbox) from Codex on the host: create
isolated sandboxes ("boxes") for coding agents, run them in parallel, queue background
runs, and push commits safely through the host relay.

Each box is a local Docker container (default) or a cloud VM (Hetzner / Daytona / Vercel /
E2B). The box shares the host's `.git/` but has **no host credentials** — `git push`, host
URLs, and checkpoints flow through a small host relay. Boxes start in under a second from
checkpoints, ship a per-box browser and VS Code, and work with Codex, Claude Code, and OpenCode.

## Install

```sh
npm -g install @madarco/agentbox
agentbox install
agentbox codex      # launch Codex inside a fresh sandboxed box
```

## What this plugin adds

A host-side skill (`skills/agentbox`) that teaches Codex how to operate the `agentbox` CLI —
provisioning boxes, running agents in parallel, attaching, accessing boxes, and lifecycle.

Source / docs: https://github.com/madarco/agentbox · https://agent-box.sh/docs

License: MIT
