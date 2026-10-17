---
name: document-review
description: Optional utility for reviewing existing docs, external specs, hand-authored notes, or non-HOTL documents. HOTL design docs and workflows get structural lint + AI review; other documents get AI-only review with a generic rubric.
---

# HOTL Document Review

## Overview

Optional utility for ad hoc document review. Use this to review existing docs, external specs, hand-authored plans, or any non-HOTL document. HOTL documents get structural lint (hard gate) followed by AI review. Non-HOTL documents skip lint and go straight to AI review with a generic rubric.

**Note:** This skill is not required in the standard HOTL flow. Writing-plans includes a built-in self-check, and execution preflight runs structural lint automatically. Use this skill when you want to review a document outside of the normal plan-then-execute cycle.

**Announce:** "Running document review. Classifying input..."

## Step 0 — Classify the Input

Before doing anything else, classify the input into one of four categories:

| Category | Detection | Review Path |
|---|---|---|
| **HOTL workflow** | Canonical `docs/plans/*-workflow.md` or legacy `hotl-workflow-*.md` | Phase 1 (HOTL lint, hard gate) → Phase 2 (HOTL AI review) |
| **HOTL design doc (marked)** | A design-doc-shaped file (canonical `docs/designs/*.md` or legacy `*-design.md` / `*-plan.md`) whose YAML frontmatter declares `design_type:` (one of `feature \| phase \| initiative \| architecture \| contract \| reference`) OR `hotl_managed: true` | Phase 1 (HOTL lint) → Phase 2 (HOTL AI review) |
| **Generic text/markdown** | Any other `.md`, `.txt`, or pasted text — including design-shaped files in `docs/designs/` that lack an HOTL marker | Skip Phase 1 → Phase 2 (generic AI review) |
| **PDF** | `.pdf` extension | If the current runtime can read/extract the content, treat as generic text and review. Otherwise, ask the user for a text, markdown, or PDF-text export. |
| **DOCX / PPTX / binary** | `.docx`, `.pptx`, or other binary formats | **STOP.** Ask the user for a markdown, plain text, or PDF export. Do not attempt conversion. |

**Phase 1.6 opt-in rule:** Path alone does NOT classify a file as HOTL. A design-shaped Markdown file in `docs/designs/` without an HOTL frontmatter marker (`design_type:` or `hotl_managed: true`) is treated as generic markdown — `document-lint.sh` will SKIP it cleanly, and this skill routes it through Phase 2's generic-rubric AI review. To opt a hand-authored design doc into HOTL strict review, add `design_type: <recognized-value>` or `hotl_managed: true` to its frontmatter.

**Announce the classification:** e.g., "Classified as HOTL design doc (marked via design_type) — running lint + HOTL review." or "Classified as generic markdown — skipping lint, running generic review."

## Phase 1: Structural Lint (HOTL Documents Only)

**Skip this phase entirely for non-HOTL documents.** If the input was classified as generic text/markdown or PDF, go directly to Phase 2 (generic AI review).

For HOTL documents only, run the deterministic lint script:

```bash
bash scripts/document-lint.sh <file>
```

Resolve `document-lint.sh` in this order:

1. If you are working in the `hotl-plugin` repo itself, use `scripts/document-lint.sh`
2. Codex native-skills install: `~/.codex/hotl/scripts/document-lint.sh`
3. Codex plugin install: `~/.codex/plugins/hotl-source/scripts/document-lint.sh`
4. Codex plugin cache fallback: `~/.codex/plugins/cache/codex-plugins/hotl/*/scripts/document-lint.sh`
5. Cline install fallback: `~/.cline/hotl/scripts/document-lint.sh`
6. Claude Code plugin fallback: `~/.claude/plugins/hotl/scripts/document-lint.sh`

Do not assume `scripts/document-lint.sh` exists in the repo being reviewed. The lint script lives in the HOTL install, not in arbitrary user projects.

#### Resolving `hotl-config.sh`

`hotl-config.sh` (the canonical reader for `.hotl/config.yml`) follows the same six-location resolution order as `document-lint.sh`:

1. If you are working in the `hotl-plugin` repo itself, use `scripts/hotl-config.sh`
2. Codex native-skills install: `~/.codex/hotl/scripts/hotl-config.sh`
3. Codex plugin install: `~/.codex/plugins/hotl-source/scripts/hotl-config.sh`
4. Codex plugin cache fallback: `~/.codex/plugins/cache/codex-plugins/hotl/*/scripts/hotl-config.sh`
5. Cline install fallback: `~/.cline/hotl/scripts/hotl-config.sh`
6. Claude Code plugin fallback: `~/.claude/plugins/hotl/scripts/hotl-config.sh`

