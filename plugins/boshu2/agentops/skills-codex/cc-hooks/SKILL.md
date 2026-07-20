---
name: cc-hooks
description: Claude Code hooks and the AgentOps
---
# Claude Code Hooks

Shell commands that fire at specific points in Claude Code's lifecycle.

Hooks enforce mechanically what prose cannot: a model can reason its way past
an instruction, but it cannot reason its way past an exit 2 — which is exactly
why every hook must be narrow, silent, and reversible.

Named failure mode — **chatty happy path**: a hook that emits stdout on exit 0
corrupts the tool call it was guarding; silence on success is part of the
contract, not a style preference.

## Constraints

- Enforcement hooks (the PreToolUse policy dispatcher) ship by DEFAULT: plugin installs auto-wire `hooks/hooks.json`; skill copies and checkouts wire with one command (`scripts/install-hooks.sh`). Operators can disable per host (`/plugin disable`, or remove the settings matchers).
- Injection hooks (SessionStart/UserPromptSubmit context stuffing) stay dead — the #511 teardown proved delta=0 at 10.35M resident tokens. Never ship one; the hookless-cold-start gate still enforces this.
- Keep the happy path silent and block only with the event's documented exit/JSON contract because stray stdout can corrupt a tool call.
- Bound Stop hooks with `stop_hook_active` and scope matchers narrowly to prevent recursion and unrelated-command interception.

<!-- TOC: Quick Start | Events | Blocking | Writing Hooks | Anti-Patterns | References -->

## Quick Start

Add to `~/.claude/settings.json` (user) or `.claude/settings.json` (project):

```json
{"hooks":{"PreToolUse":[{"matcher":"Bash","hooks":[{"type":"command","command":"my-validator.sh"}]}]}}
```

## Hook Events

| Event | When | Blocks? | Common Use |
|-------|------|---------|------------|
| `PreToolUse` | Before tool runs | Yes | Block/modify commands |
| `PostToolUse` | After tool succeeds | Feedback | Auto-format, lint |
| `PermissionRequest` | Permission dialog | Yes | Auto-approve/deny |
| `UserPromptSubmit` | Prompt submitted | Yes | Add context, validate |
| `Stop` | Claude finishes | Yes | Force continue |
| `SessionStart` | Session begins | No | Load context, set env |
| `Notification` | Notifications | No | Desktop alerts |

Full schemas: [HOOK-EVENTS.md](references/HOOK-EVENTS.md)

## Matchers

```
"Bash"              → exact match
"Edit|Write"        → regex OR
"mcp__.*__write"    → MCP tools
"*" or ""           → all tools
```

Tools: `Bash`, `Read`, `Write`, `Edit`, `Glob`, `Grep`, `Task`, `WebFetch`, `WebSearch`

## Exit Codes

| Code | Effect |
|------|--------|
| 0 | Success - JSON parsed from stdout |
| 2 | **Block** - stderr fed to Claude |
| Other | Non-blocking error |

## Blocking a Tool

**Simple (exit 2):**
```bash
echo "Blocked: reason" >&2 && exit 2
```

**JSON (exit 0):**
```json
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Blocked"}}
```

Decisions: `"allow"` (auto-approve), `"deny"` (block), `"ask"` (show dialog)

## Modifying Input

```json
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow",
  "updatedInput":{"command":"modified-command"}}}
```

## Real-World: DCG + RCH

```json
{"hooks":{"PreToolUse":[{"matcher":"Bash","hooks":[
  {"type":"command","command":"dcg"},
  {"type":"command","command":"rch"}
]}]}}
```

- **DCG**: Blocks `git reset --hard`, `rm -rf`, `git push --force`
- **RCH**: Routes builds to remote workers

Details: [DCG-RCH.md](references/DCG-RCH.md)

## Skill-First Coordination Guard (opt-in)

A copy-paste PreToolUse recipe that nudges agents to **load the coordination
skill before hand-rolling the `am`/`atm`/`ntm`/`tmux send-keys` CLI**. This
recipe auto-installs nothing; you opt in per host (unlike the policy
dispatcher, which ships by default).

