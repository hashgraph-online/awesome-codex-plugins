# Skill Factory Spec Schema

Use a JSON file as input to `create_skill_from_spec.py`.

## Minimal Spec

```json
{
  "id": "example-tool",
  "title": "Example Tool",
  "description": "Use Example Tool for <domain workflow>. Use when Codex needs ...",
  "family": "example-family",
  "tool_name": "Example Tool",
  "tasks": ["setup", "inference", "troubleshooting"],
  "triggers": ["example-tool", "example_api"]
}
```

## Optional Fields

```json
{
  "include_references": true,
  "include_real_run_script": true,
  "register_in_registry": true,
  "openai_display_name": "Example Tool",
  "openai_short_description": "Help with Example Tool workflows",
  "openai_default_prompt": "Use $example-tool to ..."
}
```

## Field Rules

- `id`: lowercase hyphen-case, e.g. `example-tool`
- `title`: user-facing title
- `description`: trigger-quality description for SKILL frontmatter; must start with "Use <tool> for" and end with "Use when Codex needs"
- `tasks`: non-empty list of task slugs (lowercase hyphen-case)
- `triggers`: non-empty list of keywords users would naturally type to invoke this skill
- `family`: routing family label (must match or extend families already in `registry/skills.yaml`)
- `tool_name`: real tool name as it appears in documentation and package names

## Notes

- Defaults: references on, real-run script on, registry append on.
- Registry update is append-only; if `id` already exists, register step is skipped.
- Use `--no-register` during development; enable in the registry manually after hand-tuning.
- Use `--output-root skills-dev` for dev/experimental skills (output goes to `skills-dev/<id>/`).
- Use `--output-root skills` (default) for stable skills ready for routing.
- Save spec files to `skills-dev/specs/<id>-spec.json` — do not drop them inside `skills-dev/skill-factory/`.

## Interactive Spec Building

If the user does not have a spec JSON yet, ask these questions in order and map answers to fields:

| Question | Maps to field |
|---|---|
| What is the tool name? | `tool_name`, `title`, `openai_display_name` |
| Describe the tool in one sentence starting with "Use X for..." and ending with "Use when Codex needs..." | `description` |
| What should the skill id be? (lowercase hyphen-case) | `id` |
| What routing family does this belong to? | `family` |
| What are the main task types? (comma-separated) | `tasks` |
| What keywords would a user type to trigger this skill? | `triggers` |
| Does the tool require an env var / API key? If yes, name it. | note in `openai_default_prompt`; hand-edit `required_env_any` in generated `skill.yaml` |
| Include reference docs? (default: yes) | `include_references` |
| Include real-run script? (default: yes) | `include_real_run_script` |
| Is this a dev/experimental skill or a stable skill? | CLI `--output-root skills-dev` (dev) or default `skills/` (stable) |

Once all answers are collected, write the complete JSON to `spec.json` and confirm with the user before running the generator.

### Example conversation → spec mapping

```
Q: Tool name?          → "AlphaFold3"
Q: Description?        → "Use AlphaFold3 for protein structure prediction. Use when Codex needs to run AF3 inference."
Q: Skill id?           → "alphafold3"
Q: Family?             → "structure-prediction"
Q: Tasks?              → "environment-setup, inference, troubleshooting"
Q: Triggers?           → "alphafold3, af3"
Q: Env var?            → none
```

Resulting spec:

```json
{
  "id": "alphafold3",
  "title": "AlphaFold3",
  "description": "Use AlphaFold3 for protein structure prediction. Use when Codex needs to run AF3 inference.",
  "family": "structure-prediction",
  "tool_name": "AlphaFold3",
  "tasks": ["environment-setup", "inference", "troubleshooting"],
  "triggers": ["alphafold3", "af3"]
}
```
