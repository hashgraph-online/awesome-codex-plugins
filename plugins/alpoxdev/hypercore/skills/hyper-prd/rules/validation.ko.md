# Validation

저장 전과 모든 `review`에서 이 규칙을 사용한다. 모드별 완료 증거, 저장 전 체크리스트, 막힘 질문 처리, 선택 단계인 맥락 없는 독자 테스트를 소유한다.

## 1. 모드별 완료 증거

| 모드 | 실행이 끝났다는 증거 | 증거가 아닌 것 |
|---|---|---|
| `create` | `.hyper/prd/<slug>/prd.md`에 저장되었고 저장 전 체크리스트 항목이 모두 통과 | 문서를 설명하는 대화 메시지 |
| `update` | 바뀐 절, 날짜와 바뀐 내용이 붙은 변경 이력 행, 모든 체크리스트 항목 통과 | 절을 고쳤다고 하면서 파일 전체를 다시 쓰는 것 |
| `review` | 체크리스트 항목별 통과·실패 표, 실패 항목과 그 위치를 명시 | 파일을 고치는 것, 표 없는 산문 판정 |

`review`는 절대 고치지 않는다. 검토에서 수정점이 나오면 그 수정점을 말하고 멈춘다. 적용은 `update`다.

## 2. 저장 전 체크리스트

의도가 아니라 저장된 문장 위에서 항목마다 확인한다.

| # | 확인 | 실패하는 때 |
|---|---|---|
| 1 | 모든 `FR-###`이 목표나 `P1`/`P2`/`P3` 스토리에 연결된다 | 요구사항이 아무것도 인용하지 않거나 비목표만 인용한다 |
| 2 | 모든 지표에 목표치, 측정 수단, 측정 시점이 있다 | 셋 중 하나가 없거나 목표치에 단위가 없다 |
| 3 | 비목표가 실제로 범위를 자른다 | 비목표가 목표를 다시 말하거나, 지워도 무엇을 만드는지가 바뀌지 않는다 |
| 4 | 모호어가 남지 않았다 | `빠르게`, `쉽게`, `적절히`, `충분히`, `사용자 친화적`, `fast`, `easy`, `appropriate`, `robust`, `seamless`가 요구사항으로 남아 있다 |
| 5 | 구현 메커니즘이 없다 | 기존 외부 제약 밖에서 파일 경로, 함수·타입 이름, 새로 고른 라이브러리, 새로 만든 스키마 이름이 나온다 |
| 6 | 모든 스토리에 `FR-###` ID를 인용하는 정상 경로와 실패·경계 시나리오가 있다 | 한쪽 경로가 없거나 시나리오가 요구사항을 인용하지 않는다 |
| 7 | 모든 `A-###`에 근거 등급과 결과가 있다 | 가정이 사실처럼 본문에 있거나 "틀렸을 때" 줄이 없다 |
| 8 | 출시 게이트 표 밖에서 `[확인 필요: …]`가 최대 3회다 | 본문 절에 네 번째 문장 안 표시가 있다 |
| 9 | 비어 있는 절이나 `N/A` 절이 없다 | 제목에 내용이 없거나 `N/A`/`TBD`라고 적혀 있다 |
| 10 | 핸드오프 블록이 완전하다 | 플랫폼, 규모, P1 범위, 남은 막힘 질문, 다음 단계 입력 중 하나가 빠진다 |
| 11 | 메타 블록에 상태, 플랫폼, 규모, 갱신일이 있다 | 필드 하나가 빠지거나, 플랫폼·규모 판정에 이유 한 줄이 없다 |
| 12 | 바뀌면 안 되는 동작이 적혀 있거나 없다고 명시했다 | 변경이 기존 흐름을 건드리는데 그 절이 없다 |
| 13 | 결정된 플랫폼마다 모든 `[M]`·`[M-조건]` 항목이 그 플랫폼의 출시 게이트 표에 결론과 함께 있다 | 결정된 플랫폼 체크리스트의 `[M]`이나 `[M-조건]` 항목에 행이 없거나, 행에 결론이 없다 |
| 14 | 기기 이름을 기준으로 한 중단점이 없다 | 중단점이 콘텐츠 폭(CSS 픽셀) 대신 `iPhone 375px`, `iPad`, `desktop 1440` 같은 기기 분류로 적혀 있다 |

8번은 본문 절의 문장 안 표시만 센다. 게이트 행의 결론으로 놓인 `[확인 필요: <질문>]`은 상한에서 제외하고, 게이트 행이 하나라도 `[확인 필요]`이면 문서는 `status: draft`를 유지한다. 13번은 행이 아니라 항목을 센다. 조건과 이유가 붙은 "비해당"으로 적힌 `[M-조건]` 항목도 통과하고, `[확인 필요: <질문>]`으로 적힌 `[M]` 항목도 문서가 `status: draft`를 유지하면 통과한다. 14번은 목표, 플랫폼 블록, 요구사항 어디에 적힌 폭에나 적용한다. 중단점은 콘텐츠 폭을 CSS 픽셀로 적고 무엇이 그 폭을 필요로 하는지 함께 쓴다. 예: `640px where the metric row wraps`. 기기 이름을 중단점에 쓰면 결함이다. 기기 목록은 바뀌지만 콘텐츠 폭은 바뀌지 않는다.

