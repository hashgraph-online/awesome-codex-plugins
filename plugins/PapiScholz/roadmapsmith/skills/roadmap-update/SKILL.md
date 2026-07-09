---
name: roadmap-update
description: Refresh ROADMAP.md with evidence-backed validation, add tasks, record evidence, or check northStar drift using the RoadmapSmith CLI.
---

# RoadmapSmith Update

Use this skill when the user wants to sync the roadmap after code changes, add a new task, mark a task complete with evidence, or check if the project has drifted from its northStar.

## Safety

`roadmapsmith update` mutates ROADMAP.md in both directions:

- unchecks `[x]` tasks whose evidence cannot be found in the repo
- auto-checks `[ ]` tasks whose evidence IS found

Neither direction requires confirmation. Always preview with `--audit --dry-run` first, review both the "Unchecked by this run" and the "Ready but unchecked" lists, and only apply after confirming both are correct. If you want the ⚠️ / ✅ sub-bullets written to the file WITHOUT flipping any checkbox, add `--evidence-only`.

## Required behavior

**Step 1 — Preview (do this first):**
```
roadmapsmith update --audit --dry-run --project-root .
```
Review the diff. Confirm no legitimate `[x]` will be silently unchecked and no `[ ]` will be auto-checked without visible evidence.

**Step 2 — Apply (only after reviewing the preview):**
```
roadmapsmith update --project-root .
```

**Add a new task:**
```
roadmapsmith update --add-task "Task description" --project-root .
```

**Record evidence for a specific task:**
```
roadmapsmith update --task TASK-ID --evidence "path/to/file.js passes tests" --project-root .
```

**Check northStar drift** (requires `product.northStar` in `roadmap-skill.config.json`):
```
roadmapsmith update --check-drift --project-root .
```

Available update flags:
- `--add-task <text>` — insert a new task into the managed block
- `--task <id>` — task ID to target (use with `--evidence`)
- `--evidence <text>` — evidence to attach to `--task`
- `--audit` — show validation audit after refresh (grouped by cause: `path-mismatch`, `no-evidence`, `deletion-task`, `namespace-gate`, `strict-mode`)
- `--evidence-only` — write ⚠️/✅ sub-bullets but never flip `[ ]`/`[x]` (safe review pass)
- `--check-drift` — compare northStar to repo state
- `--strict` — strict validation mode (preservedCheckedState does not count as pass)
- `--dry-run` — preview without writing
- `--json` — output in JSON format
- `--project-root <path>` — project root (default: cwd)

## Known limitations

- **Path resolution assumes paths in task text are relative to the repo root.** Monorepos can now add a `pathAliases` object to `roadmap-skill.config.json` (e.g. `{ "/dashboard/": "apps/web/src/app/dashboard/" }`). Without it, task text needs the full prefix. Symptoms: legitimate `[x]` tasks unchecked with `missing referenced file(s): ...` on paths that DO exist under a subdirectory.
- **Deletion tasks are recognized by keyword.** A task whose text contains `eliminado`/`eliminada`/`borrado`/`borrada`/`deleted`/`removed`/`dropped` AND names an explicit path is validated as an absence assertion: it passes when the file is absent, fails with `expected file removed, still present at <path>` if it still exists. Phrase deletion tasks accordingly, or fall back to `~~strikethrough~~` for manual attestation.
- **Duplicate explicit Task IDs are surfaced as warnings.** If the same `<!-- rs:task=id -->` appears in two sections (e.g. plan + archive), `roadmapsmith update` prints a `⚠️  Duplicate explicit task id "<id>"` warning naming both line numbers. Sync still treats them as independent — merge or rename one.
- **`[ ] → [x]` auto-checks emit a `✅ evidence:` sub-bullet** naming the matched file or symbol. If the sub-bullet is missing or looks weak, verify by hand — the tool can auto-check on shallow token overlap.

## Before running this skill in a new repo

- [ ] Are task descriptions using paths relative to the repo root? For monorepos, add a `pathAliases` object in `roadmap-skill.config.json` mapping the prefix used in task text (e.g. `/dashboard/`) to the real subdirectory (`apps/web/src/app/dashboard/`).
- [ ] Does the roadmap duplicate explicit task IDs across sections? The tool will warn but not merge — decide whether to consolidate or rename.
- [ ] Are there tasks phrased as deletions (`"X eliminado"`, `"X removed"`, `"borrado"`)? Confirm the file path is quoted with backticks so the deletion pass can extract it.

Always use `--dry-run` first when uncertain about the impact.
