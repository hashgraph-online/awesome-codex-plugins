# OOXML 요소 지도

`.docx` 안에서 어떤 것이 어디 있는지를 이름으로 찾습니다. 고치기 전에 파트나 요소를 확인해야 할 때, 리더의 오류가 위치를 알 수 없는 이름을 댈 때 씁니다.

`last_verified_at: 2026-11-13` — `build`가 만든 파일과 `python-docx`가 쓴 파일로 확인했습니다. 아래 ECMA-376 요소 이름은 두 경우에서 모두 같습니다.

## Contents

1. Parts
2. Body structure
3. Section properties
4. Runs and text
5. Images
6. Relationship types seen in practice
7. Order traps

## 1. 파트

| 파트 | 담는 것 | 루트 요소 |
|---|---|---|
| `[Content_Types].xml` | 확장자별 `Default`, 파트 이름별 `Override` | `Types` |
| `_rels/.rels` | 패키지 수준 관계(본문 문서, 코어 속성, 앱 속성) | `Relationships` |
| `word/document.xml` | `body` → 문단, 표, `sectPr` | `document` |
| `word/_rels/document.xml.rels` | 스타일, 설정, 글꼴 표, 머리글, 바닥글, 댓글, 이미지 | `Relationships` |
| `word/styles.xml` | `style` 항목: `paragraph`, `character`, `table`, `numbering` | `styles` |
| `word/numbering.xml` | 목록 id를 위한 `abstractNum`, `num` | `numbering` |
| `word/settings.xml` | `compat`, `rsid`, `trackChanges`, `defaultTabStop` | `settings` |
| `word/fontTable.xml` | `altName`, `charset`, `family`를 가진 `font` 항목 | `fonts` |
| `word/header1.xml`, `word/footer1.xml` | 페이지 장식. 이미지나 필드를 담으면 자체 `_rels`를 가짐 | `hdr`, `ftr` |
| `word/comments.xml` | `w:id`로 구분되는 `comment` 항목 | `comments` |
| `word/media/image1.png` | 이미지 이진 데이터. `r:embed`가 참조 | — |
| `docProps/core.xml` | `dc:title`, `dc:creator`, `cp:lastModifiedBy`, `dcterms:created` | `coreProperties` |
| `docProps/app.xml` | `Application`, `Pages`, `Words` | `Properties` |

## 2. 본문 구조

```
w:document
└── w:body
    ├── w:p                     문단
    │   ├── w:pPr
    │   │   ├── w:pStyle        이름 있는 문단 스타일
    │   │   ├── w:jc            정렬(left, center, both, right)
    │   │   ├── w:spacing       before, after, line, lineRule
    │   │   ├── w:ind           left, right, firstLine, hanging(트윕)
    │   │   ├── w:keepNext
    │   │   ├── w:pageBreakBefore
    │   │   ├── w:outlineLvl    탐색 계층
    │   │   ├── w:numPr         목록용 w:numId + w:ilvl
    │   │   ├── w:tabs          w:val과 w:leader(점선 리더)를 가진 w:tab
    │   │   └── w:rPr           문단 표시 서식
    │   └── w:r
    │       ├── w:rPr
    │       │   ├── w:rFonts    ascii, eastAsia, hAnsi, cs, hint
    │       │   ├── w:b / w:i / w:u
    │       │   ├── w:color     w:val은 # 없는 16진수
    │       │   ├── w:sz        반포인트(30 = 15포인트)
    │       │   ├── w:szCs
    │       │   └── w:lang      w:eastAsia="ko-KR"
    │       ├── w:t             텍스트. 앞뒤에 공백이 있으면 xml:space="preserve"
    │       ├── w:tab
    │       ├── w:br            페이지 나눔은 w:type="page"
    │       └── w:drawing       → wp:inline → a:graphic → pic:pic
    ├── w:tbl
    │   ├── w:tblPr             w:tblW(트윕 dxa), w:tblInd, w:tblBorders, w:tblLayout
    │   ├── w:tblGrid           열마다 w:gridCol
    │   └── w:tr
    │       ├── w:trPr          반복 머리글 행은 w:tblHeader
    │       └── w:tc
    │           ├── w:tcPr      w:tcW, w:gridSpan, w:shd(음영), w:vAlign
    │           └── w:p         셀에는 항상 문단이 최소 하나 들어감
    └── w:sectPr                페이지 크기, 여백, 머리글·바닥글 참조
```

## 3. 섹션 속성

`w:sectPr`가 `w:body` 끝에 있고 페이지를 지배합니다.

