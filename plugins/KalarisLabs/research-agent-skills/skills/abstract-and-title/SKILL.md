---
name: abstract-and-title
description: Write and sharpen research paper titles, abstracts (structured and unstructured), keywords, highlights, significance statements, graphical-abstract text and lay summaries. Use when drafting or revising an abstract to a word limit, turning results into a one-sentence contribution, choosing between candidate titles, writing Cell/Elsevier highlights, a PNAS significance statement or a plain-language summary, or optimizing discoverability (keywords, search terms).
license: MIT
compatibility: No runtime dependencies.
metadata:
  version: "1.0"
  category: research-writing
  maintainer: Kalaris Labs
  author: Kalaris Labs (Sayan Chowdhury)
  tags: abstract, title, keywords, highlights, significance statement, lay summary, scientific writing
---

# Titles, Abstracts and Summary Text

Most readers, editors and reviewers decide from the title and abstract alone.
They are also what search engines and indexing services see. Write them last,
from the finished results, and revise them more than any other part of the paper.

## Inputs to collect first

- The single main finding, with its key number (effect size, accuracy, p-value/CI, sample size).
- The target venue's limits: abstract word count, structured vs. unstructured, title length,
  keyword count, highlights/significance requirements. **Look these up in the venue's current
  author guidelines** (the `venue-templates` skill and journal-format skills help). Never assume.
- Who reads it: specialists (field venue) or broad scientists (Nature, Science, PNAS).

## Abstract: the five-move structure

Unstructured abstracts still follow these moves. Structured ones label them.

| Move | Share | Content |
|---|---|---|
| Context | 1 sentence | The broader problem, in terms the venue's readers care about |
| Gap | 1 sentence | What is unknown, unsolved or wrong. Make the gap concrete |
| Approach | 1-2 sentences | What you did: design, data, method, with the essential scale (n, datasets) |
| Results | 2-3 sentences | The main findings **with numbers**. Lead with the most important |
| Implication | 1 sentence | What changes because of this, bounded by what the evidence supports |

Structured formats: IMRaD (Background/Methods/Results/Conclusions) for most clinical
journals. CONSORT-for-abstracts for RCTs. PRISMA 2020 for Abstracts for systematic reviews.
Some journals (e.g. BMJ) use their own headings, so match the journal exactly.

**Rules:**
- Numbers beat adjectives: "reduced error by 23% (95% CI 18-28%)" not "substantially reduced error".
- No citations, undefined abbreviations, or claims not in the paper. Define an abbreviation only if used ≥2 times.
- Past tense for what you did and found; present tense for established facts and implications.
- Keep it self-contained: a reader should understand it without the paper.
- Hit the limit without padding. If over, cut context before results.

## Titles

Generate 5-10 candidates across types, then pick against the criteria:

- **Declarative** (states the finding): "Metformin reduces hepatic glucose output via complex IV inhibition".
  Common in biology/medicine and broad journals.
- **Descriptive** (states the topic/method): "A graph neural network for retrosynthesis planning".
  Common in CS/engineering.
- **Question**: use sparingly, only when the answer is genuinely surprising.

Criteria: accurate (no overclaiming), specific (organism, method, population), contains
the 2-3 terms people search for, within the venue's length limit, no abbreviations
except universal ones (DNA, MRI), no puns that hide the content. Check that no existing
paper already has a near-identical title.

## Keywords

Choose terms **not already in the title** to widen discoverability: synonyms, the broader
field, method names, organism/population. Prefer controlled vocabulary where the venue
uses it (MeSH for biomedicine, ACM CCS concepts, IEEE Taxonomy, JEL codes, PACS/PhySH).

## Venue-specific extras

| Element | Typical form (verify per venue) |
|---|---|
| Highlights (Cell Press, Elsevier) | 3-5 bullets, each up to ~85 characters including spaces, results-focused |
| eTOC blurb / In Brief (Cell Press) | Short third-person paragraph for non-specialists |
| Significance statement (PNAS) | Plain-language paragraph on why the work matters to a broad audience |
| Author summary (PLOS) | Non-technical summary for a general reader |
| Lay / plain-language summary | Health and life-science journals, funders: no jargon, ~reading age 12-14 |
| Graphical abstract | One image read left-to-right or top-to-bottom: problem → approach → key result |
| Teaser / tweet-length | One sentence with the key number, for press and social media |

## Revision checklist

1. Does the first sentence establish why this matters to *this venue's* readers?
2. Is the gap stated explicitly, not implied?
3. Does every result sentence contain a number or concrete outcome?
4. Is every claim supported in the main text, at the same strength?
5. Word count within the limit (count it, don't estimate)?
6. Would a researcher from an adjacent field understand it?
7. Do title, abstract, highlights and conclusions tell the *same* story with the same numbers?

## Related skills

`scientific-writing`, `ml-paper-writing`, `cover-letter-to-editor`, `venue-templates`,
journal-format skills (`nature-portfolio`, `cell-press`, `plos`, ...), `scientific-slides`.
