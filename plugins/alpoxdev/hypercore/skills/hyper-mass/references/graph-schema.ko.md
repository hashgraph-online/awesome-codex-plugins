# 그래프 스키마

실행 정의와 journal을 쓰는 동안 이 참조를 읽습니다. `graph.json`은 계약이고, `run.jsonl`은 그 계약에 실제로 무슨 일이 있었는지의 기록입니다. 둘 다 `.hyper/mass/<run-key>/` 아래에 있습니다.

## 목차

- 실행 디렉터리
- `graph.json`
- Node 객체
- Justification 객체
- Node prompt
- Self-check
- `run.jsonl`
- Resume 표
- 예제
- Key와 경로 규칙

## 실행 디렉터리

```text
.hyper/mass/<run-key>/
├── graph.json              # 정의, 시작 전에 작성
├── run.jsonl               # append-only 이벤트 journal
└── nodes/
    ├── <node-id>.md        # 노드마다 handoff 하나
    └── ...
```

리더가 `graph.json`과 `run.jsonl`을 씁니다. 노드는 자기 handoff만, 그것도 `nodes/` 안에만 씁니다. 임시 공간이 필요한 노드는 임시 디렉터리를 쓰고 끝내기 전에 지웁니다.

## `graph.json`

| 필드 | 타입 | 필수 | 의미 |
|---|---|---|---|
| `key` | string | 예 | 실행 정체성. 소문자 kebab-case, 최대 48자. 같은 key와 같은 정의는 resume입니다. |
| `name` | string | 예 | 보고에 쓰는 사람용 이름. |
| `goal` | string | 예 | 이 실행이 만드는 산출물을 지목하는 한 문장. |
| `success_criteria` | 문자열 배열 | 예 | 각 기준이 근거를 지목합니다. 명령과 기대 결과, 또는 파일과 필요한 내용입니다. |
| `justification` | 객체 | 예 | `rules/graph-planning.ko.md` §4의 여섯 필드 기록. |
| `nodes` | 객체 배열 | 예 | 노드 객체 1-32개. |
| `phase` | string | 아니요 | 바깥 루프가 목표를 소유할 때 이 실행이 담당하는 체크포인트. |
| `caps` | 객체 | 아니요 | 노드, 동시성, retry, amend에 대한 사용자 지정 덮어쓰기. |

알 수 없는 필드는 무시합니다. 위의 여섯 개를 self-check가 검증합니다.

## Node 객체

| 필드 | 타입 | 필수 | 의미 |
|---|---|---|---|
| `id` | string | 예 | 실행 안에서 고유. 소문자 kebab-case. handoff 파일명에 쓰입니다. |
| `tier` | `low` \| `medium` \| `high` | 예 | 난이도. 기본은 `low`이고 그 위는 한 줄 이유가 필요합니다. |
| `kind` | `writing` \| `visual` \| `git` | 아니요 | 전문 종류. 난이도가 아니라 작업의 종류로 고릅니다. |
| `dependsOn` | 문자열 배열 | 예, 비어 있을 수 있음 | 먼저 완료돼야 하는 노드 id. 순서를 정하며 데이터를 나르지 않습니다. |
| `reads` | 문자열 배열 | 예, 비어 있을 수 있음 | 노드가 읽을 수 있는 정확한 경로나 glob. |
| `writes` | 문자열 배열 | 예 | 노드가 바꿀 수 있는 정확한 경로나 glob. handoff 포함. |
| `handoff` | string | 예 | `.hyper/mass/<run-key>/nodes/<id>.md`. 실행 디렉터리 안이어야 합니다. |
| `prompt` | string | 예 | 다섯 표지를 갖춘 완전한 node prompt. |
| `reason` | string | `tier`가 `low`가 아닐 때 | 승격 이유 한 줄. |
| `solutionSpace` | 문자열 배열 | 아니요 | 이 노드가 고를 수 있는 짧은 접근 이름 목록. 있으면 node prompt에 적고, 노드는 목록 안의 접근만 골라야 하며(**MUST**), 목록 밖 접근을 쓴 노드는 self-check에서 실패합니다. |
| `resolvedModel` | string | 아니요 | 실제로 실행된 모델. 관찰한 결과에서만 쓰고, dispatch 전에 예측해 쓰지 않습니다. |

`dependsOn`과 `reads`는 목적이 다릅니다. 엣지는 두 노드의 순서를 정하고, read 경로는 노드가 소비하는 것을 지목합니다. 어떤 엣지도 만들지 않는 `reads` 경로는 리더가 제공한 문맥이거나 실수입니다. 시작 전에 어느 쪽인지 정합니다.

