# Evaluation And Iteration

**목적**: eval case, judge, 한도가 있는 optimization 회차를 정의한다. **읽는 조건**: 재사용 prompt를 만들거나, 채점하거나, 최적화할 때.

## Minimum Categories

JSONL prompt eval fixture를 만들 때 positive, negative, boundary, workflow, source, safety, regression, adversarial case를 포함합니다. 세트는 세는 것이 아니라 구성하는 것이며, 검증된 케이스 수라는 기준은 없습니다.

## Anti-Tautology Rule

eval은 그럴듯한 나쁜 prompt에서 실패할 수 있어야 합니다. file existence만 확인하거나, 동작과 무관한 keyword 존재를 확인하거나, 구현 text를 그대로 반복하는 check는 evidence로 세지 않습니다. 현재 구현을 보고 기대 출력을 적은 case는 동작이 아니라 구현을 측정합니다.

## Case Shape

Medium 이상 case는 다음을 정의합니다.

- 비어 있지 않은 `id`, `category`, `language`, `invocation`, `risk`, `prompt`
- 관찰 가능한 `expected.must`와 `expected.mustNot`
- runner와 judge identity
- `trace`의 required trajectory evidence
- `gate`의 binary acceptance rule

같은 intent를 English, Korean, mixed-language prompt로 다룹니다. Skill name만 보고 trigger test가 통과하지 않도록 explicit, implicit, contextual invocation을 포함합니다.

## Measurement

비결정적 동작은 한 번의 실행으로 판정하지 않습니다.

- 모든 case가 자기 `runs`와 집계 규칙을 밝힙니다. 둘 다 없는 case는 gate가 아닙니다.
- gate는 두 수치를 함께 밝힙니다. 허용할 동등성 여유(equivalence margin)와 실행 횟수가 사 주는 구간 폭입니다. 여유 안의 변화는 막지 않고, 구간이 좁다는 사실만으로 회귀를 무시할 수는 없습니다.
- `pass@k`(k회 중 한 번 이상 성공)와 함께 `pass^k`(k회 모두 성공)를 보고합니다. 신뢰성 주장이 되는 것은 두 번째뿐입니다. 실행당 성공률이 0.75라면 세 번 연속 성공은 약 42퍼센트에 그치므로, `pass@3`는 강해 보여도 `pass^3`는 이미 약합니다.
- 모든 결과에 model과 runtime version, case-set hash, grader version, benchmark version, 실행 횟수를 기록합니다. 이 값이 없는 결과는 나중에 비교할 수 없습니다.
- 실행하지 못한 run은 통과가 아니라 `SKIP`입니다. harness fault로 중단된 trial은 분모에서 제외하고 error trial로 보고하며, 실패로 평균에 넣지도 통과로 세지도 않습니다.
- 3~5개는 instruction만 바꿀 때의 출발점이고 8~15개는 일반적인 prompt 변경의 출발점이며, 어느 쪽도 검증된 하한이 아닙니다. 목표 구간 폭과 실행 횟수를 함께 밝힙니다.
- 비용은 품질과 같은 급의 축입니다. 정확도가 비슷한 두 prompt의 token과 비용은 자릿수만큼 벌어질 수 있으므로, 한 점을 얻는 데 열 배의 token을 쓴 변경은 두 수치를 함께 보고합니다.
- 한 자릿수 차이는 grader와 resource 구성이 동등하다는 것이 확인되기 전까지 결론이 아닙니다. 바뀌지 않은 출력을 다시 채점한 것만으로 공개 점수가 약 9점 움직인 사례가 있습니다.
- 포화된 case는 신호를 내지 않습니다. case가 천장에서 통과하면 regression suite로 옮기고 그 자리에 더 어려운 case를 넣습니다.

## Guard Integrity

