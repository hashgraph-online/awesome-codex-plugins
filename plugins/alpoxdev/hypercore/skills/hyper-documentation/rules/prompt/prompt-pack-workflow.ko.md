# Prompt Pack Workflow

**목적**: prompt artifact의 초안, 리팩터, 버전 판단 순서를 정한다. **읽는 조건**: artifact를 만들거나 고칠 때.

## Draft

1. prompt를 재사용할 것인지 확인합니다.
2. operator, 대상 model 또는 agent, task class, side-effect 경계를 밝힙니다.
3. 문장을 다듬기 전에 prompt contract를 채웁니다.
4. 어느 규칙이 구속력 있고 어느 규칙이 advisory 기본값인지, untrusted material이 어디로 데이터로 들어오는지 선언합니다.
5. example을 넣기 전에 variables와 context packet 자리를 만듭니다.
6. 문체 지침보다 output schema를 먼저 정합니다. shape는 instruction, example, schema 가운데 하나로 표현하고 prefilled assistant turn으로 표현하지 않습니다.
7. 계약은 stable prefix에 두고 날짜, 현재 작업, turn마다 바뀌는 값은 마지막에 붙이는 tail로 보냅니다.
8. 최적화 주장보다 eval case를 먼저 넣고, case마다 실행 횟수와 집계 규칙을 함께 적습니다.

## Refactor

1. 사용자가 동작 변경을 요청하지 않았으면 지금의 관찰 가능한 동작을 보존합니다.
2. authority, scope, evidence, output 요구를 각각 다른 절로 나눕니다.
3. 중복되거나 장식적인 문구를 지웁니다.
4. 모호한 품질 표현을 success criteria와 verification check로 바꿉니다.
5. 변동 값을 stable prefix 밖 tail로 옮기고, 규칙 하나에 정본 위치 하나만 둡니다.
6. 무엇을 왜 바꿨는지 version note에 적습니다.

## Optimize

baseline case를 기록하고, 실패를 진단하고, 가장 작은 instruction surface를 고치고, 같은 judge로 같은 case를 다시 실행합니다. 안전, 출처, schema, guard 범위를 깨지 않으면서 목표 동작이 개선될 때만 변경을 남깁니다. 결과에는 model과 runtime version, 실행 횟수, grader version, 비용 변화를 함께 기록합니다. candidate는 case, judge, metric, guard를 고칠 수 없고, 점수가 오르는데 guard 범위가 줄면 변조 신호입니다.

## Version Note

version note에는 version, 무엇을 바꿨는지, 왜 바꿨는지, 사용한 실행 횟수와 집계 방식, grader version, 남은 위험, 그리고 prompt 길이나 tool surface를 건드렸다면 비용 변화를 적습니다.

## Sources

> 확인 2026-11-03. 저장소 instruction base를 기준으로 확인했습니다.

| Claim | Source | Checked |
|---|---|---|
| 작성 순서, prompt 개선 루프, version note | `instructions/context-engineering/references/prompt-authoring.md` | 2026-11-03 |
| stable prefix, 변동 tail, 캐시 경계 위치 | `instructions/cache/CACHE.md` | 2026-11-03 |
| baseline, 같은 runner로 재실행, guard 무결성 | `instructions/harness-engineering/HARNESS_ENGINEERING.md`, `instructions/autoresearch/references/core-loop.md` | 2026-11-03 |

이 문서는 외부 URL을 인용하지 않으며, 모든 규칙은 위 저장소 base를 다시 쓴 것입니다.
