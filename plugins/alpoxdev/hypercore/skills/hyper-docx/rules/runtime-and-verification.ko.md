# 런타임과 검증

이 기계가 실제로 할 수 있는 일, 문서가 옳다는 것을 증명하는 방법, 증명하지 못한 것을 말하는 방법을 정합니다.

## 1. 주장 전에 확인

`python3 assets/tools/hyper_docx.py doctor`가 JSON 객체 하나를 출력합니다. 인터프리터를 읽고, Chromium 계열 바이너리와 LibreOffice를 찾고, 그 결과로 능력을 정합니다.

| 능력 | 필요 조건 | 없을 때 의미 |
|---|---|---|
| `build`, `inspect`, `verify`, `tracked_changes`, `comments` | Python 3.8 이상만 | 사라지지 않음. 표준 라이브러리 |
| `html_render` | Python 3.8 이상 | 사라지지 않음 |
| `pdf_render` | Chromium 계열 바이너리 | HTML 증거만 가능. PDF와 쪽 이미지 없음 |
| `docx_to_pdf` | LibreOffice(`soffice`) | 워드 엔진 변환 없음. HTML 렌더가 유일한 배치 증거 |
| `png_preview` | LibreOffice 또는 QuickLook(`qlmanage`) | 미리보기 이미지 없음 |
| `docx_to_text` | macOS의 `textutil`, 없으면 표준 라이브러리 리더 | 내장 `text` 명령은 항상 동작 |

프로브는 브라우저를 Playwright 캐시(`~/Library/Caches/ms-playwright`, `~/.cache/ms-playwright`)와 일반 애플리케이션 경로에서 찾습니다. 2026-11-13 이 기계의 결과는 Python 3.9.6, Playwright `chrome-headless-shell`, `textutil`, `qlmanage`, `sips`가 있고 LibreOffice가 없음입니다. 그래서 `pdf_render`는 되고 `docx_to_pdf`는 안 됩니다.

검사를 가능하게 하려고 패키지나 애플리케이션을 설치하지 않습니다. 빠진 능력은 해결 대상이 아니라 보고 대상입니다.

## 2. 증거 표면, 강한 순서

| 표면 | 증명하는 것 | 증명하지 않는 것 |
|---|---|---|
| 워드나 Pages가 파일을 열었다 | 복구 요청 없이 열리고 필드가 계산됨 | 이 기계에서는 아무것도. 사용자가 필요 |
| LibreOffice의 PDF 변환 | 별도의 독립 오피스 엔진이 패키지를 파싱함 | 워드의 배치 엔진은 아님 |
| HTML 렌더를 인쇄한 PDF | 내용, 쪽 상자, 여백, 표 폭, 들여쓰기, 페이지 나눔 | 워드의 줄 나눔과 글꼴 조형 |
| PDF에서 뽑은 쪽 이미지 | 스펙이 서술한 것을 독자가 봄 | 워드 충실도의 증명은 아님 |
| `verify` | 구조적 타당성: 파트, 타입, 관계, 스타일, 고정, 기하 | 모양에 대해서는 아무것도 |
| 텍스트 추출 | 낱말과 그 순서 | 배치에 대해서는 아무것도 |

`render --pdf`는 `@page` 크기가 문서 페이지 크기이고 여백이 패딩인 HTML을 쓰고, 헤드리스 브라우저로 인쇄합니다. 파일이 저장한 수치에 대한 충실한 증거입니다. 워드가 같은 곳에서 줄을 나눈다는 증거는 아닙니다. 워드의 줄 나눔과 글꼴 조형은 다릅니다.

## 3. `verify` 검사의 의미

