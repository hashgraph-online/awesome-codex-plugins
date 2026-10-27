---
name: science-aaas
description: Prepare manuscripts for Science and the Science family of journals (Science, Science Advances, Science Translational Medicine, Science Robotics, Science Immunology, Science Signaling), covering Research Article vs Report formats, abstracts and one-sentence summaries, reference and notes style, Supplementary Materials, data/code policies, figure requirements and the initial-submission vs revision workflow. Use when targeting a Science journal, converting a manuscript to Science style, or checking a submission against Science author instructions.
license: MIT
compatibility: No runtime dependencies. Word or the Science LaTeX template (check the author instructions for the current template).
metadata:
  version: "1.0"
  category: journal-formats
  maintainer: Kalaris Labs
  author: Kalaris Labs (Sayan Chowdhury)
  tags: Science, AAAS, Science Advances, journal formatting, submission
---

# Science Family Journals

## Workflow

1. Identify the exact journal and article type, open its current author guidelines, and fill in the limits table below. Never rely on remembered limits.
2. Check whether a format-free first submission is allowed. If it is, spend effort on content and mandatory statements rather than layout.
3. Restructure the manuscript into the venue's front matter and sections (see below).
4. Prepare the required statements, figures and supplementary files.
5. Run the checklist, then assemble the submission package: manuscript, source files, figures, declarations and cover letter.

## Verify first (mandatory)

Open the current instructions for the exact journal and article type
(Science: https://www.science.org/content/page/instructions-preparing-initial-manuscript and the
research-article instructions linked from https://www.science.org/journal/science; Science Advances
has its own instructions). Record the limits before editing:

| Item | Limit (fill in from the instructions) |
|---|---|
| Abstract length | |
| Main text length, figures/tables, references for this article type | |
| One-sentence summary / teaser requirements | |
| Structured abstract (Research Article) requirements | |
| Supplementary Materials rules | |

## Article types (Science)

- **Research Article**: the full-length format. A structured summary may be required at acceptance.
- **Report**: shorter format for a single, important finding. Tight limits on text, figures and references.
- Reviews, Perspectives and Policy Forum are usually commissioned or proposed first.

Science Advances is open access with more generous length. Its structure is closer to a conventional
IMRaD paper, so check its specific template.

## Writing for Science

- The first paragraph must make a general scientific reader care. Minimize jargon and define terms.
- The abstract states the context, the finding and its significance. No references.
- One-sentence summary/teaser: a plain-language statement of the main finding (check length).
- Main text in continuous prose with brief subheadings. Methods are often in the Supplementary
  Materials (Materials and Methods). Check the article type.
- Figures: few and dense. Legends begin with a short title and describe n, statistics and error bars.

## References and notes

Science uses **numbered references in order of citation**, with notes and references in one
numbered list in its traditional style. References cited only in the Supplementary Materials
may have special rules. Use the Science CSL style or the template's bibliography style. Don't hand-format.

## Required elements (commonly)

- Acknowledgments with funding, author contributions, competing interests, and **data and materials
  availability** (all data needed to evaluate the conclusions must be available in the paper,
  the SM, or a public repository with accession numbers).
- Supplementary Materials as a single PDF (Materials and Methods, supplementary text, figures S1..., tables S1...),
  plus separate files for large data or movies.
- Statistics reported with n, test, and exact P values or intervals.
- Ethics approvals, trial registration, and code availability where relevant.
- Preprint disclosure (Science allows preprints on recognized servers; disclose at submission).

## Initial submission

Science accepts initial submissions in a simpler format, and full formatting is often
required only on revision. Check the "initial manuscript" instructions. Include a cover letter
that states significance for a broad audience (see `cover-letter-to-editor`) and suggested referees.

## Related skills

`abstract-and-title`, `cover-letter-to-editor`, `reproducibility-statement`, `venue-templates`,
`scientific-visualization`, `rebuttal-and-response-to-reviewers`.
