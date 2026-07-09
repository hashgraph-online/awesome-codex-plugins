---
name: repair
description: 'Safe maintenance for an existing docflow setup: regenerate INDEX.md, install missing helpers, check links, report placeholders. Use after adding/renaming docs or when doctor recommends repair.'
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

## It Must Not Change

- README content
- product specs
- ADRs
- changelog months
- roadmap/plans
- existing project docs

Report broken links, placeholders, and validation warnings instead of fixing content unless the user asks.
