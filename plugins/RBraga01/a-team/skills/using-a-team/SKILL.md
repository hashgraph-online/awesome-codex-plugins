---
name: using-a-team
description: The meta-skill. Loaded at every session start. Defines which A Team skills and agents MUST be used for which situations. If a skill or agent applies, you do not have a choice — you must use it.
---

# Using A Team

This skill is injected at every session start. It defines mandatory skill and agent usage.

<HARD-GATE>
IF A SKILL OR AGENT IN THIS DOCUMENT APPLIES TO YOUR CURRENT TASK,
YOU DO NOT HAVE A CHOICE. YOU MUST USE IT.
Skipping a mandatory skill to save time is not allowed.
</HARD-GATE>

## Before ANY Code Is Written

| Situation | Required Skill/Agent |
|-----------|---------------------|
| New feature, component, or capability | **brainstorming** skill first |
| Have a spec, need an implementation plan | **writing-plans** skill |
| Have a plan, executing it | **subagent-driven-development** or **executing-plans** skill |
| Starting development work | **using-git-worktrees** skill (create isolation first) |

## During Development

| Situation | Required Skill/Agent |
|-----------|---------------------|
| Writing any new function or feature | **test-driven-development** skill (RED before GREEN) |
| Any bug, test failure, unexpected behavior | **debugger** agent (systematic debugging — Phase 1 first) |
| Multiple independent problems | **dispatching-parallel-agents** skill |
| Build or type errors | **build-error-resolver** agent (minimal diffs only) |

## Before Claiming Completion

| Claim | Required Skill |
|-------|---------------|
| "The tests pass" | **verification-before-completion** (run tests, read output) |
| "The build succeeds" | **verification-before-completion** (run build, read output) |
| "The bug is fixed" | **verification-before-completion** (reproduce fix, read output) |
| "The feature works" | **verification-before-completion** (run the feature, read output) |
| "Done" / "Complete" | **verification-before-completion** (ALWAYS, no exceptions) |

After verification passes, Step 5 of `verification-before-completion` is mandatory: delete all log files, stack traces, and debug dumps generated during this task before reporting done.

## After Code Changes

| Situation | Required Agent |
|-----------|---------------|
| After writing or modifying code | **code-reviewer** agent |
| Auth, API, input handling, DB changes | **security-reviewer** agent |
| Before any PR merge | **quality-gate** command (runs both) |
| Wrapping up a branch | **finishing-a-development-branch** skill |

## Architectural Decisions

| Situation | Required Agent |
|-----------|---------------|
| System design, new feature architecture | **architect** agent (produces ADR) |
| Complex feature planning | **planner** agent |
| Tech stack or pattern decision | **architect** agent |
| Inherited/unfamiliar codebase, scaling milestone, or periodic health check | **architecture-audit** skill |

## Language & Domain Reviews

| Situation | Required Agent |
|-----------|---------------|
| Go files changed | **go-reviewer** |
| Python files changed | **python-reviewer** |
| Rust files changed | **rust-reviewer** |
| Kotlin / Android files changed | **kotlin-reviewer** |
| Swift / iOS files changed | **swift-reviewer** |
| Dart / Flutter files changed | **flutter-reviewer** |
| SQL / migrations / schema changed | **database-reviewer** |
| Terraform / Docker / K8s / CI changed | **infra-reviewer** |
| Any LLM API calls added or changed | **ai-reviewer** |
| Any privacy / payment / child data code | **compliance-reviewer** |

## Before Any API Endpoint

| Situation | Required Skill |
|-----------|---------------|
| Writing a new REST / gRPC / GraphQL / event endpoint | **api-contract-first** (write the contract first) |
| Any `ALTER TABLE`, `DROP`, or backfill in production | **data-migration** (rollback plan first) |

## Performance & Production

| Situation | Required |
|-----------|---------|
| Performance regression reported | **performance-profiler** agent (measure first) |
| Performance-critical feature pre-release | **performance-audit** skill |
| Production is degraded or down | **incident-response** skill (immediately) |

## During Code Changes — Surgical Changes Rule

Every change must be scoped to what was requested. Before committing:

| Violation | What it looks like |
|-----------|-------------------|
| Drive-by refactoring | Renamed variables, added type hints, changed quote style — none of it was in the task |
| Style normalization | Rewrote adjacent code to match your preferences instead of the existing style |
| Orphan overreach | Removed dead code that existed before this task (only YOUR orphans are your responsibility) |

**Self-check:** "Would a reviewer see any line in this diff that cannot be explained by the task description?" If yes → undo it.

## Rationalization Red Flags

These thoughts mean you are about to skip a mandatory step. Stop.

- "This change is too small to need a review"
- "I'll write the test after I confirm it works"
- "The plan is in my head, I don't need to write it"
- "The tests were passing before so they're probably still passing"
- "I know this language well enough, no need for the reviewer"
- "The skill overhead slows me down" (it doesn't — it prevents the rework that slows you down)

## Session Start Checklist

On every session start, confirm:
- [ ] Is `INIT.md` present? If not → fill out `INIT_TEMPLATE.md` first
- [ ] Is `.agent-sync/TEAM.md` present? If not → run `/orchestrate init` first
- [ ] What is the current task? → identify which skills/agents apply before starting

## Skill Registration (For New Skills)

When a new skill is added to A Team, add it to the trigger table above so it gets enforced from day one.

The A Team is only as good as the discipline with which it is applied.
Skills consulted are skills that work. Skills skipped are skills that don't exist.
