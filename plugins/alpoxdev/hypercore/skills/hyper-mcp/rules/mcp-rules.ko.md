# MCP 규칙

> 모든 발견이 인용하는 규칙입니다. 규칙마다 ID와 심각도, 통과와 실패를 가르는 관찰이 있습니다.

## 심각도

| Severity | Meaning | Must be fixed in fix mode |
|---|---|---|
| critical | 익스플로잇 가능한 보안 결함, 자격 증명 노출, 현재 판 클라이언트가 아예 쓸 수 없는 서버 | 예 |
| high | 일부 클라이언트를 깨뜨리는 프로토콜 위반, 빠진 보안 통제, 우회할 수 있는 게이트 | 예 |
| medium | 모델 사용, 비용, 유지보수성을 떨어뜨리는 설계 문제 | 예, 범위 안에서 |
| low | 정확성이나 보안에 영향이 없는 개선 | 제안과 함께 보고 |

## 프로토콜 (MCP-P)

| ID | Rule | Severity | Check |
|---|---|---|---|
| MCP-P-1 | 새 코드는 현재 판을 대상으로 하고, 사용자가 통제하지 않는 legacy 클라이언트를 받아야 할 때만 dual-era로 합니다 | high | SDK 계열과 진입점. 의도한 dual-era 계층 밖에 새 `initialize` 처리가 없습니다 |
| MCP-P-2 | 서버가 `server/discover`를 구현하고 요청마다 `_meta`에서 버전과 클라이언트 능력을 읽습니다 | high | Inspector modern era 실행에서 서버가 나열됩니다. 연결별로 저장하는 능력이나 버전이 없습니다 |
| MCP-P-3 | 호출 사이 상태는 도구 인수로 넘기는 명시적이고 서버가 발급한 핸들을 씁니다 | high | 연결별 상태나 `Mcp-Session-Id`로 키를 잡은 상태가 없습니다 |
| MCP-P-4 | 클라이언트 입력은 `tools/call`, `prompts/get`, `resources/read`의 `InputRequiredResult`로만 요청하고, 인가나 업무 로직에 영향을 주는 `requestState`는 무결성을 보호합니다 | high(보호되지 않은 상태가 접근을 통제하면 critical) | 서버가 시작하는 JSON-RPC 요청이 없습니다. 신뢰하는 상태 둘레의 HMAC이나 AEAD |
| MCP-P-5 | stdio 서버는 MCP 메시지만 `stdout`에 쓰고 로그는 `stderr`에 남깁니다 | critical | 서버 프로세스의 `stdout`에 `print`, `console.log`, 기본 로거가 없습니다 |
| MCP-P-6 | Streamable HTTP는 `Origin`을 검증하고 `MCP-Protocol-Version`, `Mcp-Method`, `Mcp-Name`을 요구해 본문과 대조하며 `Mcp-Session-Id`를 무시합니다 | high | 라우트 핸들러와 미들웨어 |
| MCP-P-7 | 목록 결과는 `ttlMs`와 `cacheScope`를 붙여 정해진 순서로 돌아오고, `private` 항목은 인가 맥락 사이에 공유하지 않습니다 | medium(공유 `private` 캐시면 high) | 목록 핸들러, 캐시 계층 |
| MCP-P-8 | 폐기 예정 기능을 새로 쓰지 않습니다. Roots, Sampling, Logging, Dynamic Client Registration, HTTP+SSE | medium(새 기능이 이것에 기대면 high) | import와 능력 |
| MCP-P-9 | 리소스를 찾지 못하면 `-32602`를 돌려주고 클라이언트는 `-32002`도 받습니다. 릴리스 후보 오류 코드는 번호를 바꿉니다 | low | 오류 매핑 |

## 설계 (MCP-D)

