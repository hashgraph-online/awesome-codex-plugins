# rhwp 명령 지도

## 1. 이 지도가 있는 이유

아래 명령은 모두 rhwp v0.9.0 macOS aarch64 릴리스 바이너리로 실행해 확인했습니다. 플래그와 JSON 키, 종료 코드는 프로젝트 설명이 아니라 그 실행 결과에서 옮겼습니다. rhwp가 바뀌면 명령을 다시 돌려 이 파일보다 실행 결과를 믿으십시오. `rhwp capabilities`는 바이너리 자신의 기계 판독용 계약을 출력하므로 둘이 어긋나면 그쪽이 기준입니다.

실행하려는 명령의 절만 읽습니다.

## 2. 명령 목록

| 명령 | 하는 일 | 주의 |
|---|---|---|
| `info FILE` | 파일 크기, HWP 버전, 압축, 암호화, 배포용 여부 | 사람이 읽는 글자만 있고 JSON이 없습니다 |
| `explain FILE --json` | 형식, 쪽 수, 문단·각주 수, 표, 암호화 | "이게 뭔가"에 가장 빠른 답 |
| `digest FILE --json` | `excerpt`, `pageCount`, `format`, `outline` | 보고용이고 편집용이 아닙니다 |
| `export-text FILE --json` | `pages[].text` 아래에 쪽별 본문 | `--json`은 파일을 쓰지 않습니다. 빼면 `-o DIR`(기본 `output/`)에 쪽별 TXT를 씁니다 |
| `export-structure FILE --json` | 구역·문단 인덱스가 붙은 개요 트리 | 편집에 넘길 인덱스가 여기서 나옵니다 |
| `export-tables FILE --json` | `row`, `col`, `text`가 붙은 `tables[].cells[]` | 표 인덱스는 나타난 순서입니다 |
| `table-to-csv FILE -o OUT.csv --json` | 모든 표를 CSV로 펼침 | 표가 여럿이면 파일도 여럿입니다 |
| `fields FILE --json` | 이름 있는 서식 필드와 현재 값 | 올바른 필드 이름을 아는 유일한 출처 |
| `form-value FILE --section N --para N --ctrl N --json` | 양식 컨트롤 하나의 값 | 필드 이름이 아니라 구역·문단·컨트롤 좌표를 받습니다. 누름틀 값을 되읽으려면 `fields --json`을 씁니다 |
| `search FILE "text" --json` | `matchCount`와 일치 위치 | 인자 순서는 파일 다음 글자입니다 |
| `word-count FILE --json` | 글자·단어 합계 | 분량 제약을 확인할 때 씁니다 |
| `scaffold spec.json --format hwpx -o OUT` | JSON 명세로 문서를 만듦 | `--format hwpx`만 받습니다(5절) |
| `convert IN OUT.hwp --verify --json` | **항상 HWP5를 씁니다.** 출력 경로가 `.hwp`로 끝나야 하고 `.hwpx` 대상은 `export-hwpx`를 쓰라는 안내와 함께 거부됩니다 | 배포용 읽기 전용 표시를 벗기는 것이 이 명령의 목적입니다 |
| `export-hwpx IN OUT.hwpx --verify` | HWP·HWPX를 HWPX로 | HWP에서 HWPX로 가는 유일한 경로입니다. `--verify-pages`는 렌더 쪽 수를 비교하고 불일치에 종료 코드 4를 냅니다 |
| `edit <sub> IN -o OUT --json` | 모든 변경 | `-o`가 없으면 원본 옆에 `<이름>_<하위명령>.<확장자>`를 씁니다 |
| `run plan.json --json` | 한 파일에 적용할 편집 단계 목록 | 단계 스키마가 좁습니다. 5절 참조 |
| `csv-to-table FILE --csv IN.csv --table N -o OUT` | CSV로 표 내용을 바꿈 | CSV 모양이 표의 행·열 수와 같아야 합니다 |
| `import-pdf IN.pdf OUT.hwpx --json` | PDF를 HWPX로. `fidelity`(위치 고정 글상자, 기본)나 `editable`(문단 재배치) | v0.9.0 기능입니다. `pageCount`와 `execution` 묶음을 보고하고, 자원 한도가 입증되지 않았다는 점(`addressSpaceLimitEnforced: false`)을 적습니다 |
| `verify FILE --expect-*` | 산출물에 대한 조건 검사 | 종료 코드는 7절 |
| `hwpx-roundtrip FILE` | 파싱, 직렬화, 재파싱, 비교 | HWPX 충실도 게이트 |
| `hwp5-roundtrip FILE` | HWP5에 같은 검사 | HWP3이나 HWPX 입력에서는 실패합니다 |
| `layout-anomaly FILE --json` | 넘침, 화면 밖, 겹침, 빈 쪽 카운터 | 입력과 카운터를 비교합니다 |
| `threat-scan FILE --json` | 알려진 악성 패턴 검사 | 믿을 수 없는 파일은 편집 전에 돌립니다 |
| `armor FILE --json` | 문서 글자의 주입 신호 검사 | `clean`과 찾은 신호를 알립니다 |
| `inspect <axis> FILE --json` | `hidden-text`, `unicode`, `watermark`, `injection` | 호출마다 축 하나입니다 |
| `scan DIR --json` | 디렉터리 일괄 형식 검사 | 확장자와 매직 바이트가 다른 파일을 알립니다 |
| `batch --kind <kind> --json` | 경로 목록에 명령 하나를 반복 | 표준 입력이 경로 목록입니다 |
| `export-pdf`, `export-svg`, `export-png` | 화면 출력 | Skia 빌드와 웹폰트 캐시가 필요합니다 |
| `capabilities` | 바이너리의 명령 계약을 JSON으로 | 탐지 스크립트가 쓰는 버전 확인 |
| `mcp-serve` | 같은 표면을 노출하는 stdio MCP 서버 | MCP를 말하는 호스트용이고 셸 작업용이 아닙니다 |