실패는 그 자리에서 고치고 실패한 항목만 다시 확인한다. 끝났다는 느낌을 위해 체크리스트 전체를 다시 돌리지 않는다.

## 3. 막힘 질문

- `Blocking: yes`이고 답이 없는 `Q-###`이 있으면 `status: draft`를 유지한다.
- `draft` 문서도 저장하고 보고한다. 숨기지 않고 완성으로 보고하지도 않는다.
- 완료 보고에 남은 막힘 질문과 답할 사람을 적는다.
- 체크리스트를 모두 통과해도 `draft`일 수 있다. 체크리스트는 문장을 재고, 상태는 범위 결정이 빠졌는지를 잰다.

## 4. 선택 단계: 맥락 없는 독자 테스트

하위 에이전트를 쓸 수 있고 사용자가 금지하지 않았을 때만 실행한다. 필수 단계가 아니며, 건너뛴 테스트는 통과가 아니라 건너뜀으로 적는다.

1. 다음 단계가 문서에서 답을 얻어야 할 예상 질문 다섯을 쓴다. 무엇을 만드는가, 누구를 위한가, 무엇이 범위 밖인가, 성공을 어떻게 재는가, 아직 어떤 결정이 열려 있는가.
2. 저장한 `prd.md`만 준 새 하위 에이전트에게 그 다섯 질문을 한다.
3. 문서가 뒷받침하는 답의 수를 센다. 문서 자체 텍스트로 답할 수 없는 질문은 읽는 사람이 아니라 그 절의 결함이다.
4. 결함을 문서에 반영하고 해당 체크리스트 항목을 다시 확인한다.

결과는 `reader test: passed <n>/5` 또는 `reader test: skipped (<reason>)`로 기록한다. 실행하지 않은 통과를 주장하지 않는다.

## 5. 검토 출력 형태

```text
| # | Check | Result | Location / note |
|---|---|---|---|
| 1 | FR maps to goal or story | pass | |
| 2 | Metric target and measurement | fail | Section 5, FR-007 has no target |
| 13 | Platform `[M]` items in the release gate table | fail | Android block, A9 has no row |
| 14 | Breakpoints named by content | fail | Section 9, web block says "iPhone 375px" |
```

체크리스트 항목마다 한 행, 체크리스트 순서대로. 표 뒤에 막힘 질문을 적는 한 줄과 파일을 고치지 않았다는 한 줄을 둔다.

## Sources

> 확인 2026-11-07.

| Claim | Source |
|---|---|
| 모든 스토리의 관문으로서 독립 테스트 가능성 | [spec-kit spec-template](https://raw.githubusercontent.com/github/spec-kit/main/templates/spec-template.md) - "Each user story/journey must be INDEPENDENTLY TESTABLE" |
| N/A 대신 적용되지 않는 절을 지움 | [spec-kit specify](https://raw.githubusercontent.com/github/spec-kit/main/templates/commands/specify.md) - "When a section doesn't apply, remove it entirely (don't leave as 'N/A')." |
| 준비도 관문으로서의 확인 표시 상한 | [spec-kit specify](https://raw.githubusercontent.com/github/spec-kit/main/templates/commands/specify.md) - "Maximum 3 [NEEDS CLARIFICATION] markers total" |
| 다른 독자보다 먼저 하는 맥락 없는 독자 테스트 | [anthropics doc-coauthoring](https://github.com/anthropics/skills) - "Test the doc with a fresh Claude (no context) to catch blind spots before others read it" |
| 본문 사실과 분리한 가정 | [phuryn create-prd](https://github.com/phuryn/pm-skills) - "Don't invent. What you don't know goes to 7.4 Assumptions and open questions, clearly marked, not into the body as fact." |
| 측정 가능한 목표 집합의 일부로서 대응 지표 | [TerminalSkills prd-writing](https://github.com/TerminalSkills/skills) - "Counter-metrics: [Metrics we don't want to hurt]" |
| 구현 메커니즘 감사 | [ai-conductor prd](https://github.com/jstoup111/ai-conductor) - "It MUST NOT name the new internal mechanism by which this feature is built." |
| 체크리스트를 짧게 유지하는, 문제에 비례한 산출물 | [Martin Fowler, SDD 도구 비교](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html) - "it quickly became clear that the workflow was like using a sledgehammer to crack a nut" |
| 기기 분류가 아니라 콘텐츠로 고른 중단점 | [Responsive web design basics](https://web.dev/articles/responsive-web-design-basics) - "Don't define breakpoints based on device classes" |
| 강제 스토어 항목이 출시 게이트에 모두 닿는지 | [Play Data safety](https://support.google.com/googleplay/android-developer/answer/10787469) - "Even developers with apps that do not collect any user data must complete this form" |

### 근거 등급

`LOCAL` - 열네 체크리스트 항목과 검토 표 형태는 이 패키지의 설계다. 표시 상한과 삭제 규칙은 인용한 명세 지침에서 가져왔고, 독자 테스트는 인용한 작성 지침에서 가져왔다.
