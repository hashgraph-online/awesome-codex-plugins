---
name: agent-repo-init
description: One-click initialization of a multi-agent repository from the Antigravity template. Use this skill when users want to scaffold a new project quickly (`quick` mode) or with runtime defaults (`full` mode) including MCP toggle, swarm preference context, sandbox type, and optional git init. LLM configuration is handled later by ag-setup.
---

# Agent Repo Init

Initialize a new project from this repository template with two modes.

## Modes
- `quick`: Fast scaffold with clean copy and minimal setup.
- `full`: `quick` plus runtime profile setup (`.env`, mission, context profile, init report) and optional `git init`.

## Run via Script
Use the portable script in this skill directory:

```bash
python skills/agent-repo-init/scripts/init_project.py \
  --project-name my-agent \
  --destination-root /absolute/path \
  --mode quick
```

Full mode example:

```bash
python skills/agent-repo-init/scripts/init_project.py \
  --project-name my-agent \
  --destination-root /absolute/path \
  --mode full \
  --enable-mcp \
  --disable-swarm \
  --sandbox-runtime microsandbox \
  --init-git
```

## Expected Output
- New project at `<destination_root>/<project_name>`
- Clean copy without local runtime state
- Initialization report at `artifacts/logs/agent_repo_init_report.md`
- Script is self-contained and does not import project `src/` modules

## Notes
- Keep destination outside the current template repository.
- For `full` mode, review `.context/agent_runtime_profile.md` after generation.
- Run `/ag-setup` in the generated project to choose and write the LLM endpoint.
