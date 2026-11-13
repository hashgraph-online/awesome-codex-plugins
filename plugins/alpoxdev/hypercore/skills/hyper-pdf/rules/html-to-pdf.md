# HTML to PDF

> Two paths produce a PDF, and they are not interchangeable. Choosing wrong costs either the design or the ability to run at all.

## 1. Which path

| Requirement | Path | Command |
|---|---|---|
| Existing HTML/CSS must look exactly as it looks in a browser | `html` | `engine.js html <file.html> --out <out.pdf>` |
| A contract, invoice, report, or form from data with no web page | `build` | `engine.js build --spec <spec.json> --out <out.pdf>` |
| User wants the output tagged and language-tagged | `html` (emits a structure tree) | `engine.js html ... --tagged` |
| No browser is installed | `build` | `engine.js build ...` |
| Print rules, page breaks, running headers by CSS | `html` | `engine.js html ...` |
| Pagination must not drift between runs | `build` | `engine.js build ...` |

The `build` path lays out a JSON spec with CoreGraphics directly. It cannot reproduce arbitrary CSS: no floats, no flexbox, no grid, no `@media print`, no web fonts beyond what is installed. Saying otherwise is a lie the user sees in the first render.

## 2. The HTML path

```
engine.js html <input.html> --out <out.pdf> [--tagged] [--paper a4|letter] [--margin 20mm] [--landscape] [--chromium <path>]
```

Mechanism: the engine locates a Chromium-family binary (`findHtmlRenderer`), then runs it headless:

```
--headless --disable-gpu --export-tagged-pdf --print-to-pdf=<out> --no-pdf-header-footer <file://...>
```

| Rule | Why |
|---|---|
| Always keep `--export-tagged-pdf` | Without it the output has no structure tree and screen readers get one undifferentiated block |
| Pass a `file://` URL, not a path | A bare path is read as a search query and prints an error page |
| Set paper with CSS `@page` or the flag, not both | Two sources disagree and the flag silently wins |
| `@font-face src` must be an absolute `file://` URL or a `data:` URI | A relative URL resolves against the temporary profile, not the HTML file, and the face silently falls back |
| Wait for fonts and images | Chromium prints once the load event fires; a `@font-face` that finishes after that prints in the fallback face. Preload the font, or inline it as `data:` |
| Background graphics | `print-color-adjust: exact` on the elements that need a filled background, or the print style strips it |

When no renderer is found the command returns `blocked NO_HTML_RENDERER` with the paths it searched. Do not install a browser to get past it without asking; use `build` if the document is data-driven, or report the block.

## 3. Korean specifics for the HTML path

- A Korean web font is a multi-megabyte download; a `@font-face` pointing at a remote URL may not finish before print. Inline a local subset or use an installed face.
- `word-break: keep-all` is the only reliable way to stop a browser from breaking a Korean line mid-word at a space-less boundary; the default `normal` splits at every character for Korean.
- `line-height: 1.6` or more. A browser default of 1.2 on Hangul looks like a solid block.
- Do not rely on `text-align: justify`; Korean justification in Chromium stretches inter-character space unevenly.
- Verify the result: `rawScan` must show `structureTree: true` and a `FontFile2`/`FontFile3` entry for the Korean face.

## 4. The build path

The spec is JSON. The full block list and field table live in `references/layout-spec.md`. Shape:

```json
{
  "page": {"width": 595.28, "height": 841.89, "margin": 56.7},
  "fontSize": 10,
  "lang": "ko-KR",
  "header": "주식회사 코드",
  "footer": "대외비",
  "pageNumbers": true,
  "blocks": [
    {"type": "heading", "text": "용역 계약서", "level": 1},
    {"type": "keyValue", "pairs": [["계약번호", "KD-2026-1113"], ["갑", "주식회사 코드"]]},
    {"type": "paragraph", "text": "…", "size": 10, "leading": 16.5},
    {"type": "table", "header": ["항목", "수량", "금액"], "rows": [["설계", "1", "5,000,000"]], "widths": [3, 1, 2]},
    {"type": "rule"},
    {"type": "spacer", "height": 24}
  ],
  "signature": {"label": "2026년 11월 13일", "lines": ["갑: 주식회사 코드 (인)", "을: 홍길동 (인)"]}
}
```

`page.width`/`page.height` default to A4 in points, `page.margin` to 56.7 pt (20 mm). Margins are a single value, not four sides. The block list and every field are in `references/layout-spec.md`.

| Property | Guarantee |
|---|---|
| `lang` | Written into the Catalog by an append-only incremental update, because CoreGraphics ignores the language key |
| Determinism | Same spec gives the same layout and text on the same machine and OS version. The creation timestamp is the one field that differs between runs |
| Table page breaks | A table that outgrows the page repeats its header row on the next page; a row never splits across pages |
| Missing font | Falls back through `resolveFont` and reports `FONT_FALLBACK` rather than failing |

## 5. Verification after either path

1. `engine.js check <out.pdf>` — read every issue code; `NO_STRUCTURE_TREE` is expected on the `build` path and must be reported, not hidden.
2. `engine.js info <out.pdf>` — confirm page count, page size, and that `docTitle` is what you intended.
3. `engine.js render <out.pdf> --out-dir <dir>` — open the first page and the page where a table breaks. Look at the right edge, the header repeat, and the footer page number.
4. `engine.js text <out.pdf>` — the extracted text must contain the strings you drew. Korean text that extracts as garbage means the encoding path broke even though the render looked right.

## Sources

> Checked 2026-11-13.

| Claim | Source |
|---|---|
| Chromium headless `--print-to-pdf` flags, including tagged PDF export | <https://chromium.googlesource.com/chromium/src/+/refs/heads/main/headless/app/headless_shell_switches.cc> |
| `@page` size and margin rules | <https://www.w3.org/TR/css-page-3/> |
| `word-break: keep-all` semantics for CJK | <https://www.w3.org/TR/css-text-3/#word-break-property> |
| `print-color-adjust` | <https://www.w3.org/TR/css-color-adjust-1/> |
| Structure tree and tagged PDF requirement | <https://pdfa.org/resource/pdfa-2/> |

### Evidence grade

`LOCAL` for the flag behaviour, the `file://` requirement, and the font-timing failure, each reproduced on this machine. `SPEC` for the CSS and tagging claims.