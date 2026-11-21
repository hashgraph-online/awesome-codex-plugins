# A Team — Session Start

This content is injected at the beginning of every session via the SessionStart hook.

---

You have the **A Team** multi-agent infrastructure active in this workspace.

## Mandatory First Steps

Before taking any action, confirm:

1. **Is `INIT.md` present?**
   - YES → continue
   - NO → tell the user: "This project has not been initialized. Please fill out `INIT_TEMPLATE.md`, save it as `INIT.md`, then run `/orchestrate init`."

2. **Is `.agent-sync/TEAM.md` present?**
   - YES → continue (the team has been pruned for this project)
   - NO → run `/orchestrate init` before any other work

3. **What is the current task?** → consult `skills/using-a-team/SKILL.md` to identify mandatory skills and agents.

## Quick Skill Trigger Reference

| You are about to... | Use first |
|--------------------|-----------|
| Write a new feature | `brainstorming` skill |
| Start development | `using-git-worktrees` skill |
| Write any code | `test-driven-development` skill |
| Debug a bug | `debugger` agent (Phase 1 first) |
| Claim anything is "done" | `verification-before-completion` skill |
| Finish a review | `code-reviewer` agent |
| Merge a branch | `quality-gate` command |

## The Hard Rule

If a skill or agent applies to your current task, **you must use it.**
Skipping a mandatory skill is not a time-saver — it is a defect deferred.

---

*Full skill catalog: `skills/using-a-team/SKILL.md`*
*Full agent roster: `AGENTS.md`*
*Orchestrate a new project: `/orchestrate init`*

---

<!-- A Team metrics: fires on every session start -->
Run silently: `python scripts/metrics.py session_start 2>/dev/null || python3 scripts/metrics.py session_start 2>/dev/null || true`
