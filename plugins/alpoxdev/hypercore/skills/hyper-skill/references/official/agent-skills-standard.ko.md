# Skill-Maker를 위한 Agent Skills 표준 참조

## Contents

- 갱신 정책
- Agent Skills 명세
- 스킬 제작자를 위한 모범 사례
- 스킬 출력 품질 평가
- 스킬 설명 최적화
- 스킬에서 스크립트 사용
- Skills CLI를 통한 배포
- Sources

검토한 모든 런타임이 그 위에 세워진 공개 표준입니다. 이 스냅샷은 frontmatter 제약과 점진적 공개
예산에 대한 `PRIMARY` 출처입니다. 각 벤더가 그 위에 무엇을 더하는지는 옆의 제공자 스냅샷에 적습니다.

## 갱신 정책

- last_verified_at: 2026-11-03
- refresh_when:
  - 명세가 frontmatter 제약(name, description, compatibility, allowed-tools)을 바꿀 때
  - 점진적 공개 예산(목록 단계, 지침 단계, 줄 수 한도)이 바뀔 때
  - 참조 검증기(`skills-ref`)가 검사 항목을 바꿀 때
  - 스크립트 작성 문서가 실질적으로 바뀔 때
- supports_rules:
  - `rules/skill-anatomy.md`
  - `rules/trigger-design.md`
  - `rules/progressive-disclosure.md`
  - `rules/resource-placement.md`
  - `rules/validation-and-iteration.md`

## Agent Skills 명세

- source_url: https://agentskills.io/specification
- last_verified_at: 2026-11-03
- applies_to: frontmatter 필드와 그 제약, 디렉터리 관례, 점진적 공개, 파일 참조 깊이, 참조 검증기. 문서에는 눈에 보이는 날짜가 없고 내장된 `dateModified` 메타데이터가 2026-08-04를 가리킵니다.
- summary: 스킬은 최소한 `SKILL.md`를 담은 디렉터리이며, YAML frontmatter 뒤에 Markdown 본문이
  옵니다. `name`과 `description`은 필수이고 `license`, `compatibility`, `metadata`,
  `allowed-tools`는 선택입니다. 본문에는 형식 제한이 없습니다. `scripts/`, `references/`,
  `assets/`는 필수가 아니라 선택 관례입니다.
- implication_for_hyper_skill: 아래 제약 집합을 명세가 말한 그대로 강제하고, 선택 디렉터리는
  명세의 요구가 아니라 이 저장소가 고른 관례로 다룹니다.

### 출처가 말하는 frontmatter 제약

| 필드 | 필수 | 제약 |
|---|---|---|
| `name` | 예 | 1-64자. 소문자, 숫자, 하이픈만. 하이픈으로 시작하거나 끝날 수 없습니다. 연속 하이픈을 담을 수 없습니다. **부모 디렉터리 이름과 일치해야 합니다** |
| `description` | 예 | 1-1024자. 비어 있을 수 없습니다. 스킬이 무엇을 하는지와 언제 쓰는지를 모두 적고, 에이전트가 대조할 핵심어를 담아야 합니다 |
| `license` | 아니오 | 라이선스 이름 또는 함께 넣은 라이선스 파일 참조. 짧게 유지합니다 |
| `compatibility` | 아니오 | **제공한다면 1-500자.** 의도한 제품, 시스템 패키지, 네트워크 접근 같은 환경 요구가 있을 때만 씁니다 |
| `metadata` | 아니오 | 문자열 키에서 문자열 값으로 가는 맵. 충돌을 피하려면 키를 고유하게 유지합니다 |
| `allowed-tools` | 아니오 | 사전 승인된 도구의 공백 구분 문자열. **실험적**이며 구현마다 지원이 다릅니다 |

- implication_for_hyper_skill: `name`이 부모 디렉터리와 일치하는 것은 문체 선호가 아니라 명세
  요구이므로, 규칙 문구는 **must**로 쓰고 검증기는 이를 강제해야 합니다.

