# Bootstrap Gate

> Single source of truth for the bootstrap gate check.
> Referenced by: plan, session-start, wave-executor, session-end, discovery, evolve.

## Purpose

Every session-orchestrator skill runs this gate check silently at the start of Phase 0. When the gate is open, execution continues with zero overhead. When the gate is closed, the bootstrap skill is invoked before any other work begins.

<HARD-GATE>
If GATE_CLOSED, you MUST invoke `skills/bootstrap/SKILL.md`. Do NOT:
- Fall back to "pragmatic paths"
- Create files, directories, or code without running bootstrap first
- Interpret the user's request as permission to skip structure setup
- Rationalize that "the user clearly wants X, so structure can come later"
- Proceed to Phase 1 of any skill while the gate is closed

There is no bypass. There is no exception for urgent requests, demo repos, or spike work.
The ONLY valid next action when GATE_CLOSED is invoking the bootstrap skill and waiting for it to complete.
</HARD-GATE>

## Gate Check Algorithm

Execute these three checks in order. Any single failure = GATE_CLOSED.

```
1. Read $REPO_ROOT/CLAUDE.md (or AGENTS.md on Codex CLI / Pi).
   - If the file does not exist → GATE_CLOSED (reason: no-claude-md)
   - If the file is zero-length (empty) → GATE_CLOSED (reason: no-claude-md)

2. Grep the config file for the exact string "## Session Config".
   - If the section heading is absent → GATE_CLOSED (reason: no-session-config)

3. Read $REPO_ROOT/.orchestrator/bootstrap.lock.
   - If the file does not exist → GATE_CLOSED (reason: no-bootstrap-lock)
   - If the file is not valid YAML → GATE_CLOSED (reason: invalid-lock)
   - If the file lacks the key "version" → GATE_CLOSED (reason: no-bootstrap-lock)
   - If the file lacks the key "tier" → GATE_CLOSED (reason: no-bootstrap-lock)

All three pass → GATE_OPEN. Return silently. No output, no logging.
```

### Implementation (Bash reference)

```bash
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# Detect config file by platform
if [[ -f "$REPO_ROOT/AGENTS.md" && ( "${SO_PLATFORM:-}" == "codex" || "${SO_PLATFORM:-}" == "pi" ) ]]; then
  CONFIG_FILE="$REPO_ROOT/AGENTS.md"
else
  CONFIG_FILE="$REPO_ROOT/CLAUDE.md"
fi

# Check 1: config file exists and non-empty
if [[ ! -s "$CONFIG_FILE" ]]; then
  GATE_STATUS="CLOSED"; GATE_REASON="no-claude-md"
# Check 2: Session Config section present
elif ! grep -q "^## Session Config" "$CONFIG_FILE"; then
  GATE_STATUS="CLOSED"; GATE_REASON="no-session-config"
# Check 3: bootstrap.lock exists and has required keys
elif [[ ! -f "$REPO_ROOT/.orchestrator/bootstrap.lock" ]]; then
  GATE_STATUS="CLOSED"; GATE_REASON="no-bootstrap-lock"
elif ! grep -q "^version:" "$REPO_ROOT/.orchestrator/bootstrap.lock" \
  || ! grep -q "^tier:" "$REPO_ROOT/.orchestrator/bootstrap.lock"; then
  GATE_STATUS="CLOSED"; GATE_REASON="invalid-lock"
else
  GATE_STATUS="OPEN"
fi
```

## Gate Result Handling

**GATE_OPEN:** Continue immediately with the skill's original Phase 0 / Phase 1. No message to the user.

**GATE_CLOSED:** Read `skills/bootstrap/SKILL.md` and execute the bootstrap flow completely. Do not proceed to the original skill until bootstrap reports completion and `.orchestrator/bootstrap.lock` exists with valid `version` and `tier` keys. Then re-run the gate check once to confirm, and continue.

## `.orchestrator/bootstrap.lock` Schema

The lock file is committed to git. It is a permanent, per-repo marker — not session-ephemeral.

```yaml
# .orchestrator/bootstrap.lock
version: 1
tier: fast | standard | deep
archetype: static-html | node-minimal | nextjs-minimal | python-uv | <baseline-archetype> | null
timestamp: 2026-04-16T09:30:00Z   # ISO 8601 UTC, set at bootstrap time
source: projects-baseline | plugin-template | claude-init
```

| Field | Required | Description |
|-------|----------|-------------|
| `version` | yes | Lock file schema version. Currently always `1`. |
| `tier` | yes | Bootstrap intensity used: `fast`, `standard`, or `deep`. |
| `archetype` | yes | Template archetype applied. `null` for Fast tier (no stack). |
| `timestamp` | yes | ISO 8601 UTC timestamp of when bootstrap ran. |
| `source` | yes | How CLAUDE.md was generated: `projects-baseline` (private path), `plugin-template` (public path, Codex/Cursor), or `claude-init` (public path, Claude Code). |

**Why a dedicated lock file, not STATE.md:** STATE.md is session-ephemeral and reset between sessions. The bootstrap marker is a one-time, permanent repository property. `bootstrap.lock` is committed to git and persists across all sessions and users.

## Idempotency

A repo that has already been bootstrapped passes the gate on every subsequent invocation with zero overhead. The gate check reads three files and performs two grep operations — negligible cost.

`/bootstrap --retroactive` exists for repos that predate the gate (have `CLAUDE.md` + Session Config but no `bootstrap.lock`). It writes the lock without re-scaffolding. Documented in `commands/bootstrap.md`.

## Auto-Skill Dispatch (opt-in, default: off)

When the gate is OPEN and Session Config has `auto-skill-dispatch: true`, the calling skill SHOULD invoke `skills/using-orchestrator/SKILL.md` once before its Phase 1 to detect implicit slash-command intent in the user's first message. The meta-skill is a no-op when the flag is `false` (default), so call sites without the flag see zero behavior change.

Cross-reference: `skills/using-orchestrator/SKILL.md`.
