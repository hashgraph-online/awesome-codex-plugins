---
name: developer-docs-editing-review
description: Edit and review developer documentation for technical accuracy, completeness, structure, clarity, brevity, peer feedback, technical review, technical verification, QA procedure testing, and feedback integration. Use when reviewing, editing, refactoring, or preparing developer docs for release, especially docs with procedures, examples, prerequisites, or high-risk technical claims.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Developer Docs Editing Review
  category: Writing
  tags: developer-docs,technical-writing,documentation,editing,review
---

# Developer Docs Editing Review

Use this skill to improve developer documentation after a draft exists. It treats editing as validation and refactoring: check whether the doc is accurate, complete, structured, clear, brief, and reviewable.

This skill is derived from *Docs for Developers: An Engineer's Field Guide to Technical Writing*, especially Chapter 4, "Editing documentation." It is expanded with paraphrased guidance from Christopher Gales and the Splunk Documentation Team's *The Product Is Docs: Writing Technical Documentation in a Product Development Group*, especially Chapter 15, "Technical Editing," and Chapter 16, "Technical Verification." Do not copy book prose into user outputs. Source: https://link.springer.com/book/10.1007/978-1-4842-7217-6

## Quick Start

1. Load `guidelines.md` to choose the smallest useful reference set.
2. Identify doc type, audience, source of truth, and release risk.
3. Use separate passes for technical accuracy, completeness, structure, clarity, and brevity.
4. Use `workflows/verify-technical-doc.md` when procedures, migrations, security, data, or production changes need formal verification.
5. Use `workflows/edit-developer-doc.md` for a full edit.
6. Return findings first when the user asks for a review; return revised text when the user asks for an edit.

## Default Output

When reviewing documentation, return:

1. **Findings** - ordered by reader risk, with file/section references when available.
2. **Missing validation** - commands, examples, screenshots, API facts, or source claims not checked.
3. **Verification route** - self-test, SME review, QA test, or release blocker.
4. **Recommended edits** - exact changes or rewrites.
5. **Review routing** - who should validate technical details.
6. **Residual risk** - assumptions that remain after the edit.

When editing directly, return the revised doc plus a brief change summary and unresolved questions.

## Contents

| Need | Start Here |
|------|------------|
| Understand editing passes | `references/core/knowledge.md` |
| Apply review rules | `references/core/knowledge.md` |
| See examples of edits and feedback | `references/core/knowledge.md` |
| Run a full edit | `workflows/edit-developer-doc.md` |
| Verify risky technical docs | `workflows/verify-technical-doc.md` |
| Route by task | `guidelines.md` |

## Core Posture

- Separate writing from editing; do not polish around an unverified flaw.
- Prioritize reader-impacting errors over style preferences.
- Ask for specific reviews from the right technical owners.
- Treat high-risk procedures as release-blocking until verified or explicitly accepted.
- Integrate feedback by user need, not by reviewer rank or comment volume.
