---
name: go
description: "Go phase. Reads the approved SPEC file, maps Requirements to tasks (plan), executes via TDD (build), and integrates results verifying all Acceptance Criteria."
---

# Go — Build It

**CRITICAL**: Run `HARNESS_DIR=$(epic-harness path)` first. NEVER use `.harness/` in the project directory.

## Execution Modes

This skill has 3 internal modes that run sequentially:

1. **go:plan** — Decompose requirements into ordered, parallelizable tasks
2. **go:build** — Execute each task using TDD (Red→Green→Refactor)
3. **go:integrate** — Merge results, verify all ACs, fix failures

---

## Mode: go:plan (Plan)

Decompose the spec into an execution plan.

### Process

1. **Load the spec:**
   ```bash
   ls -t $HARNESS_DIR/specs/SPEC-*.md | head -1
   ```
   Read the file. Confirm frontmatter has `status: approved`. If not, invoke the **spec** skill first.

2. **Survey the codebase**: Identify relevant files, modules, patterns for each requirement.

3. **Decompose**: Map each Requirement → one or more Tasks. Every task must reference its source requirement:

   ```
   Task 1: [description] — satisfies: R1 — depends on: none — modifies: [file list]
   Task 2: [description] — satisfies: R2 — depends on: Task 1 — modifies: [file list]
   Task 3: [description] — satisfies: R1,R2 (integration) — depends on: Task 1,2 — modifies: [file list]
   ```

4. **Conflict analysis**:
   - Tasks modifying same files → serialize or use worktree isolation
   - Tasks modifying different files → safe to parallelize
   - Don't plan more than 8 tasks — if bigger, split into phases
   - Include "verify integration" as final task if 3+ tasks

5. Show the plan. Get user confirmation (or auto-proceed if in `/orbit`).

6. **Identify risks**: For each task, list potential failure modes:
   ```
   ### Risks
   - {risk}: {mitigation}
   ```

7. **Create feature branch** (standalone invocation only — `/orbit` handles this in Step 3):
   ```bash
   git checkout -b feature/{goal_slug}
   ```

### Execution Order Format

```
- Batch 1 (parallel): Task 1, Task 3
- Batch 2 (sequential): Task 2
```

---

## Mode: go:build (Execute TDD)

For each task, follow this TDD cycle:

### Builder Protocol

1. Read the task description carefully
2. Identify what file(s) to create or modify
3. **Red**: Write the test(s) — confirm they fail
4. **Green**: Write the minimum code to pass
5. **Refactor**: Clean up if needed — no behavior changes
6. Run tests — confirm they pass
7. Report: what was built, what tests pass

### Parallel Execution

Launch sub-agents with these rules:
- `run_in_background: true` for independent tasks (parallel execution)
- `isolation: "worktree"` if and only if parallel tasks modify overlapping files

| Scenario | Parallel? | Same Files? | Isolation? |
|----------|-----------|-------------|------------|
| Task A, B sequential | No | Any | No |
| Task A, B parallel | Yes | No overlap | No |
| Task A, B parallel | Yes | Overlap exists | Yes |

### Subagent Result States

| State | Meaning | Follow-up |
|-------|---------|-----------|
| **DONE** | Task completed, all tests pass | Proceed |
| **DONE_WITH_CONCERNS** | Completed but has warnings | Review. Escalate security/data/breaking issues. |
| **NEEDS_CONTEXT** | Cannot proceed without user input | Prompt user with specific questions |
| **BLOCKED** | Unresolvable error | Try one alternative. If still blocked, report. |

If stuck 3+ times → invoke **agent-introspection** skill.

### Subagent Output Format

```
## Status: [DONE|DONE_WITH_CONCERNS|NEEDS_CONTEXT|BLOCKED]
## Summary: [1-2 sentences]
## Evidence: [test output, file changes]
## Concerns: [only for DONE_WITH_CONCERNS]
## Questions: [only for NEEDS_CONTEXT]
## Blocker: [only for BLOCKED]
```

---

## Mode: go:integrate (Integrate)

After all tasks complete:

1. Categorize each task result by state (DONE/CONCERNS/NEEDS_CONTEXT/BLOCKED)
2. Resolve NEEDS_CONTEXT tasks before integration
3. Attempt alternatives for BLOCKED tasks, exclude from "satisfied" count
4. Run the full test suite
5. Verify each Acceptance Criterion (AC1, AC2, ...) is demonstrably met
6. If anything fails, dispatch a fix and re-verify

### Go Report

```
## Go Report
- Spec: SPEC-{timestamp} ({goal_slug})
- Branch: {branch}
- Requirements satisfied: R1 ✅, R2 ✅, ...
- AC verified: AC1 ✅, AC2 ✅, ...
- Tests: X/Y passing
- Subagent states: X DONE, Y CONCERNS, Z BLOCKED
- Remaining issues: none / [list]
```

Tell the user: **"Build complete. Run `/audit` to verify before shipping."**

## Skills Auto-Triggered

- **tdd**: Every subagent follows red-green-refactor
- **debug**: On any test failure or error
- **verify**: Before marking any task complete
- **simplify**: If any file exceeds 200 lines

## Anti-Rationalization

| Excuse | Rebuttal | What to do instead |
|--------|----------|-------------------|
| "I'll just implement it all in one go" | No plan = no accountability | Plan tasks, map to requirements |
| "Tests slow me down" | Debugging takes longer than testing | Write test first, always |
| "I'll skip the plan, it's obvious" | "Obvious" hides assumptions | Plan even for simple changes |
| "I can modify files outside my task" | Scope creep introduces bugs | Stay within task boundaries |

## Evidence Required

- [ ] Plan exists with tasks mapped to Requirements
- [ ] Each task has test(s) that pass
- [ ] All Acceptance Criteria verified
- [ ] Full test suite passes
- [ ] No uncommitted changes in worktree

## Red Flags

- Implementing without a plan
- Skipping tests "to save time"
- Not verifying the full suite after integration
- Implementing everything in a single file
- Starting without a `status: approved` spec
