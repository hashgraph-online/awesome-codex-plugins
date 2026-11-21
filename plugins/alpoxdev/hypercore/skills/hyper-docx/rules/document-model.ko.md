# 문서 모델

`.docx`가 어떻게 만들어지는지, 스펙이 무엇을 뜻하는지, 기존 패키지를 깨뜨리지 않고 고치는 방법을 정합니다.

## 1. 패키지의 실체

`.docx`는 XML 파트를 담은 zip입니다. 워드 프로세서가 복구 없이 여는 파일은 아래 파트를 빠짐없이 갖습니다.

| 파트 | 역할 | 필수 여부 |
|---|---|---|
| `[Content_Types].xml` | 확장자와 파트 이름을 미디어 타입으로 대응 | 항상 |
| `_rels/.rels` | 패키지 관계. 본문 파트를 찾는 출발점 | 항상 |
| `word/document.xml` | 본문: 문단, 표, 섹션 속성 | 항상 |
| `word/_rels/document.xml.rels` | 본문 파트가 소유한 관계 | 대상이 있을 때 |
| `word/styles.xml` | 이름 있는 문단·문자 스타일 | 예측 가능한 서식에 필요 |
| `word/settings.xml` | 편집기 설정, 호환 모드 | 권장 |
| `word/fontTable.xml` | 선언된 글꼴 | 권장 |
| `word/footer1.xml`, `word/header1.xml` | 페이지 장식 | 참조될 때 |
| `word/comments.xml` | 댓글 | 참조될 때 |
| `word/media/*` | 내장 이미지 | 참조될 때 |
| `docProps/core.xml`, `docProps/app.xml` | 메타데이터 | 권장 |

파일이 열리는지는 세 가지 불변식이 정합니다.

1. `[Content_Types].xml`의 모든 `Override`가 실제로 있는 파트를 가리키고, `.xml`도 `.rels`도 아닌 파트는 모두 `Default` 확장자 항목을 갖습니다.
2. 모든 내부 관계 대상은 패키지 루트가 아니라 그 `.rels` 파일을 소유한 파트 기준으로 풀립니다.
3. 본문에서 쓰는 관계 id(`r:embed`, 머리글·바닥글 참조의 `r:id`)가 모두 해당 파트의 `.rels`에 선언돼 있습니다.

`verify`가 이 셋을 검사합니다. 하나라도 어긋난 파일이 워드가 복구를 제안하는 파일이고, 복구 대화상자는 검증 실패를 리더가 보여주는 형태입니다.

## 2. 스펙

`build`는 JSON 객체 하나를 받습니다. `blocks`를 뺀 모든 키는 선택입니다.

| 키 | 타입 | 기본값 | 의미 |
|---|---|---|---|
| `title` | 문자열 | — | 문서 제목. 코어 속성에도 기록 |
| `author` | 문자열 | — | 작성자와 마지막 수정자 |
| `subject` | 문자열 | — | 코어 속성 주제 |
| `page` | 문자열 또는 객체 | `official-kr` | `a4`, `official-kr`, `letter`, 또는 `{size:[twipW,twipH], margin_mm:{...}}` |
| `margin_mm` | 객체 | 프리셋 | 모든 여백을 덮어씀: `top`, `bottom`, `left`, `right`, `header`, `footer` |
| `font` | 문자열 또는 객체 | 휴먼명조 | 한 이름으로 모든 문자 체계, 또는 `{ascii, eastAsia, hAnsi}` |
| `size_pt` | 숫자 | 15 | 본문 크기 |
| `line_pct` | 숫자 | 200 | 줄 간격을 단일 간격의 백분율로 |
| `footer` | 불리언 | true | 페이지 번호 바닥글 `－ N / M` |
| `min_chars` | 숫자 | — | `verify` 길이 검사가 강제하는 하한 |
| `blocks` | 배열 | 필수 | 순서가 있는 내용. 아래에서 설명 |

### 블록

