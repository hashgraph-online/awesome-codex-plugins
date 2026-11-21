# Hyper Docs용 Validation 규칙

**목적**: 완료 주장이 취향이 아니라 evidence로 뒷받침되게 합니다.

## 1. Completion Contract

모든 완료는 다음을 기록합니다.

```text
Claim → Risk → Evidence → Verification → Result → Caveat
```

`Result`는 확신 표현이 아니라 검사한 결과입니다. `ship`, `iterate`, `caveated ship`, `block` 중 하나를 결정하며, 건너뛴 점검, 실패한 guard, 남은 risk를 숨기지 않습니다.

## 2. Risk Depth와 Scope

점검을 고르기 전에 각 중요한 claim을 분류합니다.

| Depth | 적용 조건 | 최소 evidence와 gate |
|---|---|---|
| Low | 동작, source, side effect 변화가 없는 로컬 문구 또는 서식 변경 | Readback과 structural check |
| Medium | Workflow, instruction, link, schema, portability 동작 변경 | 대표 scenario, 명시적 oracle, 검사한 result |
| High | 외부/최신 주장, tool, subagent, safety boundary, consequential action, bounded loop | normal, missing-capability/context, boundary, adversarial, regression scenario; output과 trajectory 점검 |
| Critical | production, destructive, credentialed, publication, deployment, irreversible effect | 명시적 authority, precondition/approval gate, 독립 evidence, 불확실하면 block |

벌크 또는 “모든 X” 요청은 전체 후보를 search/glob하고, 포함/제외 기준을 기록하며, 새 후보를 추가하거나 정당화하고, 완료 전 재검색하고, 의도적 제외를 보고합니다.

비결정적 주장은 반복 실행으로 측정하고, 기록에는 case별 실행 횟수, case별 비율, 구간을 적습니다. 한 번의 실행에서 나온 통과/실패는 근거가 아니라 일화로 보고합니다.

미래 source date는 거부합니다. 실제 재확인하지 않았다면 `last_verified_at` 또는 동등한 verification date를 바꾸지 않습니다.

## 3. Evaluation Contract

Medium 이상 risk의 각 claim에는 아래를 정의합니다.

| Element | 필수 의미 |
|---|---|
| Scenario | Input, context, capability, 관련 failure 또는 adversarial condition |
| Oracle | 관측 가능한 필수/금지 동작; self-grading이 아님 |
| Runner | 누가/무엇이 어떤 capability 제한으로 scenario를 실행하는지 |
| Judge | oracle을 평가하는 deterministic check, 자격 있는 reviewer, 또는 명시한 rubric |
| Trace | tool, state, delegation, side effect가 중요할 때 필요한 execution trajectory evidence |
| Gate | pass/fail threshold, keep/discard rule, ship/iterate/caveated ship/block 결과 |

검증은 claim에 맞춰야 합니다. 구조에는 heading/fence/link/readback check, source 주장에는 ledger 또는 claim-source matrix와 최신 official evidence, prompt/instruction 변경에는 smoke case와 known-failure readback, harness 변경에는 tool, safety, context/state, eval 경계를 사용합니다.

memory, notes, retrieval corpus 저장소를 규정하는 문서에는 그 자체의 점검이 붙습니다. 모든 쓰기 경로를 검토하고, 저장 항목에 provenance 필드를 두고, 나중 세션이 그 저장소를 읽는 상황을 재현합니다. retrieved text가 오래 남는 context가 되는 지점이 그 쓰기이고, 검토도 그 지점에서 필요합니다.

### 3.1 비결정적 결과의 판정

| 결정 | 요건 |
|---|---|
| 지표 | 일관성이 곧 산출물이면 `pass^k`, 한 번의 성공으로 충분하면 `pass@k`를 보고하고, case마다 한 번씩 돌린 평균만 보고하지 않습니다 |
| 게이트 | 동등성 여유와 실행 횟수가 사는 구간 폭을 따로 적습니다. 여유 안의 변화는 막지 않고, 좁은 구간이 퇴행을 무시할 근거가 되지는 않습니다 |
| 평가 대상 | 결정적 검사를 우선하고 경로가 아니라 산출물을 채점합니다. tool 호출 순서 검사는 설계자가 예상하지 못한 정당한 접근을 벌합니다 |
| 부분 점수 | 구성 요소가 여럿인 과제에는 부분 점수를 줍니다. "문제는 찾았지만 쓰기에 실패"와 "처음부터 실패"는 다른 결과입니다 |
| 평가기 무결성 | 잘못된 이유로 실패하는 case로 평가기를 시험합니다. 통과에 과제 해결을 요구하고, 매 시도를 이전 시도와 격리합니다 |
| 범위 | 행동이 일어나야 하는 곳과 일어나면 안 되는 곳을 함께 시험해 과잉 트리거를 학습하지 않게 합니다. 도메인 전문가 둘이 과제 문장만 보고 같은 판정에 이르러야 하며, 통과율 0%는 대개 수행 능력의 문제가 아니라 과제나 평가기가 깨졌다는 신호입니다 |
| 판정자 | rubric과 차원별 반례, "알 수 없음" 판정을 줍니다. 차원은 따로 채점하고, 판정자의 모델·버전·사람 라벨과의 일치율을 기록합니다 |

결과를 결정하는 모델 판정자는 사람이 라벨링한 표본으로 보정해 일치율을 기록하거나, 보정하지 않았다고 보고합니다. 일치율 80% 부근이 관측된 상한입니다. 사람끼리도 그 정도로 갈리기 때문입니다. 일치율 100%로 보고된 판정자는 측정이 깨진 것이고, 판정자를 여러 개 붙이는 것은 보정을 대신하지 못합니다.

