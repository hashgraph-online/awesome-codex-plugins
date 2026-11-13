# Format routes

One source, many formats, one direction: the Markdown source is authored, the HTML is rendered from it, and everything else is derived from the HTML.

## 1. Why HTML is canonical

The HTML is the only artifact that is both the source of every other format and inspectable on its own. A PDF is a printed HTML; a page image is a screenshot of one page of that HTML; a DOCX is a conversion of that HTML. Fix the HTML, and every format inherits the fix. Hand-edit a PDF and the next render silently discards the edit.

```
report.md  --(markdown.awk)-->  body.html
body.html + report.css + theme + report.js  --(assemble.awk)-->  report.html   <- canonical
report.html  --(headless print)-->    report.pdf
report.html  --(headless screenshot)--> report-01.png ... report-NN.png
report-NN.png --(sips / magick)-->     report-NN.jpg
report.html  --(textutil)-->          report.docx
report.md    --(copy)-->              report.md
```

## 2. What each format carries

| Format | Carries | Loses | Use when |
|---|---|---|---|
| HTML | Everything: pagination, theme, tables, figures, the table of contents | Nothing, but it needs a browser to open | The reader will read on screen, or you need one file that prints correctly |
| PDF | Exactly the paginated pages, fonts embedded, fixed geometry | Text reflow, live links beyond what the browser wrote | The reader will print it, email it, or sign it |
| PNG | One file per page, at 1–3× device scale | Text selection, links, search | A slide, a chat message, a message board, a preview |
| JPG | Same as PNG, smaller | Slightly more compression artifacts on text | The destination caps file size or rejects PNG |
| DOCX | Editable text, the reader can revise | Exact pagination, the theme's typography, the footer numbering | The reader must edit or comment in Word |
| Markdown | The authored source, portable | Any layout the pipeline applied | The reader wants the text, or will re-render elsewhere |

DOCX is a courtesy export, not a layout-faithful one. Say so when delivering it: pagination in Word will not match the PDF, because Word lays out the text again with its own engine and fonts.

## 3. Format selection

Pick the smallest set that serves the stated reader.

- No format named, on-screen reader: `html,pdf`.
- No format named, print or email: `html,pdf`.
- A chat or slide destination: `png` alone, or `pdf` plus `png` for the pages that matter.
- A reader who must edit: add `docx`, and warn about pagination.
- A page-limited task ("one page"): the page count is the deliverable constraint, so check it before adding formats.

Do not add a format the user did not ask for just because the pipeline can. Five files where the user wanted one is a worse delivery than one file.

## 4. When a renderer is missing

Formats degrade in this order, and the degradation is reported, never hidden:

| Missing | Still works | Reported as |
|---|---|---|
| Any Chromium-family browser | `md` only | `BROWSER_MISSING` — the browser is the whole rendering path |
| `textutil` (non-macOS) | `html`, `pdf`, `png` | `DOCX_UNAVAILABLE` |
| `sips` and ImageMagick | `html`, `pdf`, `png` | `RASTERIZER_MISSING` for the `jpg` request only |

Never install a renderer mid-run to make a format appear. Report which format is unavailable and why, deliver the rest, and let the user decide.

## 5. The page is the unit

Every format except Markdown is page-addressed, so the page count is decided once, in the HTML, and every derived format agrees with it.

- The layout pass in `report.js` decides how many pages the content takes.
- The PDF must print exactly that many pages; a mismatch is a blocking finding.
- The image export is per page, numbered from 1, zero-padded to two digits.
- The page number in the footer is `current / total`, resolved after pagination.

This is why the source cannot contain a manual page break in the middle of flowing text except through the explicit `:::pagebreak` marker, which the paginator honors as a hard boundary.

## Sources

> Checked 2026-11-13.

| Claim | Source |
|---|---|
| Headless print-to-pdf, screenshot, and DOM dump as the rendering primitives | <https://developer.chrome.com/docs/chromium/headless> |
| `@page` size and margin, and the fixed-geometry print model | <https://developer.mozilla.org/en-US/docs/Web/CSS/@page> |
| `sips` as the macOS image converter and `textutil` as the macOS document converter | <https://ss64.com/mac/sips.html>, <https://ss64.com/mac/textutil.html> |
| DOCX re-layout in Word differing from browser pagination | This package's measurement on macOS 26.2 with Word's own layout engine, not a documented guarantee |