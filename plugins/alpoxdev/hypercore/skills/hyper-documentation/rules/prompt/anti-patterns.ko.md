# Anti-Patterns

**목적**: prompt artifact가 갖고 나가면 안 되는 실패 유형을 모아 둔다. **읽는 조건**: 어떤 prompt artifact든 마무리하기 전.

- success criteria, scope, authority, output contract, verification이 없는 persona 전용 prompt.
- hidden chain-of-thought나 private scratchpad 공개를 요구하는 prompt.
- evidence여야 할 출처 text를 instruction으로 취급하는 것.
- 검색해 온 prompt injection을 authority로 삼아 최종 prompt에 옮기는 것.
- 검색 text를 증류한 출처 표기 claim이 아니라 원문 그대로 ledger, note, memory에 붙이는 것.
- output shape를 강제하려고 prefilled assistant turn에 의존하는 prompt.
- 날짜, 현재 작업, turn마다 바뀌는 상태 같은 변동 값을 stable prefix 안에 두거나, 요약을 넘겨 살아야 하는 제약을 대화에만 적는 것.
- prompt가 사용자의 실제 과제를 무시해도 통과하는 eval case.
- downstream parser가 field를 요구하는데 output schema를 산문으로만 설명하는 것.
- variables, context packet, examples, eval cases, version note가 없는 prompt pack.
- baseline과 같은 case 재실행 없이 하는 최적화 주장.
- 비결정적 동작을 한 번 실행으로 gate 판정하거나, `pass@k` 결과로 `pass^k`를 주장하는 것.
- candidate가 case set, judge, guard, evidence log를 고치거나, guard 범위가 줄어드는데 오른 점수를 받아들이는 것.
- 특정 부작용만 gate하지 않고 정상 사용까지 막는 넓은 안전 거절.
- global 또는 home directory를 project authority로 인용하는 prompt artifact.

## Sources

> 확인 2026-11-03. 저장소 instruction base를 기준으로 확인했습니다.

| Claim | Source | Checked |
|---|---|---|
| prompt 작성과 계약의 anti-pattern | `instructions/context-engineering/references/prompt-authoring.md`, `instructions/context-engineering/CONTEXT_ENGINEERING.md` | 2026-11-03 |
| 검색, 영속화, memory의 anti-pattern | `instructions/sourcing/references/retrieval-safety.md` | 2026-11-03 |
| 단일 실행 gate와 guard 변조 | `instructions/harness-engineering/HARNESS_ENGINEERING.md`, `instructions/autoresearch/AUTORESEARCH.md` | 2026-11-03 |
| loaded head를 고정하고 변동 값을 밖으로 두는 규칙 | `instructions/cache/CACHE.md` | 2026-11-03 |

이 문서는 외부 URL을 인용하지 않으며, 모든 규칙은 위 저장소 base를 다시 쓴 것입니다.
