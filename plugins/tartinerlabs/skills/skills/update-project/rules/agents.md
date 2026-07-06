---
title: Agents Maintenance
impact: MEDIUM
tags: agents, claude-agents, documentation
---

**Rule**: Keep agent definitions current by verifying they reflect the actual project state. Look under `.claude/agents/*.md` (Claude Code) and `.agents/agents/*.md` (cross-agent convention).

### Agent File Format

Each agent file has YAML frontmatter followed by a markdown body that serves as the agent's system prompt. Frontmatter fields vary by agent; Claude Code uses `name`, `description`, `tools`, `model`, `permissionMode`, `maxTurns`, `skills`, `mcpServers`, `hooks`, `memory`. Preserve the field set the target agent expects rather than forcing one format.

### What to Scan

- **File paths**: Directories, configs, and source files referenced in the system prompt body
- **Tool permissions**: `tools` and `disallowedTools` in frontmatter vs what the agent actually needs
- **Commands**: Shell commands, scripts, or build steps mentioned in agent instructions
- **Skills**: Skills listed in `skills` frontmatter — verify they still exist and are relevant
- **Conventions**: Coding patterns, naming rules, or workflows described in agent body

### What to Update

- Fix file paths that have moved or been deleted
- Add or remove entries in `tools` / `disallowedTools` to match current agent responsibilities
- Update commands that have changed (e.g., new package manager, renamed scripts)
- Refresh conventions that have evolved in the codebase
- Update `model` if the agent's complexity no longer matches (e.g., `haiku` for simple tasks, `sonnet` or `opus` for complex ones)

### What NOT to Do

- Don't change an agent's `name` or `description` without understanding its role
- Don't remove agents that are still in use
- Don't duplicate instructions already covered by the agent instruction file (CLAUDE.md / AGENTS.md) or project rules
- Don't add `permissionMode: bypassPermissions` without explicit justification
