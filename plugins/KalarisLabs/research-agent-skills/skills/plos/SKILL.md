---
name: plos
description: Prepare manuscripts for PLOS journals (PLOS ONE, PLOS Biology, PLOS Computational Biology, PLOS Genetics, PLOS Medicine, PLOS Pathogens, PLOS Neglected Tropical Diseases, PLOS Global Public Health and others), covering structure, abstract and author summary, Vancouver-style references, the mandatory data availability policy, ethics and financial disclosure statements, figure requirements (PACE), the PLOS LaTeX template, reporting guidelines and PLOS ONE's publication criteria. Use when targeting any PLOS journal or checking compliance with PLOS policies.
license: MIT
compatibility: No runtime dependencies. Word or the PLOS LaTeX template.
metadata:
  version: "1.0"
  category: journal-formats
  maintainer: Kalaris Labs
  author: Kalaris Labs (Sayan Chowdhury)
  tags: PLOS, PLOS ONE, open access, data availability, Vancouver, journal formatting
---

# PLOS Journals

## Workflow

1. Identify the exact journal and article type, open its current author guidelines, and fill in the limits table below. Never rely on remembered limits.
2. Check whether a format-free first submission is allowed. If it is, spend effort on content and mandatory statements rather than layout.
3. Restructure the manuscript into the venue's front matter and sections (see below).
4. Prepare the required statements, figures and supplementary files.
5. Run the checklist, then assemble the submission package: manuscript, source files, figures, declarations and cover letter.

## Verify first (mandatory)

Each PLOS journal has submission guidelines (e.g. https://journals.plos.org/plosone/s/submission-guidelines)
and policy pages (data availability, ethics, competing interests). PLOS LaTeX instructions and template:
https://journals.plos.org/plosone/s/latex. Confirm:

| Item | Requirement (fill in) |
|---|---|
| Abstract length / structure (PLOS ONE commonly up to 300 words) | |
| Author summary (PLOS Biology, Comp Bio, Genetics, Pathogens, NTDs) | |
| Article type specifics (e.g. PLOS Medicine structured abstract) | |
| Figure file formats and size | |

## PLOS ONE publication criteria

PLOS ONE evaluates **scientific rigor, not perceived impact**: original research, sound methods,
conclusions supported by data, adequate reporting, ethical standards, intelligible English, and
data availability. Write the cover letter around soundness, not novelty.

## Structure

Title (plus a short title), authors and affiliations, Abstract, (Author summary where required),
Introduction, Materials and methods, Results, Discussion, Conclusions (optional), Acknowledgments,
References, Supporting information captions. Methods may come before or after Results depending on the journal.

## Mandatory policies

- **Data availability**: all data underlying the findings must be fully available without restriction
  at publication, in the paper, supporting information, or a public repository, with a Data
  Availability Statement. Restrictions (e.g. patient privacy) must be explained with an access route.
  See `reproducibility-statement`.
- **Ethics statement** in Methods: approving committee names and approval numbers, consent type, and
  animal welfare details, as applicable.
- **Financial disclosure** and **competing interests**, entered in the submission system and reflected in the manuscript.
- **Reporting guidelines**: CONSORT, STROBE, PRISMA, ARRIVE and others, submitted as supporting information checklists where relevant.
- Trial registration for clinical trials. Protocols uploaded as supporting information.
- Code: encouraged or required depending on the journal (PLOS Computational Biology has a code policy).

## References

**Vancouver** style: numbered in order of citation, in square brackets in the text `[1]`, placed
before punctuation. Use the PLOS CSL style or `plos2015.bst` from the LaTeX template. Include DOIs.
Preprints can be cited. Unpublished data and personal communications go in the text, not the list.

## Figures and supporting information

- Upload figures as separate TIFF or EPS files meeting the resolution/size rules. Check them with PLOS's
  **PACE** tool, which fixes many format problems automatically. Figure legends go in the manuscript after the paragraph that first cites them.
- Supporting information files (S1 Fig, S1 Table, S1 Text, ...) are uploaded separately with captions at the end of the manuscript.
- LaTeX submissions: PLOS requires a PDF plus source (single `.tex` with references included, or `.bbl`) at acceptance. Follow the template's rules on packages.

## Related skills

`abstract-and-title` (author summary), `reproducibility-statement`, `systematic-review-prisma`,
`statistical-analysis`, `venue-templates` (bundled PLOS ONE scaffold), `cover-letter-to-editor`.
