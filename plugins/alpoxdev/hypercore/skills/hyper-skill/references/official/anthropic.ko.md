# Skill-Maker를 위한 Anthropic 공식 참조

## Contents

- 갱신 정책
- Claude Code 스킬
- Agent Skills 개요
- 스킬 제작 모범 사례
- 엔터프라이즈용 스킬
- Agent Skills 엔지니어링 글
- Claude Skills 제품 글
- Sources

## 갱신 정책

- last_verified_at: 2026-11-03
- refresh_when:
  - Claude Code 또는 Agent Skills 지침이 실질적으로 바뀔 때
  - frontmatter 필드 표, 목록 예산, 표준·확장 구분이 바뀔 때
  - 스킬 구조, 점진적 공개, 스크립트, 검증 지침이 바뀔 때
  - 핵심 hyper-skill 규칙이 Anthropic 동작을 더 직접 인용할 때
- supports_rules:
  - `rules/skill-anatomy.md`
  - `rules/trigger-design.md`
  - `rules/progressive-disclosure.md`
  - `rules/resource-placement.md`
  - `rules/validation-and-iteration.md`

## Claude Code 스킬

- source_url: https://code.claude.com/docs/en/skills
- last_verified_at: 2026-11-03
- applies_to: `SKILL.md`, frontmatter 전체 표면, 지원 파일, 호출 제어, 동적 컨텍스트 주입, 문자열 치환, 목록 예산, 발견 위치, 컨텍스트 안 생애주기, 평가 도구
- summary: Claude Code 스킬은 Agent Skills 공개 표준을 따르고 그것을 확장합니다. **Claude Code는 여는
  `---`가 파일의 첫 줄일 때만 frontmatter를 읽습니다.** 그렇지 않으면 `---` 표시를 포함한 파일 전체를
  스킬 내용으로 취급합니다. 표시 사이의 YAML이 해석되지 않아도 스킬은 필드가 하나도 설정되지 않은
  채로 로드됩니다. 문서는 frontmatter 필드 스무 개를 제시하며 모두 선택 사항이고, 그중 표준에 속하는
  것은 `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools` 여섯입니다.
  Claude Code는 모르는 필드를 오류 없이 무시하지만, claude.ai 업로드와 Skills API 경로에서 명세가
  허용하지 않는 필드는 **하드 오류**("Unexpected key(s) in SKILL.md frontmatter")가 되며, 동적
  컨텍스트 주입 같은 Claude Code 전용 본문 기능은 그곳에서 동작하지 않습니다. 스킬은 엔터프라이즈,
  개인, 프로젝트, 중첩, `--add-dir`, 플러그인, claude.ai 계정 위치에서 로드됩니다. **호출된 스킬의
  렌더링된 내용은 하나의 메시지로 대화에 들어가 이후 턴에도 남습니다. Claude Code는 파일을 다시 읽지
  않습니다.** `claude plugin validate .claude/skills`는 frontmatter가 해석되지 않는 스킬 파일을
  보고합니다.
- implication_for_hyper_skill: 규칙 문구에서 표준 여섯 필드와 확장 열넷을 구분해야 합니다. 둘을
  섞은 스킬은 Claude Code에서만 이식 가능하기 때문입니다(SK-P-3). 스킬은 로컬에서 멀쩡해 보여도
  업로드에 실패할 수 있습니다. 첫 줄 규칙은 이미 두 저장소 게이트가 강제하므로 새 도구가 아니라
  서술이 필요합니다.

### 문서가 제시하는 frontmatter 필드

표준 필드(이식 가능): `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`.

Claude Code 확장: `when_to_use`, `argument-hint`, `arguments`, `disable-model-invocation`,
`user-invocable`, `disallowed-tools`, `model`, `effort`, `context`, `agent`, `background`, `hooks`,
`paths`, `shell`.

| 필드 | 규칙으로 가져갈 동작 |
|---|---|
| `description` | `when_to_use`와 합쳐 스킬 목록에서 **1,536자**에서 잘립니다. 핵심 용도를 앞에 둡니다 |
| `when_to_use` | 추가 트리거 맥락으로, `description` 뒤에 붙고 같은 1,536자 한도에 포함됩니다 |
| `disable-model-invocation` | `true`이면 Claude가 스킬을 자동으로 로드하지 않아 명시적 호출만 동작합니다. Codex의 `allow_implicit_invocation: false`에 대응합니다 |
| `user-invocable` | `false`이면 `/` 메뉴에서 숨겨져 Claude만 호출합니다 |
| `allowed-tools` | 스킬을 호출한 **턴 동안 Claude가 승인 없이 쓸 수 있는** 도구입니다. 스킬 내용은 컨텍스트에 남아도 다음 메시지에서 권한이 해제됩니다. 제한적 경계가 아니라 허용적 부여입니다 |
| `disallowed-tools` | 스킬이 활성인 동안 도구 풀에서 제거됩니다. 다음 메시지에서 해제됩니다 |
| `context` | `fork`로 두면 분기된 서브에이전트 컨텍스트에서 실행되며, `agent`가 서브에이전트 유형을, `background`가 턴의 대기 여부를 정합니다 |
| `paths` | 자동 활성화를 일치하는 파일로 제한하는 글롭 패턴입니다 |
| `shell` | 인라인 셸 블록에 쓸 셸입니다. 기본은 `bash`입니다 |
| `hooks` | 스킬 호출 시 등록되어 세션 동안 유지되는 훅입니다 |

