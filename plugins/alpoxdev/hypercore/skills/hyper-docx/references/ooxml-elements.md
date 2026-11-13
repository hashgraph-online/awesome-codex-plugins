# OOXML Element Map

Where a thing lives in a `.docx`, by name. Use this when a part or element must be located before editing, and when a reader's error names something you cannot place.

`last_verified_at: 2026-11-13` — checked against files produced by `build` and against a `python-docx`-written file; the ECMA-376 element names below are stable across those.

## Contents

1. Parts
2. Body structure
3. Section properties
4. Runs and text
5. Images
6. Relationship types seen in practice
7. Order traps

## 1. Parts

| Part | Holds | Root element |
|---|---|---|
| `[Content_Types].xml` | `Default` by extension, `Override` by part name | `Types` |
| `_rels/.rels` | package-level relationships (office document, core properties, app properties) | `Relationships` |
| `word/document.xml` | `body` → paragraphs, tables, `sectPr` | `document` |
| `word/_rels/document.xml.rels` | styles, settings, fontTable, header, footer, comments, images | `Relationships` |
| `word/styles.xml` | `style` entries: `paragraph`, `character`, `table`, `numbering` | `styles` |
| `word/numbering.xml` | `abstractNum`, `num` for list ids | `numbering` |
| `word/settings.xml` | `compat`, `rsid`, `trackChanges`, `defaultTabStop` | `settings` |
| `word/fontTable.xml` | `font` entries with `altName`, `charset`, `family` | `fonts` |
| `word/header1.xml`, `word/footer1.xml` | page furniture with its own `_rels` when it holds images or fields | `hdr`, `ftr` |
| `word/comments.xml` | `comment` entries keyed by `w:id` | `comments` |
| `word/media/image1.png` | binary image data, referenced by `r:embed` | — |
| `docProps/core.xml` | `dc:title`, `dc:creator`, `cp:lastModifiedBy`, `dcterms:created` | `coreProperties` |
| `docProps/app.xml` | `Application`, `Pages`, `Words` | `Properties` |

## 2. Body structure

```
w:document
└── w:body
    ├── w:p                     paragraph
    │   ├── w:pPr
    │   │   ├── w:pStyle        named paragraph style
    │   │   ├── w:jc            alignment (left, center, both, right)
    │   │   ├── w:spacing       before, after, line, lineRule
    │   │   ├── w:ind           left, right, firstLine, hanging (twips)
    │   │   ├── w:keepNext
    │   │   ├── w:pageBreakBefore
    │   │   ├── w:outlineLvl    navigation level
    │   │   ├── w:numPr         w:numId + w:ilvl for lists
    │   │   ├── w:tabs          w:tab with w:val and w:leader (dot leader)
    │   │   └── w:rPr           paragraph mark formatting
    │   └── w:r
    │       ├── w:rPr
    │       │   ├── w:rFonts    ascii, eastAsia, hAnsi, cs, hint
    │       │   ├── w:b / w:i / w:u
    │       │   ├── w:color     w:val hex without #
    │       │   ├── w:sz        half-points (30 = 15 pt)
    │       │   ├── w:szCs
    │       │   └── w:lang      w:eastAsia="ko-KR"
    │       ├── w:t             text, xml:space="preserve" when it has edge spaces
    │       ├── w:tab
    │       ├── w:br            w:type="page" for a page break
    │       └── w:drawing       → wp:inline → a:graphic → pic:pic
    ├── w:tbl
    │   ├── w:tblPr             w:tblW (dxa twips), w:tblInd, w:tblBorders, w:tblLayout
    │   ├── w:tblGrid           w:gridCol per column
    │   └── w:tr
    │       ├── w:trPr          w:tblHeader for the repeating header row
    │       └── w:tc
    │           ├── w:tcPr      w:tcW, w:gridSpan, w:shd (fill), w:vAlign
    │           └── w:p         a cell always contains at least one paragraph
    └── w:sectPr                page size, margins, header and footer references
```

