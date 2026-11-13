# Layout rules

The page is fixed geometry. Content either fits it or it does not, and the paginator will not stretch a page to be kind.

## Contents

- [1. Page geometry](#1-page-geometry)
- [2. Typographic scale](#2-typographic-scale)
- [3. What breaks a page](#3-what-breaks-a-page)
- [4. Tables](#4-tables)
- [5. Figures](#5-figures)
- [6. The cover](#6-the-cover)
- [7. Tuning when a check fails](#7-tuning-when-a-check-fails)
- [8. Sources](#sources)

## 1. Page geometry

| Token | A4 value | Effect |
|---|---|---|
| `--page-width` | 210mm | The page box |
| `--page-height` | 297mm | The page box |
| `--page-margin-x` | 17–19mm | Left and right text margin; also the footer inset |
| `--page-margin-top` | 18–20mm | Top margin; the bottom reserves 20mm for the footer rule |
| Text column | page width − 2 × margin | About 172mm on A4 at 19mm margins |

The flow area is `page height − top margin − 20mm bottom reserve`. At A4 with an 18mm top margin that is 259mm of usable height, about 62 lines at a 10.4pt type size and 1.62 leading.

The footer is absolutely positioned and never part of the flow, so it cannot be pushed off the page by long content.

## 2. Typographic scale

| Element | Size | Leading | Notes |
|---|---|---|---|
| Body | 10.2–10.4pt | 1.6–1.68 | Two themes differ here; both stay in the print-safe band |
| `h1` | 1.78em | 1.24 | Section opener |
| `h2` | 1.3em | 1.24 | Subsection, carries a rule below |
| `h3` | 1.08em | 1.24 | Rare in a report; three levels is usually one too many |
| Table | 0.94em | inherited | Small enough to fit a five-column table, large enough to read |
| Caption | 0.86em | inherited | Muted, centred |
| Footer | 8pt | — | Small, muted, ruled above |

Never go below 9pt for body text in a printed report. A page that needs 8pt has too much content, not too small a default.

## 3. What breaks a page

The paginator places one block at a time and opens a new page when the block does not fit. Three failures survive that simple rule:

**Overflow.** A single block taller than the whole flow area cannot be moved to an empty page and still fit, so it is clipped. The check reports `PAGE_OVERFLOW`. The fix is to split the block: a paragraph this long is several paragraphs, a table this tall is two tables.

**Over-wide block.** A table with many columns, or an image wider than the text column, forces horizontal overflow that the page clips. The check reports `BLOCK_TOO_WIDE` with the tag. Fixes, in order of preference: drop a column, shorten the headers, split the table, or scale the image down.

**Widow heading.** A heading as the last element on a page reads as a page ending in a title. The paginator pulls it to the next page and marks the page `page-short`; the space left behind is intentional, not a bug.

## 4. Tables

- Five columns is the comfortable maximum at A4 with 17mm margins. Six fits if the values are short.
- Long text cells wrap; a cell with a paragraph in it belongs in prose, not in a table.
- Numeric columns right-align via `---:` and use tabular figures, so digits line up across rows.
- A table never splits across pages. If it would, it moves whole to the next page, which is why a table taller than a page is a blocking finding.
- Header rows repeat only if the table splits, which it does not, so no repeat rule is needed.

## 5. Figures

- An image scales to the column width, never beyond; its height follows the aspect ratio.
- A tall figure (portrait screenshot, long chart) is the most common overflow cause. Cap it by cropping the image or by placing it alone on a page with a short caption.
- The caption sits below the figure, centred, and interprets the figure.
- A figure and its caption move together: the figure is one block, so they cannot separate.

## 6. The cover

A cover is an HTML block, not a Markdown heading:

```html
<div class="cover">
  <div>
    <div class="cover-rule"></div>
    <div class="cover-eyebrow">내부 검토용</div>
    <h1>시장 진입 분석</h1>
    <p class="cover-sub">2026년 4분기 후보 3안 비교</p>
  </div>
  <div class="cover-meta">
    <span><b>작성</b> 양민열</span>
    <span><b>일자</b> 2026-11-13</span>
    <span><b>대상</b> 경영진</span>
  </div>
</div>
```

The cover fills its page; the next block starts a new page automatically because the cover is the full flow height.

## 7. Tuning when a check fails

| Symptom | First fix | Second fix |
|---|---|---|
| One paragraph overflows | Split it | Move the last sentence to the next section |
| A table is too wide | Drop a column | Shorten header wording |
| A figure overflows | Crop the image | Place it alone on a page |
| The report is one line too long | Cut a sentence from section 2 | Tighten the leading by 0.04 |
| The last page is nearly empty | Cut content to remove the page | Merge two short sections |

Change content before you change geometry. A report with smaller type to fit a page is a report that lied about its length.

## Sources

> Checked 2026-11-13.

| Claim | Source |
|---|---|
| `@page` size and margin, and CSS page-break behavior | <https://developer.mozilla.org/en-US/docs/Web/CSS/@page> |
| `break-inside: avoid` and the inability to split a clipped overflow container | <https://developer.mozilla.org/en-US/docs/Web/CSS/break-inside> |
| Print-safe minimum body size and tabular figures | <https://developer.mozilla.org/en-US/docs/Web/CSS/font-variant-numeric> |
| The measured column and flow dimensions for A4 | This package's runtime, measured on 2026-11-13 at 794×1123 CSS pixels |