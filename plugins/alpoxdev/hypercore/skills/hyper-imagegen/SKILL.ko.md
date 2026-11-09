---
name: hyper-imagegen
description: "[Hyper] 사용자가 래스터 이미지 하나를 생성 또는 편집하거나 바로 사용할 이미지 프롬프트 하나를 받으려 할 때 사용합니다. 브리프 하나를 컴파일하고 런타임에 노출된 이미지 도구(ChatGPT에서는 모델 선택자가 노출되면 gpt-image-2.6-sunburst, 아니면 런타임 기본값)를 호출하며 프롬프트 전달에서 멈추지 않고, 검증한 종료 상태를 보고합니다. 이미지 분석, 재사용 프롬프트 팩, SVG·벡터나 코드로 그리는 그래픽, 일반 디자인 문서, 편집 가능한 UI/코드에는 사용하지 않습니다."
compatibility: 관찰된 이미지 생성 또는 편집 기능이 필요합니다. 런타임에 노출된 이미지 도구(ChatGPT 네이티브 도구, 에이전트나 MCP 이미지 도구)는 반환 산출물을 직접 전달할 수 있으며, 파일 시스템 저장에는 관찰된 안전 쓰기가 추가로 필요합니다. 파일리스 런타임에서도 독립 동작하며 동봉한 검증기에는 bash 3.2+와 jq 1.6+가 필요합니다. include는 패키지 상대 경로만 사용합니다.
---

@rules/capability-and-output.ko.md
@rules/prompt-compilation.ko.md
@references/runtime-capability-and-drift.ko.md
@references/prompt-crafting.ko.md
@references/visual-direction.ko.md

# Hyper Imagegen

> 요청 하나에 사실에 맞는 산출물 하나.

<output_language>

보고서는 기본적으로 한국어로 씁니다. 선택한 경로가 물을 수 있는 질문 하나와 종료 상태별 증거 블록도 한국어로 씁니다. 사용자의 정확한 렌더링 문구, 컴파일한 프롬프트, 파일 경로, 다이제스트, 모델명은 그대로 보존합니다. 사용자가 요청했을 때만 다른 언어를 씁니다.

</output_language>

<purpose>

한 번의 생성 또는 편집 요청을 사실에 맞는 전달 산출물로 바꾸고, 한 번의 프롬프트 전용 요청도 같은 방식으로 처리합니다.

</purpose>

<routing_rule>

요청한 산출물이 새 이미지 하나, 제공한 이미지의 편집 하나, 바로 사용할 이미지 프롬프트 하나 중 정확히 하나일 때 이 스킬을 사용합니다.

이미지 분석·비평, 재사용 프롬프트 팩과 템플릿, 일반 디자인 문서, 편집 가능한 UI와 코드에는 사용하지 않습니다. 코드로 만드는 편이 나은 에셋에도 사용하지 않습니다. 기존 SVG·벡터 아이콘 세트, 로고 체계, 일러스트 라이브러리를 확장하는 일, SVG·HTML/CSS·canvas에 어울리는 단순 도형·다이어그램·와이어프레임이 여기에 해당합니다. 프롬프트 저장을 거부하는 요청은 라우팅 문제가 아니라 `rules/capability-and-output.md`의 대체 정책이 처리합니다.

</routing_rule>

<instruction_contract>

