---
name: developer-docs-drafting
description: Draft developer documentation with clear goals, outlines, titles, headers, procedures, scenario walkthroughs, lists, callouts, skimmable structure, and reusable templates. Use when writing or rewriting READMEs, getting-started docs, tutorials, how-to guides, concepts, API guides, troubleshooting pages, migration guides, SaaS topics, or release documentation.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Developer Docs Drafting
  category: Writing
  tags: developer-docs,technical-writing,documentation,drafting,authoring
---

# Developer Docs Drafting

Use this skill to draft developer documentation that readers can skim, follow, and apply. It turns audience and plan context into clear page structure and usable prose.

This skill is derived from *Docs for Developers: An Engineer's Field Guide to Technical Writing*, especially Chapter 3, "Drafting documentation." It is expanded with paraphrased guidance from Christopher Gales and the Splunk Documentation Team's *The Product Is Docs: Writing Technical Documentation in a Product Development Group*, especially Chapter 9, "Learning Objectives," Chapter 14, "Scenario-driven Information Development," and Chapter 25, "Writing SaaS Documentation." Do not copy book prose into user outputs. Source: https://link.springer.com/book/10.1007/978-1-4842-7217-6

## Quick Start

1. Load `guidelines.md` to choose the smallest useful reference set.
2. Confirm audience, doc type, one primary reader goal, and learning objective when available.
3. Outline before drafting; treat the outline like pseudocode for the doc.
4. Use `workflows/draft-developer-doc.md` for full-page drafts.
5. Put the most important information first and make the page easy to skim.

## Default Output

When drafting a doc, return:

1. **Title** - aligned with the reader goal.
2. **Opening context** - what the reader will accomplish and prerequisites.
3. **Structured body** - headings, steps, concepts, examples, lists, and callouts as appropriate.
4. **Scenario or route** - real-world path, scope boundary, or self-contained topic context when useful.
5. **Verification or expected result** - how the reader knows the task worked.
6. **Next steps** - where the reader should go next.
7. **Draft notes** - assumptions, TODOs, or source details needing review.

## Contents

| Need | Start Here |
|------|------------|
| Understand drafting components | `references/core/knowledge.md` |
| Apply drafting rules | `references/core/knowledge.md` |
| See before/after examples | `references/core/knowledge.md` |
| Draft a page | `workflows/draft-developer-doc.md` |
| Route by task | `guidelines.md` |

## Core Posture

- Write for the reader's next decision or action.
- Make the page understandable to skimmers.
- Keep procedures actionable and verifiable.
- Lead scenario docs with the user's problem, not the product feature.
- Use templates to reduce blank-page work, not to force every doc into the same shape.
