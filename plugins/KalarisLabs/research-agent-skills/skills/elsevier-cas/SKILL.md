---
name: elsevier-cas
description: Prepare submissions to Elsevier journals (including The Lancet family style notes, Cell-independent Elsevier titles, and thousands of society journals) using the elsarticle LaTeX class, the CAS single/double-column templates or Word, covering highlights, graphical abstracts, keywords, CRediT author statements, declarations of interest, generative-AI disclosure, data availability, reference styles per journal, Editorial Manager submission and "Your Paper Your Way" format-free first submission. Use when targeting an Elsevier journal or fixing elsarticle/CAS template issues.
license: MIT
compatibility: TeX distribution with elsarticle (CTAN) or Elsevier CAS templates, or Word.
metadata:
  version: "1.0"
  category: journal-formats
  maintainer: Kalaris Labs
  author: Kalaris Labs (Sayan Chowdhury)
  tags: Elsevier, elsarticle, CAS template, highlights, graphical abstract, CRediT, journal formatting
---

# Elsevier Journals

## Workflow

1. Identify the exact journal and article type, open its current author guidelines, and fill in the limits table below. Never rely on remembered limits.
2. Check whether a format-free first submission is allowed. If it is, spend effort on content and mandatory statements rather than layout.
3. Restructure the manuscript into the venue's front matter and sections (see below).
4. Prepare the required statements, figures and supplementary files.
5. Run the checklist, then assemble the submission package: manuscript, source files, figures, declarations and cover letter.

## Verify first (mandatory)

Each Elsevier journal's **Guide for Authors** (linked from its ScienceDirect/journal home page)
overrides general advice. It sets article types, word limits, the reference style (numbered,
author-year, or journal-specific), highlights/graphical abstract rules, and whether the CAS
template is expected. LaTeX instructions: https://www.elsevier.com/researcher/author/policies-and-guidelines/latex-instructions.

Many journals follow **"Your Paper Your Way"**: the first submission can be a single PDF in any
reasonable format, and strict formatting is only needed at revision. Check before reformatting.

## LaTeX templates

```latex
% Classic, accepted by nearly all Elsevier journals:
\documentclass[preprint,12pt]{elsarticle}   % review: preprint; final look: 1p, 3p, 5p (+twocolumn)
\journal{Journal Name}
\usepackage{lineno} \linenumbers            % reviewers appreciate line numbers
\bibliographystyle{elsarticle-num}          % or elsarticle-harv / elsarticle-num-names per guide

% CAS templates (journals that request them):
% \documentclass[a4paper,fleqn]{cas-sc}     % single column
% \documentclass[a4paper,fleqn]{cas-dc}     % double column
```

The `venue-templates` skill bundles elsarticle scaffolds and `.bst` files. Front matter uses the
`frontmatter` environment with `\title`, `\author[a]`, `\affiliation[a]{...}`, `\ead{email}`,
`\cortext`, `abstract` and `keyword` environments (keywords separated by `\sep`).

### Minimal complete CAS double-column manuscript

Start from this skeleton when the journal requests the CAS template. Get `cas-dc.cls`, `cas-common.sty` and the
bibliography style from Elsevier's LaTeX instructions page, then check the macros against the template's own
documentation, because CAS versions differ.

```latex
\documentclass[a4paper,fleqn]{cas-dc}
\usepackage[authoryear]{natbib}            % or [numbers]: follow the Guide for Authors
\shorttitle{Short running title}
\shortauthors{A. Author et al.}

\begin{document}
\let\WriteBookmarks\relax
\title [mode = title]{Full title of the article}

\author[1]{First Author}[orcid=0000-0000-0000-0000]
\cormark[1]
\ead{first.author@university.edu}
\credit{Conceptualization, Methodology, Writing - original draft}
\affiliation[1]{organization={Department, University}, city={City}, country={Country}}

\author[2]{Second Author}
\credit{Formal analysis, Writing - review \& editing}
\affiliation[2]{organization={Institute}, city={City}, country={Country}}

\cortext[1]{Corresponding author}

\begin{abstract}
One paragraph within the journal's word limit.
\end{abstract}

\begin{highlights}
\item First result-focused highlight within the character limit
\item Second highlight
\item Third highlight
\end{highlights}

\begin{keywords}
keyword one \sep keyword two \sep keyword three
\end{keywords}

\maketitle

\section{Introduction}
...

\section*{CRediT authorship contribution statement}
\printcredits

\section*{Declaration of competing interest}
The authors declare that they have no known competing financial interests or personal relationships that could have
appeared to influence the work reported in this paper.

\section*{Declaration of generative AI and AI-assisted technologies in the writing process}
% Follow the journal's current required wording, or remove the section if no AI tools were used.

\section*{Data availability}
Data are available at [repository, DOI].

\bibliographystyle{cas-model2-names}        % match the journal's reference style
\bibliography{refs}
\end{document}
```

## Required and common elements

- **Highlights**: a separate file of bullet points (commonly 3-5, each up to about 85 characters including spaces). Results, not methods.
- **Graphical abstract**: required or encouraged by some journals. Single image with a minimum size given in the guide.
- **Keywords**: typically a small set (check the maximum), often without words already in the title.
- **CRediT author statement**: contributions using the 14 CRediT roles (see `reproducibility-statement`).
- **Declaration of competing interest**: many journals require Elsevier's declaration tool output as a file.
- **Declaration of generative AI and AI-assisted technologies in the writing process**: Elsevier asks
  authors to disclose such use in a dedicated statement. Check the current policy wording.
- **Data availability**: statement and/or data linking (Mendeley Data, domain repositories).
- **Funding** with grant numbers. Ethics approvals and consent for human/animal studies.

## Reference styles

The guide specifies one of: numbered `[1]`, numbered with names, author-year (Harvard), or a
named style (APA, Vancouver). Use the matching `.bst`/CSL style. Enter DOIs. For initial
"Your Paper Your Way" submissions any consistent style is usually accepted.

## Submission

Editorial Manager (journal-specific site). Upload the manuscript (PDF for initial, source files
for revision: `.tex`, `.bib`/`.bbl`, figures), highlights, graphical abstract, declarations, and
cover letter. Suggested reviewers are often requested (see `cover-letter-to-editor`).
The Elsevier Researcher Academy and journal "Article Transfer Service" may offer transfers after rejection.

## Related skills

`venue-templates`, `abstract-and-title` (highlights), `reproducibility-statement`,
`cover-letter-to-editor`, `bibtex-hygiene`, `rebuttal-and-response-to-reviewers`.