`solutionSpace`가 있으면 node prompt가 `SOLUTION SPACE:` 줄(또는 `TASK`/`SCOPE` 안)에 목록을 적어 작업자에게 허용된 접근을 보이게 합니다. 노드는 자기 handoff에 쓴 접근을 밝히고, 리더는 노드가 완료로 세기 전에 그 접근이 목록에 속하는지 확인합니다. `solutionSpace`가 없으면 노드가 자유롭게 고르고, 있으면 선택이 제한되고 검사됩니다.

## Justification 객체

```json
{
  "ceiling_removed": "",
  "topology": "",
  "state": "",
  "bounds": "",
  "approval": "",
  "rollback": ""
}
```

검증 규칙:

- 모든 필드는 비어 있지 않은 문자열입니다.
- `approval`은 되돌리기 어려운 노드마다의 승인 답이나 문자 그대로 `not required`입니다.
- `rollback`은 구체적인 되돌리기를 지목합니다. 브랜치, 커밋 범위, 되돌릴 경로, 또는 "파일 변경 없음"입니다.
- `bounds`는 사용자 덮어쓰기를 포함해 적용 중인 상한을 그대로 적습니다.

## Node prompt

```text
TASK: <명령형 문장 하나>
DELIVERABLE: <아티팩트: 파일, 보고서 형태, 근거>
SCOPE: <정확한 읽기 경로, 정확한 쓰기 경로, 범위 밖 항목>
VERIFY: <문자 그대로의 명령과 기대 결과>
STOP WHEN: <관찰 가능한 조건 하나>
```

표지가 하나라도 빠진 prompt는 self-check를 통과하지 못합니다. handoff를 지목하지만 경로를 쓰지 않거나, 실행 디렉터리 밖 경로를 쓰는 prompt도 통과하지 못합니다.

## Self-check

`run.created` 전에 실행합니다.

1. `key`가 `^[a-z0-9]+(-[a-z0-9]+)*$`에 맞고, 48자 이하이며, `..`, `/`, 절대 경로를 포함하지 않습니다.
2. `goal`이 한 문장이고, `success_criteria`가 비어 있지 않으며 모든 항목이 근거를 지목합니다.
3. `justification`에 비어 있지 않은 여섯 필드가 있습니다.
4. 노드 수가 상한 안이고, `tier: high` 노드가 최대 하나입니다.
5. 모든 `id`가 고유하고 `^[a-z0-9]+(-[a-z0-9]+)*$`에 맞습니다.
6. 모든 `dependsOn` id가 그래프에 존재합니다.
7. 그래프에 순환이 없습니다. 순환은 시작 전에 거부하며 실행 중에 고치지 않습니다.
8. 모든 wave에 실행 가능한 노드가 하나 이상 있습니다.
9. 병렬로 돌 수 있는 노드 둘이 같은 `writes` 경로를 공유하지 않습니다. 겹치면 직렬화하거나 합칩니다.
10. 모든 `handoff`가 `.hyper/mass/<key>/nodes/<id>.md`이고 `writes`에도 들어 있습니다.
11. 모든 `prompt`에 TASK, DELIVERABLE, SCOPE, VERIFY, STOP WHEN이 있습니다.
12. 모든 생산자에 의존하는 종단 검증 또는 검토 노드가 하나 이상 있습니다.
13. 코드를 바꾸는 그래프라면 종단 노드의 VERIFY가 실제 테스트나 빌드 명령을 지목합니다.
14. 모든 `solutionSpace` 항목이 비어 있지 않은 문자열이고, 노드가 사용했다고 보고한 접근이 자기 목록에 속하며, 모든 `resolvedModel` 값이 예측이 아니라 관찰한 결과에서 나왔는지 봅니다.

## `run.jsonl`

한 줄에 JSON 객체 하나, append-only. 공통 필드는 `ts`(ISO 8601 UTC), `event`, `run`입니다.

| 이벤트 | 추가 필드 |
|---|---|
| `run.created` | `mode`, `nodes`, `definition_digest`, `justification` |
| `run.resumed` | `from_event`, `reused_nodes` |
| `node.started` | `node`, `attempt` |
| `node.completed` | `node`, `handoff`, `evidence`, `resolvedModel`(결과에서 관찰한 모델, run journal에만); 검증 노드는 `verifier`(`sequential` 모드에서는 `self (no subagent capability)`) |
| `node.failed` | `node`, `attempt`, `error` |
| `node.retried` | `node`, `attempt`, `reason` |
| `node.sent` | `node`, `boundary` |
| `node.cancelled` | `node`, `reason` |
| `run.amended` | `changed`, `reason` |
| `run.settled` | `status`, `reason`, `criteria`, `landed` |

