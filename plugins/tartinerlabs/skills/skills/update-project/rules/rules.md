---
title: Rules Maintenance
impact: MEDIUM
tags: rules, claude-rules, documentation
---

**Rule**: Keep project rule files current by verifying they match the actual project conventions and structure. Rules live under `.claude/rules/*.md` (Claude Code) and `.agents/rules/*.md` (cross-agent convention).

### Rules File Format

Each rule file has optional YAML frontmatter with a `paths` field (list of glob patterns scoping when the rule applies) followed by markdown content. Rules without `paths` apply unconditionally to all files.

### What to Scan

- **Path globs**: `paths` patterns in frontmatter — verify targeted files and directories still exist
- **Coding conventions**: Patterns, naming rules, and style guidelines vs actual codebase usage
- **Tool and dependency references**: Libraries, frameworks, or CLI tools mentioned in rules
- **Workflow steps**: Processes or procedures described in rules
- **Subdirectory organisation**: Rules can live in subdirectories (e.g., `rules/frontend/`, `rules/backend/`) and support symlinks

### What to Update

- Fix `paths` globs that reference renamed, moved, or deleted directories
- Update conventions that have evolved (e.g., new naming patterns, changed import styles)
- Refresh tool or dependency references when versions or tools change
- Remove rules that enforce patterns no longer used in the codebase
- Consolidate or split rules if the project structure has changed significantly

### What NOT to Do

- Don't delete rules without confirming the convention is truly abandoned
- Don't weaken security or quality rules without explicit justification
- Don't merge rules into the agent instruction file (CLAUDE.md / AGENTS.md) — rules files exist for modular, targeted enforcement
- Don't break symlinked rules shared across projects
