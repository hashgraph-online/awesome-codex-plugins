# MCP 워크플로

> 파일에서 MCP 표면을 판별하고, 모드를 하나 골라 그 모드의 단계를 부수 효과 게이트 안에서 실행한 뒤 한국어 보고서 하나를 저장합니다.

## 1. 표면 판별

신호가 지목한 파일만 읽습니다. 각 사실은 그것을 입증하는 파일과 함께 기록합니다.

| Fact | Where to look | Signals |
|---|---|---|
| 서버 또는 클라이언트 SDK와 그 계열 | `package.json`, `pyproject.toml` / `requirements*.txt`, `go.mod`, `*.csproj`, `Cargo.toml`, `Gemfile`, `pom.xml` / `build.gradle*` | TypeScript `@modelcontextprotocol/server` 또는 `@modelcontextprotocol/client`(v2, 현재 판) 대 `@modelcontextprotocol/sdk`(v1, 핸드셰이크 era); Python `mcp` 2.x 대 1.x; 공식 Go, C#, Rust, Ruby, Java, Kotlin, Swift, PHP SDK |
| 역할 | import와 진입점 | 도구, 리소스, 프롬프트를 등록하는 서버 객체; `callTool`, `listTools` 또는 그에 해당하는 것을 호출하는 클라이언트 객체 |
| 트랜스포트 | 서버 시작 코드, 호스트 설정 | stdio(`serveStdio`, stdio 트랜스포트, 호스트 설정의 `command`/`args`) 또는 Streamable HTTP(HTTP 라우트, 호스트 설정의 `url`). HTTP+SSE(`/sse` 엔드포인트, `type: sse`)는 폐기 예정 |
| era | 소스와 의존성 | modern: 요청별 `_meta`, `server/discover`. legacy: `initialize` 핸들러, `Mcp-Session-Id`, 서버가 시작하는 `sampling`/`elicitation`/`roots` 요청, `resources/subscribe`. dual-era: 둘 다 |
| 호스트 설정 | 저장소 루트와 요청이 지목한 사용자 수준 파일 | `.mcp.json`, `.vscode/mcp.json`, `.cursor/mcp.json`, `.codex/config.toml`, `claude_desktop_config.json` |
| 레지스트리 메타데이터 | 저장소 루트 | `server.json`, `package.json`의 `mcpName`, README의 `mcp-name:` 줄 |

MCP 신호가 전혀 없고 요청이 build가 아니면 멈춥니다. 요청에 MCP 표면이 없는 것입니다. 무엇을 검색했는지 보고합니다.

## 2. 모드 선택

| Mode | Choose it when | Edits allowed |
|---|---|---|
| build | 사용자가 새 서버, 클라이언트, 새 도구를 요청합니다 | 새로 쓴 MCP 코드와 바꾼 MCP 코드, 테스트, 사용자가 요청한 호스트 진입점 |
| audit | 사용자가 리뷰, 점검, 보고만 요청하거나 호출자가 "audit only; report findings; do not edit"를 넘깁니다 | `.hyper/mcp/<slug>/` 밖에는 없습니다 |
| fix | 사용자가 리뷰와 수정을 요청합니다 | 범위 안의 발견을 닫는 변경 |
| migrate | 대상이 legacy나 dual-era이고 사용자가 갱신을 요청하거나, build나 fix가 남길 수 없는 legacy 코드를 건드립니다 | 마이그레이션 체크리스트를 구현하는 변경 |
| connect | 사용자가 호스트에서 MCP 서버를 추가, 범위 지정, 보안 설정, 복구하려고 합니다 | 호스트 설정 파일과 그 파일이 참조하는 환경 변수 이름 |
| publish | 사용자가 레지스트리 메타데이터를 준비하거나 게시하려고 합니다 | `server.json`과 소유 표식 |

보고 전용 표현("점검만", "고치지 말고", "report only", "audit only")은 audit 모드를 강제합니다. 모드 둘을 지목한 요청은 migrate, fix, connect, publish 순서로 실행하고 둘 다 기록합니다.

