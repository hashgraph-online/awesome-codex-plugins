---
name: bibtex-hygiene
description: Clean, deduplicate and validate BibTeX/BibLaTeX bibliographies before submission. Use when a .bib file has duplicate keys or works, missing fields, broken DOIs, lost acronym capitalization (e.g. "bert" instead of "BERT"), inconsistent page dashes, arXiv preprints that now have published versions, or when LaTeX/biber emits bibliography warnings. Includes a zero-dependency linter and normalizer.
license: MIT
compatibility: Python 3.9+ standard library only. Works with BibTeX, BibLaTeX/biber and natbib projects.
metadata:
  version: "1.0"
  category: literature-review
  maintainer: Kalaris Labs
  author: Kalaris Labs (Sayan Chowdhury)
  tags: BibTeX, BibLaTeX, citations, references, LaTeX, bibliography
---

# BibTeX Hygiene

A clean bibliography is a correctness issue, not cosmetics: duplicate entries inflate
reference counts, missing fields render as "?" in the PDF, lowercase acronyms signal
carelessness to reviewers, and a wrong DOI sends readers to someone else's paper.

## Workflow

1. **Lint.** Run the bundled linter on every `.bib` the manuscript uses:

   ```bash
   python scripts/bib_lint.py references.bib
   python scripts/bib_lint.py references.bib --json > bib-report.json   # for programmatic triage
   ```

   Exit code `0` clean, `1` findings, `2` unparseable input.

2. **Fix errors first**, in this order:
   - `duplicate-key`: two entries share a key, so LaTeX silently uses the first. Rename one and update `\cite{}` calls (`grep -rn "\\cite.*{oldkey" *.tex`).
   - `duplicate-work`: the same paper under two keys (same DOI or title). Keep one, repoint citations.
   - `missing-field`: add the field from the publisher page or Crossref, never from memory.
   - `doi-format` / `year-format` / `author-format`: correct from the authoritative record.

3. **Then warnings:**
   - `title-case`: wrap acronyms, proper nouns and chemical/gene symbols in braces:
     `title = {{BERT}: Pre-training of Deep Bidirectional Transformers}`,
     `{Bayesian}`, `{CRISPR}-{Cas9}`, `{\textit{E. coli}}`.
     Brace the *word*, not the whole title. Whole-title braces defeat sentence-case styles.
   - `doi-url`: store bare DOIs (`10.1038/s41586-021-03819-2`). Styles add the resolver.
   - `author-others`: list every author when there are fewer than three.

4. **Resolve preprints.** For every `preprint` note, check whether a peer-reviewed version
   exists (search the title on Crossref/OpenAlex or use the `citation-verification` skill).
   Cite the published version and keep the arXiv ID in `eprint` if the venue allows.

5. **Normalize** (optional, safe mechanical fixes only: bare DOIs, `--` page ranges,
   consistent field order):

   ```bash
   python scripts/bib_lint.py references.bib --fix references.clean.bib
   diff references.bib references.clean.bib   # review before replacing
   ```

6. **Verify the build.** Compile and read the log: `grep -i "warning.*citation\|undefined" main.log`.
   Every `\cite` must resolve and no entry should render with `??`.

## Conventions worth enforcing

| Topic | Rule |
|---|---|
| Keys | `authorYEARword`, lowercase ASCII, e.g. `vaswani2017attention`. Never reuse a key for a different work |
| Authors | `Last, First and Last, First`. Corporate authors in double braces: `{{World Health Organization}}` |
| Venues | One spelling per venue across the file (pick full name or ISO4 abbreviation per the journal's style) |
| Conference papers | `@inproceedings` with `booktitle`, not `@article` with `journal` |
| Software/data | `@software` / `@dataset` (BibLaTeX) or `@misc` with `version`, `doi`/`url`, `year` |
| Unicode | Keep UTF-8 with biber; for classic BibTeX escape accents (`{\"u}`) |
| URLs + DOI | If a DOI exists, drop the publisher URL; keep `url` only for web-only sources (+ `urldate`) |

## Anti-patterns

- Generating BibTeX from memory or from an LLM. Always export from the publisher, Crossref
  (`https://api.crossref.org/works/{doi}/transform/application/x-bibtex`), DBLP or a reference manager.
- Copying Google Scholar BibTeX blindly: it often lacks DOIs, uses wrong entry types and
  mangles capitalization.
- Wrapping the whole title in double braces to "fix" capitalization.
- Leaving `note = {Accessed ...}` on DOI-bearing articles.

## Related skills

- `citation-verification`: checks that every entry matches a real record (catches hallucinated references).
- `reference-manager-interop`: converts between Zotero/Mendeley/EndNote exports, RIS, CSL-JSON and BibTeX.
- `citation-management`: search and retrieve references from literature databases.
