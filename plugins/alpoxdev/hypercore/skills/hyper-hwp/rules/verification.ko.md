# 검증

## 1. 무엇이 증거인가

문서에 대한 주장은 출력을 그대로 인용할 수 있는 명령으로 증명합니다. 값싼 것부터 네 가지 층이 있습니다.

| 층 | 주장 | 명령 |
|---|---|---|
| 확인 | 이 파일은 HWPX이고 4쪽이며 암호가 걸리지 않았다 | `rhwp explain FILE --json` |
| 변경 | 편집이 손댄 쪽을 보고했다 | 편집 자체의 JSON: `changedPages`, `replacedCount`, `filledCount` |
| 파싱 | 산출물이 같은 중간 표현으로 다시 읽힌다 | `rhwp hwpx-roundtrip OUT` 또는 `rhwp hwp5-roundtrip OUT`(종료 코드만 보지 말고 `PASS`를 확인), 또는 `--verify`를 붙인 변환 |
| 정확 | 바뀐 내용이 사용자가 요청한 바로 그것이다 | `rhwp export-text OUT --json`으로 읽어 확인. `rhwp verify OUT --expect-contains "..."` |

2층만 하고 4층을 건너뛰는 것이 흔한 실패입니다. `replacedCount`가 1이라는 사실은 무언가 일치했다는 뜻이지 맞는 것이 일치했다는 뜻이 아닙니다. 3층만 하고 4층을 건너뛰면 파일이 온전하다는 것만 증명되고 내용이 맞다는 것은 증명되지 않습니다.

## 2. 보고 형식

단계가 둘 이상이거나 산출물이 둘 이상인 작업이면 `.hyper/hwp/[슬러그]/report.md`를 씁니다. 짧게 유지합니다.

```markdown
# [작업 이름]

## 입력
- 경로, 형식, 쪽 수, 암호·배포용 여부 (`explain` 출력에서)

## 실행
| 순서 | 명령 | 핵심 결과 |
|---|---|---|
| 1 | `rhwp edit replace-text ...` | replacedCount=2, changedPages=[0] |
| 2 | `rhwp export-text ...` | 새 문자열 확인 |

## 검증
- 왕복: `hwpx-roundtrip` 종료 0
- 조판: 발견 0건 (입력 0건)
- 재확인: `verify --expect-contains` 종료 0

## 산출물
- 절대 경로, 형식, 쪽 수, 바이트

## 하지 못한 것
- 요청 중 도구가 만족하지 못한 부분과 그 이유

Result: done - [한 줄 요약]
```

단계가 하나인 작업에는 보고 파일이 필요 없습니다. 같은 사실을 대화 답변에 적고 그 답변 끝에 `Result:` 줄을 붙입니다.

## 3. 검증 사다리

그 변경이 실제로 위협하는 검사만 아래 순서로 돌리고, 실패하면 거기서 멈춰 원인을 봅니다.

1. **재읽기.** 본문을 내보내 새 문자열이 있고 옛 문자열이 없는지 확인합니다. 잘못된 일치, 잘못된 표 인덱스, 아무것도 바꾸지 않은 편집이 여기서 걸립니다.
2. **구조 게이트.** HWPX는 `hwpx-roundtrip`, HWP5는 `hwp5-roundtrip`입니다. 둘 다 파싱, 직렬화, 재파싱을 하므로 차이가 나오면 재읽기로는 보이지 않는 손상이 있다는 뜻입니다.

   **종료 코드만 보지 말고 상태 단어를 읽습니다.** 게이트는 `[PASS]`, `[FAIL]`, `[FORMAT_SKIP]`을 출력하고 `FORMAT_SKIP`은 종료 코드 **0**입니다. HWP5 파일을 `hwpx-roundtrip`에 주거나 HWPX 파일을 `hwp5-roundtrip`에 주거나 HWP3 파일을 둘 중 하나에 주면 아무것도 검사하지 않고 통과한 것처럼 보입니다. 출력 줄이 실제 형식을 알려 줍니다: `확장자 위장: 실체 HWP3 — HWPX 게이트 범위 밖`. 여기서 `$?`를 믿는 스크립트는 거짓 통과를 기록합니다. `[PASS]`를 grep합니다.