## 3. 모드별 단계

### build

1. 배포 형태를 고르고(원격 API를 감싸는 것은 무엇이든 원격 Streamable HTTP, 서버가 사용자 기기에서 돌아야 할 때만 로컬 stdio) 그 이유를 기록합니다. `references/build-test-ship.md`가 그 표를 소유합니다.
2. 문서가 현재 판 지원을 밝힌 SDK를 고르고 대상 저장소의 언어를 우선합니다. SDK의 등급과 지원하는 판을 기록합니다.
3. 코드보다 도구 표면을 먼저 설계합니다. 작업 모양의 도구 몇 개, 이름, 입력과 출력 스키마, 오류 메시지, 응답 상한입니다(`references/server-design.md`). 설계를 보고서에 씁니다.
4. SDK의 현재 판 진입점으로 구현합니다. TypeScript stdio라면 문서가 이름 붙인 팩토리 기반 serve 함수이며 손으로 연결한 트랜스포트가 아닙니다.
5. 배포 형태에 필요한 보안 통제를 넣습니다(`references/security-and-authorization.md`). 원격 서버는 인가, 로컬 HTTP는 `Origin` 검증과 루프백 바인딩, stdio는 환경 변수로 받는 자격 증명입니다.
6. 검증(`rules/validation.md`)한 뒤 루프 예산 안에서 수정합니다.

### audit

1. `rules/mcp-rules.md`를 순서대로 훑습니다. 프로토콜, 설계, 보안, 호스트 사용 순서입니다.
2. 해당하는 규칙마다 `pass`, 발견, `not applicable` 가운데 하나를 근거와 함께 기록합니다.
3. 자격 증명이 필요 없는 읽기 전용 검사를 실행합니다. 이 저장소로 빌드한 서버에 Inspector로 목록 메서드 호출, 스키마와 설정 읽기, 의존성 버전 읽기입니다.
4. 발견을 심각도로 정렬하고 보고서를 씁니다. 그 밖에는 아무것도 수정하지 않습니다.

### fix

audit의 1~3단계를 실행한 뒤 critical, high, medium 발견을 그 순서로 범위 안에서 고치고 검증한 뒤 루프 예산 안에서 수정합니다. low 발견은 사용자가 전부 요청하지 않는 한 제안 변경과 함께 보고합니다.

### migrate

1. legacy 의존성을 모두 목록으로 만듭니다. `initialize`, 세션, 연결별 상태, 서버가 시작하는 요청, `resources/subscribe`, `ping`, `logging/setLevel`, `Last-Event-ID`, 릴리스 후보 오류 코드입니다.
2. modern-only와 dual-era 가운데 하나를 정합니다. 사용자가 통제하지 않는 클라이언트가 아직 legacy 판을 쓰는 경우에만 dual-era를 고르고 어느 클라이언트인지 기록합니다.
3. SDK 계열을 올린 뒤 `references/protocol-2026-07-28.md`의 마이그레이션 체크리스트를 항목별로 적용하고 항목마다 보고서에 기록합니다.
4. 대상이 선언할 모든 era에서 검증합니다.

### connect

1. 호스트의 설정 표면과 범위 규칙을 읽습니다(`references/host-integration.md`). 공용이고 검토한 서버는 프로젝트 파일에, 개인용이나 실험용 서버는 사용자 범위에 둡니다.
2. 원격 API만 감싸는 서버라면 그 서버의 원격 Streamable HTTP 엔드포인트를 우선합니다.
3. 로컬 서버라면 배포자, 정확한 패키지 이름, 고정한 버전이나 이미지 다이제스트를 확인하고 정확한 실행 명령을 보고서에 보여 줍니다.
4. 자격 증명은 환경 변수나 호스트의 비밀 저장소로 참조합니다. 토큰 값을 파일에 쓰지 않습니다.
5. 도구 목록을 사용자 작업에 필요한 범위로 좁히고(허용 목록, 비활성 도구) 쓰기나 외부 통신을 하는 도구는 승인을 켜 둡니다.
6. 호스트가 서버 도구를 나열할 수 있는지 확인합니다. 읽기 전용 도구만 호출하고, 그 서버 실행을 사용자가 승인했을 때만 호출합니다.

