---
name: repair
description: 'Safe maintenance for an existing docflow setup. Regenerates INDEX.md, installs or refreshes recognized DocFlow-managed helper scripts, runs link checks, and reports placeholder/validation issues. Use when docflow exists, after adding or renaming docs, or when doctor recommends repair.'
---

# repair

Goal: safe generated-file maintenance only.

## Run

```bash
bash scripts/docflow-repair.sh --target <REPO ROOT>
```

## It May Change

- `<DOCS_ROOT>/INDEX.md`
- missing helper scripts under `scripts/`
- existing helper scripts whose headers identify them as DocFlow-managed

## It Must Not Change

- README content
- product specs
- ADRs
- changelog months
- roadmap/plans
- existing project docs
- customized helper scripts without a DocFlow-managed header

Report broken links, placeholders, and validation warnings instead of fixing content unless the user asks.
