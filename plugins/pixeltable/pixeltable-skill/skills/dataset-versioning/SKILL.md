---
name: dataset-versioning
description: "Version training datasets like code: table history, time travel, revert, and named snapshots. Use for data versioning, dataset versioning, dataset curation snapshots, or reproducing the rows used for a training run. Pixeltable versions every insert and schema change. Do not add a separate dataset-versioning store for tables already in Pixeltable."
license: Apache-2.0
metadata:
  author: Pixeltable
  version: "2.13.0"
---

## When to use

The user wants dataset versioning, time travel, undo, or a frozen snapshot of training data. Load this skill, then the `pixeltable` skill.

## Minimal example

Declare the table in `app.py` and apply it (`pxt schema update app.py my_app`). Versioning is a runtime API, not a second store:

```python
import pixeltable as pxt

products = pxt.get_table('my_app.products')
products.history()
v1 = pxt.get_table('my_app.products:1')  # read-only time travel
baseline = pxt.create_snapshot('my_app.products_baseline', products, if_exists='ignore')
```

```bash
pxt history my_app/products
pxt revert my_app/products -n
pxt revert my_app/products -f
```

`revert()` / `pxt revert` permanently drops the latest version. Run `history` first. A snapshot is a named frozen copy; time travel (`table:N`) is a read-only handle. You cannot revert past version 0 or past a version a snapshot still references.

## Apply

Start from `pxt init` then `pxt schema example --brief --out app.py`. Create the table with `pxt schema update`. Then use `history`, time travel, snapshots, and revert as above.

## Load the pixeltable skill

This is a thin catalog skill. Load the `pixeltable` skill for the application file, CLI, providers, serving, and anti-patterns. In this repo: [SKILL.md](../pixeltable-skill/SKILL.md). Install: `npx skills add pixeltable/pixeltable-skill`.
