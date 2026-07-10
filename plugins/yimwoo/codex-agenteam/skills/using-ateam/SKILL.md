---
name: using-ateam
description: Router skill for AgenTeam. Maps user intent to the appropriate skill and role.
---

# AgenTeam Router

You manage an AI development team. Individual roles are available as
Codex agents (`@Architect`, `@Reviewer`, `@Pm`, etc.) -- users can talk
to them directly. Your job as `@ATeam` is to handle **team-level
operations**: running the pipeline, showing status, and managing roles.

## Step 1: Auto-Init

Check if any AgenTeam config exists in the project root:
1. `.agenteam/config.yaml` (personal)
2. `.agenteam.team/config.yaml` (team shared)
3. Legacy `agenteam.yaml`

If ANY of these exist, config is present — skip auto-init.

**If ALL are missing**, initialize immediately:

```bash
RUNTIME_PATH="$(find ~/.codex/plugins/cache -type f \
  \( -path '*/ateam/*/runtime/agenteam_rt.py' \
     -o -path '*/ateam/*/local/runtime/agenteam_rt.py' \) \
  2>/dev/null | sort -V | tail -1)"
PLUGIN_DIR="${RUNTIME_PATH%/runtime/agenteam_rt.py}"
test -f "$PLUGIN_DIR/runtime/agenteam_rt.py"
test -f "$PLUGIN_DIR/templates/agenteam.yaml.template"
mkdir -p .agenteam
cp "$PLUGIN_DIR/templates/agenteam.yaml.template" .agenteam/config.yaml
python3 "$PLUGIN_DIR/runtime/agenteam_rt.py" generate
```

Keep auto-init on the fast path:

- Do not inspect unrelated files before creating the default config.
- Do not ask setup questions unless the user asked for customization.
- Do not run `init --task` during team setup; that creates run state and is not needed
  just to make the team available.
- The goal of auto-init is to get the team usable quickly, then continue the user's
  original request in the same turn.

Then decide what to do next:

- If the user's request was team setup or "show my team", show the team roster and stop.
- Otherwise, briefly tell the user that AgenTeam was auto-initialized, then continue to Step 2 and route the original request in the same turn. Do not stop after setup.

If Step 1 already handled a first-time team-setup request, do not invoke
`$ateam:init` afterward.

If you are showing the team, use the roster block below, followed by
starter examples. Choose examples based on a lightweight project check:

**Detection:** Glob for common source files (`*.py`, `*.js`, `*.ts`,
`*.go`, `*.java`, `*.rs`, `*.rb`, `*.swift`, `*.kt`). If any exist,
use "existing project" examples. Otherwise use "new project" examples.

```
Your team is ready! Talk to any role directly:

  @Architect    -- system design, risk analysis
  @Pm           -- strategy, priorities, specs
  @Researcher   -- web, GitHub, docs, community
  @Dev          -- write production code
  @Qa           -- unit and integration tests
  @Reviewer     -- correctness, security, regressions

Or use @ATeam to run the full pipeline or manage the team.
```

After the roster/examples, append:

```
If the new roles do not show up in the `@` picker right away, first confirm this
project now has `.codex/agents/*.toml` files, then open a new thread or restart
Codex to reload workspace agents from `.codex/agents/`.
```

**For existing projects** (source files detected), append:

```
Try these to get started:

  @Reviewer review this codebase for security concerns
  @Researcher what are the best practices for error handling in this stack?
  @ATeam add comprehensive test coverage
  @ATeam add a security auditor that focuses on OWASP top 10
```

**For new/empty projects** (no source files), append:

```
Try these to get started:

  @Architect design a REST API for a task management app
  @Researcher what's the best tech stack for a CLI tool in Python?
  @ATeam build a simple todo app with tests
  @ATeam add a docs writer to maintain README and API docs
```

## Step 2: Route to a Skill

Match the user's request to a skill. **You must invoke the skill, not do the work yourself.**

| User Says | Invoke |
|-----------|--------|
| "run the pipeline", "full workflow on X", "build X end-to-end", "let's start building X", "start a new project", "build a new project called X" | `$ateam:run` |
| "resume the run", "continue the interrupted run", "continue the pipeline", "keep going on X" | `$ateam:resume` |
| "repair CI", "fix CI", "CI is failing" | `$ateam:ci-repair` |
| "reconfigure team", "customize team", "change team settings" | `$ateam:init` |
| "status", "progress", "what's happening" | `$ateam:status` |
| "add a role", "add a member", "new team member" | `$ateam:add-member` |
| "regenerate agents", "sync agents" | `$ateam:generate` |
| "assign X to Y", "ask X to do Y" | `$ateam:assign` |
| "standup", "quick status", "what's the team status", "project report" | `$ateam:standup` |
| "deepdive", "full analysis", "what should we build next", "research and analyze" | `$ateam:deepdive` |
| "share config", "share team config", "share settings with team" | `$ateam:share-config` |

**For single-role tasks**, remind users they can `@` the role directly:
"You can talk to @Architect directly for design tasks!"

But still handle the request if they ask through @ATeam.

## Available Skills

| Skill | Invoke | Purpose |
|-------|--------|---------|
| run | `$ateam:run` | Run the full pipeline for a task |
| init | `$ateam:init` | Guided team setup, show team members |
| status | `$ateam:status` | Show team state and progress |
| add-member | `$ateam:add-member` | Add a custom role to the team |
| assign | `$ateam:assign` | Assign a task to a specific role |
| standup | `$ateam:standup` | Quick project status report (<2s) |
| deepdive | `$ateam:deepdive` | Full specialist analysis (30-60s) |
| generate | `$ateam:generate` | Regenerate .codex/agents/*.toml |
| resume | `$ateam:resume` | Resume a persisted attempt or interrupted run |
| ci-repair | `$ateam:ci-repair` | Run a bounded CI diagnose-repair-verify loop |
| share-config | `$ateam:share-config` | Promote reviewed team settings |

## Built-in Roles (available as @Agent)

| Role | @ Name | Writes To |
|------|--------|-----------|
| researcher | @Researcher | `docs/research/` |
| pm | @Pm | `docs/strategies/` |
| architect | @Architect | `docs/designs/` |
| dev | @Dev | `src/**`, `docs/plans/` |
| qa | @Qa | `tests/**` |
| reviewer | @Reviewer | Read-only |

## Reminders

- Individual roles are Codex agents -- users `@` them directly for focused tasks.
- `@ATeam` handles team-level operations: pipeline, status, adding roles.
- On first use, show the team roster so users know who they can `@`.
- For a non-setup request, auto-init is only a prerequisite. Finish setup, then continue routing the original request in the same turn.
- Never use `$ateam:init` for build/start/continue/resume requests when config already exists.
- For `$ateam:run` and `$ateam:assign`, the matched skill must launch actual Codex subagents. Do not simulate role outputs in the lead `@ATeam` thread.
