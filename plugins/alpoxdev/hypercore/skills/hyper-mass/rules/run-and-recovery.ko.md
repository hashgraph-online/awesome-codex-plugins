# 실행과 복구

첫 dispatch 전, 모든 resume 전, 모든 복구 verb 전에 이 규칙을 읽습니다. 리더가 실행을 소유합니다. dispatch하고, journal에 적고, 감독하고, 복구하고, 목표가 달성됐는지 결정합니다. 노드는 자기 작업이 실행을 끝낸다고 결정하지 않습니다.

## 1. 실행 모드

런타임이 실제로 제공하는 것에서 모드를 고르고, 그 선택을 `run.created`에 기록합니다.

| 모드 | 조건 | 동작 |
|---|---|---|
| `native` | 런타임이 workflow 또는 DAG 기능을 제공 | 이 정의를 그 기능에 제출하고, 그 이벤트를 구독하고, 모든 전이를 `run.jsonl`에 그대로 옮깁니다. 그래프 파일과 journal이 의도의 기록으로 남습니다. |
| `waves` | subagent나 background agent가 있고 네이티브 엔진은 없음 | 리더가 준비 노드를 계산하고 wave를 직접 dispatch합니다. |
| `sequential` | 둘 다 없음 | 리더가 토폴로지 순서대로 각 노드를 직접 실행하고 `parallelism: none`을 기록합니다. 검증 노드는 `verifier: self (no subagent capability)`를 기록하고 결정적 판정만 낼 수 있으며, 정산은 `maker-checker not available`을 밝힙니다. |

- 네이티브 모드가 상한, 쓰기 범위, 검증 계약의 소유권을 넘기지는 않습니다. 엔진이 정의를 지켰다고 가정하지 말고 그 상태를 `graph.json`과 대조합니다.
- 네이티브 엔진에 복구 verb가 없으면 흉내 내지 않습니다. 지원되는 가장 가까운 동작을 쓰고, 그 대체를 journal에 적고, 공백을 정산에서 밝힙니다.
- `sequential` 모드에서는 생산자와 판정자가 같은 작업자입니다. 검증 노드의 handoff와 `node.completed` payload에 `verifier: self (no subagent capability)`를 적고, 판정은 결정적 확인으로 제한합니다. 캡처한 출력이 있는 명령, 파일 존재, diff입니다. 자기 평가를 독립 검토처럼 제시하지 않습니다.
- 어떤 모드도 의존 노드가 완료되지 않았거나 handoff가 관찰되지 않은 노드를 dispatch할 수 없습니다.

## 2. 토폴로지 wave

`waves` 모드의 절차입니다.

1. journal을 읽고 준비 집합을 계산합니다. 의존이 모두 `completed`이고 handoff가 존재하는 pending 노드입니다.
2. 준비된 모든 노드를 동시성 상한(8, 또는 런타임의 더 낮은 한도)까지 한 번에 dispatch합니다.
3. burst가 정산될 때까지 기다립니다. 노드별로 폴링하지 않고, 실행 중에는 독립적인 리더 작업을 합니다.
4. 정산된 각 노드의 handoff를 열고, 하위 노드가 의존하는 특정 사실을 확인한 뒤 `node.completed` 또는 `node.failed`를 journal에 적습니다.
5. 준비 집합을 다시 계산하고 다음 wave를 엽니다.
6. 목표 기준이 통과하거나, 상한이 실행을 끝내거나, 사용자만 결정할 수 있는 사항이 다음 노드를 막으면 멈춥니다.

규칙:

- 하위 노드는 조상의 handoff가 디스크에 존재하기 전에 dispatch되지 않습니다.
- 동시성 상한을 넘는 노드는 실패가 아니라 대기입니다. 폭은 대기 시간을 늘릴 뿐 정확성을 잃지 않습니다.
- pending 노드가 남았는데 wave가 비면 정체입니다. 완료가 아닙니다. 충족되지 않은 의존이나 없는 handoff가 원인이므로 journal을 다시 읽고 원인을 고칩니다.
- 오케스트레이터 역할의 리더는 제품 파일을 직접 편집하지 않습니다. dispatch하고, 검증하고, 기록합니다.

## 3. Journal

