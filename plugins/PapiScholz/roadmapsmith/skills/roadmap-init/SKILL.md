---
name: roadmap-init
description: Initialize ROADMAP.md, AGENTS.md, and host integration files for a project using the RoadmapSmith CLI.
---

# RoadmapSmith Init

Use this skill when the user wants to set up governance files for a project — greenfield, brownfield (importing from existing files), or host-only setup.

## Required behavior

1. Determine the scenario and run `roadmapsmith init` with the appropriate flags:

   **Greenfield (new project):**
   ```
   roadmapsmith init --product-name "Name" --primary-user "User" --problem-statement "Problem" --project-root .
   ```

   **Brownfield (import existing tasks):**
   ```
   roadmapsmith init --import path/to/TODO.md --project-root .
   ```

   **Host-only setup (ROADMAP.md already exists):**
   ```
   roadmapsmith init --setup-only --hosts codex,claude --editor vscode --project-root .
   ```

2. Use `--dry-run` to preview what files will be created before writing.

3. Available init flags:
   - `--product-name <name>` — product or project name (appears in ROADMAP.md title)
   - `--primary-user <user>` — primary user persona
   - `--problem-statement <text>` — problem being solved
   - `--import <file>` — import tasks from an existing markdown file (repeatable)
   - `--hosts <codex,claude>` — host integrations to set up (default: `codex,claude`)
   - `--editor <name>` — editor for host file setup (default: `vscode`)
   - `--setup-only` — only write host integration files, skip ROADMAP.md creation
   - `--dry-run` — preview without writing
   - `--project-root <path>` — project root (default: cwd)

4. After a successful init, summarize which files were created or skipped.