### 점진적 공개와 파일 참조

- 세 단계입니다. 메타데이터(`name` + `description`, 모든 스킬에 대해 시작 시 로드, 약 100토큰),
  스킬이 활성화될 때 로드되는 `SKILL.md` 본문(5,000토큰 미만 권장), 필요할 때 읽는 `scripts/`,
  `references/`, `assets/`입니다.
- 본문 `SKILL.md`는 500줄 미만으로 유지하고 세부 내용은 별도 파일로 옮깁니다.
- 다른 파일은 스킬 루트 기준 상대 경로로 참조하고, 참조는 `SKILL.md`에서 **한 단계 깊이**로
  유지합니다. 깊게 중첩된 참조 사슬은 피합니다.
- implication_for_hyper_skill: 500줄과 5,000토큰은 출처가 말한 값입니다. 이 저장소는 추가로
  `scripts/check-sources.sh`에서 300줄 게이트를 걸며, 그 검사는 `instructions`만 대상으로 합니다.
  300을 출처가 말한 값처럼 제시하지 말고 두 값을 구분해 유지합니다.

### 검증

- 출처는 참조 구현 `skills-ref validate ./my-skill`을 제시하며, 이는 `SKILL.md` frontmatter가
  유효하고 작명 관례를 따르는지 검사합니다.
- implication_for_hyper_skill: 이 저장소는 `scripts/validate-skills.sh`에서 `uvx`로 그것을
  실행합니다. 이 경로는 네트워크가 필요하고 `bash scripts/verify.sh`에 포함되지 않으므로,
  오프라인 게이트에 조용히 끼워 넣지 않습니다.

## 스킬 제작자를 위한 모범 사례

