# Print Interior

`story build . --format print --trim <size>` writes print-ready HTML using
CSS paged media: mirrored margins with a gutter, running heads (author on
the verso, chapter title on the recto, blank on chapter openings), page
numbers at the foot of chapter and back-matter pages, chapters starting on
a recto, a raised initial opening each chapter, widow and orphan control,
and a copyright page. A paged-media
engine turns it into the PDF the printer needs.

## Trim Size

| Trim | Typical use |
|------|-------------|
| `5x8` | Shorter novels, novellas, some literary fiction; compact, cheap to print |
| `5.25x8` | A common fiction size between 5x8 and 5.5x8.5 |
| `5.5x8.5` | The CLI default; general fiction, a safe choice |
| `6x9` | Long novels, epic fantasy, nonfiction-feeling books; fewer pages for the word count |
| `a5` | UK, European, and Australian markets |

Check the trim against the author's printers before choosing: every size
here is widely offered, but hardcover, expanded distribution, and specific
paper options vary by printer and size. Keep one trim across a series so
the spines line up on a shelf.

## Page Count Estimate

The metadata sheet (`story build . --format metadata`) gives an estimated
page count. As a rough rule for fiction set in 11-12 point type:

| Trim | Words per page, roughly |
|------|-------------------------|
| `5x8` | 225-275 |
| `5.5x8.5` | 250-300 |
| `6x9` | 300-350 |

The sheet's estimate, and the print build's gutter, already count the
title page, contents, front and back matter, each chapter rounded up to
whole pages below its heading sink, and the blank versos that
chapter-on-recto leaves behind. Only the rendered PDF gives the real
count; use it for pricing and the cover.

## Render To PDF

The CLI bundles no PDF engine, but `story build . --format print --pdf`
finds one the author has installed and runs it, writing
`dist/<story-id>.pdf`. It tries Prince, WeasyPrint, `pagedjs-cli`, then
headless Chrome or Chromium, in that order; `--pdf-engine <name|path>` picks
one. Chrome is a fallback: it skips the blank pages that start chapters on a
recto, leaves the contents page without page numbers in every book, and older
versions drop running heads. When the CLI reports `(chrome)`, tell the author
and suggest one of the other three for the upload copy. To run an engine by
hand:

- **Paged.js CLI:** `pagedjs-cli dist/<file>.html -o dist/<file>.pdf`
  (free; Chromium-based).
- **WeasyPrint:** `weasyprint dist/<file>.html dist/<file>.pdf` (free;
  Python).
- **Prince:** `prince dist/<file>.html -o dist/<file>.pdf` (commercial;
  free for non-commercial use with a watermark; check its current license).

Engines differ in their support for paged-media features. If running heads,
the raised initial, or recto starts render wrong in one engine, try another before
touching the manuscript. Do not hand-edit the built HTML: it is disposable
and the next build overwrites it.

## Printer Checks

Check the PDF against the printer's current file requirements. The usual
list:

- [ ] Page size equals the trim size (no bleed for a text-only interior)
- [ ] All fonts embedded, with a license that allows embedding in print
- [ ] Even page count; some printers want a multiple of 2 or 4, and add
      blank pages if not
- [ ] Margins meet the printer's minimum, with a wider gutter for thicker
      books
- [ ] Images at 300 ppi, and grayscale for a black-and-white interior
- [ ] PDF standard the printer asks for (some ask for PDF/X-1a or PDF/X-4;
      the author may need a PDF tool to convert)
- [ ] Chapters start on the right; no running head or number on blank
      pages or chapter openers
- [ ] Copyright page ISBN is the print ISBN
- [ ] Spot-check: a widow or orphan, a long word breaking a line, a scene
      break at the top or bottom of a page (a blank-line break can vanish
      there; confirm it shows a visible marker)

## Cover Wrap

- A print cover is one image: back cover + spine + front cover, plus bleed
  on every edge.
- **Spine width depends on the page count and the paper** (white, cream,
  color; paper weight). Get it from the printer's cover calculator or
  template generator after the final page count is known. Each printer's
  paper differs, so a KDP cover and an IngramSpark cover for the same book
  can need different widths.
- Spine text usually needs a minimum page count (often around 100 pages).
  Keep text inside the spine safe zone.
- The back cover needs room for the barcode, usually lower right.
- Every page-count change after the cover is made means a new cover file.

## Proofs

- Order a printed proof from each printer before release. Screen checks
  miss margins, gutter loss, paper tone, and cover color shifts.
- Read the proof for: gutter too tight to read, running heads, chapter
  openings, scene breaks, the copyright page, and front and back matter
  order.
- Record fixes as manuscript or matter changes, rebuild, re-render, and
  re-upload. Never patch the PDF by hand; the next build loses the fix.
