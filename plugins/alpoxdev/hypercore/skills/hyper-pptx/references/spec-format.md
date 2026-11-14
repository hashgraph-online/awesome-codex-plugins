# Spec Format

Write a `<slug>.deck.json` before running `render-deck.sh`. Every field below is read by `assets/runtime/layout.jq`; a field that is not listed here is ignored.

## Contents

- Deck fields
- Slide kinds
- Text fields and units
- Palettes and gradients
- Motion
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
| `transition` | no | default page transition for every slide; a slide may override it |

`fonts.latin` defaults to `Pretendard` and `fonts.eastAsian` falls back to `fonts.latin`. A font name only works when the reader has it installed; the deck records the request, it does not embed the font file.

## Slide Kinds

Every slide accepts `kind` (default `bullets`), `notes`, and the kind's own fields. Geometry for each kind is fixed by the layout; a field that is missing is omitted, not stretched.

| `kind` | Fields | Use |
|---|---|---|
| `title` | `title`, `subtitle`, `kicker`, `meta` | cover, dark background |
| `section` | `number`, `title`, `subtitle` | chapter break, dark background |
| `bullets` | `title`, `lead`, `bullets` | one argument per slide |
| `columns` | `title`, `lead`, `columns` | 2 or 3 parallel cards |
| `stats` | `title`, `lead`, `stats` | 2 to 4 headline numbers as cards |
| `kpi` | `title`, `lead`, `value`, `label`, `delta`, `bullets` | one number made the argument, with a supporting list beside it |
| `compare` | `title`, `lead`, `left`, `right` | two panels, before/after or option A/B |
| `timeline` | `title`, `lead`, `milestones` | 2 to 5 dated steps on one rule |
| `table` | `title`, `table` | `columns`, `rows`, `caption` |
| `chart` | `title`, `chart` | `type`, `categories`, `series`, `caption` |
| `image` | `title`, `image`, `caption` | one picture, full column |
| `imagetext` | `title`, `lead`, `heading`, `bullets`, `image` | picture beside an argument |
| `hero` | `title`, `subtitle`, `image`, `scrim` | picture as the page, text over a scrim |
| `gallery` | `title`, `lead`, `images`, `caption` | 1 to 4 pictures in a row, captions under each |
| `quote` | `quote`, `attribution` | a single spoken line, dark background |
| `statement` | `text`, `kicker`, `gradient` | one sentence as the page, dark background with a colour band |
| `bigstat` | `value`, `label`, `note`, `kicker` | one number as the whole argument |
| `process` | `title`, `steps` | 2 to 5 numbered steps in a row |

`title`, `section`, `hero`, `quote`, and `statement` slides render dark; everything else renders light. A slide never mixes two kinds: a table with three bullets needs two slides.

The `kpi` slide is the "one number" page. `value` is set as large as the string allows (96 points at three characters, 54 at eight or more), `label` names it, and `delta` carries the comparison in muted type. `bullets` sits in the right column and shares the card's row height, so a short card beside three bullets does not leave a step.

`compare` takes two objects of `{ "heading": "...", "bullets": [...] }`. The bullet size is chosen from whichever side needs more room, 16 to 24 points, and the pair is centred together in the space under the lead line.

`statement` is one sentence with no bullets: `text` is set at 40, 34, or 28 points depending on its length, `kicker` is the small label above it, and `gradient` paints the band behind it. Use it for the sentence a reader should remember, not for a second title.

`bigstat` differs from `stats`: `stats` compares two to four numbers on one grid, `bigstat` makes a single number the argument. `value` is set at 150 points up to four characters and steps down to 72 by nine; `label` states what the number means; `note` carries the source.

`process` takes `steps` of `{ "heading": "...", "text": "..." }`, two to five. The card height comes from the longest heading and body, so a two-line step does not clip; a sixth step is an error (`PROCESS_TOO_MANY`) because the columns stop being readable.

`timeline` takes `{ "label": "...", "title": "...", "text": "..." }`. `label` is the date or stage marker above the rule, `title` the step name, `text` the detail below. Five is the maximum; a sixth milestone is unreadable at projection size.

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

