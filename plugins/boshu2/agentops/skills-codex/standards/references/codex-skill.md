# Codex Skill Standards

## Canonical Contract

Source of truth: `docs/contracts/codex-skill-api.md`

## Frontmatter

Codex SKILL.md frontmatter must include `name` and `description`:

```yaml
---
name: skill-name
description: 'When this skill triggers and when it does not.'
---
```

**Prohibited fields** (Claude-internal, ignored by Codex):
`skill_api_version`, `context`, `allowed-tools`, `model`, `user-invocable`, `output_contract`

Existing generated bundles may still carry compatibility metadata, but the executable validator only requires the `name` and `description` fields above.

## Tool References

Skills must reference the Codex session agent surface that actually exists in this repo's runtime:

| Codex session surface | Purpose | Usage note |
|-----------------------|---------|------------|
| `spawn_agent` | Create a focused subagent | Use one agent per task, judge, or worker |
| `wait_agent` | Wait for one or more agents | Prefer explicit waits over polling loops |
| `send_input` | Send a short follow-up message | Use only for brief steering or retry prompts |
| `close_agent` | Terminate an agent | Use for stuck or no-longer-needed agents |
| `agent_type` | Label the agent role | Common roles in this repo are `default`, `explorer`, and `worker` |

### Prohibited Tool References

These Codex primitives have **no Codex equivalent** and must not appear:

- `Skill(skill=...)` — Codex uses `$skill-name` invocation, not a Skill tool
- `Agent(subagent_type=...)` — Codex uses agent roles, not subagent_type

### Mapped Forms Also Prohibited

Lowercase-hyphenated forms are equally invalid (`task-create`, `team-create`, `send-message`).

The previously-mapped `todo_write` and `update_plan` are **not available** as general-purpose tools in Codex sessions (empirically verified via `codex exec`).

## Skill Discovery Paths

| Scope | Path |
|-------|------|
| Repo | `.agents/skills/` |
| User | `~/.agents/skills/` |
| Admin | `/etc/codex/skills/` |

**Prohibited paths:** `~/.claude/skills/`, `~/.codex/skills/`

## Sub-Agent Patterns

Codex orchestration uses:

| Pattern | Tool | Use Case |
|---------|------|----------|
| Repeated spawn | `spawn_agent` | Many similar tasks, one agent per unit of work |
| Agent roles | `agent_type` | Specialized sub-agents (worker, explorer, monitor) |
| Shell orchestration | `cmd` + `bd` CLI | Issue tracking, wave management |


## Common Issues

| Pattern | Problem | Fix |
|---------|---------|-----|
| `$vibe ` | Claude Skill tool, doesn't exist | Use `$vibe` invocation syntax |
| `context.window: fork` | Claude frontmatter, ignored | Remove from Codex SKILL.md |
| `~/.claude/skills/` | Wrong path | Use `.agents/skills/` |
| `todo_write(...)` | Not available in Codex sessions | Use `bd` CLI or file-based tracking |

## Testing Codex Skills

### Two-Phase Validation (Recommended)

Use a two-phase approach for comprehensive coverage at minimal cost:

**Phase 1 — Static (fast, no API cost):**
- Check frontmatter has only `name` + `description`
- Check for `~/.codex/` paths
- Verify reference files are also clean

**Phase 2 — Live (thorough, requires Codex API):**
```bash
# Check if skill loads and is understood
codex exec -s read-only -C "$(pwd)" \
  "Read \$skill-name. Verify it loads, check all referenced tools exist. Rate PASS/PARTIAL/FAIL."
```

### DAG-First Traversal

When validating multiple interdependent skills, traverse in dependency order (leaves first). This ensures that when a skill references `$other-skill`, the referenced skill has already been validated. Encode the dependency graph explicitly — computed DAGs from frontmatter parsing are error-prone.

### Prompt Constraint Boundaries

When using LLM judges to evaluate skills, always include explicit constraint boundaries:
- "Read-only sandbox and missing network access are NOT reasons to FAIL — those are test environment limits, not skill defects"
- "Rate the skill's design quality, not whether it can execute in this test environment"

Without these boundaries, judges conflate environment limits with skill defects.

### Shell Compatibility

Scripts that validate Codex skills must work on both macOS (BSD tools) and Linux (GNU tools):
- Use `[[:space:]]` not `\s` in grep patterns (BSD grep doesn't support `\s`)
- Use `awk` instead of BSD-incompatible `sed` compound expressions
- Pre-process multi-line LLM output with `tr -d '\n'` before regex extraction

### Release Gate Script

Full DAG-based validation: `scripts/smoke-test-codex-skills.sh`
```bash
scripts/smoke-test-codex-skills.sh --static-only    # Fast CI check (no API)
scripts/smoke-test-codex-skills.sh --chain 2         # Test one chain
scripts/smoke-test-codex-skills.sh                   # Full 54-skill live test
```

## Checklist

When reviewing Codex skills (`skills-codex/*/SKILL.md`):

- [ ] Frontmatter has only `name` + `description`
- [ ] No Claude primitive names (PascalCase or lowercase-hyphenated)
- [ ] No `~/.codex/` paths
- [ ] No `Skill(skill=...)` tool invocations
- [ ] No `Agent(subagent_type=...)` tool invocations
- [ ] No batch-only spawn primitive references
- [ ] No `context.*` or `metadata.*` frontmatter
- [ ] Reference files (`references/*.md`) also free of Claude primitives
- [ ] Instructions are actionable for a Codex agent with only Codex tools
