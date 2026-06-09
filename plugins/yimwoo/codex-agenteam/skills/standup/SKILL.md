---
name: standup
description: Quick project status report synthesized from state files, artifacts, and git activity. No agent dispatch (<2s).
---

# AgenTeam Standup

Produce a fast, Linear-style project status report by reading the current
run state, role artifacts, and git activity. This skill does **not**
dispatch subagents -- the lead agent reads everything directly and
synthesizes.

## Process

### 1. Auto-Init Guard

Check for `.agenteam/config.yaml` (or legacy `agenteam.yaml`) in the project root. If missing:
- Create config dir: `mkdir -p .agenteam`
- Copy the template: `cp <plugin-dir>/templates/agenteam.yaml.template .agenteam/config.yaml`
- Set the team name to the project directory name
- Generate agents: `python3 <runtime>/agenteam_rt.py generate`
- Tell the user: "AgenTeam auto-initialized with default roles. Edit `.agenteam/config.yaml` to customize."

### 2. Gather State

Call the runtime to assemble run state, health indicator, and artifact
paths:

```bash
python3 <runtime>/agenteam_rt.py standup
```

Capture the JSON output. Expected fields:
- `health` -- `on-track`, `at-risk`, `off-track`, or `no-active-run`
- `run_id` -- current run identifier (may be null if no active run)
- `task` -- task description
- `stages` -- list of stages with status, assigned role, and gate state
- `artifact_paths` -- map of role name to artifact directory
- `governance.adoption` -- optional summary of decisions, escalations,
  tripwire checks, gate rejections, and criteria overrides
- `output_path` -- where to write the final report (e.g., `docs/meetings/<timestamp>-standup.md`)

### 3. Read Role Artifacts

For each role in `artifact_paths`, check what exists in that directory
and produce a one-line summary:

| Role | Artifact Directory | Look For |
|------|--------------------|----------|
| researcher | `docs/research/` | Research reports, dated findings |
| pm | `docs/strategies/` | Strategy docs, roadmaps, specs |
| architect | `docs/designs/` | Design docs, architecture decisions |
| dev | `src/**`, `docs/plans/` | Source files changed, plan docs |
| qa | `tests/**` | Test files, coverage reports |
| reviewer | (read-only) | Review comments in state files |

For each role with artifacts:
- List the most recent files (by modification time)
- Summarize in one line: what was produced or changed

If no active run exists, scan artifacts and git history to build
a best-effort summary of recent team activity.

### 4. Check Git Activity

Briefly inspect recent git state:

```bash
git log --oneline -10
git branch --list
git status --short
```

Summarize at the changeset level:
- Recent commits (group by area, not raw list)
- Active branches relevant to team work
- Uncommitted changes (if any)

Do **not** include raw commit hashes or full diffs. Report outcomes,
not activity.

### 5. Synthesize Report

Produce a Linear-style status report using this format:

```
Health: [ON TRACK | AT RISK | OFF TRACK]

## Completed
- [role] one-line summary of what's done

## In Progress
- [role] what's happening now

## Blocked
- [role] problem + next step + owner

## Decisions
- key decisions made (from design docs if available)

## Next
- what happens when current work completes
```

Rules for the report:
- **Health indicator** comes first. Derive from the runtime JSON `health`
  field. If stages are blocked or gates rejected, it is `AT RISK` or
  `OFF TRACK`.
- **Completed** lists roles whose stages are done, with a one-line
  summary of their artifact output.
- **In Progress** lists roles with active stages, describing current
  work.
- **Blocked** lists any role that is stuck. Every blocker must include
  three parts: the problem, the proposed next step, and the owner
  responsible for unblocking.
- **Decisions** captures key architectural or strategic decisions found
  in `governance.adoption`, design docs, or strategy files. Include open
  follow-ups, escalations, tripwire blocks, gate rejections, and criteria
  overrides when the runtime JSON reports them. Omit this section if none are
  found.
- **Next** describes what happens once current in-progress work
  completes (the next stage in the pipeline, or follow-up actions).
- Omit any section that would be empty.

### 6. Write Report

Write the synthesized report to the `output_path` from the runtime JSON
(typically `docs/meetings/<timestamp>-standup.md`):

```bash
mkdir -p "$(dirname "$output_path")"
```

Write the report content to that file.

### 7. Display to User

Show the full report to the user in the conversation. If there is an
active run, include the run context header:

```
AgenTeam Standup: <team-name>
Run: <run-id> | Task: <short task description>
```

If no active run, use:

```
AgenTeam Standup: <team-name>
(No active run -- summarizing recent activity)
```

## Runtime Path Resolution

Resolve the AgenTeam runtime:
1. If running from the plugin directory: `./runtime/agenteam_rt.py`
2. If installed as a Codex plugin: `<plugin-install-path>/runtime/agenteam_rt.py`

## Performance Target

This skill should complete in under 2 seconds. It reads local files
and runs lightweight git commands -- no LLM subagent calls, no network
requests, no web searches.