`columns` is an array of `{ "heading": "...", "bullets": [...] }`, and only the first three are laid out; each card takes its height from its own heading and bullets, with a floor of 62% of the body so three short cards still hold the page, and the row never shows a blank block under the text. `stats` is an array of `{ "value": "...", "label": "...", "note": "..." }`; only the first four are laid out, every stat may carry its own `note`, the values in a row share one size taken from the longest string, so a short figure never outshouts a long one, and the cards take the same 62% floor as `columns` so a row of three figures holds the page.

## Palettes and Gradients

| Name | Look |
|---|---|
| `ink` | neutral, warm orange accent |
| `paper` | off-white page, brown ink |
| `navy` | corporate blue |
| `forest` | deep green |
| `slate` | cool grey blue |
| `mono` | black on white, no color accent |
| `ocean` | deep blue with a teal companion |
| `plum` | purple with a magenta companion |
| `ember` | burnt orange on a warm page |
| `sand` | beige page with an earth accent |

Override any token with an object:

```json
{ "theme": { "base": "navy", "accent": "0F766E", "surface": "E6F4F1" } }
```

Colours are six-digit hex without `#`. `bg`, `fg`, `accent`, `accent2`, `muted`, `surface`, `tint`, and `line` are the light tokens; `darkBg`, `darkFg`, `darkMuted`, `darkAccent`, `darkAccent2`, `darkSurface`, and `darkTint` are the dark ones, so a dark slide keeps the same hue family instead of falling back to grey. Colours are a deck-level decision: a slide inherits them, and a page that needs a different colour is a signal that the deck has two palettes.

`accent2` is the companion colour: a second series in a chart, the badge on later process steps, a small block beside the main accent. It is a pairing, not a ranking.

A gradient is two colours and an angle, either as a pair or as an object:

```json
{ "gradient": ["0F172A", "134E4A"] }
{ "gradient": { "from": "0F172A", "to": "134E4A", "angle": 90 } }
```

`angle` is degrees counter-clockwise from the positive x axis, matching DrawingML: `0` runs left to right, `90` top to bottom. A malformed pair fails as `GRADIENT_INVALID` at layout time rather than producing a slide part that PowerPoint refuses to open.

## Motion

A transition belongs to a slide; an animation belongs to one or more shapes on it. Both are optional, and a deck without either renders exactly as before.

```json
{ "transition": "fade" }
{ "transition": { "effect": "morph", "speed": "med", "duration": 700 } }
{ "animation": [
    { "effect": "fade", "target": "title", "trigger": "with-previous", "duration": 400 },
    { "effect": "fly", "target": "body", "direction": "up", "delay": 100 }
] }
```

| `transition` effect | Notes |
|---|---|
| `fade`, `cut`, `dissolve` | plain |
| `push`, `wipe`, `cover`, `split`, `strips`, `zoom`, `plus`, `pull`, `randomBar` | take a fixed direction |
| `checker`, `blinds`, `diamond`, `circle`, `wedge`, `wheel`, `random`, `comb`, `newsflash` | geometry only |
| `morph` | PowerPoint 2019 and later; older readers fall back to a fade |
| `none` | no transition on this slide |

`speed` is `slow`, `med`, or `fast`. A name outside this list fails as `TRANSITION_UNKNOWN`: a transition element PowerPoint does not recognise makes it offer to repair the whole file, so an unknown name is rejected rather than substituted.

| `animation` effect | Kind |
|---|---|
| `appear`, `fade`, `wipe`, `fly`, `zoom`, `split` | entrance |
| `grow`, `spin` | emphasis |
| `exitFade` | exit |

| Field | Meaning |
|---|---|
| `effect` | one of the nine above; anything else is `ANIMATION_EFFECT_UNKNOWN` |
| `target` | `all` (default, meaning every content shape), a role (`title`, `body`, `kicker`, `table`, `chart`, `image`, `decor`), a shape id, or an array of any of these |
| `trigger` | `on-click` (default), `with-previous`, `after-previous` |
| `direction` | `up` (default), `down`, `left`, `right`; used by `fly` and `wipe` |
| `duration` | milliseconds, `500` by default |
| `delay` | milliseconds after the trigger, `0` by default |