| `type` | 키 | 결과 |
|---|---|---|
| `title` | `text`, `size`, `align`, `after_pt` | `Title` 스타일을 쓰는 가운데 정렬 제목 문단 |
| `heading` | `text`, `level` 1~3 | `Heading1`~`Heading3`. 탐색용 개요 수준 설정 |
| `paragraph` | `text`, `bold`, `italic`, `underline`, `color`, `align`, `style`, `size`, `font`, `left_mm`, `first_mm`, `hanging_mm`, `line_pct`, `before_pt`, `after_pt`, `keep_next`, `page_break_before` | 본문 문단 하나 |
| `item` | `mark`, `text`, `left_mm`, `hanging_mm` | 기호를 직접 준 줄 하나(`가.`). 한국어 항목 계층 |
| `row` | `text`, `value` | 오른쪽 정렬 점선 리더가 붙은 줄. 붙임 목록 형태 |
| `numbered` | `items`, 항목은 `{text, depth}` 가능 | 번호 목록 `1.` `2.` |
| `bullets` | `items` | 글머리 기호 목록 |
| `table` | `rows`(배열의 배열), `widths_mm`, `header`, `header_fill`, `font_size`, `align`, `first_col_bold` | 테두리 표. 머리글 행은 페이지 넘김마다 반복 |
| `figure` | `path`, `width_mm`, `caption` | 인라인 PNG 또는 JPEG와 선택적 캡션 |
| `page_break` | — | 앞에서 페이지를 나누는 문단 |
| `spacer` | `line_pct`, `after_pt` | 세로 여백용 빈 문단 |

줄바꿈이 의도된 곳에서 한 줄짜리 문자열 값에 `\n`을 넣으면 한 문단 안에서 여러 줄이 됩니다. 줄마다 문단을 따로 만들지 않습니다.

## 3. 결정성

같은 스펙은 같은 바이트를 만들어야 합니다. 파트를 고정 순서와 고정 시각으로 쓰고, 빌드 중에 시계를 읽지 않기 때문에 그렇게 됩니다. 같은 스펙의 빌드가 바이트를 바꾸면 diff도 캐시도 감사도 할 수 없습니다.

## 4. 기존 패키지 편집

파트를 읽고, 고치고, 되쓰고, 나머지 파트는 바이트 그대로 둡니다.

```python
import sys
sys.path.insert(0, "assets/tools")
from docxlib import Package, qn, read_text
from xml.etree import ElementTree as ET

pkg = Package.open("in.docx")
for paragraph in pkg.document().iter(qn("w:p")):
    if "기존 문장" in read_text(paragraph):
        ...                     # 이 문단의 트리를 고칩니다
        break
pkg.dirty(pkg.document_part())  # 바뀐 파트만 직렬화합니다
pkg.save("out.docx")
```

이 경로의 규칙입니다.

- 트리를 고친 뒤 바뀐 파트마다 `dirty(part)`를 한 번 부릅니다. 저장할 때 남은 dirty 파트도 함께 기록되지만, 이름을 붙여 두면 의도가 읽힙니다.
- `ensure_override`(`.xml` 파트)나 `ensure_default`(미디어 확장자)에 관계를 더하지 않고 새 파트를 쓰지 않습니다. 아무도 참조하지 않는 파트는 군더더기이고, 없는 파트를 가리키는 관계는 복구 요청입니다.
- 본문에서 참조하는 파트를 더할 때는 저장 전에 파트와 `.rels` 항목을 함께 넣습니다.
- 원래 접두사를 유지합니다. `docxlib.register_namespaces`가 파일 자체의 선언을 읽으므로 `w:`, `r:`, `wp:`가 들어온 그대로 나옵니다.

## 5. 알아 둘 한계

- 각주, 미주, 콘텐츠 컨트롤, 수식은 이 도구 모음이 만들지 않습니다. 넣으려면 파트, 관계, 콘텐츠 타입, 본문 참조를 직접 써야 하므로, 빈 자리표시자를 내보내는 대신 한계로 보고합니다.
- 섹션은 문서당 하나입니다. 페이지 기하가 다른 여러 섹션은 나눔마다 `w:pPr/w:sectPr`가 필요하고, `verify`는 본문 수준 섹션만 읽습니다.
- 필드(`PAGE`, `NUMPAGES`)는 필드를 계산하는 워드 프로세서가 파일을 열기 전까지 자리표시자 숫자를 보여 줍니다. 그 자리표시자는 설계상 `1`이며 잘못 센 페이지 수가 아닙니다.

## Sources

> Checked 2026-11-13

- ECMA-376 Part 1, 패키지와 WordprocessingML — https://ecma-international.org/publications-and-standards/standards/ecma-376/
- Microsoft Learn, Open XML SDK WordprocessingML 구조 — https://learn.microsoft.com/en-us/office/open-xml/word/structure-of-a-wordprocessingml-document
- python-docx 패키지 문서 — https://python-docx.readthedocs.io/
