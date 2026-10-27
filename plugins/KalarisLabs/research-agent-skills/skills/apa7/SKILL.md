---
name: apa7
description: Format papers, theses and references in APA Style 7th edition for psychology, education, social sciences, nursing and business, covering student vs professional papers, title page, abstract and keywords, heading levels, in-text citations, reference list entries (journal articles, books, chapters, datasets, software, webpages, AI tools), tables and figures, bias-free language, and APA via LaTeX (apa7 class + biblatex-apa), Word or Pandoc/CSL. Use when a user needs APA format, APA citations or references, or an APA-compliant manuscript or thesis.
license: MIT
compatibility: No runtime dependencies. Optional LaTeX apa7 class with biblatex-apa, or Pandoc with apa.csl.
metadata:
  version: "1.0"
  category: journal-formats
  maintainer: Kalaris Labs
  author: Kalaris Labs (Sayan Chowdhury)
  tags: APA 7, APA style, citations, references, psychology, social sciences, thesis formatting
---

# APA Style, 7th Edition

## Workflow

1. Confirm which APA variant applies: the 7th-edition manual, a journal's house rules, or a university thesis guide. Local rules win.
2. Set up the page format and title page for a student or professional paper.
3. Apply heading levels and convert in-text citations to author-date form.
4. Rebuild the reference list from a reference manager with the APA 7 style. Never type references from memory, and verify DOIs.
5. Check tables, figures and bias-free language, then proofread against the checklist below.

The authoritative sources are the *Publication Manual of the APA* (7th ed.) and
https://apastyle.apa.org. When a journal or university has its own APA variant,
the local guide wins. Ask which applies.

## Paper format

| Element | Rule |
|---|---|
| Paper type | **Student** (course papers: title, author, affiliation, course, instructor, date) or **professional** (manuscripts: title, authors, affiliations, author note, and running head) |
| Page | 1-inch margins, double-spaced throughout (including references), page numbers top right |
| Fonts | Consistent, legible: e.g. 11-pt Calibri/Arial, 12-pt Times New Roman, 11-pt Georgia |
| Paragraphs | Indent first line 0.5 in. Left-aligned, ragged right |
| Title | Bold, centered, title case, in the upper half of the title page, and repeated on the first text page |
| Abstract | Professional papers: one paragraph, typically up to 250 words (check the journal), followed by *Keywords:* (italic label) |

## Headings

| Level | Format |
|---|---|
| 1 | **Centered, Bold, Title Case** |
| 2 | **Flush Left, Bold, Title Case** |
| 3 | ***Flush Left, Bold Italic, Title Case*** |
| 4 | **Indented, Bold, Title Case, Ending With a Period.** Text continues on the same line |
| 5 | ***Indented, Bold Italic, Title Case, Ending With a Period.*** Text continues on the same line |

The introduction has no "Introduction" heading. It starts under the repeated paper title.

## In-text citations

- Author-date: (Smith, 2020) or Smith (2020). Two authors: (Smith & Lee, 2020), "Smith and Lee (2020)".
- Three or more authors: first author + "et al." from the first citation: (Garcia et al., 2019).
- Multiple works: alphabetical, separated by semicolons: (Adams, 2018; Zhou & Park, 2021).
- Direct quotes need a page or paragraph: (Smith, 2020, p. 45). Quotes of 40+ words are block quotes without quotation marks.
- Group authors: spell out; define an abbreviation at first use if it is used again.

## Reference list

Title "References" (bold, centered), alphabetical by first author, hanging indent 0.5 in, double-spaced.

```text
Journal:  Author, A. A., & Author, B. B. (2020). Title of the article in sentence case. Journal Name in Title Case, 12(3), 45–67. https://doi.org/10.xxxx/xxxxx
Book:     Author, A. A. (2019). Title of the book in sentence case (2nd ed.). Publisher.
Chapter:  Author, A. A. (2018). Chapter title. In E. E. Editor (Ed.), Book title (pp. 10–25). Publisher. https://doi.org/...
Dataset:  Author, A. A. (2021). Title of dataset (Version 2) [Data set]. Repository. https://doi.org/...
Software: Author, A. A. (2022). Title of software (Version 1.4) [Computer software]. Publisher. https://...
Webpage:  Author/Organization. (2023, May 4). Title of page. Site Name. https://...
```

- Up to **20 authors** are listed. For 21+, list the first 19, an ellipsis, then the final author.
- DOIs are written as `https://doi.org/...` URLs. No "Retrieved from" unless content is designed to change (then include a retrieval date).
- Journal name and volume in italics. Article titles in sentence case, not italic.
- For generative AI tools, follow APA's current guidance on citing AI (https://apastyle.apa.org). Describe how the tool was used in the method or text.

## Tables and figures

Number in bold ("**Table 1**"), then the title in italic title case on the next line; notes below.
Tables have no vertical rules. Figures use the same numbering and title rules. Place them
after first mention or at the end, per instructor or journal.

## Tooling

- **LaTeX**: `\documentclass[man]{apa7}` (or `stu`, `jou`, `doc`) with `biblatex` + `style=apa`, `backend=biber`.
- **Pandoc/Quarto**: `--citeproc --csl apa.csl` (from the CSL styles repository).
- **Zotero/Mendeley/EndNote**: select "American Psychological Association 7th edition". Then check
  capitalization of article titles (tools often keep title case) and DOI formatting.

## Bias-free language

Follow APA guidance: person-first or identity-first language as preferred by the community,
specific age ranges instead of "elderly", singular "they" when appropriate, precise
descriptions of race and ethnicity (capitalized), and describing participants at the right level of specificity.

## Related skills

`reference-manager-interop`, `bibtex-hygiene`, `citation-verification`, `scientific-writing`,
`statistical-analysis` (APA-style statistics reporting).
