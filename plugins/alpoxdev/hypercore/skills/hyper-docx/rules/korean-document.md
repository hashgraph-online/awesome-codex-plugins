# Korean Document Conventions

What a Korean reader expects from a 공문서·보고서·계약서, and where these numbers come from. Everything here is a default the user can override; nothing here is quoted as law.

## 1. Honest status of these numbers

The Korean public-document layout people actually use — A4, 15 pt body, 200 % line spacing, 15 mm top and bottom, 20 mm left and right — is the convention spread through 공문서 작성 guides and office templates. The annex that states it (서식의 설계 기준 in the 행정업무 운영 규정 시행규칙) could not be read at the source on 2026-11-13: law.go.kr was inside a maintenance window from 21:00 that day to 21:00 the next. Treat the preset as **industry practice, not a verified legal quotation**, and say so when a user asks whether it is the regulation. When the numbers matter contractually, read the current annex at law.go.kr and override `margin_mm`, `size_pt`, `line_pct` in the spec.

What the preset sets:

| Setting | Value | Spec key |
|---|---|---|
| Paper | A4, 210 × 297 mm | `page: "official-kr"` |
| Margins | top 15, bottom 15, left 20, right 20 mm; header and footer 10 mm | `margin_mm` |
| Body font | 휴먼명조 | `font` |
| Body size | 15 pt | `size_pt` |
| Line spacing | 200 % of single | `line_pct` |
| Alignment | justified body, centered title, footer page numbers | automatic |

## 2. Item hierarchy

Korean documents mark depth with a fixed sequence of symbols. Do not renumber or reorder them:

```
1.        level 1   번호
 가.      level 2   가지번호
 1)       level 3   괄호번호
 가)      level 4   괄호가지번호
 (1)      level 5   괄호아라비아
 (가)     level 6   괄호한글
 ①        level 7   원문자
```

In a spec, use `{"type": "item", "mark": "가.", "text": "..."}` and pass the mark explicitly. The tool does not guess the level from the indentation, because a wrong guess silently renumbers a document. Set `left_mm` and `hanging_mm` so the text after the mark aligns; a hanging indent of 5 mm with a left indent of 5–10 mm reads correctly at level 2 and 3.

Numbers that begin a sentence inside a paragraph (`1. 점검 개요`) are plain text, not list items: they carry the document's own ordering, not the tool's.

## 3. Document furniture

| Element | Convention | How |
|---|---|---|
| Title | centered, bold, larger than body; no trailing punctuation | `{"type":"title"}` |
| 두문 (발신 명의, 시행일) | top of the first page, before the title | plain paragraphs before `title` |
| 붙임 | after the body, `붙임` followed by the count (`붙임  세부 점검표 1부.`) | `{"type":"row","text":"붙임","value":"세부 점검표 1부."}` or plain text |
| 끝 | the closing marker ends the last line: `...  끝.` | plain text in the last paragraph, two spaces before `끝.` |
| Page number | centered footer, `－ 1 / 3` | `footer: true` |
| 시행일 / 접수 | date format with spaces: `2026. 11. 13.` | literal text |

The `끝.` marker belongs in the same paragraph as the last content line, not on its own line. It is a visible end-of-document mark, and a reader notices when it drifts.

## 4. Numbers, dates, units

- Dates: `2026. 11. 13.` with a period after each part and a space after the middle dots.
- Ranges: use `~` only when the source uses it; prefer `부터 … 까지` in prose.
- Money: `12,000원`, thousands separators, no space before the unit.
- Percentages: `15%`, no space.
- Units: space between the number and the unit except `%` and `°`: `15 mm`, `3 kg`, `15%`.
- Negative and ranges in tables: keep the unit in the header row (`금액(원)`) instead of repeating it in every cell.

## 5. Tables

| Rule | Reason |
|---|---|
| Header row shaded `E7E6E6`, bold, centered | separates the header from data on a long table |
| Header row repeats when the table breaks across pages | `w:tblHeader` on the first row; the builder sets it |
| Explicit column widths in millimetres or twips | a percentage width renders differently in Word, Pages, and previewers |
| `TableGrid` style plus explicit `tblBorders` | a style alone is dropped by some previewers |
| Unit in the header, not in the cell | keeps cells short and alignment clean |
| No nested tables unless the request needs one | nesting loses the reader's place |

Body text inside a table cell is smaller than the body default — 10.5–11 pt reads correctly against a 15 pt body. Set `font_size` per table.

## 6. Fonts and fallback

`휴먼명조` ships with Korean office installs, not with macOS or Linux. The package names the font anyway; the reader's machine substitutes when it is absent. Two consequences:

- A rendered proof on this machine will show whatever the substitute is, so a font *shape* claim is not verifiable here — only the size, weight, spacing, and geometry are.
- Set `w:eastAsia` and `w:hint="eastAsia"` on every run. Without the hint, a Latin-first font choice takes over Korean glyphs and the body changes shape between readers.

When the destination is a document that must look identical everywhere, name a font the destination has (`맑은 고딕`, `바탕`, `Noto Serif KR`) and say why.

## 7. When the request is silent

Apply the preset, and state in the delivery summary that the layout follows 공문서 practice. Do not present a silent default as the user's preference, and do not ask a question the preset already answers.

## Sources

> Checked 2026-11-13

- law.go.kr administrative-rule service, the 시행규칙 annex that states 서식의 설계 기준 — https://www.law.go.kr/ (unreachable during a maintenance window on 2026-11-13; preset treated as practice, not quotation)
- ECMA-376 WordprocessingML, run fonts, eastAsia hint, and table properties — https://ecma-international.org/publications-and-standards/standards/ecma-376/
- Microsoft Learn, table header repeat and cell shading in WordprocessingML — https://learn.microsoft.com/en-us/office/open-xml/word/
- 공문서 항목 구분 기호 관행 (1. / 가. / 1) / 가) / (1) / (가) / ①), as used across 공문서 작성 guides
