# Skill-Maker를 위한 OpenAI 공식 참조

## Contents

- 갱신 정책
- Codex 에이전트 스킬
- Codex 스킬 발견과 배포
- 스킬 평가
- API 스킬
- AGENTS.md 지침
- 프롬프트 엔지니어링
- 평가 모범 사례
- 에이전트 구축의 안전
- Sources

## 갱신 정책

- last_verified_at: 2026-11-03
- refresh_when:
  - Codex 스킬 지침이 실질적으로 바뀔 때
  - Codex 스킬 발견 위치, 목록 예산, `agents/openai.yaml`이 바뀔 때
  - AGENTS.md·사용자 지침 지침이 실질적으로 바뀔 때
  - 스킬 평가 지침이 검증 규칙에 영향을 주는 방식으로 바뀔 때
  - 에이전트 안전 또는 도구 호출 지침이 스킬 안전 게이트에 영향을 주는 방식으로 바뀔 때
- supports_rules:
  - `rules/trigger-design.md`
  - `rules/skill-anatomy.md`
  - `rules/progressive-disclosure.md`
  - `rules/resource-placement.md`
  - `rules/context-and-harness-alignment.md`
  - `rules/validation-and-iteration.md`

## Codex 에이전트 스킬

- source_url: https://learn.chatgpt.com/docs/build-skills
- last_verified_at: 2026-11-03
- applies_to: 스킬 패키지 형태, `name`·`description`, 호출 방식, 자원, 스크립트, 점진적 공개, 목록 예산
- summary: 스킬은 지침과 자원, 선택적 스크립트를 묶은 패키지이며, `SKILL.md`에 `name`과
  `description`이 반드시 있어야 합니다. 명시적 호출은 ChatGPT에서 `@`, Codex CLI와 IDE 확장에서
  `/skills` 또는 `$`로 하며, 작업이 `description`과 맞으면 암시적 호출이 일어납니다. Codex에서
  최초 스킬 목록은 **모델 컨텍스트 창의 최대 2%, 컨텍스트 창을 알 수 없으면 8,000자**를 쓰며,
  `skills.max_context_tokens`로 **최대 10,000토큰**까지 다른 예산을 정할 수 있습니다. 스킬이 많으면
  Codex는 **먼저 설명을 줄이고**, 스킬 집합이 크면 **일부 스킬을 최초 목록에서 빼고 경고를
  냅니다**. 이 예산은 최초 목록에만 적용되며, 스킬이 선택되면 `SKILL.md` 전체는 그대로 읽힙니다.
  Codex는 스킬 변경을 자동으로 감지하고, 갱신이 보이지 않으면 재시작을 권합니다. 이 문서는
  결정적 동작이나 외부 도구가 필요하지 않으면 스크립트보다 지침을 선호합니다.
- implication_for_hyper_skill: 실패 양상은 설명이 잘리는 것만이 아니라 스킬이 아예 나타나지 않는
  것입니다. 그러므로 핵심 트리거가 설명 맨 앞에 와야 하고 설명은 짧아야 합니다. 저장소 실측값은
  `rules/trigger-design.md`의 Sources 절에 있습니다.

## Codex 스킬 발견과 배포

- source_url: https://learn.chatgpt.com/docs/build-skills
- last_verified_at: 2026-11-03
- applies_to: Codex가 스킬을 찾는 위치, 스킬 비활성화, UI 메타데이터, 호출 정책, 배포
- summary: Codex는 현재 작업 디렉터리에서 저장소 루트까지 올라가며 각 디렉터리의
  `.agents/skills`를 훑고, 여기에 `$HOME/.agents/skills`(사용자), `/etc/codex/skills`(관리자),
  Codex에 함께 포함된 시스템 스킬을 더합니다. **두 스킬이 같은 `name`을 가지면 Codex는 병합하지
  않고 둘 다 스킬 선택기에 나타날 수 있습니다.** Codex는 심볼릭 링크된 스킬 폴더를 그 대상까지
  따라갑니다. `~/.codex/config.toml`의 `[[skills.config]]` 항목은 삭제 없이 스킬을 비활성화하며,
  한 스킬에 항목이 여러 개 걸리면 마지막으로 일치한 항목이 이깁니다. 신뢰하는 프로젝트의
  `.codex/config.toml`에서 `[skills.bundled] enabled = false`를 두면 그 프로젝트에서 포함된 시스템
  스킬이 꺼집니다. `agents/openai.yaml`은 UI 메타데이터(`interface`), 호출 정책
  (`policy.allow_implicit_invocation`, 기본값 `true`이며 `false`이면 암시적 선택이 멈추고 명시적
  `$skill` 호출은 계속 동작), 도구 의존성(`dependencies.tools`)을 설정합니다. 한 환경을 넘어
  배포할 때 이 문서는 스킬을 **플러그인**으로 묶는 방법을 권합니다. `$skill-installer`는 큐레이션된
  스킬을 추가하고, `$skill-creator`는 새 스킬 생성을 안내합니다.
