---
name: documentation-platform-selection
description: Evaluate documentation platforms and authoring tools by requirements, workflow fit, migration risk, content model, search, integrations, portability, support burden, and cost. Use when choosing docs-as-code, CMS, wiki, DITA, API reference, static-site, help-center, or custom docs tooling, planning a migration, or deciding whether tooling will fix documentation problems.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Documentation Platform Selection
  category: Writing
  tags: developer-docs,technical-writing,documentation,platform-selection,tooling
---

# Documentation Platform Selection

Use this skill to choose, compare, pilot, or migrate documentation platforms and authoring tools. It keeps the decision anchored in reader experience, author workflow, maintenance reality, and migration risk.

This skill is derived from paraphrased guidance in Christopher Gales and the Splunk Documentation Team's *The Product Is Docs: Writing Technical Documentation in a Product Development Group*, especially Chapter 17, "Tools and Content Delivery," plus related maintenance and audience guidance from Chapters 3 and 10. Do not copy book prose into user outputs. Source: https://link.springer.com/book/10.1007/978-1-4842-7217-6

## Quick Start

1. Load `guidelines.md` to choose the smallest useful reference set.
2. State current pain, target reader experience, author workflow, and constraints.
3. Use `workflows/evaluate-doc-platform.md` to compare options.
4. Use `workflows/plan-doc-migration-pilot.md` when migration or pilot planning is needed.
5. Separate tool problems from process, ownership, and information architecture problems.
6. Return requirements, comparison, recommendation, migration risk, pilot plan, and open questions.

## Default Output

When evaluating a documentation platform, return:

1. **Decision context** - current pain, audiences, content types, team workflow, and constraints.
2. **Requirements** - reader, authoring, content model, integration, maintenance, migration, portability, support, and cost.
3. **Option comparison** - weighted tradeoffs, fit, risks, and implementation burden.
4. **Process issues** - ownership, IA, review, metadata, or maintenance problems that tooling will not fix alone.
5. **Recommendation** - keep, improve process, pilot, migrate, or reject.
6. **Pilot or migration plan** - scope, success criteria, rollback, owners, and timeline.

## Contents

| Need | Start Here |
|------|------------|
| Understand platform selection concepts | `references/core/knowledge.md` |
| Evaluate and compare tools | `workflows/evaluate-doc-platform.md` |
| Plan migration or pilot | `workflows/plan-doc-migration-pilot.md` |
| Route by task or symptom | `guidelines.md` |

## Core Posture

- Start from reader and author outcomes, not vendor features.
- Diagnose process problems before blaming tooling.
- Treat migration as content, URL, metadata, search, and workflow change.
- Favor portability unless lock-in is an intentional tradeoff.
- Choose the platform the team can actually maintain.
