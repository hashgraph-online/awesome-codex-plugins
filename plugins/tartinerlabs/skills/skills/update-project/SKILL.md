---
name: update-project
description: Use when updating docs, syncing CLAUDE.md, AGENTS.md, or README.md, fixing stale documentation, or refreshing project rules and skills. Keeps docs aligned with code changes.
allowed-tools: Read Glob Edit Write Bash(git:*)
model: sonnet
effort: low
---

You keep project documentation synchronized with recent code changes and git commits.

Run after significant code changes, before a release, or whenever docs may be stale.

Read individual rule files in `rules/` for detailed requirements.

Detect which agent the project targets and maintain its instruction file accordingly: `CLAUDE.md` (Claude Code), `AGENTS.md` (Codex, OpenCode, and the cross-agent standard), or both. Component directories follow the same split — `.claude/` for Claude Code, `.agents/` for the cross-agent convention.

## Rules Overview

| Rule | Impact | File |
|------|--------|------|
| Project instructions | HIGH | `rules/project-instructions.md` |
| README.md | HIGH | `rules/readme-md.md` |
| Agents | MEDIUM | `rules/agents.md` |
| Skills | MEDIUM | `rules/skills.md` |
| Rules | MEDIUM | `rules/rules.md` |

## Workflow

### Step 1: Detect

- Run `git log --oneline -20` and `git diff` to identify recent changes
- Check which agent instruction files exist (`CLAUDE.md`, `AGENTS.md`) and whether README.md exists (create if missing)
- Scan both `.claude/` and `.agents/` for `agents/*.md`, `skills/*/SKILL.md`, and `rules/*.md` files
- Compare documented instructions against actual project state to find stale sections
- Flag any new tools, removed dependencies, changed paths, or renamed commands

### Step 2: Update

Read the relevant rule file for each document and apply updates:
- `rules/project-instructions.md` for CLAUDE.md / AGENTS.md changes
- `rules/readme-md.md` for README.md changes
- `rules/agents.md` for `.claude/agents/` or `.agents/agents/` changes
- `rules/skills.md` for `.claude/skills/` or `.agents/skills/` changes
- `rules/rules.md` for `.claude/rules/` or `.agents/rules/` changes

### Step 3: Validate

- Run project commands mentioned in docs to verify they work
- Check that instructions match current project setup
- Ensure the agent instruction file (CLAUDE.md / AGENTS.md), README.md, agents, skills, and rules complement each other without duplication
- If both CLAUDE.md and AGENTS.md exist, keep shared guidance consistent between them rather than duplicating divergent instructions
