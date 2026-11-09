# Requirements Writing

범위, 요구사항, 시나리오, 지표 절을 쓸 때 이 규칙을 사용한다. ID 형식, EARS 문장 형식, 시나리오 형태, 지표 집합, 문장 안 표시, 가정, 열린 질문, 바뀌면 안 되는 동작, 구현 메커니즘 금지를 소유한다.

## Contents

- Ids and priority
- EARS sentence forms
- Verification method
- Scenarios
- Metrics
- Inline markers
- Assumptions
- Open questions
- Must-not-change behavior
- Forbidden content
- Empty sections

## Ids and priority

| Id | Meaning | Format |
|---|---|---|
| `FR-###` | 기능 요구사항 | `FR-001`, 0으로 채운 세 자리, 문서 안에서 유일, 수정 뒤에도 번호를 다시 매기지 않는다 |
| `A-###` | 가정 | `A-001`, 그 가정에 기대는 문장에서 참조한다 |
| `Q-###` | 열린 질문 | `Q-001`, 그 질문이 막는 문장이나 절에서 참조한다 |
| `P0`/`P1`/`P2` | 요구사항 우선순위 | `P0` 없으면 목표가 실패, `P1` 첫 출시 범위, `P2` 이후 |
| `P1`/`P2`/`P3` | 스토리 우선순위 | 스토리 우선순위와 요구사항 우선순위는 다른 척도다. 스토리는 자기 요구사항 중 무엇이 `P0`인지 적는다 |

스토리에는 우선순위 이유("왜 지금이고, 밀리면 무엇이 깨지는가")와 독립 테스트("뒤 스토리 없이 이 스토리만 어떻게 증명하는가")를 붙인다.

## EARS sentence forms

모든 `FR-###`은 다음 다섯 형식 중 정확히 하나를 쓴다. 쓰기 쉬운 형식이 아니라 요구사항에 맞는 형식을 고른다.

| 형식 | 모양 | 쓰는 때 |
|---|---|---|
| 상시형 | `The <system> SHALL <response>.` | 항상 성립하는 규칙 |
| 사건형 | `WHEN <trigger>, the <system> SHALL <response>.` | 사건에 대한 응답 |
| 상태형 | `WHILE <state>, the <system> SHALL <response>.` | 상태가 유지되는 동안의 동작 |
| 원치 않는 사건형 | `IF <condition>, THEN the <system> SHALL <response>.` | 오류와 실패 경로 |
| 선택 기능형 | `WHERE <feature is included>, the <system> SHALL <response>.` | 일부 구성에서만 있는 동작 |

문장 하나에 응답 하나를 쓴다. "and"로 두 동작을 잇는 문장은 요구사항 둘로 나눈다. 시스템 이름은 제품이나 표면이고 컴포넌트, 모듈, 클래스가 아니다.

## Verification method

모든 `FR-###`에 `Verification:`으로 시작하는 한 줄을 붙이고, 관측 가능한 확인을 적는다. 측정, 검사, 테스트 시나리오, 시연이 해당한다. 무엇을 하고 무엇이 보이는지를 적는다.

- 좋음: `Verification: enter an expired code at sign-in; the screen shows the retry message and no session is created.`
- 검증 아님: `Verification: works correctly.` / `Verification: tested by QA.`

## Scenarios

Given/When/Then 시나리오는 요구사항이 아니라 스토리마다 쓴다. 스토리마다 정상 경로 하나와 실패·경계 하나를 쓴다. 시나리오는 자기가 실행하는 `FR-###` ID를 인용한다.

```text
Scenario: <name> (FR-003, FR-004)
Given <a concrete starting state with real values>
When <one action>
Then <one observable outcome>
```

`FR-###`를 인용하지 않는 시나리오는 스토리 설명이지 인수 시나리오가 아니다. `Then`을 관측할 수 없는 시나리오는 인수가 아니다.

## Metrics

