# Codex Skill Standards

## Canonical Contract

Source of truth: `docs/contracts/codex-skill-api.md`

## Frontmatter

Codex SKILL.md frontmatter must contain **only** `name` and `description`:

```yaml
---
name: skill-name
description: 'When this skill triggers and when it does not.'
---
```

**Prohibited fields** (Claude-internal, ignored by Codex):
`skill_api_version`, `context`, `metadata`, `allowed-tools`, `model`, `user-invocable`, `output_contract`

## Tool References

Skills must reference only tools available in Codex sessions:

| Codex Tool | Purpose | Claude Equivalent |
|------------|---------|-------------------|
| `read_file` | Read file contents | `Read` |
| `apply_patch` | Apply file edits | `Edit` |
| `rg` | Search file contents | `Grep` |
| `glob_file_search` | Find files by pattern | `Glob` |
| `cmd` | Shell execution | `Bash` |
| `git` | Git operations | `Bash(git ...)` |
| `list_dir` | List directory | `Bash(ls)` |
| `spawn_agent` | Spawn a focused sub-agent | `Agent` |
| `send_input` | Send follow-up input to a sub-agent | `SendMessage` |
| `wait_agent` | Wait for one or more sub-agents | Built into Agent tool |
| `close_agent` | Stop a stuck or no-longer-needed sub-agent | `TaskStop` |

### Prohibited Tool References

These Claude Code primitives have **no Codex equivalent** and must not appear:

- `TaskCreate`, `TaskList`, `TaskUpdate`, `TaskGet`, `TaskStop`
- `TeamCreate`, `TeamDelete`, `SendMessage`
- `EnterPlanMode`, `ExitPlanMode`, `EnterWorktree`
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

**NOT:** TaskList-based queueing, TeamCreate/SendMessage coordination, or Skill tool chaining.

## Common Issues

| Pattern | Problem | Fix |
|---------|---------|-----|
| `TaskCreate(subject=...)` | Claude primitive, doesn't exist | Use `bd create` via shell or `spawn_agent` |
| `TeamCreate(team_name=...)` | Claude primitive, doesn't exist | Use agent roles in config |
| `SendMessage(to=...)` | Claude primitive, doesn't exist | Use `send_input` for brief follow-up messages |
| `Skill(skill="vibe")` | Claude Skill tool, doesn't exist | Use `$validate` invocation syntax |
| `context.window: fork` | Claude frontmatter, ignored | Remove from Codex SKILL.md |
| `~/.claude/skills/` | Wrong path | Use `.agents/skills/` |
| `todo_write(...)` | Not available in Codex sessions | Use `bd` CLI or file-based tracking |

## Testing Codex Skills

### Two-Phase Validation (Recommended)

Use a two-phase approach for comprehensive coverage at minimal cost:

**Phase 1 — Static (fast, no API cost):**
- Check frontmatter has only `name` + `description`
- Grep for Claude-only primitives (TaskCreate, TeamCreate, SendMessage, etc.)
- Check for `~/.claude/` paths
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
- [ ] No `~/.claude/` paths
- [ ] No `Skill(skill=...)` tool invocations
- [ ] No `Agent(subagent_type=...)` tool invocations
- [ ] No `context.*` or `metadata.*` frontmatter
- [ ] Reference files (`references/*.md`) also free of Claude primitives
- [ ] Instructions are actionable for a Codex agent with only Codex tools
