# magents (Codex plugin)

[![HOL Trust](https://img.shields.io/endpoint?url=https%3A%2F%2Fhol.org%2Fapi%2Fregistry%2Fbadges%2Fplugin%3Fslug%3Dabnegate%252Fmagents%26metric%3Dtrust%26style%3Dflat)](https://hol.org/registry/plugins/abnegate%2Fmagents)

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