| 항목 | 계약 |
|---|---|
| Intent | 요청한 이미지, 편집 또는 한 번의 바로 사용할 프롬프트를 충실히 전달합니다. |
| Trigger | 이미지 하나, 제공한 이미지의 편집 하나, 또는 이미지 프롬프트 하나를 요청하면서, 컴파일할 재료가 있거나 그것을 물을 경로가 허용될 때입니다. |
| Scope | 제공된 참조를 증거로 읽고 런타임 반환 산출물은 직접 전달하며, 파일은 `.hyper/imagegen/<주제>/` 아래에만 쓰거나 사용자가 지정한 프로젝트 경로에 새 파일로만 씁니다. 편집 원본을 수정하거나 기존 파일을 덮어쓰지 않습니다. |
| Authority | 사용자와 프로젝트 지시가 가져온 자료보다 우선합니다. 증거는 권한을 부여하지 않습니다. |
| Evidence | 형식화된 기능 관찰, `missing_fact`, `edit_source`, 권한 상태, 순서가 있는 호출 이력, 저장 경로/다이제스트, 검사 결과를 기록합니다. |
| Tools | 이미지 요청에는 런타임에 노출된 이미지 도구(ChatGPT 네이티브 도구, 에이전트나 MCP 이미지 도구)를 사용하고, 그 밖에는 관찰된 작업별 기능만 사용합니다. API 키 스크립트, SDK 실행기, 유료 엔드포인트로 스스로 바꾸지 않고, 그 선택지는 이름만 밝힌 뒤 사용자가 요청할 때만 씁니다. 네트워크, 자격 증명, 게시를 가정하지 않습니다. |
| Loop | 열린 반복은 없습니다. 이미지마다 변경 불가인 브리프 하나를 쓰고 최대 두 번만 호출하며, 첫 객관적 호출 실패 뒤에만 재시도합니다. 전달 뒤 사용자가 요청한 수정은 한 가지만 바꾸고 모든 불변 조건을 다시 적는 새 요청입니다. |
| Output | 요청마다 산출물 하나를 냅니다. ChatGPT 네이티브 반환 이미지 또는 `.hyper/imagegen/<주제>/` 아래에 저장한 이미지나 프롬프트 전용 `.txt` 파일이며 상대 경로, 다이제스트, 검사 상태를 포함합니다. |
| Verification | 시각·렌더링 문구·제약·시리즈 결과를 주장하기 전에 기능 관찰, 순서가 있는 시도 이력, 저장 경로/다이제스트, 반환 산출물 검사 결과를 확인합니다. |
| Stop condition | `generated_verified`, `generated_caveated`, `prompt_saved`, `awaiting_input`, `blocked`에서 끝내고 성공을 꾸미지 않은 증거와 한계를 보고합니다. |

</instruction_contract>

<activation_examples>

긍정 요청:

**한국어 생성:** “비 오는 밤, 한글 ‘밤 산책’을 선명하게 넣은 서점 포스터를 만들어 줘.” `밤 산책`을 정확히 한 번 보존하고 새 이미지 생성 완료를 관찰한 뒤, ChatGPT 네이티브 반환 산출물 또는 저장 및 적절한 검사 증거로 전달합니다.

**ChatGPT 생성:** “GPT로 여름 바다 포스터 이미지를 만들어 줘.” 완전한 프롬프트를 컴파일하고 ChatGPT에 노출된 네이티브 이미지 도구를 한 번 호출하여(모델 선택자가 노출되면 `gpt-image-2.6-sunburst`, 아니면 런타임 기본값) 반환 이미지를 전달하며, 프롬프트를 쓰거나 표시하는 데서 멈추지 않습니다.

**승인된 편집:** “Use my supplied product photo, keep the label unchanged, and replace only the background with a dawn market.” 제공된 편집 원본이 있으므로 그 경우에만 권한을 확인하고, 원본을 보존하며 관찰된 편집 기능으로 새 산출물을 저장합니다.

**대체 거부:** “Make an illustration, but do not save a prompt if image completion is unavailable.” `explicitly_rejected`를 기록합니다. 완료 기능이 사용 불가 또는 미상이거나 두 번 실패하면 프롬프트를 쓰지 않고 `blocked`로 끝납니다.

**참고 이미지 기반 생성:** “Make a summer café poster in the style of these two photos.” 두 사진은 편집 대상이 아니라 스타일 참고 자료입니다. `Image 1: style reference`, `Image 2: style reference`로 표시하고 새 이미지를 생성하며 편집 권한 질문은 하지 않습니다.

부정 요청:

- “이 사진 구도를 분석해 줘.” — 이미지 하나나 프롬프트 하나가 아니라 분석입니다.
- “우리 브랜드용 프롬프트 팩 20개 만들어 줘.” — 재사용 프롬프트 팩입니다.
- “우리 아이콘 SVG 세트에 맞춰 설정 아이콘 하나 더 그려 줘.” — 생성 비트맵이 아니라 코드로 만드는 벡터 에셋입니다.

경계 요청:

- “이미지는 만들지 말고 프롬프트만 파일로 저장해 줘.” — 다른 스킬이 아니라 이 스킬의 프롬프트 전용 경로입니다.
- “포스터를 만들고 그 결과를 평가해 줘.” — 생성은 여기서 하고, 결과 평가는 범위 밖입니다.

