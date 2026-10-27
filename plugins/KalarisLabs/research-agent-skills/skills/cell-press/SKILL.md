---
name: cell-press
description: Prepare manuscripts for Cell Press journals (Cell, Molecular Cell, Neuron, Immunity, Cell Reports, Cell Systems, iScience, Cell Metabolism, Current Biology and others), covering Summary, Highlights, eTOC blurb and graphical abstract, STAR Methods with the Key Resources Table, resource availability (lead contact, materials, data and code), figure and statistics requirements, and Cell Press formatting at submission vs revision. Use when targeting a Cell Press journal, writing highlights or a graphical abstract, or converting methods into STAR Methods.
license: MIT
compatibility: No runtime dependencies.
metadata:
  version: "1.0"
  category: journal-formats
  maintainer: Kalaris Labs
  author: Kalaris Labs (Sayan Chowdhury)
  tags: Cell Press, Cell, Neuron, Cell Reports, STAR Methods, graphical abstract, highlights, journal formatting
---

# Cell Press Journals

## Workflow

1. Identify the exact journal and article type, open its current author guidelines, and fill in the limits table below. Never rely on remembered limits.
2. Check whether a format-free first submission is allowed. If it is, spend effort on content and mandatory statements rather than layout.
3. Restructure the manuscript into the venue's front matter and sections (see below).
4. Prepare the required statements, figures and supplementary files.
5. Run the checklist, then assemble the submission package: manuscript, source files, figures, declarations and cover letter.

## Verify first (mandatory)

Each journal has its own author guide (e.g. https://www.cell.com/cell/authors, and the STAR Methods
guide at https://www.cell.com/star-methods). Confirm the current limits for your journal and article type:

| Item | Limit (fill in) |
|---|---|
| Summary length | |
| Highlights: number of bullets and characters per bullet | |
| eTOC blurb length | |
| Main text / character count, figures, references | |
| Supplemental information rules | |

## Front matter unique to Cell Press

- **Summary**: a single paragraph (commonly up to about 150 words) for a broad audience,
  without references. Context → gap → what you did → key findings → significance.
- **Highlights**: a short list of bullet points (commonly 3-4) with a strict per-bullet character
  limit (commonly about 85 characters including spaces). Each is a standalone finding, not a method.
- **eTOC blurb / In Brief**: a short third-person paragraph for non-specialists: "Smith et al. show that ...".
- **Graphical abstract**: a single square-ish panel summarizing the main message. Read in one direction,
  minimal text, no data plots copied from figures, no journal-style legends.

See `abstract-and-title` for writing techniques.

## STAR Methods (Structured, Transparent, Accessible Reporting)

Required for research papers in most Cell Press journals. Standard headings (verify the current set):

1. **Resource availability**: Lead contact, Materials availability, Data and code availability
   (accessions, DOIs, repository links, and a statement that any additional information is available from the lead contact).
2. **Key Resources Table (KRT)**: a structured table of antibodies, bacterial/viral strains, biological
   samples, chemicals, critical commercial assays, deposited data, experimental models (cell lines,
   organisms/strains), oligonucleotides, recombinant DNA, software and algorithms, and other items, with
   **source and identifier** (RRIDs, catalog numbers, accessions) for each row.
3. **Experimental model and study participant details**: species, strain, sex, age, source, husbandry,
   ethics approvals, and for human participants demographics and consent.
4. **Method details**: step-by-step, citing protocols where they exist (protocols.io DOIs).
5. **Quantification and statistical analysis**: software, tests, what n represents, definitions of
   centre/dispersion, significance thresholds, and where the statistical details appear in figure legends.

Tips: use RRIDs (https://scicrunch.org/resources) for antibodies, cell lines, organisms and software.
Keep main-text Methods out, since STAR Methods replaces them.

## Figures and data

- Figures are multi-panel with consistent styling. Legends state n, statistical test and error bars.
- Show individual data points where feasible. Avoid bar-only plots for small n.
- Image integrity: retain unprocessed images. Apply adjustments uniformly across the image.
- Deposit sequencing, proteomics and structures in community repositories before submission.

## Process

- Many Cell Press journals allow a **free-format first submission**. Full formatting (STAR Methods,
  KRT, highlights) is needed at revision. Check the journal's policy.
- Presubmission inquiries are welcomed by several journals (see `cover-letter-to-editor`).
- Preprints are allowed. Disclose them at submission.
- Cell Press offers transfers between its journals with reviews.

## Related skills

`venue-templates` (Cell style reference), `abstract-and-title`, `reproducibility-statement`,
`scientific-visualization`, `statistical-analysis`, `protocolsio-integration`, `cover-letter-to-editor`.
