# Korean typesetting and font rules

> Korean text breaks, spaces, and renders differently from Latin text. A PDF that ignores this looks machine-made even when every glyph is present.

## 1. Line breaking

Korean wraps between characters, not only at spaces, and the break must not separate a character from the particle that follows it.

| Rule | Detail |
|---|---|
| Break unit | A Hangul syllable block is a break opportunity; a Latin word is not |
| Prohibited start | `,` `.` `)` `]` `}` `:` `;` `!` `?` `%` `°` `”` `’` `》` `〉` `】` and closing quotes never begin a line |
| Prohibited end | `(` `[` `{` `“` `‘` `《` `〈` `【` and opening quotes never end a line |
| Particle attachment | A line does not end with a bare noun whose particle starts the next line when the noun is a single syllable |
| Number–unit | `1,000원`, `30%`, `2026년` stay on one line; break before the number, never inside it |
| Latin mix | An embedded English word or identifier stays whole; break at the space before it |
| Long identifier | A path, URL, or code token wider than the measure breaks at `/`, `-`, or `_`, not at an arbitrary character |

`wrapText` in `assets/runtime/native.js` calls `CTTypesetterSuggestLineBreak`, which already applies the Unicode line-breaking algorithm including the prohibited-start set. Do not re-implement wrapping with a character counter: a character count produces the classic Korean defect where a line ends in `)` or starts with `,`.

Verification: after rendering, read the page image and look at the right edge. A ragged edge with lines ending in closing punctuation, or a lone particle at a line start, means the wrapper was bypassed.

## 2. Spacing

| Case | Rule |
|---|---|
| Between Hangul and Latin/digits | Insert a thin space: `PDF 3개`, `2026년 11월` |
| Between number and unit | No space for `%`, `℃`, `원` handled as a suffix in a table cell; one space in running prose |
| Between sentences | One space; do not justify a Korean paragraph by stretching spaces, because the stretch destroys the character rhythm |
| Table cells | No leading or trailing space; the cell padding already provides the gap |
| Quotation | Use `“` `”` for speech and `‘` `’` for a quote inside it; do not substitute `"` |

## 3. Font choice and coverage

The failure that matters is silent: a font without a glyph does not error, the renderer substitutes another face, and the paragraph reflows at a different width.

1. Pick a face with full modern Hangul coverage (U+AC00–U+D7A3 plus the compatibility jamo block used in word-processor output).
2. Composite and rare characters are the usual gaps: `㈜` U+3236, circled numbers, half-width jamo, and some CJK compatibility ideographs are missing from many display faces. A `Type3` object in the produced PDF is the signature of this substitution; `check` reports it as `TYPE3_GLYPHS`.
3. Keep an explicit fallback face for those characters rather than letting the renderer choose one, so the substituted glyph at least shares the weight and width of the body face.
4. Never synthesise bold for a Korean face by stroking the outline: the strokes collide in dense syllables. Use a real bold weight, or a slightly larger size with a heavier colour.

## 4. Font embedding

A PDF that references a font by name only renders correctly on a machine that has that font. `check` reports `FONT_NOT_EMBEDDED` when the byte scan finds no `FontFile2` (TrueType) or `FontFile3` (OpenType/CFF) program.

| Path | Embedding behaviour |
|---|---|
| `build` (layout spec) | CoreGraphics embeds the program it draws with; `FontFile2` appears for a TrueType-backed system face |
| `html` (Chromium) | Embeds a subset per face; a `@font-face` pointing at a local `.ttf`/`.ttc` gives a subset with the font's own name |
| Base-14 reference (`Helvetica`) | Not embedded by design; acceptable only for a throwaway internal draft, never for a document that leaves the machine |

Korean text needs the embedding more than Latin does: a Korean face is a large file that a reader machine is unlikely to have, and the substitution changes metrics enough to move every line.

## 5. Page geometry

| Item | Korean default | Reason |
|---|---|---|
| Page | A4 210 × 297 mm (595.28 × 841.89 pt) | Korean office standard; Letter is a defect in a domestic business document |
| Margin | 20 mm sides, 15 mm top and bottom for a report; 25 mm all round for a contract | A contract is signed and bound |
| Body size | 10–11 pt at 1.6–1.7 line height | Hangul syllable blocks are denser than Latin lowercase; 1.5 looks cramped |
| Line length | 60–75 Hangul characters per line | Beyond this the eye loses the return point |
| First-line indent | Optional for prose, none for a list or a table | Indent plus a leading space is a common doubled-indent defect |

## Sources

> Checked 2026-11-13.

| Claim | Source |
|---|---|
| Korean line-breaking rules, prohibited line-start and line-end characters | <https://www.w3.org/TR/klreq/> |
| Unicode line-breaking algorithm applied by CoreText | <https://www.unicode.org/reports/tr14/> |
| Font subsetting and the `FontFile2`/`Type3` distinction in PDF | <https://pdfa.org/resource/pdfa-2/> (ISO 19005-2 font embedding requirement) |
| Korean typography spacing with Latin and digits | <https://www.w3.org/TR/klreq/#spacing> |
| A4 as the Korean office standard page | <https://www.iso.org/standard/71690.html> (ISO 216) |

### Evidence grade

`LOCAL` for the defaults in §5 and the fallback policy in §3.1, verified by rendering on this machine. `SPEC` for the line-breaking and embedding rules, which rest on the cited standards.