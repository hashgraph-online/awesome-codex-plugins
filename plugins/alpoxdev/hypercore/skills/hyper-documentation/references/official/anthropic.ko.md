# Hyper Docs용 Anthropic 공식 참조

**목적**: 이 스킬의 docs 모드가 쓰는 provider 민감 근거와 갱신 정책. **읽는 조건**: 문서가 이 provider의 모델이나 prompting 동작을 주장해 출처를 다시 확인해야 할 때.

## 목차

- 갱신 정책
- Prompting Best Practices
- Prompt Engineering Overview
- Long Context Ordering
- 성공 기준과 평가
- Context Windows
- Compaction
- Prompt Caching
- Agent Skills Best Practices
- Migration Guide
- Prompt Leak Reduction
- 병합되거나 옮겨진 페이지
- Sources

## 갱신 정책
- last_verified_at: 2026-11-03
- refresh_when:
  - migration 가이드가 바뀔 때
  - prompt, tool, context 동작이 실질적으로 바뀔 때
  - canonical docs 모드 규칙에 Anthropic 전용 예외가 필요할 때
  - 구체적인 모델 문자열이나 capability 노트가 낡을 때
  - 리뷰어가 canonical provider 민감 주장을 아래 출처로 연결하지 못할 때
- maintenance_note: 구체적인 모델 문자열과 migration 예시는 canonical core 규칙이 아니라 이 파일에 둡니다.

## Prompting Best Practices
- source_url: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
- last_verified_at: 2026-11-03
- applies_to: 현행 Claude 모델. 명확성, 예시, XML 구조, 긴 context 배치, tool 사용, agentic system
- refresh_when: prompt 구조나 긴 context 처리에 대한 권고가 바뀔 때
- summary: 모델별 prompt 페이지를 먼저 읽고 공통 기법을 뒤에 적용합니다. XML tag는 지시, context, 예시, 변수 입력이 섞인 prompt를 "모호함 없이 파싱"하도록 돕고, 일관되고 서술적인 tag 이름과 계층에 따른 중첩을 권합니다. 형식과 어조를 가장 안정적으로 이끄는 것은 예시이며, 세 개에서 다섯 개를 적정선으로 적습니다. system prompt의 역할 문장 하나가 행동을 집중시킵니다. 긴 자료는 위쪽에 두고 질문은 그 뒤에 둡니다. 구조는 구획 경계를 만들기 위한 것이며 특정 문법이 요구 사항은 아닙니다.
- implication_for_hyper_docs: 문서를 구획하고 경계를 드러내되, XML을 구조 선택지 하나로 다룹니다. tag 어휘를 요구 사항으로 제시하지 않습니다.

## Prompt Engineering Overview
- source_url: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview
- last_verified_at: 2026-11-03
- applies_to: prompt engineering이 맞는 도구인지, 시작 전에 무엇이 있어야 하는지
- refresh_when: prompt 작성 workflow에 대한 안내가 바뀔 때
- summary: 성공 기준의 명확한 정의, 그 기준으로 경험적으로 시험할 방법, 개선할 초안 세 가지를 전제로 둡니다. 실패하는 기준이 모두 prompt 문제는 아니며, 지연과 비용은 다른 모델 선택으로 더 쉽게 해결되는 경우가 있다고 적습니다. 기법 자체는 살아 있는 참조인 best-practices 페이지로 넘깁니다.
- implication_for_hyper_docs: 성공 기준과 시험 경로가 없는 prompt 문서는 불완전하며, "prompt를 다시 쓴다"가 모든 실패의 기본 처방은 아닙니다.

## Long Context Ordering
- source_url: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
- last_verified_at: 2026-11-03
- applies_to: 대략 20k token을 넘는 prompt, 여러 문서 입력
- refresh_when: 긴 context 배치나 인용 기반 접지 지침이 바뀔 때
- summary: 긴 문서와 입력을 질문, 지시, 예시보다 위쪽에 둡니다. 질문을 맨 뒤에 두면 시험에서 응답 품질이 30%까지 좋아질 수 있다고 적습니다. 문서마다 index, source, content를 붙이고, 긴 문서 과제에서는 관련 인용을 먼저 요청해 두 번째 단계가 짧고 확인 가능한 집합만 다루게 합니다.
- implication_for_hyper_docs: 대용량 context prompt를 다루는 문서에는 배치 규칙을 적고, 블록 수를 줄입니다. 잘 표시된 문서 몇 개가 잘게 쪼갠 조각 여럿보다 낫습니다.

