# 스킬 구조

**Purpose**: 높은 품질의 스킬에 필요한 최소 형태와 책임 분담을 정의합니다.

## 1. 최소 구조

스킬은 `SKILL.md`로 시작하고, 발동성·신뢰성·재사용·검증을 개선할 때만 지원 파일을 더합니다.

권장 형태:

```text
skill-name/
├── SKILL.md
├── SKILL.ko.md
├── rules/
├── references/
├── scripts/
├── assets/
└── agents/
```

| 요소 | 요건 | 책임 |
|---|---|---|
| `SKILL.md` | 필수 | 메타데이터, 트리거, 핵심 실행 계약, 워크플로, 검증 |
| `SKILL.ko.md` | 저장소 관례 | 로컬·사용자 대면용 한국어 미러 |
| `rules/` | 조건부 | 재사용 정책, 판단 기준, 검증 체크리스트, 안티패턴 |
| `references/` | 조건부 | 공식 요약, 상세 지식, 스키마, 경계 사례, 긴 예시 |
| `scripts/` | 조건부 | 결정적 도우미, 검증기, 포매터, 데이터 변환 |
| `assets/` | 조건부 | 템플릿, 픽스처, 스키마, 정적 출력 자원 |
| `agents/` | 조건부 | 런타임이 소비할 때만 쓰는 런타임 메타데이터 - 예를 들어 Codex `agents/openai.yaml`(UI 텍스트, 호출 정책, 도구 의존성) |

## 2. Frontmatter

```yaml
---
name: skill-name
description: Use this skill when the user asks to ... Do not use for ...
compatibility: Optional runtime/dependency requirements.
---
```

규칙:

- `name`은 소문자 케밥 표기이며 **부모 디렉터리 이름과 일치해야 합니다**.
- `description`은 마케팅 문구가 아니라 트리거 안내이며, 스킬이 무엇을 하는지와 언제 쓰는지를 모두 적습니다.
- `compatibility`는 선택이며 실제 런타임, 네트워크, 패키지, 도구, 권한 제약을 적습니다.
- 도구 허용 목록 같은 구현별 필드는 선택이며 핵심 지침을 대체할 수 없습니다.

## 2a. 이식 가능한 핵심, 문서화된 확장

기반 문서는 이것을 `SK-P-3`(이식 가능한 핵심, 문서화된 확장)으로 서술합니다. 명세의 여섯 필드가
계약을 나르고, 런타임 전용 frontmatter는 자기 런타임 이름을 붙이며 부하를 지지 않아야 합니다.

실제로는 이렇습니다. 다른 런타임의 독자가 여섯 명세 필드와 본문만으로 스킬을 발동하고 실행할 수
있어야 합니다. 런타임 전용 필드를 쓸 때는 나타나는 자리에 그 런타임 이름을 적고, 그 필드가 강제하는
것(수동 호출, 도구 한도, 경로 한도)을 스킬 자체 계약에도 다시 적습니다.

| 런타임 | 확장 | 효과 |
|---|---|---|
| Claude Code | `when_to_use` | 목록에서 `description` 뒤에 붙으며, 1,536자 항목 자르기에 포함됩니다 |
| Claude Code | `argument-hint`, `arguments` | 자동 완성 힌트와 `$name` 이름 있는 치환 |
| Claude Code | `disable-model-invocation`, `user-invocable` | 각각 자동 호출이나 수동 호출을 끕니다 |
| Claude Code | `allowed-tools`, `disallowed-tools` | 호출한 턴에만 도구를 더하거나 뺍니다 |
| Claude Code | `model`, `effort`, `context`, `agent`, `background` | 모델·노력 재정의. `context: fork`는 스킬을 서브에이전트에서 실행합니다 |
| Claude Code | `hooks`, `paths`, `shell` | 호출 시 세션 훅, 경로 글롭 활성화 제한, 인라인 셸 선택 |
| Codex | `agents/openai.yaml`(frontmatter가 아니라 파일) | `interface` 텍스트와 아이콘, `policy.allow_implicit_invocation`, `dependencies.tools` |

필드 동작의 전체 내용은 `references/official/anthropic.md`와 `references/official/openai.md`에 있습니다.

## 3. Frontmatter 제약

아래 모든 제약은 명세에서 오며, 게이트가 있는 곳에서는 강제됩니다.

| 필드 | 필수 | 제약 |
|---|---|---|
| `name` | 예 | 1-64자. 소문자, 숫자, 하이픈만. 하이픈으로 시작하거나 끝날 수 없습니다. 연속 하이픈을 담을 수 없습니다. **부모 디렉터리 이름과 일치해야 합니다** |
| `description` | 예 | 1-1024자, 비어 있을 수 없습니다. 스킬이 무엇을 하는지와 언제 쓰는지를 적습니다 |
| `license` | 아니오 | 라이선스 이름 또는 함께 넣은 라이선스 파일 참조 |
| `compatibility` | 아니오 | **제공한다면 1-500자.** 환경 요구가 있을 때만 씁니다 |
| `metadata` | 아니오 | 명세가 정의하지 않은 속성을 위한 문자열 키-값 맵 |
| `allowed-tools` | 아니오 | 사전 승인된 도구의 공백 구분 문자열. **실험적** |

