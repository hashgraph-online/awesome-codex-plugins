---
name: validate
description: 'Run the profile-aware DocFlow documentation readiness gate. Always blocks broken links, stale maps, and missing headings; applies native naming and section rules strictly to new scaffolds while treating established adopted structures as cleanup guidance.'
---

# validate

Goal: block objectively broken documentation before an agent reports work as complete.

## Run

```bash
bash scripts/docflow-validate.sh --target <REPO ROOT>
```

If running from an installed plugin where scripts are not in the target repo, use the plugin script path.

## Interpret

- `Errors` are blockers. Fix them before saying the docs are complete.
- `Warnings` are legacy/adoption cleanup. Report them, but they do not block unless the user asked for a strict cleanup.
- Fresh scaffold placeholders are warnings because new repos intentionally start from templates.
- `strict` is the native scaffold profile; `adopted` preserves established naming and section vocabulary.

## Rules

- Run after `/docflow:author`, `/docflow:changelog`, `/docflow:repair`, or any manual docs edit.
- Regenerate `INDEX.md` before validation when files were added, renamed, or removed.
- Keep the output concise: status, blockers, warnings worth acting on.