목표마다 주 지표 하나, 필요하면 보조 지표, 문서마다 대응 지표 최소 하나를 둔다.

| 구분 | 필수 필드 |
|---|---|
| 주 지표 | 이름, 단위가 붙은 목표치, 측정 수단, 측정 시점 |
| 보조 지표 | 같은 네 필드, 주 지표를 뒷받침 |
| 대응 지표 | 나빠지면 안 되는 지표, 하한, 측정 수단, 측정 시점 |

- 목표치는 단위와 방향이 붙은 수, 또는 범위다. "더 좋게"는 목표치가 아니다.
- 측정 수단은 수치가 어디서 오는지 밝힌다. 기존 보고서, 이벤트 수, 크기가 정해진 수동 표본.
- 측정 시점은 창을 밝힌다. "출시 후 첫 14일", "첫 달 주 1회".
- 대응 지표는 변경이 망칠 수 있는 것을 지킨다. 지연, 문의 건수, 해지율, 배터리, 비용.

## Inline markers

표시는 두 가지이고, 끝에 모아 두지 않고 공백이 생긴 문장에 둔다.

| 표시 | 뜻 | 상한 |
|---|---|---|
| `[가정: <statement>]` | 그럴듯하지만 검증되지 않음. 문서는 그것으로 진행한다 | 고정 상한은 없지만 범위를 바꾸는 것은 `A-###` 항목을 갖는다 |
| `[확인 필요: <question>]` | 모름. 문장이 확정되려면 누군가 답해야 한다 | 본문 절의 문장 안 표시 3개 |

`[확인 필요: …]`가 상한을 넘으면 문서는 준비되지 않았다. 남는 것을 해소하거나, 소유자를 붙인 가정으로 바꾸거나, `status: draft`로 두고 보고한다. 출시 게이트 표의 행 결론으로 놓인 `[확인 필요: <질문>]`은 상한에서 세지 않고, 게이트 행이 하나라도 `[확인 필요]`이면 문서는 `status: draft`를 유지한다.

## Assumptions

범위를 바꾸는 모든 가정은 `A-###`로 적는다.

```text
- A-001: <the assumed statement>
  - Evidence grade: repo fact | convention default | guess
  - Basis: <path, quote, or the convention relied on>
  - If wrong: <the section, requirement, or scope that changes>
```

근거 등급은 정확히 셋이다. 저장소에서 읽은 사실, 증거 없이 택한 관례 기본값, 추측. P1 범위를 바꿀 추측은 가정이 아니라 막힘 표시를 붙여 열린 질문에 넣는다.

## Open questions

```text
- Q-001: <the question>
  - Answerer: <role or person>
  - Blocking: yes | no
  - History: Q: <question as asked> → A: <answer, or "unanswered">
```

`Blocking: yes`인 질문이 답을 받지 못하면 `status: draft`를 유지한다. 답이 오면 질문을 지우지 않고 이력 줄에 답을 덧붙인다. 질문을 닫으려고 답을 지어내지 않는다.

## Must-not-change behavior

변경 뒤에도 살아남아야 하는 동작을 `SHALL CONTINUE TO`로 적는다.

```text
FR-010 WHEN a saved draft is reopened, the editor SHALL CONTINUE TO restore the last cursor position.
```

변경이 기존 흐름, 데이터 계약, 권한을 건드리는 곳마다 쓴다. 그런 동작이 없는 문서는 절을 몰래 빼지 않고 한 줄로 그렇다고 적는다.

## Forbidden content

요구사항은 구현 메커니즘을 쓰지 않는다.

- 파일 경로, 모듈 이름, 함수 이름, 타입 이름, 클래스 이름
- 새로 고르는 라이브러리, 프레임워크, 데이터베이스, 서비스
- 이 문서가 새로 만든 스키마 이름, 테이블 이름, 컬럼 이름, 이벤트 이름
- 태스크 목록, 추정치, 인력 계획