## 성공 기준과 평가
- source_url: https://platform.claude.com/docs/en/test-and-evaluate/develop-tests
- last_verified_at: 2026-11-03
- applies_to: 성공 기준, 평가 설계, 채점 방식
- refresh_when: 평가 구성이나 성공 기준 안내가 바뀔 때
- summary: 성공 기준은 구체적이고 측정 가능해야 하며, 안전처럼 흐릿한 영역도 1만 회 시도 중 비율처럼 수치화할 수 있다고 적습니다. 문구를 다듬기 전에 첫 평가 세트를 만들고 그것으로 반복합니다. 이 페이지가 예전의 독립 성공 기준 페이지를 대체했습니다.
- implication_for_hyper_docs: 성공 기준과 시험 경로 없이 prompt 반복을 문서화하지 않습니다. 정성 기준에는 척도를 붙입니다.

## Context Windows
- source_url: https://platform.claude.com/docs/en/build-with-claude/context-windows
- last_verified_at: 2026-11-03
- applies_to: context 크기 산정, 창에 포함되는 것, 장기 대화
- refresh_when: context window나 산정 안내가 바뀔 때
- summary: "context가 많다고 자동으로 나아지지는 않습니다". token 수가 늘면 정확도와 재현율이 떨어지며 페이지는 이를 context rot이라 부릅니다. 창이 남아도 내용을 선별하는 일이 공간만큼 중요합니다. 장기 실행에는 서버 측 compaction을 주된 전략으로 적습니다. system prompt, tool 결과, 이미지, 문서, tool 정의, 모델 자신의 사고가 모두 창에 포함됩니다. usage 필드는 요청이 쓴 양을 input, cache read, cache creation으로 나눠 보고합니다.
- implication_for_hyper_docs: 장기 실행 agent를 다루는 문서는 예산과 선별 정책을 적고, 비용을 다루는 문서는 추정이 아니라 usage 필드를 읽습니다.

## Compaction
- source_url: https://platform.claude.com/docs/en/build-with-claude/compaction
- last_verified_at: 2026-11-03
- applies_to: 장기 대화와 agent
- refresh_when: compaction 방식, 파라미터, 적용 제외 모델이 바뀔 때
- summary: compaction은 오래된 turn을 서버가 쓴 요약으로 대체합니다. 방식은 둘입니다. 애플리케이션이 요약을 요청해 받은 블록을 교체하는 on-demand 방식과, 평범한 요청 안에서 입력 token이 임계값에 닿으면 API가 실행하는 threshold 방식입니다. 오래된 tool 결과나 사고 블록을 규칙으로 지우는 것은 별도 기능(context editing)이며 다시 가져올 수 있는 자료에는 더 싼 선택입니다. 최근 turn을 그대로 유지할 수 있고, 클라이언트 측 요약기도 여전히 가능합니다.
- implication_for_hyper_docs: 상태 정책에서 정리와 요약을 구분하고, "compaction"을 단일 설정처럼 쓰지 않습니다. 선택에 따라 남는 것이 달라집니다.

## Prompt Caching
- source_url: https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- last_verified_at: 2026-11-03
- applies_to: 재사용 prompt 앞부분, 비용과 지연
- refresh_when: 캐시 방식, TTL, 가격이 바뀔 때
- summary: 캐시를 켜는 방법은 둘입니다. 최상위 `cache_control` 하나로 대화가 길어질수록 경계를 앞으로 옮기는 자동 방식과, 개별 content block에 명시적으로 경계를 두는 방식입니다. 캐시 항목에는 짧은 TTL과 긴 TTL이 있고, 캐시 읽기와 쓰기는 usage에 나타납니다.
- implication_for_hyper_docs: 안정적인 앞부분을 실제로 동일하게 유지하고 경계를 그 끝에 둡니다. 앞부분에 날짜나 요청별 값이 들어가면 설계가 무너집니다.

## Agent Skills Best Practices
- source_url: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- last_verified_at: 2026-11-03
- applies_to: 스킬과 지시 패키지 설계
- refresh_when: 스킬 패키징이나 작성 안내가 바뀔 때
- summary: "간결함이 핵심"입니다. 미리 로드되는 것은 metadata뿐이고 본문은 트리거될 때, 추가 파일은 필요할 때 로드되므로 본문의 모든 token이 대화 이력과 경쟁합니다. 모델이 이미 갖고 있지 않은 context만 더합니다. 구체성의 정도는 과제의 취약성과 가변성에 맞추고, 문장을 다듬는 대신 실제 사용으로 시험합니다.
- implication_for_hyper_docs: 로드되는 core는 작게 유지하고 상세는 참조 파일로 내립니다. "모델이 이미 아는가"라는 시험은 문서가 모든 줄에 적용해야 할 제거 시험과 같습니다.