## 3. 글자·문단 서식

`apply-char-format`과 `apply-para-format`은 `--props` JSON을 받습니다. `set-cell-props`와 달리 이 둘은 **모르는 키를 거부합니다**. 모르는 속성은 `--props 에서 적용할 글자 서식 키를 찾지 못했습니다 (키 이름 확인)`과 함께 종료 코드 2로 끝납니다. 그래서 키 집합은 시도로 알아낼 수 있고, 그 수가 적습니다.

| 키 | 타입 | 확인 |
|---|---|---|
| `bold`, `italic`, `underline` | 불리언 | 받아들여지고 종료 0, `hwpx-roundtrip` PASS |
| `fontSize` | 정수(HWPUNIT 계열 크기 값) | 받아들여짐 |
| `fontId` | 정수, 문서 글꼴 표의 인덱스 | 받아들여지고 **경계 검사가 없음**. 글꼴 세 개짜리 문서에 `{"fontId":999}`도 종료 0 |
| `baseSize`, `textColor`, `shadeColor`, `strikeout` | `rhwp export-ir-schema`의 `CharShape` 참조 | IR 스키마에 정의됨. `color`, `strike`라는 키 이름은 거부됨 |

지정은 `--section`, `--para`, `--offset`, `--count`로 하고 `--count`를 빼면 문단 끝까지입니다. `apply-para-format`은 `--section`·`--para`와 `{"alignment":"center"}` 같은 `--props`로 지정합니다.

**글꼴 표를 나열하는 명령은 없습니다.** `{"fontId":3}`은 글꼴 3번이 없어도 받아들여지므로, 찍은 인덱스는 독자가 대체 글꼴로 그려야 하는 문서를 조용히 만듭니다. 사용자가 특정 글꼴을 요구하면 이렇게 말합니다. CLI는 인덱스로 글꼴을 적용할 수 있지만 어느 인덱스가 함초롬돋움인지는 알려 주지 못합니다. 그래서 이름으로 본문 글꼴을 바꾸는 일은 이 스킬의 범위 밖이고, 시도하지 않고 한계로 보고합니다.

## 4. 실제로 읽게 되는 JSON 키

