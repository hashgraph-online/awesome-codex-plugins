# 멀티 에이전트 능력·도구·스킬 로딩 대응표

Hypercore 스킬 본문이 쓰는 중립적인 **능력 이름**을 **omp**, **Antigravity(`agy`)**, **Claude Code**, **Codex** 네 환경의 실제 도구 이름, 스킬 설치 경로, 스킬 간 상호 참조 규칙, 머리말(frontmatter) 규칙에 대응시키는 단일 기준 문서입니다. 각 스킬 본문은 특정 제품의 도구 이름을 박지 않고 §1의 능력 이름만 씁니다.

## 목차

- 1. 능력 이름 대 환경별 도구 대응표
- 2. 환경별 스킬 탐색·설치 경로와 상호 참조 표준
- 3. 이식 가능한 머리말(Frontmatter) 계약
- 4. 환경별 직접 검증 범위와 추정 표시
- Sources

## 1. 능력 이름 대 환경별 도구 대응표

스킬 본문은 "파일 읽기", "파일 쓰기·수정", "본문·파일 검색", "셸 명령 실행", "하위 작업 위임", "사용자 질문", "스킬 불러오기"처럼 **능력**만 적고, 실행 환경에 맞춰 아래 표면으로 수행합니다.

| 스킬 본문의 능력 이름 | omp (`oh-my-pi`) | Antigravity (`agy`) | Claude Code | Codex (`codex` CLI / 앱) |
|---|---|---|---|---|
| 파일 읽기 (`Read file`) | `read` | `read_file` | `Read` | 내장 파일 읽기 / `exec_command` (`sed`, `cat`) |
| 파일 쓰기·수정 (`Write / edit file`) | `write`, `edit` | `write_file`, `edit_file` | `Write`, `Edit` | `apply_patch` |
| 파일·본문 검색 (`Search files & text`) | `grep`, `find` | `run_command` (`rg`, `fd`) | `Grep`, `Glob` | `exec_command` (`rg`, `fd`) |
| 셸 명령 실행 (`Run shell command`) | `bash` | `run_command` (백그라운드는 `manage_task`) | `Bash` | `exec_command` (비대화형 CLI는 `codex exec`) |
| 하위 작업 위임 (`Delegate subtask`) | `task` (또는 구성된 `hc` 워커) | `invoke_subagent` (`define_subagent`, `send_message`, `run_workflow`) | `Agent` / `Task` 도구 (`.claude/agents/*.md`, agent teams) [문서] | 네이티브 하위 에이전트 / `spawn_agent`, `send_input`, `wait_agent` (`.codex/agents/*.toml`) [문서] |
| 사용자 질문 (`Ask user`) | `ask` (또는 일반 텍스트 질문) | `ask_question` (객관식) 또는 일반 텍스트 질문 | `AskUserQuestion` 또는 일반 텍스트 질문 [문서] | 일반 텍스트 질문 (계획 모드의 `request_user_input` 노출 여부는 모드별 추정) |
| 스킬 불러오기 (`Load skill`) | `skill://<name>` 또는 `../<name>/SKILL.md` 읽기 | 탐색된 스킬 활성화 또는 `../<name>/SKILL.md` 읽기 | `/<name>`·`Skill` 도구 또는 `../<name>/SKILL.md` 읽기 [문서] | `$<name>` 또는 `../<name>/SKILL.md` 읽기 |
| 프로젝트 지침 표면 (`Instruction surface`) | `AGENTS.md`, `~/.omp/agent/rules/` | `GEMINI.md`, `AGENTS.md`, `.agents/rules/`, `~/.gemini/config/rules/` | `AGENTS.md`(v2.1.277+, `CLAUDE.md`가 없을 때), `CLAUDE.md` [문서] | `AGENTS.md`, `AGENTS.override.md`, `~/.codex/config.toml` |

기능 부재 시 대체 규칙:

- **하위 작업 위임 도구가 없을 때**: 독립 읽기 전용 점검은 현재 세션에서 순서대로 직접 수행합니다. 단, 스킬 계약이 독립 리뷰어를 필수로 요구하는 고강도 리뷰 모드에서는 해당 스킬의 정지·축소 규칙을 따릅니다.
- **전용 질문 도구가 없을 때**: 권장안 하나를 붙인 짧은 일반 텍스트 질문 하나만 출력하고 답을 기다립니다.

## 2. 환경별 스킬 탐색·설치 경로와 상호 참조 표준

환경마다 스킬이 놓이는 상위 폴더와 호출 문법이 다르므로, 저장소 루트 기준 경로(`skills/<name>/SKILL.md`)나 특정 URI(`skill://<name>`)에 의존하면 다른 환경에서 깨집니다.

| 런타임 | 프로젝트 스킬 경로 | 사용자 전역 스킬 경로 | 확인된 `npx skills` 설치 명령 |
|---|---|---|---|
| omp | `.agents/skills/<name>/` | `~/.omp/agent/skills/<name>/` | `npx skills add alpoxdev/hypercore -a codex` (프로젝트 단위. `skills@1.9.0`에서 `-a omp`는 미지원) |
| Antigravity (`agy`) | `.agents/skills/<name>/` | `~/.gemini/config/skills/<name>/` | `npx skills add alpoxdev/hypercore -a antigravity-cli -g` (또는 `-a antigravity`, 프로젝트 설치는 `-g` 생략) |
| Claude Code | `.claude/skills/<name>/` (또는 플러그인 `skills/`) | `~/.claude/skills/<name>/` | `npx skills add alpoxdev/hypercore -a claude-code -g` (또는 `claude plugin install hypercore@alpoxdev`) |
| Codex | `.agents/skills/<name>/` | `~/.agents/skills/<name>/` | `npx skills add alpoxdev/hypercore -a codex -g` (`$CODEX_HOME/skills`는 주 경로가 아님) |