</activation_examples>

<trigger_conditions>

| 상황 | 경로 |
|---|---|
| 브리프에 필요한 사실이 모두 있음 | 변경 불가인 브리프 하나를 컴파일하고 그대로 진행 |
| `subject`, `reference`, `rendered_text`, `preserve_change` 중 하나가 없음 | 그 규칙의 한국어 질문 하나를 묻고 `awaiting_input`으로 끝내며 컴파일하지 않음 |
| 편집 원본이 제공됨 | 사용 전에 권한 질문 하나를 함 |
| ChatGPT가 네이티브 이미지 도구를 노출함 | 같은 실행에서 컴파일과 호출을 하고, 모델 선택자가 노출될 때만 `gpt-image-2.6-sunburst`를 지정 |
| 사용자가 프롬프트 대체를 거부함 | `explicitly_rejected`를 설정하고, 완료 기능이 없으면 `blocked`로 끝냄 |
| 네이티브 이미지 도구도 안전 쓰기도 없음 | 브리프를 응답 본문에 제시하고 `blocked`로 끝냄 |
| 제공한 이미지가 스타일, 구도, 주제 참고용일 뿐임 | 이미지마다 번호와 역할을 붙여 생성하며, 편집하는 것이 없으므로 권한 질문을 하지 않음 |
| 사용자가 프로젝트 경로를 지정함("public/hero.png") | 평소처럼 전달한 뒤 최종 이미지를 그 경로에 새 파일로 복사하며, 파일이 이미 있으면 `hero-v2.png` 같은 버전 이름을 씀 |

</trigger_conditions>

<skill_architecture>

- Core(`SKILL.md`): routing, 계약, 경로 선택 표, workflow, required/forbidden 동작.
- Rules: 해결 순서, 종료 상태, 시도 이력, 안전한 출력 처리는 `rules/capability-and-output.md`가, 브리프 구조·렌더링 문구·시리즈 불변 조건·편집 경계는 `rules/prompt-compilation.md`가 소유합니다.
- References: `references/prompt-crafting.md`(요청 카테고리, 형식 선택, 텍스트 렌더링), `references/visual-direction.md`(구성, 재질, 조명, 시리즈 일관성), `references/runtime-capability-and-drift.md`(기능 관찰과 제공자 드리프트).
- Assets: resolver와 behavior corpus인 `assets/evals/hyper-imagegen-cases.jsonl`.
- Scripts: `scripts/validate-hyper-imagegen.sh`가 corpus, resolver self-test, 패키지 문서 감사를 다시 실행합니다.

</skill_architecture>

<loop_policy>

열린 반복은 없습니다. 이미지마다 변경 불가인 브리프 하나, 최대 두 번의 호출, 첫 객관적 호출 실패 뒤에만 재시도합니다. 검색·저장 실패 뒤에는 다시 호출하지 않고, 경로가 질문 하나를 이미 했으면 두 번째 질문을 하지 않습니다. 호출 상한에 닿으면 `fallback_policy`를 다시 적용하고, 대체가 허용되지 않았거나 파일을 쓸 수 없을 때만 시도 이력과 함께 `blocked`로 보고합니다.

</loop_policy>

<language_and_translation_default>

사용자가 다른 언어를 요청하지 않은 한 보고서를 한국어로 씁니다. 렌더링 문구, 컴파일한 프롬프트, 경로, 다이제스트, 모델명은 산출된 그대로 두고, 이중 언어 보고서에서는 두 언어가 공유하는 증거를 동일하게 인용합니다.

</language_and_translation_default>

<reference_routing>

- 경로를 고르기 전과 보고서나 산출물을 쓰기 전에 [rules/capability-and-output.md](rules/capability-and-output.md)를 읽습니다.
- 브리프를 컴파일하기 전에 [rules/prompt-compilation.md](rules/prompt-compilation.md)를 읽습니다.
- 모든 이미지 작업 전과 런타임 변경 뒤에 [references/runtime-capability-and-drift.md](references/runtime-capability-and-drift.md)를 읽습니다.
- 카테고리 라우팅, 형식 선택, 텍스트 렌더 규칙은 [references/prompt-crafting.md](references/prompt-crafting.md)를 읽습니다.
- 시각 방향, 구성, 재질, 조명, 시리즈 일관성에 판단이 필요하면 [references/visual-direction.md](references/visual-direction.md)를 읽습니다.

