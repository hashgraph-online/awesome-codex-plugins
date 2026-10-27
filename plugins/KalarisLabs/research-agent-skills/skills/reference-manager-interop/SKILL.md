---
name: reference-manager-interop
description: Move and sync reference libraries between Zotero, Mendeley, EndNote, JabRef, Paperpile and writing tools (LaTeX/BibTeX, Word, Google Docs, Pandoc, Quarto, Overleaf). Use when converting RIS, BibTeX, BibLaTeX or CSL-JSON files, migrating a library, setting up auto-exported .bib files, choosing a citation style (CSL), or fixing citations lost between tools. Includes a zero-dependency BibTeX/RIS/CSL-JSON converter.
license: MIT
compatibility: Python 3.9+ standard library for scripts/convert_refs.py; Pandoc optional for rendering with CSL styles.
metadata:
  version: "1.0"
  category: literature-review
  maintainer: Kalaris Labs
  author: Kalaris Labs (Sayan Chowdhury)
  tags: Zotero, Mendeley, EndNote, JabRef, BibTeX, RIS, CSL-JSON, Pandoc, Quarto, Overleaf, reference manager
---

# Reference Manager Interoperability

Every reference manager speaks at least one of three interchange formats:

| Format | Best for | Notes |
|---|---|---|
| **BibTeX / BibLaTeX** (`.bib`) | LaTeX, Overleaf, JabRef | BibLaTeX adds `@online`, `@dataset`, `@software`, UTF-8 via biber |
| **RIS** (`.ris`) | EndNote, Mendeley, Scopus/WoS/PubMed exports | Tag-per-line, loses some structure (e.g. corporate authors) |
| **CSL-JSON** (`.json`) | Pandoc, Quarto, Zotero, citeproc-js, Word/Docs plugins | The richest *interchange* format, native to citation styles |

## Convert between formats

```bash
python scripts/convert_refs.py library.ris references.bib        # EndNote/Mendeley -> LaTeX
python scripts/convert_refs.py references.bib references.json    # LaTeX -> Pandoc/Quarto
python scripts/convert_refs.py export.json out.ris --from csljson --to ris
```

Conversion is lossy for exotic fields. Always diff counts (`grep -c "^@" refs.bib`,
`grep -c "^TY  -" lib.ris`) and spot-check authors with particles (van, de, von)
and corporate authors. Then run the `bibtex-hygiene` linter on any produced `.bib`.

## Tool-specific recipes

**Zotero (recommended hub)**
- Install the *Better BibTeX* plugin, then right-click a collection → *Export* → *Keep updated*
  to write an auto-refreshing `.bib` next to the manuscript with stable citation keys.
- Programmatic access: the `pyzotero` skill (Zotero Web API; needs a user API key).
- Word/Google Docs: the Zotero connector plugins insert live citations and bibliography.

**Mendeley Reference Manager**
- Export: select references → *Export* → BibTeX (`.bib`), RIS or EndNote XML.
- To migrate to Zotero: import the `.ris`/`.bib` export, or use Zotero's built-in Mendeley importer.
- Don't build new automation against Mendeley's web API. Work from exported files instead.

**EndNote**
- Export: *File → Export* with output style "RefMan (RIS) Export" (`.ris`) or XML.
- Import `.ris` back with the "Reference Manager (RIS)" filter. Check the encoding is UTF-8.

**JabRef**: native BibTeX/BibLaTeX. Use *Quality → Cleanup entries* and *Check integrity* before submission.

**Overleaf**: link a Zotero/Mendeley account or upload the `.bib`. With an auto-exported
Better BibTeX file, re-upload it or sync via Git.

## Rendering citations with CSL styles (Pandoc / Quarto)

```bash
pandoc paper.md --citeproc --bibliography references.json --csl nature.csl -o paper.docx
```

Quarto front matter:

```yaml
bibliography: references.json
csl: apa.csl          # fetch from https://github.com/citation-style-language/styles
```

Pick the exact style file for the target journal from the CSL repository (over 10,000 styles).
Never approximate a journal's style by editing a similar one unless none exists.

## Migration checklist

1. Export from the source tool in its **richest** format (CSL-JSON or native XML > RIS > BibTeX).
2. Record the reference count before and after.
3. Convert with `scripts/convert_refs.py` if the target cannot import the source format.
4. Import, then check 10 random entries for authors, title case, container, year, DOI.
5. Re-attach PDFs separately. Attachments never travel inside RIS/BibTeX/CSL-JSON.
6. Rebuild citation keys only if the manuscript does not already cite the old keys.

## Related skills

`bibtex-hygiene`, `citation-verification`, `citation-management`, `pyzotero`.