- implication_for_hyper_skill: "재사용 가능한 Codex 스킬 폴더"는 이야기의 절반입니다. 발견 위치를
  밝히고, `.agents/skills`가 다른 런타임과 공유된다는 점을 적고, 배포 경로로 플러그인을 다룹니다.
  `allow_implicit_invocation: false`는 스킬을 수동 전용으로 만드는 Codex 쪽 방법이며, 런타임에만
  적용되는 스위치입니다(SK-P-3).

## 스킬 평가

- source_url: https://developers.openai.com/blog/eval-skills
- last_verified_at: 2026-11-03
- applies_to: 트리거 테스트, 과정 점검, 출력 형식 점검, 결정적 채점기, 프롬프트 집합 크기
- summary: 스킬 품질은 작은 프롬프트 집합과 관찰 가능한 점검으로 네 축에서 평가합니다.
  **결과, 과정, 형식, 효율**("헤매지 않고 거기까지 갔는가")입니다. "10-20개 프롬프트의 작은 집합만
  으로도 회귀를 드러내고 개선을 일찍 확인하기에 충분하며", 명시적·암시적·맥락적·부정 통제 호출을
  아우릅니다. `codex exec`가 자동화 경로이며, 진행은 stderr로 흘리고 최종 결과만 stdout에 씁니다.
  글의 예시 스킬 경로는 예전 `.codex/skills` 위치를 쓰지만, build-skills 문서의
  `.agents/skills` 위치가 우선합니다.
- implication_for_hyper_skill: 네 축과 호출 방식 구분이 핵심이며, 케이스 개수는 검증된 최적값이
  아니라 시작 권장값으로 유지합니다.

## API 스킬

- source_url: https://developers.openai.com/api/docs/guides/tools-skills
- last_verified_at: 2026-11-03
- applies_to: OpenAI API로 업로드하는 스킬, 버전 관리, 묶음 한도, 보안 태세
- summary: 업로드한 스킬은 버전이 붙은 묶음(`skill_reference.version`, 예: `"2"` 또는 `"latest"`)을
  쓰며 공개 Agent Skills 표준과 호환됩니다. 한 묶음에는 `SKILL.md`가 정확히 하나 들어가고 파일은
  최대 500개이며, zip 50 MB, 압축 해제 파일 25 MB 한도가 있습니다. 스킬 지침은 시스템 프롬프트가
  아니라 사용자 프롬프트 입력입니다. 이 문서는 스킬이 "프롬프트 주입으로 인한 데이터 유출 같은
  보안 위험을 낳는다"고 경고하며, 스킬을 특권이 있는 코드이자 지침으로 다루고 공개 스킬 저장소를
  최종 사용자에게 노출하지 말라고 합니다.
- implication_for_hyper_skill: 스킬은 계획과 도구 사용에 실제 권한을 가진 코드와 지침의 결합이므로,
  산출물 감사와 버전 고정이 이 표면에도 적용됩니다.

## AGENTS.md 지침

- source_url: https://learn.chatgpt.com/docs/agent-configuration/agents-md
- last_verified_at: 2026-06-02
- recheck_status: 2026-09-20 또는 2026-11-03 점검에서 다시 읽지 않았습니다. 위 날짜는 마지막으로 실제 읽은 날짜입니다
- applies_to: 프로젝트 지침 발견, 범위, 우선순위, 로컬 지침 계층
- summary: 저장소 지침은 에이전트에 범위가 정해진 지침을 제공하며 프로젝트 안에서 작업할 때 고려해야 합니다.
- implication_for_hyper_skill: 로컬 `instructions/`와 프로젝트 규칙이 일반적인 제공자 예시보다 우선합니다.

## 프롬프트 엔지니어링

- source_url: https://developers.openai.com/api/docs/guides/prompt-engineering
- last_verified_at: 2026-06-02
- recheck_status: 2026-09-20 또는 2026-11-03 점검에서 다시 읽지 않았습니다. 위 날짜는 마지막으로 실제 읽은 날짜입니다
- applies_to: 명확한 지침, 예시, 구조화된 컨텍스트, 명시적 출력 형식
- summary: 명확한 지침과 예시, 명시적 형식이 따르기 쉬움을 높입니다.
- implication_for_hyper_skill: 핵심 스킬 지침은 명시적이고 예시로 뒷받침되며 계약 형태여야 합니다.

