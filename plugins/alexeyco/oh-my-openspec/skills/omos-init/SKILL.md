---
name: omos-init
description: "Bootstrap baseline specs via $oh-my-openspec:omos-init — research the codebase, agree on capabilities, write openspec/specs/** describing what exists, critique and validate. Invoke via $oh-my-openspec:omos-init."
---

> Codex host adaptation (generated from skills/omos-init/SKILL.md — source of truth stays there):
> - Dispatch roles with `spawn_agent` / `send_input` / `wait_agent` / `close_agent`. Subagents are asynchronous (default up to 6 concurrent threads), so a wave is one batch of `spawn_agent` calls followed by `wait_agent` collection — never poll.
> - `openspec_validate` is provided by this plugin's bundled MCP server as `mcp__openspec__openspec_validate` — call it with `cwd` set to your session's project directory (the `change` filter optional); the VALID/INVALID/UNAVAILABLE/ERROR one-look report format is identical to OpenCode.
> - This skill is invoked as a `$oh-my-openspec:omos-init` mention (or picked from /skills). There is no argument substitution: arguments arrive as plain text in the user's message after the mention — read them from there; when absent, follow this skill's elicitation steps.
> - Roles run from `~/.codex/agents/omos-*.toml`. If `spawn_agent` reports an unknown agent, stop and tell the user to run `$oh-my-openspec:omos-setup` once.

# omos-init

Form the project's initial spec: baseline capability specs under
`openspec/specs/` describing what the code does today. The orchestrator
dispatches, never drafts. You never run git write commands.

## Flow

### 1. Preconditions

- Check the CLI: call `openspec_validate` once. `UNAVAILABLE` → offer to
  install it now: run `npm install -g @fission-ai/openspec` (suggest
  `brew install openspec` on macOS when the user prefers it) — a global
  install is a system change, so proceed only on an explicit yes. Installed
  → re-check and continue. **Declined** → stop: unlike `$oh-my-openspec:omos-plan`,
  this command cannot degrade — bootstrapping specs without the mechanical
  gate is how baselines rot.
- Check the project: `openspec/` must exist. **Missing** → ask consent, run
  `openspec init --tools none` (project artifacts only; the plugin already
  provides every OpenSpec skill). **Declined** → stop.

### 2. Baseline state

Read `openspec/specs/`.

- **Empty** → proceed to discovery.
- **Non-empty** → report existing capabilities; ask: extend (add only
  missing capabilities, never touch existing spec files) or stop. Extend
  mode: discovery skips covered capabilities.

### 3. Capability discovery

Dispatch `omos-researcher` subagents in parallel — one per suspected
area (entry points, packages, services; use the user's `Focus areas:` when
given). Each reports observable behaviors with `path:line` evidence.

Merge findings into a capability map:
`<capability-name>: <one-line purpose> — <key evidence>`. Propose names as
kebab-case nouns of what the system does, sized so each has 2–6
requirements.

### 4. Confirm the map

Present the map; interview until the user confirms add/remove/rename —
at most 5 questions per round, each with a recommendation. A capability no
researcher evidenced is dropped, not guessed.

### 5. Draft baselines

Dispatch `omos-planner` with `MODE: baseline`: the confirmed map plus the
research facts. It writes `openspec/specs/<capability>/spec.md` —
`## Purpose` (a real paragraph, not a stub), `## Requirements` with
`### Requirement:` SHALL statements and `#### Scenario:` WHEN/THEN blocks
describing **current, observed behavior only**. Aspirations belong in
`$oh-my-openspec:omos-plan`, not here.

### 6. Critique loop (≤3 rounds)

Dispatch `omos-critic` in spec-review mode over the new files.

- `NEEDS-FIX` → `omos-planner` revises the exact findings; repeat.
- `CLEAN` → continue. Still `NEEDS-FIX` after 3 rounds → present open
  findings, ask whether to accept or stop.
- Mechanical INVALID lines from `openspec_validate` are always fixed first.

### 7. Approval

Run `openspec_validate` (all specs and changes) and present: capability
list with requirement/scenario counts, gate output verbatim, every
`UNVERIFIED` line the critic flagged.

- Confirmed → final report: files, counts, gate result; next step —
  future work goes through `$oh-my-openspec:omos-plan <idea>`. Stop.
- Rejected → collect the fix list, go to §5.

## Guardrails

- Writes land only in `openspec/specs/` — no changes/, no project code.
- Existing spec files are never overwritten without per-file consent.
- Baseline = what the code does; `UNVERIFIED` beats an invented SHALL.
- Never commit, push, or stage anything.
