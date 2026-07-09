---
title: Skills Maintenance
impact: MEDIUM
tags: skills, claude-skills, documentation
---

**Rule**: Keep project-scoped skills current by verifying they reflect the actual project state. Skills live at `<name>/SKILL.md` under `.claude/skills/` (Claude Code), `.agents/skills/`, or `.opencode/skills/` (cross-agent and OpenCode discovery paths).

### Skill File Format

Each skill directory contains a `SKILL.md` with YAML frontmatter (`name`, `description`, `allowed-tools`, `model`, `context`, `agent`, `user-invocable`, `disable-model-invocation`, `argument-hint`, `hooks`) followed by a markdown body with instructions. Skills may include a `rules/` subdirectory with standalone rule files.

### What to Scan

- **Description**: `description` serves as the activation trigger — verify it matches what the skill actually does
- **Tool permissions**: `allowed-tools` in frontmatter vs what the skill instructions actually require
- **Commands**: Shell commands, scripts, or CLI tools referenced in skill instructions
- **File paths**: Directories, configs, or source files referenced in skill body
- **Rules subdirectory**: If the skill has a `rules/` folder, verify each rule file is still relevant and referenced in the main `SKILL.md`
- **Invocation settings**: `user-invocable` and `disable-model-invocation` — verify they match the intended use

### What to Update

- Fix `allowed-tools` when the skill needs tools it doesn't have or lists tools it no longer uses
- Update commands that have changed (e.g., renamed scripts, new CLI tools)
- Fix file paths that have moved or been deleted
- Refresh `description` trigger phrases if the skill's scope has changed
- Update `model` if the skill's complexity no longer matches (e.g., `haiku` for simple tasks, `sonnet` for complex ones)
- Remove orphaned rule files no longer referenced by `SKILL.md`

### What NOT to Do

- Don't change a skill's `name` — it's the invocation identifier (e.g., `/skill-name`)
- Don't remove skills that are still in use
- Don't alter skill instructions in ways that change their intended behaviour without understanding the full scope
- Don't duplicate instructions already covered by the agent instruction file (CLAUDE.md / AGENTS.md), agents, or project rules
