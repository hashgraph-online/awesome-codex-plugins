---
name: skill-factory
description: Build production-style Codex skills from a JSON spec, including SKILL.md, skill.yaml, agents/openai.yaml, references, and runnable scripts. Use when Codex needs to scaffold a new tool-specific skill quickly and consistently with this repository's conventions.
---

# Skill Factory

## Overview

Use this skill to produce a new tool-specific skill package interactively or from a pre-built JSON spec.
Prefer: gather requirements → build spec → generate → validate → enable — in that order.

## Follow This Decision Flow

1. Determine whether a spec JSON already exists.
   - If the user provides a path to a `.json` file, skip to step 3.
   - If no spec exists yet, proceed to step 2.

2. Build the spec interactively. Ask the user in order:
   - What is the tool name? (Used in doc text and script comments.)
   - One-sentence description starting with "Use <tool> for ..." and ending with "Use when Codex needs ...".
   - Skill id: lowercase hyphen-case, e.g. `my-tool`.
   - Routing family (e.g. `genome-language-model-inference`, `api-variant-prediction`).
   - Task list, e.g. `["environment-setup", "inference", "troubleshooting"]`.
   - Trigger words users would naturally type, e.g. `["my-tool", "my_tool_api"]`.
   - Does the tool require an env var (API key)? If yes, what is the variable name?
   - Include reference docs? (Default: yes.) Include real-run script? (Default: yes.)
   - Write the resulting JSON to `spec.json` per `references/spec-schema.md` before proceeding.

3. Generate the skill package.
   - Dry-run first: `python skills/skill-factory/scripts/create_skill_from_spec.py --spec <spec.json> --dry-run`
   - For development/experimental skills, add `--output-root skills-dev` to place output under `skills-dev/<id>/` instead of `skills/<id>/`.
   - If output looks correct, run without `--dry-run`.
   - Use `--no-register` if the skill is not yet ready for routing.
   - Use `--overwrite` only when intentionally replacing an existing folder.

4. Validate generated artifacts.
   - Confirm `<output-root>/<id>/` contains: `SKILL.md`, `skill.yaml`, `agents/openai.yaml`.
   - If references enabled: confirm `references/` has four `.md` files.
   - If script enabled: confirm `scripts/run_real_<id>_workflow.py` exists and is executable.
   - Run `bash scripts/validate_registry.sh` from repo root.
   - Run `bash scripts/validate_skill_metadata.sh` from repo root.

5. Enable the skill in the registry.
   - If `--no-register` was used, run `register_skill.py` manually (see commands below).
   - Confirm `registry/skills.yaml` has `enabled: true` for the new skill id.

6. Hand-tune the generated content.
   - `references/inference-patterns.md`: replace the TODO block with at least one real executable code snippet.
   - `references/constraints.md`: replace TODO lines with real limits and coordinate conventions.
   - `scripts/run_real_<id>_workflow.py`: replace the fake_result stub with real inference or API call logic.
   - `SKILL.md` (in the generated skill): populate `## Grounded API/CLI Surface` with verified import paths and function signatures.

## Grounded Factory Commands

- `python skills/skill-factory/scripts/create_skill_from_spec.py --spec <spec.json>`
- `python skills/skill-factory/scripts/create_skill_from_spec.py --spec <spec.json> --dry-run`
- `python skills/skill-factory/scripts/create_skill_from_spec.py --spec <spec.json> --output-root skills-dev`  ← for dev/experimental skills
- `python skills/skill-factory/scripts/create_skill_from_spec.py --spec <spec.json> --no-register`
- `python skills/skill-factory/scripts/create_skill_from_spec.py --spec <spec.json> --overwrite`
- `python skills/skill-factory/scripts/create_skill_from_spec.py --list-templates`
- `python skills/skill-factory/scripts/register_skill.py --repo-root . --skill-id <id> --path <output-root>/<id> --family <family> --task <task> --trigger <trigger>`

## Output Contract

A generated skill must include:
- `SKILL.md` — decision flow + grounded API surface, not a README
- `skill.yaml` — status active, tool contracts, priority rules, input mappings
- `agents/openai.yaml` — display name, short description, default prompt
- `references/` — four `.md` docs with real content (no TODO stubs)
- `scripts/run_real_<id>_workflow.py` — real inference logic with argparse, output JSON, exit contract

## References

- `references/spec-schema.md` — field rules and interactive spec-building guide
- `assets/templates/` — all Jinja-style templates used by the generator

## Scripts

- `scripts/create_skill_from_spec.py`
- `scripts/register_skill.py`
