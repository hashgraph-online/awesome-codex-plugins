---
name: context-pack
description: Get a first-pass briefing of a repository (instructions to follow, build/test/lint commands, entry points, key files, workspace packages, layout, active git work, repo memory) before exploring it. Use at the start of work in an unfamiliar or large repo, before reviewing a branch, or when the user asks where something lives.
metadata:
  short-description: First-pass repo briefing
---

# Context Pack

Run the briefing before a manual tree walk. With the MCP server installed, call `get_context` (or `get_changed_context` for review); otherwise run the CLI.

## Workflow

1. Brief: `context-pack --cwd <repo>`.
   - Reviewing or resuming work: `context-pack review --cwd <repo>`.
   - Tight budget: `context-pack compact --cwd <repo>`; more detail: `context-pack deep --cwd <repo>`.
   - A subsystem the ranking misses: add `--include '<glob>'`; noise: `--exclude '<glob>'`.
2. Follow every file under **Agent instructions** before editing.
3. Use **Commands** to verify changes; prefer the ones CI runs.
4. Start reading at **Entry points** and **Key files**; use **Layout** and **Workspace** to find the right package.
5. When you learn a durable, non-obvious fact about the repo (setup quirk, invariant, pitfall), record it: `context-pack memory add "<fact>"` or the `add_memory_note` tool. Never store secrets or task-specific state.

## Guardrails

- Rankings are heuristics. If the code disagrees with the briefing, trust the code and say so.
- The briefing is a starting map; switch to targeted search and file reads once you know where to look.
