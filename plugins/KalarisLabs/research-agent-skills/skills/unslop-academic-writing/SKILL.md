---
name: unslop-academic-writing
description: Remove AI slop from research writing so papers, theses, grant proposals, reviews and rebuttals read as written by a careful human expert. Covers stock vocabulary (delve, tapestry, pivotal, underscores), empty emphasis, hedge stacks, formulaic signposting, "not only X but also Y" constructions, em-dash pileups, monotone rhythm, and claims vaguer than the data. Use when drafting or revising academic text with an AI assistant, when a draft "sounds like ChatGPT", before submission, or to match an author's own voice. Includes a zero-dependency slop linter for Markdown, LaTeX, text and Word files.
license: MIT
compatibility: Python 3.9+ standard library for scripts/slop_check.py.
metadata:
  version: "1.0"
  category: research-writing
  maintainer: Kalaris Labs
  author: Kalaris Labs (Sayan Chowdhury)
  tags: AI slop, academic writing, tone, voice, humanize, clarity, editing, scientific writing
---

# Unslop Academic Writing

Slop is prose that is fluent but says less than it seems to. Readers, reviewers and
editors now recognize it on sight, and it costs credibility even when the science
is sound. The fix is **specificity**: every sentence should carry information a
generic paper on the topic would not.

This skill is about **clarity and authorship, not about disguising AI use**. Follow
the venue's policy on AI assistance (most require disclosure, see `reproducibility-statement`).
The author remains responsible for every claim.

## Workflow

1. **Measure.** Run the linter on the draft (or a section):

   ```bash
   python scripts/slop_check.py manuscript.tex
   python scripts/slop_check.py intro.md --json > slop.json
   ```

   It ignores math, citations, code and markup. Index bands: < 5 clean, 5-15 some slop,
   15-30 heavy, > 30 severe. Each finding has a line number and a rewrite hint.

2. **Fix content first, words last.** Work top-down. Polishing vocabulary in a paragraph
   that should not exist is wasted effort.

   | Level | Question | Typical fix |
   |---|---|---|
   | Claim | Does each paragraph make one claim a specialist would find non-obvious? | Cut paragraphs that restate the field; merge duplicates |
   | Evidence | Is every claim tied to a number, citation, figure or method? | Replace "significantly improves" with the effect size, interval and test |
   | Structure | Does the logic carry the connection, or do signposts ("Moreover") fake it? | Reorder sentences so each follows from the last; delete connective filler |
   | Rhythm | Do sentence lengths vary with content? | Short sentence for the key finding; longer ones for mechanism and caveats |
   | Words | Stock vocabulary, hype, stacked hedges? | Use the hints and [references/patterns.md](references/patterns.md) |

3. **Preserve what matters.** Never change numbers, units, citations, technical terms,
   defined abbreviations or the strength of a claim while "unslopping". Hedges that
   reflect genuine uncertainty stay. Remove only the *second* hedge in a stack.

4. **Match the author's voice.** Ask for 1-3 pages the author wrote before using AI (a
   previous paper or thesis chapter). Note their sentence length, use of "we"/"I", preferred
   transitions and terminology, then keep the revision within that range. Follow the
   discipline norms in [references/discipline-voice.md](references/discipline-voice.md).

5. **Re-measure and read aloud.** Target an index under 5 for abstracts and introductions,
   under 10 for methods-heavy sections. The linter is a floor, not a judge: finish by
   reading the text as a skeptical reviewer.

## Rewrite rules (apply in order)

1. **Delete the frame, keep the point.** "It is important to note that X" → "X".
2. **Replace abstraction with the specific thing.** "a wide range of tasks" → "12 of the 14 benchmark tasks".
3. **Replace evaluation with evidence.** "a remarkable improvement" → "a 9.4-point improvement (95% CI 7.1-11.7)".
4. **Name the mechanism, not the role.** "plays a pivotal role in" → "is required for", "accounts for 40% of".
5. **One hedge, sized to the evidence.** "may potentially suggest" → "suggests" (strong data) or "is consistent with" (weak data).
6. **State the contrast directly.** "not only X, but also Y" → "X and Y", or keep only the stronger point.
7. **Use the verb.** "perform an analysis of" → "analyse"; "provide a description" → "describe".
8. **Let structure replace signposts.** Delete "Moreover/Furthermore/Additionally" where the logical relation is clear.
9. **Punctuate normally.** Most em dashes become commas, colons, parentheses or full stops.
10. **Vary rhythm deliberately.** After two long sentences, write a short one that states the takeaway.

## Before and after

> **Before:** In today's rapidly evolving landscape, single-cell technologies play a pivotal role in
> unraveling the intricate tapestry of cellular heterogeneity. It is important to note that our novel
> framework significantly outperforms existing methods, paving the way for groundbreaking discoveries.
>
> **After:** Single-cell RNA-seq atlases now exceed 10 million cells, but cluster labels still disagree
> between annotation tools on about 20% of cells. Our method reduced this disagreement to 7% on three
> held-out atlases (paired t-test, p < 0.01), mainly by resolving T-cell subtypes that marker-based tools merge.

## Integrity rules

- Never fabricate specifics to replace vague text. If the draft lacks the number or citation, ask the author or mark a placeholder such as `[N = ?]`.
- Verify that each rewritten sentence says the same thing as the original, at the same strength.

## What the linter cannot judge

Accuracy, novelty, whether a citation supports the sentence, or whether the argument is
right. Pair this skill with `citation-verification`, `scientific-critical-thinking` and a
human co-author's read.

## Related skills

`scientific-writing`, `ml-paper-writing`, `abstract-and-title`, `rebuttal-and-response-to-reviewers`,
`cover-letter-to-editor`, `peer-review`, `reproducibility-statement`.
