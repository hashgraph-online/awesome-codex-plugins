---
name: session-bootstrap
description: "Run session bootstrap."
---

# `ao session bootstrap` — the universal init prompt

> **One-line value:** every agent in the swarm starts with the same orientation report, regardless of model.

## When to invoke

**Every agent spawned into an AgentOps repository runs this first.** No exceptions. The bootstrap is the contract that makes the future fungibility charter (soc-vuu6.29) operational: identical starting frames let you swap Claude for Codex (or vice versa) on any bead without re-orienting.

Triggers:

- **Manual spawn** — operator just spawned a fresh agent into the repo: `ao session bootstrap`.
- **SessionStart hook (opt-in)** — AgentOps 3.0 ships no SessionStart hook. If you author one via the `hooks-authoring` skill, it can fail-open auto-fire `ao session bootstrap --robot` and discard the exit code.
- **Pipeline submit** — `agentopsd` and headless CI agents call `ao session bootstrap --json` before claiming work.

If you spawned without running it: stop, run it, then resume.

## What it does

Four fail-open substeps, each producing a field in the [session-bootstrap.v1 schema](../../schemas/session-bootstrap.v1.schema.json):

1. **Confirm tier-split AGENTS.md present** — checks `AGENTS.md` and the post-soc-vuu6.3 siblings (`AGENTS-WORKFLOW.md`, `AGENTS-CI.md`, `AGENTS-CODEX.md`, `AGENTS-RUNTIME.md`). Reports which exist. The agent reads them itself once oriented; the bootstrap just confirms presence.
2. **Invoke `onboard --auto`** — the future task-routed reading list subcommand under soc-vuu6.9. Currently P3 / not yet implemented: bootstrap falls back to `phase="skipped:not-implemented"` and continues without blocking.
3. **Count ready beads** — `bd ready --json` length. Surfaces what's immediately claimable. Fails to `null` if bd is missing or errors.
4. **Probe mcp-agent-mail** — soft, optional. Reports unread-count or `null`. Skipped with `--no-mail` or env `MCP_AGENT_MAIL_DISABLED=1`.

## Flags

| Flag        | Effect                                                                                |
|-------------|---------------------------------------------------------------------------------------|
| `--json`    | Emit the full status object (machine-readable, matches the v1 schema)                 |
| `--robot`   | Same as `--json` plus a tight exit-code contract for opt-in SessionStart hooks        |
| `--no-mail` | Skip the mcp-agent-mail probe even when the MCP server is reachable                   |

Default (no flags): one-line human summary on stdout, plus a stderr warning if `AGENTS.md` is missing.

## Output shape

```json
{
  "agents_md_read": true,
  "agents_siblings_read": ["AGENTS-WORKFLOW.md", "AGENTS-CI.md", "AGENTS-CODEX.md", "AGENTS-RUNTIME.md"],
  "onboard_phase": "skipped:not-implemented",
  "ready_beads_count": 12,
  "mail_unread_count": null,
  "runtime": "codex",
  "started_at": "2026-05-21T01:50:00Z",
  "bootstrap_version": "v1"
}
```

Schema at [`schemas/session-bootstrap.v1.schema.json`](../../schemas/session-bootstrap.v1.schema.json) — every field is required; nullable fields carry `null` when the substep was skipped or errored.

## Why fungibility wants this

The [agent-fungibility-philosophy](https://github.com/boshu2/agentops/issues?q=label%3Afungibility-charter) mandates: *one init prompt for every agent regardless of type*. Today every operator hand-rolls orientation: "read AGENTS.md, check bd ready, register with the mail server, then start." Two agents spawned by two different operators don't have the same starting frame. That's anti-fungibility — the swarm can't safely swap them mid-bead.

`ao session bootstrap` is the operational primitive that closes the gap. It's deliberately tiny: ~50 LOC Go + a JSON schema. It does the same four things every time, in the same order, with the same fail-open semantics. Then the agent reads the orientation tier-split itself.

## What this is NOT

- **Not a long orientation document.** The bootstrap reports *status* (read/missing/skipped), not content. Agents still read `AGENTS.md` themselves.
- **Not a workflow engine.** It does not claim work, dispatch, or modify state. It's a status snapshot.
- **Not a hard gate.** Every substep is fail-open: a missing `bd` binary, an unavailable MCP server, or a deferred `onboard` produces a `null`/`skipped` marker and the command still exits 0. The agent decides what to do with degraded orientation.

## Composes with

- **soc-vuu6.3 (AGENTS.md tier split)** — bootstrap reports which sibling files were detected.
- **soc-vuu6.9 (the future `onboard --auto` subcommand)** — when implemented, bootstrap's onboard substep wires through automatically via subprocess shellout.
- **soc-vuu6.29 (Fungibility Charter)** — the doctrinal frame this primitive operationalizes.
- **mcp-agent-mail** — soft dependency; bootstrap surfaces unread count when present.

## CI guarantees

- `cli/cmd/ao/session_bootstrap_test.go` — 8 cases (full status, missing AGENTS.md, partial split, no-mail flag, runtime detection, human summary, JSON round-trip).
- `validate-skill-frontmatter` keeps the SKILL.md frontmatter contract intact.
- No new CI gate added for the schema yet; follow-up bead can add `validate-session-bootstrap-schema` if schema-drift becomes a concern.

## See also

- [`AGENTS.md`](../../AGENTS.md) — orientation entry-point that points here.
- [`AGENTS-WORKFLOW.md`](../../AGENTS-WORKFLOW.md) — what to do after bootstrap reports.
- [`schemas/session-bootstrap.v1.schema.json`](../../schemas/session-bootstrap.v1.schema.json) — full output contract.
