---
name: "hyper-mass"
description: "[Hyper] 사용자가 의존 관계가 있는 다중 에이전트 작업을 그래프로 요청할 때 사용합니다. 작업 DAG, mass 실행, \"의존성 그래프\", \"단계별 병렬\"처럼 어떤 작업이 다른 작업보다 먼저 끝나야 하고 그 순서 자체가 핵심인 경우가 여기에 해당합니다. 한 단계를 노드, tier, 쓰기 범위, handoff 파일, 숫자 상한, 검증 노드로 정의한 뒤 네이티브 workflow 기능이나 리더가 도는 토폴로지 wave로 실행하고, retry, amend, send, cancel로 복구합니다. 순서가 없는 독립 병렬 작업, 작성된 계획 파일을 체크박스 순서대로 실행하는 일, 조사 리포트 작성에는 사용하지 않습니다."
compatibility: "하위 에이전트나 백그라운드 에이전트 기능이 있고, 런타임이 제공하면 네이티브 workflow 또는 DAG 엔진이 있을 때 가장 잘 동작합니다. 실행 상태, handoff 파일, 근거 확인을 위한 로컬 셸이 필요하며, 하위 에이전트가 없으면 리더가 각 노드를 순차 실행하고 병렬성 없음을 기록합니다."
---

아래 규칙은 본문의 읽기 순서에 따라 엽니다. 스킬에 포함된 파일 경로는 이 문서가 있는 폴더를 기준으로 해석하고 작업 대상 경로는 프로젝트를 기준으로 해석합니다.

- [rules/graph-planning.ko.md](rules/graph-planning.ko.md)
- [rules/run-and-recovery.ko.md](rules/run-and-recovery.ko.md)

# Hyper Mass Skill

> 의존 관계가 있는 작업의 한 단계를 명시적인 그래프로 바꾸고, wave를 실행하고, 모든 상태 전이를 journal에 기록하며, 목표의 성공 기준이 캡처한 근거와 함께 통과할 때만 끝냅니다.

- **목적**: 의존 순서가 있는 다중 에이전트 작업의 한 단계를 겹치지 않는 쓰기 범위, 노드 handoff 파일, 숫자 상한, 독립 검증 노드를 갖춘 명시적 DAG로 계획하고 실행합니다.
- **쓰지 않을 때**: 작업 간 순서 의존이 없는 독립 병렬 작업, 단일 작업, 작성된 계획 파일의 체크박스 순차 실행, 조사 리포트 작성에는 쓰지 않습니다.
- **입력**: 순서 의존이 있는 한 단계의 목표와 저장소 맥락(재개 시 기존 `.hyper/mass/<run-key>/`의 `graph.json`과 `run.jsonl`).
- **산출물**: `.hyper/mass/<run-key>/{graph.json,run.jsonl,nodes/<node-id>.md}`, 검증된 대상 변경·아티팩트, 한국어 마감 보고.

<output_language>

이 표준 스킬 파일이 영어로 작성되어 있어도 사용자에게 보이는 모든 산출물, 저장 아티팩트, 리포트, handoff 메모, 커밋과 메시지 초안, 검증 메모는 기본적으로 한국어로 씁니다.

소스 코드 식별자, CLI 명령, 파일 경로, 스키마 키, JSON/YAML 필드명, API 이름, 패키지명, 고유명사, 인용한 원문 발췌는 요구 언어나 원문 그대로 유지합니다.

</output_language>

<purpose>

- 다중 에이전트 작업의 한 단계를 첫 dispatch 전에 노드, 엣지, 겹치지 않는 쓰기 범위, handoff 파일, tier, 숫자 상한, 종단 검증 노드가 확정된 선언형 DAG(`graph.json`)로 실행합니다.
- `graph.json`을 계약으로 다루어 모든 전이를 `run.jsonl`에 즉시 기록하고, 그래프 변경은 기록된 `amend` 이벤트로만 수행합니다.
- 생산 노드의 자기 보고가 아니라 종단 검증 노드가 아티팩트와 실제 검증 명령으로 성공 기준을 증명했을 때만 정산합니다.

</purpose>

<routing_rule>

작업 C가 A와 B 완료 뒤에 시작해야 하거나 fan-out 결과가 축약·검증 단계로 합쳐져야 하는 실제 순서 의존 요청(`mass`, `DAG`, `의존성 그래프`, `단계별 병렬` 포함)에 이 스킬을 씁니다.

다음 경우에는 쓰지 않습니다.