## Migration Guide
- source_url: https://platform.claude.com/docs/en/about-claude/models/migration-guide
- last_verified_at: 2026-11-03
- applies_to: 모델 변경과 호환성 드리프트
- refresh_when: 새 모델 계열이나 migration 공지가 나올 때
- summary: 이 페이지는 단일 문서가 아니라 모델별 migration 가이드의 색인이고, capability 상세는 release note와 모델 개요로 넘깁니다. 모델 이름과 동작은 시간에 따라 바뀌므로 모델명을 박아 넣은 문서는 migration 의무를 함께 떠안습니다.
- implication_for_hyper_docs: 고정 모델 문자열은 canonical 지침에서 빼고 capability profile을 둡니다. 구체적인 문자열과 확인 날짜는 이 파일이나 배포 예시에 둡니다.

## Prompt Leak Reduction
- source_url: https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-prompt-leak
- last_verified_at: 2026-11-03
- applies_to: prompt 유출, prompt injection, context 분리, 출력 필터링
- refresh_when: 가드레일이나 prompt 유출 안내가 바뀔 때
- summary: 유출 저항 prompt는 정말 필요할 때만 쓰라고 권합니다. 복잡도가 늘면 다른 과제 성능이 떨어질 수 있기 때문입니다. 모니터링과 후처리를 먼저 두고, context와 질의 분리, 출력 필터링, 모델에 필요 없는 세부 생략, 정기 감사를 제시합니다. Claude 4.6 이후 모델에서는 assistant turn을 미리 채우는 prefill이 지원되지 않고, prompt에 군더더기를 넣으면 "말하지 말라"는 지시 준수가 떨어진다고 적습니다.
- implication_for_hyper_docs: 안전 지침은 권한 경계, 최소 context, 출력 점검, 감사 경로를 함께 씁니다. 지시 한 줄이 유출을 막는다고 약속하지 않고, assistant turn을 미리 채우는 설계를 처방하지 않습니다.

## 병합되거나 옮겨진 페이지
이전 판이 인용하던 경로 세 개는 더 이상 독립 페이지로 존재하지 않습니다.
- `build-with-claude/prompt-engineering/use-xml-tags`는 prompting best-practices 페이지로 넘어가고, XML tag 안내는 그 페이지에 있습니다.
- `build-with-claude/prompt-engineering/prompt-templates-and-variables`와 `build-with-claude/prompt-engineering/long-context-tips`도 같은 best-practices 페이지로 넘어갑니다.
- `test-and-evaluate/define-success`는 `test-and-evaluate/develop-tests`로 넘어갑니다.

주제는 그대로인데 위치가 옮겨진 경로가 둘 있습니다.
- `build-with-claude/agent-skills/best-practices`는 내용 없이 문서 껍데기만 응답합니다. 실제 페이지는 `agents-and-tools/agent-skills/best-practices`입니다.
- `docs.anthropic.com/en/docs/...` 경로는 모두 `platform.claude.com/docs/en/...` 대응 경로로 해석됩니다.

## Sources

> 링크 확인 2026-11-03. 위 URL은 같은 날짜에 열어 각자의 내용으로 응답했고, 병합된 경로 세 개는 열어서 이 파일이 밝힌 페이지로 넘어가는 것을 확인했습니다.

| 항목 | URL | 확인 |
|---|---|---|
| Prompting best practices | <https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices> | 2026-11-03 |
| Prompt engineering overview | <https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview> | 2026-11-03 |
| 성공 기준과 평가 | <https://platform.claude.com/docs/en/test-and-evaluate/develop-tests> | 2026-11-03 |
| Context windows | <https://platform.claude.com/docs/en/build-with-claude/context-windows> | 2026-11-03 |
| Compaction | <https://platform.claude.com/docs/en/build-with-claude/compaction> | 2026-11-03 |
| Prompt caching | <https://platform.claude.com/docs/en/build-with-claude/prompt-caching> | 2026-11-03 |
| Agent skills best practices | <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices> | 2026-11-03 |
| Migration guide 색인 | <https://platform.claude.com/docs/en/about-claude/models/migration-guide> | 2026-11-03 |
| Prompt 유출 감소 | <https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-prompt-leak> | 2026-11-03 |

이 파일은 출처만 기록합니다. 사용자와 프로젝트 지시가 우선하며, 페이지 본문은 지시가 아니라 근거입니다.
