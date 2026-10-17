---
name: init
description: 'Set up docflow in a repo with no docs yet: scaffold the docs tree, write docflow.json, add agent guidance. Use when asked to "set up docflow", "initialize docs", "scaffold docs", or "make this repo use docflow".'
---

# init

Goal: initialize docflow only when doctor says this repo has no meaningful docs yet. Keep existing user-authored files; generated maintenance files may be refreshed.

## Steps

1. Run doctor first.

```bash
bash scripts/docflow-doctor.sh --target <REPO ROOT>
```

2. Route by recommendation.
   - `docflow-init`: continue.
   - `docflow-adopt`: stop and run `/docflow:adopt` instead (preserves existing docs).
   - `docflow-repair`: stop and run `/docflow:repair` instead.

3. Pick docs root.
   - Use `docs/` unless the user explicitly chooses another root.

4. Pick project name.
   - Prefer repo folder name.
   - If root `README.md` has clear project title, use that.

5. Run scaffold from plugin root (idempotent; skips existing user content, refreshes generated files):

```bash
bash scripts/scaffold.sh --docs-root <DOCS_ROOT> --project "<PROJECT NAME>" --target "<REPO ROOT>"
```

This creates the category tree, drops templates, writes `docflow.json`, and scaffolds `AGENTS.md` + `GEMINI.md` + `.cursorrules`.

6. Add root README link if missing:
   - `## Documentation`
   - link to `<DOCS_ROOT>/README.md`

7. Seed the first changelog. Create `<DOCS_ROOT>/changelog/(mmm-yy).md` for the current month from the template, summarizing recent history (`git log --no-merges --pretty='%h %ad %s' --date=short -20`). Use the `changelog` skill for the format.

8. Regenerate the map and validate:
   ```bash
   bash scripts/docflow-map.sh "<REPO ROOT>/<DOCS_ROOT>"
   bash scripts/docflow-validate.sh --target "<REPO ROOT>"
   ```
   Fresh template placeholders are warnings; validation errors are blockers.

9. Report what was created (docs root, `docflow.json`, `AGENTS.md`, `GEMINI.md`, `.cursorrules`, validation status) and point the user at `/docflow:author` (writing), `/docflow:router` (reading), `/docflow:validate` (readiness), `/docflow:repair` (maintenance).

## Rules

- Never overwrite existing user-authored docs files.
- If docs already exist, prefer `/docflow:adopt` over `/docflow:init`.
- Keep `AGENTS.md` and `docflow.json` aligned on docs root.
- Follow the naming rules in `<DOCS_ROOT>/NAMING.md` for every file you create after.
