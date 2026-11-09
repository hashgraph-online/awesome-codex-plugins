# LaTeX Report

Use this reference only when the user asks for LaTeX or a typeset PDF. The Markdown report stays the deliverable of record; the `.tex` file is built from the finished report, never the other way around.

## Contents

- Build output
- Citation and ledger
- Compile order
- Log-first repair
- Korean typesetting
- Page review
- Missing toolchain

## Build Output

Build the deliverable beside the saved report in `.hyper/research/` as `[NN].slug.tex`, plus the compiled `[NN].slug.pdf` when the toolchain is present. The `.tex` source is a rendering of the finished Markdown report: same claims, same citations, same numbers. Any prose polish applied while adapting the report to LaTeX must not move a `\cite` and must not strengthen an uncertain claim. A claim that is hedged in the report stays hedged in the `.tex`; a claim that sits in the unresolved annex is not promoted into the findings to fill a page.

## Citation And Ledger

Every `\cite{Sn}` in the `.tex` file must resolve to a `[Sn]` row in the run's sources ledger (the journal's `sources.md`). Before compiling, list every cite key in the `.tex` file and check it against the ledger rows:

- A cite key with a ledger row is safe to compile.
- A cite key with no ledger row blocks delivery. Add the missing row from the opened source, or remove the cite and its claim, then recheck. Do not compile a report that cites a source the run never opened.
- Citation shape follows the report itself: `\cite{S1}` cites one row, `\cite{S1,S4}` cites two rows. Numbers and other figures still carry their `MEASURED`, `ASSUMED`, or `DERIVED` lineage from the report.

The `.tex` file also carries the bibliography those cite keys resolve to, one entry per cited ledger row: either a `thebibliography` item whose label is `S<n>`, or a `.bib` entry whose key is `S<n>`. Fill each entry from the ledger row's title, publisher, URL or path, and publication date, and leave out a field the ledger does not hold instead of inventing one. A cite key that resolves to a ledger row but has no bibliography entry still renders as `?` in the PDF, so add the entry in the same pass that adds the cite.

## Compile Order

Compile with `latexmk -xelatex` first. It drives the engine, the bibliography tool when the file uses a `.bib`, and the extra engine passes for references and cross-references by itself:

```sh
latexmk -xelatex [NN].slug.tex
```

When `latexmk` is not installed, run the engine, the bibliography tool, and the engine twice by hand:

```sh
xelatex [NN].slug.tex
biber [NN].slug
xelatex [NN].slug.tex
xelatex [NN].slug.tex
```

Substitute `bibtex` for `biber` when the bibliography is BibTeX-shaped. Skip the bibliography tool entirely when the file uses a `thebibliography` list: there is no `.bib` to process, and running `biber` then fails with `Cannot find 'control' file`. Two engine passes are required so that citation numbers and cross-references settle; with a bibliography tool they come after it, and with `thebibliography` they follow the first pass. A single pass leaves `?` markers in the PDF.

## Log-First Repair

Read the compiler log (`.log`) before touching the source, and fix the first `!` error first. TeX stops reporting once error recovery replaces a missing piece, so later errors are often symptoms of an earlier one. The routine loop is:

1. Run the compile order above.
2. Search the log for the first line starting with `!`. That line, and the lines around it, name the failure.
3. Fix only the cause of that first error, then recompile.
4. Repeat until the log shows no `!` line.

Never rewrite the whole document to silence a log: one error, one fix, one recompilation. A missing citation key is not a log error, so it is checked separately under Citation And Ledger.

## Korean Typesetting

Use the XeTeX engine so Korean text renders: `latexmk -xelatex` and `xelatex` already do. The `.tex` file must set a Korean font the engine can find (for example `fontspec` with a Korean font available on the machine) and must use a CJK-capable class or package. Three rules before delivery:

- The Korean font really is installed on the machine that compiles the report. Name it only if it is present; if no Korean font is installed, say so in the report instead of silently falling back to blank glyphs.
- Compile once and check the log: missing-glyph warnings (`Missing character`) mean the font or the class is wrong. Fix the font choice, not the text.
- English titles, commands, and URLs stay in the font that carries them; only the Korean prose needs the Korean font.

## Page Review

Look at the rendered pages, not only the compiler exit code. When `pdftoppm` is available, render the PDF to page images and read the ones that carry the parts most likely to break:

```sh
pdftoppm -png -r 100 [NN].slug.pdf page
```

Review at least the first page, one page with a comparison table, and one page with long Korean prose. Check that tables fit the text width, no glyph is blank, and citation numbers render instead of `?`. When `pdftoppm` is not available, review the `.tex` source against the Markdown report line by line and say in the report that page images were not reviewed.

## Missing Toolchain

When no TeX toolchain is installed (`latexmk` and `xelatex` both absent), deliver the `.tex` source and state plainly that the PDF was not built. The report must name the missing tool and the command that would build the PDF. Never claim a PDF exists when the compile never ran, and never attach a PDF path that has no file behind it.

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| `latexmk -xelatex` first with an engine, bibliography tool, and two-pass fallback, log-first repair of the first `!` error, page review with `pdftoppm`, every `\cite` mapped to a ledger row, and prose polish that neither moves a `\cite` nor strengthens an uncertain claim | `dbc-hbin/omp-ulw` at commit `74df40f` (2026-11-09); the source repository has no license, so the mechanism was re-authored in this package's own words and no text or code was copied |
| The saved Markdown report at `.hyper/research/[NN].slug.md` and its `[S<n>]` citations resolving to the journal's `sources.md` rows | `references/report-template.md` and `references/journal-format.md` in this package |

### Evidence grade

`LOCAL` - the compile route and the citation-to-ledger check are this package's own decision. The Markdown report remains the deliverable of record; the LaTeX route is an optional second rendering.