| 요소 | 의미 | 단위 |
|---|---|---|
| `w:pgSz` | `w:w`, `w:h` | 트윕(1밀리미터 ≈ 56.7) |
| `w:pgMar` | `w:top`, `w:right`, `w:bottom`, `w:left`, `w:header`, `w:footer`, `w:gutter` | 트윕 |
| `w:headerReference` | `w:type`(default, first, even), `r:id` | — |
| `w:footerReference` | 같음 | — |
| `w:cols` | 열 수와 간격 | — |
| `w:docGrid` | 동아시아 줄 격자를 위한 `w:linePitch` | — |

`w:tblPr` 안의 속성 순서는 일부 리더에게 중요합니다. `w:tblW`와 `w:tblInd`가 `w:tblLayout`보다 앞에 옵니다. 순서가 틀리면 엄격한 파서는 표를 거부하고 너그러운 파서는 열을 한 글자 폭으로 배치합니다.

## 4. 런과 텍스트

| 상황 | 요소 | 비고 |
|---|---|---|
| 일반 텍스트 | `w:t` | 텍스트가 공백으로 시작하거나 끝나면 `xml:space="preserve"` 추가 |
| 문단 안 줄바꿈 | `w:br` | 새 `w:p`가 아님 |
| 페이지 나눔 | `w:br w:type="page"` 또는 다음 문단의 `w:pageBreakBefore` | 둘 다 동작. 문단 속성이 더 깔끔 |
| 탭 | `w:tab` | 리더가 필요하면 `w:leader="dot"`을 담은 `w:tabs` 항목과 짝 |
| 삭제된 텍스트 | `w:del` 안 `w:delText` | `w:t`가 아님 |
| 필드 | `w:instrText`를 감싼 `w:fldChar` begin/separate/end | 결과 텍스트는 separate와 end 사이 |

## 5. 이미지

인라인 이미지에는 네 단계가 필요하고, `verify`가 모두 검사합니다.

1. 런 안의 `w:drawing`
2. `distT`/`distB`/`distL`/`distR`를 가진 `wp:inline`
3. `wp:extent`(`cx`, `cy`는 EMU. 1밀리미터 = 36000 EMU)와 고유 `id`를 가진 `wp:docPr`
4. `a:graphic` → `a:graphicData uri=".../picture"` → `pic:pic` → `pic:blipFill` → `a:blip r:embed="rIdN"`

`rIdN`은 `word/_rels/document.xml.rels`에 `Type=".../image"`, `Target="media/image1.png"`로 있어야 하고, 확장자는 콘텐츠 타입에 `Default`가 있어야 합니다.

## 6. 실무에서 보는 관계 타입

| 타입 접미사 | 대상 |
|---|---|
| `/officeDocument` | `word/document.xml` |
| `/styles` | `word/styles.xml` |
| `/settings` | `word/settings.xml` |
| `/fontTable` | `word/fontTable.xml` |
| `/numbering` | `word/numbering.xml` |
| `/header`, `/footer` | 머리글 또는 바닥글 파트 |
| `/comments` | `word/comments.xml` |
| `/image` | 미디어 파일 |
| `/core-properties` | `docProps/core.xml` |
| `/extended-properties` | `docProps/app.xml` |

## 7. 순서 함정

- `w:pPr` 자식은 스키마 순서가 있습니다. `w:pStyle`, `w:keepNext`, `w:keepLines`, `w:pageBreakBefore`, `w:tabs`, `w:spacing`, `w:ind`, `w:jc`, `w:outlineLvl`, `w:rPr`. 순서가 틀리면 조용히 받아들여진 뒤 무시될 수 있습니다.
- `w:rPr` 순서는 `w:rFonts`, `w:b`, `w:i`, `w:u`, `w:color`, `w:sz`, `w:szCs`, `w:lang`입니다.
- `w:tcPr` 순서는 `w:tcW`, `w:gridSpan`, `w:shd`, `w:vAlign`입니다.
- 셀은 문단으로 끝나야 합니다. 중첩 표만 든 셀은 유효하지 않습니다.

## Sources

> Checked 2026-11-13

- ECMA-376 Part 1, WordprocessingML 요소 참조 — https://ecma-international.org/publications-and-standards/standards/ecma-376/
- Microsoft Learn, WordprocessingML 구조와 요소 순서 — https://learn.microsoft.com/en-us/office/open-xml/word/structure-of-a-wordprocessingml-document
- Microsoft Learn, Open XML 패키지 관계 — https://learn.microsoft.com/en-us/office/open-xml/word/how-to-manipulate-relationships