틀리기 쉬운 두 가지:

- `compatibility`의 하한 1은 명세가 **실제로** 말합니다. "Must be 1-500 characters if provided"입니다.
  이 필드는 양끝이 모두 제한된다고 봅니다.
- `name`이 부모 디렉터리와 일치하는 것은 **명세 요구**이지 문체 선호가 아닙니다. "가능하면 폴더와
  맞추는 것이 좋다"고 적은 규칙은 스스로 구현한다고 주장하는 표준보다 약합니다.

## 4. Claude 고유 제약

Claude는 명세 위에 제약을 더합니다. 이것을 어긴 스킬은 Claude로 이식되지 않습니다.

- `name`은 XML tags를 담을 수 없고 예약어 **"anthropic"**과 **"claude"**를 담을 수 없습니다.
- `description`은 XML tags를 담을 수 없습니다.
- 설명은 **third person**으로 씁니다. 이 필드는 시스템 프롬프트에 주입되므로 인칭이 흔들리는 설명은
  발견에 문제를 만듭니다.
- gerund 형태 이름(동사 + `-ing`)이 권장 관례입니다. 명사구와 동작 지향 이름도 허용되며 `helper`,
  `utils`, `tools` 같은 모호한 이름은 그렇지 않습니다.

함께 기억할 것: claude.ai 업로드와 Skills API 경로에서는 표준 여섯 필드만 허용되고 추가 필드는 조용히
무시되지 않고 **하드 오류**입니다. Claude Code 자신은 알 수 없는 필드를 오류 없이 무시하므로, 스킬이
로컬에서는 멀쩡해 보여도 업로드에서 실패할 수 있습니다. Claude Code 확장 필드에 의존하는 스킬은
이식 가능한 스킬이 아니라 Claude Code 스킬입니다(SK-P-3).

## 5. `allowed-tools`가 실제로 하는 일

양방향 모두 틀리기 쉬우므로 정확히 적습니다.

- **허용적 부여**입니다. Claude Code는 이것을 **스킬을 호출한 턴 동안 승인 없이 쓸 수 있는** 도구라고
  문서화하며, 다음 메시지에서 권한이 해제됩니다. 즉 실제 효과가 있습니다.
- **제한적 경계가 아닙니다.** 에이전트가 다른 도구를 쓰는 것을 막지 않고, 독립적인 권한·안전 게이트를
  대체하지 않습니다. 명세는 이 필드를 실험적으로 표시하며, 다른 런타임은 파싱은 하지만 강제하지
  않는다고 기록합니다.

따라서 정확한 결론은 "효과가 없다"도 "보안 통제다"도 아닙니다. 편의를 위한 부여이며, 부작용 게이팅은
스킬 자체의 계약에 적어야 합니다.

## 6. 첫 줄 규칙과 발견

**여는 `---`가 파일의 첫 줄일 때만 frontmatter를 읽습니다.** 그렇지 않으면 `---` 표시를 포함한 파일
전체가 스킬 내용으로 취급되며, 스킬은 발견 메타데이터를 조용히 잃고 이름으로는 여전히 로드될 수
있습니다.

이 규칙은 이미 두 저장소 게이트가 강제하므로 새 도구가 아니라 서술이 필요합니다.

- `validate-hyper-skill.sh`는 파일 시작에 `---`를 요구하는 앵커로 frontmatter를 찾으므로, 앞에 빈 줄이
  있으면 블록을 찾지 못하고 `FRONTMATTER_NAME`, `FRONTMATTER_DESCRIPTION`, `FRONTMATTER_TRIGGER`를
  보고합니다.
- `validate-skills-corpus.sh`는 `FRONTMATTER_MISSING`을 보고합니다.

설명이 애초에 보이는지를 결정하는 목록 예산은 `rules/trigger-design.md` §6에 한 번만 적습니다.

런타임에 따라 다른 발견 관련 사실 두 가지가 패키지를 배포하는 방식을 바꿉니다.

- Codex는 작업 디렉터리에서 저장소 루트까지의 모든 디렉터리에 있는 `.agents/skills`와 사용자, 관리자,
  번들 위치를 읽습니다. 같은 `name`을 가진 스킬 두 개는 **합쳐지지 않고** 둘 다 나타날 수 있습니다.
- Claude Code는 호출된 스킬의 본문을 이후 턴에도 컨텍스트에 유지하고 파일을 다시 읽지 않으므로,
  세션 도중에 한 편집은 새 세션에서 스킬을 다시 호출할 때까지 보이지 않습니다.

## 7. 최소 핵심 계약

비사소한 `SKILL.md`는 다음을 드러내야 합니다.

