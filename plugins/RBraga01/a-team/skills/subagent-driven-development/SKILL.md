---
name: subagent-driven-development
description: Use when executing implementation plans with independent tasks in the current session. Dispatches a fresh subagent per task with two-stage review (spec compliance, then code quality).
---

# Subagent-Driven Development

Execute a plan by dispatching fresh subagents per task, with two-stage review after each.

**Core principle:** Fresh subagent per task + two-stage review (spec then quality) = high quality, fast iteration.

**Continuous execution:** Do not pause to check in between tasks. Execute all tasks without stopping.
The only reasons to stop: BLOCKED status you cannot resolve, genuine ambiguity, or all tasks complete.

## Process

### Step 0: Setup
- Read plan file once; extract ALL tasks with full text and context
- Create TodoWrite with all tasks
- Verify git worktree isolation is configured

### Per Task:
1. Dispatch implementer subagent with full task text + relevant context
2. If implementer asks questions → answer, re-dispatch
3. Implementer implements, tests, commits, self-reviews
4. Dispatch spec compliance reviewer — confirms code matches spec
5. If spec issues → implementer fixes, reviewer re-reviews (loop)
6. Dispatch code quality reviewer — confirms quality standards met
7. If quality issues → implementer fixes, reviewer re-reviews (loop)
8. Mark task complete in TodoWrite

### After All Tasks:
- Dispatch final code reviewer for entire implementation
- Use `finishing-a-development-branch` skill

## Implementer Status Handling

| Status | Action |
|--------|--------|
| DONE | Proceed to spec compliance review |
| DONE_WITH_CONCERNS | Read concerns, address if correctness/scope issues |
| NEEDS_CONTEXT | Provide missing context, re-dispatch |
| BLOCKED | Assess: context problem → more context; reasoning → higher model; too large → break up; wrong plan → escalate |

## Model Selection

Select the lowest tier that can handle the task:

| Scope | Claude Code | OpenAI | Google |
|-------|------------|--------|--------|
| 1-2 files, clear spec | `claude-haiku-4-5` | `gpt-4.1-mini` | `gemini-2.0-flash-lite` |
| Multi-file, integration concerns | `claude-sonnet-4-6` | `gpt-4.1` | `gemini-2.5-flash` |
| Design judgment, broad codebase | `claude-opus-4-8` | `o3` / `gpt-5.5` | `gemini-2.5-pro` |

## Review Order (Critical)

**Spec compliance MUST be ✅ before starting code quality review.**
Never skip either review stage.

## Red Flags — Never Do

- Start on main/master branch without explicit user consent
- Skip either review stage
- Dispatch multiple implementation subagents in parallel (file conflicts)
- Make subagent read plan file (provide full text instead)
- Accept "close enough" on spec compliance
- Ignore subagent questions before they start work

## Integration

Uses: `writing-plans` (creates the plan), `finishing-a-development-branch` (completes work)
Subagents use: test-driven-development, code-review patterns
