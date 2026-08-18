---
name: docs-agile-integration
description: Integrate documentation work with Agile product development by making docs visible in sprint planning, release trains, definitions of done, review timing, and retrospective improvement. Use when docs are missing from scrum boards, stories, acceptance criteria, release planning, or cross-team work, or when writers need a lightweight process for documentation inside Agile teams.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Docs Agile Integration
  category: Writing
  tags: developer-docs,technical-writing,documentation,agile,docs-ops
---

# Docs Agile Integration

Use this skill to integrate documentation with Agile product development without hiding docs-specific work. It helps writers and product teams plan docs, reviews, release readiness, and maintenance in the cadence where product decisions happen.

This skill is derived from paraphrased guidance in Christopher Gales and the Splunk Documentation Team's *The Product Is Docs: Writing Technical Documentation in a Product Development Group*, especially Chapter 2, "Agile," Chapter 19, "Working with Engineers," Chapter 22, "Working with Product Management," and Chapter 23, "Working on a Remote Team." Do not copy book prose into user outputs. Source: https://link.springer.com/book/10.1007/978-1-4842-7217-6

## Quick Start

1. Load `guidelines.md` to choose the smallest useful reference set.
2. Identify the team's Agile cadence, planning artifacts, release model, and where docs are currently invisible.
3. Use `workflows/integrate-docs-agile.md` to attach docs work to product work.
4. Use `workflows/define-docs-done.md` to add documentation checks to definition of done or release readiness.
5. Separate feature-sprint docs from docs work that legitimately spans sprints or teams.
6. Return recommended board changes, doc tasks, review checkpoints, blockers, and retrospective signals.

## Default Output

When integrating docs with Agile work, return:

1. **Current process map** - cadence, artifacts, boards, roles, release gates, and review paths.
2. **Docs visibility gaps** - where docs impact, tasks, blockers, reviews, or release readiness are missing.
3. **Recommended workflow** - ticket/linking model, planning checkpoints, owner, and review timing.
4. **Definition-of-done updates** - docs impact, draft, review, QA, publish, release notes, and maintenance checks.
5. **Cross-sprint handling** - how scenario, maintenance, IA, or cross-team docs stay visible without pretending to fit one sprint.
6. **Inspect-and-adapt signals** - support feedback, review misses, late docs, stale content, and retrospective actions.

## Contents

| Need | Start Here |
|------|------------|
| Understand docs and Agile concepts | `references/core/knowledge.md` |
| Integrate docs into planning and boards | `workflows/integrate-docs-agile.md` |
| Define docs done and release readiness | `workflows/define-docs-done.md` |
| Route by task or symptom | `guidelines.md` |

## Core Posture

- Treat documentation as product work.
- Make docs visible in the planning system the product team already uses.
- Match docs cadence to actual scope instead of forcing every docs activity into one sprint.
- Add lightweight checkpoints before release risk appears.
- Use retrospectives and customer signals to improve the process.