| 명령 | 키 |
|---|---|
| `explain` | `format`, `pageCount`, `paragraphCount`, `footnoteCount`, `endnoteCount`, `encrypted`, `tables[]`, `fields`, `summary` |
| `digest` | `excerpt`, `pageCount`, `paraCount`, `format`, `outline`, `nextStep`, `truncated` |
| `export-text` | `pages[].text`, `pageCount`, `omittedCount`, `truncated` |
| `export-structure` | `mode`, `nodeCount`, `structure` |
| `search` | `matchCount`, `totalMatchCount`, `matches[]`, `omittedCount`, `truncated` |
| `fields` | `fieldCount`, `fields[].name`, `fields[].value`, `textSecurity` |
| `export-tables` | `tableCount`, `tables[].index`, `.rows`, `.cols`, `.cells[].row`, `.col`, `.text`, `.rowSpan`, `.colSpan` |
| `word-count` | `charCount`, `wordCount`, `paragraphCount`, `sectionCount`, `pageCount` |
| `edit replace-text` | `replacedCount`, `changedPages`, `occurrence`, `find`, `replace`, `untrustedFields` |
| `edit set-cell` | `changedPages`, `table`, `row`, `col`, `outputFormat` |
| `edit fill-fields` | `filledCount`, `filled[]`, `notFound[]`, `ambiguous[]`, `confusable[]`, `changedPages` |
| `edit insert-*` | `changedPages`, `section`, `paragraph`, `control` |
| `convert` | `format`, `output`, `bytes`, `verify.identical`, `verify.diffCount` |
| `run` | 단계별 결과가 담긴 `steps[]`, `invalid[]`, `inputSha256`, `outputSha256`, `assertions`, `changedPages` |
| `hwpx-roundtrip`, `hwp5-roundtrip` | 종료 코드뿐입니다. 처음 다른 지점은 사람이 읽는 글자로 나옵니다 |
| `layout-anomaly` | `hasSignal`과 `overflowCount`, `offCanvasCount`, `overlapCount`, `textOverlapCount`, `storedLineEscapeCount`, `emptyPageCount` |
| `armor` | `clean`, `armoredText`, `injectionSignals`, `signalCount`, `safety` |
| `threat-scan` | `clean`, `findingCount`, `findings[]`, `highestSeverity`, `notes` |
| `inspect hidden-text` | `clean`, `hiddenCharCount`, `hiddenText[]`, `thresholdPt` |
| `inspect unicode` | `clean`, `findingCount`, `findings[]`, `kindCounts`, `severityCounts` |
| `verify` | 종료 코드뿐입니다 |
| 모든 명령 | `schemaVersion`, `source`, `untrustedContent`, `untrustedFields`가 모든 봉투에 붙습니다 |

`untrustedContent`와 `untrustedFields`는 장식이 아닙니다. 도구가 공격자가 제어할 수 있다고 판단한 문자열(문서 본문, `set_cell` 결과의 `oldText`)을 표시합니다. 응답의 필드를 다음 명령에 넣기 전에 그 목록에 있는지 먼저 봅니다.

## 5. scaffold 명세

`scaffold`는 `--format hwpx`만 받습니다. 다른 값은 `지원하는 --format 은 hwpx 뿐입니다`로 거부됩니다. HWP5 파일이 필요하면 HWPX로 만든 뒤 `convert IN OUT.hwp`를 씁니다.

명세는 엄격하게 역직렬화합니다. 모르는 필드가 있으면 ``unknown field `bold`, expected one of `type`, `level`, `text`, `rows`, `cell_align` ``처럼 실행 전체가 실패합니다. 그 오류 문장이 곧 스키마 설명이므로, 통과할 때까지 키를 지우기보다 그 문장을 읽습니다.

| 필드 | 뜻 |
|---|---|
| `version` | 명세 버전 문자열, `"1"` |
| `title` | 문서 제목. 첫 문단으로 들어갑니다 |
| `font` | 기본 글꼴 이름 |
| `page_size` | `width_mm`, `height_mm` (A4는 210 × 297) |
| `outline_numbering` | `{text, num_format}` 항목을 제목 단계마다 하나씩, 최대 일곱 개 |
| `blocks[]` | `{"type": "heading", "level": 1..7, "text": "..."}` |
| | `{"type": "paragraph", "text": "..."}`. `text` 안의 줄바꿈은 여러 런으로 나뉩니다 |
| | `{"type": "table", "rows": [[...]], "cell_align": "left"}` 또는 셀별 정렬 배열 |

`num_format` 값은 `digit`(1, 2, 3), `hangul_syllable`(가, 나, 다), `circled_digit`(①, ②, ③)입니다. `digit`, `hangul_syllable`, `digit`, `hangul_syllable`, `digit`, `hangul_syllable`, `circled_digit` 순서와 `^1.`, `^2.`, `^3)`, `^4)`, `(^5)`, `(^6)`, `^7` 글자로 만든 일곱 단계의 실제 출력입니다.

