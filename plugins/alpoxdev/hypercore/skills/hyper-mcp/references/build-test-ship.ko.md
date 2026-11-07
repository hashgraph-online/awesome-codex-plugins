# 빌드, 테스트, 배포

MCP 서버나 클라이언트 설계를 `2026-07-28`을 대상으로 하는 동작 코드로 바꾸고 참조 도구로 동작을 증명하고 배포하는 방법이다. SDK 선택, 최소 골격, 인스펙터 기반 점검, 디버깅 순서, 레지스트리 배포를 소유한다. 도구와 리소스 설계는 [`server-design.ko.md`](server-design.ko.md)에 있다.

> 영어판: [`build-test-ship.md`](build-test-ship.md)

## 목차

- Choose the deployment shape first
- Choose an SDK by tier and revision
- Minimal server contract
- Test with the inspector
- Debug in this order
- Publish

## Choose the deployment shape first

공식 서버 구축 안내서는 코드보다 배포 모델을 먼저 고르게 한다(agent-skills 안내서, 2026-11-07 확인).

| 형태 | 쓰는 때 | 감수하는 비용 |
|---|---|---|
| 원격, Streamable HTTP | 서버가 클라우드 API를 감싸거나 많은 사용자에게 서비스할 때. 안내서는 이를 "클라우드 API를 감싸는 모든 것의 기본값"이라고 부른다 | HTTP 인가([`security-and-authorization.ko.md`](security-and-authorization.ko.md)), 호스팅, 속도 제한 |
| 로컬, stdio | 프로토타이핑, 또는 서버가 사용자 머신(파일, 로컬 앱)을 필요로 할 때 | 호스트의 권한으로 실행된다. 프로토콜 경계가 없다 |
| 로컬, MCP 번들 (`.mcpb`) | 런타임을 설치하지 않을 사람에게 로컬 서버를 배포할 때 | 번들마다 패키징과 서명 |
| MCP 앱(확장) | 결과물이 호스트 안에서 렌더링되는 상호작용 UI일 때 | 그 확장을 구현한 호스트만 렌더링한다 |

## Choose an SDK by tier and revision

SDK 등급 정책은 인기가 아니라 적합성과 유지보수를 평가한다(SDK 등급 페이지, 2026-11-07 확인).

| 등급 | SDK | 등급이 보장하는 것 |
|---|---|---|
| 1 | TypeScript, Python, C#, Go, Rust, Ruby | 적합성 테스트 100%. 명세 출시 전 신규 명세 기능. 영업일 2일 안 트리아지. 7일 안 치명적 버그 |
| 2 | Java | 적합성 80%. 6개월 안 신규 기능 |
| 3 | Swift, PHP, Kotlin | 적합성 하한 없음 |

- 등급이 판 지원을 뜻하지는 않는다. "SDK는 각자의 일정에 따라 새 프로토콜 판을 받아들인다"는 말이므로, 어느 판을 말하는지는 SDK 자체 문서에서 읽는다. Java와 Kotlin 퀵스타트는 여전히 `2025-11-25` 서버를 만들고 현대 전용 클라이언트는 그 서버에 닿지 못한다(SDK 페이지와 퀵스타트, 2026-11-07 확인).
- Tasks와 MCP 앱 같은 확장은 "어느 등급에도 필수가 아니다". 1등급 SDK도 이것을 갖추지 못할 수 있다. Python SDK v2는 Tasks API가 "이 SDK가 아직 구현하지 않은" 것 가운데 하나라고 밝힌다(2026-11-07 확인).
- TypeScript: v2는 `@modelcontextprotocol/server`와 `@modelcontextprotocol/client`로 배포되고 `2026-07-28`을 구현한다. v1(`@modelcontextprotocol/sdk`)은 2026-07-27 v2 출시 뒤 최소 6개월 동안 `v1.x` 브랜치에 남는다(SDK README, 2026-11-07 확인).
- Python: v2는 "2026-07-28 판을 구현하고 **두** 판을 동시에 서비스한다". `FastMCP`는 `MCPServer`로 이름이 바뀌었다. 서버 튜토리얼은 SDK 2.0.0 이상을 요구한다(2026-11-07 확인).

