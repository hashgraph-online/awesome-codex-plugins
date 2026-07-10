---
name: debugging
description: "Use when fixing bugs, investigating errors, debugging failures, or diagnosing unexpected behavior."
user-invocable: true
allowed-tools: Glob, Grep, Read, Bash, Task, Skill, Edit, Write, AskUserQuestion
---

# Systematic Debugging

Apply [Iron Rules](../../shared/iron-rules.md): Principle 9 (root cause, not symptoms) and Principle 8 (every hypothesis tested against fresh evidence) govern every step.

**Phase 0 — baseline:** run the existing suite first and record pass/fail counts; pre-existing failures are NOT your regressions.

**Language context:** if a language skill is active, read its `patterns.md` during investigation for team-specific patterns.

**Routing:**
- Integrated — slots into Phase 1 (Research + Plan) of the [shared workflow](../../shared/workflow.md); once the root cause is found, continue the locked plan through the remaining phases.
- Standalone (`/debugging`) — announce root cause + proposed fix, then ask before entering the dev workflow.
