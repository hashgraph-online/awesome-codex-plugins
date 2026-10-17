# Maintenance Notes

## Role in this repository

This skill is one of the shipped capabilities in the `codex-obsidian` plugin and remains the core note-content workflow skill.

## Authoring guidance

- Keep the skill focused on one official surface area.
- Preserve the refusal boundaries unless the official Obsidian CLI surface actually expands.
- Prefer tightening routing and safety policy before adding more files.
- If a future Obsidian capability needs materially different routing or safety rules, split it into a sibling skill instead of widening this one too far.
- Keep explicit invocation as the default until manual prompt checks show implicit routing is selective enough.
- Keep the plugin repo clean and publishable; skill support notes belong here, not in repo-wide scratch files.
