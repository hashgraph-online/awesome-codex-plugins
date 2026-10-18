---
name: autopilot-resume
description: Resume a previously started 오토파일럿 project from saved state files. Use when the user asks to continue, resume, keep going, or finish an existing autopilot project.
summary: Read state, pick the next task, continue execution.
metadata:
  priority: 7
  promptSignals:
    phrases:
      - "오토파일럿 계속"
      - "오토파일럿 재개"
      - "resume autopilot"
      - "continue autopilot"
      - "keep going"
      - "다음 작업 이어서"
    anyOf:
      - "resume"
      - "continue"
      - "재개"
      - "계속"
    minScore: 4
retrieval:
  aliases:
    - 오토파일럿 재개
    - resume autopilot
    - continue execution
  intents:
    - continue a saved project
    - resume from progress files
  entities:
    - spec
    - progress
    - next
    - blockers
---

# Auto Pilot Resume

Use this skill when a project already has saved autopilot state.

## Required Inputs

Read these files first if they exist:

- `autopilot/state.json`
- `autopilot/blockers.json`
- `autopilot/secrets-status.json`
- `docs/next.md`
- `docs/spec.md` when setup is already complete
- `docs/design.md` for user-facing projects when setup is already complete
- `docs/progress.md` when setup is already complete

## Resume Workflow

1. Read `executionMode`, `teamRoles`, `currentOwner`, `qualityGates`, `lastPlannerCheckpoint`, `lastReviewerVerdict`, and `setupStatus`.
2. If `setupStatus` is `pending` or `autopilot/secrets-status.json.status` is `pending`, treat resume as setup continuation.
3. In that setup continuation path:
   - surface only the missing env payload
   - treat the project as a valid existing project even if `docs/spec.md` and `docs/progress.md` do not exist yet
   - do not resume implementation work until setup is complete
4. Otherwise determine whether there is an active blocker.
5. If the blocker is `human-required`, surface only the next minimal action.
6. If not blocked, confirm whether native sub-agents are currently available.
7. If the saved mode assumes native specialists but they are unavailable, downgrade the runtime path to `serial-fallback` and update state/progress/next before continuing.
8. Resume from the current owner role and the highest-priority unfinished task.
9. Preserve the manager flow:
   - planner before builder
   - designer review for user-facing UI slices
   - QA verdict before completion
10. Implement, validate, and update the state files.
   - use `python3 ../../scripts/team_checkpoint.py ...` after each planner / architect / builder / designer / QA result so resume state actually advances
11. Stop only if:
   - definition of done is met, or
   - a human-required blocker prevents further work

## Resume Output

Return a concise status update:

- last completed work
- current owner role
- current task
- next task after this
- QA verdict
- blocker or setup status
