---
name: arxiv-submission
description: Prepare and post preprints to arXiv without processing failures or leaks, covering TeX source packaging (.bbl, figures, case-sensitive paths), stripping private comments, choosing categories and license, endorsement, metadata (title, abstract, comments field), versioning and replacements, and linking the journal DOI later. Use when posting a paper to arXiv, when arXiv's TeX compilation fails, before uploading source, or when updating a preprint after acceptance. Includes a zero-dependency preflight checker.
license: MIT
compatibility: Python 3.9+ standard library for the preflight script; a local TeX installation to build the .bbl.
metadata:
  version: "1.0"
  category: journal-formats
  maintainer: Kalaris Labs
  author: Kalaris Labs (Sayan Chowdhury)
  tags: arXiv, preprint, LaTeX, submission, open access
---

# Posting to arXiv

**Verify first.** Policies (size limits, accepted formats, license options,
endorsement, moderation rules) change. Read https://info.arxiv.org/help/submit/index.html
and https://info.arxiv.org/help/submit_tex.html before each submission. Also check the
target journal's or conference's preprint policy, especially anonymity periods for
double-blind venues.

## 1. Build clean source

1. Compile locally from scratch (`latexmk -pdf main.tex`) and confirm the PDF is final.
2. Copy only what is needed into a fresh folder, or run Google's `arxiv_latex_cleaner`
   (`pip install arxiv-latex-cleaner; arxiv_latex_cleaner paper/`), which strips comments and unused files.
3. Run the preflight:

```bash
python scripts/arxiv_preflight.py paper_arxiv/
```

It flags: missing `.bbl` (upload the compiled `.bbl` named like the main file; with biblatex the
`.bbl` must match arXiv's biber version, so plain BibTeX `.bbl` files are safer), case-mismatched
or absolute paths, EPS with pdflatex, build artifacts, hidden files, private files (response
letters, reviews, drafts), `TODO`/reviewer comments (**source is public forever**), unicode or
spaces in file names, and large uploads.

4. Put `\pdfoutput=1` in the first lines of the main file for pdflatex processing.
5. Compress: photos as JPEG, huge vector plots rasterized at 300 dpi, no unused figures.

## 2. Metadata

| Field | Guidance |
|---|---|
| Title | Same as the paper. Plain text. Use TeX only where needed for math |
| Authors | Full names in order. Match the paper and your other papers (affects author pages) |
| Abstract | Plain text, no citations or `\cite`. Keep math minimal. Lines are rewrapped |
| Comments | "12 pages, 5 figures; accepted at XYZ 2026" and code link if public |
| Primary category | The single best fit (e.g. cs.LG, q-bio.GN, astro-ph.CO); cross-lists sparingly |
| Journal-ref / DOI | Add after publication (you can update metadata without a new version) |
| License | Choose deliberately: it cannot be made more restrictive later. CC BY is common for OA mandates. Check funder and journal requirements |

First submission in a category may require **endorsement** from an established author.

## 3. After submitting

- Check the compiled PDF in the preview. arXiv's TeX Live may differ from yours.
- Announcement follows the daily schedule. Fix problems before the cutoff with "replace" or "unsubmit".
- **Replacements** create v2, v3...: summarize changes in the comments. Old versions stay public.
- After journal acceptance, update to the accepted manuscript if the publisher's policy allows
  (check the self-archiving policy, e.g. via Sherpa Romeo), and add the DOI.
- Withdrawal does not delete earlier versions. Never post content you may not share
  (patient data, embargoed results, third-party figures without permission).

## Related skills

`ml-paper-writing` (templates), `venue-templates`, `bibtex-hygiene`, `citation-verification`,
`reproducibility-statement` (code/data links).
