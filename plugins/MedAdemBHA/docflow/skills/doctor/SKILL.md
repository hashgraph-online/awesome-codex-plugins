---
name: doctor
description: 'Read-only docflow diagnosis: scans docs, config, changelog, and links, then recommends init, adopt, or repair. Use when asked "check docs setup", "should I set up docflow", "why is docflow not working", or "doctor".'
---

# doctor

Goal: inspect before changing anything. This skill is read-only.

## Run

```bash
bash scripts/docflow-doctor.sh --target <REPO ROOT>
```

If running from an installed plugin where scripts are not in the target repo, use the plugin script path.

## Interpret the recommendation

- `docflow-init` = no meaningful docs found; scaffolding is safe → run `/docflow:init`.
- `docflow-adopt` = docs/README already exist; preserve them → run `/docflow:adopt`.
- `docflow-repair` = docflow exists; regenerate map/check links → run `/docflow:repair`.
- `validation: fail` = docs have blockers; run `/docflow:validate` for details.

## Report

Use these headings: `Status`, `Detected`, `Missing`, `Risks`, `Recommended next command`.

## Rules

- Do not edit files.
- Do not run scaffold/adopt/repair.
- Keep output concise and copy the doctor's section headings.