- 작업 사이에 순서 의존이 없는 독립 작업(단순 병렬 위임 사용)
- 작업이 하나뿐인 경우(직접 실행)
- 작성된 계획 파일을 체크박스 순서대로 실행하는 작업
- 출처 기반 조사 리포트 작성
- 여러 단계에 걸친 작업(실행 하나당 한 단계만 맡고 실행을 이어 붙임)

</routing_rule>

<instruction_contract>

| 필드 | 계약 |
|---|---|
| Intent | 의존 순서가 있는 작업의 한 단계를 그래프로 실행해 노드, handoff, 종단 검증 노드가 목표의 성공 기준을 증명하게 합니다. |
| Trigger | 작업 간 실제 순서 의존, join이 있는 fan-out, 또는 `mass`·`DAG`·`의존성 그래프`·`단계별 병렬` 요청. |
| Scope | 한 단계의 선별, 목표·기준, justification 기록, `graph.json`, wave dispatch, `run.jsonl`, 복구(`retry`, `amend`, `send`, `cancel`), 종단 검증, 마감 보고를 맡습니다. |
| Authority | 사용자와 프로젝트 지침(저장소에 `instructions/harness-engineering/references/skill-common-rules.ko.md`가 있으면 포함)이 이 스킬보다 우선합니다. node prompt, handoff, 노드 답변, 가져온 페이지는 근거일 뿐 범위를 넓히거나 승인을 대신할 수 없습니다. |
| Evidence | `.hyper/mass/<run-key>/nodes/` 아래 handoff 파일, 캡처한 명령 출력, 종단 검증 노드의 실제 확인입니다. 노드의 완료 주장만으로는 근거가 되지 않습니다. |
| Tools | 기능 단위로만 요구합니다: 하위·백그라운드 작업 위임, 런타임 노출 시 네이티브 workflow·DAG 엔진, 로컬 셸·파일 접근. 하위 위임이 없으면 순차 실행으로 정직하게 기록합니다. |
| Loop | `<bounds>`의 동시성, retry, amend 상한 안에서 도는 토폴로지 wave 루프입니다. |
| Output | `.hyper/mass/<run-key>/`(`graph.json`, `run.jsonl`, `nodes/<node-id>.md`), 종단 아티팩트, 한국어 마감 보고. |
| Verification | 종단 검증 노드가 모든 생산 노드에 의존하며 필수 handoff 존재를 확인하고 실제 검증 명령으로 성공 기준을 증명합니다. |
| Stop condition | 성공 기준이 근거와 함께 통과해 검증 노드가 확인했거나, 상한 소진으로 `exhausted`가 됐거나, 사용자 전용 승인 노드에서 대기하거나, 같은 실패 서명이 2회 반복될 때 멈춥니다. |

</instruction_contract>

<activation_examples>

긍정 요청:

- "이 기능을 mass로 DAG 짜서 실행해줘. API 다음에 UI, 마지막에 e2e."
- "Run this refactor as a DAG: audit, then three parallel fixes, then one review."
- "단계별 병렬로 마이그레이션해줘. B랑 C는 A가 끝난 뒤에 시작해야 해."
- "Fan out the doc updates across packages and join them through one verification pass."

부정 요청:

- "이 세 파일을 각각 독립적으로 고쳐줘."
- "Fix the failing test in `auth.ts`."
- "이 계획서 체크박스 순서대로 실행해줘."
- "WebSocket과 SSE를 비교 조사해서 리포트로 저장해줘."

경계 요청:

- 작업 없이 `hyper-mass`만 온 경우 -> 노드를 정의하기 전에 목표를 묻는 질문 하나만 합니다.
- "DAG로 돌리고, 끝나면 배포까지 해줘." -> 되돌리기 어려운 배포 노드 앞에 승인 노드를 두고 명시적 답을 받기 전에는 dispatch하지 않습니다.
- "한 번에 다 해줘. 조사, 구현, 배포까지." -> 이번 `<run-key>`는 한 단계만 다루고 검증된 근거를 읽은 뒤 다음 실행으로 잇습니다.

</activation_examples>

<trigger_conditions>

| 상황 | 모드 |
|---|---|
| 작업 간 실제 순서 의존 또는 join이 있는 fan-out | 그래프 실행 |
| 여러 단계에 걸친 작업 | 단계마다 실행 하나씩 분리해 리더가 연결 |
| 순서 없는 독립 작업 또는 단일 작업 | 범위 밖(단순 병렬 위임 또는 직접 실행) |
| 작성된 계획서 실행 또는 조사 리포트 | 범위 밖 |
| 런타임이 네이티브 DAG·workflow 엔진 제공 | 네이티브 실행 |
| 네이티브 엔진은 없고 하위 에이전트 위임 가능 | 리더 토폴로지 wave 실행 |
| 엔진과 하위 위임 모두 없음 | 리더 순차 실행 및 병렬성 없음 기록 |