Do not assume `scripts/hotl-config.sh` exists in the repo being reviewed. Callers that do not know their install location should invoke `scripts/hotl-config-resolve.sh` (a thin command proxy that locates `hotl-config.sh` and forwards argv).

**If lint FAILS:** STOP. Show all errors. The author MUST fix structural issues before AI review runs. Do not proceed.

**If lint PASSES:** Continue to Phase 2 (HOTL AI review).

### What Lint Checks

**Design docs (canonical `docs/designs/*.md`, plus legacy `*-design.md` / `*-plan.md` tactical docs):**
- Intent Contract with intent, constraints, success_criteria, risk_level
- Verification Contract with at least one verify step
- Governance Contract with approval_gates and rollback
- risk_level is low, medium, or high

**Workflow files (canonical `docs/plans/*-workflow.md`, plus legacy `hotl-workflow-*.md`):**
- YAML frontmatter with intent, success_criteria, risk_level
- Every step has action and loop fields
- Every looped step (loop: until) has verify and max_iterations
- Preferred workflow step syntax is `- [ ] **Step N: ...**`, though legacy `### N.` headings may still appear
- High-risk steps with security keywords have gate: human

## Phase 2: AI-Driven Review (Soft Gate)

Read the full document and evaluate using the rubric that matches the classification:

### For Design Docs

1. **Internal consistency** — Do the three contracts align with each other? Does the verification contract actually test the intent?
2. **YAGNI** — Is anything speculative, overbuilt, or solving problems that don't exist yet?
3. **Risk assessment** — Is the risk_level appropriate? Are high-risk areas (auth, encryption, billing) correctly identified?
4. **Success criteria** — Are they concrete and testable, or vague?
5. **Scope** — Does this cross too many subsystems? Should it be decomposed?

### For Workflow Files

1. **Step sizing** — Are steps atomic (2-5 minutes each)? Flag steps that are too large or vague.
2. **Verify coverage** — Do verify commands actually test what the step claims to do?
3. **Gate placement** — Are human gates placed at the right points? Any risky steps missing gates?
4. **Loop safety** — Are max_iterations reasonable? Any infinite-loop risks?
5. **Ordering** — Do steps build on each other logically? Any missing dependencies?

### For Generic Documents

1. **Clarity** — Is the writing clear, specific, and unambiguous?
2. **Completeness** — Are important details, assumptions, or decisions missing?
3. **Internal consistency** — Does the document contradict itself anywhere?
4. **Actionability** — Are decisions, next steps, owners, or open questions clearly stated?
5. **Risk / Ambiguity** — Are there risky assumptions, vague areas, or likely points of confusion?

## Review Outcomes

After completing the review, output exactly one of the following. Use `Lint: PASSED` for HOTL documents or `Lint: SKIPPED (non-HOTL document)` for all other inputs.

### PASS
All checks satisfied. Document is ready.

```
REVIEW: PASS
Document: <filename>
Lint: PASSED | SKIPPED (non-HOTL document)
AI Review: No issues found.
Ready for execution.
```

### REVISE
Issues found that should be fixed. List each with a specific suggestion.

```
REVIEW: REVISE
Document: <filename>
Lint: PASSED | SKIPPED (non-HOTL document)
AI Review: <N> issue(s) found.

Issues:
1. [ISSUE]: <description>
   Suggestion: <how to fix>
2. [ISSUE]: <description>
   Suggestion: <how to fix>

Fix these issues and re-run document review.
```

### HUMAN_OVERRIDE_REQUIRED
Serious concerns that the AI cannot resolve. Human must decide whether to proceed.

```
REVIEW: HUMAN_OVERRIDE_REQUIRED
Document: <filename>
Lint: PASSED | SKIPPED (non-HOTL document)
AI Review: Serious concern(s) requiring human judgment.

Concerns:
1. [CONCERN]: <description>
   Risk: <what could go wrong>
2. [CONCERN]: <description>
   Risk: <what could go wrong>

Do not continue until a human explicitly says to override these concerns.
```

## Rules

- Always classify the input before choosing a review path.
- For HOTL documents: never skip lint; never continue to execution when lint fails.
- For non-HOTL documents: skip lint entirely (no structural validation).
- For DOCX/PPTX/binary: do not attempt conversion; ask for an export.
- If review outcome is `REVISE`, the author fixes the document first.
- If review outcome is `HUMAN_OVERRIDE_REQUIRED`, only an explicit human decision allows execution to proceed.
