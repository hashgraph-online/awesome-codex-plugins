# OCR on scanned pages

> A scanned page has pixels, not characters. OCR adds a text layer over those pixels; it does not repair them, and its accuracy is a property of the image, not of the engine.

## 1. When OCR applies

| Condition | Action |
|---|---|
| `check` reports `PAGE_NEEDS_OCR` | OCR the listed pages only |
| The page already has a text layer | Do not OCR; it doubles the layer and breaks search |
| A single word is unreadable in a page that has text | Not an OCR case; the source had no character there |
| The image is rotated or skewed | Still OCR-able; Vision handles modest skew, not a 20° rotation |
| The image is below roughly 150 DPI | Expect degraded accuracy; upscale or ask for a better scan |

## 2. Mechanism

```
engine.js ocr <pdf> --out OUT.pdf [--langs ko-KR,en-US] [--pages SPEC] [--work-dir DIR]
```

Per page: render at 2×, run Vision text recognition, then draw each recognized line in invisible render mode at the measured box. Invisible render mode (PDF text rendering mode 3) records glyph positions and characters with no ink, so the page looks identical and selection, search, and copy work.

| Choice | Why |
|---|---|
| Draw over the original, do not re-render the page | Re-drawing loses the original raster quality and changes the visual |
| One invisible line per recognized observation | Matches what a reader selects; one block per page does not |
| Font size derived from the observation height | Keeps the selection highlight roughly over the ink |
| Languages from `--langs` | Vision needs the script to select a model; a Korean page with only `en-US` returns garbage |

## 3. Accuracy and honesty

- Report `textCharacters` and `perPage[].observations`. Zero observations on a page that has ink means the recognition failed, not that the page was blank.
- Do not correct the recognized text silently. If the user wants a clean transcription, that is a separate pass, and the raw layer must stay as recognized so the original can be re-checked.
- Numbers, Korean resident registration numbers, and account numbers are where recognition fails most. On a financial document, read those fields against the image before shipping.
- A recognition rate is not a quality guarantee for the document. The only proof is opening the page and reading it.

## 4. After OCR

1. `check` again: `PAGE_NEEDS_OCR` should be gone for the processed pages.
2. `text` on a processed page: the strings must be plausible in the declared language.
3. `render` the same page: the visual must be unchanged. Invisible text that is visible means the render mode was not applied.
4. `.hyper-pdf-ocr` under the output directory holds the intermediate rasters. Delete it after verification; it is several times the size of the PDF.

## 5. What OCR cannot do

- It cannot restore a character that the scan destroyed. A smudged digit stays ambiguous.
- It cannot infer a table structure. Cell boundaries come from `tables` on the resulting text layer, with the same limits.
- It cannot prove the text is right. A user who needs legal certainty reads the image.

## Sources

> Checked 2026-11-13.

| Claim | Source |
|---|---|
| Vision text recognition and language selection | <https://developer.apple.com/documentation/vision/recognizing-text-in-images> |
| PDF text rendering mode 3 (invisible) | <https://opensource.adobe.com/dc-acrobat-sdk-docs/pdfstandards/PDF32000_2008.pdf> (§9.3.6) |
| OCR accuracy dependence on scan resolution | <https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html> (approach evidence; the implementation here uses Vision) |

### Evidence grade

`LOCAL` for the mechanism, flags, and outputs, run on this machine against a raster-only PDF. `SPEC` for the format-level rendering-mode claim.