예:

```json
{"ts":"2026-11-03T09:00:00Z","event":"run.created","run":"checkout-refactor-2026-11-03","mode":"waves","nodes":6,"justification":{"ceiling_removed":"serialized latency","topology":"5 components","state":"handoffs and worktree","bounds":"6 nodes, 4 concurrent","approval":"not required","rollback":"revert branch"}}
{"ts":"2026-11-03T09:00:05Z","event":"node.started","run":"checkout-refactor-2026-11-03","node":"audit","attempt":1}
{"ts":"2026-11-03T09:04:10Z","event":"node.completed","run":"checkout-refactor-2026-11-03","node":"audit","handoff":".hyper/mass/checkout-refactor-2026-11-03/nodes/audit.md","evidence":"13 call sites listed"}
{"ts":"2026-11-03T09:04:11Z","event":"node.started","run":"checkout-refactor-2026-11-03","node":"api","attempt":1}
{"ts":"2026-11-03T09:30:00Z","event":"node.failed","run":"checkout-refactor-2026-11-03","node":"api","attempt":1,"error":"handoff missing; node exited before writing"}
{"ts":"2026-11-03T09:31:00Z","event":"node.retried","run":"checkout-refactor-2026-11-03","node":"api","attempt":2,"reason":"missing handoff, rerun with write-first instruction"}
{"ts":"2026-11-03T10:20:00Z","event":"run.settled","run":"checkout-refactor-2026-11-03","status":"completed","reason":"all criteria pass","criteria":["checkout tests exit 0","e2e log attached"],"landed":["9f2c1ab","41d7e02"]}
```

규칙:

- `node.completed`는 노드가 답했을 때가 아니라 리더가 handoff를 연 뒤에 씁니다. 리더는 바로 그때 관찰한 결과(런타임이 실제로 돌아간 모델을 알린 값)에서 `resolvedModel`을 적습니다. dispatch 전에는 쓰지 않으며 `tier`에서 예측하지 않습니다.
- `solutionSpace`가 있는 노드는 자기 handoff에 쓴 접근을 밝힙니다. 리더는 `node.completed` 전에 목록과 대조하고, 목록 밖 접근은 완료가 아니라 실패한 self-check로 다룹니다.
- `run.settled`는 실행마다 한 번 씁니다. 재개한 실행은 새 dispatch wave 뒤에 새 정산을 덧붙입니다.
- 타임스탬프는 UTC입니다. 보고는 현지 시간으로 보여 줄 수 있지만 journal은 그렇게 하지 않습니다.

## Resume 표

| Journal 상태 | Handoff 파일 | 재개 시 상태 |
|---|---|---|
| `node.completed` | 존재하고 비어 있지 않음 | 완료, 다시 실행하지 않음 |
| `node.completed` | 없거나 비어 있음 | 실패, 시도 횟수 유지 |
| `node.started`만 있음 | 무관 | pending, 준비 집합에서 다시 dispatch |
| `node.failed` | 무관 | 실패, 시도가 남았을 때만 retry |
| `node.failed` 뒤 `node.retried` | 무관 | 시도 횟수가 늘어난 실패 |
| `node.cancelled` | 무관 | 취소됨. 목표를 다시 열 때만 retry |
| 이벤트 없음 | 무관 | pending |

재개한 실행은 무엇이든 dispatch하기 전에 `run.resumed`를 journal에 적습니다.

## 예제

컴포넌트 다섯 개짜리 리팩터링, 한 단계입니다.