### 본문 기능

- **동적 컨텍스트 주입**: `` !`command` ``는 명령을 실행하고 Claude가 스킬 내용을 보기 전에 그 줄을
  출력으로 바꿉니다. Claude Code 전용이며 claude.ai나 API 경로에서는 동작하지 않습니다.
- **문자열 치환**: `$ARGUMENTS`, `$ARGUMENTS[N]`·`$N`, `arguments` 목록의 이름 있는 `$name`,
  `${CLAUDE_SESSION_ID}`, `${CLAUDE_EFFORT}`, `${CLAUDE_SKILL_DIR}`, `${CLAUDE_PROJECT_DIR}`, 그리고
  플러그인 스킬에서는 `${CLAUDE_PLUGIN_ROOT}`와 `${CLAUDE_PLUGIN_DATA}`입니다.
- `${CLAUDE_SKILL_DIR}`과 `${CLAUDE_PROJECT_DIR}`는 스킬의 마크다운 내용과 `allowed-tools`의 Bash
  규칙 두 곳에서 치환됩니다. 같은 변수를 두 곳에 쓰면 스킬이 함께 넣은 스크립트를 권한 프롬프트 없이
  실행할 수 있습니다. 스크립트를 함께 배포할 때의 문서화된 패턴입니다.

### 목록 예산

- Claude Code는 스킬 이름과 설명의 목록을 컨텍스트에 로드합니다. **목록에는 항상 모든 스킬 이름이
  들어가지만 넘치면 Claude Code가 설명을 줄이며, 가장 적게 호출한 스킬부터 시작합니다.** 예산은
  **모델 컨텍스트 창의 1%**로 정해지고, 각 항목의 `description` + `when_to_use` 합친 텍스트는 예산과
  무관하게 1,536자에서 잘립니다. `skillListingBudgetFraction`, `SLASH_COMMAND_TOOL_CHAR_BUDGET`,
  `skillListingMaxDescChars`가 예산을 바꿉니다. `/doctor`는 목록 비용과 가장 큰 기여 항목을 추정하고,
  `/skill-doctor`는 스킬별 비용과 사용 빈도를 보여줍니다. `skillOverrides` 설정은 스킬 frontmatter를
  고치지 않고 설정에서 가시성을 조절하며(`on`, `name-only`, `user-invocable-only`, `off`), 플러그인
  스킬에는 적용되지 않습니다.
- implication_for_hyper_skill: Codex의 2%·8,000자보다 더 빠듯한 두 번째 예산이며, 위치가 아니라 사용
  빈도로 잘립니다. 드물게 호출되는 스킬이 설명을 가장 먼저 잃으므로 핵심 트리거가 앞에 와야 합니다.

### 평가 도구

- `skill-creator` 스킬은 프롬프트와 입력 파일, 기대 동작을 스킬 디렉터리 안의
  `evals/evals.json`에 저장하고 사례마다 서브에이전트를 띄워 매 실행이 깨끗하게 시작되게 합니다.
- `claude plugin eval`은 각 프롬프트를 플러그인이 있거나 없거나 격리된 세션에서 실행하고 채점기로
  점수를 매기며, 한도 아래에서는 0이 아닌 코드로 끝나 CI가 게이트로 쓸 수 있게 합니다. `tool_used:
  Skill` 채점기는 트리거링을 측정합니다.
- **두 형식은 서로 바꿔 쓸 수 없습니다.**
- 스킬을 쓸 때 남은 컨텍스트가 작성한 지침의 빈틈을 가리므로, 평가 실행은 매번 새 세션에서
  시작합니다.

## Agent Skills 개요