- 출력 언어 계약
- 목적
- 라우팅 규칙
- 지침 계약
- 활성화 예시
- 트리거 조건 또는 지원 대상
- 스킬 구조 또는 자원 모델
- 워크플로
- 지원 파일 읽기 순서 또는 안내 문구
- 필수·금지 동작
- 검증 체크리스트

지침 계약은 intent, trigger, scope, authority, evidence, tools, output, verification, stop 조건을
찾을 수 있게 해야 합니다.

## 8. `SKILL.md`에 들어갈 것

핵심 스킬에 남길 것:

- 스킬이 무엇을 하는지
- 언제 쓰고 언제 쓰지 않는지
- 어떤 출력이나 변환을 만들어야 하는지
- 상위 수준 워크플로
- 필수적인 권위·안전·정지 조건 경계
- 더 깊은 규칙이나 참조 안내

핵심 스킬을 전체 지식 기반으로 만들지 않습니다. 예산은 그 정본인 `rules/progressive-disclosure.md`에
있으며, 이 파일은 그것을 다시 적지 않습니다.

## 9. 언어와 미러 짝

정본 스킬 마크다운은 기본적으로 영어로 쓰되, 생성되는 사용자 대면 산출물은 기본을 한국어로 둡니다.

스킬 폴더 안에 마크다운 파일을 만들거나 실질적으로 수정할 때마다 한국어 형제 번역을 유지합니다.

- `SKILL.md`는 `SKILL.ko.md`와 짝입니다
- `rules/name.md`는 `rules/name.ko.md`와 짝입니다
- `references/path/name.md`는 `references/path/name.ko.md`와 짝입니다

국지화가 사소한 표현 변경을 요구하지 않는 한 제목, 절 순서, 링크, 예시를 짝 사이에서 구조적으로
맞춥니다. `## Sources` 제목은 두 파일 모두 영어로 유지합니다. 패리티 게이트가 그 제목을 그대로
대조하기 때문입니다. `###` 소제목과 필드 값은 자유롭게 번역합니다.

## 10. 품질 게이트

- [ ] `SKILL.md`가 모든 지원 파일을 읽지 않고도 스킬을 설명합니다.
- [ ] frontmatter가 발견과 트리거 선택을 뒷받침합니다.
- [ ] `name`이 부모 디렉터리 이름과 정확히 일치합니다.
- [ ] 계약 필드를 찾을 수 있습니다. intent, trigger, scope, authority, evidence, tools, output, verification, stop.
- [ ] 규칙이 정책을 담고 부풀린 참조 세부를 담지 않습니다.
- [ ] 참조가 세부를 담고 핵심 트리거 로직을 담지 않습니다.
- [ ] 스크립트·자산이 정당화되고 문서화된 경우에만 존재합니다.
- [ ] 선택 메타데이터가 의도적으로 있거나 의도적으로 없습니다.
- [ ] 런타임 전용 필드마다 그 런타임 이름이 붙어 있고, 그것 없이도 스킬이 올바르게 읽히고 발동합니다(SK-P-3).
- [ ] `allowed-tools`를 쓸 때 안전 경계로 제시하지 않습니다.

## Sources

> 확인 2026-11-03.

| 주장 | 출처 |
|---|---|
| frontmatter 필드 표와 그 모든 제약, 필수·선택 구분 | <https://agentskills.io/specification> |
| `name`의 XML 태그·예약어 제약, `description`의 XML 태그 제약, 3인칭 설명, 동명사 작명 관례 | <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices> |
| 표준 여섯 필드, Claude Code 확장 목록, 업로드·API 경로에서 비표준 필드의 하드 오류, 알 수 없는 필드를 무시하는 Claude Code, 첫 줄 규칙, 호출된 스킬의 컨텍스트 수명 | <https://code.claude.com/docs/en/skills> |
| `agents/openai.yaml`, `.agents/skills` 탐색, 같은 `name`을 합치지 않는 동작 | <https://learn.chatgpt.com/docs/build-skills> |
| 제한적 경계가 아니라 호출 턴에 대한 허용적 부여로서의 `allowed-tools` | <https://code.claude.com/docs/en/skills> |
| 파싱은 되지만 강제 가능한 권한 경계로 확립되지 않은 `allowed-tools` | <https://github.com/alpoxdev/hypercore/blob/01be78de5973eb75a616e5156058621a6fabbc97/instructions/cli/jcode/README.md> |
| `SK-P-3` | `instructions/skill/SKILL_AUTHORING.md` |
| 첫 줄 규칙을 이미 강제하는 게이트 | `skills/hyper-skill/scripts/validate-hyper-skill.sh` |

### 증거 등급

frontmatter 제약은 `PRIMARY`이며 명세가 말합니다. Claude 추가 사항, 확장 필드, 발견 관련 사실은
`VENDOR`이며 각 벤더가 자기 제품에 대해 한 서술입니다.