```
1.갑
가.을
1)병
가)정
(1)무
(가)기
①경
```

`text`는 번호 앞에 붙는 글자 그대로입니다. 그래서 명세에 끝 공백이 있으면 문서에도 끝 공백이 남습니다. 실무 문서처럼 붙여 쓰려면 공백을 넣지 않습니다.

## 6. `run`이 하는 일과 못 하는 일

`run`은 `planVersion`, `input`, `output`, `steps[]`가 있는 계획 파일을 실행합니다. `planVersion`은 문자열 `"1.0"`이어야 합니다. `"1"`은 `planVersion "1.0" 이 필요합니다`와 함께 종료 코드 2로 끝납니다. 각 단계의 `action`은 `rhwp export-plan-schema`가 공개하는 여덟 값의 태그드 유니온입니다.

| `action` | 단계에 필요한 필드 |
|---|---|
| `replace_text` | `find`, `replace`, 선택 `occurrence`, `caseSensitive` |
| `set_cell` | `table`, `row`, `col`, `text`, 선택 `keepStyle` |
| `fill_fields` | 필드 이름과 값의 대응 |
| `set_checkbox` | 체크박스 대상 |
| `fill_template`, `repeat_and_fill_paragraph_block`, `repeat_and_fill_table_rows`, `import_paragraph_block` | 단독 단계 템플릿. 다른 단계와 섞을 수 없습니다 |

모든 단계는 `if` 조건을 함께 받습니다. 모르는 `action`은 최상위 스키마 오류가 아니라 응답의 `invalid[]` 배열에 `알 수 없는 action` 사유로 담기고, 출력 파일을 쓰지 않은 채 종료 코드 2로 끝납니다. 종료 코드만 보지 말고 `invalid[]`를 읽습니다.

성공한 실행은 단계별 결과와 `inputSha256`, `outputSha256`을 보고하므로, 어떤 입력에서 어떤 파일이 나왔는지 증명할 수 있습니다.

단계가 실패하면 개별 `edit` 호출로 돌아가는 편이 낫습니다. `edit`은 실패한 하위 명령과 그 옵션을 알려 주지만 계획 스키마는 그러지 못합니다.

## 7. 종료 코드

바이너리가 자기 표를 공개합니다. `rhwp capabilities --json | jq .exitCodes`가 이 표를 그대로 출력합니다.

| 코드 | 뜻 |
|---|---|
| 0 | 성공 |
| 1 | 실행 실패. 읽기, 파싱, 렌더, 쓰기 |
| 2 | 사용법 오류. 인자 없음, 모르는 옵션·명령, 쪽 범위 초과 |
| 3 | 검증 단언 실패. `convert`·`export-hwpx --verify`의 IR 차이, `edit ... --verify` 세 가지의 저장본 불일치, `run` 계획 단언 미충족, `render-diff --json` 시각 회귀, `layout-anomaly --strict` 확정 신호 |
| 4 | `--verify-pages` 쪽 수 불일치 |

실무에 두 가지가 따라옵니다. 단언 실패는 1이 아니라 3이므로 0이 아닌지만 보는 스크립트는 안전하지만 "1은 파싱 오류"로 기록하는 스크립트는 틀립니다. 기대 조건 없이 `rhwp verify FILE`만 주면 종료 코드 2입니다. 암호가 걸린 입력에 `--password`를 주지 않으면 암호화를 지목하는 파싱 오류와 함께 0이 아닌 코드로 끝납니다.

## 8. 형식별로 되는 일

