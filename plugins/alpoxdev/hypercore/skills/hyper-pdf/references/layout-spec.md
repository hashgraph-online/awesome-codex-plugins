# Layout spec reference

> The `build` path takes one JSON file and produces one PDF with no browser. Everything the page shows comes from this object, so an undocumented field is a field a caller guesses wrong.

## Table of Contents

1. [Document root](#1-document-root)
2. [Blocks](#2-blocks)
3. [Signature block](#3-signature-block)
4. [Worked example](#4-worked-example)
5. [Composer limits](#5-composer-limits)

## 1. Document root

| Field | Type | Default | Meaning |
|---|---|---|---|
| `page.width` | number, pt | `595.28` | Page width (A4) |
| `page.height` | number, pt | `841.89` | Page height (A4) |
| `page.margin` | number, pt | `56.7` | Margin on all four sides (20 mm) |
| `fontSize` | number, pt | `11` | Base size that blocks inherit |
| `font` | string path | `null` | Explicit font file; `null` means `resolveFont` picks the Korean-capable default |
| `lang` | string | `null` | BCP 47 tag written into the Catalog as `/Lang` |
| `header` | string | `null` | Running header, drawn at the left margin above the content box |
| `footer` | string | `null` | Running footer, drawn at the left margin below the content box |
| `pageNumbers` | boolean | `true` | Draw the page number centred in the footer band |
| `blocks` | array | `[]` | Ordered content, drawn top to bottom |
| `signature` | object | `null` | Signature block appended after the last block |

Units are points throughout. 1 mm = 2.8346 pt, so 20 mm is 56.7 pt. There is one margin value; a document needing different top and side margins encodes the difference with a `spacer` block.

## 2. Blocks

Every block has `type`. An unknown `type` falls through to `paragraph`, so a typo renders text instead of failing — check that the output has the block you meant.

### `heading`

| Field | Type | Default | Meaning |
|---|---|---|---|
| `text` | string | `''` | Heading text; wraps at the content width |
| `level` | integer 1–5 | `1` | Selects size 22/17/14/12/11 pt when `size` is absent |
| `size` | number | by level | Explicit size |
| `keepWithNext` | boolean | `false` | Reserves 2.2 line heights so the heading is not orphaned at a page bottom |
| `rule` | boolean | `false` | Draw a hairline under the heading |

A heading never splits; if it does not fit it moves whole to the next page.

### `paragraph`

| Field | Type | Default | Meaning |
|---|---|---|---|
| `text` | string | `''` | Body text |
| `size` | number | doc `fontSize` | Font size |
| `leading` | number | `size × 1.65` | Baseline-to-baseline distance |
| `indent` | number | `0` | Left indent from the content margin |
| `color` | `[r,g,b,a]` 0–1 | near-black | Text colour |

A paragraph breaks between lines, never inside one, so it can continue across a page boundary. The 1.65 default is the Korean comfortable range; 1.5 looks cramped with Hangul.

### `list`

| Field | Type | Default | Meaning |
|---|---|---|---|
| `items` | string[] | `[]` | One entry per item |
| `ordered` | boolean | `false` | Numbered marker instead of `•` |
| `size` | number | doc `fontSize` | Font size |

Marker sits at the margin, text is indented 16 pt. An item and its continuation lines never split across pages.

### `table`

| Field | Type | Default | Meaning |
|---|---|---|---|
| `header` | string[] | `null` | Header row; also what repeats after a page break |
| `rows` | array of string[] | `[]` | Body rows |
| `columns` | integer | header length | Column count when `header` is absent |
| `widths` | number[] | equal | Relative column weights, not absolute widths |
| `size` | number | `fontSize − 1` | Cell font size |

Behaviour worth knowing before writing a spec:

- Column widths are proportional. `widths: [3,1,2]` splits the content width 3:2:1.
- Cells wrap; a row's height is the tallest cell in it.
- When a row does not fit, the header row is redrawn on the new page and the row follows. A row never splits.
- Grid: vertical rule at every column boundary on every row, a horizontal rule under a header row, and one closing rule under the last row. No full grid, because a ruled box on every financial row reads as noise.
- Header cells get a 0.93 grey fill.

### `keyValue`

| Field | Type | Default | Meaning |
|---|---|---|---|
| `pairs` | array of `[label, value]` | `[]` | Label in grey at the margin, value at `labelWidth` |
| `size` | number | doc `fontSize` | Font size |
| `labelWidth` | number | `min(160, 34% of width)` | Label column width |

The workhorse for a contract's party block, an invoice's billing header, or a report's cover metadata.

### `rule`

No fields. A hairline across the content width with 18 pt of vertical space.

### `spacer`

| Field | Type | Default | Meaning |
|---|---|---|---|
| `height` | number | `12` | Vertical gap in points |

### `pageBreak`

No fields. Closes the current page and opens a new one at the top margin.

## 3. Signature block

| Field | Type | Meaning |
|---|---|---|
| `label` | string | Line drawn above the signature area (usually the date) |
| `lines` | string[] | One line per signatory, e.g. `"갑: 주식회사 코드 (인)"` |

It is a root field, not a block: it always draws last, after `blocks`, and reserves five line heights so it does not spill.

## 4. Worked example

```json
{
  "page": {"margin": 70.9},
  "fontSize": 10,
  "lang": "ko-KR",
  "header": "주식회사 코드",
  "footer": "대외비",
  "blocks": [
    {"type": "heading", "text": "용역 계약서", "level": 1, "rule": true},
    {"type": "keyValue", "pairs": [
      ["계약번호", "KD-2026-1113"],
      ["계약일", "2026년 11월 13일"],
      ["갑", "주식회사 코드 (대표 양민열)"],
      ["을", "홍길동"]
    ]},
    {"type": "spacer", "height": 20},
    {"type": "heading", "text": "제1조 (목적)", "level": 3, "keepWithNext": true},
    {"type": "paragraph", "text": "이 계약은 갑이 을에게 의뢰하는 소프트웨어 개발 용역의 범위와 조건을 정한다.", "leading": 17},
    {"type": "table",
     "header": ["항목", "수량", "단가", "금액"],
     "rows": [["설계", "1", "3,000,000", "3,000,000"], ["구현", "1", "5,000,000", "5,000,000"]],
     "widths": [4, 1, 2, 2]},
    {"type": "pageBreak"},
    {"type": "heading", "text": "제2조 (대금 지급)", "level": 3}
  ],
  "signature": {"label": "2026년 11월 13일", "lines": ["갑: 주식회사 코드 (인)", "을: 홍길동 (인)"]}
}
```

## 5. Composer limits

| Limit | Detail |
|---|---|
| No images | There is no image block. A document needing a logo or a chart must use the `html` path |
| No nested structure | Blocks are a flat list; a table cannot contain a list |
| No page-level columns | One text column per page |
| No absolute placement | Content flows top to bottom; there is no `x`/`y` per block |
| No style inheritance | Each block states its own `size`; nothing cascades except the document `fontSize` |
| No header/footer variables | `header` and `footer` are literal strings; the page number is a separate automatic element |

Each of these is a reason to route to `html` instead. Choosing `build` and then discovering a missing logo halfway through is a rewrite, not an adjustment.

## Sources

> Checked 2026-11-13.

| Claim | Source |
|---|---|
| A4 in points (595.28 × 841.89) | <https://www.iso.org/standard/71690.html> (ISO 216) |
| Korean comfortable line height range | <https://www.w3.org/TR/klreq/> |
| CoreText line suggestion used for wrapping | <https://developer.apple.com/documentation/coretext/cttypesetter> |
| CGContext drawing and text matrix | <https://developer.apple.com/documentation/coregraphics/cgcontext> |

### Evidence grade

`LOCAL` for every field, default, and limit: read from `assets/runtime/compose.js` and exercised by building documents on this machine. `SPEC` for the standard page geometry.
