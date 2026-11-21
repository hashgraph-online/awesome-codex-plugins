# 실행, 재개, 게이트

모든 체크포인트, 모든 재개, 조향 동사가 왔을 때, 실패 한도에 닿았을 때, `final-gate.json`을 쓰기 전에 이 규칙을 읽는다.

## 1. 체크포인트

체크포인트는 작업이 끝난 듯한 순간이 아니라 목표의 증거를 판정하는 순간이다.

- 비최종 체크포인트: 목표의 `essential` 기준이 모두 신선한 증거로 통과하고 `depends_on`의 목표가 모두 `complete`다. 비핵심 기준은 여기서 대기해도 되지만 최종 게이트에서는 안 된다.
- 먼저 검증기를 돌린다. `bash <skill-dir>/scripts/verify-loop-state.sh --goal <id> --dir .hyper/loop/<slug>`. 종료 코드 0이면 체크포인트 행을 덧붙이고, 1이면 아직 체크포인트가 없다.
- 검증기는 아무것도 쓰지 않는다. 종료 코드 0 뒤에 체크포인트 행을 덧붙이고 `goals.json`의 목표 상태를 직접 고친다. 검증기 실행은 상태 변경이 아니다.
- 실패하는 기준을 추가한 체크포인트, 또는 통과하던 기준이 깨진 뒤에야 통과한 체크포인트는 체크포인트가 아니다. 수리를 되돌리고 보고한다.

## 2. 실패 한도

계열 관례는 같은 실패 서명으로 세 번 시도한 뒤 막는 것이다.

| 신호 | 뜻 |
|---|---|
| 실패 서명 | 실패의 정규화된 정체. 실패한 명령, 오류 종류, 실패한 단언이나 종료 코드에서 시간·경로처럼 흔들리는 부분을 뺀 값 |
| 시도 | 그 서명으로 실패한 캡처 한 번 |
| 순환 | 어느 기준이 실패했는지와 무관한, 목표 기준 전체를 한 바퀴 돈 것 |

규칙:

- 같은 서명으로 세 번 시도했거나 목표의 필수 기준이 통과하지 않은 채 다섯 번 순환했으면 목표를 `failed` 또는 `blocked`로 두고 행에 서명을 기록한다.
- 서명이 다르면 새 서명의 시도 횟수는 초기화되지만 순환 횟수는 초기화되지 않는다.
- 막힌 목표는 빠진 의존, 능력, 자격 증명, 판단을 적고 무엇이 해소하는지 적는다. 해소 단계가 없는 "막힘"은 진단이 불분명한 `failed` 목표다.
- 해소 단계가 실제로 일어나고 기록되지 않았으면 같은 실행에서 막힌 목표를 다시 시도하지 않는다.

## 3. 조향

조향 동사는 실행 중 요청이 기록을 거짓으로 만들지 않고 계획을 바꾸는 방법이다. 모든 동사는 `pending` 목표만 바꾼다.

| 동사 | 효과 | 필요한 필드 |
|---|---|---|
| `add_subgoal` | 증거가 범위 안이라고 보여 준 목표를 추가한다. 원래 범위 밖 결함은 발견 사항으로 남긴다 | `title`, `objective`, `depends_on`, `criteria`, `evidence`, `rationale` |
| `split_subgoal` | `pending` 목표 하나를 기준을 유지한 더 작은 목표 여럿으로 바꾼다 | `targetGoalId`, `childGoals`(`title`, `objective`, `criteria` 포함), `evidence`, `rationale` |
| `reorder_pending` | 실제 의존을 깨지 않고 `pending` 목표의 순서를 바꾼다 | `pendingOrder`, `evidence`, `rationale` |
| `revise_criterion` | `pending` 기준의 시나리오·기대 증거·통과 조건을 바로잡는다 | `goalId`, `criterionId`, `scenario`·`expected_evidence`·`pass_condition` 중 최소 하나, `evidence`, `rationale` |
| `mark_blocked_superseded` | 막힌 목표를 물리고 선택적으로 자식 목표로 대체하며 옛 증거를 유지한다 | `targetGoalId`, 선택적 `childGoals`, `evidence`, `rationale` |

동사를 적용하기 전에 확인하는 불변 조건:

- `complete` 목표나 이미 통과한 기준을 대상으로 삼을 수 없다.
- `fail`이나 `stale` 캡처를 `pass`로 바꿀 수 없고, 그 행을 기록한 행을 지울 수 없다.
- 고친 `pass_condition`은 효력이 새로 생긴 기준이다. 옛 증명은 새 조건의 증거가 아니므로 그 기준은 `pending`으로 돌아가고 새 캡처가 필요하다.
- id는 고유하게 유지되고 의존은 순환 없이 유지되며, 어떤 동사도 `brief.md`의 목적을 다시 쓰지 않는다.

제안은 `steering` 행 하나에 결정(수락·거절)과 이유를 담아 기록하고, 수락한 변경을 `goals.json`에 적용한다. 조향은 증거 흔적을 남기는 로컬 파일 변경이지 런타임 기능 요청이 아니다.

## 4. 최종 게이트

완료는 파일 하나와 통과하는 검사다. 선언이 아니다.

`final-gate.json`은 다음을 담는다.