3. **조판 게이트.** `layout-anomaly OUT --json`을 돌려 `overflowCount`, `offCanvasCount`, `overlapCount`, `textOverlapCount`, `storedLineEscapeCount`, `emptyPageCount`와 `hasSignal`을 입력과 비교합니다. 편집 뒤에 늘어난 수는 왕복 검사가 잡지 못하는 퇴행입니다. `--strict`는 확정 신호에 종료 코드 3을 냅니다.
4. **조건 게이트.** 사용자가 말한 사실(쪽 수, 있어야 할 글자)에 `rhwp verify OUT --expect-pages N --expect-contains "문자열" --expect-min-chars N --expect-format hwpx`를 씁니다.
5. **왕복 검사는 파일을 씁니다.** 두 왕복 명령은 `-o`로 폴더를 지정하지 않으면 작업 디렉터리 기준 `output/poc/task1315/`(HWPX)나 `output/poc/task1552/`(HWP5)에 재조립 문서와 `inventory.tsv`를 씁니다. 사용자의 문서 폴더 안에 산출물이 떨어지지 않도록 `-o`를 임시 폴더로 지정합니다.

6. **화면 게이트, 요청받았을 때만.** `export-pdf`나 `export-png`로 그린 뒤 쪽을 봅니다. 줄바꿈이 옮겨간 것을 볼 수 있는 유일한 방법입니다. Skia 빌드와 웹폰트 캐시가 필요하고, 없으면 조판이 괜찮다고 주장하지 말고 그 사실을 말합니다.

## 4. 종결 상태

| 상태 | 언제 |
|---|---|
| `done` | 산출물이 있고, 그 변경이 위협하는 검사가 통과했고, 답변이 무엇이 바뀌었는지 말함 |
| `prerequisite_missing` | 탐지 스크립트가 `rhwp_not_found`나 `version_too_old`를 냄. 설치·업그레이드 경로를 알리고 멈춤 |
| `awaiting_input` | 대상 글자, 필드 이름, 출력 경로가 주어지지 않았고 파일에서 추론할 수도 없음 |
| `blocked` | 두 번 고쳐 본 뒤에도 검사가 실패했거나 파일을 전혀 파싱할 수 없음 |

`blocked` 보고에는 실패한 명령, 그 종료 코드, 오류 첫 줄을 담습니다. 마지막 검사가 실패한 실행에 `done`을 붙이지 않습니다.

## 5. 주장하면 안 되는 것

- 문서가 한글 프로그램에서 제대로 열린다는 것. 여기에 설치돼 있지 않고 이를 증명하는 명령도 없습니다.
- 변환한 HWP3 파일이 여전히 HWP3이라는 것.
- 조판이 한글 자체의 쪽 나눔과 같다는 것. rhwp는 자체 엔진으로 그리므로 줄바꿈이 다를 수 있습니다.
- 왕복이 통과했으니 편집이 안전하다는 것. 왕복은 형식을 증명할 뿐 의도를 증명하지 않습니다.
- 출력이 `[FORMAT_SKIP]`인데 왕복이 통과했다는 것. 그 단어는 그 게이트에 맞지 않는 형식이었고 아무것도 검증되지 않았다는 뜻입니다.
- `export-tables`가 문서에 보이는 것보다 적은 표를 돌려줬는데 표 추출이 완전하다는 것. 중첩 표와 글상자 안의 표가 흔한 누락이고, 누락은 누락으로 보고합니다.

## Sources

> 확인 2026-11-13. 이 기기에서 rhwp v0.9.0으로 scaffold·변환·편집한 문서에 각 게이트를 돌려 확인했습니다.

- 관찰한 종료 코드와 플래그: `verify`는 통과 0, 불일치 3, 읽기 실패 1, 사용법 오류 2를 냅니다. `hwpx-roundtrip`과 `hwp5-roundtrip`은 0 또는 0이 아닌 코드와 첫 차이 이름을 냅니다. `layout-anomaly --strict`는 발견이 있으면 0이 아닌 코드를 냅니다
- `layout-anomaly` JSON에는 `hasSignal`과 여섯 개 카운터가 있습니다. scaffold로 만든 한 쪽 문서는 `hasSignal: false`에 모든 카운터가 0이었고 `--strict`도 종료 코드 0이었습니다
- `convert --verify`는 `verify.identical`과 `verify.diffCount`를 보고합니다. scaffold로 만든 표 문서의 HWPX→HWP5 변환은 `identical: true`를 냈습니다
- rhwp 저장소: <https://github.com/edwardkim/rhwp>
