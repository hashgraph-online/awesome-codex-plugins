# 검증

> 관찰한 실행으로 MCP 결과를 증명하고, 모드별 점검 목록을 실행하며, 보고서가 디스크의 파일과 맞을 때만 닫습니다.

## 1. Inspector 실행

MCP Inspector CLI는 프로세스마다 메서드 하나를 실행하고 문서화된 종료 코드로 끝납니다. 기본 프로토콜 era가 `legacy`이므로 `--protocol-era`(`legacy`, `auto`, `modern`)로 era를 항상 고정합니다.

```bash
# stdio server built from this repository: the server command is positional
npx @modelcontextprotocol/inspector --cli node build/index.js --protocol-era modern --method tools/list
npx @modelcontextprotocol/inspector --cli node build/index.js --protocol-era modern --method tools/list --strict

# Streamable HTTP server on loopback
npx @modelcontextprotocol/inspector --cli http://127.0.0.1:<port>/mcp --transport http --protocol-era modern --method tools/list

# one read-only tool call
npx @modelcontextprotocol/inspector --cli <server> --protocol-era modern --method tools/call --tool-name <read_only_tool> --tool-arg <key>=<value>

# dual-era target: repeat the list call with --protocol-era legacy
```

`node build/index.js`는 대상의 실제 시작 명령으로 바꿉니다. 플래그 이름은 기대기 전에 설치된 Inspector의 `--help`로 확인합니다(`references/build-test-ship.md`가 문서화된 종료 코드를 기록합니다). 비대화형 실행에는 `--stored-auth-only`를 붙여 Inspector가 OAuth 흐름을 시작하지 않게 하고, 다른 단계가 출력을 파싱하면 `--format json`을 붙입니다.

| Exit code | Meaning for the run |
|---|---|
| 0 | 통과 |
| 3 | 인가 필요: 멈추고 묻습니다. 사용자 대신 로그인하지 않습니다 |
| 4 | 연결 불가: 서버가 시작하지 않았거나 다른 곳에서 듣고 있습니다 |
| 5 | 도구 오류 또는 도구를 찾지 못함 |
| 6 | `--strict`가 도구 스키마 이식성 오류를 찾음 |
| 그 밖의 0이 아닌 값 | `stderr`의 한 줄 JSON 오류를 읽고 기록합니다 |

Inspector를 실행할 수 없으면(Node.js 22.19+ 없음, `npx`용 네트워크 없음, 자격 증명이 필요한 서버) 사유와 함께 `not run`을 기록하고 프로젝트 자체 테스트와 `rules/mcp-rules.md`에 대한 정적 리뷰로 대체합니다. 정적 리뷰는 검사를 `passed`로 올리지 않습니다.

## 2. 모드별 검사

| Mode | Required checks |
|---|---|
| build | 프로젝트 빌드와 테스트가 통과하고, 선언한 모든 era에서 Inspector 목록 호출이 통과하며, `--strict`가 통과하고, 읽기 전용 도구 호출 하나가 기대한 모양을 돌려주며, 잘못된 입력 호출 하나가 `isError: true`를 돌려주고, 배포 형태에 대한 보안 점검 목록(§3)을 통과합니다 |
| audit | `rules/mcp-rules.md`의 모든 규칙이 근거와 함께 `pass`, 발견, `not applicable` 가운데 하나로 표시되고, 자격 증명이 필요 없는 읽기 전용 런타임 검사를 마칩니다 |
| fix | audit 검사를 실행한 뒤 고친 발견마다 그 규칙이 지목한 관찰로 다시 검사합니다. 이전에 통과한 검사가 하나도 실패하지 않아야 합니다 |
| migrate | 마이그레이션 체크리스트 항목을 모두 기록하고, 의도한 dual-era 계층 밖에 legacy 표식이 남지 않았고, 선언한 era마다 Inspector가 통과하며 프로젝트 테스트가 통과합니다 |
| connect | 설정이 파싱되고 어떤 파일에도 리터럴 비밀이 없으며 호스트가 서버 도구를 나열하고 승인과 허용 목록이 작업과 맞습니다 |
| publish | `server.json`이 선언한 스키마로 검증되고 소유 표식이 있으며 버전이 새것이고 게시 명령은 명시적 요청에서만 실행됐습니다 |

## 3. 보안 점검 목록

- [ ] 소스, 설정, URL, 로그, 보고서에 리터럴 자격 증명이 없습니다(MCP-S-5).
- [ ] stdio 서버: 자격 증명은 환경에서 오고 `stdout`은 MCP 메시지만 나릅니다(MCP-P-5).
- [ ] 로컬 HTTP: `Origin`을 검증하고 루프백에 바인딩하며 인증을 요구합니다(MCP-S-4).
- [ ] 원격: 인가 프로필이 완비됐고 요청마다 토큰 대상을 검증합니다(MCP-S-2, MCP-S-3).
- [ ] 핸들과 `requestState`는 무작위이고 만료되며 사용자에 묶이고, 중요한 곳에서 무결성을 보호합니다(MCP-S-7, MCP-P-4).
- [ ] 모든 도구 설명을 읽었고 무관한 지시가 없습니다(MCP-D-8).
- [ ] connect 모드: 서드파티 서버는 버전을 고정하고 격리했으며 쓰기와 외부 통신에 승인을 켰습니다(MCP-S-1, MCP-U-3).

## 4. 보고서 게이트

실행을 닫기 전에 확인합니다.

- [ ] `.hyper/mcp/<slug>/report.md`가 있고 `변경` 표의 바뀐 파일이 모두 그 변경과 함께 존재합니다.
- [ ] 검사 행마다 `passed`, `failed`, `not run` 가운데 하나이고 `passed` 행은 그것을 낸 명령을 밝힙니다.
- [ ] 범위 안의 critical, high 발견이 모두 닫혔거나 `남은 위험`에 막는 요인과 함께 실렸습니다.
- [ ] 수정 루프가 두 번 안에서 끝났고 되돌린 수정을 기록했습니다.
- [ ] `rules/mcp-workflow.md` §4의 게이트가 걸린 행동을 사용자의 명시적 요청 없이 실행하지 않았습니다.

## 5. 패키지 변경

이 패키지 자체가 바뀌면 `skills/hyper-mcp`에 저장소의 스킬 전용 검증기를 `assets/evals/hyper-mcp-cases.jsonl`과 함께 실행하고, 저장소 검증 게이트와 바뀐 파일마다의 영어/한국어 구조 패리티 검사를 실행합니다.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Inspector 클라이언트, `legacy` 기본 era, 메서드 하나짜리 CLI, 종료 코드, `--stored-auth-only` | `references/build-test-ship.md` |
| 보안 검사 | `references/security-and-authorization.md`, `rules/mcp-rules.md` |
| 모드별 검사와 보고서 게이트 | 이 패키지가 고른 설계이며 검증된 최적값이 아님 |
