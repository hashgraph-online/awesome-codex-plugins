# Artifact Level

**목적**: 요청을 만족하는 가장 작은 prompt artifact level을 고른다. **읽는 조건**: artifact level을 고르거나 낮출 때.

## Level

| Level | Required shape |
|---|---|
| Standalone reusable prompt | Intent, inputs, authority, scope, output, verification, stop |
| Parameterized template | Standalone contract에 typed variable, default, missing-input behavior, example을 더한다 |
| Prompt pack | Identity, variable, context packet, example, constraint, output schema, eval case, 필요할 때 source 처리, version note |
| Eval-only artifact | Scenario, oracle, runner, judge, trace, gate, baseline, result contract |

## 선택 규칙

Reusable prompt나 eval fixture만 요청한 사용자에게 full prompt pack을 강제하지 않는다. Downstream parser가 결과를 소비하면 안정적인 machine-readable key를 쓰고, malformed required input은 추측하지 않고 거절한다.

## Sources

> 외부 출처 없음. 내용 확인 2026-11-03.

이 파일은 이 패키지가 이미 적용한 artifact level을 그대로 서술하며 외부 출처를 인용하지 않는다.
