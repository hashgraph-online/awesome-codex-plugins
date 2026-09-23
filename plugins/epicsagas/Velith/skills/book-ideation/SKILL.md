---
name: book-ideation
description: "Phase 1: Ideation. Stress-test the premise, research real comparable titles, generate and rank concepts, offer voice samples, and lock a single concept with a reader promise."
argument-hint: "[project-dir]"
---

# Phase 1: Ideation

Goal: one concept the author is excited about, that a real reader would pay for, that this author can write, and that no existing book already delivers. Everything downstream inherits this decision.

Read `PRD.md`, `STYLE.md`, `sources/INDEX.md`, and `${CLAUDE_PLUGIN_ROOT}/skills/book-{genre}/SKILL.md`.

## 1. Premise stress test

Before generating alternatives, interrogate what the author already has. Answer in writing:

- **Why this book?** What does it do that the reader cannot get elsewhere in an afternoon of searching?
- **Why now?** What changed in the world, the field, or the author's life that makes this timely? If nothing, that is fine, but say so.
- **Why this author?** What access, experience, or angle do they have? (For fiction: what obsession or wound is underneath the premise?)
- **What is the reader's objection?** The strongest reason a target reader would put it back on the shelf.
- **Where is the book most likely to fail?** Middle sag, a premise that runs out at 30%, research the author does not have, a voice that will tire.

## 2. Comparable titles

Research 5-8 real books the target reader has read or would consider instead. Use web search when available; otherwise rely on known titles and mark each as `verified` or `from memory`. **Never invent a title, author, or sales figure.** For each comp: title, author, year, what it does well, what it leaves undone, how this book differs. Write the matrix into `ideation.md`.

For Korean-market books, include domestic comps (교보/예스24/알라딘 bestseller lists, 밀리의 서재 trends) and translated comps separately.

## 3. Concept generation

Generate 5-10 concepts. Concepts are angles on the premise, not random alternatives. Each:

- Elevator pitch (two sentences, no adjectives doing the work)
- Reader promise (what they have at the end)
- The first chapter in one paragraph (this exposes weak concepts fast)
- Differentiation against the comps
- What the author would need to research or invent
- Risk (one line)

Score each on: clarity, reader value, differentiation, feasibility for this author, timeliness, and fit with the voice fingerprint. Rank. Recommend one and explain why in three sentences.

## 4. Voice samples (if STYLE.md has no voice sample)

Write three 200-word openings of the recommended concept in three distinct voices consistent with the fingerprint's constraints. Label the choices in each (distance, sentence rhythm, diction). The author's pick is recorded in `STYLE.md` under `## Voice Sample` and refines the fingerprint.

## 5. Author checkpoint

Present the ranked concepts, the recommendation, and the voice samples. Ask the author to choose (or merge up to three). This is a required stop. Do not proceed to outlining in the same turn without the author's choice.

## Output

`ideation.md`: Premise stress test, Comparable titles (verified/unverified flagged), Concepts (ranked, scored), Chosen concept with final reader promise and working title, Voice sample decision, Open risks to carry into outlining.

Update `PRD.md` with the chosen concept, working title, and reader promise.

## Gate

`ideation.md` exists with a `## Chosen Concept` section approved by the author. Comps matrix has at least five entries with verification status marked. Reader promise is one sentence.

## Post-completion

```bash
node ${CLAUDE_PLUGIN_ROOT}/velith.mjs scan [project-dir]
```
