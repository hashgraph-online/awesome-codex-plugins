---
name: book-toc-lab
description: Design and pressure-test useful nonfiction book promises, scopes, recommendation loops, and takeaway-first tables of contents before drafting. Use when planning, outlining, scoping, restructuring, validating, or testing a practical book, guide, manual, course-like book, or other reader-outcome-focused long-form nonfiction.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Book TOC Lab
  category: Writing
  tags: writing,books,nonfiction,outlining,toc
---

# Book TOC Lab

Treat a useful nonfiction book as a problem-solving product for a specific
reader. The table of contents is the product design, not a decorative outline.
Build and test the promise, scope, recommendation loop, and TOC before drafting
so the manuscript has a clear job and useful progression.

Use this skill to produce or improve a book plan that answers:

- Who is this book for?
- What painful or valuable problem does it help them solve?
- What should be different for the reader after each chapter?
- What does the book deliberately leave out?
- Why would a satisfied reader recommend it to a specific person in a specific
  situation?

## Resource Routing

Load only the files needed for the task:

| Need | Read |
| --- | --- |
| Core model, DEEP, promise, scope, recommendation loop | `references/core/knowledge.md` |
| Concrete planning and validation rules | `references/core/rules.md` |
| Before/after examples for scope and TOC titles | `references/core/examples.md` |
| Quick planning and review checklist | `references/core/checklist.md` |
| Step-by-step TOC design before drafting | `workflows/design-toc.md` |
| Step-by-step TOC validation with readers | `workflows/validate-toc.md` |

## Fast Workflow

1. Lock the reader promise before outlining.
2. Define in-scope, out-of-scope, prerequisites, and depth lines.
3. Write the recommendation story: trigger, recommender, recommended reader, and
   why this book is the obvious fit.
4. Draft chapters as reader takeaways, not author topic buckets.
5. Order chapters by reader progress: orientation, foundation, action, judgment,
   and integration.
6. Pressure-test every chapter against the promise, reader outcome, missing
   steps, boredom risk, confusion risk, skepticism, and recommendability.
7. Validate the TOC before drafting when practical.

## Output Format

When asked to create or improve a TOC, return:

1. Book brief: reader, problem, promise, scope, out-of-scope.
2. Recommendation story: trigger, recommender, recommended reader, why this book.
3. Recommended TOC with chapter-level reader problems and takeaways.
4. Reader journey notes explaining the order.
5. Risk list: missing prerequisites, vague chapters, likely confusion, likely
   boredom.
6. Validation plan: 3-7 concrete ways to test the TOC before drafting.

## Quality Bar

A good TOC should feel useful even before the book exists. A reader should be
able to scan it and understand what the book helps them accomplish, whether it
is for them, and why the chapter sequence makes sense.

Do not optimize for literary cleverness before usefulness. Clever titles are
acceptable only after the reader promise and chapter takeaways are obvious.
