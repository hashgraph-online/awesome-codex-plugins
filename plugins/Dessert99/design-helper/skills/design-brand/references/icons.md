# Icon sets

Candidates come from these public sets, not from drawing new icons. `icons.cjs` knows
them by the key in the first column. Counts change between versions; the report gives
the real version, and the caption cites it.

| key | set | package | license | how it draws | styles |
|---|---|---|---|---|---|
| `lucide` | Lucide | `lucide-static` (React: `lucide-react`) | ISC | strokes, round ends, 24 grid, stroke 2 | one style; stroke width can change |
| `phosphor` | Phosphor | `@phosphor-icons/core` (React: `@phosphor-icons/react`) | MIT | filled outlines, 256 grid | weights thin, light, regular, bold, fill, duotone |
| `tabler` | Tabler | `@tabler/icons` (React: `@tabler/icons-react`) | MIT | strokes, 24 grid, stroke 2, most icons | outline, filled (fewer) |
| `heroicons` | Heroicons | `heroicons` (React: `@heroicons/react`) | MIT | strokes 1.5 on 24; solid at 20 and 16 | `24/outline`, `24/solid`, `20/solid`, `16/solid` |
| `material` | Material Symbols | `@material-symbols/svg-400` | Apache-2.0 | filled shapes, 960 grid | `outlined`, `rounded`, `sharp`; `fill: true` for filled |

Material Symbols leave more room around the glyph on their grid, so at the same size they
look about 2px smaller than the stroke sets. Say it on the caption when Material is drawn.

## Names differ

The same concept has different names per set. Try these when `find` misses:

| concept | lucide | phosphor | tabler | heroicons | material |
|---|---|---|---|---|---|
| 홈 | `house` | `house` | `home` | `home` | `home` |
| 검색 | `search` | `magnifying-glass` | `search` | `magnifying-glass` | `search` |
| 설정 | `settings` | `gear` | `settings` | `cog-6-tooth` | `settings` |
| 알림 | `bell` | `bell` | `bell` | `bell` | `notifications` |
| 추가 | `plus` | `plus` | `plus` | `plus` | `add` |
| 편집 | `pencil` | `pencil-simple` | `pencil` | `pencil` | `edit` |
| 삭제 | `trash-2` | `trash` | `trash` | `trash` | `delete` |
| 빈 상자 | `inbox` | `tray` | `inbox` | `inbox` | `inbox` |

Another set the user names may be used the same way when its SVG files are public and its
license allows use: draw it from its files, never from memory.

## Choosing two to four (I2)

- The current set, when there is one, as `A 지금`. Its cost slot reads `지금 코드`; any
  other reads `패키지 교체`.
- Sets that genuinely differ for this product: a stroke set and a filled set; round ends
  and square ends; a set with the concepts the product needs and one without.
- The concepts the product needs decide more than looks: a set missing three of them
  means three icons drawn by someone later, in a different hand. Show the count.

## Weight and fill (I3)

| set | the ladder |
|---|---|
| stroke sets (Lucide, Tabler) | stroke 1.5 · 1.75 · 2 · 2.25, set with CSS `stroke-width` on `.ic`; plus the same screen width at every size (Lucide `absoluteStrokeWidth`: `stroke-width` divided by size over 24) |
| Phosphor | thin · light · regular · bold (one `collect` per weight) |
| Heroicons | outline at 24 against solid at 20 and 16 |
| Material Symbols | outlined · rounded · sharp, or `fill` for the selected state |

The selected state is its own row: the selected menu item outlined like the rest, or
filled. Draw both in the menu. A stroke-only set has no filled drawings: filling its
outline (`fill: currentColor`) can swallow inner lines, so show that, and a light tint
fill as the middle option.

## Sizes (I4)

Sizes per spot: beside 14px text 16, in a 32 to 36px button 16 to 20, the menu 20 to
24, an empty state 48 or more. Draw the ladder in the spot it decides, beside the real
text. Measure what changes: the row height (`check.cjs --props box`), the padding left in
a fixed-size button. The icon's middle against the text's middle is usually 0 under the
project's flex alignment; say it once, not per rung.

## Concepts that split (I5)

Only concepts where sets or habits differ get a step of their own. Common ones:

| concept | options |
|---|---|
| 설정 | gear, sliders |
| 내보내기 | arrow into a tray, arrow out of a box, share |
| 삭제 | trash can, cross |
| 보관 | box, archive tray |
| 더 보기 | three dots across, three dots down |
| 알림 | bell, inbox |

One concept per section, every option in the same spots.