</reference_routing>

<support_file_read_order>

1. 이 core 파일: 작업이 이미지 하나 또는 프롬프트 하나인지 확인하고 경로를 고릅니다.
2. `rules/capability-and-output.md`: 해결 순서, 종료 상태, 산출물 규칙.
3. `rules/prompt-compilation.md`: 브리프를 컴파일하기 전.
4. `references/runtime-capability-and-drift.md`: 첫 작업 전.
5. `references/prompt-crafting.md`: 고른 카테고리.
6. `references/visual-direction.md`: 방향 판단이 남아 있을 때.

</support_file_read_order>

<workflow>

1. **라우팅 후 확인과 컴파일.** 요청의 신호 단어를 읽어 `generate`와 `edit` 중 하나를 정하고(참고 자료만 있으면 `generate`), `references/prompt-crafting.ko.md`에서 생성 카테고리 하나나 편집 카테고리 하나를 고른 뒤 그 행만 로드합니다. 그 다음 컴파일 전에 `missing_fact`를 적용합니다. 실제로 필요한 `subject`, `reference`, `rendered_text`, `preserve_change`에만 규칙의 정확한 한국어 질문 하나를 묻고 선택적 스타일이나 모델 선택은 묻지 않습니다. 해결된 이미지마다 완전하고 변경 불가인 프롬프트 하나를 컴파일합니다. `rules/prompt-compilation.ko.md`의 구체성 정책(자세한 요청은 정리만 하고, 일반적인 요청은 허용된 세부만 보탬)을 따르고 정확한 렌더링 문구, 시리즈 불변 조건, 편집 경계를 보존합니다.
2. **관찰 후 결정.** 작업 선택 전에 런타임 참조를 읽고 기능 규칙을 적용합니다. 노출된 이미지 도구(ChatGPT 네이티브 도구, 에이전트나 MCP 이미지 도구)를 선언된 생성/편집 작업과 반환 경로의 직접 증거로 보고 컴파일한 프롬프트를 즉시 전달합니다. 제공된 편집 원본에 대해서만 권한을 묻습니다. 생성으로 편집을 대체하지 않습니다.
3. **제한된 전달.** 최대 두 번만 호출하고 첫 객관적 호출 실패 뒤에만 재시도합니다. 성공한 네이티브 반환은 직접 전달하며 저장소 쓰기를 사용할 수 없다는 이유로 막지 않습니다. 로컬 저장이 가능하고 요청되었으면 관찰된 안전 쓰기 기능으로 추가 저장하고 확장자 앞에 접미사를 붙입니다(`image-2.png`). 사용자가 지정한 프로젝트 경로에는 덮어쓰지 않고 새 사본을 씁니다. 네이티브 반환이 없는 파일 전달에는 기능 규칙의 저장 게이트를 그대로 적용합니다.
4. **보고 후 중단.** 기본 한국어 보고에는 종료 상태, 정확한 호출 횟수, 순서가 있는 시도 이력, 최종 컴파일 프롬프트, 네이티브 반환 산출물 증거 또는 저장된 상대 경로/다이제스트를 포함합니다. 검사가 가능하면 생성 종료 상태에 검사 상태도 포함합니다. 네이티브 이미지 반환에 성공하고도 프롬프트 전용 완료로 보고하지 않습니다.

</workflow>

<required>

| 범주 | 규칙 |
|------|------|
| Observed capability | 제품명이 아니라 관찰된 증거로 동작을 고릅니다. `unknown`은 보수적인 증거이며 권한이 아닙니다. |
| Exact text | 렌더링 문구, 시리즈 불변 조건, 제공된 편집 경계를 사용자가 말한 그대로 보존합니다. |
| Evidence record | 종료 상태가 요구하는 형식화된 기능 관찰, 순서가 있는 시도 이력, 저장 경로와 다이제스트, 검사 결과를 남깁니다. |
| One artifact | 요청마다 산출물 하나를 `.hyper/imagegen/<주제>/` 아래에만 쓰고(사용자가 지정한 경로에는 새 사본 추가), 편집 원본은 쓰기로 열지 않습니다. |
| Labeled inputs | 제공한 이미지마다 번호와 역할(편집 대상, 스타일 참고, 삽입 요소)을 붙입니다. 편집 대상이 있을 때만 요청이 편집입니다. |
| Honest terminal | `generated_verified`, `generated_caveated`, `prompt_saved`, `awaiting_input`, `blocked` 중 하나만 그 증거 필드와 함께 보고합니다. |
| One question | 선택한 경로가 정의한 질문 하나만 묻습니다. 선택적 스타일, 형식, 모델 선택은 묻지 않습니다. |