| 입력 | 읽기 | 편집 | 되쓸 때 형식 |
|---|---|---|---|
| HWPX | 됨 | 됨 | HWPX(원래 형식) |
| HWP 5.x | 됨 | 됨 | HWP5(원래 형식) |
| HWP 3.x | 됨 | 됨 | **HWP5**. 3.x 기록기가 없어 결과가 형식 승격이 됩니다 |
| HML | 비어 있지 않고 올바를 때 됨 | 제한적 | 원본이 HML일 때만 HML. 아니면 `HML_SOURCE_REQUIRED` |
| `edit replace-text pw.hwpx --password 123456 -o out.hwpx` | 종료 0, `replacedCount: 42`; `info out.hwpx`가 `암호화: 아니오` | 암호 문서 편집은 암호 해제이므로 `edit-safety.ko.md` 2절에 적고 6절에서 동의 없이는 거절 |
| `convert pw.hwpx out.hwp --password 123456` | 종료 0, `passwordProtected: false`, `wasDistribution: false` | 변환도 암호를 벗깁니다. JSON의 이 불리언이 보고에 쓰기 가장 빠릅니다 |
| 암호 걸린 HWPX | `--password`가 있을 때만 | 같음 | 같은 형식 |
| PDF | `import-pdf`로 HWPX나 HWP로 | 가져오기는 재구성이고 편집이 아닙니다 | 기본 HWPX |
| DOCX, XLSX, PPTX, ODT | 안 됨 | 안 됨 | - |

화면 출력(`export-pdf`, `export-svg`, `export-png`)은 빌드에 `--features native-skia`가 있어야 하고 처음 쓸 때 `~/.cache/rhwp/webfonts`에 한글 웹폰트를 내려받습니다. 네트워크와 그 캐시가 없으면 렌더링은 실패하지만 글자·표·편집 명령은 계속 동작합니다.

## 9. 표 손질

구조를 바꾸는 편집 명령은 있고 동작합니다. 다만 사용자의 의도를 검사해 주지는 않습니다.

| 필요한 일 | 명령 | 주의 |
|---|---|---|
| 칸 글자 바꾸기 | `edit set-cell --table N --row R --col C` | 글자만 바꿉니다. 좌표는 `export-tables`에서 |
| 열 폭 바꾸기 | `edit set-column-widths --table N --widths "12000,24000"` | HWPUNIT이고 개수가 열 수와 같아야 합니다. 다르면 `열 폭 개수 … 와 다릅니다`로 실패합니다 |
| 사각형 병합 | `edit merge-cells --table N --row R --col C --end-row R2 --end-col C2` | 양 끝 좌표를 포함합니다 |
| 병합 칸 나누기 | `edit split-cell --table N --row R --col C` | |
| 행·열 넣고 지우기 | `edit insert-row`, `insert-col`, `delete-row`, `delete-col` | 행 삽입은 `--below`, 열 삽입은 `--right` |
| 칸 크기 조절 | `edit resize-table --row R --col C [--vertical]` | 칸 하나의 높이나 너비를 바꾸고 이웃으로 전파할 수 있습니다 |
| 표·칸 속성 | `edit set-table-props --props '<json>'`, `set-cell-props --table N --row R --col C --props '<json>'` | **속성은 스키마 검사가 없습니다**. 모르는 키도 받아들이고 성공으로 보고하며, 어떤 카운터로도 알 수 없는 차이가 있는 파일을 씁니다 |
| 표 전체 재배치 | `edit fit-table`, `move-table`, `merge-table` | |

작업 방식에 두 가지가 따라옵니다.

- 구조를 바꾼 뒤에는 표 인덱스와 칸 좌표가 밀릴 수 있습니다. 다음 좌표 편집 전에 `export-tables`를 다시 읽습니다(`rules/edit-safety.md` 3절).
- `set-cell-props`가 엉터리 키도 조용히 받으므로, 속성 변경은 명령의 종료 코드가 아니라 원한 결과(폭을 다시 읽기, 쪽을 다시 그리기)로 확인합니다.

## 10. CLI가 하지 않는 일

- `insert-table`은 `--rows`, `--cols`, `--section`, `--para`, `--offset`을 받고 칸 글자는 받지 않습니다. 넣은 뒤 `set-cell`로 채웁니다.
- `csv-to-table`은 모양이 같은 기존 표가 필요합니다. 행을 덧붙이지 않습니다.
- HML 저장은 원본이 HML일 때만 됩니다.
- `set-cell-props`와 `set-table-props`는 타입 없는 JSON 묶음을 받고, 모르는 키를 거부하지 않습니다.
- 한글 프로그램 자체의 조판을 파서에 물어볼 방법은 없습니다. `export-pdf`는 rhwp 엔진으로 그리므로 한글과 줄바꿈이 다를 수 있습니다.

## 11. 실행 확인

이 파일의 명령에 대한 주장은 프로젝트 설명을 읽은 것이 아니라 실행에서 나왔습니다. 2026-11-13과 2026-11-14에 릴리스 바이너리로 두 차례 돌렸습니다.

