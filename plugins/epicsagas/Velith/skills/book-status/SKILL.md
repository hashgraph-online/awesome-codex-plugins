---
name: book-status
description: "Book project status and progress dashboard. Writes status.json for the web UI."
model: haiku
allowed-tools: Bash(node), Read, Write
---

# Book Status

Run: `node {PLUGIN_ROOT}/velith.mjs scan [dir] [--ui] --plugin-root={PLUGIN_ROOT}`

Outputs: `{dir}/.velith/status.json`, `~/.velith/projects.json`, terminal ASCII dashboard.

`--ui` opens browser dashboard at `http://localhost:9631/{index}/overview`.
