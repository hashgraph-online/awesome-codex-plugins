# Spec Format

Write a `<slug>.deck.json` before running `render-deck.sh`. Every field below is read by `assets/runtime/layout.jq`; a field that is not listed here is ignored.

## Contents

- Deck fields
- Slide kinds
- Text fields and units
- Palettes
- Charts
- Images
- Notes and captions
- A complete example

## Deck Fields

| Field | Required | Meaning |
|---|---|---|
| `slides` | yes | non-empty array of slide objects |
| `title` | no | deck title, stored in `docProps` |
| `author` | no | author, stored in `docProps` |
| `lang` | no | `ko` by default; sets the language tag on every run |
| `footer` | no | running footer text; also adds a page number |
| `theme` | no | palette name (`ink` by default) or a palette override object |
| `fonts` | no | `{ "latin": "...", "eastAsian": "...", "mono": "..." }` |

`fonts.latin` defaults to `Pretendard` and `fonts.eastAsian` falls back to `fonts.latin`. A font name only works when the reader has it installed; the deck records the request, it does not embed the font file.

## Slide Kinds

Every slide accepts `kind` (default `bullets`), `notes`, and the kind's own fields.

| `kind` | Fields | Use |
|---|---|---|
| `title` | `title`, `subtitle`, `meta` | cover, dark background |
| `section` | `number`, `title`, `subtitle` | chapter break, dark background |
| `bullets` | `title`, `lead`, `bullets` | one argument per slide |
| `columns` | `title`, `columns` | 2 or 3 parallel cards |
| `stats` | `title`, `stats` | up to 4 headline numbers |
| `table` | `title`, `table` | `columns`, `rows`, `caption` |
| `chart` | `title`, `chart` | `type`, `categories`, `series`, `caption` |
| `image` | `title`, `image`, `caption` | one full-width picture |
| `quote` | `quote`, `attribution` | a single spoken line, dark background |

`title` slides, `section` slides, and `quote` slides render dark; everything else renders light. A slide never mixes two kinds: a table with three bullets needs two slides.

## Text Fields and Units

`bullets` takes a string or an object:

```json
{ "text": "카드 인증에서 47%가 끊긴다", "level": 0, "bold": false, "size": 18, "color": "12171D", "bullet": true, "space": 6 }
```

| Field | Meaning |
|---|---|
| `level` | `0` or `1`; level 1 shrinks to the parent size minus 2 points and indents |
| `size` | point size, `18` by default at level 0 |
| `space` | points of space before this line, `6` by default at level 0 |
| `bullet` | `false` removes the bullet glyph |

Sizes and spacing are typographic points, not pixels. The layout converts them; a value copied from a CSS file will be about a third of the intended size.

`columns` is an array of `{ "heading": "...", "bullets": [...] }`, and only the first three are laid out. `stats` is an array of `{ "value": "...", "label": "...", "note": "..." }`; only the first four are laid out, and `note` is drawn only when the first stat has one.

## Palettes

| Name | Look |
|---|---|
| `ink` | neutral, warm orange accent |
| `paper` | off-white page, brown ink |
| `navy` | corporate blue |
| `forest` | deep green |
| `mono` | black on white, no color accent |

Override any token with an object:

```json
{ "theme": { "base": "navy", "accent": "0F766E", "surface": "E6F4F1" } }
```

Colours are six-digit hex without `#`. `bg`, `fg`, `accent`, `muted`, `surface`, and `line` are the light tokens; the dark variant of a slide is derived from the same palette, so a custom `bg` does not change dark slides.

## Charts

```json
{ "chart": { "type": "column", "categories": ["W1", "W2"], "series": [{ "name": "실패율", "values": [8.4, 7.1] }] } }
```

`type` is `column` (default), `bar` (horizontal), `line`, `pie`, or `stacked`. Numeric values must be JSON numbers, not strings. `pie` draws only the first series. Category count must match every series' value count.

## Images

```json
{ "image": { "path": "/abs/path/shot.png", "aspect": 1.7778 } }
```

`path` must be a local `png`, `jpg`, or `gif`; remote URLs are rejected so a deck never depends on a network. `aspect` is width divided by height and must match the file, because the picture is placed into the box without cropping. `height` overrides the starting height in EMU before the width is fitted to the text column.

The image is not generated. Take an existing file from the user, from a chart export, or from another tool, and put its path in the spec.

## Notes and Captions

`notes` becomes real PowerPoint speaker notes, so the deck opens with them in the notes pane. A caption under a table, chart, or image is a real text shape and reserves its own space, so it can never overlap the content above it.

## A Complete Example

```json
{
  "title": "결제 실패율 개선",
  "footer": "결제팀",
  "theme": "ink",
  "fonts": { "latin": "Pretendard", "eastAsian": "Pretendard" },
  "slides": [
    { "kind": "title", "title": "결제 실패율 3주 만에 12% 줄이기", "subtitle": "원인 분석과 3단계 개선안", "meta": "2026-11-13" },
    { "kind": "bullets", "title": "결제 실패는 3개 구간에서 발생한다", "lead": "실패 로그 12만 건을 구간별로 나눴습니다.",
      "bullets": ["카드 인증 단계 실패 47%", { "text": "잔액 부족 응답 지연 31%", "level": 1 }], "notes": "로그 기준" },
    { "kind": "stats", "title": "한눈에 보는 개선 효과",
      "stats": [{ "value": "12%", "label": "실패율 감소" }, { "value": "3주", "label": "적용 기간" }] },
    { "kind": "chart", "title": "주간 실패율", "chart": { "type": "line", "categories": ["W1", "W2"],
      "series": [{ "name": "실패율", "values": [8.4, 7.1] }], "caption": "배포 후 2주" } }
  ]
}
```

## Sources

> Checked 2026-11-13.

| Claim | Source |
|---|---|
| Slide size 13.333 × 7.5 in and EMU coordinates | <https://learn.microsoft.com/en-us/office/open-xml/presentation/structure-of-a-presentationml-document> |
| Speaker notes live in a `notesSlide` part | <https://learn.microsoft.com/en-us/office/open-xml/presentation/working-with-notes-slides> |
| Chart parts carry cached categories and values | <https://learn.microsoft.com/en-us/office/open-xml/presentation/working-with-charts> |

### Evidence grade

`LOCAL` — every field name and default in this file is read from `assets/runtime/layout.jq` in this package, and each kind was rendered and inspected on 2026-11-13.
