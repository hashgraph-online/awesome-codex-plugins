# Machine-Readable Surfaces (For Agents)

## Contents

- [Three Levels of Discovery](#three-levels-of-discovery)
- [Per-Command JSON Mode](#per-command-json-mode)
- [Unified Response Envelope](#unified-response-envelope)
- [Output Format Modes](#output-format-modes)
- [Useful jq Recipes](#useful-jq-recipes)
- [Wire-Level Hook Protocol](#wire-level-hook-protocol)
- [Built-In Robot Docs](#built-in-robot-docs)
- [Where Agents Trip Up](#where-agents-trip-up)

`rch` is built for agents. Every command returns structured output, every command exposes its schema, and the whole CLI is queryable as JSON. This file is the canonical guide for using those surfaces — so an agent can discover capability instead of guessing.

---

## Three Levels of Discovery

### 1. `--capabilities` — what does this `rch` know how to do?

```bash
rch --capabilities
```

Returns a JSON object describing version, build info, supported runtimes (rust, bun, node), available subcommands, and feature flags. Use this once at session start to confirm you're talking to the rch you expect.

### 2. `--help-json` — full CLI tree as JSON

```bash
rch --help-json                  # entire CLI
rch --help-json workers          # one subcommand subtree
rch --help-json workers probe
```

Parse this to drive an agent that needs to construct flags it hasn't seen before.

### 3. `--schema` — JSON Schema for a specific command's output

```bash
rch --schema config lint
rch --schema workers list
rch --schema daemon status
```

Validate the JSON you get back, or use it to build typed clients.

---

## Per-Command JSON Mode

Every subcommand accepts `--json` (and `-F json|toon`):

```bash
rch --json check                          # quick health
rch --json daemon status                  # daemon state
rch --json workers list                   # configured workers
rch --json workers probe --all            # connectivity
rch --json status --workers --jobs        # full status with workers and jobs
rch --json queue                          # build backlog
rch --json hook status                    # hook install state across agents
rch --json agents status                  # agent detection result
rch --json self-test --all                # end-to-end verification
rch --json speedscore --all               # composite score per worker
rch --json fleet status                   # fleet deploy state
rch --json fleet history --limit 20       # deployment timeline
rch --json doctor                         # diagnostic report
rch --json config show --sources          # effective config + provenance
rch --json config get general.socket_path # one value with source
rch --json config diff                    # delta from defaults
rch --json diagnose --dry-run "<cmd>"     # explain routing decision
```

**stdout is always data-only.** Diagnostics go to stderr. Exit code 0 means success.

---

## Unified Response Envelope

Every JSON response follows this shape:

```json
{
  "kind": "ok" | "error",
  "command": "workers.probe",
  "data":  { ... },        // present when kind=ok
  "error": { ... },        // present when kind=error
  "elapsed_ms": 123,
  "request_id": "...",
  "version": "1.0.18"
}
```

Schema: `rch schema export -o ./schemas` produces:

- `api-response.schema.json` — the success envelope
- `api-error.schema.json` — the error envelope
- `error-codes.json` — the full RCH-Exxx catalog

Errors carry `error.code` (`RCH-Exxx`), `error.message`, and `error.remediation` (an array of strings). Use the code as the stable handle.

---

## Output Format Modes

```bash
RCH_OUTPUT_FORMAT=json rch status     # JSON (implies --json)
RCH_OUTPUT_FORMAT=toon rch status     # TOON (compact text-overlay format)
TOON_DEFAULT_FORMAT=toon rch --json status   # Switch JSON-flagged calls to TOON
```

For agent pipelines, JSON is universally safest. TOON is useful for terminals.

`NO_COLOR=1` and `FORCE_COLOR=1` work as expected.

---

## Useful jq Recipes

These jq paths reflect the actual response shapes in rch v1.0.18. Each path
was verified against live output, not assumed.

```bash
# Daemon health summary
rch --json check | jq -r '.data.status'   # "ready" | "degraded" | "unhealthy"

# Daemon version (NOT in 'rch --json daemon status' — that endpoint is minimal)
rch --json status | jq -r '.data.daemon.daemon.version'

# Worker IDs that are reachable. `rch --json workers probe --all` returns
# .data as a flat array, not nested under .workers.
rch --json workers probe --all \
  | jq -r '.data[] | select(.status == "ok") | .id'

# Workers that aren't healthy (any non-"ok" status surfaces an error string)
rch --json workers probe --all \
  | jq -r '.data[] | select(.status != "ok") | "\(.id) [\(.status)] \(.error // "")"'

# Workers under pressure. Pressure fields live FLAT on each worker record
# under .data.daemon.workers[] inside `rch --json status`.
rch --json status --workers \
  | jq -r '.data.daemon.workers[]
           | select(.pressure_state != "healthy")
           | "\(.id) [\(.pressure_state)] \(.pressure_reason_code)"'

# Active builds (lives in `rch --json queue`, NOT `daemon status`)
rch --json queue | jq -r '.data.active_builds[]? | "\(.id) \(.worker_id) \(.project_id)"'

# Queue depth
rch --json queue | jq '.data.active_builds | length'

# Configured workers (canonical shape: .data.workers[].{id, host, user, total_slots, priority, tags})
rch --json workers list | jq -r '.data.workers[] | "\(.id)\t\(.host)\t\(.tags|join(","))"'

# Hook install state across detected agents
rch --json hook status | jq -r '.data.agents[] | "\(.agent)\t\(.status)"'

# All known error codes for a category (after `rch schema export -o ./schemas`)
jq -r '.errors[] | select(.category == "transfer") | "\(.code)\t\(.message)"' schemas/error-codes.json
```

---

## Wire-Level Hook Protocol

`rch` is itself a Claude Code PreToolUse hook. You can hand-craft requests to it (useful for tests):

```bash
printf '%s\n' \
  '{"tool_name":"Bash","tool_input":{"command":"cargo build --release"}}' \
  | rch
```

Three response shapes (full text in `references/HOOKS.md`):

- Empty stdout → allow unchanged
- `{"hookSpecificOutput": {"permissionDecision": "allow", "updatedInput": {"command": "rch exec -- ..."}}}` → allow with rewrite
- `{"hookSpecificOutput": {"permissionDecision": "deny", "permissionDecisionReason": "..."}}` → block

Drive a deeper protocol probe with the skill's `scripts/protocol_test.sh`.

---

## Built-In Robot Docs

```bash
rch --help                       # human help
rch --help-json                  # everything as JSON
rch schema list                  # what schemas are available
rch schema export -o ./schemas   # write them to disk
```

For comparison, `cass robot-docs guide` is the cass equivalent (used by the `cass` skill).

---

## Where Agents Trip Up

- **Forgetting `--json`.** Human-readable rch output is nice but reformats. Always use `--json` (or `--schema`) when piping into other tools.
- **Conflating "exit 0" with "build was remote".** It isn't. See `FAIL_OPEN.md`.
- **Bare `rch dashboard` / `rch web`.** Both launch interactive UIs that block your session. Don't run them from automation.
- **Bare `rch tui`-like commands.** RCH does not currently ship a `tui` subcommand; the dashboard is `rch dashboard`. The general anti-pattern is the same: anything interactive blocks.
- **Reading `--json` output with grep instead of jq.** Field names are stable. Use jq.