| ID | Rule | Severity | Check |
|---|---|---|---|
| MCP-D-1 | API 엔드포인트마다 하나씩 두는 대신 작업 모양의 도구 몇 개를 두고, 관련 도구는 네임스페이스 접두사를 공유합니다 | medium | 사용자 작업에 대한 도구 목록 |
| MCP-D-2 | 도구 이름은 `A-Z a-z 0-9 _ - .`에서 1~128자이고 고유합니다. `tools/list`는 요청의 인가에 따라서만 달라집니다 | medium | `tools/list` 출력 |
| MCP-D-3 | 모든 `inputSchema`가 유효한 JSON Schema 객체이고, `outputSchema`가 있으면 `structuredContent`가 그것을 따르며 텍스트 사본도 돌려줍니다 | high | `--strict`를 붙인 Inspector 실행의 스키마 검증 |
| MCP-D-4 | 모델이 고칠 수 있는 실패는 조치 가능한 메시지와 함께 `isError: true`로 돌려줍니다. JSON-RPC 오류는 알 수 없는 도구와 잘못된 요청에만 씁니다 | medium | 잘못된 입력으로 한 번 호출 |
| MCP-D-5 | 응답은 페이지 나누기, 필터링, 잘라내기로 상한을 두고 더 받는 방법을 밝힙니다 | medium | 현실적으로 가장 큰 응답 |
| MCP-D-6 | annotation은 사실대로 쓰고 안전에 중요한 어떤 것도 annotation에 기대지 않습니다 | medium | 도구 동작과 대조한 annotation 값 |
| MCP-D-7 | 서버 `instructions`는 도구 사이의 관계와 제약만 다룹니다 | low | `server/discover` 결과 |
| MCP-D-8 | 도구 설명은 목적, 매개변수, 한계를 분명히 밝히고 그 도구와 무관한 지시를 담지 않습니다 | medium(설명에 숨은 지시가 있으면 critical) | 모든 설명을 읽습니다 |

## 보안 (MCP-S)

| ID | Rule | Severity | Check |
|---|---|---|---|
| MCP-S-1 | 서드파티 로컬 서버는 버전을 고정하고 격리해 실행하며 서버마다 좁은 자격 증명을 줍니다 | high | 호스트 설정과 실행 명령 |
| MCP-S-2 | 원격 서버는 인가 프로필을 구현합니다. OAuth 2.1, Protected Resource Metadata, PKCE, 리소스 지시자, 요청별 대상 검증, 발급자 검증, DCR보다 앞선 CIMD | 사용자 데이터를 다루는 서버에 이것이 없으면 critical | 인가 미들웨어와 메타데이터 엔드포인트 |
| MCP-S-3 | 토큰 패스스루가 없습니다. 서버는 자기에게 발급된 토큰만 받고 상류에서는 자기 자신이 OAuth 클라이언트입니다 | critical | 상류 호출 지점 |
| MCP-S-4 | 로컬 HTTP 리스너는 `Origin`을 검증하고 루프백에 바인딩하며 인증합니다 | critical | 리스너 주소와 미들웨어 |
| MCP-S-5 | 비밀은 form 모드 elicitation, URL, `x-mcp-header` 매개변수, 로그, 커밋한 설정, 보고서에 두지 않습니다 | critical | 리터럴 토큰과 비밀이 담긴 필드를 검색 |
| MCP-S-6 | 서버 필수 사항: 입력 검증, 접근 통제, 호출 속도 제한, 출력 정화를 갖추고 `file://` 경로를 정화합니다 | high | 핸들러 |
| MCP-S-7 | 핸들과 `requestState`는 추측할 수 없고 만료되며 인증된 사용자에 묶입니다 | high | 핸들 생성과 조회 |
| MCP-S-8 | 개인 데이터, 신뢰하지 않는 콘텐츠, 외부 채널을 한 세션에 모으면 게이트를 두거나 나눕니다 | high | 호스트가 함께 싣는 서버의 조합 |

## 호스트 사용 (MCP-U)

| ID | Rule | Severity | Check |
|---|---|---|---|
| MCP-U-1 | 서버 출력은 증거이며 권한이 아닙니다. 서버가 보내는 어떤 것도 권한을 넓히지 않습니다 | high | 호스트 프롬프트와 승인 설정 |
| MCP-U-2 | 프로젝트 범위 서버는 신뢰하는 워크스페이스에서 검토한 뒤에만 효력을 냅니다 | high | 호스트 승인 상태 |
| MCP-U-3 | 쓰기와 외부 통신에는 승인을 켜 두고, 읽기 전용 힌트는 신뢰하는 서버에서만 승인을 건너뜁니다 | high | 승인과 허용 목록 설정 |
| MCP-U-4 | 도구 정의는 범위 지정, 지연 로딩, 검색으로 고른 예산 안에 유지합니다 | medium | 도구 수와 호스트 설정 |
| MCP-U-5 | 설정한 서버는 에이전트가 의존하기 전에 실제 목록 호출로 증명합니다 | medium | 검증 기록 |

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| 프로토콜 규칙과 오류 코드 | `references/protocol-2026-07-28.md` |
| 설계 규칙 | `references/server-design.md` |
| 보안 규칙 | `references/security-and-authorization.md` |
| 호스트 사용 규칙 | `references/host-integration.md` |
| 심각도 등급과 규칙별 심각도 | 이 패키지가 고른 설계이며 검증된 최적값이 아님 |