</required>

<forbidden>

| 범주 | 피할 것 |
|------|------|
| Prompt as image | 컴파일한 프롬프트, 미리보기, 계획을 전달된 이미지로 제시하는 행위 |
| Model improvisation | 런타임이 노출하지 않은 모델명을 말하거나, 모델명을 프롬프트 문자열이나 브리프에 넣는 행위 |
| Extra attempts | 세 번째 호출, 또는 검색·저장 실패 뒤의 재호출 |
| Unsafe write | `.hyper/imagegen/<주제>/`나 사용자가 지정한 경로 밖에 쓰거나, 검증하지 않은 링크를 따라가거나, 제공된 원본이나 기존 파일을 덮어쓰는 행위 |
| Silent escalation | 사용자가 요청하지 않았는데 API 키 스크립트, SDK 실행기, 유료 엔드포인트로 바꾸는 행위 |
| Code-native substitution | 기존 SVG·벡터·코드 에셋 세트를 확장해야 할 에셋을 비트맵으로 생성하거나, 래스터 이미지를 요청받고 SVG·HTML 자리표시자를 그리는 행위 |
| Unverified claim | 검사 증거 없이 시각·렌더링 문구·정확한 제약·시리즈 결과를 주장하는 행위 |
| Fabricated success | 이번 실행에서 돌아온 것이 없는데 이미지나 프롬프트 파일이 있다고 주장하는 행위 |

</forbidden>

<validation>

- [ ] 요청이 생성·편집·프롬프트 전용 중 하나로 라우팅되었고, 제공된 편집 원본은 사용 전에 권한을 확인했습니다.
- [ ] 필수 사실이 빠진 경우 한국어 질문 하나와 `awaiting_input`으로 끝냈고 컴파일·호출·저장을 하지 않았습니다.
- [ ] 컴파일한 브리프가 카테고리 행 하나에서 나왔고, 구체성 정책을 따랐으며, 입력 이미지마다 역할을 붙였고, 렌더링 문구, 시리즈 불변 조건, 편집 경계를 보존했습니다.
- [ ] 관찰된 기능으로 동작을 골랐고, ChatGPT 네이티브 반환은 저장소 쓰기를 요구하지 않고 전달했습니다.
- [ ] 호출 횟수와 순서가 있는 시도 이력이 실제 실행과 일치하고, 호출은 최대 두 번입니다.
- [ ] 종료 상태가 다섯 중 하나이며, 요구되는 저장 상대 경로와 다이제스트 또는 네이티브 반환 산출물 기록을 포함합니다.
- [ ] 검사 증거 없이 시각·렌더링 문구·제약·시리즈 결과를 주장하지 않았고, 미검증 항목을 caveat로 밝혔습니다.
- [ ] `bash skills/hyper-imagegen/scripts/validate-hyper-imagegen.sh --root skills/hyper-imagegen`가 통과하고, `assets/evals/hyper-imagegen-cases.jsonl`이 이 파일이 밝힌 경로를 계속 다룹니다.

</validation>

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| `image-maker`에서 이름을 바꾸고 공개된 이미지 스킬을 참고해 최적화하라는 요청 | user instruction, 2026-11-07 |
| 코드로 만들 에셋의 경계, 참고 자료만 있으면 생성으로 보는 생성·편집 구분, 번호를 붙인 입력 이미지 역할, 구체성 정책, 덮어쓰지 않는 `-v2` 경로 사본, API 키 경로로 스스로 바꾸지 않음 | OpenAI `imagegen` system skill, <https://github.com/openai/skills> (commit `e6afb0d`, file `.system/imagegen/SKILL.md`) |
| 해결 순서, 다섯 종료 상태, 두 번 호출 상한, 안전 쓰기 규칙 | `image-maker`에서 이어받은 이 패키지의 `rules/` |