`target: "all"` skips decoration and the page furniture: an entrance on the rule under a title makes the page look like it is assembling itself. A target that matches nothing fails as `ANIMATION_TARGET_EMPTY` instead of producing a timing tree with no target.

Motion is written from the ECMA-376 schema. See `motion.md` for what this means in a projector and for what is deliberately not supported.

## Charts

```json
{ "chart": { "type": "column", "categories": ["W1", "W2"], "series": [{ "name": "실패율", "values": [8.4, 7.1] }] } }
```

| `type` | Draws |
|---|---|
| `column` (default) | vertical clustered bars |
| `bar` | horizontal clustered bars, value axis along the bottom |
| `stacked` | vertical stacked bars |
| `stackedBar` | horizontal stacked bars |
| `line` | line with markers |
| `area` | line with a light fill under it |
| `scatter` | points; the category is the x when it parses as a number, the position otherwise |
| `pie` | first series only |
| `doughnut` | first series only, ring thickness from `hole` |
| `combo` | bars on the left value axis, lines on a second axis on the right |

| Field | Meaning |
|---|---|
| `categories` | array of strings; the category axis, or the x values of a scatter |
| `series` | array of `{ "name": "...", "values": [...], "as": "bar" \| "line" }` |
| `as` | combo only: which group a series joins; defaults to `bar` for the first series and `line` for the rest |
| `labels` | `true` draws a value label on every point, bar, or slice |
| `legend` | `none`, `bottom`, `top`, `left`, `right`, `topRight`; defaults to `bottom` above one series |
| `numberFormat` | an Excel format such as `0.0`, `#,##0`, `0%`; applied to ticks and labels |
| `valueAxisTitle` | rotated caption beside the value axis |
| `categoryAxisTitle` | caption under the category axis |
| `hole` | doughnut ring thickness as a percentage, `50` by default |
| `caption` | one line under the chart, in its own reserved band |

Values must be JSON numbers, not strings, and every series carries one value per category. A `combo` exists to put two units on one page: a rate series on the right axis keeps its shape instead of flattening against bars measured in hundreds. Both halves share the category axis.

## Images

```json
{ "image": { "path": "/abs/path/shot.png", "alt": "재시도 안내 화면", "fit": "contain", "side": "right", "credit": "내부 시안" } }
```

| Field | Meaning |
|---|---|
| `path` | path to a local `png`, `jpg`, or `gif`; relative paths resolve against the spec file's folder, and remote URLs are rejected so a deck never depends on a network |
| `alt` | alternative text written into the picture; required for a delivery, because a picture with no text is invisible to a reader who cannot see it |
| `fit` | `contain` (whole picture, letterboxed), `fill` (crop to the box), or `cover`; per kind defaults below |
| `side` | `imagetext` only: `right` (default) or `left` |
| `credit` | appended to the caption with a separator |
| `aspect` | width divided by height; only needed when the file cannot be read, and it must match the file |
| `caption` | per picture in a `gallery`, or the caption of an `image` slide |

`fit` defaults: `image` is `contain`, `imagetext` and `gallery` are `fill`, and `hero` is always `fill` because the picture is the page. `fill` crops the centre of the picture through `srcRect`, so the crop is visible in PowerPoint and reproducible in the preview. The image is not generated: take an existing file from the user, a chart export, or another tool.

`gallery` takes 1 to 4 pictures, each `{ "path": ..., "alt": ..., "caption": ..., "fit": ... }`. The picture height is computed after the captions have taken their band, so a caption never lands on the picture above it.

