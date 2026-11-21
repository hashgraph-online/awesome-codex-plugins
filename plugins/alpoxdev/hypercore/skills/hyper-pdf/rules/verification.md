# Verification before delivery

> A generated PDF is a claim. The page image, the byte scan, and the extracted text are the three checks that turn the claim into evidence.

## 1. The gate

Every produced document passes three checks, in this order. Skipping one is a defect in the report, not a shortcut.

| Step | Command | What it proves |
|---|---|---|
| Structure | `check <out.pdf>` | Fonts are embedded, language tag exists, pages are not blank, scans are flagged |
| Geometry | `info <out.pdf>` | Page count, page size, rotation, metadata are what you intended |
| Appearance | `render <out.pdf> --out-dir DIR` | The page actually looks like the document you described |

A fourth step applies whenever text matters:

| Step | Command | What it proves |
|---|---|---|
| Legibility | `text <out.pdf>` | The characters extract as the strings you drew, in the right script |

## 2. Reading a `check` result

| `status` | What to do |
|---|---|
| `ok` | Report the result and the checks run |
| `caveated` | Report each `issues[]` code with the loss it causes; do not call the file finished |
| `blocked` / `error` | Nothing was produced; report the code and what it needs |

`NO_STRUCTURE_TREE` is expected on the `build` path. It is still a limitation worth one line: a screen reader cannot recover reading order from that file. Do not suppress it, and do not describe the file as accessible.

## 3. What the rendered page catches

The byte scan cannot see these, and every one of them has shipped in a real document:

| Defect | Signature on the image |
|---|---|
| Mirrored or inverted text | Characters read right to left, or upside down |
| Wrong baseline | Text overlapping the rule above it, or floating in whitespace |
| Header repeat missing | Page two of a table with no column labels |
| Margin overflow | Text or a table edge past the margin |
| Fallback font | One word in a visibly different face mid-paragraph |
| Korean line break defect | A line starting with `,` or `)` |
| Missing page number | Footer band empty on a multi-page document |
| Blank trailing page | Last page has nothing on it |
| Clipped cell | Text cut at the column boundary instead of wrapping |

## 4. Evidence to keep in the report

- Output path, page count, page size in mm.
- The `check` status and every issue code.
- Which pages were rendered and inspected, and what was seen.
- The exact command lines, so the result can be reproduced.
- Any check that was not run and why. An unrun check is reported as unrun, never as passed.

## 5. Reporting a limitation

State it as a property of the artefact, not an apology:

- "구조 트리가 없어 화면 낭독기가 읽기 순서를 복원하지 못합니다."
- "글꼴이 임베딩되지 않아 이 글꼴이 없는 기기에서는 대체 글꼴로 다시 배치됩니다."
- "OCR 정확도는 확인하지 않았습니다. 3쪽 이미지를 직접 확인해 주세요."

## 6. When the user asks to skip verification

Produce the file, then report what was skipped and what risk that leaves. The user's instruction governs the work, not the accuracy of the report: a report that says "verified" when nothing was verified is a lie regardless of who asked for speed.

## Sources

> Checked 2026-11-13.

| Claim | Source |
|---|---|
| Font embedding requirement and substitution behaviour | <https://pdfa.org/resource/pdfa-2/> (ISO 19005-2) |
| Structure tree and reading order | <https://opensource.adobe.com/dc-acrobat-sdk-docs/pdfstandards/PDF32000_2008.pdf> (§14.8) |
| Korean prohibited line-start characters | <https://www.w3.org/TR/klreq/> |
| Rendering a page for visual review | <https://developer.apple.com/documentation/pdfkit/pdfpage> |

### Evidence grade

`LOCAL` for the check sequence, the defect signatures, and the codes, all observed on documents built on this machine. `SPEC` for the standard claims.