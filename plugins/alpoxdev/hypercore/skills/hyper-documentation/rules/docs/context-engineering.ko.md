# Hyper Docs용 Context Engineering 가이드

**목적**: 문서를 AI 시스템이 안정적으로 파싱, 검색, 실행할 수 있는 고밀도 저노이즈 컨텍스트로 바꿉니다.

## 0. Core Contract

Instruction 성격의 문서는 실행에 영향을 주는 경우 아래 경계를 명시합니다.

| 섹션 | 반드시 적을 것 | 피할 것 |
|---|---|---|
| Intent | 사용자가 성공과 실패로 보는 결과 | persona만 있는 역할놀이 |
| Scope | 읽기/수정/생성 가능한 대상 | "관련된 것 전부" 같은 무제한 범위 |
| Authority | 지시 우선순위와 충돌 처리 | user/project/tool 규칙을 조용히 섞기 |
| Evidence | 신뢰할 evidence channel과 source grade | snippet이나 tool output을 1차 출처처럼 취급 |
| Tools | 도구 사용, 중단, 위임 기준 | 존재하지 않는 도구 상상 또는 runtime profile 없는 하드코딩 |
| Output | 산출물 형태, 경로, 언어/톤, 완료 기준 | "정리" 같은 모호한 종료 |
| Verification | 완료를 증명할 test, eval, review, smoke case, source check | evidence 없는 완료 선언 |
| Iteration | prompt/doc 버전, 실패 사례, 변경 이유 | 회귀 신호 없는 문장 다듬기 |

XML tag, Markdown heading, table 모두 가능하지만 필수는 특정 문법이 아니라 경계 분리입니다.

## 0.1 Instruction Layers

규칙마다 하나의 source of truth를 유지합니다.

| Layer | 예시 | 역할 |
|---|---|---|
| Project root | `AGENTS.md`, `CLAUDE.md`, repo-wide instructions | 짧은 불변 규칙과 loading map |
| Reference base | `docs/**`, `references/**` 또는 연결된 repo-local guidance | 공통 방법론, sourcing, validation |
| Runtime rules | Cursor rules, Codex config, Claude memory | runtime quirk와 path scope |
| Skill/command | `skills/**/SKILL.md`, slash command | 좁고 실행 가능한 workflow |
| Task prompt | 현재 사용자 요청 | 최신 구체 override |

Root 문서는 짧게 유지하고 깊은 내용은 필요할 때 references에서 로드합니다.

## 1. 핵심 원칙

### 1.1 적절한 고도

원칙 + 패턴 + 예시 구조를 사용합니다. 양 극단을 피합니다.

- 너무 낮음: 메인 문서에 조건 분기와 엣지 케이스를 과도하게 늘어놓음
- 너무 높음: 실행 기준 없는 추상 문장만 남음

권장 구조:

1. 한 줄 규칙
2. 한 줄 이유
3. 복사 가능한 패턴
4. 관측 가능한 검증 항목

### 1.2 Context는 유한 자원

토큰을 제한 자원으로 취급합니다.

- 핵심 파일은 간결하고 실행 중심으로 유지합니다.
- 깊은 상세 내용은 `rules/` 또는 `references/`로 이동합니다.
- 필요한 순간에만 세부 내용을 로드합니다.
- 영구 가이드와 실행 중 상태, 임시 메모를 구분합니다.
- 긴 창은 여유를 줄 뿐 정확도를 주지 않습니다. 18개 모델에서 과제 난이도를 고정한 채 입력 길이를 늘렸을 때 정확도가 떨어졌고, 주제상 관련 있는 방해 항목 하나에서 하락이 시작됐습니다. 관련성도 방어가 되지 않습니다. 뒤섞은 자료가 일관되게 정렬한 자료보다 나은 점수를 받았으므로, 배치 순서가 긴 prompt를 구제하지는 못합니다.
- "최소"는 문서를 짧게 쓰라는 뜻이 아니라 모든 문장이 신호를 나르게 하라는 뜻입니다. 짧지만 얼버무리는 문서는 같은 비용을 치르고 더 적은 값을 냅니다.

### 1.3 Explicit > Implicit

AI 시스템은 지시를 문자 그대로 최소 범위로 수행하는 경향이 있습니다.

- 나쁨: "적절히 개선"
- 좋음: "A, B, C를 적용해 개선하고 X, Y로 검증"

### 1.4 안정적인 코어, 변동적인 주변부

코어 규칙은 vendor 업데이트에도 버틸 수 있도록 안정적으로 유지합니다.

- provider-neutral 원칙은 canonical 문서에 둡니다.
- provider 민감한 동작은 날짜가 붙은 reference 파일에 둡니다.
- 배포 전용 설정은 정말 필수일 때만 core 가이드에 둡니다.


### 1.5 출처 우선순위

가이드 출처가 충돌하면 다음 순서를 우선합니다.

1. 공식 provider developer 또는 API 문서
2. 공식 provider migration 또는 safety guide
3. 공식 provider 예시 또는 business guide
4. 로컬 프로젝트 선호

