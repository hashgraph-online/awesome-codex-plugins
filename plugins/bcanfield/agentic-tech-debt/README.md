# debt-ops — Codex adapter

The [debt-ops](../README.md) disciplines, packaged as a [Codex](https://developers.openai.com/codex) plugin. Behavior matches the [Claude Code adapter](../claude-code); this README covers only what's Codex-specific.

## Install

Register the marketplace from your shell, then install from the plugin browser:

```bash
codex plugin marketplace add bcanfield/agentic-tech-debt
```

Open `/plugins` inside Codex and install **debt-ops**. Working *inside* this repo, Codex auto-discovers the bundled marketplace at `.agents/plugins/marketplace.json` once the project is trusted — no add step needed. Requires a git repo and Python 3.10+ (stdlib only).

## What's wired

Layout follows Codex's plugin conventions: hooks bundle their scripts under `hooks/` (referenced via `${PLUGIN_ROOT}/hooks/…`), and each skill bundles its helper under its own `scripts/` (referenced by a relative path, the documented skill convention).

| Codex primitive | File | Role |
| --- | --- | --- |
| `SessionStart` hook | `hooks/session-start.py` | Injects the disciplines + detects/caches quality commands and ADR/registry dirs |
| `PostToolUse` hook (`apply_patch\|Edit\|Write`) | `hooks/feedback.py` | Runs quality commands on edited files under a 3s/command budget |
| `Stop` hook | `hooks/stop.py` | TODO-sniff safety net — nudges when deferrals went unregistered |
| `UserPromptSubmit` hook | `hooks/drop.py` | Handles `drop A` / `drop A,C` / `drop all` shorthand |
| `$add` skill | `skills/add/` (+ `scripts/register.py`) | Registers a debt entry, assigns a batch letter |
| `$review` skill | `skills/review/` (+ `scripts/review.py`) | Audits + ranks the registry; walks paydown |
| `$init` skill *(explicit-only)* | `skills/init/` | Writes the `## Tech debt operations` charter into `AGENTS.md` |
| `$metrics` skill | `skills/metrics/` | Read-only health summary from the metrics log |

## Codex-specific notes

- **Charter file is `AGENTS.md`**, not `CLAUDE.md` — `$init` writes the managed `## Tech debt operations` section there, and the hooks read quality commands from it.
- **Edits are `apply_patch`.** The feedback hook parses the V4A patch envelope (`*** Add/Update File:`, `*** Move to:`) to learn which files changed, since there's no `tool_input.file_path`.
- **Cache** lives at `~/.cache/debt-ops/cache/<repo-hash>/` (override with `DEBT_OPS_CACHE`) so the hooks and skill Bash always agree on one path ([ADR 0012](../docs/adr/0012-codex-deterministic-cache-base.md)).
- **Skill invocation** is `$add` / `$review` / `$init` / `$metrics` (or the `/skills` picker). `$init` is explicit-only (`skills/init/agents/openai.yaml`).
- **Debug:** set `DEBT_OPS_DEBUG=1` to log every hook fire to `<cache>/debug.log`.

## Research

Disciplines map to the [nine tool-agnostic pillars](../docs/tech-debt-pillars.md); the [Claude Code mapping](../docs/tech-debt-plugin-plan.md) explains why each hook exists. Same evidence base, different agent.