### publish

1. 네임스페이스가 계획한 인증 방식과 맞는지, 패키지 유형에 맞는 소유 표식이 있는지 확인합니다.
2. 패키지 버전과 맞는 고유하고 바꿀 수 없는 버전으로 `server.json`을 쓰거나 갱신합니다. 원격 엔드포인트는 Streamable HTTP로 공개 접근이 가능할 때만 싣습니다.
3. 메타데이터를 로컬에서 검증합니다. 이 요청에서 사용자가 게시를 명시적으로 요청했을 때만 게시 명령을 실행하고, 아니면 사용자가 실행할 정확한 명령을 보고합니다.

## 4. 부수 효과 게이트

| Action | Gate |
|---|---|
| 대상 저장소 안에 의존성 설치 | build, fix, migrate에서 허용합니다. 저장소가 이미 쓰는 방식으로 버전을 고정합니다 |
| 검증을 위해 이 저장소로 빌드한 서버 시작 | 허용합니다. 루프백에 바인딩하고 검사가 끝나면 중지합니다 |
| 서드파티 서버 시작 | 사용자가 이름을 댄 서버만, 고정한 버전으로, 그 도구 설명을 읽은 뒤에 시작합니다. 아니면 멈추고 묻습니다 |
| OAuth 로그인, 실제 토큰 사용, 프로덕션 엔드포인트 호출 | 멈추고 묻습니다. 로그인은 사용자가 합니다 |
| 쓰기, 삭제, 전송, 과금 도구 호출 | 검증 중에는 하지 않습니다 |
| 레지스트리나 패키지 인덱스에 게시 | 이번 실행에서 사용자가 명시적으로 요청했을 때만 합니다 |
| 커밋이나 푸시 | 이 스킬의 행동이 아닙니다. 바뀐 파일을 보고합니다 |

## 5. 보고

`.hyper/mcp/<slug>/report.md`를 씁니다. `<slug>`는 대상과 작업을 짧게 줄인 kebab-case 이름입니다. 같은 이름의 파일이 다른 작업으로 이미 있으면 `-2`, `-3`을 붙입니다. 코드, 경로, 규칙 ID, 명령을 뺀 나머지는 한국어로 씁니다.

```markdown
# <대상> MCP <모드> 보고

- 요청: <the user's request, verbatim>
- 모드: build | audit | fix | migrate | connect | publish
- 대상: <paths>
- 감지: SDK <name@version> (<file>), 역할 <server|client|host>, 트랜스포트 <stdio|streamable-http|http+sse>, era <modern|legacy|dual-era> (<evidence>)

## 결과 요약
<three lines at most: what is now true, what is still open>

## 발견
| ID | 규칙 | 심각도 | 위치 | 근거 | 조치 |
|---|---|---|---|---|---|

## 변경
| 파일 | 변경 내용 | 닫은 발견 |
|---|---|---|

## 검증
| 검사 | 명령 | 결과 | 비고 |
|---|---|---|---|

## 남은 위험
- <risk and the action that would close it>
```

audit 모드에서는 `변경` 표에 행 하나만 남깁니다: `없음 (점검 전용)`.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| SDK 패키지 이름, 현재 판 계열, TypeScript serve 진입점 | `references/build-test-ship.md` |
| legacy 표식, 마이그레이션 체크리스트, era 선택 | `references/protocol-2026-07-28.md` |
| 호스트 설정 파일과 범위 규칙 | `references/host-integration.md` |
| 로컬 서버 검증, 자격 증명 처리, 게이트가 걸린 행동 | `references/security-and-authorization.md` |
| 모드, 단계 순서, 게이트 표, 보고서 형태 | 이 패키지가 고른 설계이며 검증된 최적값이 아님 |
