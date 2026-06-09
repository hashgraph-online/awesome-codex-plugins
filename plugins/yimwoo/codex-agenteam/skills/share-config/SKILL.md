---
name: share-config
description: Promote local config to a shared team config that can be committed to git.
---

# AgenTeam Share Config

Create a shared team config from your local config so collaborators
can use the same pipeline, roles, and settings.

## Process

### 1. Check Prerequisites

Verify `.agenteam/config.yaml` (or legacy `agenteam.yaml`) exists.
If not, tell the user: "No local config found. Run `@ATeam init` first."

### 2. Check for Existing Team Config

If `.agenteam.team/config.yaml` already exists:
- Tell the user: "Team config already exists at `.agenteam.team/config.yaml`.
  Edit it directly to change team settings."
- Stop. Do not overwrite.

### 3. Load and Strip Personal Fields

Load the current config. Strip ALL personal-allowlist fields from
every role:

- `model` (personal preference)
- `reasoning_effort` (personal preference)
- `system_instructions` (may contain personal addenda)
- `nickname_candidates` (personal display preference)
- `mcp_servers` (local/private tool wiring)
- `skills_config` (local/private skill wiring)

These fields are stripped because they should not become team policy.
The user can review and re-add team-relevant instructions manually.

### 4. Normalize Version

If `version` is not `"2"`, set it to `"2"`.

### 5. Write Team Config

```bash
mkdir -p .agenteam.team
```

Write the stripped config to `.agenteam.team/config.yaml`.

### 6. Summary

Print:

```
Team config created at .agenteam.team/config.yaml

What was stripped (personal-only fields):
  - roles.*.model
  - roles.*.reasoning_effort
  - roles.*.system_instructions
  - roles.*.nickname_candidates
  - roles.*.mcp_servers
  - roles.*.skills_config

Review it before committing. To customize:
  - Team settings: edit .agenteam.team/config.yaml (tracked in git)
  - Personal overrides: create .agenteam/config.yaml (gitignored)

Next steps:
  git add .agenteam.team/
  git commit -m "Add shared AgenTeam team config"
```

## Notes

- The team config becomes the source of truth for pipeline, stages,
  gates, roles, and isolation.
- Personal overrides in `.agenteam/config.yaml` can only change
  `model`, `reasoning_effort`, `system_instructions` (append),
  `nickname_candidates`, `mcp_servers`, and `skills_config`.
- The team can widen personal overrides with `allow_personal_override`
  in the team config.