```json
{
  "key": "checkout-refactor-2026-11-03",
  "name": "Checkout refactor",
  "goal": "Move checkout onto the new payment client without changing user-visible behavior.",
  "success_criteria": [
    "`npm test -- checkout` exits 0 and its output is captured in nodes/verify.md",
    "`npm run e2e -- checkout` exits 0 and its log is captured in nodes/verify.md"
  ],
  "justification": {
    "ceiling_removed": "serialized latency: three independent surfaces plus one integration proof",
    "topology": "C1 audit, C2 API adapter, C3 UI copy, C4 docs, C5 end-to-end proof",
    "state": "handoff files and the working tree only; no shared in-memory state",
    "bounds": "6 nodes, at most 4 concurrent, 2 retries per node, 3 amends",
    "approval": "not required: no deploy, spend, or external send in this phase",
    "rollback": "revert the branch commits listed in nodes/verify.md; no data migration"
  },
  "nodes": [
    {
      "id": "audit",
      "tier": "low",
      "dependsOn": [],
      "reads": ["src/checkout/**", "src/payments/**"],
      "writes": [".hyper/mass/checkout-refactor-2026-11-03/nodes/audit.md"],
      "handoff": ".hyper/mass/checkout-refactor-2026-11-03/nodes/audit.md",
      "prompt": "TASK: List every checkout call site that uses the old payment client.\nDELIVERABLE: `.hyper/mass/checkout-refactor-2026-11-03/nodes/audit.md` containing a table with file, line, current call, and replacement call.\nSCOPE: read src/checkout/** and src/payments/** only. Write only `.hyper/mass/checkout-refactor-2026-11-03/nodes/audit.md`.\nVERIFY: every row names an existing file and line; run `grep -rn oldPayment src` and paste the count.\nSTOP WHEN: every call site in those directories is listed or marked read-only."
    },
    {
      "id": "api",
      "tier": "low",
      "dependsOn": ["audit"],
      "reads": ["src/payments/**", ".hyper/mass/checkout-refactor-2026-11-03/nodes/audit.md"],
      "writes": ["src/payments/**", ".hyper/mass/checkout-refactor-2026-11-03/nodes/api.md"],
      "handoff": ".hyper/mass/checkout-refactor-2026-11-03/nodes/api.md",
      "prompt": "TASK: Replace the old payment client with the new adapter at every call site listed in nodes/audit.md.\nDELIVERABLE: changed files plus a handoff listing each replacement and the command output.\nSCOPE: write only src/payments/** and nodes/api.md. Do not touch src/checkout/ui/** or tests/**.\nVERIFY: run `npm test -- payments` and paste the exit code and the final summary line.\nSTOP WHEN: the test exits 0 and every audit row is replaced."
    },
    {
      "id": "ui",
      "tier": "medium",
      "kind": "visual",
      "reason": "copy and state changes across four checkout screens",
      "solutionSpace": ["copy-update", "state-map", "a11y-pass"],
      "dependsOn": ["audit"],
      "reads": ["src/checkout/ui/**", ".hyper/mass/checkout-refactor-2026-11-03/nodes/audit.md"],
      "writes": ["src/checkout/ui/**", ".hyper/mass/checkout-refactor-2026-11-03/nodes/ui.md"],
      "handoff": ".hyper/mass/checkout-refactor-2026-11-03/nodes/ui.md",
      "prompt": "TASK: Update the checkout screens to the new payment states named in nodes/audit.md.\nDELIVERABLE: changed components plus a handoff listing each screen and its state mapping.\nSCOPE: write only src/checkout/ui/**. Do not touch src/payments/** or tests/**.\nVERIFY: run `npm run build` and paste the exit code; confirm each mapped state appears in the built bundle.\nSTOP WHEN: the build exits 0 and every listed screen has a mapped state."
    },
    {
      "id": "docs",
      "tier": "low",
      "kind": "writing",
      "dependsOn": ["audit"],
      "reads": ["docs/checkout.md", ".hyper/mass/checkout-refactor-2026-11-03/nodes/audit.md"],
      "writes": ["docs/checkout.md", ".hyper/mass/checkout-refactor-2026-11-03/nodes/docs.md"],
      "handoff": ".hyper/mass/checkout-refactor-2026-11-03/nodes/docs.md",
      "prompt": "TASK: Update docs/checkout.md to describe the new payment client and its states.\nDELIVERABLE: the edited page plus a handoff listing each changed section.\nSCOPE: write only docs/checkout.md and nodes/docs.md. Do not change code.\nVERIFY: every code identifier in the page exists in src/; paste the check command and its output.\nSTOP WHEN: every stale identifier is replaced and the check passes."
    },
    {
      "id": "e2e",
      "tier": "medium",
      "reason": "integration surface across API and UI",
      "dependsOn": ["api", "ui"],
      "reads": ["tests/e2e/**", "src/payments/**", "src/checkout/ui/**"],
      "writes": ["tests/e2e/**", ".hyper/mass/checkout-refactor-2026-11-03/nodes/e2e.md"],
      "handoff": ".hyper/mass/checkout-refactor-2026-11-03/nodes/e2e.md",
      "prompt": "TASK: Add and run the end-to-end checkout test for the new payment client.\nDELIVERABLE: the test file plus a handoff with the command, exit code, and log path.\nSCOPE: write only tests/e2e/** and nodes/e2e.md. Do not change product code; report a product defect instead.\nVERIFY: run `npm run e2e -- checkout` and paste the exit code and the last 20 log lines.\nSTOP WHEN: the suite exits 0 or the failing assertion is written to the handoff."
    },
    {
      "id": "verify",
      "tier": "medium",
      "reason": "independent judgment over every producer",
      "dependsOn": ["audit", "api", "ui", "docs", "e2e"],
      "reads": [".hyper/mass/checkout-refactor-2026-11-03/nodes/**"],
      "writes": [".hyper/mass/checkout-refactor-2026-11-03/nodes/verify.md"],
      "handoff": ".hyper/mass/checkout-refactor-2026-11-03/nodes/verify.md",
      "prompt": "TASK: Verify the checkout refactor against the run's success criteria.\nDELIVERABLE: nodes/verify.md with each criterion, the literal command, exit code, and captured output.\nSCOPE: read every handoff and the repository; write only nodes/verify.md. Do not fix product code.\nVERIFY: `npm test -- checkout` and `npm run e2e -- checkout` both exit 0; every producer handoff exists and is non-empty.\nSTOP WHEN: every criterion has a captured result, or a failing criterion names the producer and the exact failure."
    }
  ]
}
```

