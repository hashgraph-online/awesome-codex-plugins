# 생태계

2026-11-08 기준으로 이 패키지가 놓인 자리입니다. TypeSafe Jev용으로 공급자가 배포한 에이전트 스킬, 결정 모델 주변의 커뮤니티 스킬, 이 패키지가 내는 것을 다룹니다. 커뮤니티 항목에는 모두 **커뮤니티, 필수 아님, 참고용**이라는 표시를 붙입니다. 여기 있는 어떤 것도 의존성이 아닙니다.

## Contents

- 갱신 정책
- 공급자가 배포한 스킬
- 커뮤니티 스킬
- 이 패키지가 내는 것
- 이 목록을 읽는 방법
- 확인되지 않은 항목
- Sources

## 갱신 정책

- last_verified_at: 2026-11-08
- refresh_when:
  - 공급자 스킬이 새 릴리스를 내거나 설치 경로를 바꿀 때
  - 여기 나열한 커뮤니티 스킬이 보관되거나, 이름이 바뀌거나, 옮겨질 때
  - 다른 공급자가 공식 decision API 스킬을 배포할 때
- supports_rules:
  - rules/modes-and-routing.md

## 공급자가 배포한 스킬

TypeSafe는 `typesafe-ai/skills` 저장소에 `typesafe-ai` 스킬 하나를 배포합니다. 2026-11-08에 이 저장소에는 `SKILL.md`(288줄) 하나와 라이선스만 있었고 references나 scripts는 없었습니다. 마지막 릴리스는 2026-10-23의 v0.6.2이며, v0.5.7(2026-09-12)을 거의 전부 다시 쓴 판입니다.

공급자 페이지의 설치 경로입니다. 오래된 사본이 에이전트가 요청이나 응답 필드를 지어내는 원인이므로, 페이지는 하나만 쓰라고 합니다.

```bash
claude plugin marketplace add typesafe-ai/skills
claude plugin install typesafe@typesafe-ai
npx skills add typesafe-ai/skills --skill typesafe-ai
```

v0.6.2가 가르치는 것과 이 패키지에서 받아들인 위치입니다.

| 공급자 지침 | 받아들인 곳 |
|---|---|
| 판단은 모델이, 결정은 코드가 맡습니다. 결정은 진리표로 두고 판단만 묻습니다 | `../rules/modes-and-routing.ko.md` §2 |
| 사람 시험. 유능한 사람이 이 state와 질문만으로 바로 답할 수 있어야 합니다 | `../rules/modes-and-routing.ko.md` §2, `./question-design.ko.md` |
| 확신도가 관문인 경우는 드뭅니다. 고른 선택지의 확률로 행동합니다 | `../rules/safety-and-boundaries.ko.md` §5, `./patterns.ko.md` |
| 경고 신호("prompt gymnastics"). 기준에 테스트 항목 이름 넣기, 실패 사례마다 절 추가, 사례에 맞춘 임계값, 정확한 확률을 단언하는 테스트, 답을 조용히 덮어쓰는 코드 | `./eval-and-audit.ko.md` |
| 질문, 선택지, 기준, 임계값을 담는 상수 모듈 하나를 검토 대상으로 둡니다 | `../assets/templates/constants.template.ts` |
| 작업 중에 실제 문서를 열고, 페이지를 못 읽으면 그렇다고 말합니다 | `../rules/safety-and-boundaries.ko.md` §10 |

## 커뮤니티 스킬

모든 행은 2026-11-08에 `SKILL.md`를 직접 열어 확인했고, 마지막 커밋 날짜는 저장소에서 읽었습니다.

