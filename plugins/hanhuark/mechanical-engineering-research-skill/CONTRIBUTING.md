# Contributing

Thank you for improving this thermal-fluid research workflow plugin.

## Guidelines

- Keep `SKILL.md` concise and focused on routing, workflow, and reference selection.
- Put detailed guidance in `skills/mechanical-engineering-research/references/`.
- Put reusable workflow prompts in `commands/`.
- Prefer reusable research heuristics over project-specific details.
- Preserve source-aware reasoning: separate evidence, assumptions, inference, and uncertainty.
- Validate the skill before opening a pull request.

## Validation

Run:

```powershell
python "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" ".\skills\mechanical-engineering-research"
python "$env:USERPROFILE\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py" "."
```

## Review Checklist

- Does the change help future research, writing, analysis, plotting, presentation, or AI/ML work?
- Is the guidance concise enough to be useful in a skill context?
- Are new reference files linked from `SKILL.md`?
- Are new workflow prompts placed in `commands/` when they are reusable across tasks?
- Are examples generalizable beyond one paper, dataset, or presentation?
