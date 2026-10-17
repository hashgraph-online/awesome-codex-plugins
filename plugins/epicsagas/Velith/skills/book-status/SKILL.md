---
name: book-status
description: "Book project status and progress dashboard. Scans the project, writes status.json for the web UI, and reports phase, chapters, readiness score, and metrics."
model: haiku
allowed-tools: Bash(node), Read, Write
argument-hint: "[project-dir] [--ui] [--metrics]"
---

# Book Status

Run: `node ${CLAUDE_PLUGIN_ROOT}/velith.mjs scan [dir] [--ui]`

Outputs `{dir}/.velith/status.json`, updates `~/.velith/velith.db`, prints a terminal dashboard including the readiness verdict and score when `edits/readiness-report.md` exists.

`--ui` opens the browser dashboard at `http://localhost:9631/{index}/overview`.

`--metrics` also runs `node ${CLAUDE_PLUGIN_ROOT}/velith.mjs metrics {dir}/drafts` and prints per-chapter sentence statistics, repeated phrases, and AI-tell counts. Use it to spot drift between chapters before running the editing pipeline.

Other commands: `list` (all projects), `stats [dir]` (JSON), `words <file>`, `snapshot <dir> <label>`.