`run.jsonl`은 append-only이고, 한 줄에 JSON 객체 하나이며, 이벤트 순서를 따릅니다.

| 이벤트 | 기록 시점 | payload |
|---|---|---|
| `run.created` | 첫 dispatch 전 | `mode`, `nodes`, `definition_digest`, justification 존재 여부 |
| `run.resumed` | 기존 실행을 재개할 때 | `from_event`, `reused_nodes` |
| `node.started` | dispatch 직전 | `node`, `attempt` |
| `node.completed` | handoff를 열어 확인한 뒤 | `node`, `handoff`, `evidence` |
| `node.failed` | 실패를 관찰한 뒤 | `node`, `attempt`, `error` |
| `node.retried` | retry를 발행할 때 | `node`, `attempt`, `reason` |
| `node.sent` | 조정 메시지를 전달할 때 | `node`, `boundary` |
| `node.cancelled` | 실행 취소 중 노드의 자식을 멈춘 뒤 | `node`, `reason` |
| `run.amended` | 정의 변경을 받아들일 때 | `changed`(노드 id), `reason` |
| `run.settled` | 실행이 끝날 때 | `status`, `reason`, `criteria`, `landed`(이 실행이 커밋한 sha들, 또는 사유와 함께 빈 배열) |

규칙:

- 모든 줄에 ISO 8601 UTC 형식의 `ts`와 `event`가 있습니다.
- dispatch 전에 `node.started`를 쓰고, 결과를 관찰한 뒤 `node.completed`와 `node.failed`를 씁니다. 노드의 메시지만 보고 쓰지 않습니다.
- 역사를 다시 쓰지 않습니다. 정정은 새 이벤트입니다.
- 노드는 handoff가 존재하고 리더가 그것을 열었을 때만 완료입니다. 막혔다고 보고하는 답변은 완료가 아니라 실패입니다.
- journal이 resume의 진실 원천입니다. 네이티브 엔진 상태는 두 번째 의견입니다.

## 4. Resume

실행 디렉터리가 이미 있으면 다음 순서로 처리합니다.

1. 어떤 노드도 건드리기 전에 `graph.json`과 `run.jsonl`의 모든 줄을 읽습니다.
2. journal에서 노드 상태를 재구성합니다. handoff가 존재하는 완료 노드는 완료로 남고 다시 실행하지 않습니다. handoff가 없는 완료 노드는 `failed`로 내립니다. 시작했지만 정산되지 않은 노드는 pending으로 돌립니다. 실패 노드는 시도 횟수를 유지합니다.
3. 재사용한 노드 id와 함께 `run.resumed`를 journal에 적습니다.
4. 준비 집합을 다시 계산하고 첫 미완성 wave부터 이어 갑니다.

| 상황 | 행동 |
|---|---|
| 같은 key, 같은 정의, 중단됨 | 재개. 완료 노드는 다시 실행하지 않음 |
| 같은 key, 바뀐 정의 | `amend`. 바뀌거나 추가된 노드와 그 전이 의존만 다시 실행 |
| 같은 key, 완료된 실행, 변경 없음 | 그대로 반환. 아무것도 예약하지 않음 |
| 같은 작업에 새 key | retry가 아니라 다른 실행. 실패 복구에 쓰지 않음 |
| 완료 노드의 handoff 없음 | 실패로 다루고 상한 안에서 retry |

전체 그래프를 다시 dispatch하는 방식으로 재개하지 않습니다. 끝난 작업을 반복하고 부작용을 두 번 낼 수 있습니다.

## 5. 복구 Verb

