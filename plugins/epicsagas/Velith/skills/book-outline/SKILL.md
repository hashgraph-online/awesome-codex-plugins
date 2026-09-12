---
name: book-outline
description: "Phase 2: Outlining. Build the chapter-by-chapter outline with genre structure, create the book bible, validate structure with book-architect, and get author approval."
argument-hint: "[project-dir]"
---

# Phase 2: Outlining

Goal: an outline detailed enough that each chapter can be drafted in full context without inventing structure, and a bible that keeps twenty chapters telling one story or making one argument.

Read `PRD.md`, `STYLE.md`, `ideation.md`, `sources/INDEX.md`, the genre skill, and `${CLAUDE_PLUGIN_ROOT}/skills/loom/quality-bar.md`.

## Process

1. **Invoke `book-architect`** with the project directory. It produces `outline.md` (draft) and `bible.md` (initial), then validates its own structure and writes the score and issues into `outline.md`'s `## Validation` section.
2. **Review the validation.** If the score is below 8/10 or any Critical issue remains, have book-architect revise once. If still below, surface the issues to the author instead of iterating blindly.
3. **Author checkpoint.** Present: the structural shape (one paragraph), the chapter list with one-line purposes, the pacing map, the top three risks the architect flagged, and the bible summary. Ask for approval or changes. Required stop.
4. On approval, add `## Approval` to `outline.md` with the date and any author notes. The router treats an outline without this section as unapproved.

## What a chapter spec must contain

The chapter-writer will draft from this spec plus the full manuscript so far. Anything missing here gets invented inconsistently. Per chapter:

- **Title** (working) and slug
- **Purpose** — what this chapter changes for the reader. If two chapters have the same purpose, one is redundant.
- **Entry state** — where the reader (and, for fiction, the protagonist) is at the start: what they know, want, fear, believe
- **Exit state** — same, at the end. The delta is the chapter.
- **Pull** — the question or tension that carries the reader through this chapter
- **Content** — for fiction: 2-5 scene seeds (situation, turn, what is at stake); for nonfiction: the claims made, evidence used (source IDs), the example or story that anchors it; for technical: concepts, the code artifact built, the failure shown
- **Sets up / pays off** — references to other chapters by number
- **Must not** — repetitions to avoid, things the reader must not learn yet, tonal limits
- **Length target** and difficulty (nonfiction/technical)
- **Sources** — IDs from `sources/INDEX.md`

## Structure by genre

Genre skills carry the options. The architect chooses a structure and states why in `outline.md`; it does not apply a template silently. Shapes are tools, not rules: a 15-beat sheet that produces fifteen equal chapters has been applied, not used.

- Fiction: three-act, Save the Cat, Hero's Journey, Story Grid, or a bespoke shape derived from the premise. Also: POV plan, timeline, subplot braid.
- Nonfiction: problem → principles → practice → advanced; or narrative spine with argument chapters; or question-driven. Also: evidence map, recurring example strategy.
- Technical: intro → foundations → practice → advanced → reference, with a running project that the reader builds across chapters.
- Screenplay, poetry, game, academic: see the genre skill.

## The bible

`bible.md` is created here and updated by every drafting and editing agent. Initial sections:

- **Characters / Key concepts** — per entry: name, role, what they want, what they fear, how they speak (fiction); definition, first-introduced chapter, dependencies (nonfiction/technical)
- **World and term rules** — settings, systems, terminology decisions, spelling and naming conventions, 존댓말 map (Korean fiction)
- **Timeline** — dated or relative sequence of events (fiction), or chronology of the field/story (nonfiction)
- **Motifs and images reserved** — recurring images, phrases, or examples and where they are allowed to appear
- **Open threads** — setups awaiting payoff, with the chapter that must pay them
- **Chapter ledger** — empty; chapter-writer appends one entry per chapter drafted

## Visual plan

If the book will carry images (nonfiction and technical almost always; fiction by author choice; see the genre skill's Visuals section), the outline includes a `## Figure plan`: per chapter, the figures and illustrations with a purpose sentence, type, maker (`figure-engineer` / `illustrator` / photo), and data source. This is the seed of `visuals/manifest.json`; `art-director` refines it in `/book-visuals plan`. A chapter spec that needs a diagram says so, and the chapter-writer places the reference and caption while drafting.

## Output

`outline.md`: Structure and rationale, Pacing map, Chapter specs, Cross-reference map (DAG for technical/nonfiction; setup/payoff table for fiction), Figure plan (if any), Validation (score, issues, recommendations), Approval.

`bible.md` as above.

## Gate

`outline.md` has `## Approval`. Architect score ≥ 8/10 with no Critical issues, or author explicitly accepted the remaining issues. Every chapter spec has purpose, entry/exit state, pull, and content. `bible.md` exists with at least the characters/concepts and term rules sections filled.

## Post-completion

```bash
node ${CLAUDE_PLUGIN_ROOT}/velith.mjs scan [project-dir]
```