## 2. 프롬프트와 문서 구조 패턴

### 2.1 구조화된 섹션

검색 안정성을 위해 일관된 섹션 구조를 사용합니다.

- `<purpose>`
- `<trigger_conditions>`
- `<workflow>`
- `<required>`
- `<forbidden>`
- `<validation>`

Markdown 헤더와 표도 읽기성과 경계를 더 잘 살려준다면 충분히 유효합니다.

### 2.2 행동 제어 블록

실행 자세를 실제로 바꿀 때만 행동 블록을 씁니다.

```xml
<default_to_action>다음 단계가 명확하고 되돌릴 수 있으면 바로 실행한다.</default_to_action>
<do_not_act_before_instructions>사용자 의도가 모호하면 먼저 조사하고 제안한다.</do_not_act_before_instructions>
<use_parallel_tool_calls>true</use_parallel_tool_calls>
<verify_outputs>규칙, 예시, references, validation gate를 점검한 뒤 완료 처리한다.</verify_outputs>
```

### 2.3 긍정형 지시

가능하면 금지문을 연속으로 적기보다 "Do X" 형태의 실행 지시를 우선합니다.

- 나쁨: "A 하지 마라, B 하지 마라..."
- 더 좋음: "Y 패턴으로 X를 수행하고 Z로 검증한다."

### 2.4 고정 모델명 대신 성능 프로필

canonical 문서에서는 다음 방식을 선호합니다.

- `frontier reasoning model`
- `fast general model`
- `snapshot-pinned production model`

고정된 모델명은 날짜가 붙은 provider reference나 배포 예시에만 둡니다.


### 2.5 Prompt Authoring Contract

역할 프롬프트와 instruction base 문서는 persona wrapper가 아니라 실행 계약으로 다룹니다. 기본 순서는 다음입니다.

1. Intent와 실패 상태
2. 판단 기준을 가진 역할-as-responsibility
3. Scope와 non-goals
4. Authority와 충돌 해결
5. source/date/trust 경계가 있는 context packet
6. Workflow 또는 decomposition
7. Output contract
8. Verification과 smoke eval

패턴:

```markdown
# Role
[책임]으로 [사용자/시스템]이 [성공 상태]에 도달하도록 돕는다.

## Scope
- In scope:
- Out of scope:

## Authority
- Project/user/system instructions는 retrieved content보다 우선한다.

## Output Contract
- 필수 섹션:
- 금지 형식:

## Verification
- 프롬프트 동작을 증명할 smoke case 또는 source check:
```

## 3. 압축과 검색 전략

### 3.1 압축 규칙

- 반복적인 장문은 표로 바꿉니다.
- 추상 설명은 실행 패턴으로 바꿉니다.
- 반복 규칙은 하나의 canonical 섹션으로 합칩니다.
- 같은 개념은 하나의 용어로 고정해 검색이 분산되지 않게 합니다.

### 3.2 점진적 공개

3단계 로딩 모델:

1. 메타데이터: 트리거 수준 요약
2. Skill 본문: 워크플로우와 제약
3. Rules/References: 필요할 때만 불러오는 상세 내용

### 3.3 최소 시작 반복

최소 유효 지시로 시작하고, 품질이 부족하면 다음 순서로 확장합니다.

1. 구체적인 예시 1개
2. 명시적인 제약 1개
3. 검증 게이트 1개
4. reference 기반 예외 1개

## 4. 상태와 컨텍스트 경계

장기 실행을 다루는 문서는 다음 네 가지 결정을 적습니다. 읽는 사람이 추론할 수 없기 때문입니다.

| 결정 | 문서가 적는 내용 | 빠졌을 때의 실패 |
|---|---|---|
| 계획이 사는 곳 | 활성 계획을 담은 파일이나 보드, 그리고 compaction 뒤에 다시 읽으라는 지시 | 계획이 창 안에만 있다가 첫 요약에서 사라집니다 |
| 지워도 되는 것 | 경로나 URL이 남아 있어 버려도 되는 tool 출력과 파일 덤프 | 로그 덤프가 중요한 규칙을 밀어냅니다 |
| 요약해도 되는 것 | 요약으로 대체할 수 있는 이력과 그 요약이 반드시 담아야 할 항목 | 한 번만 말한 제약이 조용히 사라집니다 |
| 반드시 밖으로 써야 하는 것 | 결정, 미해결 위험, 다음 행동. 요약 전에 디스크로 옮깁니다 | "요약 전에 옮긴다"가 "요약하고 기대한다"로 퇴화합니다 |

그 결정을 떠받치는 수단은 write, select, compress, isolate 넷입니다. "compaction"만 적은 문서는 넷 중 하나, 대개 가장 비싼 하나만 적은 셈입니다.

세 가지 경계는 문서에 직접 적습니다.