| 필드 | 계약 |
|---|---|
| `status` | `complete`, `blocked`, `paused` 중 정확히 하나. `complete`만 게이트를 통과할 수 있다 |
| `tree`, `diff_sha256` | 게이트를 쓴 시점의 지문. 마지막 변경 뒤에 뜬 스냅샷에서 복사한다 |
| `surfaceEvidence` | 기준 증명마다 한 행. `criterionRef`(`<goal-id>:<criterion-id>`), `surface`, `invocation`, `verdict: "passed"`, `artifactRefs` |
| `criteriaCoverage` | `totalCriteria`, `passCount`, `originalIntent`, `desiredOutcome`, `userOutcomeReview` |
| `review` | 독립 리뷰어가 돌았으면 `{"by": "<리뷰어 정체>", "recommendation": "approve", "evidence": "..."}`. 런타임이 제공하지 않았으면 `{"by": "deterministic", "recommendation": "approve"}`와 검증 명령 |
| `blockers` | `complete`면 빈 배열. 아니면 목표, 서명, 해소 단계 |

규칙:

- `essential: false`를 포함한 모든 목표의 모든 기준에 통과 `surfaceEvidence` 행과 신선한 장부 행이 필요하다. 체크포인트에서 통과한 뒤 낡은 기준은 덮이지 않는다.
- 목표가 선언한 `surface`마다 그 표면의 통과 행이 최소 하나 필요하다. 선언한 표면에 행이 없으면 게이트가 실패한다.
- 게이트 자체의 지문이 지금 뜬 스냅샷과 같아야 한다. 게이트를 쓴 뒤의 수리는 게이트를 무효로 만드니 가장 마지막에 쓴다.
- 런타임이 독립 리뷰어를 제공하면 그 리뷰어를 쓴다. `review: deterministic`은 리뷰어가 없을 때만 정직한 기록이다. 리뷰가 가능했는데 건너뛰는 수단이 아니다.
- `bash <skill-dir>/scripts/verify-loop-state.sh --final .hyper/loop/<slug>/final-gate.json`은 완전하고 덮였고 스냅샷에 묶인 `complete` 게이트에서 종료 코드 0이다. 1은 빠진 것을 열거하고, 2는 파일 자체를 쓸 수 없다는 뜻이다.

## 5. 실행 끝내기

| 끝 | 시점 | 기록 |
|---|---|---|
| `complete` | 게이트가 통과했다 | 실행 상태 `complete`, 게이트 상태 `complete` |
| `blocked` | 실패 한도에 닿았거나 필요한 판단·자격 증명·능력이 없다 | 실행 상태 `blocked`, 게이트 상태 `blocked`, 목표와 서명 명시 |
| `paused` | 사용자가 멈췄다 | 실행 상태 `paused`, 게이트 상태 `paused`. 멈춘 목표는 `in_progress`를 유지하고 사용자 지시가 있을 때만 재개한다 |

마무리 브리핑은 상태 디렉터리, 끝난 목표와 각 목표가 기대는 증거, 끝나지 않은 목표와 이유, 실행이 의도적으로 건드리지 않은 것을 적는다. `blocked`나 `paused`로 끝난 실행은 과정의 실패가 아니라 보고된 결과다.

## 6. 전달 경계

저장소 관례가 요구하면 목표 안에서 커밋해 tree와 기록을 맞춘다. 이 실행은 푸시, 병합, 풀 리퀘스트 생성, 릴리스, 그 밖의 원격 전달을 하지 않는다. 그 일은 자체 판단이 필요한 별도 단계다. 사용자가 같은 요청에서 전달까지 요구하면 루프를 끝내고 게이트를 보고한 뒤, 원격 작업은 전달 단계가 맡게 한다.

## Sources

> 확인 2026-11-09.

아래 출처 경로는 원본 저장소의 스킬 루트(`skills` 디렉터리)를 기준으로 적었다.

| Claim | Source |
|---|---|
| 핵심 기준으로 하는 비최종 체크포인트와, 모든 기준에 형 있는 게이트 파일을 더한 최종 완료 | `dbc-hbin/omp-ulw@74df40f ulw-loop/SKILL.md` 및 `references/full-workflow.md` (메커니즘 참조, 재작성) |
| 조향 동사 집합과, 조향으로 실패한 증거를 통과로 바꿀 수 없다는 규칙 | `dbc-hbin/omp-ulw@74df40f ulw-loop/references/full-workflow.md` (메커니즘 참조, 재작성) |
| 실패 체크포인트 전 같은 서명 세 번, 필수 기준이 통과하지 않은 채 다섯 번 순환 | `dbc-hbin/omp-ulw@74df40f ulw-loop/references/full-workflow.md` (메커니즘 참조, 재작성) |
| `surfaceEvidence`를 통한 기준 덮임과 독립 리뷰어가 없을 때의 `review: deterministic` 대체 | `dbc-hbin/omp-ulw@74df40f ulw-loop/references/full-workflow.md`. 게이트 상태를 이 패키지의 `complete`/`blocked`/`paused`로 바꿔 적용함 |

### Evidence grade

`LOCAL` - 게이트 필드 집합, 상태 이름, 전달 경계는 이 패키지가 정한 것이다. `complete`, `blocked`, `paused` 상태 이름은 자유 텍스트가 아니라 실행 계약이 고정한 값이다. 원본 저장소에는 라이선스가 없으며 메커니즘은 복사하지 않고 다시 작성했다.