## 평가 모범 사례

- source_url: https://developers.openai.com/api/docs/guides/evaluation-best-practices
- last_verified_at: 2026-06-02
- recheck_status: 2026-09-20 또는 2026-11-03 점검에서 다시 읽지 않았습니다. 위 날짜는 마지막으로 실제 읽은 날짜입니다
- applies_to: AI 시스템 변동성, 평가 기반 반복
- summary: 모델 동작은 변하므로 프로덕션에 닿는 동작에는 직관이 아니라 평가가 필요합니다.
- implication_for_hyper_skill: 중요한 스킬 변경에는 최소한 작은 평가나 스모크 집합이 있어야 합니다.

## 에이전트 구축의 안전

- source_url: https://developers.openai.com/api/docs/guides/agent-builder-safety
- last_verified_at: 2026-06-02
- recheck_status: 2026-09-20 또는 2026-11-03 점검에서 다시 읽지 않았습니다. 위 날짜는 마지막으로 실제 읽은 날짜입니다
- applies_to: 프롬프트 주입, 도구 호출, MCP·도구 안전, 부작용 게이트
- summary: 에이전트 시스템에는 신뢰할 수 없는 입력, 도구, 권한, 부작용에 대한 보호 장치가 필요합니다.
- implication_for_hyper_skill: 네트워크, 자격 증명, 파괴적 동작, 프로덕션 부작용을 언급하는 스킬은 그 동작을 명시적으로 게이트해야 합니다.

## Sources

> 확인 2026-11-03. "예"로 표시한 행을 읽었습니다. `developers.openai.com/codex/skills`가 이제 `learn.chatgpt.com/docs/build-skills`를 정규 링크로 걸린 build-skills 문서를 제공하므로 정규 URL을 인용합니다.

| 주장 | 출처 | 2026-11-03 점검에서 읽음 |
|---|---|---|
| 스킬 패키지 형태, 필수 `name`·`description`, `@` / `/skills` / `$` 호출, 2%·8,000자 목록 예산, 최대 10,000토큰의 `skills.max_context_tokens`, 먼저 줄이고 이후 생략, 예산이 최초 목록에만 적용되는 범위 | <https://learn.chatgpt.com/docs/build-skills> | 예 |
| 발견 위치, 같은 `name` 비병합, 심볼릭 링크 스킬 폴더, 마지막 일치가 이기는 `[[skills.config]]`, `[skills.bundled]`, `allow_implicit_invocation`을 포함한 `agents/openai.yaml`, 배포 경로로서의 플러그인, `$skill-installer`, `$skill-creator` | <https://learn.chatgpt.com/docs/build-skills> | 예 |
| 네 가지 평가 축, 10-20개 프롬프트 시작 집합, 네 가지 호출 방식, 반복 실행을 위한 `codex exec` | <https://developers.openai.com/blog/eval-skills> | 예 |
| 버전이 붙은 API 묶음, 표준 호환, 묶음 한도, 사용자 프롬프트 우선, 프롬프트 주입·유출 경고 | <https://developers.openai.com/api/docs/guides/tools-skills> | 예 |
| AGENTS.md 발견과 우선순위 | <https://learn.chatgpt.com/docs/agent-configuration/agents-md> | 아니오 |
| 명확한 지침, 예시, 명시적 출력 형식 | <https://developers.openai.com/api/docs/guides/prompt-engineering> | 아니오 |
| 모델 변동성과 평가 기반 반복 | <https://developers.openai.com/api/docs/guides/evaluation-best-practices> | 아니오 |
| 프롬프트 주입, 도구 호출, 부작용 보호 장치 | <https://developers.openai.com/api/docs/guides/agent-builder-safety> | 아니오 |

### 증거 등급

`VENDOR`입니다. OpenAI가 자기 제품에 관해 한 서술입니다. 자사 로딩 역학(발견 위치, 크기 한도, 호출
정책)에 대한 벤더 서술은 그 제품에 관한 사실이고, 같은 벤더가 무엇이 좋은 스킬인지에 관해 한
서술은 휴리스틱입니다. 위 표의 네 행은 2026-06-02 점검에서 읽은 그대로 이월했으며, 날짜를 새로
찍지 않고 그 사실을 표시했습니다.
