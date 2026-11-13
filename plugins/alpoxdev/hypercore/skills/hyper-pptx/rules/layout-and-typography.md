# Layout And Typography

Use this rule file when a slide is crowded, when type looks wrong, or when a deck must read from the back of a room. The geometry itself lives in `assets/runtime/layout.jq`; this file explains the decisions a spec author has to make inside it.

## 1. The Grid

| Value | EMU | Inches |
|---|---|---|
| slide | 12192000 × 6858000 | 13.333 × 7.5 |
| margin | 609600 | 0.667 |
| text column | 10972800 | 12.0 |
| title baseline area | y 533400, height 838200 | 0.583, 0.917 |
| body top | y 1600200 | 1.75 |
| body bottom | y 6248400 | 6.833 |
| footer | y 6355080 | 6.95 |

Left edge is one margin for every element, including cards and tables. Nothing is centred horizontally except the image slide, because a centred column that does not match the title's left edge reads as a mistake.

## 2. Type Scale

| Role | Points | Why |
|---|---|---|
| title slide headline | 44 | the only 40+ element in a deck |
| section number | 15, accent colour | a label, not a heading |
| section title | 36 | |
| slide title | 30 | one line, about 20 Korean characters |
| lead line | 17 | one sentence under the title |
| body bullet | 18 | the size a room reads |
| sub-bullet | 16 | derived: body minus 2 |
| column heading | 17, accent colour | |
| column bullet | 15 | |
| stat value | 46 | |
| stat label | 15 | |
| stat note | 12, muted | |
| table text | 13 | |
| caption | 12, muted | |
| quote | 32 | |
| footer and page number | 11, muted | |

Two rules follow. Body is never smaller than 15 points, because below that a projector turns text into texture. Emphasis comes from weight and colour, not from size: a 30-point title and an 18-point body differ enough that a 24-point "important" bullet only looks inconsistent.

## 3. Spacing

- `spaceBefore` is in points, and the default 6 is a paragraph gap, not a line gap. Line spacing is left to the reader and the font.
- Cards and stats use a 304800 EMU gap (0.333 inch). A wider gap breaks the row into separate things; a narrower one fuses them.
- A lead line pushes the body down by 640080 EMU. Do not also add space to the first bullet; the layout already moved the box.
- Vertical centring is for single-line boxes only. A multi-line box anchored to centre moves when text is edited, which makes two versions of the same slide look different.
- A columns card is only as tall as its tallest column needs, measured from the heading band, the wrapped bullets, and the bottom pad. A card fixed to a share of the body leaves a large empty panel under three short bullets, and a card that grows past the body is reported as `LAYOUT_OVERFLOW` instead of being cropped silently.

## 4. Colour

- One accent colour per deck. It marks the one thing per slide the eye should hit first: a stat value, a column heading, the table header, the chart's first series.
- Muted colour is for text that supports: captions, notes, footer, sub-bullets. Never for a claim.
- Dark slides (title, section, quote) use the palette's dark tokens. Mixing a light body colour onto a dark background produces text that vanishes on a bad projector.
- Contrast: body text on background at least 4.5:1, and large text at least 3:1. The `ink` and `mono` palettes clear this; a custom `accent` must be checked before use as text.

## 5. Tables And Charts

- Table: header row filled with the accent, body rows alternating with the surface colour. Six columns maximum; the column width is equal, so a column of long sentences will wrap and push the row height.
- A table row height is derived from the body area divided by the row count and clamped to 0.35-0.8 inch. The 0.35 floor wins from 15 rows including the header (14 with a caption), the table then runs past the body bottom, and the renderer reports it as an overflow. Split the table before that.
- Chart: the first series takes the accent, the rest fall back to muted, line, and surface. A pie with more than five slices is unreadable; use a bar chart.
- Chart values must be numbers. A string value renders as a category label and silently produces a flat chart.

## 6. Images

- Set `aspect` to the real width divided by height. The layout fits the picture into the body area without cropping, so a wrong aspect letterboxes the slide.
- A caption reserves 411480 EMU below the picture. Do not place text over a photograph; a scrim strong enough to read over any photo dulls the photo.
- One picture per slide. Two pictures with text is a layout problem, not a picture problem.

## 7. What To Check Before Delivering

- Title on one line; if it wrapped, shorten it rather than shrinking the type.
- No bullet reaching past the text column, and no bullet ending in an ellipsis that came from truncation.
- Every caption directly under the thing it names, not under the next thing.
- The footer present on every slide except the title slide, with the correct page number.

## Sources

> Checked 2026-11-13.

| Claim | Source |
|---|---|
| Slide dimensions, EMU, and the 16:9 geometry | <https://learn.microsoft.com/en-us/office/open-xml/presentation/structure-of-a-presentationml-document> |
| Contrast ratios for text | <https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html> |
| Type size and line length for projected text | <https://www.w3.org/WAI/tutorials/images/complex/> |
| Chart series colour assignment and cached values | <https://learn.microsoft.com/en-us/office/open-xml/presentation/working-with-charts> |

### Evidence grade

`LOCAL` — the grid, the type scale, and the clamps are read from `assets/runtime/layout.jq` and were rendered and inspected slide by slide on 2026-11-13. The contrast floor is the WCAG 2.2 minimum.