- candidate는 metric 절차, case set, judge, 필수 guard, evidence log를 수정할 수 없습니다.
- guard 범위가 줄어드는데 metric이 오르면 진행이 아니라 변조 신호입니다. 실행되는 check가 줄거나 evaluator가 바뀌거나 metric 문구가 바뀌는 것이 모두 범위 축소입니다.
- artifact가 자기 harness를 수정할 수 있게 설계했다면 evaluator, guard, log는 수정 가능 집합 밖에 두고, 그 변경은 별도 변경으로 검토합니다.

## Judge Calibration

- rubric에 금지 사항과 차원별 반례를 붙여 밝힙니다.
- 근거가 모자랄 때 판단을 지어내지 않도록 judge에 `unknown` 판정을 줍니다.
- 작은 human 표본에 label을 달고, 같은 표본을 judge가 채점하게 한 뒤 alignment rate를 계산하고 불일치를 살핍니다. 비율이 정한 기준을 넘을 때까지 judge prompt를 고쳐 반복합니다. judge model, 그 version, 달성한 비율을 기록합니다.
- 문체를 잘 보는 judge가 정확성을 보는 judge는 아닙니다. 여러 judge를 평균내지 말고 차원을 나눠 채점합니다.
- 보정하지 않은 judge는 통과가 아니라 보정되지 않았다고 보고합니다.

## Iteration Loop

직접 deterministic check로 요청 artifact를 증명할 수 있으면 no loop를 사용합니다. Optimization은 최대 3회 candidate iteration만 실행합니다.

1. Baseline 출력과 점수를 실행 횟수, guard 집합과 함께 잡습니다.
2. Target metric 또는 rubric과 개선 방향을 선언합니다.
3. Case, runner, judge, 비회귀 guard를 고정하고 version을 기록합니다.
4. 실패를 instruction 부족, context 부족, schema 불일치, source 경계 문제, 안전 문제, model·runtime 불일치로 진단합니다.
5. 가장 작은 prompt surface를 고치고 같은 case를 다시 실행합니다.
6. Target이 개선되고 모든 guard가 선언한 범위 그대로 통과할 때만 candidate를 남기고, 아니면 버립니다.
7. 새 실패 유형마다 regression case를 추가하고 비용 변화와 남은 위험을 기록합니다.

## Stop

Target을 달성했거나, candidate 세 개를 평가했거나, guard 실패를 고치려면 범위를 넓혀야 하거나, 남은 실패에 context·capability·model·runtime·사용자 권한이 필요할 때 최적화를 멈춥니다. 개선을 주장하려고 baseline, case, runner, judge, guard를 바꾸지 않습니다. guard를 넓히거나 case set을 줄이면 개선이 아니라 비교가 baseline으로 되돌아간 것입니다.

## Sources

> 확인 2026-11-03. 저장소 instruction base를 기준으로 확인했습니다.

| Claim | Source | Checked |
|---|---|---|
| 판정 규칙, eval case 형태, `pass@k`와 함께 쓰는 `pass^k`, 결과 기록 항목 | `instructions/harness-engineering/HARNESS_ENGINEERING.md` | 2026-11-03 |
| 잡음 하한, 재채점 이동 폭, 비용 축, eval awareness | `instructions/harness-engineering/references/measurement.md` | 2026-11-03 |
| 채점자 위계, judge 보정, 부분 점수, 보고 규칙 | `instructions/validation/references/evaluation-design.md` | 2026-11-03 |
| candidate가 metric·guard·log를 수정할 수 없고 guard 축소가 정지 조건이라는 규칙 | `instructions/autoresearch/AUTORESEARCH.md`, `instructions/autoresearch/references/core-loop.md` | 2026-11-03 |
| with/without 기준선과 양쪽 모두 통과하는 단언 제거 규칙 | `instructions/skill/references/validation.md` | 2026-11-03 |

이 문서는 외부 URL을 인용하지 않으며, 모든 규칙은 위 저장소 base를 다시 쓴 것입니다.
