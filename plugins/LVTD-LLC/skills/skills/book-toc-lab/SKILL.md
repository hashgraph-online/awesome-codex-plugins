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

## Baseline

Treat a useful nonfiction book as a problem-solving product for a specific reader. The table of contents is the product design, not a decorative outline. Build and test the promise, scope, recommendation loop, and TOC before drafting so the manuscript has a clear job and a useful progression.

Use this skill to produce or improve a book plan that answers:

- Who is this book for?
- What painful or valuable problem does it help them solve?
- What should be different for the reader after each chapter?
- What does the book deliberately leave out?
- Why would a satisfied reader recommend it to a specific person in a specific situation?

## Reference Routing

Load only the files needed for the task:

| Need | Read |
|------|------|
| Core model, DEEP, promise, scope, recommendation loop | `references/core/knowledge.md` |
| Concrete planning and validation rules | `references/core/rules.md` |
| Before/after examples for scope and TOC titles | `references/core/examples.md` |
| Quick planning and review checklist | `references/core/checklist.md` |
| Step-by-step TOC validation with readers | `workflows/validate-toc.md` |

## Workflow

### 1. Lock The Reader Promise

Start with a one-paragraph book brief:

- **Target reader:** one recognizable type of person, not a broad market.
- **Current struggle:** the problem, confusion, risk, or opportunity that makes the book worth reading.
- **Book promise:** the useful outcome the book can credibly help create.
- **Starting assumptions:** what the reader already knows, has, or believes.
- **Success evidence:** what the reader can do, decide, avoid, or build after reading.

If these are vague, stop and refine them before outlining. A weak promise creates a weak TOC.

### 2. Set Scope Boundaries

Define both sides of the scope:

- **In scope:** what the book must cover to deliver the promise.
- **Out of scope:** adjacent topics that are tempting but distract from the promise.
- **Prerequisites:** what should be taught, assumed, or linked elsewhere.
- **Depth line:** where the book should go deep versus where a concise pointer is enough.

Prefer a narrow book that fully solves one reader problem over a broad book that surveys many topics without changing the reader's life.

### 3. Check Recommendability

Write the recommendation story:

- What situation makes the reader complain, search, ask for help, or give advice?
- Who hears that problem and naturally recommends this book?
- Why is this book the obvious solution for that person, not merely one option among many?
- What outcome would make the reader confident enough to recommend it?

If the story is weak, adjust the reader, promise, or scope before drafting.

### 4. Draft A Takeaway-First TOC

Create chapters as reader takeaways, not clever titles. For each chapter, capture:

- Chapter title.
- Reader question or problem.
- Main takeaway.
- Practical output, decision, habit, checklist, model, or skill the reader gains.
- Why this chapter belongs here.
- What confusion or objection it resolves.

Use this table while designing:

```text
Chapter | Reader problem | Takeaway | Reader output | Why now? | Risk if missing
```

### 5. Shape The Reader Journey

Order chapters by reader progress, not author knowledge. A strong sequence usually moves through:

1. Orientation: help the reader recognize the problem and adopt the right mental model.
2. Foundation: teach the few concepts needed for later action.
3. Action: walk through the core work.
4. Judgment: show how to make tradeoffs, avoid mistakes, and adapt.
5. Integration: help the reader apply, maintain, or extend what they learned.

Avoid front-loading background that the reader does not need yet. Put value early enough that the reader feels progress in the first chapter.

### 6. Pressure-Test The TOC

Run these checks before drafting:

- **Promise check:** every chapter directly supports the book promise.
- **Reader check:** the TOC uses reader problems and outcomes, not only author categories.
- **Missing step check:** no chapter assumes a concept, decision, or tool the reader has not received.
- **Boredom check:** remove or compress chapters whose payoff is delayed, obvious, or mostly throat-clearing.
- **Confusion check:** identify where a reader may ask "why does this matter?" or "what do I do with this?"
- **Skepticism check:** mark claims that will need proof, examples, or caveats.
- **Recommendation check:** describe the exact person a happy reader would recommend the book to and the sentence they would use.

Revise until each chapter earns its place.

### 7. Test Before Drafting

When practical, validate the TOC with real or simulated readers before writing full chapters:

- Teach from the TOC in a short call, workshop, article series, or outline review.
- Ask readers where they get confused, bored, skeptical, or excited.
- Ask what they expected to see but did not.
- Ask which chapter they would read first and which they might skip.
- Ask what outcome would make the book worth recommending.

Treat negative feedback as design data. Update the TOC before turning it into prose.

## Output Format

When asked to create or improve a TOC, return:

1. Book brief: reader, problem, promise, scope, out-of-scope.
2. Recommendation story: trigger, recommender, recommended reader, why this book.
3. Recommended TOC with chapter-level reader problems and takeaways.
4. Reader journey notes explaining the order.
5. Risk list: missing prerequisites, vague chapters, likely confusion, likely boredom.
6. Validation plan: 3-7 concrete ways to test the TOC before drafting.

## Quality Bar

A good TOC should feel useful even before the book exists. A reader should be able to scan it and understand what the book helps them accomplish, whether it is for them, and why the chapter sequence makes sense.

Do not optimize for literary cleverness before usefulness. Clever titles are acceptable only after the reader promise and chapter takeaways are obvious.
