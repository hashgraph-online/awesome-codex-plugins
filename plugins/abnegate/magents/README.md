# magents (Codex plugin)

Shared session bus for Codex: skill + MCP (`magents mcp`).

## Prerequisite

```bash
brew install abnegate/tap/magents
```

`magents` must be on PATH.

## Install

Point Codex at this plugin directory (or install from a marketplace that mirrors
`plugins/codex`). Manifest: `.codex-plugin/plugin.json`.

## What it does

List/read other live sessions, hand off, send into a specific chat, spawn
independent work that replies through magents. Skill: `skills/magents/SKILL.md`.
