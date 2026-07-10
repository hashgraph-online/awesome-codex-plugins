---
name: team
description: "Org-level agent team designer via `epic team` CLI (cross-project, append-merge). Subcommands: list, show, sync, link, unlink, history. Use when setting up agents, designing teams, or /spec yields 3+ requirements."
---

# /team — Agent Team Design

This skill is a thin wrapper around the `epic team` CLI.

**Run in terminal:**
```
epic team
```

`epic team` handles the full interactive flow:
- Resolves org (`HARNESS_ORG` env → prompt → default `"epic"`)
- Scans the project (tech stack, domain boundaries, key modules)
- Recommends team type and agent composition
- Shows diff if team already exists in `~/.harness/orgs/`
- Applies merge strategy (no silent overwrites)
- Copies agents to `.claude/agents/{team}/` with `## Team Context` injected

For the full spec see `docs/research/team-spec.md`.

## Other subcommands

```
epic team list                     # list teams in current org
epic team show {team}              # config + agents + mission
epic team show {team} --playbook   # full accumulated playbook
epic team sync {team}              # re-copy agents to .claude/agents/
epic team link {team}              # attach existing team (skip design)
epic team unlink {team}            # remove .claude/agents/{team}/
epic team history {team} {agent}   # show .history/ entries
```