</trigger_conditions>

<bounds>

| 상한 | 값 |
|---|---|
| 그래프당 최상위 컴포넌트 | 1∼6 |
| 실행당 노드 | 32 |
| 동시 노드 | 8, 또는 런타임의 더 낮은 한도 |
| 노드당 retry | 2 (같은 실패 서명 2회 반복 시 즉시 종료) |
| 실행당 amend | 3 |
| `high` tier 노드 | 1 |
| digest 크기 상한 | 기본 5,000 토큰 |

사용자가 지정한 상한이 이 표보다 우선합니다. 노드나 동시성 상한을 넘으면 새 `<run-key>` 실행으로 분할합니다. 배치 하나를 넘는 reducer는 상한 안에서 handoff 인용이 붙은 digest를 내고 최종 reducer는 digest만 읽습니다.

</bounds>

<skill_architecture>

- 코어(`SKILL.ko.md`): 트리거, 계약, 숫자 상한, 단계 게이트, 체크리스트, 종료 조건.
- 규칙: [rules/graph-planning.ko.md](rules/graph-planning.ko.md)(선별, 목표, justification, 토폴로지, 비겹침 쓰기 범위, node prompt, 검증 노드), [rules/run-and-recovery.ko.md](rules/run-and-recovery.ko.md)(실행 모드, wave, `run.jsonl`, 재개, 복구 verb).
- 참조: [references/graph-schema.ko.md](references/graph-schema.ko.md)(`graph.json`, `run.jsonl`, self-check 목록, 예제).
- 자산: `assets/evals/hyper-mass-cases.jsonl`.

</skill_architecture>

<loop_policy>

- 첫 dispatch 전에 준비 집합, 동시성 상한, retry 상한(`2`), amend 상한(`3`)을 고정한 토폴로지 wave 루프 하나를 돕니다.
- 생산 노드의 보고가 아니라 종단 검증 노드가 캡처한 실행 결과가 성공 기준을 증명할 때만 정산합니다.
- 같은 노드 retry 2회, 동일 실패 서명 2회, 또는 같은 실행 amend 3회에 닿으면 남은 공백을 밝히고 `exhausted`로 정산합니다.

</loop_policy>

<language_and_translation_default>

사용자에게 보이는 리포트, handoff 요약, 채팅 출력은 한국어를 기본으로 씁니다. 기계 식별자, `graph.json` 키, `run.jsonl` 이벤트 이름은 영어 원문을 유지합니다.

</language_and_translation_default>

<reference_routing>

- 노드를 정의하기 전과 모든 `amend` 전에 [rules/graph-planning.ko.md](rules/graph-planning.ko.md)를 읽습니다.
- `graph.json`, `run.jsonl` 작성 전과 재개 조정 때 [references/graph-schema.ko.md](references/graph-schema.ko.md)를 읽습니다.
- 4단계 첫 dispatch 전, 재개 시, 복구 verb 실행 전에 [rules/run-and-recovery.ko.md](rules/run-and-recovery.ko.md)를 읽습니다.

</reference_routing>

<support_file_read_order>

1. 이 `SKILL.ko.md`를 읽어 실제 순서 의존을 확인하고 한 단계를 고릅니다.
2. 선별, 목표 기준, justification, 노드 분해를 위해 `rules/graph-planning.ko.md`를 읽습니다.
3. `graph.json` 작성과 self-check 동안 `references/graph-schema.ko.md`를 읽습니다.
4. wave dispatch, 재개, 복구 전에 `rules/run-and-recovery.ko.md`를 읽습니다.

</support_file_read_order>

<workflow>

### 재개 절차

1단계를 시작하기 전에 `.hyper/mass/` 아래에 이번 작업과 일치하거나 사용자가 지목한 `<run-key>` 디렉터리가 있는지 확인합니다. `graph.json`과 `run.jsonl`이 있으면 두 파일과 기존 `.hyper/mass/<run-key>/nodes/*.md` handoff를 먼저 읽고 `run.jsonl`에 `run.resumed`를 추가한 뒤, handoff 파일이 디스크에 존재하는 완료 노드는 건너뛰고 다음 준비 wave부터 이어 갑니다(`rules/run-and-recovery.ko.md`). `.hyper/mass/`에 쓰기 전에 `.gitignore`의 `.hyper/` 등록 여부를 확인합니다.

