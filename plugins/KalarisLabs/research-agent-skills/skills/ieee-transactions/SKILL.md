---
name: ieee-transactions
description: Format and submit papers to IEEE journals (Transactions, Journals, Letters, IEEE Access) and IEEE conferences using the IEEEtran LaTeX class or Word templates, covering journal vs conference modes, abstracts and index terms, numbered IEEE reference style, figures and equations, author biographies, page limits and overlength charges, IEEE PDF eXpress, copyright forms, double-blind options and ScholarOne/IEEE Author Portal submission. Use when writing for any IEEE venue, fixing IEEEtran layout issues, or checking IEEE submission compliance.
license: MIT
compatibility: TeX distribution with IEEEtran (CTAN), or Word with IEEE templates.
metadata:
  version: "1.0"
  category: journal-formats
  maintainer: Kalaris Labs
  author: Kalaris Labs (Sayan Chowdhury)
  tags: IEEE, IEEEtran, IEEE Transactions, IEEE Access, LaTeX, conference, journal formatting
---

# IEEE Journals and Conferences

## Verify first (mandatory)

Each IEEE periodical and conference sets its own page limits, overlength charges, review
model (single- vs double-blind) and submission system. Check:
- The journal's "Information for Authors" page (from its IEEE Xplore home) or the conference call for papers.
- IEEE Author Center: https://journals.ieeeauthorcenter.ieee.org/ (journals) and the conference author kit.
- The official template via the IEEE Template Selector (https://template-selector.ieee.org/).

Record: page limit (initial vs final), reference counting, overlength charges, anonymization
rules, and whether a graphical abstract or multimedia is allowed.

## LaTeX setup (IEEEtran)

```latex
\documentclass[journal]{IEEEtran}        % Transactions/Journals
% \documentclass[conference]{IEEEtran}   % conferences
% \documentclass[journal,compsoc]{IEEEtran} % Computer Society journals
\usepackage{cite}          % compresses [1]-[4]
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage[hidelinks]{hyperref}   % check venue rules; some conferences disallow bookmarks in final PDFs
```

- Don't change margins, fonts, spacing or column widths. Reviewers and IEEE production reject tweaked templates.
- Bibliography: `\bibliographystyle{IEEEtran}` + `\bibliography{refs}` (IEEEtran.bst ships with the class).
- Title and authors: `\title{}`, `\author{}` with `\thanks{}` for affiliations and funding
  (journal mode), and `\IEEEauthorblockN/A` in conference mode.
- `\begin{IEEEkeywords} ... \end{IEEEkeywords}` for **Index Terms** after the abstract.
- Figures: `figure` for one column, `figure*` for two. Tables use `\caption` above the table.
- Journal final versions include `\begin{IEEEbiography}` author bios (with photos for many Transactions).

## Content conventions

- **Abstract**: one paragraph, no citations/equations/abbreviations. IEEE Author Center recommends about
  150-250 words (verify per journal). Include the key result.
- **Index Terms**: from the IEEE Taxonomy/thesaurus where possible, alphabetical.
- **References**: numbered in order of citation, in square brackets `[1]`, cited as nouns sparingly
  ("as shown in [3]"). Include DOIs where available.
- Equations are numbered in parentheses and referenced as "(1)". Define every symbol.
- Units in SI. Use "Fig. 1" in text and captions per IEEE style.
- The first page footnote in journals includes received/revised dates (filled by IEEE) and funding.

## Submission workflow

1. Check page count and overlength charges. Supplementary material goes separately if allowed.
2. **Conferences**: validate the final PDF with **IEEE PDF eXpress** (fonts embedded, Xplore-compatible)
   using the conference ID, then upload to the conference system.
3. **Journals**: submit via ScholarOne Manuscripts or the IEEE Author Portal for that periodical.
   Complete the **IEEE Copyright Form** (eCF) or open-access license at acceptance.
4. Double-blind venues: remove author info, anonymize self-citations ("[5]" in third person), and
   strip PDF metadata (`\hypersetup{pdfauthor={}}`).
5. IEEE Access and open-access journals charge APCs. Hybrid journals offer an OA option.

## Common rejections at check-in

Modified template or margins; over page limit; missing index terms; non-embedded fonts; figures
unreadable in grayscale (for print); references not in IEEE style; plagiarism/similarity score
too high, including self-overlap with your own conference version (journals expect substantial extension).

## Related skills

`venue-templates`, `bibtex-hygiene`, `citation-verification`, `scientific-visualization`,
`arxiv-submission`, `rebuttal-and-response-to-reviewers`.