| 검사 | 실패 조건 | 흔한 원인 |
|---|---|---|
| `xml-wellformed` | 파트를 파싱할 수 없음 | 손으로 고친 파트의 닫히지 않은 태그 |
| `document-part` | 본문 파트가 없음 | 관계 대상 오타 |
| `content-types` | override가 없는 파트를 가리키거나 미디어 파트에 기본 확장자가 없음 | `ensure_override` 없이 파트 추가 |
| `relationship-targets` | 내부 대상이 풀리지 않음 | 대상을 소유 파트가 아니라 패키지 루트 기준으로 씀 |
| `styles-resolve` | 문단이 정의되지 않은 스타일 id를 씀 | `pStyle`로 문단을 만들고 스타일을 선언하지 않음 |
| `images` | 관계가 없는 파트를 가리키거나, blip에 관계가 없거나, extent가 0이거나 페이지보다 넓거나, extent가 터무니없는 해상도를 함의함 | 파일이 옮겨진 뒤 경로를 읽음. extent를 EMU가 아닌 트윕으로 씀(1밀리미터 = 36000) |
| `comment-anchors` | 댓글에 구간이 없거나 구간에 댓글이 없음 | 시작·끝 쌍 없이 댓글을 씀 |
| `placeholders` | `TODO`, `TBD`, `FIXME`, `XXX`, 로렘 텍스트가 본문에 남음 | 초안 스펙을 최종본으로 전달 |
| `geometry` | 페이지 크기나 여백이 스펙과 2트윕 넘게 다름 | 빌드 뒤 스펙을 고침 |
| `length` | 본문 글자 수가 `min_chars`보다 적음 | 잘린 빌드나 빈 블록 목록 |

`skipped`는 `pass`가 아닙니다. 스펙을 넘기지 않으면 기하 검사가 `skipped`로 나오고, `skipped`를 초록으로 세는 보고는 틀린 보고입니다.

## 4. 독립 읽기

두 번째 리더가 자기 검사로 잡지 못하는 것을 잡습니다. 빠진 파트, 깨진 관계, 리더가 무시하는 스타일이 그렇습니다. 이 기계에서는 이렇게 합니다.

```bash
textutil -convert txt -stdout out.docx | head -40      # macOS. 항상 있음
python3 -c "import docx; d=docx.Document('out.docx'); print(len(d.paragraphs), len(d.tables))"   # python-docx가 있을 때
```

둘 다 스킬이 설치하지 않습니다. 둘 다 없으면 내장 `text` 명령이 리더이고, 보고에 그렇게 적습니다. 자기 읽기는 독립 읽기보다 약한 증거이므로 그렇게 표시합니다.

## 5. 리더가 파일이 깨졌다고 할 때

먼저 `verify`를 돌립니다. 실패한 검사가 파트를 지목하고, 거의 모든 경우에 진단은 거기서 끝납니다.

| 리더 증상 | 먼저 볼 검사 |
|---|---|
| "Word에서 읽을 수 없는 내용을 발견했습니다" | `content-types`, 그다음 `relationship-targets` |
| 이미지가 빨간 X로 보임 | `images` |
| 그림이 실오라기처럼 보임 | `images`. 트윕으로 쓴 extent는 그림을 17분의 1로 줄임 |
| 댓글이 사라짐 | `comment-anchors` |
| 글꼴이 다르게 보임 | 검증 실패가 아님. 런 속성의 `w:rFonts`를 읽음 |
| 미리보기에서 표 테두리가 없음 | 패키지 결함이 아님. 미리보기가 스타일 전용 테두리를 버림. `tblBorders`를 직접 지정 |
| 페이지 나눔 위치가 다름 | `geometry`, 그다음 `pageBreakBefore`를 가진 문단 |

워드는 테두리를 그리고 미리보기는 테두리 없이 그리는 경우는 미리보기의 한계이고 패키지 결함이 아닙니다. 고치기 전에 XML에 `tblBorders`가 있는지 확인합니다.

## 6. 격차 보고

무엇을 어떻게 증명했는지 말하고, 증명하지 못한 것을 한 줄씩 말합니다.

- "verify 통과, HTML 렌더 PDF로 여백·표 폭 확인. Word 실물 렌더는 이 기기에 LibreOffice가 없어 확인하지 못했습니다."
- "폰트 모양은 대체 폰트로 렌더되어 확인하지 못했고, 크기·굵기·줄간격만 확인했습니다."

격차를 분명히 말하는 편이 재현할 수 없는 주장보다 낫습니다.

## Sources

> Checked 2026-11-13

- python-docx 설치와 리더 동작 — https://python-docx.readthedocs.io/
- Microsoft Learn, Open XML 패키지와 콘텐츠 타입 규칙 — https://learn.microsoft.com/en-us/office/open-xml/word/
- Chromium 헤드리스 인쇄와 `--print-to-pdf` 동작 — https://developer.chrome.com/docs/chromium/headless
- ECMA-376, 패키지 관계와 파트 해석 — https://ecma-international.org/publications-and-standards/standards/ecma-376/
