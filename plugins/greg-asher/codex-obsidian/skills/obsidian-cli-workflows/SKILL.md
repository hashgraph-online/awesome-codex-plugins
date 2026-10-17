---
name: obsidian-cli-workflows
description: Use this skill for one-command Obsidian workflow orchestration across the existing six domain skills. This skill owns named workflow command IDs and preview/apply execution policy, while delegating all direct official CLI command execution to the appropriate domain skill.
---

# Obsidian CLI Workflows

Use this skill for orchestration-only one-command workflows that chain the existing official Obsidian CLI domain skills.

## Routing contract

Use this skill when:
- the user asks for a named one-command workflow ID such as `tasks.rollup` or `daily.bootstrap`
- the user wants a preview/apply orchestration plan that may span multiple domain skills
- the user asks to run a multi-step vault workflow with explicit risk classification and side-effect reporting

Do not use this skill when:
- the user asks to run raw direct command families (route to the owning domain skill)
- the request is only note CRUD/tasks/properties/history without workflow orchestration
- the request is only runtime admin/devtools/sync/publish or only workspace/navigation without one-command orchestration
- the request depends on community CLI tooling, `obsidian://` launchers, or Headless Sync

## Public workflow command interface

Workflow invocation must use a named command ID from `references/workflow-registry.md`.

No natural-language-only invocation mode in this release:
- require explicit `workflow_id=<command-id>`
- reject unregistered workflow IDs

Common controls for every workflow:
- `mode=preview|apply` (default: `preview`)
- `vault=<name>` optional pass-through
- `output=inline|note|json` (default: `inline`)

## Core orchestration policy

1. This skill owns orchestration logic only and does not replace direct command ownership contracts of the six domain skills.
2. All workflows default to `mode=preview`.
3. Preview output must include step plan, target summary, risk classification, and required confirmations.
4. Apply output must include executed-step list, skipped-step list, and explicit mutation summaries.
5. Medium/high-risk workflows require explicit apply confirmation before mutating steps.
6. Apply mode may run only user-approved steps that match preview targets.
7. Ambiguous note/base/workspace targets fail closed with a disambiguation requirement.
8. `publish.release_gate` must probe `help publish:status` before any publish command.
9. If publish probe returns unsupported, return explicit blocker and do not attempt `publish:*`.
10. Keep `vault:open` out of executable workflow steps in this release.
11. Preserve existing domain-skill safety boundaries and mutation guardrails.
12. If a request falls outside official desktop CLI workflow surface, say so and stop.

## Codex-safe launcher and escalation policy

This skill delegates execution to the six domain skills.
For delegated command execution, inherit the same sanitized launcher and escalation behavior already defined in those skills.

## Risk model

- `low`: read-only workflows or report-only outcomes
- `medium`: controlled note/bookmark/runtime mutations with bounded scope
- `high`: workspace/layout mutations, direct base-create flows, or publish gating flows that can trigger remote side effects

## Response contract

Always return:
- `workflow_id`
- selected `mode`
- selected `output`
- delegated skill chain
- risk level
- step plan (`preview`) or execution summary (`apply`)
- target summary and ambiguity status
- mutation/side-effect summary when applicable
- blocking reason when capability/target checks fail

## Workflow registry

All workflow definitions and guardrails are in:
- `references/workflow-registry.md`

## References

- `references/playbook.md`
- `references/limitations-and-boundaries.md`
- `references/validation.md`
- `references/source-links.md`