## 3. Section properties

`w:sectPr` sits at the end of `w:body` and controls the page:

| Element | Meaning | Unit |
|---|---|---|
| `w:pgSz` | `w:w`, `w:h` | twips (1 mm ≈ 56.7) |
| `w:pgMar` | `w:top`, `w:right`, `w:bottom`, `w:left`, `w:header`, `w:footer`, `w:gutter` | twips |
| `w:headerReference` | `w:type` (default, first, even), `r:id` | — |
| `w:footerReference` | same | — |
| `w:cols` | column count and spacing | — |
| `w:docGrid` | `w:linePitch` for East Asian line grid | — |

Attribute order inside `w:tblPr` matters to some readers: `w:tblW` and `w:tblInd` come before `w:tblLayout`. Out of order, strict parsers reject the table and lenient ones lay the columns out at one character wide.

## 4. Runs and text

| Situation | Element | Note |
|---|---|---|
| Plain text | `w:t` | add `xml:space="preserve"` when the text begins or ends with a space |
| Line break inside a paragraph | `w:br` | not a new `w:p` |
| Page break | `w:br w:type="page"`, or `w:pageBreakBefore` on the next paragraph | both work; the paragraph property is tidier |
| Tab | `w:tab` | pairs with a `w:tabs` entry carrying `w:leader="dot"` for a leader |
| Deleted text | `w:delText` inside `w:del` | never `w:t` |
| Field | `w:fldChar` begin/separate/end around `w:instrText` | result text sits between separate and end |

## 5. Images

An inline image needs four levels, and every one of them is checked by `verify`:

1. `w:drawing` in a run
2. `wp:inline` with `distT`/`distB`/`distL`/`distR`
3. `wp:extent` (`cx`, `cy` in EMU; 1 mm = 36000 EMU) and `wp:docPr` with a unique `id`
4. `a:graphic` → `a:graphicData uri=".../picture"` → `pic:pic` → `pic:blipFill` → `a:blip r:embed="rIdN"`

`rIdN` must be in `word/_rels/document.xml.rels` with `Type=".../image"` and `Target="media/image1.png"`; the extension must have a `Default` in the content types.

## 6. Relationship types seen in practice

| Type suffix | Target |
|---|---|
| `/officeDocument` | `word/document.xml` |
| `/styles` | `word/styles.xml` |
| `/settings` | `word/settings.xml` |
| `/fontTable` | `word/fontTable.xml` |
| `/numbering` | `word/numbering.xml` |
| `/header`, `/footer` | the header or footer part |
| `/comments` | `word/comments.xml` |
| `/image` | a media file |
| `/core-properties` | `docProps/core.xml` |
| `/extended-properties` | `docProps/app.xml` |

## 7. Order traps

- `w:pPr` children have a schema order: `w:pStyle`, `w:keepNext`, `w:keepLines`, `w:pageBreakBefore`, `w:tabs`, `w:spacing`, `w:ind`, `w:jc`, `w:outlineLvl`, `w:rPr`. A wrong order can be accepted quietly and then ignored.
- `w:rPr` order: `w:rFonts`, `w:b`, `w:i`, `w:u`, `w:color`, `w:sz`, `w:szCs`, `w:lang`.
- `w:tcPr` order: `w:tcW`, `w:gridSpan`, `w:shd`, `w:vAlign`.
- A cell must end with a paragraph; a table cell holding only a nested table is invalid.

## Sources

> Checked 2026-11-13

- ECMA-376 Part 1, WordprocessingML element reference — https://ecma-international.org/publications-and-standards/standards/ecma-376/
- Microsoft Learn, WordprocessingML structure and element ordering — https://learn.microsoft.com/en-us/office/open-xml/word/structure-of-a-wordprocessingml-document
- Microsoft Learn, Open XML package relationships — https://learn.microsoft.com/en-us/office/open-xml/word/how-to-manipulate-relationships
