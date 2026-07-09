---
name: adopt
description: 'Add docflow to a repo that already has docs, without rewriting them. Adds missing config, folders, helpers, agent guidance, and an adoption review. Use when docs already exist or doctor recommends adopt.'
---

# adopt

Goal: preserve existing docs, add missing docflow infrastructure.

## Steps

1. Run doctor:
   ```bash
   bash scripts/docflow-doctor.sh --target <REPO ROOT>
   ```

2. Choose docs root:
   - Use detected docs root if present.
   - Else use `docs`.

3. Choose project name:
   - Prefer README H1.
   - Else repo folder name.

4. Run adopt:
   ```bash
   bash scripts/docflow-adopt.sh --target <REPO ROOT> --docs-root <DOCS_ROOT> --project "<PROJECT NAME>"
   ```

5. Report created/skipped files and point at the adoption review doc.

## Rules

- Never move/delete/rewrite existing docs.
- Existing root guidance files are preserved.
- Run `/docflow:repair` after manual cleanup.
