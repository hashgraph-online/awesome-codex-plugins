---
name: roadmap-update
description: Refresh ROADMAP.md with evidence-backed validation, add tasks, record evidence, or check northStar drift using the RoadmapSmith CLI.
---

# RoadmapSmith Update

Use this skill when the user wants to sync the roadmap after code changes, add a new task, mark a task complete with evidence, or check if the project has drifted from its northStar.

## Required behavior

Choose the mode that matches the user's intent:

**Default refresh** (re-validate all tasks against current repo evidence):
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

**Refresh and show validation audit:**
```
roadmapsmith update --audit --project-root .
```

Available update flags:
- `--add-task <text>` — insert a new task into the managed block
- `--task <id>` — task ID to target (use with `--evidence`)
- `--evidence <text>` — evidence to attach to `--task`
- `--audit` — show validation audit after refresh
- `--check-drift` — compare northStar to repo state
- `--strict` — strict validation mode (preservedCheckedState does not count as pass)
- `--dry-run` — preview without writing
- `--json` — output in JSON format
- `--project-root <path>` — project root (default: cwd)

Always use `--dry-run` first when uncertain about the impact.