| Verb | 대상 | 규칙 |
|---|---|---|
| `retry` | 실패하거나 취소된 노드, 또는 지목한 일부 | 실패를 prompt에 붙여 새로 시도합니다. 건너뛴 하위 노드는 실패한 조상이 retry 집합에 있을 때만 다시 들어갑니다. 완료 노드는 거부되며 그 경로는 `amend`입니다. 실행이 아직 활성이면 거부되므로 wave가 정산될 때까지 기다립니다. 노드당 두 번입니다. |
| `amend` | 정의 | 노드마다 지문을 비교합니다. 바뀌지 않은 완료 노드는 handoff를 유지하고, 바뀌거나 추가된 노드와 그 전이 의존만 다시 실행합니다. 실행 중인 노드에 대한 amend는 거부됩니다. 실행당 세 번입니다. 바뀐 id와 이유를 `run.amended`에 적습니다. |
| `send` | 실행 중이거나 상주 중인 노드 하나 | 노드를 자기 `SCOPE` 안으로 되돌리거나, 끝났지만 상주 중인 자식을 문맥 그대로 다시 깨웁니다. 정의를 바꾸지 않습니다. 영구적인 변경은 `amend`입니다. 이어 갈 수 없는 노드는 거부되고 해결책은 `retry`입니다. |
| `cancel` | 실행 전체 | 목표를 포기할 때만 이유와 함께 씁니다. 시간이 지났다는 것만으로는 정당하지 않습니다. 먼저 활성 노드의 자식을 모두 멈추고 종료하며 노드마다 `node.cancelled`를 journal에 적습니다. 활성 노드가 하나도 없을 때만 `status: cancelled`와 이유를 `run.settled`에 적습니다. 정산 뒤에 계속 쓰는 노드는 없어야 합니다. |

- retry는 새 시도이지 새 key가 아닙니다.
- amend는 정의 변경이지 retry가 아닙니다. 상한을 피하려고 둘을 섞지 않습니다.
- send는 조정이지 새 지시문이 아닙니다. 노드가 다르게 일해야 하면 prompt를 amend합니다.
- 모든 verb는 journal 한 줄을 만듭니다. 기록 없는 복구는 일어나지 않은 일입니다.

## 6. 감독

감독은 상태를 지켜보는 일이 아니라 실행 중인 작업을 읽는 일입니다.

매 wake마다 활성 노드를 그 노드의 `SCOPE`와 대조합니다.

- 선언한 `writes` 밖에 쓰는가
- `DELIVERABLE`을 넘어 과하게 만드는가
- 끝내지 않고 하위 문제 하나를 맴도는가
- 범위가 패키지 하나인데 저장소 전체를 읽는가
- 이웃 노드의 일을 가져가는가

흔들리면 넘은 경계를 정확히 지목해 `send`합니다. 계속 벗어나는 노드는 wave가 정산된 뒤 `retry`나 `amend`로 prompt를 조입니다. wave 1에서 고친 흔들림은 메시지 하나면 되지만, 종합 단계에서 발견한 흔들림은 실행 전체를 잃습니다.

## 7. 실패 대응

| 증상 | 해석 | 행동 |
|---|---|---|
| 노드 하나가 실패 | 그 하위 노드만 막히고 나머지 그래프는 정상 | 오류를 읽고, 오류를 prompt에 넣어 그 노드를 `retry` |
| 여러 노드가 시작 몇 초 만에 handoff 없이 실패 | prompt 문제가 아니라 provider나 라우트 폭풍 | 발행을 멈추고 라우트를 고친 뒤 `retry`. 완료 노드는 결과 유지 |
| wave 중간에 실행 중인 노드가 0개 | 동시성 상한의 대기열이며 정체가 아님 | 노드 상태를 확인하고 기다림. 취소하거나 다시 dispatch하지 않음 |
| 노드가 완료라고 하는데 handoff가 없거나 비어 있음 | 거짓 완료 | 실패로 표시하고 retry. 빈 handoff를 하위로 넘기지 않음 |
| 하위 노드가 입력 handoff를 찾지 못함 | 엣지가 데이터를 나르지 못함 | 그 노드와 실행 기준을 FAIL로 처리. 가정으로 진행하게 두지 않음 |
| 같은 노드에서 같은 실패 서명이 두 번 | 원인이 일시적이지 않음 | 그 노드를 멈추고 서명을 보고하고 amend하거나 에스컬레이션 |
| retry나 amend 상한에 도달 | 상한 안에서 수렴할 수 없음 | `exhausted`로 정산하고, 충족하지 못한 기준을 밝히고, 분할이나 사용자 결정을 제안 |
| 네이티브 엔진과 journal이 불일치 | 엔진은 기록이 아님 | handoff를 다시 읽어 조정하고 해결을 journal에 적음. 엔진을 조용히 믿지 않음 |
| 노드가 자기 작업에 대해 "확인됨"이라고 보고 | 검증되지 않은 주장 | 검증 노드가 실제 확인을 다시 실행 |
| 되돌리기 어려운 작업이 dispatch되려 함 | 승인은 문장이 아니라 노드 | dispatch 전에 멈추고 사용자만 답할 수 있는 질문 하나를 함 |

