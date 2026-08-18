---
name: generate
description: Regenerate .codex/agents/*.toml from agenteam.yaml and plugin defaults.
---

# AgenTeam Generate

Regenerate Codex-native agent files from the current configuration.

## When to Use

- After editing `agenteam.yaml` manually
- After adding or removing roles
- After updating the plugin (new default role templates)
- To verify generated agents match the config

## Process

### 1. Validate Config

```bash
python3 <runtime>/agenteam_rt.py roles list
```

If this fails, the config has errors — show them and stop.

Role models should normally inherit the platform default. For any explicit pin,
compare it with `codex debug models`; warn about unavailable or deprecated
entries without rejecting values solely because a static AgenTeam list is old.

### 2. Generate Agents

```bash
python3 <runtime>/agenteam_rt.py generate
```

### 3. Report Results

Show what was generated:

```
Generated agents:
  .codex/agents/architect.toml      (updated)
  .codex/agents/dev.toml    (updated)
  .codex/agents/reviewer.toml       (updated)
  .codex/agents/qa.toml    (updated)
```

If custom roles were included, highlight them:
```
  .codex/agents/security_auditor.toml  (custom role)
```

### 4. Verify

Optionally show a summary of each generated agent's key fields
(name, model, can_write, participates_in) for user verification.
Display an omitted model as `platform default`, not as a missing setting.

If the user regenerated agents because roles are missing from the `@` picker,
tell them to confirm the files now exist under `.codex/agents/` in the current
project, then open a new thread or restart Codex so it reloads workspace agents.