- source_url: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
- last_verified_at: 2026-11-03
- applies_to: 비용이 붙는 세 가지 로딩 단계, 필드 제약, 표면 차이
- summary: 메타데이터는 시작 시 스킬당 약 100토큰으로 로드되고, `SKILL.md` 본문은 트리거될 때 로드되며
  5k 토큰 아래로 유지해야 합니다. 함께 넣은 자원은 읽기 전까지 비용이 없고, 스크립트의 코드는
  컨텍스트에 들어가지 않으며 그 출력만 들어갑니다. `name`은 소문자와 숫자, 하이픈으로 된 64자
  이하이고 XML 태그와 예약어 "anthropic", "claude"를 담을 수 없으며, `description`은 XML 태그 없이
  1,024자 이하입니다. 사용자 지정 스킬은 표면(claude.ai, API, Claude Code) 사이에서 동기화되지
  않습니다. API에서는 스킬이 네트워크 접근 없이 코드 실행 컨테이너에서 돌고, Claude Code에서는 그
  기기의 다른 프로그램과 같은 네트워크 접근을 가집니다.
- implication_for_hyper_skill: 명세의 1,024자 한도와 Claude Code 목록의 1,536자 절단은 서로 다른
  한도이며, 스킬의 네트워크 태세는 실행 표면에 달려 있습니다.

## 스킬 제작 모범 사례

- source_url: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- last_verified_at: 2026-11-03
- applies_to: Claude가 더하는 frontmatter 제약, 작명, 설명의 인칭, 점진적 공개 패턴, 참조 파일 구조, 모델 커버리지, 자유도
- summary: Claude는 표준 위에 제약을 더합니다. `name`은 XML 태그를 담을 수 없고 예약어 **"anthropic"**과
  **"claude"**를 담을 수 없으며, `description`은 XML 태그를 담을 수 없습니다. 설명은 **3인칭**으로
  써야 합니다. 이 필드가 시스템 프롬프트에 주입되므로 인칭이 일관되지 않으면 발견에 문제가 생깁니다.
  동명사형 이름(동사 + `-ing`)이 권장 관례이고, 명사구와 동작 지향 이름도 허용되며 `helper`나 `utils`
  같은 모호한 이름은 피합니다. `SKILL.md`는 500줄 미만으로 유지합니다. 참조는 **한 단계 깊이**로
  유지합니다. Claude는 다른 참조에서 참조된 파일을 부분적으로 읽고 `head -100`으로 미리보기할 수
  있어 전체를 읽지 않을 수 있기 때문입니다. **100줄을 넘는 참조 파일에는 맨 위에 목차를 넣어**
  부분 읽기에서도 전체 범위가 보이게 합니다. 계획한 모든 모델에서 스킬을 시험합니다. "Opus에서
  완벽하게 동작하는 것이 Haiku에는 더 자세한 설명이 필요할 수 있습니다". 구체성은 깨지기 쉬움에
  맞춥니다. 여러 접근이 유효하면 높은 자유도(텍스트 지침), 선호 패턴이 있으면 중간 자유도(매개변수
  있는 스크립트), 동작이 깨지기 쉽고 일관성이 중요하면 낮은 자유도(매개변수 없는 정확한 스크립트)입니다.
- implication_for_hyper_skill: 3인칭 규칙, 예약어·XML 태그 제약, 동명사 관례, 100줄 초과 목차
  규칙은 모두 검사 가능하므로 규칙 문구에 들어가야 합니다. 500줄은 명세와 일치합니다.

## 엔터프라이즈용 스킬

- source_url: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise
- last_verified_at: 2026-11-03
- applies_to: 스킬 심사, 위험 등급표, 공존을 포함한 평가 차원, 버전 고정, 회수 한도, 스캔 범위
- summary: 위험 등급표는 우려 수준과 함께 일곱 지표를 제시합니다. **코드 실행**, **지침 조작**,
  **MCP 서버 참조**, **네트워크 접근 패턴**, **하드코딩된 자격 증명**이 높음이고, **파일시스템 접근
  범위**와 **도구 호출**이 중간입니다. 배포 전 평가에는 **공존, "이 스킬을 더하면 다른 스킬이
  나빠지는가?"** 가 들어가며, 실패 사례로 "새 스킬의 설명이 너무 넓어 기존 스킬의 트리거를
  가로챕니다"를 듭니다. 스킬마다 트리거해야 하는 경우, 트리거하지 말아야 하는 경우, 모호한 경우를
  아우르는 대표 질의 3-5개를 씁니다. 프로덕션에서는 스킬을 특정 버전에 고정하고, 모든 갱신을 전체
  보안 검토가 필요한 새 배포로 다루고, 이전 버전을 롤백용으로 남기고, 검토한 스킬의 체크섬을 계산해
  배포 시 검증하며, 작성자가 자기 스킬을 검토하지 못하게 합니다. 동시에 로드하는 스킬 수를 제한해
  회수를 안정적으로 유지하며, API는 요청당 최대 20개 스킬을 받습니다. 자동 스캔은 Skills API나
  Console로 업로드한 스킬을 다루지 않습니다.
- implication_for_hyper_skill: 산출물 감사는 위험 행 일곱 개를 모두 담아야 하고, 공존은 부차적
  항목이 아니라 평가 차원이어야 하며, 설치된 스킬 수는 예산입니다.

