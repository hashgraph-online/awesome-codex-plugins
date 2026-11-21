# gongmunseo and 기안문 conventions

## 1. When this file applies

Read it only when the document is, or must look like, a 기안문, an official 공문서, an attached form (별지 서식), a plan, or a result report. Ordinary document editing does not need it.

## 2. The seven item levels

Korean government documents number their items in a fixed order. The seven `outline_numbering` levels of rhwp produce exactly that order.

| Level | Form | `num_format` | `text` example |
|---|---|---|---|
| 1 | 1., 2., 3. | `digit` | `^1.` |
| 2 | 가., 나., 다. | `hangul_syllable` | `^2.` |
| 3 | 1), 2), 3) | `digit` | `^3)` |
| 4 | 가), 나), 다. | `hangul_syllable` | `^4)` |
| 5 | (1), (2), (3) | `digit` | `(^5)` |
| 6 | (가), (나), (다) | `hangul_syllable` | `(^6)` |
| 7 | ①, ②, ③ | `circled_digit` | `^7` |

`text` is the literal string placed before each number, so `"^1."` yields `1.갑` and `"^1. "` (with a trailing space) yields `1. 갑`. Government documents usually pack the number against the word, so omit the space.

Past the seventh level the numbering returns to 1., so an eighth layer means the document structure needs rework, not another level.

## 3. The skeleton of a 기안문

| Position | Content |
|---|---|
| Header | 시행일자, 시행번호, 접수일자, 접수번호, postal code, address, telephone, 문서번호 |
| Title | the matter in one line, with no closing period |
| Body | starts with an item number; the first item is usually a purpose sentence ending `…하고자 함` |
| Attachments | the word `붙임`, no colon after it, two spaces, then the list, closed with `끝.` |
| Sender | institution and position, with the seal position |

The first body line carries the purpose and the conclusion. Open the background with a fact - a directive date, a statute's enforcement date, a complaint count. Do not open with atmosphere such as "급변하는 행정환경에 따라".

## 4. Notation rules

| Item | Rule | Example |
|---|---|---|
| Date | space between the dots and the numbers, no leading zeros for month or day, period after the day | `2026. 11. 13.` |
| Time | 24-hour clock, colon packed between hour and minute | `09:00`, `15:30` |
| Amount | Arabic numerals with thousands separators, unit packed, never abbreviated to 천원 | `345,000원` |
| Range | never a tilde and 까지 together | `2026. 2. 20.∼2. 24.` |
| Colon | packed to the preceding word, one space after | `원장: 김갑동` |
| Foreign term | Korean first, original in parentheses | `업무 협약(MOU)` |

## 5. Tables

- Use a table only for three or more items that must be compared. Two items are a sentence.
- Bold the header row. Put the unit in the header and do not repeat it in every cell.
- Numbers align right, text aligns left. rhwp's `cell_align` accepts `"left"`, `"center"`, `"right"`, or a per-cell array.
- When a total row exists, separate it from the other rows with a rule.

## 6. Footnotes

- A footnote attaches evidence without breaking the flow: a source, a statute article, a calculation.
- In rhwp a footnote takes two commands: `edit insert-footnote` creates the anchor and `edit insert-footnote-text` supplies the body. They are a pair.
- The document numbers the footnotes; never type the number in the body text.

## 7. Voice

- 개조식 ends in a noun form (`… 추진`, `… 완료`). 서술식 ends in `…한다`. Do not mix the two in one document.
- One paragraph carries one fact.
- Never invent a figure. When the number is unknown, leave `○○건` or `2026. ○. ○.` as a placeholder and list it as an item to fill.
- Replace index-free closings such as "체감도 제고" or "만족도 향상" with a target (`민원 연 412건 → 200건`).

## 8. Building one with rhwp

1. For all seven levels, put seven entries in the scaffold spec's `outline_numbering` and select the level per block with `level`.
2. Build tables with the spec's `table` block; change individual values later with `edit set-cell` rather than rebuilding.
3. Write the attachment list as `paragraph` blocks. The tool does not add `붙임` or `끝.` for you.
4. For footnotes, scaffold first, then run `insert-footnote` and `insert-footnote-text` in that order.
5. Table shape is editable: `set-column-widths`, `merge-cells`, `split-cell`, `insert-row`/`insert-col`, and `set-cell-props` all work. Property JSON is not schema-checked, so change properties and then re-read the widths or re-render the page; a successful exit code proves only that the command ran (`rules/rhwp-command-map.md` §8).

## Sources

> Checked 2026-11-13. The item numbering and notation rules come from secondary sources; law.go.kr did not respond from this environment (302 redirect).

- Seven item levels and notation rules: 행정안전부 「행정업무의 운영 및 혁신에 관한 규정 시행규칙」 별지 제1호서식, as restated in <https://github.com/jkf87/hwpx-skill/blob/main/references/gonmunseo-2025-writing-rules.md>
- Document structure (why → what → how) and forbidden phrasing: the gongmunseo reference under `.claude/` in <https://github.com/chrisryugj/kordoc>
- The seven levels as actually printed: a rhwp v0.9.0 `scaffold` run mixing `digit`, `hangul_syllable`, and `circled_digit`, read back with `export-text`
- `cell_align` values: `src/scaffold/schema.rs` in <https://github.com/edwardkim/rhwp>
