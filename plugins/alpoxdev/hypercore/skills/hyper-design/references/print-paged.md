# Print and Paged Media

Read when the output is a document that must paginate — a print stylesheet, an invoice or a report turned into a PDF, a receipt, or any layout that breaks across pages. The screen rules in this package describe one continuous canvas; here the canvas is a sequence of page boxes, and the failures are half-empty pages, split table rows, and headings stranded at the bottom of a page.

## Contents

- 1. Page box and margins
- 2. Breaking control
- 3. Blocks that must stay whole
- 4. Side effects of break control
- 5. Reviewing the produced PDF

## 1. Page box and margins

| Tell | Why | Fix |
|---|---|---|
| The print rendering keeps the screen width | The page is a viewport, not paper | Set the `@page` size and margins first, then let the content size to the page |
| Paper with a hole in the middle: big empty margins nobody chose | The default margin is treated as free, so content hugs the paper edge | Set margins to what the document needs, and put running headers and page numbers in the margin area instead of the content boxes |
| Every page slightly taller than the paper | The document grew a ragged last page | Check the page count, find the block that overflows, and fix it there rather than by shrinking everything |

## 2. Breaking control

| Tell | Why | Fix |
|---|---|---|
| A page that ends mid-paragraph with one line on the next page | The widow line reads as a mistake | `orphans: 3` and `widows: 3` on body text, so a block that starts on a page carries lines with it |
| A table row split across two pages, with the second half carrying no header | The row is unreadable | `break-inside: avoid` on rows and figures; repeat the header row when a table must split |
| A heading alone at the foot of a page, with its paragraph on the next | The reader loses the structure at the break | `break-after: avoid` on headings, which keeps a heading with the block it introduces |
| A section forced onto a new page that leaves the previous page a third full | A manual break repeats wherever the content changes | Reserve `break-before: page` for genuine starts (a chapter, a form field group); elsewhere let the flow paginate |

## 3. Blocks that must stay whole

Keep on one page unless the block is longer than a page, in which case it must be allowed to split deliberately:

- Figures with their captions.
- Table rows, and table cells that contain more than one line.
- A heading with the first lines of the block it introduces.
- A signature line with the text it signs, and a form field with its label and error message.
- Any pull quote or callout, whose separation from its text breaks the argument.

## 4. Side effects of break control

`break-inside: avoid` is not free: applied to a block taller than a page, it pushes the block onto the next page and repeats until the block is the only thing left, or overflows. Apply it only to blocks short enough to fit a page, and where a block is long, let it split and control the split with `orphans` and `widows` instead. A forced page break can also leave the page before it short; after any manual break, check the page before it.

## 5. Reviewing the produced PDF

The source stylesheet never proves the pagination. Proof is the produced PDF:

- Read the page count and compare it against what the document should be. A surprise page is a defect until explained.
- Look at every page break in order: the last block of each page and the first of the next, checking for orphaned lines, split rows, stranded headings, and the near-empty page.
- Check the margins and the running header or page number on each page, especially the first page and any landscape page.
- Record the page count and the breaks checked in the report. Without a rendered PDF, these items are `static_only`.

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| The fragmentation properties (`break-before`, `break-after`, `break-inside`, `orphans`, `widows`) and the page boxes | <https://www.w3.org/TR/css-break-4/>, <https://www.w3.org/TR/css-page-3/> |
| The idea and the section shape (page box, blocks that must not split, the side effects of `break-inside`) | `dbc-hbin/omp-ulw @ 74df40f` (2026-11-09), re-authored in this package's own words; the source repository has no license and no text or code was copied |

### Evidence grade

The property names and the page model come from the standards above. The rest is a practitioner rule set with no measurements taken.
