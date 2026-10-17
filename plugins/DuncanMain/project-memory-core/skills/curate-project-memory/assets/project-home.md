---
type: project-home
project_id: "{{project_id}}"
status: active
updated: "{{date}}"
review_after: "{{review_after}}"
tags:
  - project-memory
---

# {{project_name}}

> [!summary] What this project is
> {{one_sentence_purpose}}

## At a glance

| | |
|---|---|
| **Status** | {{status_summary}} |
| **Current focus** | {{current_focus}} |
| **Next milestone** | {{next_milestone}} |
| **Last reviewed** | {{date}} |

## Start here

- [[Current State|Current state and next actions]]
- [[Handoff|Latest handoff]]
- [[Project|Project details]]
- [[Inbox/Promotion Inbox|Knowledge awaiting review]]

## How the project fits together

{{architecture_or_structure_summary}}

## Important commands

| Action | Command |
|---|---|
| Run | `{{run_command}}` |
| Test | `{{test_command}}` |
| Build | `{{build_command}}` |

Remove unknown command rows instead of guessing.

## Decisions and constraints

{{decision_and_constraint_links}}

## Risks and blockers

{{risks_and_blockers}}

## Next actions

{{next_actions}}

---

> [!info] Private by design
> This project memory is ordinary Markdown in your Obsidian vault. PMC asks before promoting durable knowledge and does not send your notes to the plugin developer.
