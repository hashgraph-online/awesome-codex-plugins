---
name: technical-manuscript-verification
description: Verify technical nonfiction manuscripts for runnable accuracy, including commands, configuration, code snippets, links, version drift, screenshots, prerequisites, security warnings, expected outputs, and reproducibility. Use when auditing self-hosting, DevOps, programming, infrastructure, data, security, or software tutorial drafts before beta reading, publication, or release.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Technical Manuscript Verification
  category: Writing
  tags: writing,books,nonfiction,technical-writing,verification
---

# Technical Manuscript Verification

## Core Lens

Technical nonfiction must work in the reader's environment, not just in the author's memory. Verification checks whether commands run, configs are coherent, screenshots match text, links still resolve, safety boundaries are clear, and the reader has enough context to recover from failure.

Use this skill to audit:

- Technical book chapters and tutorials.
- Self-hosting and infrastructure guides.
- Code snippets, shell commands, Docker Compose files, config examples, diagrams, and screenshots.
- Claims that depend on current platform behavior or version-specific documentation.
- Pre-beta or pre-publication technical accuracy.

## Reference Routing

| Need | Read |
|------|------|
| Verification concepts and terminology | `references/core/knowledge.md` |
| Audit rules and evidence standards | `references/core/rules.md` |
| Example findings and verification tables | `references/core/examples.md` |
| Fast verification checklist | `references/core/checklist.md` |
| Step-by-step verification pass | `workflows/verify-technical-manuscript.md` |

## Workflow

### 1. Define The Verification Scope

Identify what needs verification:

- Commands and code.
- Config files and environment variables.
- Installation and setup steps.
- Screenshots, diagrams, and expected outputs.
- Links and external references.
- Safety, security, privacy, data loss, and cost warnings.

Use a narrow pass when the manuscript is large.

### 2. Build An Evidence Table

For each technical item, track:

```text
Item | Location | Assumption | Verification method | Result | Fix
```

Do not rely on plausibility when the item can be checked.

### 3. Verify Against Real Or Simulated Environments

Prefer running commands, linting configs, checking links, rendering examples, or consulting primary documentation. When execution is unsafe or impractical, state the assumption and the evidence still needed.

### 4. Classify Findings By Reader Risk

Prioritize:

- Data loss, security exposure, privacy harm, or irreversible changes.
- Commands that fail or produce different output.
- Missing prerequisites that block readers.
- Current-info drift from tool or platform changes.
- Misleading screenshots or diagrams.

### 5. Return Fixes The Author Can Apply

Recommend exact changes:

- Add prerequisite.
- Change command or config.
- Add expected output.
- Add warning, rollback, or troubleshooting note.
- Move volatile steps to a companion resource.
- Mark claim for current-doc verification.

## Output Format

When verifying a manuscript, return:

1. Verification scope and assumptions.
2. Findings ordered by reader risk.
3. Evidence table with pass/fail/untested status.
4. Exact manuscript fixes.
5. Items requiring current primary-source verification.
6. Suggested beta-reader or expert-review checks.

## Quality Bar

Be concrete and evidence-driven. Distinguish "verified," "likely," "untested," and "unsafe to test here." Never imply that a technical instruction works unless it was actually checked or the limitation is clearly stated.
