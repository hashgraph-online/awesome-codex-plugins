---
name: deepdive
description: Full specialist analysis via parallel agent dispatch. Researcher, Architect, and PM produce a prioritized report of what to build next (30-60s).
---

# AgenTeam Deepdive

Run a full specialist analysis by dispatching three roles in parallel.
Unlike the standup skill (which reads state locally), deepdive launches
Codex subagents to investigate external signals, internal code health,
and strategic priorities. Expect 30-60 seconds for completion.

## Process

### 1. Auto-Init Guard

Check for `.agenteam/config.yaml`, `.agenteam.team/config.yaml`, or legacy
`agenteam.yaml` in the project root. If all are missing:
- Create config dir: `mkdir -p .agenteam`
- Copy the template: `cp <plugin-dir>/templates/agenteam.yaml.template .agenteam/config.yaml`
- Set the team name to the project directory name
- Generate agents: `python3 <runtime>/agenteam_rt.py generate`
- Tell the user: "AgenTeam auto-initialized with default roles. Edit `.agenteam/config.yaml` to customize."

### 2. Gather State with Dispatch Flag

Call the runtime with the `--dispatch` flag to get state and dispatch
plans for the three specialist roles:

```bash
python3 <runtime>/agenteam_rt.py standup --dispatch
```

Capture the JSON output. Expected fields (same as standup, plus
dispatch info):
- `health` -- `on-track`, `at-risk`, `off-track`, or `no-active-run`
- `run_id` -- current run identifier (may be null)
- `task` -- task description
- `stages` -- stage statuses
- `artifact_paths` -- map of role name to artifact directory
- `output_path` -- where to write the final report (e.g., `docs/meetings/<timestamp>-deepdive.md`)
- `dispatch` -- list of `{role, agent}` objects for the three specialist roles (researcher, architect, pm)

Create a durable checkpoint at `.agenteam/deepdive/<run_id>.json` before
dispatch. Record `max_elapsed_minutes` (default 60), `max_agents` (default 2
concurrent specialists), each role's attempt/thread ID, last heartbeat, output
artifact, and stop reason. On restart, validate completed artifacts and resume
only missing or interrupted roles; never repeat a completed specialist solely
because the controller restarted.

### 3. Dispatch Specialist Agents in Parallel

Launch three Codex subagents in parallel. Each role has a focused
mandate:

#### Researcher (`@Researcher`)

Agent file: `.codex/agents/researcher.toml`

Prompt the researcher with:
- Read all files in `docs/research/` and assess staleness (anything
  older than 2 weeks is potentially outdated)
- Search the web and GitHub for new trends, tools, and community
  discussions relevant to the project
- Check for competitor moves, new releases in the dependency ecosystem,
  and community feedback on similar tools
- Produce a structured report of external signals

Expected output format:
```
## External Signals

### Trends
- [signal] description and relevance to this project

### Ecosystem
- [dependency/tool] notable updates or risks

### Community
- [source] feedback, requests, or discussions relevant to our work
```

#### Architect (`@Architect`)

Agent file: `.codex/agents/architect.toml`

Prompt the architect with:
- Read all files in `docs/designs/` and compare against the current
  codebase -- identify design drift (where the implementation diverges
  from the documented design)
- Check for tech debt signals: duplicated logic, overly complex
  modules, missing error handling, dead code
- Review dependency health: outdated packages, known vulnerabilities,
  abandoned upstream projects
- Produce a structured report of internal health

Expected output format:
```
## Internal Health

### Design Drift
- [area] how implementation differs from design doc

### Tech Debt
- [area] description and severity (low/medium/high)

### Dependencies
- [package] status and risk level
```

#### PM (`@Pm`)

Agent file: `.codex/agents/pm.toml`

Prompt the PM with:
- Wait for and read the Researcher and Architect outputs (passed as
  context once they complete)
- Read `docs/strategies/` for current roadmap and strategic priorities
- Cross-reference external signals (Researcher) with internal health
  (Architect) and existing strategy
- Produce a prioritized list of recommendations for what to build next,
  with rationale for each item

Expected output format:
```
## Recommendations

1. **[title]** -- rationale based on research + architecture analysis
   Priority: [high/medium/low]
   Effort: [small/medium/large]

2. **[title]** -- rationale
   Priority: ...
   Effort: ...
```

**Dispatch order:** Researcher and Architect run in parallel. PM runs
after both complete (it needs their outputs as input).

### 4. Collect Outputs

Gather the outputs from all three subagents:
- Researcher report (external signals)
- Architect report (internal health)
- PM report (prioritized recommendations)

If any agent fails, include an error note in that section and continue
with the available outputs.

Update the checkpoint and emit a heartbeat whenever a specialist reports
progress. Enforce the elapsed and agent budgets. A timed-out specialist is
recorded as interrupted; if it has a resumable thread, resume it before
considering a fresh attempt. Synthesis is its own checkpoint and starts only
after the Researcher/Architect terminal states are durable.

### 5. Synthesize Deepdive Report

Combine all three outputs into a single report using this format:

```
# AgenTeam Deepdive: <project-name>
Date: <YYYY-MM-DD HH:MM>

## Health: [ON TRACK | AT RISK | OFF TRACK]

## External Signals (Researcher)
- trending approaches, competitor moves, community feedback

## Internal Health (Architect)
- design drift, tech debt, dependency risks

## Recommendations (PM)
- prioritized list of what to build next, with rationale

## Action Items
- specific next steps with owners
```

Rules for the report:
- **Health** is derived from the runtime JSON, same as the standup
  skill.
- **External Signals** comes directly from the Researcher output.
  Trim to the most actionable items (no more than 5-7 bullets).
- **Internal Health** comes from the Architect output. Group by
  severity, high-severity items first.
- **Recommendations** comes from the PM output. Keep prioritization
  and effort estimates. Limit to the top 5-7 items.
- **Action Items** is a synthesis step you perform: extract the most
  concrete next steps from all three reports, assign an owner (role
  name) to each, and list them in priority order.
- Omit any section where the corresponding agent produced no output
  (e.g., if the Researcher found nothing notable, omit External
  Signals).

### 6. Write Report

Write the synthesized report to the `output_path` from the runtime JSON
(typically `docs/meetings/<timestamp>-deepdive.md`):

```bash
mkdir -p "$(dirname "$output_path")"
```

Write the report content to that file.

### 7. Display to User

Show the full deepdive report to the user in the conversation. Include
a timing note:

```
AgenTeam Deepdive: <project-name>
Completed in ~<elapsed>s (3 specialists dispatched)
```

## Runtime Path Resolution

Resolve the AgenTeam runtime:
1. If running from the plugin directory: `./runtime/agenteam_rt.py`
2. If installed as a Codex plugin: `<plugin-install-path>/runtime/agenteam_rt.py`

## Error Handling

- If a subagent fails, include a note in the corresponding section:
  "[role] analysis unavailable -- [error reason]"
- If the runtime command fails, fall back to a best-effort report
  using direct file reads (same approach as the standup skill)
- Never let one agent's failure block the entire report

## Performance Target

Fast runs may finish in 30-60 seconds, but correctness does not depend on that
estimate. The durable `max_elapsed_minutes` budget and heartbeat/checkpoint
state govern long-running analysis. Researcher and Architect run in parallel;
PM starts after both terminal outputs are checkpointed.
