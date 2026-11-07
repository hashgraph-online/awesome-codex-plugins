# Prompt Contract

**목적**: 오래 쓰는 prompt 계약의 필드 집합과 authority 구분을 정의한다. **읽는 조건**: 그 계약을 만들거나 크게 고칠 때.

지속적으로 사용할 prompt는 persona paragraph가 아니라 execution contract로 다룹니다.

## Required Contract Fields

| Field | Purpose |
|---|---|
| Intent | 실제 사용자 outcome, success state, failure state입니다. |
| Trigger | prompt를 사용할 때와 사용하지 않을 때입니다. |
| Scope | 허용 actions, owned artifacts, non-goals, side-effect limits입니다. |
| Authority | instruction priority와 conflict handling입니다. |
| Evidence | claims를 뒷받침하는 context, files, sources, evals, ledgers입니다. |
| Tools | allowed tools, required gates, forbidden side effects입니다. |
| Output | shape, language, required fields, forbidden formats, destination입니다. |
| Verification | tests, evals, source checks, readback checks, review gates입니다. |
| Stop condition | 관찰 가능한 completion criteria와 blocker conditions입니다. |

## Authority Shape

Authority에는 순서가 있고, 그 순서는 만들어 내는 것이 아니라 공개된 것입니다. 현재 공개된 spec은 Root, System, Developer, User, Guideline 순으로 두고, assistant 메시지와 tool 메시지, 인용문, 파일 첨부, 그 밖의 untrusted data에는 기본적으로 authority가 없다고 정합니다. prompt artifact는 이 위계를 다시 적지 않습니다. 자기 규칙이 이 위계 어디에 놓이는지를 밝힙니다.

- 어느 규칙이 매 실행마다 구속하는 developer 수준 instruction이고 어느 규칙이 사용자가 덮어쓸 수 있는 advisory 기본값인지 표시합니다. 구속하려는 규칙을 선호 표현으로 쓰지 않고, 하위 계층이 상위 계층을 조용히 덮어쓰지 않게 합니다.
- assistant 메시지와 tool 메시지, 인용문, 첨부, 검색한 페이지, 위임받은 요약은 authority가 없는 데이터로 다룹니다. prompt에는 그것을 따르라고 하지 않고 분석하라고 지시합니다.
- untrusted material은 YAML, JSON, XML처럼 표시가 분명한 block으로 전달합니다. 그 안의 인용문이나 tag가 instruction 자리에 끼어들지 못하게 하기 위해서입니다.

출처는 익숙하다는 이유로 신뢰를 얻지 않습니다. 저장소의 `AGENTS.md`가 내려받은 파일보다 우선하는 것은 경로와 검토 이력 때문이며, 읽는 사람이 알아봤기 때문이 아닙니다.

## Stable Prefix And Volatile Tail

재사용 prompt는 여러 번 읽히므로, 변하지 않는 부분을 앞에 두고 매 turn 바뀌는 부분을 뒤에 둡니다.

- 계약(identity, scope, authority, evidence 규칙, output schema, verification)이 stable prefix입니다. 날짜, 현재 작업, 대상 환경, turn마다 달라지는 입력은 그 뒤에 붙이는 tail에 둡니다.
- Stable prefix는 저장된 prefix가 아닙니다. 대화 상태를 이어 붙이면 runtime이 앞선 instruction을 다시 보내지 않습니다. OpenAI Responses API의 `instructions` parameter는 현재 응답에만 적용되고, 상태를 이어 붙이면 이전 turn에 사용한 instruction은 context에 남지 않습니다. 매 turn 살아 있어야 하는 내용은 runtime이 다시 주입하는 project instruction file에 두고, 첫 turn 메시지에 두지 않습니다.
- compaction은 tail이 기대는 앞선 맥락을 지울 수 있습니다. 대화에서 한 번 말한 제약은 요약에 남지 않을 수 있으므로, 요약보다 오래 살아야 하는 규칙은 다음 단계가 다시 읽는 file에 둡니다.
- 캐시 경계는 요청마다 동일한 마지막 block 뒤에 둡니다. write에 과금하는 provider라면 그 경계 뒤의 내용은 캐시에 쓰이지 않고 일반 입력 요율로 처리됩니다.

## Long-Context Layout

prompt가 문서, code, 여러 자료를 담으면 배치가 계약의 일부입니다.

1. 자료를 앞에 두고 질문, 지시, output format을 뒤에 둡니다. 두 주요 vendor가 이 순서를 문서화했고, Anthropic은 질문을 끝에 두면 "can improve response quality by up to 30 percent in tests"라고 보고합니다.
2. block마다 id와 source를 붙이고, 답할 때 사용한 id를 밝히게 합니다. 자료가 크면 근거를 짧게 먼저 추출하고 그 추출 결과로 최종 답을 만들게 합니다.
3. block 수를 줄입니다. 크고 표시가 분명한 문서 몇 개가 작은 조각 여럿보다 낫습니다. 조각마다 근거를 담지 않는 경계 문구가 붙기 때문입니다.
4. 배치를 선택의 대체물로 쓰지 않습니다. context 크기는 비용만이 아니라 품질 변수입니다. 과제 난이도를 고정해도 입력이 길어지면 정확도가 떨어지는 것이 여러 model 계열에서 측정됐습니다.
5. output shape는 instruction, example, schema 가운데 하나로 표현합니다. prefilled assistant turn을 심지 않습니다. 현재 Claude model은 마지막 assistant 메시지가 prefill이면 400 오류를 반환하므로, prefill에 의존하는 artifact는 model을 올리는 순간 깨집니다.

## Reasoning Visibility

hidden chain-of-thought, private reasoning transcripts, internal scratchpad 공개를 요구하지 않습니다. 대신 concise public rationale, assumptions, decision criteria, verification evidence를 요구합니다.

## Prompt Shape

prompt pack에는 identity, variables, context packet, examples, constraints, output schema, eval cases, version note가 있어야 합니다. downstream tools가 의존하면 정확한 schema keys를 사용합니다. 기대 동작을 온전히 설명하는 최소 정보 집합을 목표로 하며, 최소라는 말은 문서가 짧아야 한다는 뜻이 아니라 모든 문장이 신호를 담아야 한다는 뜻입니다.

## Sources

> 확인 2026-11-03. 저장소 instruction base를 기준으로 확인했습니다. 외부 vendor page 한 건은 같은 날 직접 열었습니다.

| Claim | Source | Checked |
|---|---|---|
| 계약 필드, 작성 순서, authority 수준, dynamic tail, long-context 배치, prefill 규칙 | `instructions/context-engineering/references/prompt-authoring.md` | 2026-11-03 |
| stable prefix, 캐시 경계, write와 read 비용 | `instructions/cache/CACHE.md` | 2026-11-03 |
| context 크기의 품질 영향과 최소 집합 크기 규칙 | `instructions/context-engineering/references/core-principles.md` | 2026-11-03 |
| 긴 문서를 앞에, 질문을 뒤에 두는 배치와 Claude 4.6 이후 prefilled response의 400 오류 | <https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices> | 2026-11-03 |

계약 규칙은 저장소 base를 다시 쓴 것입니다. vendor page는 배치 주장과 prefill 상태에 대해서만 직접 확인했으며, 두 항목은 생성되는 prompt에 담을 수 있는 내용을 바꿉니다.