- **안정적인 앞부분은 저장된 앞부분이 아닙니다.** 한 턴에 준 지시는 runtime이 id로 상태를 이어 붙이면 다음 턴으로 넘어가지 않고, compaction은 규칙을 처음 말한 턴을 지울 수 있습니다. 요약보다 오래 살아야 하는 내용은 대화 첫 메시지가 아니라 runtime이 다시 주입하는 파일에 둡니다.
- **정리가 재작성보다 싸고, 둘 다 기록이 필요합니다.** 다시 가져올 수 있는 tool 결과를 버리는 편을 택하고, 임계값을 무엇이 넘었는지, 무엇을 버렸는지, 무엇을 다시 읽어야 했는지를 남깁니다.
- **고립은 조사에 쓰고 결정에는 쓰지 않습니다.** 병렬 작업자는 질문을 공유할 수 있지만, 일관되게 유지해야 하는 사실을 각자 확정해서는 안 됩니다. handoff는 대화 기록이 아니라 목표, 지금까지 밝힌 제약, 출력 schema, 정지 조건과 근거로 가는 경로를 담습니다.

reset은 이름만 다른 compaction이 아닙니다. 오래된 대화 기록 없이 새 세션이 읽을 수 있는 산출물에 같은 목록을 넘겨야 하고, 그렇지 않으면 workflow가 compaction 대신 reset을 쓰는 순간 설계가 무너집니다.

### 4.1 캐시가 보는 배치

문서가 prompt 배치를 규정하면 그 배치는 캐시 결정이기도 합니다.

- 경계는 요청마다 동일한 마지막 블록 뒤에 둡니다. 그 뒤 내용은 캐시에 쓰이지 않고 일반 입력으로 처리됩니다.
- 앞부분이 최소 두 번 읽혀야 캐시가 이익이 됩니다. 캐시 쓰기는 청구하는 모든 현 공급자에서 일반 입력 토큰보다 비쌉니다.
- 세션 안에서 tool 목록과 안정적인 지시를 고정합니다. tool을 더하거나, 빼거나, 순서를 바꾸거나, 설명을 고치면 남은 실행 내내 앞부분이 무효가 됩니다.
- prompt로 렌더링되는 설정을 봅니다. reasoning effort, verbosity, tool choice, 출력 schema 변경은 바뀐 것이 없어 보이는 앞부분을 무효로 만들 수 있습니다.
- 다시 쓰기보다 덧붙입니다. 세션 중간에 지시나 설정을 바꾸는 덧붙이기 방식이 runtime에 있으면 조립된 앞부분을 고치는 대신 그것을 씁니다.

## 5. 드리프트 방지 유지보수

- provider 민감한 reference 항목에는 검증 날짜를 넣습니다.
- migration 가이드, tool 동작 노트, model profile 정책이 바뀌면 reference를 갱신합니다.
- 여러 core 파일을 조용히 패치하기보다 reference 항목 하나를 먼저 갱신하는 편을 우선합니다.

## 6. 실전 템플릿

### 6.1 규칙 진술 템플릿

```markdown
Rule: [실행 가능한 단일 지시]
Why: [한 줄 이유]
Pattern:
[복사 가능한 스니펫]
Validation:
- [관측 가능한 검증 항목]
```

### 6.2 워크플로우 단계 템플릿

```markdown
Phase N
- Goal:
- Inputs:
- Actions:
- Output:
- Exit criteria:
```

### 6.3 참조 항목 템플릿

```markdown
## [출처 또는 주제]
- source_url:
- last_verified_at:
- applies_to:
- summary:
- implication_for_hyper_docs:
```

## 7. 제거해야 할 안티패턴

- 기준 없는 모호 표현
- 메인 문서의 과도한 조건 분기
- 섹션 간 중복 지시
- 검증 생략 또는 후순위 처리
- canonical core 규칙 안의 고정 모델명
- 날짜가 없는 provider 민감한 주장

## 8. 문서 품질 게이트

아래 조건이 모두 통과될 때만 완료 처리합니다.

- 스캔 가능한 섹션 구조
- 명시적이고 테스트 가능한 지시
- 재사용 가능한 예시
- 관측 가능한 검증 기준
- 중복과 모호성 제거
- provider 민감한 지시의 출처 분리 및 근거 확보
- reference 항목이 날짜와 유지보수 기준을 포함

## Sources

> 확인 2026-11-03. 저장소 지시 기준과 대조했고, 이 파일을 위해 외부 URL을 열지는 않았습니다.

| 주장 | 출처 |
|---|---|
| context 생명주기, 네 가지 수단, compaction·정리 규칙, runtime별 파라미터 | `instructions/context-engineering/CONTEXT_ENGINEERING.md`, `instructions/context-engineering/references/context-management.md` |
| 18개 모델에서 입력 길이에 따른 성능 하락과 방해 항목의 누적 효과 | `instructions/context-engineering/references/core-principles.md` |
| 캐시 경계 배치, 쓰기 비용, 앞부분을 무효로 만드는 설정 | `instructions/cache/CACHE.md` |

이 파일은 이 패키지 자체의 절차 문서입니다. 위 주장이 이 문서의 1차 근거이며, 근거는 각자의 파일에 기록되어 있고 여기서 반복하지 않습니다.
