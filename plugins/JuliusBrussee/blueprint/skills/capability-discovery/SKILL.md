---
name: capability-discovery
description: |
  Detect which MCP servers, Claude Code plugins, and CLI tools are available
  in the current environment, so kits and build sites can bind to real
  capabilities instead of imagined ones. Runs via /ck:init --tools-only or
  `cavekit-tools.cjs discover`. Writes .cavekit/capabilities.json. Trigger
  phrases: "what do we have available", "what's installed", "detect tools",
  "can we use X", "setup tools".
---

# Capability Discovery

The pipeline should never invent tools. Before drafting a kit that references
GitHub Actions, Supabase, Codex, or any other external dependency, check what
actually exists.

## What we detect

- **CLI tools on $PATH**: `gh`, `git`, `node`, `go`, `rustc`, `cargo`,
  `python3`, `pip`, `docker`, `vercel`, `supabase`, `firebase`, `wrangler`,
  `ffmpeg`, `playwright`, `codex`, `graphify`.
- **MCP servers**: parsed from `.mcp.json` in the project root and
  `~/.claude.json` (user level).
- **Claude Code plugins**: parsed from `~/.claude/plugins/installed_plugins.json`.
- **Codex**: presence of the `codex` CLI (enables peer-review commands).
- **Knowledge graph**: presence of `graphify-out/graph.json` (enables the
  `graphify-integration` skill).

## Running discovery

```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/cavekit-tools.cjs" discover
```

Writes `.cavekit/capabilities.json`:

```json
{
  "discovered_at": "2026-04-17T14:22Z",
  "cli_tools": {
    "gh": true, "git": true, "node": true, "codex": false
  },
  "mcp_servers": ["codex-reviewer", "graphify"],
  "plugins": [],
  "codex": { "available": false }
}
```

## How other commands use it

- **`/ck:sketch`** — reads capabilities before proposing integrations. If a
  kit would need a missing tool, it either adds a "Setup" task to the build
  site or asks the user whether to proceed without it.
- **`/ck:map`** — flags tasks that depend on missing capabilities as
  `blocked: setup-required`.
- **`/ck:make`** — refuses to dispatch subagents that require a missing MCP
  server.
- **`/ck:check`** — includes a "Capability Coverage" section in the inspect
  report.

## When to re-run

- After installing a new CLI tool.
- After adding or removing an MCP server.
- At the start of every new project (via `/ck:init`).
- Whenever a task fails with "command not found".

The file is cheap to regenerate — always discover, never guess.

## What we deliberately do not detect

- Network-accessible APIs behind credentials. Availability is not reachability;
  kits should record credentials as a separate concern (never committed).
- IDE extensions. They are not scriptable from the loop and would create false
  assurances.
- Language versions. Version-pinning is the project's responsibility
  (package.json / go.mod / pyproject.toml); discovery only confirms
  executables exist.