**스킬 간 상호 참조 표준**:

1. 위 네 환경 모두 같은 묶음으로 설치된 형제 스킬을 같은 상위 `skills/` 폴더 아래 나란히 둡니다.
2. 오케스트레이터나 인계 규칙이 다른 Hypercore 스킬을 열 때는 현재 스킬 폴더 기준 상대 경로 **`../<skill>/SKILL.md` 읽기**를 표준으로 씁니다(런타임 스킬 로더가 있으면 동등한 단축 경로로 병행 가능).
3. `../<skill>/SKILL.md`를 연 뒤에는 머리말의 `name`이 `<skill>`과 일치하는지 확인하고, 그 스킬의 `rules/`, `references/`, `scripts/`, `assets/`는 `../<skill>/` 기준으로 해석합니다.

## 3. 이식 가능한 머리말(Frontmatter) 계약

- **필수 공통 키**: 모든 에이전트가 공통으로 읽는 `name`과 `description` 두 키만 필수로 둡니다.
- **선택 확장 키**: `compatibility`, `license`, `metadata`, `allowed-tools`, 런타임 전용 스위치(`disable-model-invocation`)는 선택 사항이며, 이를 무시하는 환경에서도 본문만으로 계약이 그대로 성립해야 합니다.
- **안전한 따옴표 강제**: `SKILL.md`와 `SKILL.ko.md` 머리말의 모든 단일 문자열 값(`name`, `description`, `compatibility`, `license`)은 항상 큰따옴표(또는 유효한 블록 스칼라)로 감싸 `: `나 ` #`가 들어가도 파서가 깨지지 않게 합니다(`scripts/check-skill-frontmatter.sh`가 검사).

## 4. 환경별 직접 검증 범위와 추정 표시

| 런타임 | 이 기기에서 직접 확인한 항목 (2026-11-23) | 문서 기준·추정(`추정`) 항목 |
|---|---|---|
| omp | `omp --help`(`v19.1.0`), `~/.omp/agent/` 구조, 헤드리스 이어받기 통과 기록(`omp/18.18.6`), `-a codex` 프로젝트 설치 | 향후 버전의 내부 도구 파라미터 세부 변경(추정) |
| Antigravity (`agy`) | 현재 세션 도구 선언(`read_file`, `write_file`, `edit_file`, `run_command`, `invoke_subagent`, `ask_question`, `run_workflow`), 내장 `agy-customizations` 탐색 규칙, 격리 `/tmp`에서 `skills@1.9.0` `-a antigravity`·`-a antigravity-cli` 설치 실측 | 데스크톱 IDE 빌드별 UI 전용 슬래시 명령 차이(추정) |
| Claude Code | 격리 `/tmp`에서 `skills@1.9.0` `-a claude-code` 설치 실측(`.claude/skills`), `.claude-plugin/` 매니페스트 검증 | 이 맥미니에는 `claude` 실행 파일이 설치돼 있지 않음(`not_run`). `Read`·`Edit`·`Bash`·`Agent`·`AskUserQuestion` 및 v2.1.277+ `AGENTS.md` 동작은 Anthropic 공식 문서 기준이며 실기기 세부 플래그 동작은 추정 표시 |
| Codex | 로컬 `codex --help` 및 `codex exec --help`, 격리 `/tmp`에서 `skills@1.9.0` `-a codex` 설치 실측(`.agents/skills`) | 내부 하네스 도구 이름(`apply_patch`, `spawn_agent`, `request_user_input`)은 `--help`에 출력되지 않으므로 OpenAI Codex 문서 기준이며 모드별 노출 차이는 추정 표시 |

## Sources

> Checked 2026-11-23.

| Claim | Source |
|---|---|
| `skills@1.9.0` 에이전트 대상(`antigravity`, `antigravity-cli`, `claude-code`, `codex`, `cursor`, `pi`)과 프로젝트·전역 설치 경로 | 로컬 `npx skills --version`(`1.9.0`), `skills/dist/remove.mjs` 확인, 격리 `/tmp` 설치 실측, 2026-11-23 |
| `omp v19.1.0` CLI 플래그 및 `.agents/skills`·`~/.omp/agent/skills` 로딩 | 로컬 `omp --help`(`v19.1.0`), 2026-11-23; <https://raw.githubusercontent.com/can1357/oh-my-pi/main/docs/skills.md> (확인 2026-11-10) |
| Antigravity 도구 선언과 `.agents/`·`~/.gemini/config/` 탐색 우선순위 | 현재 Antigravity 세션 도구 선언 및 내장 `agy-customizations` 문서, 2026-11-23 |
| Claude Code 도구, `.claude/skills`, `CLAUDE.md`·`AGENTS.md` 우선순위 및 머리말 검증 | <https://code.claude.com/docs/en/skills>, <https://code.claude.com/docs/en/sub-agents>, `instructions/context-engineering/references/runtime-profiles.ko.md` (확인 2026-11-08) |
| Codex CLI 명령(`codex exec`, `resume`, `review`, `mcp`)과 `.agents/skills`·`agents/openai.yaml` | 로컬 `codex --help`·`codex exec --help`, 2026-11-23; <https://learn.chatgpt.com/docs/build-skills> (확인 2026-11-08) |

### Evidence grade

`LOCAL` (`omp`, `Antigravity`, `codex --help`, `npx skills@1.9.0` 격리 설치 실측, 2026-11-23) 및 `EXTERNAL-VENDOR-DOC` (이 기기에 설치되지 않은 `Claude Code` CLI 실행 세부와 `Codex` 내부 도구 스키마는 공식 문서 기준 및 추정 명시).
