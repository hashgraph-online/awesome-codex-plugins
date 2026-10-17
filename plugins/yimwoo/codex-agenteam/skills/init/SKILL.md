---
name: init
description: Initialize team config for a project. Creates .agenteam/config.yaml (or legacy agenteam.yaml) and generates .codex/agents/*.toml.
---

# AgenTeam Init

Set up AgenTeam for the current project.

## Process

### 1. Check Prerequisites

Resolve the runtime path first, then use the runtime entrypoint itself as the
readiness check. Do not spend time on separate environment probes if the runtime
can tell you what is missing.

Fast path:
```bash
python3 <plugin-dir>/runtime/agenteam_rt.py --help
```

If Python or dependencies are missing, the runtime prints a JSON error. Only then
offer the minimal install fix:
```bash
pip install pyyaml toml
```

### 2. Check for Existing Config

Check for config in this order:
1. `.agenteam/config.yaml` (personal)
2. `.agenteam.team/config.yaml` (team shared)
3. Legacy `agenteam.yaml`

- **If `.agenteam.team/config.yaml` exists (team project):** Use it as the
  team config. Do not create `.agenteam/config.yaml` — personal overrides
  are opt-in. Skip to step 4 (validate).
- **If `.agenteam/config.yaml` or `agenteam.yaml` exists:** Ask the user if
  they want to reconfigure or keep existing config. If keeping, skip to step 4.
- **If absent:** Continue to step 3.

### 3. Create Config

Copy the template:

```bash
mkdir -p .agenteam
cp <plugin-dir>/templates/agenteam.yaml.template .agenteam/config.yaml
```

Default to a fast setup unless the user explicitly asks to customize:

- Team name: use the project directory name
- Pipeline mode: keep the template default unless the user asked for HOTL or dispatch-only
- Write scopes: keep defaults unless the repo clearly needs different paths
- Models: inherit the Codex platform default. Do not add role pins during
  setup unless the user asks and the live Codex model catalog confirms them.
- Custom roles: do not ask up front; mention they can be added later with `$ateam:add-member`

Only ask follow-up questions when a decision is genuinely ambiguous or the user
asked for a tailored team. Do not turn basic setup into a multi-question interview.

### 4. Validate Config

```bash
python3 <plugin-dir>/runtime/agenteam_rt.py validate
```

If validation fails, show the error and help the user fix it.

### 5. Generate Agents

```bash
python3 <plugin-dir>/runtime/agenteam_rt.py generate
```

This creates `.codex/agents/*.toml` for each role. Show the user what was generated.
If the new roles do not appear in the `@` picker immediately, tell the user to:
- Confirm the generated files exist under `.codex/agents/` in the current project
- Open a new thread or restart Codex so it reloads workspace agents from that folder

### 6. HOTL Detection

Only do this if it changes the recommendation you will give the user. Skip it for
simple setup if the team is already ready to use.

```bash
python3 <plugin-dir>/runtime/agenteam_rt.py hotl check
```

If HOTL is available and pipeline is not already set to `hotl`:
- Inform the user: "HOTL plugin detected. You can set `pipeline: hotl` in
  .agenteam/config.yaml (or legacy agenteam.yaml) to integrate with HOTL workflows."
- Do not change the config automatically.

### 7. Summary

Show:
- Config file location
- Generated agent files
- Team roster (same format as using-ateam skill)
- Starter examples based on project type:

**Detection:** Glob for common source files (`*.py`, `*.js`, `*.ts`,
`*.go`, `*.java`, `*.rs`, `*.rb`, `*.swift`, `*.kt`). If any exist,
use "existing project" examples. Otherwise use "new project" examples.

**For existing projects** (source files detected):

```
Try these to get started:

  @Reviewer review this codebase for security concerns
  @Researcher what are the best practices for error handling in this stack?
  @ATeam add comprehensive test coverage
  @ATeam add a security auditor that focuses on OWASP top 10
```

**For new/empty projects** (no source files):

```
Try these to get started:

  @Architect design a REST API for a task management app
  @Researcher what's the best tech stack for a CLI tool in Python?
  @ATeam build a simple todo app with tests
  @ATeam add a docs writer to maintain README and API docs
```

**Team config suggestion (when no `.agenteam.team/config.yaml` was detected):**

After the starter examples, if the config was created locally (no team
config exists), append:

```
Your AgenTeam config is local. To share team settings with
collaborators, run @ATeam share-config.
```

Do not show this if `.agenteam.team/config.yaml` already exists.

After the roster/examples, add this note when setup created or refreshed local
agents:

```
If the new roles do not show up in the `@` picker right away, first confirm this
project now has `.codex/agents/*.toml` files, then open a new thread or restart
Codex to reload workspace agents from `.codex/agents/`.
```

## Runtime Path Resolution

Resolve the AgenTeam runtime:
1. If running from the plugin directory: `./runtime/agenteam_rt.py`
2. If installed as a Codex plugin cache entry: `<plugin-install-path>/local/runtime/agenteam_rt.py`

Resolve a versioned cache entry by locating its actual
`runtime/agenteam_rt.py` file and validating the sibling `templates/` directory;
never stop at the unversioned `.../ateam` parent.

## Performance Guardrails

- Prefer the shortest successful path: create config, validate, generate, show roster.
- Avoid unrelated repo exploration during first-time setup.
- Do not create a dummy run just to validate config.
- A normal first-time setup should usually take a few seconds, not minutes.
