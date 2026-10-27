---
name: springer-lncs
description: Format papers for Springer Lecture Notes in Computer Science (LNCS) and related proceedings series (LNAI, LNBI, CCIS) and Springer Nature journals using the llncs class or Springer Nature's sn-jnl template, covering page limits, abstract and keywords, splncs04 references, ORCID, running heads, camera-ready packages and the consent-to-publish form. Use when writing for conferences published in LNCS (e.g. ECCV, MICCAI, ESWC, many workshops), preparing an LNCS camera-ready, or targeting Springer Nature journals.
license: MIT
compatibility: TeX distribution with llncs (CTAN / Springer site) or the Springer Nature LaTeX template; Word templates available.
metadata:
  version: "1.0"
  category: journal-formats
  maintainer: Kalaris Labs
  author: Kalaris Labs (Sayan Chowdhury)
  tags: Springer, LNCS, llncs, splncs04, conference proceedings, Springer Nature, journal formatting
---

# Springer LNCS Proceedings (and Springer Nature Journals)

## Verify first (mandatory)

- Page limits, anonymization and whether references count are set by the **conference**, not Springer. Read the CfP.
- Springer's author guidelines for proceedings: https://www.springer.com/gp/computer-science/lncs/conference-proceedings-guidelines
  (templates for LaTeX and Word, plus the author instructions PDF). The class is also on CTAN (https://ctan.org/pkg/llncs).
- Springer Nature journals use a different template (`sn-jnl`). See the journal's submission guidelines.

## LaTeX setup (llncs)

```latex
\documentclass[runningheads]{llncs}
\usepackage{graphicx}
\usepackage[T1]{fontenc}
\begin{document}
\title{Contribution Title}
\titlerunning{Short Title}                  % if the title is long
\author{First Author\inst{1}\orcidID{0000-0000-0000-0000} \and Second Author\inst{2}}
\authorrunning{F. Author et al.}
\institute{Institution, City, Country \email{a@b.org} \and Other Institution}
\maketitle
\begin{abstract}
One paragraph, commonly 150--250 words.
\keywords{First keyword \and Second keyword \and Third keyword}
\end{abstract}
...
\bibliographystyle{splncs04}
\bibliography{refs}
\end{document}
```

Rules from the LNCS guidelines (confirm the current version):
- Don't alter the layout, fonts, margins or spacing, and don't add page numbers or custom headers.
- Headings are numbered to two levels. Use `\subsubsection*` or run-in `\paragraph` below that.
- References: `splncs04` numbered style. Include DOIs where available. Avoid "et al." in the reference list unless very long.
- Figures: vector preferred. Lines and text must be legible at printed size. Colour appears online (print may be grayscale).
- Provide ORCIDs via `\orcidID{}`. Many conferences require them for all authors.

## Camera-ready package

1. Source files (`.tex`, `.bib` or `.bbl`, figures, the llncs class unmodified) and the final PDF.
2. Signed **Consent to Publish / License to Publish** form (one per paper, by the corresponding author on behalf of all).
3. Check that authors, order and affiliations match the conference system exactly.
4. Supplementary material only if the conference and volume editors allow it.

## Double-blind submissions

Remove names, affiliations and ORCIDs. Refer to prior work in the third person, anonymize repository
links, and scrub PDF metadata. Some conferences require a specific anonymous paper ID in the header.

## Springer Nature journals (sn-jnl)

Use the Springer Nature LaTeX template with the reference style the journal names (numbered,
author-year, or discipline-specific). Declarations (funding, competing interests, ethics, consent,
data/code availability, author contributions) typically go in a "Declarations" section. Check the journal page.

## Related skills

`venue-templates`, `bibtex-hygiene`, `citation-verification`, `arxiv-submission`,
`rebuttal-and-response-to-reviewers`, `scientific-visualization`.
