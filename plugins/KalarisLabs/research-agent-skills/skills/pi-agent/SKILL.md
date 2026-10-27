---
name: pi-agent
description: Build with and use Pi, the minimal terminal coding harness. Use for installing Pi, configuring providers/models/settings/environment variables, creating Pi skills/extensions/packages/themes/prompt templates, embedding Pi through the SDK, integrating over RPC or JSON event streams, parsing sessions, running local models through the llama.cpp router, developing custom Pi providers and TUI components, or using ecosystem packages such as pi-subagents (delegation/orchestration), pi-mcp-adapter (MCP servers), pi-interview (interactive forms), and pi-web-access (web search, fetching, video understanding).
license: MIT
compatibility: Requires Node.js >= 22.19 and npm for Pi CLI and SDK usage. Pi package name is @earendil-works/pi-coding-agent.
metadata:
  version: '1.4'
  category: research-automation
  maintainer: Kalaris Labs
  tags: coding agents, terminal agents, AI agents, developer tools
---

# Pi Agent

Use this skill when the user wants to operate Pi or build on top of Pi. Pi is a minimal terminal coding harness extended through TypeScript extensions, skills, prompt templates, themes, packages, custom models/providers, SDK integrations, RPC mode, JSON event streams, and TUI components.

## First Decision

Pick the reference before answering or coding:

| User intent | Read |
|---|---|
| What Pi is, docs map, install methods | `references/overview.md` |
| Install, authenticate, first run | `references/quickstart.md` |
| Day-to-day CLI usage, commands, modes, flags, project trust | `references/usage.md` |
| Provider auth, API keys, cloud provider setup | `references/providers.md` |
| Custom model entries, local models, proxies, compat flags | `references/models.md` |
| Local llama.cpp router, `/llama`, model download/load | `references/llama-cpp.md` |
| Settings keys and defaults | `references/settings.md` |
| `PI_*` and other environment variables | `references/environment-variables.md` |
| Extension development, custom tools, events, commands | `references/extensions.md` |
| Custom provider implementation, OAuth, custom streaming | `references/custom-provider.md` |
| Embed Pi in Node/TypeScript | `references/sdk.md` |
| Integrate from another process/language | `references/rpc.md` |
| Consume JSONL event output | `references/json.md` |
| Build terminal UI components | `references/tui.md` |
| Package extensions/skills/prompts/themes | `references/packages.md` |
| Delegate to subagents, chains, parallel runs, orchestration | `references/pi-subagents.md` |
| Connect MCP servers, MCP tool discovery/config | `references/pi-mcp-adapter.md` |
| Interactive interview forms, structured user input | `references/pi-interview.md` |
| Web search, URL/PDF/repo fetching, video understanding | `references/pi-web-access.md` |
| Author Pi skills | `references/skills.md` |
| Prompt templates or themes | `references/prompt-templates.md`, `references/themes.md` |
| Sessions, branching, compaction, parsing JSONL | `references/sessions.md`, `references/compaction.md`, `references/session-format.md` |
| Security, sandboxing, trust | `references/security.md`, `references/containerization.md` |
| Keyboard or terminal issues | `references/keybindings.md`, `references/terminal-setup.md`, `references/tmux.md`, `references/windows.md`, `references/termux.md`, `references/shell-aliases.md` |
| Working on Pi itself | `references/development.md` |

## Build-On-Pi Defaults

Prefer the SDK for Node/TypeScript apps that need type safety, direct state access, in-process custom tools/extensions, or custom resource loading. Use `createAgentSession()` for a single stable session; use `createAgentSessionRuntime()` when the app must replace sessions through new/resume/fork/clone/import flows. Auth and model lookup go through `ModelRuntime.create()`.

Prefer RPC mode when the client is not Node.js, needs process isolation, or wants a language-agnostic JSONL protocol. Start with `pi --mode rpc --no-session` for stateless subprocess integration, then add session flags when persistence matters. Split records on `\n` only — Node `readline` is not protocol-compliant.