## Minimal server contract

어떤 SDK를 쓰든 `2026-07-28` 서버는 아래가 모두 성립할 때만 완성이다. 각 항목은 스타일 선호가 아니라 [`protocol-2026-07-28.ko.md`](protocol-2026-07-28.ko.md)의 프로토콜 규칙이다.

- [ ] `server/discover`가 지원 버전, 능력, `serverInfo`, 캐싱 힌트로 응답한다.
- [ ] 모든 핸들러가 버전과 클라이언트 능력을 연결 상태가 아니라 요청의 `_meta`에서 읽는다.
- [ ] stdio에서는 MCP 메시지 말고는 무엇도 `stdout`에 닿지 않는다. 구축 안내서는 이렇게 못 박는다. "stdout에 절대 쓰지 마라. stdout에 쓰면 JSON-RPC 메시지가 깨지고 서버가 망가진다"(2026-11-07 확인). `stderr` 로거를 쓴다(`console.error`, Python `logging`, stderr로 보내는 SLF4J).
- [ ] 도구 실패는 읽을 수 있는 텍스트와 함께 `isError: true`를 반환한다. 클라이언트 SDK는 이를 예외가 아니라 결과로 보고한다. "실패하는 도구가 예외를 던질 것이라 기대하지 말고 `result.isError`를 확인하라"(클라이언트 안내서, 2026-11-07 확인).
- [ ] HTTP에서는 `Origin`을 검증하고 필수 `Mcp-*` 헤더를 본문과 대조한다.

SDK별 배선은 어느 era를 지원하는지를 좌우한다. TypeScript 서버 안내서에 따르면 `serveStdio(createServer)`는 "각 클라이언트와 프로토콜 판을 협상하므로 같은 서버가 2026-07-28 클라이언트와 아직 2025년 판의 `initialize` 핸드셰이크로 여는 클라이언트 모두에 응답한다". 반면 `server.connect(new StdioServerTransport())`로 손수 배선한 서버는 "2025년 판 클라이언트만 지원한다"(2026-11-07 확인). SDK README의 시작하기 예제는 그런 단서 없이 손수 배선한 형태를 여전히 보여준다. 문서 사이트를 권위로 삼고 아래 modern era 인스펙터 실행으로 확인한다.

## Test with the inspector

MCP 인스펙터는 웹, CLI, 터미널 UI 세 클라이언트를 한 패키지로 제공하고 Node 22.19.0 이상이 필요하다(인스펙터 페이지, 2026-11-07 확인).

- **era를 고정한다.** 인스펙터의 기본 프로토콜 era는 `legacy`다. "`initialize`만 쓰고 탐색은 전혀 하지 않는데", "디버깅 도구가 자동으로 탐색해서는 안 되기" 때문이다. `2026-07-28`을 시험하려면 `--protocol-era modern`을 넘긴다. 기본 era로 성공한 실행으로는 현재 판을 확인할 수 없다(protocol-eras 페이지, 2026-11-07 확인). dual-era 서버는 era마다 한 번씩 실행해야 한다.
- **스크립트로 돌린다.** CLI는 프로세스마다 메서드 하나만 실행하고(`--method tools/list`, `tools/call`, `resources/read`, `prompts/get` 등) 결과를 출력한 뒤 종료한다. CI 작업이 원하는 형태다.
- **종료 코드로 분기한다.** `0` 성공, `3` 인가 필요, `4` 접근 불가, `5` 도구 오류 또는 도구 없음, `6` `--strict`가 오류 등급의 도구 스키마 이식성 문제를 찾음, `11` HTTP 429. 0이 아닌 종료는 모두 `stderr`에 JSON 한 줄도 쓴다(CLI 페이지, 2026-11-07 확인).
- **CI를 비대화형으로 유지한다.** `--stored-auth-only`는 대화형 OAuth 흐름을 시작하지 않는다. `--format json`은 출력을 기계가 읽을 수 있게 한다. `--strict`는 스키마 이식성 발견을 실패로 바꾼다.

