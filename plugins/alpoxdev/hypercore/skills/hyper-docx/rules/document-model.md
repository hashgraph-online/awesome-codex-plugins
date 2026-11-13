# Document Model

How a `.docx` is built, what the spec means, and how an existing package is changed without breaking it.

## 1. What a package actually is

A `.docx` is a zip of XML parts. A file a word processor opens without repair has these parts and nothing missing:

| Part | Role | Must exist |
|---|---|---|
| `[Content_Types].xml` | maps extensions and part names to media types | always |
| `_rels/.rels` | package relationships; resolves the main document part | always |
| `word/document.xml` | body content: paragraphs, tables, section properties | always |
| `word/_rels/document.xml.rels` | relationships owned by the document part | when any target exists |
| `word/styles.xml` | named paragraph and character styles | for predictable formatting |
| `word/settings.xml` | editor settings, compatibility mode | recommended |
| `word/fontTable.xml` | declared fonts | recommended |
| `word/footer1.xml`, `word/header1.xml` | page furniture | when referenced |
| `word/comments.xml` | comments | when referenced |
| `word/media/*` | embedded images | when referenced |
| `docProps/core.xml`, `docProps/app.xml` | metadata | recommended |

Three invariants decide whether a file opens:

1. Every `Override` in `[Content_Types].xml` names a part that exists, and every part that is neither `.xml` nor `.rels` has a `Default` extension entry.
2. Every internal relationship target resolves from the part that owns the `.rels` file, not from the package root.
3. Every relationship id used in the content (`r:embed`, `r:id` on header and footer references) is declared in that part's `.rels`.

`verify` checks all three. A file that fails any of them is the file Word offers to repair, and the repair dialog is the reader's equivalent of a failing verify.

## 2. The spec

`build` takes one JSON object. Every key is optional except `blocks`.

| Key | Type | Default | Meaning |
|---|---|---|---|
| `title` | string | — | document title, also written into core properties |
| `author` | string | — | creator and last-modified-by |
| `subject` | string | — | core property subject |
| `page` | string or object | `official-kr` | `a4`, `official-kr`, `letter`, or `{size:[twipW,twipH], margin_mm:{...}}` |
| `margin_mm` | object | preset | overrides any edge: `top`, `bottom`, `left`, `right`, `header`, `footer` |
| `font` | string or object | 휴먼명조 | one name for all scripts, or `{ascii, eastAsia, hAnsi}` |
| `size_pt` | number | 15 | body size |
| `line_pct` | number | 200 | line spacing as a percentage of single |
| `footer` | bool | true | page number footer `－ N / M` |
| `min_chars` | number | — | a floor the `verify` length check enforces |
| `blocks` | array | required | ordered content, described below |

### Blocks

| `type` | Keys | Result |
|---|---|---|
| `title` | `text`, `size`, `align`, `after_pt` | centered title paragraph with the `Title` style |
| `heading` | `text`, `level` 1–3 | `Heading1`–`Heading3`, outline level set for navigation |
| `paragraph` | `text`, `bold`, `italic`, `underline`, `color`, `align`, `style`, `size`, `font`, `left_mm`, `first_mm`, `hanging_mm`, `line_pct`, `before_pt`, `after_pt`, `keep_next`, `page_break_before` | one body paragraph |
| `item` | `mark`, `text`, `left_mm`, `hanging_mm` | one line with an explicit mark (`가.`) — Korean item hierarchy |
| `row` | `text`, `value` | one line with a right-aligned dotted leader, as in 붙임 lists |
| `numbered` | `items`, item may be `{text, depth}` | numbered list `1.` `2.` |
| `bullets` | `items` | bulleted list |
| `table` | `rows` (array of arrays), `widths_mm`, `header`, `header_fill`, `font_size`, `align`, `first_col_bold` | bordered table, header row repeated across pages |
| `figure` | `path`, `width_mm`, `caption` | inline PNG or JPEG plus an optional caption |
| `page_break` | — | paragraph carrying a page break before it |
| `spacer` | `line_pct`, `after_pt` | empty paragraph for vertical space |

A single-line text value containing `\n` becomes multiple lines inside one paragraph; do not build one paragraph per line when the break is deliberate.

## 3. Determinism

The same spec must produce the same bytes. Two things make that true: parts are written in a fixed order with a fixed timestamp, and nothing reads the clock during a build. A document that changes bytes between identical builds cannot be diffed, cached, or audited.

## 4. Editing an existing package

Read the part, change it, write it back, leave every other part byte-identical:

```python
import sys
sys.path.insert(0, "assets/tools")
from docxlib import Package, qn, read_text
from xml.etree import ElementTree as ET

pkg = Package.open("in.docx")
for paragraph in pkg.document().iter(qn("w:p")):
    if "기존 문장" in read_text(paragraph):
        ...                     # mutate this paragraph's tree
        break
pkg.dirty(pkg.document_part())  # serialize exactly the parts that changed
pkg.save("out.docx")
```

Rules for this path:

- Change the tree, then call `dirty(part)` once per changed part. Saving flushes any remaining dirty part, but naming them keeps the intent readable.
- Never write a new part without `ensure_override` (an `.xml` part) or `ensure_default` (a media extension) plus a relationship; a part nobody references is dead weight, and a relationship to a missing part is a repair prompt.
- When adding a part that is referenced from the content, add both the part and the `.rels` entry before saving.
- Keep the original prefixes: `docxlib.register_namespaces` reads them from the file's own declarations, so `w:`, `r:`, `wp:` come back as they went in.

## 5. Limits worth knowing

- Footnotes, endnotes, content controls, and math are not built by this toolset. Adding them means writing the part, the relationship, the content type, and the body reference by hand; report that as a limit instead of emitting a placeholder.
- Sections: one section per document. Multiple sections with different page geometry need a `w:pPr/w:sectPr` per break; `verify` reads the body-level section only.
- A field (`PAGE`, `NUMPAGES`) renders a placeholder number until the file is opened by a word processor that evaluates fields. The placeholder is `1` by design, not a wrong page count.

## Sources

> Checked 2026-11-13

- ECMA-376 Part 1, package and WordprocessingML — https://ecma-international.org/publications-and-standards/standards/ecma-376/
- Microsoft Learn, Open XML SDK WordprocessingML structure — https://learn.microsoft.com/en-us/office/open-xml/word/structure-of-a-wordprocessingml-document
- python-docx package documentation — https://python-docx.readthedocs.io/
