# HTML을 PDF로

> PDF를 만드는 경로는 둘이고 서로 대체할 수 없습니다. 잘못 고르면 디자인을 잃거나 아예 실행하지 못합니다.

## 1. 어느 경로인가

| 요구 | 경로 | 명령 |
|---|---|---|
| 기존 HTML/CSS가 브라우저에서 보이는 그대로여야 함 | `html` | `engine.js html <file.html> --out <out.pdf>` |
| 웹 페이지 없이 데이터로 계약서·청구서·보고서·양식을 만듦 | `build` | `engine.js build --spec <spec.json> --out <out.pdf>` |
| 결과에 태그와 언어 태그가 필요 | `html`(구조 트리를 냄) | `engine.js html ... --tagged` |
| 브라우저가 설치돼 있지 않음 | `build` | `engine.js build ...` |
| CSS로 인쇄 규칙·쪽 나눔·반복 머리글을 지정 | `html` | `engine.js html ...` |
| 실행마다 쪽 나눔이 흔들리면 안 됨 | `build` | `engine.js build ...` |

`build` 경로는 JSON 스펙을 CoreGraphics로 직접 배치합니다. 임의의 CSS를 재현하지 못합니다. float, flexbox, grid, `@media print`, 설치되지 않은 웹 글꼴은 안 됩니다. 아니라고 말하면 사용자가 첫 렌더에서 보게 되는 거짓말이 됩니다.

## 2. HTML 경로

```
engine.js html <input.html> --out <out.pdf> [--tagged] [--paper a4|letter] [--margin 20mm] [--landscape] [--chromium <path>]
```

동작: 엔진이 Chromium 계열 실행 파일을 찾고(`findHtmlRenderer`) 헤드리스로 실행합니다.

```
--headless --disable-gpu --export-tagged-pdf --print-to-pdf=<out> --no-pdf-header-footer <file://...>
```

| 규칙 | 이유 |
|---|---|
| `--export-tagged-pdf`를 항상 유지 | 없으면 구조 트리가 없고 화면 낭독기는 구분 없는 덩어리 하나를 받음 |
| 경로가 아니라 `file://` URL을 넘김 | 맨 경로는 검색어로 읽혀 오류 쪽을 인쇄함 |
| 용지는 CSS `@page`나 플래그 중 하나로만 지정 | 두 출처가 어긋나면 플래그가 조용히 이김 |
| `@font-face src`는 절대 `file://` URL이나 `data:` URI | 상대 URL은 HTML 파일이 아니라 임시 프로필 기준으로 풀려 글꼴이 조용히 대체됨 |
| 글꼴·이미지 로드를 기다림 | Chromium은 load 이벤트에서 인쇄하고, 그 뒤 끝나는 `@font-face`는 대체 글꼴로 인쇄됨. 글꼴을 미리 읽거나 `data:`로 인라인 |
| 배경 그래픽 | 배경이 필요한 요소에 `print-color-adjust: exact`, 없으면 인쇄 스타일이 배경을 제거 |

렌더러를 찾지 못하면 명령이 찾아본 경로와 함께 `blocked NO_HTML_RENDERER`를 반환합니다. 묻지 않고 브라우저를 설치해 넘어가지 마세요. 데이터 기반 문서면 `build`를 쓰고, 아니면 막힌 사실을 보고합니다.

## 3. HTML 경로의 한국어 사항

- 한국어 웹 글꼴은 수 메가바이트 다운로드입니다. 원격 URL을 가리키는 `@font-face`는 인쇄 전에 끝나지 않을 수 있습니다. 로컬 부분집합을 인라인하거나 설치된 글꼴을 씁니다.
- 브라우저가 한국어 줄을 공백 없는 경계에서 단어 중간에 끊지 않게 막는 확실한 방법은 `word-break: keep-all`뿐입니다. 기본값 `normal`은 한국어에서 모든 글자에서 끊습니다.
- 줄 높이 1.6 이상. 한글에서 브라우저 기본 1.2는 꽉 찬 덩어리처럼 보입니다.
- `text-align: justify`에 기대지 마세요. Chromium의 한국어 양끝 맞춤은 글자 사이 공간을 고르지 않게 늘립니다.
- 결과 확인: `rawScan`에 `structureTree: true`와 한글 글꼴의 `FontFile2`/`FontFile3` 항목이 있어야 합니다.

## 4. build 경로

스펙은 JSON입니다. 블록 목록과 필드 표 전체는 `references/layout-spec.md`에 있습니다. 형태:

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

`page.width`/`page.height`는 포인트 단위 A4가 기본값이고 `page.margin`은 56.7 pt(20 mm)입니다. 여백은 한 값이며 네 변이 아닙니다. 블록 목록과 각 필드는 `references/layout-spec.md`에 있습니다.

| 속성 | 보장 |
|---|---|
| `lang` | CoreGraphics가 언어 키를 무시하므로 추가 전용 증분 갱신으로 카탈로그에 기록 |
| 결정성 | 같은 스펙은 같은 기기·같은 OS 버전에서 같은 배치와 같은 텍스트를 냅니다. 실행마다 다른 필드는 생성 시각 하나입니다 |
| 표 쪽 나눔 | 쪽을 넘는 표가 다음 쪽에서 머리글 행을 다시 그림. 행은 쪽 사이에서 쪼개지지 않음 |
| 글꼴 없음 | `resolveFont`로 대체하고 실패하지 않고 `FONT_FALLBACK`을 보고 |

## 5. 두 경로 공통 검증

1. `engine.js check <out.pdf>` — 모든 이슈 코드를 읽습니다. `build` 경로에서 `NO_STRUCTURE_TREE`는 예상된 결과이고 숨기지 말고 보고합니다.
2. `engine.js info <out.pdf>` — 쪽 수, 쪽 크기, `docTitle`이 의도한 값인지 확인합니다.
3. `engine.js render <out.pdf> --out-dir <dir>` — 첫 쪽과 표가 넘어가는 쪽을 엽니다. 오른쪽 끝, 머리글 반복, 바닥글 쪽 번호를 봅니다.
4. `engine.js text <out.pdf>` — 추출한 텍스트에 그린 문자열이 있어야 합니다. 렌더가 맞아도 한국어가 쓰레기로 추출되면 인코딩 경로가 깨진 것입니다.

## Sources

> Checked 2026-11-13.

| Claim | Source |
|---|---|
| Chromium 헤드리스 `--print-to-pdf` 플래그와 태그 PDF 내보내기 | <https://chromium.googlesource.com/chromium/src/+/refs/heads/main/headless/app/headless_shell_switches.cc> |
| `@page` 크기와 여백 규칙 | <https://www.w3.org/TR/css-page-3/> |
| CJK에서 `word-break: keep-all`의 의미 | <https://www.w3.org/TR/css-text-3/#word-break-property> |
| `print-color-adjust` | <https://www.w3.org/TR/css-color-adjust-1/> |
| 구조 트리와 태그 PDF 요구 | <https://pdfa.org/resource/pdfa-2/> |

### Evidence grade

플래그 동작, `file://` 요구, 글꼴 타이밍 실패는 이 기기에서 재현한 `LOCAL`입니다. CSS와 태그 관련 주장은 `SPEC`입니다.