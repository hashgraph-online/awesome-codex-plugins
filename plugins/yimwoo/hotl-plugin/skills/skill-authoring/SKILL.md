---
name: skill-authoring
description: Use when creating, editing, or reviewing HOTL skills, agents, command prompts, or other behavior-shaping instruction files.
---

# HOTL Skill Authoring

## Overview

HOTL skills are behavior-shaping code. Treat changes to skill text, agent prompts, command routers, and adapter instructions with the same care as production logic: define the failure mode, make the desired behavior explicit, verify the change, and update every index or mirror that exposes it.

## When To Use

Use this before changing:
- `skills/*/SKILL.md`
- `agents/*.md`
- `commands/*.md`
- `cline/rules/*.md`
- adapter templates that steer agent behavior
- docs that define skill invocation or routing

Do not use it for ordinary product docs, generated reports, or local project README edits unless they change how agents should behave.

## Process

1. **State the behavior change**
   - What agent behavior is wrong, missing, or ambiguous?
   - What prompt or session exposed the issue?
   - Is the change broadly useful, or project-specific?

2. **Choose the right abstraction**
   - Skill: reusable workflow or process the user can invoke.
   - Agent: isolated specialist with a stable output contract.
   - Inline prompt: short role text used by one skill only.
   - Script/lint: deterministic rule that should not depend on model judgment.

3. **Write trigger-only frontmatter**
   - `name`: kebab-case, no command-name collision.
   - `description`: says when to activate, not the workflow steps.
   - Avoid descriptions that summarize the process; agents may follow the summary and skip the body.

4. **Keep behavior text testable**
   - Use direct rules for invariants.
   - Add red flags for common rationalizations.
   - Prefer short, concrete examples over long narratives.
   - Separate heavy references or templates into adjacent files only when they reduce the main skill's noise.

5. **Update routing and mirrors**
   - Add new skills to `skills/using-hotl/SKILL.md`.
   - Update `docs/skills.md`, README tables, and Codex docs for user-visible skill changes.
   - Update Cline rules or adapter templates when their behavior mirrors the changed skill.

6. **Verify behavior**
   - Add or update smoke tests for structural expectations.
   - For high-impact skill wording, run pressure tests or before/after sessions that demonstrate the target behavior.
   - Run `bats test/smoke.bats` before claiming the skill change is ready.

## Description Trap

The frontmatter `description` is discovery text, not a miniature skill. If it contains a workflow summary, an agent may act on that summary without reading the full body.

Bad:

```yaml
description: Use when executing plans - dispatches workers, reviews every task, then finalizes
```

Good:

```yaml
description: Use when executing implementation workflows that can delegate contained steps to fresh subagents.
```

## Checklist

- [ ] The change solves a real behavior gap.
- [ ] The abstraction is skill vs agent vs inline vs script for a reason.
- [ ] Frontmatter description is trigger-only.
- [ ] New skills are indexed in `using-hotl`.
- [ ] User-facing docs list new or renamed skills.
- [ ] Mirrors and adapters are updated when behavior is shared.
- [ ] Smoke tests or pressure tests cover the changed behavior.
