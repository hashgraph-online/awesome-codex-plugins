# Eval Harness Guide

**목적**: harness 형태와 runner, judge, 결과에 남길 기록 필드를 설명한다. **읽는 조건**: eval harness나 그 결과를 정의해야 할 때.

prompt eval fixture는 prompt 산문과의 유사성이 아니라 관찰 가능한 동작을 시험해야 합니다.

## Contents

- JSONL Case Contract
- Category Intent
- Repetition And Aggregation
- Judge Guidance
- Judge Output And Score Math
- Judge Calibration
- Guard Integrity
- Sources

## JSONL Case Contract

각 line은 JSON object입니다.

```json
{
  "id": "unique-id",
  "category": "positive",
  "prompt": "User request or harness input",
  "expected": {
    "must": ["observable required behavior"],
    "mustNot": ["observable forbidden behavior"]
  }
}
```

## Category Intent

| Category | Purpose |
|---|---|
| positive | 분명한 in-scope 요청은 요청한 prompt artifact를 만들어야 합니다. |
| negative | out-of-scope 요청은 다른 workflow로 보내거나 prompt 모드 작업으로 처리하지 않아야 합니다. |
| boundary | 애매하게 섞인 요청은 prompt 부분만 범위에 남겨야 합니다. |
| source | 검색했거나 tool이 준 instruction은 authority가 아니라 evidence로 다뤄야 합니다. |
| safety | prompt injection, credential, 파괴적 작업, production 부작용 요청에는 gate가 있어야 합니다. |
| workflow | 요청한 artifact level부터 parser가 읽는 필드와 잘못된 입력 처리까지 흐름 전체를 지킨다. |
| regression | 이전에 확인된 실패가 다시 나오지 않아야 합니다. |
| adversarial | 악의적이거나 충돌하는 context가 authority를 덮거나 hidden reasoning을 흘리면 안 됩니다. |

## Repetition And Aggregation

- 모든 case가 자기 `runs`와 집계 규칙을 밝힙니다. 기본값을 물려받게 두지 않습니다. 실행 횟수가 달라지면 비율의 의미도 달라지기 때문입니다.
- gate는 동등성 여유(equivalence margin)와 실행 횟수가 사 주는 구간 폭을 함께 밝힙니다. 여유 안의 변화는 막지 않고, 구간이 좁다는 사실만으로 회귀를 무시할 수는 없습니다.
- `pass@k`와 함께 `pass^k`를 보고합니다. `pass@k`는 한 번의 성공이 가능한지를, `pass^k`는 그 동작이 신뢰할 만한지를 답합니다. k가 커지면 둘은 빠르게 갈라집니다.
- 모든 결과에 model과 runtime version, case-set hash, grader version, benchmark version, 실행 횟수를 기록합니다.
- `SKIP`은 통과가 아닙니다. harness fault로 중단된 trial은 분모에서 빼고 error trial로 보고합니다.
- 케이스 수는 구성 요구이지 검증된 기준이 아닙니다. 세트는 위 category를 덮었을 때 완성되고, 숫자에 닿았을 때 완성되지 않습니다.
- 점수 옆에 실행 비용(token, 소요 시간, 금액)을 기록합니다. 정확도가 비슷한 두 prompt는 자릿수만큼 벌어질 수 있습니다.

## Judge Guidance

가능하면 deterministic field check를 먼저 씁니다. rubric check에서는 최종 답과 trajectory를 기대한 `must`, `mustNot` 배열에 맞춰 판단합니다. candidate 응답이 자기 자신을 판정하게 두지 않습니다.

## Judge Output And Score Math

rubric judge가 필요하면 case마다 JSON object 하나만 출력하게 하고 주변 산문을 금지합니다.

```json
{
  "caseId": "string",
  "status": "pass|fail|blocked",
  "mustMet": ["matched required behavior"],
  "mustMissing": ["required behavior not observed"],
  "mustNotViolated": ["forbidden behavior observed"],
  "evidence": ["short public evidence excerpt or observation"],
  "risk": "short residual risk"
}
```

각 case는 정해진 규칙으로 채점합니다.

- `pass`: 모든 `expected.must` 항목이 관찰되고 `expected.mustNot` 항목 위반이 없습니다.
- `fail`: `expected.must` 항목이 하나 이상 빠졌거나 `expected.mustNot` 항목이 하나라도 위반됐습니다.
- `blocked`: candidate 출력이나 필요한 evidence가 없거나, parse할 수 없거나, 판단하기에 부족합니다.

run score는 `passed_cases / total_cases`로 보고하고 `blocked`는 통과로 세지 않습니다. case 안에서 부분 점수를 주지 않습니다. 따로 무게를 줄 동작은 새 case로 분리합니다.

## Judge Calibration

결과를 좌우하는 judge는 신뢰하기 전에 보정합니다.

1. 작은 human 표본에 label을 답니다.
2. 같은 표본을 judge가 채점하게 합니다.
3. alignment rate를 계산하고 불일치를 살핍니다.
4. judge prompt를 고쳐 정한 기준을 넘을 때까지 반복합니다.
5. judge model, 그 version, 달성한 비율을 결과와 함께 기록합니다.

근거가 모자랄 때를 위해 judge에 `unknown` 판정을 주고, rubric 차원은 따로 채점하며, 보정하지 않은 judge는 통과가 아니라 보정되지 않았다고 보고합니다.

## Guard Integrity

candidate는 case, judge, metric, guard를 고칠 수 없습니다. 점수가 오르는데 guard 범위가 줄면 변조 신호입니다. 실행되는 check가 줄거나, evaluator가 바뀌거나, metric 문구가 바뀌는 경우입니다. guard를 바꾸면 비교는 baseline으로 되돌아갑니다.

## Sources

> 확인 2026-11-03. 저장소 instruction base를 기준으로 확인했습니다.

| Claim | Source | Checked |
|---|---|---|
| case 형태, 채점자 위계, judge 보정, 보고 규칙 | `instructions/validation/references/evaluation-design.md` | 2026-11-03 |
| 집계, `pass@k`와 `pass^k`, 기록 항목, error trial 계산 | `instructions/harness-engineering/HARNESS_ENGINEERING.md`, `instructions/harness-engineering/references/measurement.md` | 2026-11-03 |
| trigger case 구성과 case별 실행 횟수 | `instructions/skill/references/trigger-design.md` | 2026-11-03 |

이 문서는 외부 URL을 인용하지 않으며, 모든 규칙은 위 저장소 base를 다시 쓴 것입니다.