인스펙터 자체가 보안 사고였다. 0.14.1 미만 버전은 웹 페이지에서 닿을 수 있는 인증 없는 프록시를 노출했다(CVE-2025-49596, 2025-06-13 게재). 최신으로 유지하고 루프백에 묶는다([`security-and-authorization.ko.md`](security-and-authorization.ko.md)).

인스펙터 점검은 프로토콜 적합성을 다룬다. 모델이 알맞은 도구를 고르고 오류에서 회복하는지는 별도 평가다. [`server-design.ko.md`](server-design.ko.md)를 본다.

## Debug in this order

디버깅 안내서가 도구 순서를 정한다. 호스트에서 시작하지 말고 그 순서를 따른다(2026-11-07 확인).

1. **인스펙터**를 올바른 era로 서버에만 붙인다. 서버 버그를 호스트 버그와 분리한다.
2. **서버 로그.** stdio 서버는 `stderr`에 기록하고 호스트가 흔히 이를 수집한다(Claude Desktop은 `mcp-server-SERVERNAME.log`를 쓴다). Streamable HTTP는 수집되는 `stderr`가 없으므로 자체 로그 집계나 OpenTelemetry를 쓴다. `notifications/message`로 남기는 프로토콜 수준 로깅은 폐기 예정(Deprecated)이고 요청의 `logLevel`에 걸린다.
3. **호스트 설정.** 절대 경로를 쓴다(stdio 서버의 작업 디렉터리는 정의되지 않을 수 있다). 필수 환경 변수는 명시적으로 넘긴다. stdio 서버는 제한된 환경 변수 일부만 물려받기 때문이다.
4. **오류 코드.** `-32022` 지원하지 않는 버전(그 `supported` 목록을 읽는다), `-32602` 빠진 `_meta` 필드나 잘못된 파라미터, `-32021` 서버가 선언하지 않은 클라이언트 능력을 요구한다.

## Publish

### MCP Registry

레지스트리는 공개 서버를 위한 프로젝트의 메타데이터 카탈로그다(레지스트리 페이지, 2026-11-07 확인).

| 사실 | 결과 |
|---|---|
| "MCP 레지스트리는 현재 프리뷰다." | 배포 흐름에 호환성을 깨는 변경을 예상한다. |
| 코드가 아니라 메타데이터를 저장하고 "비공개 서버를 지원하지 않는다". | 내부 서버는 비공개 카탈로그나 애그리게이터가 필요하다. |
| "호스트 애플리케이션이 직접 소비하도록 의도되지 않았다". | 호스트는 자체 선별을 더하는 애그리게이터로 읽는다. |
| 네임스페이스는 인증 방식을 따른다. GitHub 로그인은 `io.github.<user-or-org>/*`, DNS나 HTTP 도메인 증명은 역 DNS 이름이다. | 첫 배포 전에 네임스페이스를 고른다. |
| 소유권은 패키지 유형마다 증명한다. npm은 `package.json`의 `mcpName`, PyPI·NuGet·crates.io는 README에 보이는 `mcp-name:` 줄, OCI는 이미지 레이블, MCPB는 "mcp"를 포함한 URL과 `fileSha256`이다. | 패키지 자체를 배포하기 전에 표시를 넣는다. |
| 버전은 "배포마다 고유해야 한다(**MUST**)"고 나중에 바꿀 수 없다. 버전 범위는 금지된다. | 배포한 `server.json`은 불변으로 다루고 되돌리지 말고 다음 버전에서 고친다. |
| 운영 심사는 "불법 콘텐츠, 악성코드, 스팸, 완전히 망가진 서버"를 제거하고 보안 취약점이 있는 서버는 명시적으로 제거하지 않는다. | 레지스트리 등재는 보안 검토가 아니다. |