audit가 겹치지 않는 세 표면으로 fan-out하고, `e2e`가 두 코드 생산자를 join하며, `verify`가 모든 생산자에 의존합니다. audit의 handoff가 세 표면 모두의 입력이므로 audit도 포함합니다. 두 번째 `high` 노드가 없고, 병렬 노드 둘이 쓰기 경로를 공유하지 않습니다.

## Key와 경로 규칙

- `key`와 `id`는 소문자 ASCII kebab-case를 씁니다. `^[a-z0-9]+(-[a-z0-9]+)*$`입니다. `..`, `/`, 절대 경로를 거부합니다.
- `reads`, `writes`, `handoff`의 경로는 저장소 상대 경로나 절대 경로이며, 노드가 보는 그대로 적습니다. glob은 `reads`와 `writes`에서만 허용하고 `handoff`에는 쓰지 않습니다.
- handoff는 실행 디렉터리 안에 두어 재개한 실행이 추측 없이 찾을 수 있게 합니다.
- 실행 하나에 디렉터리 하나입니다. 다른 key나 바뀐 정의에 디렉터리를 재사용하지 않습니다. 그 일은 `amend`가 합니다.

## Sources

> 확인 2026-11-09.

| Claim | Source |
|---|---|
| 실행 디렉터리 형태, 노드 필드, 의존 규칙, wave 실행, journal 이벤트, 복구 의미를 `mass-ulw` 스킬과 그 계획 참조에서 각색 | <https://github.com/code-yeongyu/oh-my-openagent/tree/0d80470e4201925727e88afbafcdf24d7801a588> |
| 순환 경계, missing은 빈 것이 아님, 생산자와 분리된 검증자, fan-out 상한 | `instructions/graph-engineering/GRAPH_ENGINEERING.md` |
| 체크포인트 resume을 가정하지 않고 시험하기, 동적 경로의 전이 기록 | `instructions/graph-engineering/GRAPH_ENGINEERING.md` |
| 근거 파일이 없으면 일어나지 않은 일, `SKIP`은 통과가 아님 | `instructions/harness-engineering/HARNESS_ENGINEERING.md` |
| 패밀리 계약의 `.hyper/mass/<run-key>/` 경로와 여섯 justification 필드 | 패밀리 계약, 2026-11-03 |
| 노드 `solutionSpace` 경계, 목록 밖 접근 실패, 관찰한 결과에서 가져오는 `resolvedModel`, 토큰 상한과 handoff 인용이 붙은 클러스터 digest, digest만 읽는 최종 reducer | `dbc-hbin/omp-ulw @ 74df40f`(2026-11-09), 다시 쓴 것. 원본 저장소에는 license 파일이 없어 본문·코드를 복사하지 않았습니다 |

### 근거 등급

`LOCAL` - 스키마는 이 패키지가 패밀리 계약을 구현한 것입니다. 필드 이름은 계약과 맞고, `run.resumed`, `node.sent`, `node.cancelled`, `phase`, `caps`, `reason`은 추가이며 이 문서에 적혀 있습니다.
