# Agent Harness Skills - Repository Instructions

## Purpose

This repository contains reusable skills for building agent-first harnesses across software projects. Keep the skills general-purpose: they should help an agent assess, design, validate, and deliver repo harness work without copying any single product's private workflow.

## Rules

- Keep each skill in `skills/<skill-name>/SKILL.md`.
- Skill folder names and frontmatter `name` values must be lowercase kebab-case.
- Frontmatter `description` must start with `Use when` and describe triggering conditions only.
- Every skill must keep these sections in order: `Overview`, `When To Use`, `Inputs Needed`, `Execution Order`, `Step-by-Step Process`, `Checks`, `Output Format`, `Common Mistakes`, `Example Prompts`.
- Use bilingual repository documentation where appropriate: README files are split by language, but every `SKILL.md` must be English-only.
- Keep examples repo-neutral and engineering-form agnostic. Source repositories may inform authoring privately, but committed guidance must contain only distilled generic patterns.
- Do not add project-specific secrets, URLs, credentials, or private environment assumptions.

## Validation

- Run `python3 scripts/validate_skill_quality.py` before committing.
- Run `python3 scripts/check_skill_language.py` before committing skill wording changes.
- Run `python3 scripts/check_skill_closure.py` before committing skill workflow/reference changes.
- Run `python3 scripts/check_reference_neutrality.py` before committing public skill references or repository guidance.
- Run `python3 scripts/check_profile_consistency.py` before committing profile or template changes.
- Run `python3 scripts/validate_plugin_metadata.py` before committing plugin or extension metadata changes.
- Run `node --check .opencode/plugins/agent-harness-skills.js` before committing OpenCode plugin entrypoint changes.
- For substantial wording changes, test the skill with at least one realistic prompt and record the observed output manually in the commit or PR notes.

## Commit Discipline

- Use Conventional Commits.
- Keep commits atomic: one logical skill/content change per commit.
- Do not mix unrelated skill edits, validation script edits, and formatting churn unless the change is intentionally repository-wide.
