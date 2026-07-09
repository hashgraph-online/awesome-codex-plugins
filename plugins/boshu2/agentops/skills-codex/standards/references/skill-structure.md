# Skill Structure Standard

**Version:** 2.0.0
**Last Updated:** 2026-02-20
**Source:** Claude Code official documentation (https://code.claude.com/docs/en/skills)
**Purpose:** Defines the required structure, frontmatter, and quality standards for all AgentOps skills.

---

## Table of Contents

1. [File Structure](#file-structure)
2. [YAML Frontmatter](#yaml-frontmatter)
3. [Description Field](#description-field)
4. [Body Structure](#body-structure)
5. [Progressive Disclosure](#progressive-disclosure)
6. [Quality Checklist](#quality-checklist)
7. [AgentOps Extensions](#agentops-extensions)

---

## File Structure

```
skill-name/
├── SKILL.md              # Required — exact case, no variations
├── SELF-TEST.md          # Optional — trigger and behavior self-test
├── scripts/              # Optional — helper code
├── references/           # Optional — progressive disclosure docs
└── assets/               # Optional — templates, fonts, icons
```

### Rules

| Rule | ALWAYS | NEVER |
|------|--------|-------|
| Entry point | `SKILL.md` (exact case) | `skill.md`, `SKILL.MD`, `Skill.md` |
| Folder name | kebab-case (`bug-hunt`) | spaces, underscores, capitals |
| Name match | Folder name = `name:` field | Mismatch between folder and frontmatter |
| README | None inside repo-runtime skill folders unless an external package profile explicitly allows it | Accidental `README.md` drift in normal AgentOps skill directories |
| Self-test | `SELF-TEST.md` for market-facing execution, judgment, and product skills | User-facing publishable skill with no trigger/behavior test |
| Reserved | Any valid kebab-case name | `claude-*` or `anthropic-*` prefixes |

---

## YAML Frontmatter

### Required Fields

```yaml
---
name: skill-name
description: 'What it does. When to use it. Trigger phrases.'
---
```

Only `description` is technically required (recommended). If `name` is omitted, the directory name is used.

### All Claude Code Frontmatter Fields

| Field | Required | Purpose |
|-------|----------|---------|
| `name` | No | Display name. Lowercase letters, numbers, hyphens only (max 64 chars). Defaults to directory name. |
| `description` | Recommended | What the skill does and when to use it. Claude uses this to decide when to load the skill. |
| `argument-hint` | No | Hint shown during autocomplete (e.g., `[issue-number]`, `[filename] [format]`). |
| `disable-model-invocation` | No | Set to `true` to prevent Claude from auto-loading. User must invoke with `/name`. Default: `false`. |
| `user-invocable` | No | Set to `false` to hide from `/` menu. Use for background knowledge. Default: `true`. |
| `allowed-tools` | No | Tools Claude can use without permission when skill is active (e.g., `Read, Grep, Glob`). |
| `model` | No | Model to use when skill is active (`sonnet`, `opus`, `haiku`, `inherit`). |
| `context` | No | Set to `fork` to run in a forked subagent context. **Only for worker spawner skills** (e.g., council, codex-team). Never set on orchestrators (evolve, rpi, crank) — they need visibility. See two-tier rule in SKILL-TIERS.md. |
| `agent` | No | Which subagent type to use when `context: fork` is set (e.g., `Explore`, `Plan`, `general-purpose`). |
| `hooks` | No | Hooks scoped to this skill's lifecycle. |

### Execution Mode (Three-Tier Rule)

Skills follow a three-tier execution model based on what the caller needs to see:

| Mode | `context: { window: fork }` | When to use |
|------|-----------------|-------------|
| Orchestrator | Do NOT set | Skills that loop, gate phases, or report progress (evolve, rpi, crank) |
| Discovery primitive | Set `window: fork` | Skills that explore/decompose and produce filesystem artifacts (research, plan) |
| Worker spawner / Judgment | Set `window: fork` | Skills that fan out parallel workers or validate artifacts (council, vibe, pre-mortem) |

When `window: fork` is set, the skill's markdown body becomes the task prompt for a forked subagent. The subagent runs in isolation — only the summary returns to the caller's context.

Optionally add `execution_mode` to the `metadata` block for documentation (informational only — no tooling reads this field):

```yaml
metadata:
  tier: execution
  execution_mode: orchestrator  # informational — stays in main context
```

See `SKILL-TIERS.md` for the full classification table and tier definitions.

### Invocation Control Matrix

| Frontmatter | User can invoke | Claude can invoke | Context loading |
|-------------|----------------|-------------------|-----------------|
| (default) | Yes | Yes | Description always in context, full skill loads when invoked |
| `disable-model-invocation: true` | Yes | No | Description not in context, full skill loads when user invokes |
| `user-invocable: false` | No | Yes | Description always in context, full skill loads when invoked |

### String Substitutions

| Variable | Description |
|----------|-------------|
| `$ARGUMENTS` | All arguments passed when invoking the skill |
| `$ARGUMENTS[N]` | Specific argument by 0-based index |
| `$N` | Shorthand for `$ARGUMENTS[N]` |
| `${CLAUDE_SESSION_ID}` | Current session ID |

### Dynamic Context Injection

The `` !`command` `` syntax runs shell commands before skill content is sent to Claude:

```yaml
## Context
- Current branch: !`git branch --show-current`
- Recent changes: !`git log --oneline -5`
```

### AgentOps Extension Fields (under `metadata:`)

AgentOps uses these custom fields under `metadata:` for tooling integration:

```yaml
metadata:
  tier: execution     # see schema enum + tier-caps reference below
  dependencies:       # List of skill names this skill depends on
    - standards
    - council
  internal: true      # true for non-user-facing skills
  replaces: old-name  # Deprecated skill this replaces
```

**Allowed tier values** (binding — from `scripts/validate-skill-schema.sh:174-178`):
`judgment`, `execution`, `library`, `session`, `product`, `contribute`, `meta`, `background`, `orchestration`, `cross-vendor`, `knowledge`.

**Per-tier line caps:** see [`skill-tier-caps.md`](skill-tier-caps.md) for the canonical mapping enforced by `tests/skills/lint-skills.sh:65-77`.

`SKILL-TIERS.md` describes "utility", "team", and "solo" categories — these are narrative groupings, NOT binding `metadata.tier` values. Skills in those categories use `tier: execution` (e.g., `bug-hunt`, `brainstorm`, `system-tuning`).

### Security Restrictions

- No XML angle brackets (`<` `>`) in frontmatter
- No `claude` or `anthropic` in skill names
- YAML safe parsing only (no code execution)

---

## Description Field

The description is the **most critical field** — it determines when Claude loads the skill.

### Structure

```
[What it does] + [When to use it] + [Key capabilities]
```

### Requirements

- Target under 120 characters; hard limit 180 characters for the repo catalog
- Converter adapters may still enforce their own external hard caps, but repo
  skills should stay far below those caps so all descriptions fit the always-loaded catalog
- MUST include trigger phrases users would actually say
- MUST explain what the skill does (not just when)
- No XML tags

### Good Examples

```yaml
# Specific + actionable + triggers
description: 'Investigate bugs or audit code with repro evidence, root cause analysis, and fixes.'

# Clear value prop + multiple triggers
description: 'Validate code readiness with complexity checks and council or inline review.'
```

### Bad Examples

```yaml
# Too vague
description: Helps with projects.

# Missing triggers
description: Creates sophisticated multi-page documentation systems.

# Too technical, no user triggers
description: Implements the Project entity model with hierarchical relationships.
```

### Internal Skills Exception

Library/background/meta skills that are auto-loaded (not user-invoked) may describe their loading mechanism instead of user triggers:

```yaml
description: 'Auto-loaded by /validate, /implement based on file types.'
```

---

## Body Structure

### Recommended Template

```markdown
---
name: skill-name
description: '...'
metadata:
  tier: execution
---

# Skill Name

## Quick Start

Example invocations showing common usage patterns.

## Instructions

### Step 1: [First Major Step]
Specific, actionable instructions with exact commands.

### Step 2: [Next Step]
...

## Examples

### Example 1: [Common scenario]
User says: "..."
Actions: ...
Result: ...

## Troubleshooting

### Error: [Common error]
Cause: ...
Solution: ...
```

### Requirements

| Aspect | Requirement |
|--------|-------------|
| Size | Under 5,000 words; per-tier line caps enforced (see `skill-tier-caps.md`). PreToolUse hook warns at 248 lines globally. |
| Instructions | Specific and actionable (exact commands, not "validate the data") |
| Examples | At least 2-3 usage examples for user-facing skills |
| Error handling | Troubleshooting section for common failures |
| References | Link to `references/` for detailed docs (don't inline everything) |

---

## Progressive Disclosure

Skills use three levels:

1. **Frontmatter** — Always in system prompt. Minimal: name + description.
2. **SKILL.md body** — Loaded when skill is relevant. Core instructions.
3. **references/** — Loaded on-demand. Detailed docs, schemas, examples.

### Rules

- Keep SKILL.md focused on core workflow
- Move detailed reference material to `references/`
- Explicitly link to references: "Read `references/api-patterns.md` for..."
- Move scripts >20 lines to `scripts/` directory
- Move inline bash >30 lines to `scripts/` or `references/`

---

## Quality Checklist

### Before Commit

- [ ] `SKILL.md` exists (exact case)
- [ ] Folder name matches `name:` field
- [ ] Folder name is kebab-case
- [ ] Description includes WHAT + WHEN (triggers)
- [ ] Description under 180 characters, preferably under 120
- [ ] No XML tags in frontmatter
- [ ] No `claude`/`anthropic` in name
- [ ] `metadata.tier` is set and valid
- [ ] SKILL.md under 5,000 words
- [ ] User-facing skills have examples section
- [ ] User-facing skills have troubleshooting section
- [ ] Market-facing user skills have `SELF-TEST.md`
- [ ] Detailed docs in references/, not inlined
- [ ] No README.md in repo-runtime skill folder unless an external package profile explicitly permits it

### Trigger Testing

- [ ] Triggers on 3+ obvious phrases
- [ ] Triggers on paraphrased requests
- [ ] Does NOT trigger on unrelated topics

---

## AgentOps Extensions

These are AgentOps-specific patterns not in the Claude Code spec:

### Tier System

Controls line limits and categorization. Enforced by `tests/skills/lint-skills.sh`.

### Dependencies

Declared under `metadata.dependencies`. Validated by `tests/skills/validate-skill.sh`.

### Skill Tiers Document

Full taxonomy at `skills/SKILL-TIERS.md`.

### Standards Loading

Language standards loaded JIT by `/validate`, `/implement` — see `references/standards-index.md`.

### Marketplace Export Profile

A marketplace-facing package shape differs from AgentOps' repo-runtime shape:

- Published package candidates should pass the target marketplace validator before release.
- Package-clean skills should stay at or under a 50-file validator limit.
- Mega skills above that limit should be split or handled as an explicit product-bundle profile.
- Exported `scripts/` files should be non-executable for marketplace validation, even if repo-native AgentOps scripts remain executable.
- Strong market-facing skills should include `SELF-TEST.md`.
- Large skills should keep `SKILL.md` as a routing kernel and move expensive context into `references/`, `scripts/`, `assets/`, and, when justified, `subagents/`.

Use `docs/reference/skill-quality-rubric.md` for scoring against this profile.
