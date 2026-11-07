# Prompt Pack Schema

**목적**: parser가 읽는 pack 필드를 정의한다. **읽는 조건**: 완전한 pack이나 parser가 읽는 schema를 요청받았을 때.

재사용 가능한 prompt artifact에는 이 schema를 사용합니다. eval harness나 downstream script가 읽는 경우 key를 안정적으로 유지합니다.

```yaml
identity:
  name: ""
  role: ""
  responsibility: ""
intent:
  user_goal: ""
  success_criteria: []
  failure_criteria: []
trigger:
  use_when: []
  do_not_use_when: []
scope:
  in_scope: []
  out_of_scope: []
  side_effect_limits: []
authority:
  priority_order: []
  conflict_rule: ""
  binding_rules: []       # developer 수준: 매 실행마다 유효
  advisory_rules: []      # 사용자가 덮어쓸 수 있는 기본값
  untrusted_data_shaping: "yaml | json | xml | labeled-block"
evidence:
  required_sources: []
  source_ledger: ""
tools:
  allowed: []
  gated: []
variables:
  required: []
  optional: []
context_packet:
  documents: []
  material_order: "문서를 앞에, 질문과 output format을 뒤에"
  assumptions: []
  missing_information: []
  volatile_tail: []       # 날짜, 현재 작업, turn마다 바뀌는 값을 마지막에 붙임
examples:
  positive: []
  negative: []
constraints:
  style: []
  safety: []
  reasoning_visibility: "hidden chain-of-thought를 요구하지 않고 public rationale과 verification evidence를 요구합니다."
  output_shape: "instructions | example | schema"   # prefilled assistant turn은 쓰지 않습니다
output_schema:
  format: "markdown | json | yaml"
  fields: []
  forbidden: []
eval_cases:
  fixture: ""
  categories: [positive, negative, boundary, workflow, source, safety, regression, adversarial]
  runs: 0
  aggregation: ""
  grader_version: ""
version_note:
  version: ""
  changed: []
  rationale: ""
  remaining_risk: ""
```

## Required Sections

prompt pack에는 identity, variables, context packet, examples, constraints, output schema, eval cases, version note가 있어야 합니다. 값이 비어 있어야 한다면 이유를 함께 적습니다.

## Field Rules

- `authority.binding_rules`와 `authority.advisory_rules`를 나눠 두면 하위 계층이 상위 계층을 조용히 덮어쓰지 못합니다. advisory로 적은 규칙은 금지처럼 읽히면 안 됩니다.
- `context_packet.material_order`와 `context_packet.volatile_tail`이 stable prefix를 유지합니다. compaction을 넘겨 살아야 하는 내용은 이 block이 아니라 file에 둡니다.
- `constraints.output_shape`는 shape를 표현하는 방식을 밝힙니다. prefilled assistant turn은 선택지가 아닙니다. 현재 Claude model은 마지막 assistant 메시지가 prefill이면 400 오류를 반환합니다.
- `eval_cases.runs`와 `eval_cases.aggregation`은 case마다 정합니다. judge가 바뀌면 `eval_cases.grader_version`도 바뀌고, grader가 바뀌면 이전 점수와 비교할 수 없습니다.

`format`이 `json` 또는 `yaml`이면 정확한 key name과 type을 정의하고 malformed required input을 reject하며 output을 parse하는 schema eval을 포함합니다. Required field를 prose로 언급만 한 결과는 허용하지 않습니다.

## Sources

> 확인 2026-11-03. 저장소 instruction base를 기준으로 확인했습니다.

| Claim | Source | Checked |
|---|---|---|
| authority 수준과 untrusted data 처리 방식 | `instructions/context-engineering/references/prompt-authoring.md` | 2026-11-03 |
| stable prefix와 변동 tail | `instructions/cache/CACHE.md` | 2026-11-03 |
| case별 실행 횟수, 집계 방식, 기록에 남기는 grader version | `instructions/harness-engineering/HARNESS_ENGINEERING.md` | 2026-11-03 |
| 현재 Claude model의 prefilled response 거부 | <https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices> | 2026-11-03 |

그 밖의 외부 URL은 인용하지 않으며, schema 규칙은 위 저장소 base를 다시 쓴 것입니다.