| 단계 | 수행 작업 | 끝 조건 | 건너뛰면 안 되는 이유 |
|---|---|---|---|
| 1 | 순서 의존 필요성을 선별하고 한 단계만 고정한 뒤 재개 상태와 증거 기반 목표·성공 기준 작성 | 선별 결과, 단일 단계 범위, 목표·성공 기준 블록이 기록됨 | 순서 없는 작업이나 다단계 작업을 한 그래프에 넣으면 상한과 종료 기준이 무너짐 |
| 2 | 6개 필드의 `justification`(병목, 토폴로지, 상태, 상한, 승인, rollback)을 쓰고 비순환 노드 분해 | 모든 노드에 고유 ID, tier 사유, 병렬 비겹침 쓰기 범위, handoff 경로, prompt가 지정됨 | 병렬 노드의 쓰기 범위가 겹치면 서로의 변경을 조용히 덮어씀 |
| 3 | 종단 검증 노드와 digest reducer 규칙을 포함해 self-check를 돌리고 `graph.json` 저장 | `.hyper/mass/<run-key>/graph.json`이 비순환·상한·쓰기 범위·검증 노드 점검을 통과함 | 확정된 `graph.json` 없이 dispatch하면 실행 중 범위가 임의로 흔들림 |
| 4 | `run.jsonl`에 `run.created`(또는 `run.resumed`)를 기록하고 동시성 상한 안에서 준비된 wave 실행 | 전이마다 `run.jsonl`에 즉시 기록되고 완료 노드의 `nodes/<id>.md` handoff가 확인됨 | handoff 누락이나 사후 일괄 기록은 중단 복구와 하위 노드 입력을 깨뜨림 |
| 5 | 실패나 그래프 수정 필요 시 상한 안에서 복구(`retry` <= 2, `amend` <= 3, `send`, `cancel`) 수행 | 복구 이벤트가 `run.jsonl`에 기록되거나 한도 도달 시 `exhausted`로 정직하게 멈춤 | 같은 실패 서명에 세 번째 시도를 쓰면 원인을 바꾸지 못한 채 예산만 소모함 |
| 6 | 모든 생산 노드에 의존하는 종단 검증 노드로 실제 확인을 돌리고 `run.settled`와 한국어 마감 보고 작성 | 검증 명령 출력이 성공 기준을 증명하고 `run.settled` 기록 뒤 마감 보고가 출력됨 | 생산 노드의 완료 주장만 믿고 정산하면 깨진 통합 결과가 그대로 남음 |

### 단계 점검 체크리스트

wave를 넘기거나 실행을 정산하기 전에 아래 예/아니오 항목을 확인합니다.

| # | 예/아니오 질문 | 위반 시 되돌아갈 단계 |
|---|---|---|
| 1 | 실행이 실제 순서 의존이 있는 한 단계만 다루며 `run.created` 전에 6개 필드 `justification`을 적었습니까? (예/아니오) | 1단계 |
| 2 | `graph.json`에 순환이 없고 `<bounds>` 상한(노드 <= 32, `high` tier <= 1)과 병렬 노드 비겹침 쓰기 범위를 지켰습니까? (예/아니오) | 2단계 |
| 3 | 완료된 상위 노드마다 비어 있지 않은 `.hyper/mass/<run-key>/nodes/<id>.md`가 있고 다중 배치 reducer가 토큰 상한 digest만 주고받습니까? (예/아니오) | 4단계 |
| 4 | 모든 상태 전이와 `amend`·`retry` 이벤트가 상한 안에서 즉시 `run.jsonl`에 기록됐습니까? (예/아니오) | 5단계 |
| 5 | 생산자와 분리된 종단 검증 노드가 아티팩트를 열고 실제 검증 명령을 통과한 뒤 `run.settled`를 기록했습니까? (예/아니오) | 6단계 |

</workflow>

<required>

