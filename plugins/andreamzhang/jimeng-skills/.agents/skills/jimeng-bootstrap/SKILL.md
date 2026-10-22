---
name: jimeng-bootstrap
description: Use when the user says "用 jimeng-bootstrap 初始化项目", "初始化即梦分镜师", "把当前项目装成即梦分镜师", or asks to bootstrap the plugin workflow. It installs the producer rules and prepares a short-drama project in the current workspace.
---

# Jimeng Bootstrap

Make the plugin useful in the user's current project, without changing unrelated files.

Make the plugin useful in the user's current project, without changing unrelated files.

Steps:

1. Determine the current project root:
   - Use the root that contains `AGENTS.md`, `.codex/`, or `scripts/`.
   - If none of these exist, treat the current working directory as a new project root.

2. If `AGENTS.md` is missing, add it from the installed plugin:
   - Read `${SKILL_DIR}/../../AGENTS.md`.
   - Write the same content to `<project-root>/AGENTS.md`.

3. If `.codex/agents/`, `.agents/skills/`, or `tools/` are missing:
   - Do **not** create a fake one.
   - Tell the user to use the plugin repository root, or clone `https://github.com/andreamzhang/jimeng-skills.git` into the project root.

4. If creating a new drama, run:
   `tools\py.cmd tools\new_drama_memory.py "<剧名>" --dirs`

5. Do not add extra rules to this skill. This is only a bootstrap helper.