Prefer JSON mode for one-shot command-line pipelines that only need streamed events, not bidirectional control: `pi --mode json "prompt"`.

Use extensions for Pi-native behavior: custom tools, command handlers, event hooks, provider registration, custom compaction, path protection, project trust policy, UI prompts, widgets, and TUI components.

Use packages when sharing or installing reusable extensions, skills, prompt templates, or themes across machines or projects.

## Safety Defaults

Pi is local and not sandboxed by default. Treat extensions, packages, skills, shell commands, and project-local `.pi` resources as code with the permissions of the Pi process. Project trust only guards which project inputs load — it is not a sandbox. For untrusted repos or unattended automation, isolate with Docker, OpenShell, Gondolin, a VM, or a remote sandbox.

Do not store secrets in project files. Prefer env vars, `~/.pi/agent/auth.json`, OAuth via `/login`, or command-backed secret lookups in `models.json`/provider config.

## Common Commands

```bash
npm install -g --ignore-scripts @earendil-works/pi-coding-agent
pi
pi -p "Summarize this codebase"
pi --mode json "List files"
pi --mode rpc --no-session
pi --provider anthropic --model claude-sonnet-4-5
pi --model sonnet:high "Solve this complex problem"
pi --tools read,grep,find,ls -p "Review this repository"
pi --tui-mode fullscreen
pi install npm:pi-subagents
pi update --all
```

## Source Coverage

These references summarize the Pi documentation at `https://pi.dev/docs/latest` and every docs page found under it, as of Pi **0.84.2** (docs source: `packages/coding-agent/docs/` in `https://github.com/earendil-works/pi`, formerly `pi-mono`). They also cover the package pages for `pi-subagents`, `pi-mcp-adapter`, `pi-interview`, and `pi-web-access` at `https://pi.dev/packages/`, cross-checked against the published npm READMEs and package docs (`pi-web-access` 0.22.0, `pi-mcp-adapter` 2.25.0, `pi-subagents` 0.49.0, `pi-interview` 0.11.0). When exact API behavior matters, prefer the cited reference page and inspect installed TypeScript definitions under `node_modules/@earendil-works/pi-coding-agent/dist/` and `node_modules/@earendil-works/pi-ai/dist/`.

## Agent operating procedure

1. **Check the environment.** Confirm the objective, evaluation metric, budget (time, compute, money) and stopping criteria.
2. **Pin down the inputs.** Confirm formats, identifiers and parameters from the data or the user. Ask rather than guess any value that changes the result.
3. **Run a small version first.** Run one iteration end to end and inspect logs before scaling up.
4. **Execute the full task** using the instructions and references above.
5. **Validate the result.** Evaluate on held-out data; keep an audit trail of every iteration, hypothesis and result.
6. **Report.** State what was run (versions, commands, parameters), what was checked, and what is still uncertain.

| If this happens | Do this |
|---|---|
| An iteration produces suspiciously large gains | Check for leakage or evaluation bugs before accepting the result. |
| A function, flag or endpoint in these instructions is missing in the installed version | Check the installed version's own documentation (`help()`, `--help`, official docs), adapt, and tell the user. Never invent an API. |
| A required input, identifier or parameter is ambiguous | Ask the user, or state the assumption explicitly before running. |

**Integrity rules**

- Never fabricate results, parameters, identifiers, citations or statistics. If something cannot be run or verified, say so plainly.
- Record negative results; never select or report only favourable runs.
- Treat version-specific details here as possibly outdated: confirm them against the official documentation for the installed version.
- Ask before actions that cost money, consume shared GPUs or cloud quota, touch personal or patient data, or cannot be undone.

## Related skills

- `qiskit`: Build, simulate, transpile, and execute quantum circuits with Qiskit and IBM Quantum Runtime.
