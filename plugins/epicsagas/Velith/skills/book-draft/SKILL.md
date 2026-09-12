---
name: book-draft
description: "Phase 3: Drafting. Voice lock on a sample chapter, then sequential full-context chapter drafting with draft-critique-revise, bible ledger updates, and periodic continuity checks."
argument-hint: "[project-dir] [chapter-number|all] [--force] [--voice-lock]"
---

# Phase 3: Drafting

Goal: a complete manuscript in one voice, internally consistent, each chapter already revised once against the quality bar. Drafting done this way needs an editor; drafting done to word count needs a rewrite.

Read `${CLAUDE_PLUGIN_ROOT}/skills/loom/quality-bar.md`, then `PRD.md`, `STYLE.md`, `outline.md`, `bible.md`.

Refuse to draft if `outline.md` lacks `## Approval`. Point the author to `/book-outline`.

## Step 0: Voice lock (once per book)

If `STYLE.md`'s `## Voice Lock` says pending:

1. Choose the sample chapter: chapter 1 by default, or the chapter the author names. For fiction, the architect may recommend a mid-book chapter if chapter 1 is atypical (prologue, framing device).
2. Run `scene-generator` (fiction) then `chapter-writer` on that chapter exactly as in normal drafting.
3. Present the chapter to the author with the writer's own critique scores. Ask: is this the voice? What is off? Required stop.
4. On approval, record in `STYLE.md` under `## Voice Lock`: date, chapter, the author's notes, and 2-3 quoted passages from the approved chapter that best represent the voice. Chapter-writer reads these on every later chapter.
5. On rejection, revise the fingerprint per the author's notes, regenerate, present again. Up to three rounds, then ask the author to supply or edit a sample directly.

`--voice-lock` forces this step even if a lock exists (voice change mid-book).

## Step 1: Order and concurrency

**Narrative genres** (fiction, screenplay, game, memoir, narrative nonfiction, poetry sequences): strictly sequential. Chapter N requires chapter N-1 saved with `status: draft` or later and a bible ledger entry.

**Technical, reference, academic**: read the dependency DAG in `outline.md`. Chapters with no unsatisfied prerequisites and no mutual references may draft concurrently, at most 3. Each concurrent writer still reads all completed chapters.

Never run two chapter-writers on the same chapter.

## Step 2: Per-chapter loop

For each chapter to draft (skip existing unless `--force`):

1. **Fiction only:** invoke `scene-generator` → `drafts/ch{NN}-scenes.md` (a plan, not prose).
2. Invoke `chapter-writer` with the chapter number. It reads everything, drafts, critiques, revises, writes `drafts/ch{NN}-{slug}.md`, appends the chapter ledger in `bible.md`, and writes `.velith/critiques/ch{NN}.md`.
3. Verify the writer's self-reported scores. If any axis < 6 after its revision, run it again with the critique as additional input before moving on.
4. If the chapter spec lists figures, the writer has placed `![alt](../visuals/figures/{id}.svg)` references with captions at the right spots. Invoke `figure-engineer` for those ids now (technical and nonfiction) so the figure exists while the chapter is fresh; illustrations wait for the look lock in `/book-visuals`.
5. `node ${CLAUDE_PLUGIN_ROOT}/velith.mjs scan [project-dir]` so the dashboard updates.

## Step 3: Continuity checks

Invoke `continuity-editor` after chapters 3, then every 4 chapters, then after the final chapter. It reads the whole manuscript against the bible. Minor issues are fixed in place; Critical and Major issues are reported and, for narrative genres, must be resolved before drafting continues (a contradiction in chapter 5 propagates into 6 through 20).

## Chapter file format

```markdown
---
chapter: 7
title: "..."
slug: "..."
word_target: 4000
words: 4120
status: draft        # draft | edited | final
revision: 1
critique_score: {voice: 7, structure: 7, depth: 8, specificity: 7, reader: 7}
created: 2026-09-04
updated: 2026-09-04
---

# Chapter title

Body...
```

Korean projects count characters excluding whitespace; `count_unit: chars` in PRD.

## Gate

All chapters in `outline.md` exist as drafts. Every chapter has a critique with all five axes ≥ 6. Bible ledger has an entry per chapter. Last continuity report has no unresolved Critical issues. Voice lock recorded.

## Resuming

`/book-draft` with no chapter argument resumes from the first missing chapter. `/book-draft 12` drafts chapter 12 only (refuses for narrative genres if 11 is missing). `/book-draft 12 --force` redrafts 12 and warns that later chapters may need continuity review.

## Post-completion

```bash
node ${CLAUDE_PLUGIN_ROOT}/velith.mjs scan [project-dir]
```