- `run.created` 전에 작성한 목표, 증거 기반 성공 기준, 단일 단계 범위, 6개 필드 `justification`.
- `<bounds>` 상한을 지키는 비순환 `graph.json`, 병렬 노드 비겹침 쓰기 범위, 노드별 `.hyper/mass/<run-key>/nodes/<node-id>.md` handoff, 최대 1개의 `high` tier 노드.
- 모든 생산 노드에 의존하며 실제 검증 명령을 실행하는 분리된 종단 검증 노드 1개.
- 배치 하나를 넘는 축약에서의 토큰 상한(`<= 5,000` 토큰)·handoff 인용 digest 규칙과 선언 시 `solutionSpace`·`resolvedModel` 대조.
- 타임스탬프가 붙은 `run.jsonl` 이벤트 기록과 실행 key, 노드 결과, handoff 경로, 검증 출력, 복구 조치, 잔여 위험을 담은 한국어 마감 보고.

</required>

<forbidden>

- 순서 없는 작업 그래프화, 다단계 작업 단일 실행, `<bounds>` 상한 초과, 병렬 노드 간 동일 경로 쓰기, 다른 스킬 이름 의존 선언.
- 나쁜 예: 병렬로 도는 두 작업 노드가 동시에 `src/router.ts`를 수정하도록 배치함. -> 좋은 예: 병렬 노드의 쓰기 범위를 파일 단위로 분리하거나 직렬·통합 노드로 순서를 둠.
- 나쁜 예: `nodes/api.md` handoff 파일이 없는데 빈 결과로 치고 하위 UI 노드를 시작함. -> 좋은 예: handoff 누락을 `node.failed`로 기록하고 하위 dispatch 전에 복구 절차를 밟음.
- 나쁜 예: 생산 노드가 자기 결과를 스스로 검증하거나 날 노드 출력 20개를 최종 종합 노드에 바로 넣음. -> 좋은 예: 배치별 5,000 토큰 이하 인용 digest로 축약하고 분리된 종단 검증 노드가 실제 명령으로 확인함.
- 나쁜 예: wave 사이에 `graph.json`을 조용히 고치거나 똑같은 실패 서명을 세 번 재시도함. -> 좋은 예: 그래프 변경은 `run.amended`(최대 3회)로 기록하고 같은 실패 서명이 2회 반복되면 노드를 종료함.

</forbidden>

<validation>

- [ ] 선별에서 실제 순서 의존과 제거할 병목을 확인했고 한 단계만 범위에 두었다.
- [ ] `run.created` 전에 목표, 증거 기반 성공 기준, 6개 필드 `justification`을 작성했다.
- [ ] `graph.json`에 순환이 없고 `<bounds>` 상한과 병렬 노드 비겹침 쓰기 범위를 지켰다.
- [ ] 완료된 모든 노드가 `.hyper/mass/<run-key>/nodes/<node-id>.md`를 남겼고 다중 배치 reducer가 상한 내 인용 digest만 썼다.
- [ ] 생산자와 분리된 종단 검증 노드가 실제 검증 명령을 실행해 출력을 캡처했다.
- [ ] `run.jsonl`에 모든 전이·복구·`run.settled` 이벤트가 기록됐고 재개 실행이 완료 노드를 다시 돌리지 않았다.

</validation>

## Sources

> 확인 2026-11-09.

| Claim | Source |
|---|---|
| 의존 그래프 오케스트레이션, 실행당 한 단계, 토폴로지 고정, split 우선 라우팅, node prompt 계약, 검증 wave, 복구 verb | <https://github.com/code-yeongyu/oh-my-openagent/tree/0d80470e4201925727e88afbafcdf24d7801a588> |
| 그래프 전 선별, 구조적 승인 노드, 생산자와 분리된 검증자, fan-out 상한, missing은 빈 것이 아님 | `instructions/graph-engineering/GRAPH_ENGINEERING.md` |
| 종료 조건의 숫자 상한과 예산 소진의 `exhausted` 정산 | `instructions/loop-engineering/LOOP_ENGINEERING.md` |
| 근거 파일이 없으면 일어나지 않은 일, `SKIP`은 통과가 아님, 독립 판정 입력 | `instructions/harness-engineering/HARNESS_ENGINEERING.md` |
| 위임 prompt 항목과 상위 통합·검증 원칙 | `instructions/context-engineering/references/parallel-workflows.md` |
| 계약 필드, 트리거 우선 description, 두 언어 패키지 형태 | `instructions/skill/SKILL_AUTHORING.md` |
| `solutionSpace` 경계, 인용 digest 축약, digest만 읽는 최종 reducer, 관찰된 `resolvedModel` | `dbc-hbin/omp-ulw @ 74df40f`(2026-11-09, 복사 없이 재작성) |

### 근거 등급

위에 고정한 출처를 기능 중립적 표현으로 각색한 절차이며, 숫자 상한은 저장소의 루프·그래프 규칙에서 가져왔습니다.
