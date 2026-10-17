---
name: docs-release-maintenance
description: Manage developer documentation release, publishing, ownership, freshness, automation, maintenance, SaaS cadence, deprecation, deletion, redirects, and migration alongside software changes. Use when planning docs for a release, defining docs ownership, creating publishing checklists, setting up freshness checks, refreshing existing content, documenting SaaS releases, or retiring stale documentation.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Docs Release Maintenance
  category: Writing
  tags: developer-docs,technical-writing,documentation,release-management,maintenance
---

# Docs Release Maintenance

Use this skill to keep developer documentation aligned with software release and maintenance lifecycles. It covers publishing readiness, ownership, automation, freshness, and responsible deprecation or deletion.

This skill is derived from *Docs for Developers: An Engineer's Field Guide to Technical Writing*, especially Chapter 7, "Publishing documentation," and Chapter 11, "Maintaining and deprecating documentation." It is expanded with paraphrased guidance from Christopher Gales and the Splunk Documentation Team's *The Product Is Docs: Writing Technical Documentation in a Product Development Group*, especially Chapter 10, "Maintaining Existing Content," Chapter 25, "Writing SaaS Documentation," and Chapter 2, "Agile." Do not copy book prose into user outputs. Source: https://link.springer.com/book/10.1007/978-1-4842-7217-6

## Quick Start

1. Load `guidelines.md` to choose the smallest useful reference set.
2. Identify the release, affected users, docs owners, source of truth, and publication path.
3. Use `workflows/plan-doc-release-maintenance.md` for release or maintenance planning.
4. Use `workflows/refresh-existing-docs.md` when stale content, patch buildup, or dependency updates require a focused refresh.
5. Align doc publication, review, testing, announcement, and deprecation with code changes.
6. Prefer automation that removes known toil; do not automate an unclear process.

## Default Output

When planning release or maintenance work, return:

1. **Release or maintenance scope** - code/product change and affected docs.
2. **User impact** - who is affected and what action they need.
3. **Publishing checklist** - owner, reviewers, approval, tests, delivery, announcement.
4. **Maintenance plan** - owners, freshness checks, link checks, linting, generated references.
5. **Deprecation or deletion plan** - warnings, alternatives, migration guide, redirects, and timing.
6. **Risks and blockers** - unverified facts, missing owners, or automation gaps.

## Contents

| Need | Start Here |
|------|------------|
| Understand release and maintenance concepts | `references/core/knowledge.md` |
| Apply lifecycle rules | `references/core/knowledge.md` |
| See checklist examples | `references/core/knowledge.md` |
| Plan release, maintenance, or deprecation | `workflows/plan-doc-release-maintenance.md` |
| Refresh existing docs | `workflows/refresh-existing-docs.md` |
| Route by task | `guidelines.md` |

## Core Posture

- Docs should ship with the software change they explain.
- Every maintained doc needs ownership or an authoritative source.
- Automation should follow a understood manual process.
- Maintenance work should assess scope before patching content.
- Deprecation and deletion are user communication problems, not just cleanup tasks.
