# 렌더링과 검증

첫 렌더링 전과 전달 전에 이 규칙 파일을 사용합니다. 렌더 명령, 보고, 수정 반복, 마무리 보고를 담습니다.

## 1. Command

```bash
bash <skill-dir>/scripts/render-diagram.sh --spec <out-dir>/<slug>.diagram.json --out-dir <out-dir> \
  [--formats html,jpg[,pdf]] [--theme light|dark] [--scale 1-4] [--name <slug>] [--budget-ms <ms>]
```

- `<skill-dir>`는 이 스킬 폴더이며, 절대 경로나 작업 디렉터리 기준 경로로 씁니다.
- 기본값: `--formats html,jpg`, `--scale 2`, 테마는 spec을 따릅니다(없으면 `light`), 굽기 단계의 `--budget-ms`는 `30000`입니다.
- `--browser <path>`나 `HYPER_DIAGRAM_BROWSER`로 브라우저를 고르고, `--list-browsers`로 찾은 목록을 봅니다.
- 그래프 타입(`architecture`, `flowchart`, `dataflow`, `state`, `class`, `erd`)은 elkjs가 필요합니다. 스크립트가 한 번 내려받아 SHA-256을 확인하고, 오프라인 기기에서는 `HYPER_DIAGRAM_ELK`로 이미 확인한 사본을 가리킵니다.

## 2. Exit Codes And Report

| 종료 코드 | 뜻 | 다음 단계 |
|---|---|---|
| 0 | `status: pass`, 산출물 생성 | JPG 확인(§4) |
| 1 | `status: fail`, 파일은 확인용일 뿐 | 수정(§3) |
| 2 | 사용법·spec 오류(`SPEC_INVALID`, `BAD_FORMAT`, `SPEC_MISSING`, `BAD_SCALE`, `BAD_THEME`, `BAD_BUDGET`, `BAD_NAME` 등) | 명령이나 JSON 수정 |
| 3 | 막힘(`BROWSER_MISSING`, `ELK_UNAVAILABLE`, `BAKE_FAILED`, `RUNTIME_NO_RESULT`, `CANVAS_EMPTY`) | 막힌 이유와 해결 방법 보고, spec 보존 |

표준 출력의 보고에는 `status`, `type`, `canvas`, `counts`, `outputs`, `pdfPages`, `errors`, `warnings`가 들어 있습니다.

## 3. Repair

| 코드 | 뜻 | 보통 고치는 법 |
|---|---|---|
| `TITLE_MISSING`, `DESCRIPTION_MISSING` | 필수 글 없음 | 씁니다 |
| `BAD_ID`, `DUPLICATE_ID`, `UNKNOWN_ENDPOINT`, `UNKNOWN_GROUP`, `UNKNOWN_PARENT` | 참조 오류 | id를 고칩니다 |
| `TYPE_UNKNOWN`, `NO_NODES`, `BAD_DATE`, `TASK_LENGTH`, `NOTE_TARGET` | spec 모양 오류 | `references/spec-format.md`를 따릅니다 |
| `TEXT_OVERFLOW`, `NODE_OVERLAP`, `LABEL_OVERLAP`, `LABEL_OVERLAPS_NODE` | 너무 빽빽함 | 글을 줄이거나 `sub`로 옮기거나 `spacing`을 키웁니다 |
| `NODE_CROSSES_GROUP`, `GROUP_OVERLAP` | 그룹 소속 오류 | 노드에 `group`, 그룹에 `parent`를 지정합니다 |
| `EDGE_CROSSES_NODE` | 경로가 상자를 지남 | 노드 순서, `direction`, 그룹을 바꿉니다 |
| `PDF_MULTIPAGE`, `JPG_FAILED`, `PDF_FAILED`, `SCRIPT_LEFT` | 내보내기 오류 | 다시 실행하고, 반복되면 보고합니다 |
| 경고 `EDGE_CROSSINGS` | 간선이 교차함 | spec의 노드 순서를 바꿉니다. ELK는 입력 순서를 지킵니다 |
| 경고 `SMALL_TEXT` | 글자가 9.5px보다 작게 렌더됨 | 라벨을 줄이거나 `spacing`을 키우거나 다이어그램을 나눕니다 |
| 경고 `DENSE_DIAGRAM`, `WIDE_DIAGRAM` | 너무 큼 | 나누거나(`rules/diagram-selection.md` §2) `direction`을 정합니다 |

- 첫 렌더링 뒤 수정은 최대 3회입니다. 오류를 늘린 수정은 되돌립니다.
- 모양보다 의미를 먼저 지킵니다. 검사를 통과하려고 요소나 관계를 말없이 빼지 않습니다.

## 4. Visual Check

검사는 의미를 보지 못합니다. JPG를 열어 다음을 확인합니다.

- 주 경로가 지그재그 없이 한 방향으로 읽힙니다.
- 라벨이 엉뚱한 간선에 붙거나 간선에서 멀리 떨어져 있지 않습니다.
- 그룹이 자료가 말하는 구분과 같습니다.
- 중요한 요소가 너무 작거나 잘리지 않았습니다.

## 5. Closing Report

한국어로 보고합니다: 산출물 경로(spec, HTML, JPG, PDF), 타입과 고른 이유, 두 줄 구조 요약, 추정으로 표시한 요소, 남은 경고, 실행한 검증(종료 코드, 쪽수, 시각 확인).

## Sources

> 확인 2026-11-08.

| Claim | Source |
|---|---|
| headless Chromium `--dump-dom`, `--screenshot`, `--print-to-pdf`와 1쪽 조건 | `.hyper/research/21.diagram-skill.md` 실행 확인, 2026-11-08 |
| 요청하면 ELK 계층 배치가 입력 순서를 지킴 | <https://eclipse.dev/elk/reference/algorithms/org-eclipse-elk-layered.html> |
| 코드 목록, 종료 코드, 수정 3회 한도 | 이 패키지의 `scripts/render-diagram.sh`, `assets/runtime/run.js` |

### 근거 등급

`LOCAL` - 코드와 수정 표는 이 패키지의 런타임을 설명합니다.