**Context-budget doctrine for hooks:** hooks are the most powerful enforcement
(mechanical, can't be reasoned past) but they pollute context — use sparingly. A
hook must be SILENT on the happy path (exit 0, no stdout/stderr), fire ONLY on a
real violation (ideally once per session, sentinel-gated), prefer PreToolUse
violation-guards over `UserPromptSubmit`/`SessionStart` per-turn injectors, and
NEVER emit stray stdout on an exit-0 PreToolUse path (it is parsed as JSON and
breaks the tool call). Block via exit 2 + stderr.

The recipe ships both scripts verbatim, a precise head-only matcher (so a
`br create --body "...am/atm/ntm..."` never false-fires), the two-matcher
opt-in `settings.json` snippet, and a bats test proving every fire/silent case.

Recipe: [SKILL-FIRST-COORDINATION-GUARD.md](references/SKILL-FIRST-COORDINATION-GUARD.md)

## Installed-Skill-Edit Guard (opt-in)

A PreToolUse `Edit|Write` guard that routes an edit of an **installed skill copy**
(`*/.claude/skills/**`, `.codex`, `.gemini`) back to the repo source of truth
`skills/<name>/`. This is a TRUE mistake-token — editing an installed/symlinked
copy has no legitimate form (overwritten on install, or symlinks through to the
factory checkout). Zero false-positive surface: it matches `tool_input.file_path`
only, so a doc that merely mentions `claude/skills` in its body never fires.
Reversible → it ROUTES (exit 2 + one-line redirect), not hard-blocks. Silent on
every other path; fires once per session. Ships INERT — opt-in installer:

```bash
scripts/install-installed-skill-edit-guard.sh   # user scope; --project for project
```

Recipe: [INSTALLED-SKILL-EDIT-GUARD.md](references/INSTALLED-SKILL-EDIT-GUARD.md)

### Value-proof (why this guard survives the hookless teardown)

The keystone guard ships **gate-blind per-fire telemetry**: on each fire it
appends exactly one JSONL line — `{ts, session, token_class, path_sha256}` — to
`${AGENTOPS_HOME:-~/.agents/ao}/guardrail-telemetry.jsonl` (override with
`AGENTOPS_GUARDRAIL_TELEMETRY`). The path is **SHA-256 hashed, never raw**
(privacy); nothing is written on the happy path; the sensor is inert until the
guard is installed and fires. The pre-registered methodology — metric =
declining fire-ATTEMPT rate over time (a signal the redirect cannot fake, NOT the
circular hand-roll rate), minimum N, noise floor, and **null-at-small-N is an
acceptable outcome** — satisfies ADR-0002 l.58 ("test or eval evidence showing
positive value"), the criterion whose absence killed 2.x hooks (#511).

Methodology: [GUARDRAIL-VALUE-PROOF.md](references/GUARDRAIL-VALUE-PROOF.md)

## Policy Dispatch Engine (ships by default)

The admission-control layer (epic age-4qw1): **one** PreToolUse dispatcher —
[hooks/policy-dispatch.sh](hooks/policy-dispatch.sh) — evaluating a
**policies-as-data** registry
([policies/policies.json](policies/policies.json), contract
`schemas/hooks-manifest.v2.schema.json`) instead of N hand-wired settings
entries. This is the membrane at tool-call altitude: same vocabulary, lower
altitude than the pawl/gate at push time.

Per policy: dcg-style id (`domain.object:token`), `mode: deny | route | audit`,
matchers (tool + `command`/`file_path` regex), a `route_message` that names THE
correct tool, a rationale, and a pre-registered `value_proof` (the ADR-0002
lease-on-life: no proof accruing → retire the policy).

**Predicate discipline, schema-enforced** (the #511 anti-lesson): only
`predicate_class: pure` — syntactic mistake-tokens over the command or file
path — may `deny`/`route`. Lookup/stateful predicates ship `audit`-only until
promoted with reviewed fires.
[scripts/lint-policies.sh](scripts/lint-policies.sh) enforces this mechanically
(jq-only; runs in bats and CI).

Semantics: happy path = exit 0, zero output. `deny` = exit 2 + one stderr
route line (full message once per session, short line after — every attempt
still blocks). `route` = exit 0 + `permissionDecision:"ask"` JSON. `audit` =
allow + record. Every fire appends one hashed guardrail-telemetry line
(`token_class` = policy id, plus `mode`/`decision`). Waive once with
`AOP_WAIVE=<policy-id>`, or a `policy-waivers` file line
`<policy-id> <expiry-epoch>`. Missing registry or jq fails OPEN.

Day-1 enforce cohort (age-wnyt, all pure-regex, high-pain):

| Policy | Blocks | Routes to |
|---|---|---|
| `core.git:add-beads-ledger` | `git add` naming `_beads/` (private ledger leak is one-way) | push the ledger repo itself — never `git add _beads` in the public tree |
| `core.provenance:ledger-hand-append` | redirect/`tee`/Edit/Write onto `docs/provenance/ledger.jsonl` (hash-chained, sealed) | `ao provenance add` |
| `core.skills:copy-into-installed` | `cp`/`rsync`/`mv` INTO `~/.claude|.codex|.gemini/skills` (dest-position enforced) | `ao skills link` |
| `core.skills:edit-installed-copy` | Edit/Write of an installed skill copy (`file_path` only — prose can never fire it) | edit repo `skills/<name>/` |

**How it reaches users — every install path delivers hooks:**

| Install path | Delivery |
|---|---|
| Claude Code plugin (`claude plugin install agentops@agentops-marketplace`) | **Automatic** — the plugin bundles `hooks/hooks.json` (`${CLAUDE_PLUGIN_ROOT}` paths); hooks are active on install, no wiring step |
| `npx skills@latest add boshu2/agentops` / skills.sh copy | The skill package carries its own installer: `~/.claude/skills/cc-hooks/scripts/install-hooks.sh` (one command; file copies cannot self-wire) |
| git clone / brew checkout | `scripts/install-policy-dispatch.sh` (delegates to the same skill-embedded installer) |

The installer lints the registry before wiring, backs up settings, and is
idempotent. Disable per host with `/plugin disable agentops` or by removing the
two PreToolUse matchers from settings.

Contract tests: `tests/scripts/policy-dispatch.bats` (block+message+telemetry
per policy, stray-stdout hazard, waivers, audit/route modes, fail-open).

## Writing Your Own Hook

**Minimal Python:**
```python
#!/usr/bin/env python3
import json, sys

data = json.load(sys.stdin)
cmd = data.get('tool_input', {}).get('command', '')

if 'dangerous' in cmd:
    print("Blocked: dangerous", file=sys.stderr)
    sys.exit(2)

sys.exit(0)  # Allow
```

**Hook input (stdin):**
```json
{"tool_name":"Bash","tool_input":{"command":"npm test"},"session_id":"...","cwd":"..."}
```

## Environment Variables

| Variable | Scope | Purpose |
|----------|-------|---------|
| `CLAUDE_PROJECT_DIR` | All | Project root |
| `CLAUDE_ENV_FILE` | SessionStart/Setup | Persist env vars |

## Stop Hook (Force Continue)

```json
{"decision":"block","reason":"Tests failing. Fix before stopping."}
```

**Critical:** Check `stop_hook_active` to prevent infinite loops.

## Anti-Patterns

| Don't | Do |
|-------|-----|
| Old object format | Array format with `matcher` |
| Unquoted `$VAR` | `"$VAR"` |
| Exit 2 with JSON | Exit 2 uses stderr only |
| Skip `stop_hook_active` check | Always check in Stop hooks |

## Debugging

```bash
claude --debug  # Hook execution details
/hooks          # View/edit in REPL
```

## Output Specification

- **Path:** user `~/.claude/settings.json` or project `.claude/settings.json`, plus explicitly named hook scripts; no runtime hook is installed by default.
- **Filename:** preserve `settings.json`; give scripts descriptive executable filenames rather than embedding large shell programs in JSON.
- **Format:** valid Claude hook JSON using event arrays, matchers, and command objects; hook stdout/stderr and exit codes follow the selected event schema.
- **Exit code:** validate with `jq -e '.hooks | type=="object"' <settings.json>` and a representative silent/fire test for each matcher; any parse error, noisy happy path, or recursion risk blocks activation.
- **Downstream handoff:** consumed by the operator only after the exact scope, reversal command, test evidence, and opt-in location are reported.

## Quality Checklist

- The matcher fires on the intended event/input and stays silent on representative near misses.
- Blocking and allow paths use the documented exit code and output channel without leaking context.
- The hook is reversible, narrowly scoped, recursion-safe, and clearly labeled as opt-in host policy.

## References

- [HOOK-EVENTS.md](references/HOOK-EVENTS.md) - All events with full schemas
- [DCG-RCH.md](references/DCG-RCH.md) - Production examples (dcg, rch)
- [INSTALLED-SKILL-EDIT-GUARD.md](references/INSTALLED-SKILL-EDIT-GUARD.md) - Opt-in guard routing installed-skill edits to repo skills/ (keystone)
- [GUARDRAIL-VALUE-PROOF.md](references/GUARDRAIL-VALUE-PROOF.md) - Pre-registered value-proof methodology + per-fire telemetry contract (ADR-0002 l.58)
- [PATTERNS.md](references/PATTERNS.md) - Auto-format, logging, notifications
- [JSON-OUTPUT.md](references/JSON-OUTPUT.md) - Response schemas