표 손질(9절)은 두 열 두 행짜리 scaffold HWPX로 실행했고, 각 산출물이 `hwpx-roundtrip`을 통과했습니다(종료 코드 0).

| 실행 | 결과 |
|---|---|
| `edit set-column-widths --table 0 --widths "12000,24000"` | 종료 0, `widths: [12000, 24000]` |
| `edit set-column-widths --table 0 --widths "12000"` (두 열 표에 하나) | 종료 1, `열 폭 개수 1 가 표의 열 수 2 와 다릅니다` |
| `edit merge-cells --table 0 --row 0 --col 0 --end-row 0 --end-col 1` | 종료 0, `endRow: 0, endCol: 1` |
| `edit insert-row --table 0 --row 1 --below` | 종료 0, `below: true` |
| `edit set-cell-props --row 1 --col 1 --props '{"bogus":1}'` | 종료 0, 파일을 씀. 올바른 속성을 준 같은 호출과 바이트가 같음 |
| `edit set-cell-props --row 9 --col 9` (2×2 표) | 종료 2, `좌표가 격자를 벗어났습니다` |

이 파일의 서술을 바꾸게 만든 실행:

| 실행 | 결과 | 바뀐 서술 |
|---|---|---|
| `hwpx-roundtrip legacy.hwp` (HWP3 파일) | `[FORMAT_SKIP]`, **종료 0** | 2절과 `verification.md`가 상태 단어를 읽으라고 말합니다. 건너뜀은 조용한 거짓 통과입니다 |
| `hwp5-roundtrip plan.hwpx` (HWPX 파일) | `[FORMAT_SKIP]`, 종료 0 | 같음 |
| `convert a.hwpx out.hwpx` | 종료 1, `convert 출력 경로는 .hwp 확장자여야 합니다` | `convert`는 HWP5 전용이고 HWP→HWPX는 `export-hwpx`입니다 |
| `run`에 `planVersion: "1"` | 종료 2, `planVersion "1.0" 이 필요합니다` | 6절이 버전 문자열을 고정합니다 |
| `run`에 `action: "insert_text"` | 종료 2, `invalid[]`가 `알 수 없는 action`을 지목 | 6절이 실제 여덟 action을 적고 `invalid[]`를 읽으라고 합니다 |
| 서식 표본에 `edit fill-fields --data '{"myMsg01":"홍길동"}'` | 종료 0, `filledCount: 1`, `myMsg01=홍길동`으로 재읽기 | `fill-fields`는 `--set`이 아니라 `--data`를 받습니다 |
| `form-value --name myMsg01` | 종료 2, 모르는 옵션 | 양식 값은 `--section/--para/--ctrl`을 받고, 필드 값은 `fields --json`으로 읽습니다 |
| `edit replace-text --find 추진 --occurrence 0` | `replacedCount: 1`, 종료 0. `--occurrence 1`은 0이고 파일도 쓰지 않음 | `--occurrence`는 0부터 셉니다 |
| `import-pdf out2.pdf imp.hwpx` | 종료 0, `pageCount: 1`, `execution.filesystemNetworkSandbox: false` | PDF 가져오기는 되지만 격리 수준이 플래그 이름이 시사하는 것과 다릅니다. 그대로 보고합니다 |
| `export-hml a.hwpx -o x.hml` | 종료 1, `HML_SOURCE_REQUIRED` | HML 출력은 원본 형식에 묶입니다 |

## Sources

> 확인 2026-11-13. rhwp v0.9.0 macOS aarch64 릴리스 바이너리 기준입니다(`~/.cargo/bin/rhwp`는 `edit`, `scaffold`, `convert`가 없는 0.7.15 빌드여서 릴리스 압축 파일을 썼습니다).

- rhwp 저장소와 릴리스 자산: <https://github.com/edwardkim/rhwp>
- scaffold 스키마: 그 저장소의 `src/scaffold/schema.rs`. 바이너리가 강제하는 계획 스키마는 `rhwp export-plan-schema`가 출력합니다
- 프로젝트 에이전트 안내서: `mydocs/manual/rhwp_cli_skill_guide.md`, `mydocs/manual/agent_toolkit_cli.md`
- crates.io 메타데이터(0.9.0은 2026-11-08 공개): <https://crates.io/crates/rhwp>