## Agent Skills 엔지니어링 글

- source_url: https://www.anthropic.com/research/equipping-agents-for-the-real-world-with-agent-skills
- last_verified_at: 2026-11-03
- applies_to: 스킬 구조, 점진적 공개, 스크립트, 평가 우선 반복, 신뢰 경계
- summary: 2025-10-16에 게시되었고 예전 `/engineering/` URL은 이곳으로 넘어옵니다. "점진적 공개는
  Agent Skills를 유연하고 확장 가능하게 만드는 핵심 설계 원칙"이며, 메타데이터, 본문, 연결된 파일
  순서로 진행됩니다. 코드는 결정적이므로 함께 넣은 스크립트를 컨텍스트에 올리지 않고도 워크플로를
  일관되고 반복 가능하게 만듭니다. 스킬은 신뢰하는 출처에서만 설치하고, 신뢰할 수 없는 스킬은 쓰기
  전에 함께 넣은 파일, 코드 의존성, 신뢰할 수 없는 네트워크 출처에 닿으라는 지시를 감사합니다.
  평가에서 시작해 빈틈에 맞춰 스킬을 점진적으로 키웁니다.
- implication_for_hyper_skill: 점진적 공개, 목적이 분명한 스크립트, 출처·자원 신뢰 점검이 일급 규칙입니다.

## Claude Skills 제품 글

- source_url: https://claude.com/blog/skills
- last_verified_at: 2026-06-02
- recheck_status: 2026-09-20 또는 2026-11-03 점검에서 다시 읽지 않았습니다. 위 날짜는 마지막으로 실제 읽은 날짜입니다
- applies_to: 이식성, 조합성, 재사용 역량으로서의 스크립트·자원
- summary: 스킬은 지침, 스크립트, 자원을 담은 폴더이며 전문 워크플로를 이식 가능하고 조합 가능하게 만듭니다.
- implication_for_hyper_skill: 스킬은 일회성 프롬프트가 아니라 재사용 패키지로 유지해야 합니다.

## Sources

> 확인 2026-11-03. "예"로 표시한 행을 읽었습니다.

| 주장 | 출처 | 2026-11-03 점검에서 읽음 |
|---|---|---|
| 스무 개 frontmatter 필드 표, 표준 여섯 필드, 업로드·API 경로에서 비표준 필드의 하드 오류, 로컬에서 무시되는 미지 필드, 첫 줄 규칙, YAML 해석 실패 시 대체 동작, 발견 위치, 컨텍스트 안 생애주기, `context: fork`, 동적 컨텍스트 주입, 문자열 치환, 적게 호출한 순서로 잘리는 1%·1,536자 목록 예산, `/doctor`, `/skill-doctor`, `skillOverrides`, `claude plugin validate`, `evals/evals.json`, `claude plugin eval`, 서로 바꿀 수 없는 두 형식, 평가 실행마다 새 세션 | <https://code.claude.com/docs/en/skills> | 예 |
| `name`의 XML 태그·예약어 제약, `description`의 XML 태그 제약, 3인칭 설명, 동명사 관례, 500줄 본문, 한 단계 깊이 참조와 부분 읽기 이유, 100줄 초과 목차 규칙, 모델 커버리지 시험, 세 단계 자유도 | <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices> | 예 |
| 토큰 비용이 있는 세 단계 로딩, 필드 한도, 표면 간 동기화 없음, 표면에 따른 네트워크 태세 | <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview> | 예 |
| 우려 수준이 있는 위험 등급 일곱 행, 공존, 3-5개 질의 묶음, 버전 고정, 재검토, 롤백, 체크섬, 직무 분리, 요청당 20개 스킬 한도, 스캔 빈틈 | <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise> | 예 |
| 핵심 원칙으로서의 점진적 공개, 신뢰 출처·감사 규칙, 평가 우선 반복(2025-10-16 게시) | <https://www.anthropic.com/research/equipping-agents-for-the-real-world-with-agent-skills> | 예 |
| 이식성, 조합성, 재사용 패키지로서의 스킬 | <https://claude.com/blog/skills> | 아니오 |

### 증거 등급

`VENDOR`입니다. Anthropic이 자기 제품에 관해 한 서술입니다. 위 표의 한 행은 2026-06-02 점검에서 읽은
그대로 이월했으며 날짜를 새로 찍지 않고 그 사실을 표시했습니다. 엔터프라이즈 문서의 심각도 표시는
그 문서의 부여이며 통제된 연구의 결과가 아니므로, 그것에 대한 감사는 알려진 산출물 수준 문제를
걸러내는 체크리스트이지 안전의 증명이 아닙니다. 요청당 20개 스킬 한도는 개요 문서가 아니라
엔터프라이즈 문서에 적혀 있습니다.