`hero` places a `back` layer picture over the whole canvas, then a flat scrim, then the text at full contrast. `scrim` is the alpha of that black overlay, `0.55` by default; raise it when the picture is busy, lower it when the picture is already dark.

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
    { "kind": "title", "title": "결제 실패율 3주 만에 12% 줄이기", "subtitle": "원인 분석과 3단계 개선안", "kicker": "분기 리뷰", "meta": "2026-11-13" },
    { "kind": "bullets", "title": "결제 실패는 3개 구간에서 발생한다", "lead": "실패 로그 12만 건을 구간별로 나눴습니다.",
      "bullets": ["카드 인증 단계 실패 47%", { "text": "잔액 부족 응답 지연 31%", "level": 1 }], "notes": "로그 기준" },
    { "kind": "stats", "title": "한눈에 보는 개선 효과",
      "stats": [{ "value": "12%", "label": "실패율 감소" }, { "value": "3주", "label": "적용 기간" }] },
    { "kind": "kpi", "title": "실패율은 8.3%에서 7.1%로 내려갔습니다", "value": "7.1%", "label": "현재 주간 실패율",
      "delta": "직전 분기 평균 8.3% 대비 1.2%p 감소", "bullets": ["인증 구간 실패는 47%에서 39%로 줄었습니다"] },
    { "kind": "compare", "title": "처리 방식이 이렇게 달라졌습니다",
      "left": { "heading": "개선 전", "bullets": ["타임아웃 10초 고정", "재시도 없음"] },
      "right": { "heading": "개선 후", "bullets": ["타임아웃 3초", "대체 채널 자동 전환"] } },
    { "kind": "timeline", "title": "3주에 걸쳐 적용했습니다",
      "milestones": [{ "label": "11.01", "title": "인증 우회", "text": "3초 타임아웃" }, { "label": "11.08", "title": "잔액 안내", "text": "재시도 유도" }] },
    { "kind": "chart", "title": "주간 실패율", "chart": { "type": "combo", "categories": ["W1", "W2"],
      "series": [{ "name": "실패율", "values": [8.4, 7.1], "as": "bar" }, { "name": "성장률", "values": [8, 12], "as": "line" }],
      "labels": true, "numberFormat": "0.0", "caption": "배포 후 2주" } },
    { "kind": "imagetext", "title": "안내 화면도 함께 바꿨습니다", "heading": "재시도 유도",
      "bullets": ["실패 즉시 대체 채널을 안내합니다"], "image": { "path": "/abs/retry.png", "alt": "재시도 안내 화면" } },
    { "kind": "hero", "title": "다음 분기는 해외 결제입니다", "subtitle": "인증 지연 12초를 3초로 줄입니다",
      "image": { "path": "/abs/city.png", "alt": "도시 야경" }, "scrim": 0.6 }
  ]
}
```

## Sources

> Checked 2026-11-14.

| Claim | Source |
|---|---|
| Slide size 13.333 × 7.5 in and EMU coordinates | <https://learn.microsoft.com/en-us/office/open-xml/presentation/structure-of-a-presentationml-document> |
| Speaker notes live in a `notesSlide` part | <https://learn.microsoft.com/en-us/office/open-xml/presentation/working-with-notes-slides> |
| Chart parts carry cached categories and values | <https://learn.microsoft.com/en-us/office/open-xml/presentation/working-with-charts> |
| Combo charts are two chart groups sharing an axis pair | <https://learn.microsoft.com/en-us/office/open-xml/presentation/working-with-charts> |
| `srcRect` crops a picture without rewriting the image | <http://www.datypic.com/sc/ooxml/e-a_srcRect-1.html> |
| `p:transition` and `p:timing` are children of `p:sld` | <https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.presentation.slide> |
| Morph is a `p159` extension with an `mc:AlternateContent` fallback | <https://learn.microsoft.com/en-us/office/open-xml/presentation/working-with-presentations> |

### Evidence grade

`LOCAL` — every field name, default, and kind in this file is read from `assets/runtime/layout.jq`, and each kind, chart type, transition, and animation was rendered on 2026-11-14. The PNGs were inspected; the transitions and animations were verified in the slide XML, not played in PowerPoint, which is not installed here.
