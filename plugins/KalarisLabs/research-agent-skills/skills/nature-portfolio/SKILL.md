---
name: nature-portfolio
description: Prepare manuscripts for Nature and Nature Portfolio journals (Nature, Nature Communications, Nature Methods, Nature Biotechnology, Scientific Reports and other Nature-branded titles), covering article types, summary paragraph vs abstract, main-text and display-item limits, Methods and Extended Data, reporting summaries, data/code availability, figure preparation, references and presubmission enquiries. Use when targeting any Nature Portfolio journal, reformatting a paper for one, or checking a submission against its guidelines.
license: MIT
compatibility: No runtime dependencies. Word or LaTeX (Nature Portfolio LaTeX template on Overleaf).
metadata:
  version: "1.0"
  category: journal-formats
  maintainer: Kalaris Labs
  author: Kalaris Labs (Sayan Chowdhury)
  tags: Nature, Nature Communications, Scientific Reports, journal formatting, submission
---

# Nature Portfolio Journals

## Workflow

1. Identify the exact journal and article type, open its current author guidelines, and fill in the limits table below. Never rely on remembered limits.
2. Check whether a format-free first submission is allowed. If it is, spend effort on content and mandatory statements rather than layout.
3. Restructure the manuscript into the venue's front matter and sections (see below).
4. Prepare the required statements, figures and supplementary files.
5. Run the checklist, then assemble the submission package: manuscript, source files, figures, declarations and cover letter.

## Verify first (mandatory)

Requirements differ **by journal and article type** and are revised often. Open the
current guide for the exact journal (e.g. https://www.nature.com/nature/for-authors and its
formatting guide, or `https://www.nature.com/<journal>/submission-guidelines`). Record what you
found before editing:

| Item | Limit for this journal/type (fill in from guide) |
|---|---|
| Abstract / summary paragraph length, referenced or not | |
| Main text length (what it includes and excludes) | |
| Display items (figures + tables) | |
| Reference limit | |
| Methods length / placement | |
| Extended Data / Supplementary Information rules | |
| Title length | |

Many Nature Portfolio journals accept a **format-free initial submission**. Check whether
strict formatting is needed only at revision. Don't spend effort formatting prematurely.

## Structure (Nature-style research Article)

- **Title**: short, no abbreviations, no punctuation-heavy constructions. Declarative titles are common.
- **Summary paragraph** (Nature) / **Abstract** (most other titles): Nature's summary paragraph is
  a single referenced paragraph that introduces the field for non-specialists, states the gap,
  then gives the main result and its implication. Other titles use a conventional unreferenced abstract.
- **Main text**: minimal or no "Introduction" heading in Nature. Results use short subheadings
  that state findings. Discussion is brief. Written for a broad scientific audience.
- **Methods**: after the main text (online Methods). Detailed enough to reproduce. Includes statistics.
- **Figures**: few, dense, multi-panel. Legends begin with a one-sentence title and define n,
  statistical tests and error bars.
- **Extended Data**: a limited number of extra figures/tables (check the limit), each with a legend.
  Additional material goes in Supplementary Information.

## Mandatory elements (commonly required)

- **Reporting Summary** (life sciences, behavioural, ecological research) and editorial policy checklists.
- **Data availability** and **code availability** statements with accession codes/DOIs (see `reproducibility-statement`).
- **Source Data** files for graphs where requested.
- **Author contributions**, **competing interests**, **acknowledgements**, **corresponding author**.
- Statistics: exact n, what n is (biological vs technical replicates), test used, exact P values where possible, and definitions of centre and error bars.
- Image integrity: no selective enhancement. Keep unprocessed blots/gels for Source Data.
- Ethics approvals and consent statements. Clinical trial registration where applicable.

## References and style

Nature style: numbered superscripts in order of first citation. References list includes
all authors up to a threshold, then et al., with journal abbreviations. Use the Nature CSL style
(Zotero/Pandoc) or the Nature Portfolio LaTeX template's `.bst` (`naturemag`/template default). Don't hand-format.

## Figures

- Size to final column widths (single/double column; check the guide), with sans-serif fonts at
  legible sizes, vector formats for line art, and sufficient resolution for images.
- Colour-blind-safe palettes. Avoid red/green contrasts. See `scientific-visualization`.
- No figure titles inside the image. The title goes in the legend.

## Process tips

- **Presubmission enquiry**: optional for many titles. Send the abstract plus a significance pitch (see `cover-letter-to-editor`).
- **Transfers**: rejected manuscripts can transfer within the portfolio with reviews. Nature Communications and Scientific Reports are common destinations.
- **Preprints** are allowed (arXiv, bioRxiv, medRxiv, Research Square). Disclose them in the cover letter.
- **Embargo**: accepted papers are under press embargo until publication.

## Related skills

`venue-templates` (bundled Nature LaTeX scaffold), `abstract-and-title`, `cover-letter-to-editor`,
`reproducibility-statement`, `scientific-visualization`, `statistical-analysis`, `rebuttal-and-response-to-reviewers`.
