# 모드 라우팅

> 요청한 산출물로 모드를 정확히 하나 고르고, 그 모드의 파일만 읽습니다.

**목적**: 네 모드 중 어느 모드가 요청을 맡을지 정하거나, 요청을 이 스킬 밖으로 보냅니다. **읽는 조건**: 매 실행마다, 고른 모드의 첫 단계 전에 읽습니다.

## 1. Modes

| 모드 | 요청 산출물 | 자주 쓰는 말 | 모드 계약 |
|---|---|---|---|
| `readme` | 코드베이스를 읽고 쓰는 프로젝트 `README.md`, 또는 모노레포 안 패키지 `README.md` | README, 리드미, "프로젝트 소개 문서", install/usage 섹션 | `rules/readme/mode-contract.md` |
| `agents-md` | 루트·중첩 `AGENTS.md`, 인접 `rules/*.md` 분리, `AGENTS.ko.md` 미러 | AGENTS.md, "에이전트 지침 파일", 중첩 AGENTS.md | `rules/agents-md/mode-contract.md` |
| `prompt` | 재사용 역할·system·developer·agent·task 프롬프트, 프롬프트 템플릿이나 팩, 프롬프트 eval 픽스처·judge 계약·회귀 세트 | prompt, 프롬프트, system prompt, template, prompt pack, eval fixture | `rules/prompt/mode-contract.md` |
| `docs` | 그 밖의 AI가 읽는 문서: instruction base, 에이전트 가이드, 런북, 운영 절차, 명세, 정책·규칙 팩, 하네스 문서 | 런북, 가이드, 운영 절차, 명세, 규칙 팩, runbook, rule pack | `rules/docs/mode-contract.md` |

## 2. Selection Order

위에서부터 적용하고 처음 맞는 항목을 고릅니다.

1. 요청이 `README.md`를 산출물로 지목하면 `readme`입니다.
2. 요청이 `AGENTS.md`, `AGENTS.ko.md`, 중첩 `AGENTS.md`, 또는 그 `rules/*.md` 분리를 지목하면 `agents-md`입니다.
3. 요청이 `CLAUDE.md`, `.claude/CLAUDE.md`, `CLAUDE.local.md`를 산출물로 지목하면 경계 안내만 하는 `agents-md`입니다. 이 스킬은 `AGENTS.md`와 `AGENTS.ko.md`만 만든다고 밝히고 그 산출물을 제안하며, 요청한 파일은 만들거나 고치거나 심링크하거나 이름을 바꾸거나 지우지 않습니다.
4. 산출물을 지시 계약이나 eval 대상으로 다시 쓸 예정이면 `prompt`입니다.
5. 그 밖에 에이전트나 관리자가 읽고 따르는 구조화된 문서이면 `docs`입니다.

## 3. Tie-Breaks

- **한 요청에 산출물 둘**("README랑 AGENTS.md 둘 다"): 사용자가 말한 순서대로 모드를 차례로 실행합니다. 모드마다 자기 계약, 게이트, 보고 섹션을 따로 두고 두 계약을 한 번에 섞지 않습니다.
- **파일을 지목하지 않은 "이 프로젝트 문서화해줘"**: 코드를 설치하거나 쓰는 사람을 위한 프로젝트 첫 화면 문서는 `readme`, 운영 가이드·런북·instruction base는 `docs`입니다. 요청과 저장소 어느 쪽으로도 정해지지 않고 잘못 고르면 작업을 다시 해야 하면, 두 해석과 권장안을 담아 한 번만 묻습니다.
- **프롬프트인가 문서인가**: 산출물을 지시 계약이나 eval 대상으로 다시 쓸 때만 `prompt`를 고릅니다. 프롬프트 엔지니어링*에 관한* 가이드는 `docs`입니다.
- **스킬 폴더 안의 프롬프트**: `prompt`는 요청이 지목한 프롬프트 파일만 맡습니다. 스킬 폴더 자체는 범위 밖입니다(§4).
- **런타임 규칙 팩**: `AGENTS.md`에 기반하면 `agents-md`, 그 밖의 런타임 규칙 팩은 `docs`입니다.
- **지금 보낼 답장의 한 문장 수정**: 바로 답합니다. 재사용 프롬프트가 아닙니다.

## 4. Out of Scope

다른 담당자 이름이 아니라 산출물 모양으로 밖으로 보냅니다.

- 재사용 스킬 폴더(`SKILL.md`와 그 rules, references, scripts, assets).
- `CHANGELOG.md`, `CONTRIBUTING.md`, `LICENSE`, 릴리스 노트, 버전 올리기.
- 저장할 산출물이 없는 답변형 조사나 일회성 답변.
- 문서가 부산물인 제품 코드, 설정, 테스트 작업.
- 제품 기획 패키지(PRD, 기능 명세, 사용자 흐름, 와이어프레임)나 구현 전 계획.
- 검색 노출 점검이나 마케팅 페이지 최적화.
- 완성한 문서의 커밋, 푸시, 게시. 문서는 여기서 쓰고, 그 뒤의 버전 관리 동작은 별도 단계입니다.

## 5. Route Line

고른 모드의 첫 단계 전에 한국어 한 줄을 출력합니다.

```text
모드: <readme|agents-md|prompt|docs> / 근거: <그 모드를 고른 요청 구절이나 파일>
```

§2.3 경계 요청이면 `모드: agents-md (경계 안내만)`을 출력합니다. §4 요청이면 산출물 모양을 출력하고 모드를 불러오지 않은 채 멈춥니다.

## Sources

> 외부 출처는 사용하지 않았습니다. 내용 확인 2026-11-07.

| 주장 | 출처 |
|---|---|
| 네 모드, 선택 순서, 동점 처리 | 2026-11-07 사용자 지시로 산출물이 하나씩인 문서 워크플로 네 개를 이 스킬로 합칠 때 정한 이 패키지의 설계 |
| 프롬프트와 문서를 나누는 규칙, 스킬 폴더 안 프롬프트 규칙 | 이 패키지의 이전 프롬프트 라우팅 규칙. 내용은 그대로 가져왔습니다 |
| `CLAUDE.md` 경계 | `rules/agents-md/mode-contract.md` (이 패키지) |
