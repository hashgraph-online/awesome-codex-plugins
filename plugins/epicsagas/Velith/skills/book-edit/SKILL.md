---
name: book-edit
description: "Phase 4: Editing. Fact-check (nonfiction), assessment, developmental edit, line edit, copy edit, proofread, then a cold read by simulated readers that issues the readiness verdict. Rewrites the manuscript; does not only file reports."
argument-hint: "[project-dir] [stage 0-6|all] [chapter-file]"
---

# Phase 4: Editing

Goal: a manuscript that passes a cold read by its target readers. Editing here means rewriting. Each stage snapshots the drafts, changes them, and files a report of what changed and why.

Read `${CLAUDE_PLUGIN_ROOT}/skills/loom/quality-bar.md`. Every stage reads the whole manuscript, `STYLE.md` (voice lock passages), `bible.md`, and the genre skill.

Refuse to run if any outlined chapter is missing. Editing an incomplete book fixes the wrong things.

## Stages

| # | Stage | Who | Rewrites? | Report |
|---|-------|-----|-----------|--------|
| 0 | Fact check (nonfiction, technical, academic, and fiction with real-world claims) | `fact-checker` | Yes, removes or corrects unverifiable claims | `edits/00-fact-check.md` |
| 1 | Editorial assessment | skill (you) | No | `edits/01-assessment.md` |
| 2 | Developmental edit | skill + `chapter-writer` for rewrites, `continuity-editor` after | Yes, chapter-level | `edits/02-developmental.md` |
| 3 | Line edit | `style-doctor` then skill | Yes, paragraph and sentence level | `edits/03-line-edit.md` |
| 4 | Copy edit | skill | Yes, mechanical | `edits/04-copy-edit.md` |
| 5 | Proofread | skill | Yes, final | `edits/05-proofread.md` |
| 6 | Readiness | `beta-reader` | No | `edits/06-readiness-report.md` (also `edits/readiness-report.md`) |

Before every rewriting stage: `node ${CLAUDE_PLUGIN_ROOT}/velith.mjs snapshot [project-dir] stage{N}`.

After each stage: update chapter frontmatter `status: edited`, bump `revision`, run `scan`.

### Stage 0 — Fact check

Invoke `fact-checker`. It builds a claim ledger, verifies against `sources/` and the web, and edits drafts to remove or correct what cannot be verified. It also reconciles every figure's labels and plotted values with the text and the data files in `sources/`. A claim that would embarrass the author in a review is a Critical. Fiction runs this stage only if the bible flags real-world claims (real places, real history, real science). Stage 0 runs before anything else because a developmental edit built on a false claim is wasted.

### Stage 1 — Editorial assessment

Read the whole book once at reading speed (cold-read protocol). Produce the macro diagnosis:

- Where the book delivers its promise and where it does not (against `PRD.md` reader promise)
- Pacing map: per chapter, engagement 1-5 and why; identify the sag
- Structural redundancies and gaps (two chapters doing one job; a job nobody does)
- Proportion: is the setup too long, the ending too fast
- Voice consistency across chapters (quote a line from chapter 2 and one from chapter 18 side by side)
- Five-axis score for the whole manuscript
- Ordered list of developmental interventions with expected impact

No rewriting in this stage. The report is the plan for stage 2.

### Stage 2 — Developmental edit

Execute the stage 1 plan. Interventions, in order of scale:

- **Restructure** (reorder, merge, split, cut chapters): requires author approval. Present the proposal with rationale and the concrete new chapter list. Required stop.
- **Rewrite chapter** (purpose unchanged, execution replaced): invoke `chapter-writer` with the assessment findings for that chapter as extra input and `--force`. It reads the whole book, so it will match the voice lock.
- **Add or remove scenes/sections** within a chapter: do it directly, in the voice, then update the bible ledger.
- **Deepen** (a character who acts without wanting; an argument missing its strongest objection): targeted rewrites of the passages, not the chapter.

After all interventions, invoke `continuity-editor` on the full manuscript. Report: what changed per chapter, what was left as-is and why, and the new pacing map.

### Stage 3 — Line edit

Invoke `style-doctor`. It measures (`velith.mjs metrics`), reads, rewrites paragraphs and sentences in place, and reports before/after with metrics. Then do your own line pass on anything it flagged as "author decision": sentences whose problem is meaning, not style.

Line-edit priorities: rhythm uniformity, the structural tells, emotional tells, dialogue that answers, figurative density against the fingerprint, paragraphs that end on a punch, Korean 번역투 and ~것이다 endings, ~5% trim of every chapter by cutting what the reader already knows.

### Stage 4 — Copy edit

Mechanical consistency against `bible.md` and `STYLE.md`: spelling of names and terms, hyphenation, number style, capitalization, quotation marks, 띄어쓰기, tense agreement, heading levels, code formatting (technical), citation format (academic), cross-references that point to the right chapter, figure numbering and caption format, every figure referenced in the text before it appears. Run `node ${CLAUDE_PLUGIN_ROOT}/velith.mjs images check [project-dir]` and fix unresolved references and missing alt text. Fix directly. Report only counts by category plus anything ambiguous for the author.

### Stage 5 — Proofread

Final pass on the revised text: typos, doubled words, orphaned formatting, markdown artifacts, missing scene breaks, dialogue punctuation, image references that resolve. Fix directly. Then set every chapter `status: final`.

### Stage 6 — Readiness

Invoke `beta-reader`. It cold-reads the whole manuscript as three target readers and one genre expert, writes `edits/06-readiness-report.md` with per-chapter engagement, put-down points, confusion log, AI-feel log with quotes, comp comparison, five-axis scores, and a verdict.

- `verdict: PASS` — write `edits/editorial-report.md` summarizing all stages and the scores. Phase complete.
- `verdict: REVISE` — the report includes a prioritized fix list. Apply the fixes (stage 2 or 3 interventions as appropriate), then rerun stage 6. Maximum two loops, then present the report to the author with the remaining issues and ask whether to override or continue. Required stop.

Copy the final report to `edits/readiness-report.md` (the router and dashboard read this path).

## Running a single stage or chapter

`/book-edit 3` runs only the line edit. `/book-edit 3 drafts/ch07-x.md` line-edits one chapter (still with full-book context). Snapshots and reports are still written.

## Gate

`edits/readiness-report.md` has `verdict: PASS` (or an author override recorded in `edits/editorial-report.md`). All chapters `status: final`. Stage reports 01-06 exist (00 for nonfiction). No unresolved Critical issues in the last continuity or fact-check report.

## Post-completion

```bash
node ${CLAUDE_PLUGIN_ROOT}/velith.mjs scan [project-dir]
```
