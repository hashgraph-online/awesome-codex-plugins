---
name: skill-router
description: Use when the user explicitly asks to diagnose or improve Codex skill/plugin routing, determine which skill or plugin should handle a request, refresh or check a skill registry, investigate why a skill/plugin did not trigger, or review skill descriptions for trigger quality. Do not use for ordinary task execution when a concrete domain skill clearly applies, unless routing is ambiguous or the user asks for routing.
---

# Skill Router

Use this skill as a diagnostic and routing-assistance layer. It does not replace Codex native skill discovery, Superpowers process skills, or subagent orchestration. It helps decide which capabilities are relevant, why they are relevant, and when not to use them.

## Boundaries

- Do not execute the user's domain task unless the user asks you to continue after routing.
- Do not assume external connectors are authenticated or can see data.
- Do not treat registry cards as the source of truth. Use them as hints with provenance.
- Do not perform dynamic scanning unless the user asks to refresh or check the registry.
- Prefer local files, local repositories, browser verification, and build/test commands unless the user explicitly names an external app or the source of truth clearly lives there.

## When To Use

Use this skill when the user asks things like:

- "Which skill should handle this?"
- "Why did this skill not trigger?"
- "Refresh the skill registry."
- "Review this skill description for trigger quality."
- "List likely skills/plugins for this task."
- "Help me improve skill/plugin hit rate."

## When Not To Use

Do not use this skill for simple tasks with an obvious primary skill:

- Editing a local PDF: use the PDF skill.
- Creating a slide deck: use the presentation skill.
- Debugging a failing test: use systematic debugging first.
- Implementing a frontend app: use frontend app building/testing skills.

If the task is complex or ambiguous, perform a brief routing check and then continue with the selected primary skill.

## Diagnostic Workflow

1. Classify the user request:
   - task type: explain, create, edit, debug, analyze, test, review, deploy
   - source: local, web, GitHub, Gmail, Drive, Notion, Slack, Figma, Linear
   - artifact: code, document, spreadsheet, presentation, PDF, image, webpage, report
   - process need: planning, debugging, TDD, verification, review, orchestration
2. Read the registry if available.
3. Identify recommended skill/plugin candidates.
4. Apply local-first and connector-explicit rules.
5. Return concise output:
   - Recommended skill
   - Helper skills
   - Why
   - Do not use
   - Needs confirmation
6. If debug mode is requested, include skipped candidates and scoring details.

## Output Format

```text
Recommended skill:
- ...

Helper skills:
- ...

Why:
- ...

Do not use:
- ...

Needs confirmation:
- ...
```

## Registry Maintenance

Use `scripts/build_registry.py` only when the user explicitly asks to refresh the registry or when the registry is stale, missing, or inconsistent.

Use `scripts/route_request.py --check-registry` to inspect registry health.

See `references/capability-card-schema.md` for card fields and provenance requirements.
