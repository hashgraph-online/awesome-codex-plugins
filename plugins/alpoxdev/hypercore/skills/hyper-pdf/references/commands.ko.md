# 명령 레퍼런스

> 모든 명령은 표준 출력에 JSON 객체 하나만 냅니다. 사람이 읽을 문장은 출력하지 않으므로 호출자는 grep이 아니라 파싱을 합니다.

```
osascript -l JavaScript <skill>/assets/runtime/engine.js <command> [inputs] [flags]
```

## 목차

1. [종료 코드와 상태](#1-종료-코드와-상태)
2. [읽기](#2-읽기)
3. [구조](#3-구조)
4. [보안과 양식](#4-보안과-양식)
5. [생성](#5-생성)
6. [검사](#6-검사)
7. [모든 명령에 적용되는 불변식](#7-모든-명령에-적용되는-불변식)

## 1. 종료 코드와 상태

| 종료 | `status` | 의미 |
|---|---|---|
| 0 | `ok` | 작업이 끝났고 주의할 것이 없음 |
| 0 | `caveated` | 파일은 만들어졌지만 `issues` 배열에 실제 결함이 있음(구조 트리 없음, 글꼴 미임베딩, 양식 필드 `missing`) |
| 1 | `blocked` | 진행하지 못해 아무것도 만들지 않음: `NO_PDF_FRAMEWORK`, `NO_HTML_RENDERER`, `ENCRYPTED`, `BAD_PASSWORD` |
| 1 | `error` | 인자 오류나 런타임 실패: `ARGS`, `NO_INPUT`, `UNKNOWN_COMMAND`, `RUNTIME` |

종료 코드는 파일이 만들어졌는지만 답합니다. 엔진은 `osascript`에서 도는데 이 실행기는 0이나 1만 내고 `exit`가 없습니다. `ok`와 `caveated`, `blocked`와 `error`를 가르는 것은 `status` 필드입니다. 두 경우 모두 표준 출력에 JSON 객체 하나를 내고, 실패한 경우에는 표준 오류에도 씁니다.

`caveated`는 성공이 아닙니다. `issues` 항목이 남아 있는데 결과를 "완료"라고 보고하면 거짓 보고입니다.

## 2. 읽기

### `info <pdf>`

| 필드 | 내용 |
|---|---|
| `pages` | 쪽 수 |
| `encrypted` | 지금 잠겨 있거나 `/Encrypt`가 있음 |
| `metadata` | `title`, `author`, `subject`, `keywords`, `creator`, `producer`, 생성·수정 날짜 |
| `raw` | 전체 바이트 검사(§6) |
| `pageDetails[]` | 쪽별 `page`, 포인트 단위 `width`·`height`, `rotation`, `textChars`, `annotations` |

### `text <pdf> [--pages SPEC] [--runs]`

`--pages`는 `1-3,7,10-` 형식입니다(경계를 생략하면 첫 쪽 또는 마지막 쪽).

| 필드 | 내용 |
|---|---|
| `content[]` | 쪽별 `page`, `text`. `--runs`면 `lines[]`에 `{y, runs:[{text, x, width, font, size}]}`도 포함 |
| `characters` | 추출한 총 글자 수 |
| `scanned` | 글자를 하나도 추출하지 못하면 `true` |

### `tables <pdf> [--pages SPEC]`

| 필드 | 내용 |
|---|---|
| `tables[]` | 쪽별 `page`, `columns`, 셀 문자열의 `rows[][]` |
| `limitation` | 항상 있으며 경계를 어떻게 추론했는지 밝힘 |

행 경계는 베이스라인 정렬에서, 셀 경계는 가로 간격에서 옵니다. 셀이 여러 줄로 접힌 괘선 표나 간격이 고르지 않은 무괘선 표는 사람이 직접 읽어야 합니다. 격자를 정확한 것으로 내놓지 마세요.

### `images <pdf> --out-dir DIR`

쪽마다 PNG로 2배 렌더합니다. `images[]`에 `page`, `raster` 경로, `width`, `height`를 줍니다. 내장 이미지 객체는 자기 해상도를 유지하고 리샘플되지 않습니다.

### `render <pdf> --out-dir DIR [--scale N] [--pages SPEC]`

쪽마다 `page-<n>.png`를 `--scale`(기본 2)로 씁니다. 쪽이 어떻게 보이는지 증명하는 명령이고, 생성 후 항상 씁니다.

### `fonts`

`resolveFont`가 쓸 수 있는 설치 글꼴 파일을 나열합니다. 인자 없음.

## 3. 구조

### `merge --out OUT.pdf <a.pdf> <b.pdf> ...`

| 필드 | 내용 |
|---|---|
| `pages` | 출력의 총 쪽 수 |
| `sources[]` | 입력별 `path`, `pages`, `locked` |

풀지 못하는 암호 입력은 병합을 막습니다. 쪽을 조용히 빼지 않습니다.

### `split <pdf> --out-dir DIR (--pages SPEC | --every N)`

| 필드 | 내용 |
|---|---|
| `sourcePages` | 입력의 쪽 수 |
| `parts[]` | 출력별 `from`, `to`, `out` 경로, `pages` |

파일명은 `pages-<from>-<to>.pdf`입니다. `--every 5`는 다섯 쪽씩 나눕니다.

### `rotate <pdf> --out OUT.pdf [--angle 90] [--pages SPEC]`

`--angle`은 90의 배수여야 합니다(음수 허용). `pagesRotated`와 적용한 `angle`을 보고합니다. 회전은 쪽의 기존 회전에 누적됩니다.

### `watermark <pdf> --out OUT.pdf --text TEXT [--opacity 0.3] [--size 48] [--angle 45] [--pages SPEC] [--font PATH]`

쪽을 새 컨텍스트로 재생해 대각선 텍스트를 얹습니다. `pages`와 표시를 받은 쪽 수 `watermarked`를 보고합니다. 텍스트는 주석이 아니라 그려지므로 끌 수 없고 추출에도 나타납니다.

### `stamp <pdf> --out OUT.pdf --text TEXT [--page 1] [--x] [--y] [--width 240] [--height 60] [--size 24] [--opacity 0.5] [--font PATH]`

기본 빨간색 FreeText 주석을 넣습니다. `watermark`와 달리 주석으로 남으므로 쪽에 굽는 것은 `flatten`입니다.

### `metadata <pdf> [--set "key=value;key=value"] [--out OUT.pdf | --in-place]`

`--set`이 없으면 읽기만 합니다. 있으면 지정한 속성을 적용합니다. 키는 `title`, `author`, `subject`, `keywords`, `creator`입니다. `--out`이 있으면 그리로, `--in-place`일 때만 원본으로, 둘 다 없으면 아무 데도 쓰지 않습니다. `before`, `after`, `applied`를 보고합니다.

## 4. 보안과 양식

### `encrypt <pdf> --out OUT.pdf --user-password PW [--owner-password PW]`

결과를 다시 열어 `locked`를 보고합니다. note는 답의 일부입니다. PDFKit은 RC4 128비트 암호를 적용하고 AES-256과 권한 비트 집합을 제공하지 않습니다. AES나 동작별 권한이 필요한 요청은 이 명령으로 충족할 수 없고, 그 사실을 암시가 아니라 말로 밝혀야 합니다.

### `decrypt <pdf> --out OUT.pdf [--password PW]`

암호가 풀지 못하면 `blocked BAD_PASSWORD`. 추측하지 않습니다.

### `form <pdf>`

필드를 읽습니다. `fields[]`에 `page`, `name`, `type`, `value`, `rect`; `fillable` 불리언.

### `form <pdf> --fill "name=value;name=value" --out OUT.pdf`

| 필드 | 내용 |
|---|---|
| `applied[]` | 필드별 `field`, `value`, `widgets`(값을 받은 위젯 수) |
| `missing[]` | 맞는 위젯이 없는 필드 이름. 있으면 상태가 `caveated` |

값을 `;`와 `=`로 나누므로 그 문자가 든 값은 다른 경로가 필요합니다(스펙 기반 문서를 따로 만드세요).

### `flatten <pdf> --out OUT.pdf`

쪽을 재생하며 주석을 콘텐츠에 그립니다. `pages`와 `remainingFormFields`를 보고합니다. 대화형 위젯은 설계상 버립니다. 출력은 인쇄 전용이고, 채울 수 있어야 하는 양식은 flatten하지 않습니다.

## 5. 생성

### `build --spec SPEC.json --out OUT.pdf`

| 필드 | 내용 |
|---|---|
| `pages`, `blocks` | 만들어진 결과 |
| `language` | `/Lang` 증분 쓰기의 `{injected, language, catalog}` |
| `issues[]` | `FONT_NOT_EMBEDDED`, `TYPE3_GLYPHS`, `NO_LANGUAGE_TAG`, `NO_STRUCTURE_TREE`, `LANGUAGE_TAG_FAILED` |

### `html <input.html> --out OUT.pdf [--renderer PATH] [--untagged] [--timeout-ms 8000]`

| 필드 | 내용 |
|---|---|
| `renderer` | 쓴 실행 파일 경로 |
| `taggedRequested` | 태그를 요청했는지(`--untagged`면 끔) |
| `raw` | 출력의 바이트 검사 |
| `issues[]` | `build`와 같은 코드 집합 |

`--renderer`는 탐색 결과를 덮어씁니다. `blocked NO_HTML_RENDERER`는 찾아본 경로를 알려줍니다.

### `ocr <pdf> --out OUT.pdf [--langs ko-KR,en-US] [--pages SPEC] [--work-dir DIR]`

| 필드 | 내용 |
|---|---|
| `languages` | 쓴 인식 언어 |
| `textCharacters` | 출력에서 이제 추출되는 글자 수 |
| `pages_ocred` | 레이어를 받은 쪽 수 |
| `perPage[]` | `page`, `observations`(인식한 줄 수) |

인식 텍스트는 손대지 않은 쪽 이미지 위에 보이지 않는 렌더 모드로 그려집니다. 화면은 유지되고 선택은 동작합니다. 좌표는 Vision 정규화 상자에서 쪽마다 변환합니다.

## 6. 검사

### `check <pdf> [--scan-threshold 0.02]`

| 필드 | 내용 |
|---|---|
| `raw` | 바이트 검사 |
| `pageChecks[]` | 쪽별 `textChars`, `inkRatio`, `likelyScan` |
| `issues[]` | `{code, page?, detail}` |
| `verdict` | 빈 쪽이나 OCR 필요 쪽이 있으면 `attn`, 아니면 `ok` |

이슈 코드와 그 결과는 `rules/accessibility.md`에 있습니다. `raw`는 코드가 도출되는 값들을 담습니다.

`bytes`, `version`, `encrypted`, `objectStreams`, `crossReferenceStreams`, `fontFile2`, `fontFile3`, `type0`, `type3`, `structureTree`, `markInfo`, `language`, `images`, `acroForm`, `linearized`, `javascript`, `launch`, `embeddedFiles`, `attachments`

## 7. 모든 명령에 적용되는 불변식

| 불변식 | 결과 |
|---|---|
| 표준 출력에 JSON 객체 하나, 그 외 없음 | 호출을 감싸 파싱. 로그 줄을 파싱하지 않음 |
| 숫자는 모두 실제 숫자 | ObjC 브리지 값을 `int`/`num`으로 강제 변환. 숫자 자리에 문자열이 오면 호출자 가정의 버그 |
| 입력은 바뀌지 않음 | 쓰는 명령은 모두 `--out`을 받음. 원본을 건드리는 것은 `metadata --in-place`뿐 |
| 잠긴 입력은 막고 추측하지 않음 | `--password` 없으면 `ENCRYPTED`, 틀리면 `BAD_PASSWORD` |
| 경로는 절대 경로로 해석 | 상대 경로는 호출 시점 작업 디렉터리 기준 |

## Sources

> Checked 2026-11-13.

| Claim | Source |
|---|---|
| PDF 권한과 암호화 처리 | <https://opensource.adobe.com/dc-acrobat-sdk-docs/pdfstandards/PDF32000_2008.pdf> (§7.6) |
| FreeText 주석 동작 | <https://opensource.adobe.com/dc-acrobat-sdk-docs/pdfstandards/PDF32000_2008.pdf> (§12.5.6.6) |
| Vision 텍스트 인식 좌표 규약 | <https://developer.apple.com/documentation/vision/vnrecognizedtextobservation> |
| PDFKit 암호 옵션 | <https://developer.apple.com/documentation/pdfkit/pdfdocument> |

### Evidence grade

전부 `LOCAL`입니다. 이 파일의 명령·플래그·종료 코드·출력 필드는 구현에서 읽고 이 기기에서 실행해 확인했습니다. 의도만으로 적은 필드는 없습니다.