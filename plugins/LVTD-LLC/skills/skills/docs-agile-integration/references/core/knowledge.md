# Docs Agile Integration Knowledge

Documentation is part of the product experience and should be visible in the product development system.

Source basis: *The Product Is Docs*, Chapter 2, "Agile," Chapter 19, "Working with Engineers," Chapter 22, "Working with Product Management," and Chapter 23, "Working on a Remote Team."

## Key Concepts

### Docs Impact Assessment

**Definition**: A lightweight check during planning that asks whether a product change affects public docs, internal docs, release notes, support enablement, samples, screenshots, or maintenance.

This prevents docs from being discovered only when code is ready to ship.

### Docs Work Item

**Definition**: A visible task, subtask, linked issue, or checklist item that tracks documentation work, owner, priority, blockers, and review needs.

Docs work can be linked to a feature story or tracked separately when it spans multiple features.

### Docs Definition Of Done

**Definition**: Release-readiness checks that ensure user-facing documentation is assessed, drafted, reviewed, validated, published, and maintainable when relevant.

Definition of done should be specific enough to prevent missed docs but light enough for the team to use.

### Cross-Sprint Documentation

**Definition**: Documentation work that cannot be finished inside one feature sprint because it spans scenarios, information architecture, maintenance, learning objectives, troubleshooting, or multiple teams.

Cross-sprint docs still need visibility in Agile tools, but their cadence should match their real scope.

### Inspect And Adapt

**Definition**: Using retrospectives, support signals, review misses, and release outcomes to adjust documentation intake, ownership, and timing.

Agile docs integration is an operating loop, not a one-time checklist.

## Core Rules

1. **Make docs visible early** - Add docs impact checks during backlog refinement, sprint planning, or release planning.
2. **Link docs to product work** - Use tasks, subtasks, labels, checklist fields, or linked tickets where the team already plans.
3. **Assign owners and reviewers** - Docs tasks need owner, source of truth, reviewer, and due timing.
4. **Track blockers openly** - Missing API names, UI labels, examples, release timing, and SME reviews should be visible.
5. **Use definition of done selectively** - Not every code change needs docs, but every user-facing change needs assessment.
6. **Plan review before final sprint pressure** - Technical review, QA validation, product approval, and editorial review need room.
7. **Separate feature docs from docs projects** - Scenarios, maintenance, IA, and learning paths may require separate docs epics or Kanban work.
8. **Bring docs signals to retrospectives** - Late reviews, support tickets, customer confusion, and stale docs are process data.
9. **Use remote-friendly records** - Distributed teams need written decisions, async review, links, and durable source notes.
10. **Avoid hidden side work** - Untracked docs work creates false velocity and release risk.
11. **Include internal docs where relevant** - Support, field, and operations docs can be part of release readiness.
12. **Keep process lightweight** - Add checkpoints that reduce risk, not ceremony for its own sake.

## Planning Touchpoints

| Agile Moment | Docs Question |
|--------------|---------------|
| Backlog refinement | Does this change affect docs, examples, screenshots, release notes, support, or internal runbooks? |
| Sprint planning | What docs tasks, owners, reviewers, and blockers belong on the board? |
| Daily standup or async update | Are docs blocked by facts, access, UI labels, code samples, or reviews? |
| Demo | Can docs use the demonstrated workflow, screenshots, examples, or acceptance criteria? |
| Release planning | What must publish with the release and what can follow later? |
| Retrospective | Did docs arrive late, block release, or trigger customer/support issues? |

## Definition Of Done Checks

| Check | Use When |
|-------|----------|
| Docs impact assessed | Every user-facing story or release item |
| Public docs updated | New or changed user behavior |
| Release note added | Users need change awareness or action |
| Technical review complete | Behavior, limits, APIs, security, or data claims matter |
| QA path validated | Procedure or example can be tested |
| Support/ops docs updated | Support, field, incident, or managed-service workflows change |
| Owner and source recorded | Content must stay accurate after release |

## Common Misconceptions

- **Myth**: Agile means all docs must finish in the same sprint as code.
  **Reality**: Feature-specific docs should be visible in sprint work, but some docs legitimately span sprints or teams.
- **Myth**: Docs can be tracked in a separate system without product team visibility.
  **Reality**: Separate docs tracking can work only if feature links, blockers, and release gates remain visible.
- **Myth**: Definition of done should force docs for every ticket.
  **Reality**: It should force assessment and require docs when user-facing impact exists.
- **Myth**: Writers only need information after the feature is complete.
  **Reality**: Early participation exposes user questions, product ambiguity, and review risk.

## Red Flags

- Docs tasks appear only after code freeze.
- Stories have user-facing changes but no docs impact field or checklist.
- Reviewers are unnamed or unavailable until release week.
- Docs blockers are private notes rather than board-visible blockers.
- Writers attend meetings but decisions are not recorded.
- Cross-team docs work is split across boards with no owner.
- Definition of done says "docs updated" without criteria.
- Retrospectives ignore late docs, support confusion, and release misses.

## Patterns

### Linked Docs Task Pattern

```text
Feature: Add webhook replay
Docs task: Document webhook replay for admins
Linked to: Feature story PAY-1842
Owner: Developer docs
Sources: API owner, support lead, QA replay test
Reviewers: API engineer, PM, support
Blocks: Final retention limit and UI label
Due: Draft before release candidate; publish with feature flag rollout
```

### Definition Of Done Pattern

```text
Docs impact assessed: yes/no
If yes:
- Public docs updated or created
- Release note includes impact and customer action
- Code samples or screenshots validated
- Technical review complete
- Support or runbook updates linked
- Owner and review trigger recorded
```