| 계열 | 이름과 저장소 | 마지막 커밋 | 하는 일 |
|---|---|---|---|
| 설계 안내 | `system-one`, magnus919/agent-skills | 2026-10-15 | 여러 공급자에 걸쳐 System One 결정 모델을 설계, 통합, 평가, 자체 호스팅 |
| 설계 안내 | `building-with-decision-models`, aaddrick/building-with-decision-models | 2026-10-10 | `building-with-typesafe-jev`의 공급자 중립 후속작. 공급자마다 파일 하나 |
| 설계 안내 | `building-with-typesafe-jev`, aaddrick/building-with-typesafe-jev | 2026-09-27 | Jev 의도-형태 대응표, API 참조, 패턴, 평가 케이스 6개 |
| 공급자 게이트웨이 | `openrouter-decisions`, OpenRouterTeam/skills | 2026-10-29 | OpenRouter Decisions API 구현. 프리미티브, state, 모델 고정, 임계값 탐색 |
| 프레임워크 | `langgraph-decision-models`, langchain-ai/langchain-skills | 2026-09-25 | LangGraph 라우팅을 결정 모델 분류기로 대체 |
| 질문 생성 | `grill-jev`, grgy078033/grill-jev; Blue-And-White/Grill-Jev; notque/vexjoy-agent | 2026-09-20~2026-10-30 | 계획이나 작업의 결정 지점마다 결정 모델에 질문 |
| 분류 | `jev-triage`, wuyoscar/jev-skill(포크 여러 개) | 2026-09-22 | 스모크 테스트 파일럿을 곁들인 받은 편지함·티켓 분류 |
| 평가 | `jev-eval`, OneWave-AI/claude-skills; BarakChamo/jev-kit; wuyoscar/jev-skill | 2026-09-22~2026-09-29 | 라벨 세트, 기준과 임계값 탐색, 확신하며 틀린 답 찾기 |
| 평가 | `jev-avaliar`, ia-automation/How-to-use-JEV | 2026-10-01 | 고정된 보류 세트를 쓰는 포르투갈어 도메인 평가 |
| 감사 | `jev-audit`, OneWave-AI/claude-skills; idogoldd/skills; magicbeansai/jev-audit; chaseai-yt/jev-audit | 2026-09-19~2026-10-07 | 라벨만 돌려주는 LLM 호출이나 휴리스틱 코드를 찾아 교체 순위 매기기 |

## 이 패키지가 내는 것

- 조언이 아니라 파일을 냅니다. 방언별 요청 JSON, 상수 파일, 경로와 언어별 호출 코드, 템플릿 세트, 평가 케이스 뼈대, 읽기 전용 감사 표입니다.
- 공급자를 가로지르는 계약 하나를 둡니다. 중립 타입 `boolean`, `choice`, `score`, `box`, 방언 대응표, 확률이 돌아오는지 밝히는 경로 층 네 개입니다.
- 키와 네트워크가 필요 없는 방언별 오프라인 검사기가 있습니다.
- 자주 바뀌는 사실은 날짜가 붙은 참조에만 두고 30일이 지나면 다시 확인합니다.

설계 안내 계열과 겹치는 부분은 의도적이고 얕습니다. 이 패키지는 모델이 할 수 있는 일을 공급자 참조로 링크하고, 분량은 생성되는 산출물과 그 검사에 씁니다.

## 이 목록을 읽는 방법

이 페이지의 이름은 실마리이지 의존성이 아닙니다. 커뮤니티 스킬은 관리되지 않거나, 현재 공급자 문서와 어긋나거나, 이미 없는 모델 버전을 대상으로 할 수 있습니다. 별 개수와 설치 수는 고르는 근거로 쓰지 않습니다. 근거는 그 스킬이 지금 필요한 산출물을 만드는지, 공급자의 현재 페이지와 맞는지입니다. 2026-11-08에 TypeSafe와 OpenRouter 말고 decision API 스킬을 배포한 공급자는 없었습니다.

## 확인되지 않은 항목

- 커뮤니티 스킬의 설치 수와 레지스트리 등재: 하루에 한 번 검색한 결과이며 근거로 쓰지 않습니다.
- `jev-triage`와 `jev-audit`의 포크와 미러: 일부 저장소는 원본이 아니라 미러이므로 원본만 나열했습니다.
- 위 항목과 이름은 같지만 내용이 무관한 스킬이 있습니다(`hraness/system-one-skills`). 이름이 아니라 내용으로 맞춥니다.

## Sources

> Links checked 2026-11-08.

| Claim | Source |
|---|---|
| 공급자 스킬의 저장소, 릴리스 이력, 내용 | <https://github.com/typesafe-ai/skills> (release v0.6.2, 2026-10-23) |
| 설치 경로, 하나만 쓰는 규칙, 오래된 사본의 실패 | <https://docs.typesafe.ai/agent-skill.md> |
| 커뮤니티 스킬의 위치, 내용, 마지막 커밋 | 표에 적은 저장소, 2026-11-08 GitHub에서 열어 확인 |
| 이 패키지가 내는 것과 받아들인 관행 | 이 패키지 자체의 규칙과 참조 |

### Evidence grade

공급자가 배포한 스킬 절은 `VENDOR`이며, 2026-11-08에 그 저장소와 공급자 페이지에서 읽었습니다. 커뮤니티 표는 `COMMUNITY`입니다. 모든 행을 열어 봤지만 어느 것도 보증하거나 정확성을 확인하지 않았습니다. 이 패키지가 내는 것 절은 `LOCAL`입니다.
