# Text, table, and image extraction

> Read the page as it was built, not as it looks. Extraction quality is decided by the drawing operators, and the recovery strategy must follow them.

## 1. Decide the class first

`check` and `info` classify the document before any extraction runs. The class decides which method can work.

| Signal | Class | Consequence |
|---|---|---|
| `pageText` returns more than a few characters per page | Digital text | Extract directly; every character is real |
| Text is present but `inkRatio` is high on the same page | Text over a scanned background | Extract text, treat the background as decoration |
| `pageText` near zero and the page has ink | Scan | Only `ocr` can produce text |
| `FONT_NOT_EMBEDDED` plus `TYPE3_GLYPHS` | Substituted faces | Extracted characters may be right while the visual is wrong; report both |
| `/Encrypt` in the trailer | Encrypted | `blocked ENCRYPTED`; stop and ask for the password |

Never run OCR on a page that already has a text layer. It doubles the file and puts a second, slightly different string over the real one, which breaks search and screen readers.

## 2. Text extraction

```
engine.js text <file> [--pages 1-5] [--runs] [--json]
```

- Default returns whole-document text in reading order per page.
- `--runs` returns each text-showing operation with its position, font, and size. This is what you need when a paragraph is split across two columns, a header repeats on every page, or a table cell is visually one line but three runs.
- Reading order comes from the content stream, not from visual position. A PDF built poorly can emit a right column before a left column. When order looks wrong, sort the `--runs` output by `y` descending then `x` ascending and rebuild the lines yourself.
- Ligature and soft hyphen handling: a word broken across lines arrives with no hyphen or with a hyphen that is not part of the word. Rejoin at the line break, and drop a trailing hyphen only when the same word continues the next line without one.
- Whitespace inside a run is literal. Two spaces in the source stay two spaces; do not normalise unless the user asked for clean prose.

Limits worth stating in the report:

- A page whose text is drawn as vector outlines or inside an image has no text layer. Report the page number and the class.
- Character encoding can be wrong even when extraction succeeds: a PDF with a broken `/ToUnicode` map returns plausible-looking garbage. Detect it by a high ratio of characters outside the expected script for the declared language.

## 3. Table reconstruction

There is no table object to read. A table is a set of rules (lines) plus text placed inside the cells, and recovering it is inference.

1. Prefer the drawn rules. `pageLines` gives each stroked line; cluster near-equal `y` values into a horizontal rule, near-equal `x` into a vertical rule, and intersect the two sets to get the cell grid.
2. If no rules exist, fall back to text columns: cluster `--runs` by `x` start, and treat a wide gap as a column edge. This works for a simple three-column invoice and fails on a merged header row.
3. Header detection: the first row whose cells are shorter than the body rows and whose font weight or size differs.
4. Emit markdown with an explicit note when a row's cell count differs from the header's, because that is the signature of a merged cell and the markdown table cannot express it.

State the method used and its confidence. A reconstructed grid with guessed boundaries is a hypothesis; presenting it as exact is a lie the user will discover when the numbers do not add up.

## 4. Images

```
engine.js images <file> --out-dir <dir> [--min-size 64]
```

- Each image is extracted at its stored resolution, not the display resolution. A 300 DPI scan referenced at 72 DPI still extracts at 300.
- `--min-size` filters out the 1×1 spacer images and bullet bitmaps that many generators emit. Below the threshold is decoration, not content.
- An image drawn with a mask (soft edge, transparency) extracts as the base image; the mask is a separate object and is not applied. If visual fidelity matters, render the page instead.
- A page that is one full-bleed image is a scan even when it has a small text layer from a previous OCR pass.

## 5. Metadata and structure

```
engine.js info <file>
```

Returns page count, page boxes, rotation per page, `documentAttributes` (title, author, subject, keywords, creator, producer, dates), form-field count, outline presence, and the byte-scan flags. Use it before extraction to decide the plan, and after generation to confirm what was written.

Form field values are read through `listAnnotations` and written through `setFieldValue`. A field with no appearance stream still holds a value; filling it without regenerating the appearance produces a value the reader shows but the printed page does not.

## Sources

> Checked 2026-11-13.

| Claim | Source |
|---|---|
| PDF content stream text operators and their order | <https://opensource.adobe.com/dc-acrobat-sdk-docs/pdfstandards/PDF32000_2008.pdf> (ISO 32000-1 §9.4) |
| `/ToUnicode` map and why broken mapping yields wrong characters | <https://opensource.adobe.com/dc-acrobat-sdk-docs/pdfstandards/PDF32000_2008.pdf> (§9.10.3) |
| Table recovery by rule intersection | <https://github.com/jsvine/pdfplumber> (approach only; the implementation here is independent) |
| Image XObject resolution versus display size | <https://opensource.adobe.com/dc-acrobat-sdk-docs/pdfstandards/PDF32000_2008.pdf> (§8.9.5) |

### Evidence grade

`LOCAL` for the extraction behaviour and limits, verified by running the engine on generated and real-world documents on this machine. `SPEC` for the format-level claims.