- source_url: https://agentskills.io/skill-creation/best-practices
- last_verified_at: 2026-11-03
- applies_to: 스킬 내용의 출처, 실제 실행을 통한 개선, 컨텍스트 사용, 함정, 읽기 신호, 기본값
- summary: 스킬은 일반 지식에서 생성하기보다 실제 전문성에 근거해야 합니다. 직접 수행한 작업에서
  추출하거나, 기존 프로젝트 산출물(내부 문서, 런북, API 명세, 코드 리뷰 코멘트, 버전 관리 이력,
  실제 실패 사례)에서 합성합니다. 실제 작업에 스킬을 돌리고 최종 출력만이 아니라 실행 추적을 읽어
  개선합니다. 내용 조각마다 "이 지침이 없으면 에이전트가 이것을 틀렸을까?"를 물어 아니면 덜어냅니다.
  구체성은 작업의 깨지기 쉬움에 맞추고 각 부분을 따로 조정합니다. 함정은 에이전트가 그 상황을
  만나기 전에 읽는 `SKILL.md`에 두고, 읽기 신호는 조건으로 씁니다("API가 200이 아닌 상태 코드를
  반환하면 `references/api-errors.md`를 읽으십시오"). 선택 메뉴가 아니라 기본값을 제시합니다.
  500줄·5,000토큰 예산을 말합니다.
- implication_for_hyper_skill: 스킬 초안을 쓰기 전에 도메인 전문성의 출처를 밝히게 하고, 개선
  단계에서는 출력이 아니라 추적을 읽게 하며, 함정은 핵심 문서에 두게 합니다.

## 스킬 출력 품질 평가

- source_url: https://agentskills.io/skill-creation/evaluating-skills
- last_verified_at: 2026-11-03
- applies_to: 테스트 케이스 설계, 스킬 있음·없음 쌍, 실행별 시간·채점 기록, 사람 검토, 단언, 반복 작업 공간
- summary: 테스트 케이스는 프롬프트, 사람이 읽는 기대 출력, 선택적 입력 파일로 이루어지며 스킬
  디렉터리 안의 `evals/evals.json`에 저장합니다. 각 케이스를 두 번, 즉 스킬과 함께 한 번 그리고
  없이(또는 `old_skill/`로 저장한 이전 버전과) 한 번, 실행마다 깨끗한 컨텍스트에서 돌립니다. 결과는
  스킬 옆 작업 공간에 두고 패스마다 `iteration-N/` 디렉터리를 만들며, `timing.json`(토큰과 시간),
  `grading.json`(PASS 또는 FAIL을 **구체적 증거와 함께**), 집계한 `benchmark.json`을 담습니다. 사람
  검토는 `feedback.json`에 남기며 "피드백이 비어 있으면 출력이 괜찮아 보였다는 뜻입니다". 기계적
  검사는 스크립트에 맡깁니다. 두 구성 모두에서 통과하는 단언은 빼거나 바꿉니다. 2-3개 케이스로
  시작합니다. 결과가 만족스럽거나 피드백이 계속 비어 있거나 반복이 의미 있게 나아지지 않으면
  멈춥니다.
- implication_for_hyper_skill: 짝지은 실행과 증거 문자열, 사람 피드백 기록이 핵심입니다. 증거
  문자열 없는 `passed: true`는 기록이 아닙니다. 이 저장소는 파일 이름은 유지하되 결과를
  `.omo/evidence/` 아래에 둡니다(`rules/resource-placement.md` §8).

## 스킬 설명 최적화

- source_url: https://agentskills.io/skill-creation/optimizing-descriptions
- last_verified_at: 2026-11-03
- applies_to: 지표로서의 트리거 비율, 케이스별 실행 횟수와 임계값, 훈련·검증 선택, 설명 길이 한도
- summary: 트리거 동작은 확률적이므로 질의마다 여러 번 실행하고("3이 합리적인 출발점입니다")
  트리거해야 하는 질의는 비율이 임계값을 넘을 때 통과시킵니다("0.5가 합리적인 기본값입니다").
  질의 약 20개를 양방향 8-10개씩 겨냥하고, 아슬아슬한 실패가 가장 값진 부정 사례입니다. 훈련과
  검증으로 대략 60/40으로 나누고, 훈련 실패에서만 설명을 바꾸며, 검증 통과율로 선택합니다. 가장
  좋은 설명이 마지막 설명은 아닐 수 있습니다. 편집할 때마다 1024자 한도를 다시 확인합니다. 다섯 번
  반복이면 보통 충분하며, 그다음 새 질의 5-10개로 다시 시험합니다. 명령형 표현("Use this skill
  when...")을 씁니다.
- implication_for_hyper_skill: 최종 점수만 보고하는 실행은 개선의 증거가 아닙니다. 반복마다 훈련과
  검증 수치를 함께 보고합니다.

## 스킬에서 스크립트 사용

- source_url: https://agentskills.io/skill-creation/using-scripts
- last_verified_at: 2026-11-03
- applies_to: 함께 넣는 코드를 어떻게 쓰고 문서화해야 하는가
- summary: 스크립트는 비대화형이어야 합니다. 이는 "에이전트 실행 환경의 강한 요구 사항"이며, 입력을
  기다리며 멈추는 스크립트는 멈춰 버리기 때문입니다. `--help`는 에이전트가 인터페이스를 익히는
  주된 방법입니다. 무엇이 잘못됐는지, 무엇을 기대했는지, 무엇을 시도할지를 말하는 도움이 되는
  오류를 쓰고, 모호한 입력은 추측하지 말고 분명한 오류로 거절합니다. 구조화된 데이터는 stdout으로,
  진단은 stderr로 보내고, 서로 다른 종료 코드를 쓰고, 멱등 동작을 선호하며, 출력 크기를 제한합니다.
  코드 블록의 경로는 스킬 루트 기준입니다. 의존성은 인라인으로 선언하거나 `SKILL.md`에 사전 조건을
  적습니다. 명세의 `scripts/` 절은 여기에 더해 스크립트가 자립적이거나 의존성을 문서화하고 경계
  조건을 우아하게 처리해야 한다고 말합니다.
- implication_for_hyper_skill: 스크립트의 인터페이스는 `--help`, 종료 코드, stdout입니다. 검토자가
  읽고 검증기가 다뤄야 하는 것이 바로 그것입니다.

## Skills CLI를 통한 배포

- source_url: https://github.com/vercel-labs/skills
- last_verified_at: 2026-11-03
- applies_to: 에이전트 전반에서 공유 형식의 스킬을 설치하고 갱신하고 제거하기
- summary: `npx skills add`, `find`, `update`, `remove`, `init`이 OpenCode, Claude Code, Codex,
  Cursor, "그리고 75개 더"의 에이전트를 위해 스킬을 관리하며, Node.js 22.20 이상을 요구합니다.
  많은 에이전트가 프로젝트 경로로 `.agents/skills/`를, 전역 경로로 `~/.agents/skills/`를 공유하며,
  `-g`/`--global`은 사용자 디렉터리에 설치합니다. 중복 처리는 Codex와 다릅니다. 두 스킬이 이름을
  공유하면 CLI는 처음 찾은 하나만 남깁니다.
- implication_for_hyper_skill: 파일은 같아도 설치 경로는 에이전트마다 다르고, 같은 이름 처리 방식은
  런타임마다 다르므로 둘을 한 규칙으로 쓰지 않습니다.

## Sources

> 확인 2026-11-03.

| 주장 | 출처 |
|---|---|
| frontmatter 필드 표와 그 모든 제약, 필수·선택 구분, 디렉터리 관례, 세 단계 공개 모델, 500줄 지침, 한 단계 깊이 파일 참조 규칙, `scripts/`의 자립성·경계 조건 지침, `dateModified` 메타데이터 | <https://agentskills.io/specification> |
| 실제 전문성에 근거한 스킬 작성, 추적을 통한 개선, 제거 질문, 깨지기 쉬움에 맞춘 구체성, `SKILL.md`의 함정, 조건부 읽기 신호, 메뉴보다 기본값, 5,000토큰 예산 | <https://agentskills.io/skill-creation/best-practices> |
| 테스트 케이스 형태, `evals/evals.json`, 스킬 있음·없음 또는 `old_skill/` 쌍, 실행마다 깨끗한 컨텍스트, `timing.json`, 증거가 있는 `grading.json`, `benchmark.json`, `feedback.json`, 반복 작업 공간, 2-3개 케이스 시작, 정지 조건 | <https://agentskills.io/skill-creation/evaluating-skills> |
| 트리거 비율, 3회 실행, 0.5 임계값, 약 20개 질의 집합, 약 60/40 분할, 훈련에서만 받는 피드백, "가장 좋은 것이 마지막은 아닐 수 있음", 1024자 재확인, 다섯 번 반복, 새 질의 5-10개 | <https://agentskills.io/skill-creation/optimizing-descriptions> |
| 비대화형 스크립트, `--help`, 도움이 되는 오류, 입력 거절, stdout·stderr 분리, 종료 코드, 멱등성, 출력 한도, 스킬 루트 기준 경로 | <https://agentskills.io/skill-creation/using-scripts> |
| skills CLI 명령 집합, 에이전트 수 표기, 공유 프로젝트·전역 경로, Node.js 22.20 요구, 처음 찾은 것만 남기는 중복 처리 | <https://github.com/vercel-labs/skills> |

### 증거 등급

`PRIMARY`입니다. 명세 문서가 frontmatter 제약과 공개 예산을 직접 말합니다. skills CLI 행은
`VENDOR`입니다. 한 도구가 자기 동작에 관해 한 서술입니다. 이 파일의 이전 판은 "경계 조건 처리"를
using-scripts 문서에 돌렸지만, 2026-11-03 점검에서 그 문장이 명세 문서에 있음을 확인했고 위에서
귀속을 바로잡았습니다.