`server.json` 스키마는 자체 날짜를 갖는다(퀵스타트에서는 `2025-12-11`). 이 날짜는 프로토콜 판이 아니라 레지스트리 형식의 버전이다.

### Before you publish

- [ ] 서버가 `server/discover`에 응답하고 자기가 지원한다고 밝힌 모든 era에서 인스펙터 실행을 통과한다.
- [ ] `remotes`에 나열한 원격 서버가 Streamable HTTP로 공개 접근 가능하다. 레지스트리는 폐기 예정인 `sse` 유형을 여전히 받지만 새 SSE 엔드포인트를 배포하지 않는다.
- [ ] 도구 이름, 설명, annotation이 이 버전에서 최종이다. 호스트와 프롬프트 캐시가 이것을 키로 삼으므로 나중에 바꾸면 연결된 모든 호스트에서 캐시가 깨진다.
- [ ] [`security-and-authorization.ko.md`](security-and-authorization.ko.md)의 보안 점검 목록을 통과한다.

## Sources

> 확인 2026-11-07. URL이 달리 말하지 않는 한 문서 페이지는 `2026-07-28` 판이다.

| 주장 | 출처 | 게재 |
|---|---|---|
| 배포 경로와 원격 기본값 | <https://modelcontextprotocol.io/docs/2026-07-28/develop/build-with-agent-skills> | 날짜 없음 |
| 서버 골격, `stdout` 규칙, `serveStdio`의 era 지원 범위, Python SDK 2.0.0 | <https://modelcontextprotocol.io/docs/2026-07-28/develop/build-server> | 날짜 없음 |
| 클라이언트 수명 주기, 예외가 아니라 결과로 반환되는 `isError` | <https://modelcontextprotocol.io/docs/2026-07-28/develop/build-client> | 날짜 없음 |
| SDK 목록과 판 주의 | <https://modelcontextprotocol.io/docs/2026-07-28/sdk> | 날짜 없음 |
| 등급 정의, 적합성 하한, 필수가 아닌 확장 | <https://modelcontextprotocol.io/community/sdk-tiers> | 날짜 없음 |
| TypeScript v2 패키지와 v1 지원 기간 | <https://github.com/modelcontextprotocol/typescript-sdk> | v2 2026-07-27 |
| Python v2 이중 판 지원, `MCPServer` 개명, Tasks 미구현 | <https://py.sdk.modelcontextprotocol.io/whats-new/> | 날짜 없음 |
| 인스펙터 클라이언트와 Node 요구 사항 | <https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector> | 날짜 없음 |
| CLI 메서드 모델, 종료 코드, CI 플래그 | <https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector/cli> | 날짜 없음 |
| 기본 era `legacy`, 자동 탐색 없음 | <https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector/protocol-eras> | 날짜 없음 |
| 디버깅 순서, 로그 위치, 절대 경로 | <https://modelcontextprotocol.io/docs/2026-07-28/tools/debugging> | 날짜 없음 |
| 레지스트리 프리뷰 상태, 비공개 서버 없음, 호스트 직접 사용 아님 | <https://modelcontextprotocol.io/registry/about> | 날짜 없음 |
| 패키지 유형별 소유권 표시 | <https://modelcontextprotocol.io/registry/package-types> | 날짜 없음 |
| 인증 방식별 네임스페이스 | <https://modelcontextprotocol.io/registry/authentication> | 날짜 없음 |
| 불변 버전, 범위 금지 | <https://modelcontextprotocol.io/registry/versioning> | 날짜 없음 |
| stdio `stderr`의 호스트 로그 파일 이름, 설정의 절대 경로 | <https://modelcontextprotocol.io/docs/2026-07-28/develop/connect-local-servers> | 날짜 없음 |
| 운영 심사 범위 | <https://modelcontextprotocol.io/registry/moderation-policy> | 날짜 없음 |
| 인스펙터 인증 없는 프록시 원격 코드 실행, 0.14.1에서 수정 | <https://github.com/advisories/GHSA-7f8r-222p-6f5g> | 2025-06-13 |
