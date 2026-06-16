---
name: book-edit
description: "Phase 4: Editing. 5-stage pipeline — editorial assessment, developmental edit, line edit, copy edit, proofread."
---

# Phase 4: Editing

Sequential 5-stage pipeline. Context accumulates across stages.

| Stage | Focus | Output |
|-------|-------|--------|
| 1. Assessment | Macro: proportions, pacing, gaps, redundancies | `edits/01-assessment.md` |
| 2. Developmental | Chapter-level restructuring, argument strength | `edits/02-developmental.md` |
| 3. Line Edit | Paragraph-level, STYLE.md consistency | `edits/03-line-edit.md` |
| 4. Copy Edit | Spelling, terminology, numbers, code formatting | `edits/04-copy-edit.md` |
| 5. Proofread | Typos, spacing, markdown, references | `edits/05-proofread.md` |

**Severity**: Critical/Major → user approval required. Minor → auto-fix (spelling, markdown, terminology, headings).

Auto-fix scope: spelling/spacing, format normalization, terminology per STYLE.md, heading consistency.

Gate: all 5 stages done, <5 Critical/Major remaining, report generated, user approved Critical/Major.


## Post-Completion

Update the project dashboard status:

```bash
node {PLUGIN_ROOT}/velith.mjs scan [project-dir] --plugin-root={PLUGIN_ROOT}
```
