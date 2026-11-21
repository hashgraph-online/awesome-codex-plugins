# Accessibility and structure

> A tagged PDF is not an accessible PDF. The tags are the floor; reading order, language, and alt text are what a screen reader actually needs.

## 1. What the byte scan can prove

`check` reports issue codes from a byte-level scan plus CoreGraphics queries. Each code maps to a concrete loss for assistive technology.

| Code | Meaning | What the user loses |
|---|---|---|
| `NO_STRUCTURE_TREE` | No `/StructTreeRoot` in the Catalog | The reader gets one undifferentiated text block: no headings, no list, no table |
| `NO_LANGUAGE_TAG` | Catalog has no `/Lang` | The reader guesses pronunciation; Korean read with English phonemes |
| `FONT_NOT_EMBEDDED` | No `FontFile2`/`FontFile3` for a used face | The reader may substitute a different face, changing line breaks and, for a symbol font, the spoken character |
| `TYPE3_GLYPHS` | A `Type3` font object is present | Glyphs are drawn as procedures with no reliable Unicode mapping; extraction and speech can both break |
| `PAGE_BLANK` | Page renders almost no ink | A blank page in a delivered document is a defect the reader sees |
| `PAGE_NEEDS_OCR` | Page has ink and no text | The page is invisible to search and to a screen reader |
| `CONTAINS_JAVASCRIPT` | `/JS` or `/JavaScript` in the name tree | Not an accessibility defect, but a reason to inspect before opening |
| `CONTAINS_LAUNCH_ACTION` | `/Launch` or `/SubmitForm` action | A click can start an external program; treat as untrusted |
| `ENCRYPTED` | `/Encrypt` in the trailer | Text extraction and assistive technology need the password first |

## 2. Reading order

The structure tree encodes order. A PDF built from a content stream that draws a right column before a left one has correct characters and a wrong tree; a screen reader then reads the page backward.

| Source | Order quality |
|---|---|
| `html` path with `--export-tagged-pdf` | Chromium derives the tree from the DOM, so the order follows the markup, not the visual position |
| `build` path | No structure tree at all; order is the block order in the spec, which is correct by construction, but no reader can see it |
| Scanned + OCR | Order follows the OCR engine's own line detection; verify on a two-column page |

Check the order on any document with two columns by extracting text and comparing the sequence with the visual top-to-bottom, left-to-right reading. If they disagree, say so; a reader with no vision has no other way to learn it.

## 3. Language tagging

CoreGraphics writes `/Info` but ignores the language key. The engine writes `/Lang` by appending the existing Catalog as a new object with an incremental update, so the original bytes and offsets stay valid.

```
engine.js build --spec <spec.json> --out <out.pdf>   # spec.lang: "ko-KR"
```

Rules:

- Tag the document language on the Catalog `/Lang`, and a differing run inside it with a `Span` `/Lang` (for example an English product name in a Korean contract).
- Use a BCP 47 tag: `ko-KR`, not `korean` and not `ko_KR`.
- Verify from the scan, not from the input: `rawScan.lang` must equal the intended tag. A build that succeeded does not prove the tag landed.

## 4. Alternative text

`check` cannot prove alt text is meaningful; it can only prove a figure has none. When a document contains a chart, a signature image, or a diagram:

- Add `alt` in the spec's image block, or `alt` on the `<img>` in the HTML path.
- Alt text describes the function, not the pixels: "2026년 매출 추이, 3분기부터 증가" not "chart image".
- A decorative rule or background pattern takes an empty alt so the reader skips it.

## 5. What this skill does not do

- It does not repair a structure tree in an arbitrary third-party PDF. Rebuilding a tree on top of a wrong content stream produces a tree that claims structure the content does not have, which is worse than none.
- It does not certify conformance to a standard. `check` reports mechanical findings; conformance also needs real reading-order and alt-text judgement by a person.
- It does not run an assistive technology. Any claim that a document "works with a screen reader" without that test is unverified, and must be reported as such.

## Sources

> Checked 2026-11-13.

| Claim | Source |
|---|---|
| Tagged PDF, structure tree, `/StructTreeRoot`, `/Lang` | <https://opensource.adobe.com/dc-acrobat-sdk-docs/pdfstandards/PDF32000_2008.pdf> (ISO 32000-1 §14.7–14.8) |
| PDF/UA requirements for tagging, language, and alt text | <https://www.iso.org/standard/64599.html> (ISO 14289-1) |
| BCP 47 language tag syntax | <https://www.rfc-editor.org/rfc/rfc5646> |
| Why Type3 fonts break extraction | <https://opensource.adobe.com/dc-acrobat-sdk-docs/pdfstandards/PDF32000_2008.pdf> (§9.6.5) |
| Alternate description requirement | <https://www.w3.org/TR/WCAG21/#non-text-content> |

### Evidence grade

`LOCAL` for the issue codes and the `/Lang` incremental-write behaviour, each reproduced on this machine. `SPEC` for the standard requirements.