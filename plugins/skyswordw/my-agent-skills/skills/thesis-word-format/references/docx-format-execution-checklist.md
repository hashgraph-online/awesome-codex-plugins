# DOCX Format Execution Checklist

Use this when the user asks for the whole Word thesis to follow the standard format.

## 1. Preflight

- Work on a copy under `output/doc/`; never edit files in `raw/`.
- Inspect sections, styles, headings, tables, figures, equations, headers, footers, fields, and reference paragraphs before editing.
- If the document contains Zotero fields, hyperlinks, bookmarks, comments, footnotes, or text boxes, record them before running scripts that rebuild runs.

## 2. Page Setup

- Paper: A4.
- Target print block: 160 mm x 247 mm, excluding header and footer lines.
- Use margins that preserve that block on A4. Starting point: left/right about 25 mm and top/bottom about 25 mm, then verify rendered width/height against the standard.
- Preserve section breaks unless they are clearly accidental. Check odd/even pages if double-sided output is required.

## 3. Word style mapping

Map the thesis styles explicitly; do not rely on imported `.doc` styles from `textutil`.

| Content | Word style mapping | Standard target |
|---|---|---|
| Body text | `Normal` | 小四号宋体; Latin/digits Times New Roman; consistent line spacing |
| First-level heading | `Heading 1` | 二号黑体, centered, occupies about 3 lines |
| Second-level heading | `Heading 2` | 三号黑体, left aligned, occupies about 2 lines |
| Third-level heading | `Heading 3` | 四号黑体, left aligned, occupies about 2 lines |
| Fourth-level heading | `Heading 4` | 小四号黑体, left aligned, occupies about 1 line |
| Figure caption | caption paragraph | below figure, 5 号 font, chapter numbering like `图2.1` |
| Table caption | caption paragraph | above table, centered, 5 号宋体, chapter numbering like `表2.1` |
| References | reference paragraph style | `[n] Author. Title[type]. ...`, consistent hanging indent if used |

## 4. Document Structure

- Treat `摘要`, `Abstract`, `目录`, `参考文献`, `致谢`, academic achievements, and personal resume as first-level headings.
- Keep chapter headings as first-level headings, e.g. `第一章 绪论` or `第1章 XXX`.
- Rebuild or refresh the table of contents only after heading styles are stable.
- Apply the page header (页眉) from the abstract onward: left side `东北大学硕士、博士学位论文`, right side chapter number/title, 5 号楷体.
- Add footer (页脚) page numbers centered at the bottom. Use Arabic numbers and match body font size; decorate as `·3·` or `-3-` only if the current school template expects it.

## 5. References and Citation Markers

- Generate or verify final reference numbering before citation-marker styling.
- Run `scripts/normalize_citation_markers.py` on the final static DOCX to set terminal `[n]` markers as superscript.
- Review the JSON report for `rewritten_author_led_citations`. The script rewrites English author-led sentence/clause openings such as `Sun等[n]...` and `Chen等[n]...` to `文献[n]...`; `文献` remains baseline and the `[n]` marker is still superscript. Inspect those changes when author identity matters.
- Confirm reference-list entries remain baseline text, not superscript.
- For Zotero dynamic deliverables, select `NEU Thesis GB/T 7714-2015 Numeric` before Refresh and then run `scripts/postprocess_zotero_bibliography.py` to remove `[[ZOTERO_BIBLIOGRAPHY`/`]]` residue and apply hanging indent with normal thesis line spacing.

## 6. Rendered Validation

- Convert the final DOCX with LibreOffice:

```bash
soffice --headless --convert-to pdf --outdir tmp/render output/doc/final.docx
```

- Render pages with Poppler:

```bash
pdftoppm -png -f 1 -l 5 tmp/render/final.pdf tmp/render/page
```

- Check the PDF with `pdfinfo`: page size must be A4.
- Inspect representative pages: cover/front matter, first chapter page, dense body page, table/figure page, reference-list page.
- Verify no overlapping text, clipped captions, broken page numbers, missing header/footer, or stray local reference blocks.
- Spot-check page density: body pages should stay near 30-35 lines/page and 35-38 Chinese characters/line. Treat this as a layout check, not an exact automated invariant.

## 7. risk boundary

- `normalize_citation_markers.py` handles normal body paragraphs and table-cell paragraphs. It does not handle headers, footers, footnotes/endnotes, text boxes, comments, or Word field codes.
- The script rebuilds affected paragraph runs. It preserves common character formatting, but complex XML such as hyperlinks, bookmarks, Zotero fields, and comments can be damaged. For documents with those structures, make a checkpoint copy and inspect XML/rendered output before replacing the final Word file.
- Do not create fake Zotero dynamic fields. If dynamic citations are required, use the official Word + Zotero plugin workflow.