## 8. 반영, 정산, 보고

파일을 바꾼 실행은 정산 전에 그 변경을 반영합니다. 이 단계가 자기 전달을 소유하므로 뒤에서 커밋해 줄 단계가 없고, 반영하지 않은 실행은 체크아웃이 넘어가는 순간 작업을 잃습니다.

- 결산된 노드의 `writes`에 적힌 경로만 스테이징하고 저장소 메시지 관례로 커밋하며, 웨이브 순서대로 웨이브마다 커밋 하나를 만들고 각 sha를 정산 payload의 `landed`에 기록합니다.
- 체크아웃이 이미 있는 브랜치에 커밋하고 그 브랜치 이름을 정산에 적습니다. 브랜치를 바꾸거나 rebase하거나 직접 병합을 반영하지 않습니다.
- 푸시, PR 생성, 병합은 사용자가 이 대화에서 그 전달을 요청했을 때만 합니다. 그렇지 않으면 커밋은 로컬에 남고 정산이 그 사실을 밝힙니다.
- 사용자가 이름을 대지 않은 `main`, `master`, 기본 브랜치, 배포 브랜치에는 병합하지 않고, force-push하지 않습니다.
- git 체크아웃이 아니거나, 이 실행이 건드리지 않은 변경이 이미 있는 체크아웃이면 커밋하지 않고 `landed: []`와 사유로 정산하며, 변경은 작업 트리에 그대로 두고 사용자에게 남깁니다.

다음 가운데 하나일 때만 정산합니다.

- 모든 성공 기준이 캡처한 근거와 함께 통과하고 검증 노드가 확인하며(`completed`) 반영된 커밋이 기록됨
- 상한이나 두 번 반복된 실패가 실행을 끝냄(`exhausted` 또는 `failed`)
- 사용자가 목표를 취소함(`cancelled`)
- 사용자만 결정할 수 있는 사항이 다음 노드를 막음(질문 하나를 기다리는 `blocked`)

마감 보고에는 실행 key와 디렉터리, 노드 결과, handoff 경로, 검증 명령과 캡처한 결과, 반영된 커밋 또는 반영하지 않은 사유, 모든 retry와 amend, 도달한 상한, 잔여 위험이 들어갑니다. `sequential` 모드에서는 `maker-checker not available`도 밝힙니다. 마지막 노드가 반환했다는 이유로 실행이 완료됐다고 보고하지 않습니다.

## Sources

> 확인 2026-11-03.

| Claim | Source |
|---|---|
| 네이티브 workflow 실행과 리더 wave, journal 이벤트 집합, journal 기반 resume, retry/amend/send/cancel 의미를 `mass-ulw` 스킬에서 각색 | <https://github.com/code-yeongyu/oh-my-openagent/tree/0d80470e4201925727e88afbafcdf24d7801a588> |
| fan-out 상한, 없는 분기 규칙, 체크포인트 resume, 생산자가 자기 작업을 채점하는 안티패턴 | `instructions/graph-engineering/GRAPH_ENGINEERING.md` |
| 종료 조건의 숫자 상한과 예산 소진을 완료가 아닌 `exhausted`로 보고 | `instructions/loop-engineering/LOOP_ENGINEERING.md` |
| 근거 파일이 없으면 일어나지 않은 일, `SKIP`은 통과가 아님, 행위자와 분리된 판정자 | `instructions/harness-engineering/HARNESS_ENGINEERING.md` |
| 상위가 통합하고 검증하며, 요약이 아니라 아티팩트를 받음 | `instructions/context-engineering/references/parallel-workflows.md` |

### 근거 등급

`LOCAL` - 이 파일은 이 패키지의 실행 계약을 서술합니다. 이벤트 이름과 verb 규칙은 업스트림 스킬에서 각색했고, 상한과 resume 표는 패밀리 계약에 맞춘 이 패키지의 선택입니다.