이미 있는 외부 제약만 예외이고 제약으로 인용한다. 반드시 써야 하는 외부 API, 오프라인 필수, 스토어 규정, 법적 의무가 해당한다. 제약과 출처를 적고, 그것에서 내부 설계를 끌어내지 않는다. 스토어나 OS가 강제하는 스토어 규칙 값과 파일·형식 이름도 새로 지어낸 구현 수단이 아니라 외부 제약이다. 대상 API 레벨, 업로드 산출물 형식인 `.aab`, 프라이버시 매니페스트 파일 이름은 그것을 요구하는 규칙과 함께 인용한다.

모호한 품질 단어도 금지한다. 관측 가능한 뜻이 없는 `빠르게`, `쉽게`, `적절히`, `충분히`, `사용자 친화적`, `fast`, `easy`, `appropriate`, `robust`, `seamless`가 해당한다. 각각을 수, 상태, 확인으로 바꾼다.

## Empty sections

적용되지 않는 절은 지운다. 제목만 두고 내용을 비우지 않고, `N/A`, `TBD`, `-`도 쓰지 않는다. 지운 절은 문서에 보이지 않고, 비워 둔 절은 없는 내용이 있다고 주장한다.

## Sources

> 확인 2026-11-07.

| Claim | Source |
|---|---|
| MUST/SHALL과 독립 테스트를 붙인 번호 요구사항 | [spec-kit spec-template](https://raw.githubusercontent.com/github/spec-kit/main/templates/spec-template.md) - "Each user story/journey must be INDEPENDENTLY TESTABLE" |
| 기능 요구사항의 WHEN/SHALL 형식 | [Kiro feature specs](https://kiro.dev/docs/specs/feature-specs.md) - "WHEN [condition/event] THE SYSTEM SHALL [expected behavior]" |
| 상태형과 원치 않는 사건형을 포함한 EARS 다섯 형식 | [EARS](https://alistairmavin.com/ears/) |
| 바뀌면 안 되는 동작의 `SHALL CONTINUE TO` | [Kiro bugfix specs](https://kiro.dev/docs/specs/bugfix-specs.md) - "WHEN [condition] THEN the system SHALL CONTINUE TO [existing behavior]" |
| 공백 지점에 남기는 문장 안 표시 | [deanpeters prd-development](https://github.com/deanpeters/Product-Manager-Skills) - "Tag inline where the gap appears, not just at the end." |
| 확인 표시 상한 | [spec-kit specify](https://raw.githubusercontent.com/github/spec-kit/main/templates/commands/specify.md) - "Maximum 3 [NEEDS CLARIFICATION] markers total" |
| 본문 사실과 분리한 가정 | [phuryn create-prd](https://github.com/phuryn/pm-skills) - "Don't invent. What you don't know goes to 7.4 Assumptions and open questions, clearly marked, not into the body as fact." |
| 열린 질문에 답할 사람을 적음 | [anthropics write-spec](https://github.com/anthropics/knowledge-work-plugins) - "Tag each with who should answer (engineering, design, legal, data, stakeholder)" |
| 주 지표 옆의 대응 지표 | [TerminalSkills prd-writing](https://github.com/TerminalSkills/skills) - "Counter-metrics: [Metrics we don't want to hurt]" |
| 내부 메커니즘을 이름으로 쓰지 않음 | [ai-conductor prd](https://github.com/jstoup111/ai-conductor) - "It MUST NOT name the new internal mechanism by which this feature is built." |
| N/A 대신 적용되지 않는 절을 지움 | [spec-kit specify](https://raw.githubusercontent.com/github/spec-kit/main/templates/commands/specify.md) - "When a section doesn't apply, remove it entirely (don't leave as 'N/A')." |

### 근거 등급

`LOCAL` - ID 체계, 표시 상한, 가정 필드는 위 출처를 조합한 이 패키지의 설계다. EARS 형식은 EARS 문서에서 인용했고, `SHALL CONTINUE TO` 형식은 Kiro 버그픽스 문서에서 인용했다.
