---
name: reader-experience-edit
description: Audit and revise practical nonfiction drafts for reader experience, value pacing, front-loaded insight, value-per-page, boredom, and beta-readiness. Use when editing, restructuring, shortening, or reviewing a book, guide, manual, course-like manuscript, or long-form educational draft so readers receive useful value quickly and keep reading.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Reader Experience Edit
  category: Writing
  tags: writing,books,nonfiction,editing,reader-experience
---

# Reader Experience Edit

## Core Lens

Treat reader experience as value received over time spent. Practical nonfiction does not keep readers engaged through suspense; it keeps them engaged by regularly delivering the outcome promised by the book.

Use this skill to diagnose and improve:

- Slow starts.
- Long stretches of theory before payoff.
- Low value-per-page.
- Sections whose value is unclear.
- Drafts that need to be coherent enough for beta readers, not polished enough for publication.

## Reference Routing

| Need | Read |
|------|------|
| Core concepts and terminology | `references/core/knowledge.md` |
| Revision rules and decision criteria | `references/core/rules.md` |
| Before/after patterns | `references/core/examples.md` |
| Fast audit checklist | `references/core/checklist.md` |
| Step-by-step manuscript audit | `workflows/audit-manuscript.md` |

## Workflow

### 1. Anchor On The Promise

Identify:

- Target reader.
- Book promise.
- First meaningful piece of value.
- What the reader should be able to do, decide, or understand after each major section.

If the promise is unclear, use `book-toc-lab` before editing the manuscript.

### 2. Create A Value Map

Build a table:

```text
Section | Word count | Reader takeaway | Value type | Risk
```

Use it to find:

- Slow start: too many words before first value.
- Long slog: back-to-back sections without strong takeaways.
- Fluff: high word count relative to reader value.

### 3. Front-Load Value

Look for ways to deliver the first useful result earlier:

- Cut front matter.
- Insert real value into theory sections.
- Start with the main insight, tool, checklist, example, or result.
- Move background after the reader has a reason to care.

### 4. Increase Value-Per-Page

Prefer deletion before addition.

- Cut anything outside the target reader's scope.
- Replace general motivation with concrete examples.
- Compress explanations that do not change reader behavior.
- Save deleted material in a separate cutting-room-floor note when useful.

### 5. Prepare For Beta Readers

Do not aim for perfect prose yet. Aim for a draft that is coherent enough for motivated readers to identify real problems.

Return:

1. Main reader-experience diagnosis.
2. Value map or section-by-section risk table.
3. Highest-leverage cuts, moves, and rewrites.
4. Revised opening or TOC recommendations when relevant.
5. Beta-readiness note: what must be fixed before readers see it.

## Quality Bar

Recommendations should be structural and specific. Prefer "move this section after X", "cut this setup", or "turn this theory into a worked example" over generic writing advice.
