---
name: acm-sigconf
description: Format ACM conference papers and journal articles with the acmart LaTeX class (sigconf, sigplan, acmsmall, acmlarge, acmtog, manuscript/review/anonymous modes) or the ACM Word template, covering CCS concepts, keywords, ACM Reference Format, rights management and copyright blocks, anonymization for double-blind review, accessibility (alt text), the TAPS production workflow and common acmart errors. Use when writing for CHI, SIGGRAPH, KDD, SIGMOD, CCS, FAccT, WWW, SIGIR, CSCW, PLDI or any ACM venue or journal.
license: MIT
compatibility: TeX distribution with acmart (CTAN, recent version required by TAPS), or ACM Word template.
metadata:
  version: "1.0"
  category: journal-formats
  maintainer: Kalaris Labs
  author: Kalaris Labs (Sayan Chowdhury)
  tags: ACM, acmart, sigconf, CHI, KDD, SIGGRAPH, TAPS, LaTeX, journal formatting
---

# ACM Conferences and Journals (acmart)

## Workflow

1. Identify the exact journal and article type, open its current author guidelines, and fill in the limits table below. Never rely on remembered limits.
2. Check whether a format-free first submission is allowed. If it is, spend effort on content and mandatory statements rather than layout.
3. Restructure the manuscript into the venue's front matter and sections (see below).
4. Prepare the required statements, figures and supplementary files.
5. Run the checklist, then assemble the submission package: manuscript, source files, figures, declarations and cover letter.

## Verify first (mandatory)

The call for papers sets the format (e.g. `sigconf` vs `acmsmall` for PACM-style venues),
page limits (often excluding references), anonymization and supplementary rules. The master
template and documentation are at https://www.acm.org/publications/proceedings-template, and
the class on CTAN is https://ctan.org/pkg/acmart. Use the **latest acmart**, because TAPS rejects old versions.

## LaTeX setup

```latex
% Submission (double-blind, line numbers, review mode):
\documentclass[sigconf,review,anonymous]{acmart}
% Camera-ready:
% \documentclass[sigconf]{acmart}
% Journals / PACM: \documentclass[acmsmall]{acmart}

\setcopyright{acmlicensed}          % from your rights form at camera-ready
\copyrightyear{2026}
\acmYear{2026}
\acmDOI{XXXXXXX.XXXXXXX}            % from the rights form email
\acmConference[Short Name '26]{Full Conference Name}{Month dd--dd, 2026}{City, Country}
\acmISBN{978-x-xxxx-xxxx-x/2026/mm}
```

- Keep `\author{}`, `\affiliation{}` (with `\institution`, `\city`, `\country`) and `\email{}` blocks
  per author. Use `\renewcommand{\shortauthors}{...}` if names are long.
- Abstract goes **before** `\maketitle` in acmart.
- **CCS concepts**: generate XML at https://dl.acm.org/ccs, paste the `\begin{CCSXML}...` block and
  `\ccsdesc[500]{...}` lines, and include `\keywords{...}`.
- Bibliography: `\bibliographystyle{ACM-Reference-Format}` + `\bibliography{refs}`. With BibLaTeX use
  the `acmart` BibLaTeX styles. The "ACM Reference Format" block is generated automatically.
- Teaser figure: `\begin{teaserfigure}` before `\maketitle`.

## Accessibility and TAPS

- Provide **alt text** for figures (`\Description{...}` inside each figure). ACM requires it.
- The TAPS workflow compiles your source into ACM's HTML and PDF formats. Unsupported packages or
  custom macros that redefine layout will fail. Test by compiling with the latest acmart and
  avoiding `\vspace` hacks, font changes and margin packages.
- Keep all source files in one folder with no absolute paths, and upload the `.bib` (TAPS runs BibTeX).

## Double-blind checklist

`anonymous` option (hides authors and acknowledgments). Refer to your own prior work in the third
person. Anonymize links to code (e.g. anonymous GitHub). Remove PDF metadata. No identifying
acknowledgments or grant numbers in the submission.

## Common problems

- "Overfull hbox" in author block: shorten affiliations or use `\shortauthors`.
- Missing `\Description` warnings: add alt text to every figure.
- Wrong format option (`sigconf` vs `acmsmall`) for PACM venues: check the CfP.
- Page limit breaches caused by excluding appendices incorrectly: check whether appendices count.
- Using `\usepackage{times}` or geometry changes, which TAPS rejects.

## Related skills

`venue-templates`, `ml-paper-writing` (KDD/WWW-style ML papers), `bibtex-hygiene`,
`scientific-visualization`, `rebuttal-and-response-to-reviewers`, `arxiv-submission`.