## 4. Trace Assertions

agent, subagent, tool, background workflow를 문서화할 때 관련 trajectory evidence를 요구합니다.

- bounded objective, scope, output, stop condition
- 독립 작업 또는 명시적 sequencing; 선언한 write ownership과 shared-resource conflict 없음
- least-privilege capability access 및 capability 부재 시 명시적 fallback, skip, block 경로
- child evidence reporting, parent synthesis, parent final verification
- consequential side effect의 approval/precondition gate
- no loop 또는 관측 가능한 feedback, metric/rubric, guard, bounded iterations, keep/discard rule, stop condition

## 5. Smoke Eval Shape

선택한 risk depth에 맞는 압축된 case를 사용합니다.

```yaml
id: unique-case-id
risk: low|medium|high|critical
scenario:
  intent: user goal
  context: { files: [], sources: [], capabilities: [] }
  condition: normal|missing_context|boundary|adversarial|regression
oracle:
  must: [required behavior]
  must_not: [forbidden behavior]
runner: capability-limited executor
judge: 결정적 검사, 또는 보정 상태를 밝힌 rubric
trace: required trajectory evidence or none
runs: 3
gate: 집계 규칙, 동등성 여유, ship 결정
```

trigger case는 참/거짓 하나로 끝나지 않습니다. positive, negative, boundary case마다 `expect`(`trigger` 또는 `no_trigger`), `runs`, `threshold`를 그 case에 적고, 실행 결과에는 측정한 비율을 기록합니다. 기본값을 물려받게 하지 않습니다. 실행 횟수가 달라지면 비율의 의미도 달라지기 때문입니다. `runs` 3회와 `threshold` 0.5는 권장 출발점이며 검증된 최적값이 아닙니다. 경계가 모호한 case에 세 번째 기대값을 만들지 않고 `note`와 함께 `no_trigger`로 적습니다. 측정한 비율에는 모델·런타임 식별자와 실행 횟수를 함께 기록하고, 통과율만이 아니라 목표 구간 폭을 밝힙니다.

유지되는 regression surface는 `../../assets/evals/hyper-documentation-cases.jsonl`의 `mode: docs` 케이스입니다. 완료 전에 변경된 모든 behavior를 이 fixture로 실행하거나 수동 점검합니다. Candidate를 통과시키려고 expected behavior를 바꾸지 말고, 새로 관측한 failure를 regression case로 추가합니다.

## 6. Readback 및 Bilingual Gate

갱신한 문서를 새 maintainer, context pressure 아래 실행하는 agent, 오래되었거나 근거 없거나 관심사가 섞였거나 미래 날짜이거나 authority가 충돌하는 claim을 찾는 reviewer 관점에서 읽습니다. validation path를 위해 무관한 파일을 검색해야 하면 실패입니다.

English/Korean mirror는 파일 존재만이 아니라 동등한 contract field, route condition, loop/runtime behavior, phase order, risk depth, gate, 대표 behavioral case를 점검합니다.

`../../assets/evals/hyper-documentation-cases.jsonl`에서 `mode: docs`인 `en` 케이스와 `ko` 케이스를 scenario type, expected route, required/forbidden behavior, trace, gate 기준으로 비교합니다. ID와 prose는 지역화할 수 있지만 behavioral coverage는 사라지면 안 됩니다.

## 7. Reviewer Quick Gate

다음 중 하나라도 참이면 문서를 fail 또는 block합니다.

- canonical docs가 고정 모델명 또는 runtime-only syntax를 universal rule처럼 제시함
- provider-sensitive/current claim에 적절한 evidence, provenance, non-future date가 없음
- 판이 있는 표준을 판 없이 인용하거나, 산출물을 가리키기만 하는 페이지에 주장을 얹음
- 비결정적 주장을 한 번의 실행으로 보고하거나, 일치율을 측정한 적 없이 결과를 결정하는 모델 판정자를 보정된 것으로 제시함
- retrieved content, tool output, subagent output을 instruction authority처럼 취급하거나, 그것을 지시인 양 문서에 인용함
- 필수 capability가 요청 범위를 조용히 줄이거나 consequential effect에 authority/gate가 없음
- loop가 unbounded이거나 self-grading만 하거나 baseline을 바꾸거나 failed-guard result를 유지함
- harness docs가 범위 내 scenario/oracle/runner/judge/trace/gate coverage를 빠뜨림
- English/Korean mirror가 호환되지 않는 behavioral contract를 드러냄

## Sources

> 확인 2026-11-03. 저장소 지시 기준과 대조했고, 이 파일을 위해 외부 URL을 열지는 않았습니다.

| 주장 | 출처 |
|---|---|
| 위험 깊이 척도, 완료 계약, 리뷰어 게이트 | `instructions/validation/index.md` |
| 실행 결과 보고, `pass@k`와 `pass^k`, 평가기 무결성, 판정자 보정 | `instructions/validation/references/evaluation-design.md` |
| 이 파일이 적용하는 판정 규칙과 증거 규율 | `instructions/harness-engineering/HARNESS_ENGINEERING.md` |
| 이 파일이 지목하는 회귀 fixture와 EN/KO 행동 비교 | `../../assets/evals/hyper-documentation-cases.jsonl`, `mode: docs` 케이스 (이 패키지) |
