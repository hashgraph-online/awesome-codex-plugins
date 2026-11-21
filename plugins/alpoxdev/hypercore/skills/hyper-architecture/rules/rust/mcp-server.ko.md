# MCP 서버

> 서버를 `rmcp`로 만들고, 명세 리비전을 진술하며, stdout은 프로토콜 프레임에 남겨두고, 도구 계층은 테스트 가능한 함수 위의 얇은 어댑터로 둡니다.

이 파일의 규칙은 `references/official/rust/rust-crates-2026-11-07.md`에서 연 페이지가 그대로 진술한 경우 `official`, 이 패키지가 기본값으로 고른 경우 `hypercore-default`로 표시합니다. 프로토콜 수준 설계 결정 — capability 협상, 콘텐츠 모델, 페이지네이션 의미 — 은 MCP 명세의 관심사이고, 이 파일은 그것을 구현하는 Rust crate를 다룹니다.

## 1. SDK와 리비전

`official` — `rmcp` 3.9.0(2026-11-05 출시)은 "tokio 비동기 런타임을 쓰는 공식 Rust Model Context Protocol SDK 구현"이고 `github.com/modelcontextprotocol/rust-sdk`에 있으며 `rmcp-macros` crate를 동반합니다(https://raw.githubusercontent.com/modelcontextprotocol/rust-sdk/main/README.md).

`official` — "이 SDK는 안정 MCP `2026-07-28` 명세를 구현하면서 `2025-11-25` 릴리스와 그 이전 버전과 완전히 호환됩니다"(https://raw.githubusercontent.com/modelcontextprotocol/rust-sdk/main/README.md). 명세 자체는 `2026-07-28`을 현재 프로토콜 버전으로 나열하고, 리비전을 Draft, Current, Final로 표시하며, 최소 12개월, 신속 예외의 경우 최소 90일의 폐기 유예를 둡니다(https://modelcontextprotocol.io/docs/2026-07-28/learn/versioning.md).

`hypercore-default` — 대상을 한 곳에 진술합니다. crate 문서나 서버 이름 옆의 상수입니다. "MCP `2026-07-28`, `2025-11-25`와 하위 호환" 같은 형태입니다. 리비전을 명명할 수 없는 서버는 어떤 스키마 규칙이 적용되는지 결정할 수 없습니다.

`hypercore-default` — JSON-RPC 프레이밍, initialize 협상, capability 광고를 손으로 구현하지 않습니다. `rmcp`가 프로토콜을 소유합니다. 맞춤 전송은 이점 없이 버그 표면만 늘리며, 호스트 환경이 SDK를 금지하는 경우는 기록된 결정입니다.

## 2. 기능과 전송

`official` — 기본값은 `base64`, `macros`, `server`, `schemars`, `transport-async-rw`, `uuid`입니다. 전송은 기능으로 게이트되어 있고 명시적으로 추가해야 합니다. `transport-io`(stdio 서버), `transport-child-process`(클라이언트 spawn), `transport-streamable-http-server`, `transport-streamable-http-client-reqwest`, `transport-worker`입니다(https://docs.rs/crate/rmcp/latest/features).

`official` — TLS 선택 기능은 rustls를 쓰는 `reqwest`(문서가 "권장 기본"이라 부름), `reqwest-native-tls`, `reqwest-tls-no-provider`입니다(https://docs.rs/rmcp/latest/rmcp/).

```toml
[dependencies.rmcp]
version = "3.9"
features = ["server", "transport-io"]          # add "transport-streamable-http-server" for HTTP

[dependencies.tracing-subscriber]
version = "0.3"
features = ["env-filter"]
```

`hypercore-default` — 배포가 쓰는 전송만 켭니다. HTTP 전송까지 컴파일하는 stdio 서버는 한 번도 마운트하지 않는 라우터를 출하하고, 리뷰어는 어느 경로가 살아 있는지 알 수 없습니다.

## 3. 도구와 스키마

`official` — `#[tool]`은 `name`(함수 이름이 기본), `description`(문서 주석이 기본), `input_schema`(`Parameters<T>` 인자의 JSON 스키마가 기본), `annotations`를 가진 `rmcp::model::Tool`을 생성합니다(https://docs.rs/rmcp-macros/latest/rmcp_macros/attr.tool.html). `#[tool_router]`는 `impl` 블록에서 라우터를 만들고, 도구만 있는 서버는 `#[tool_router(server_handler)]`가 별도 `ServerHandler` 구현을 생략하게 하며, `#[tool_handler(name = ..., version = ..., instructions = ...)]`는 사용자 메타데이터나 여러 capability가 필요할 때의 명시적 형식입니다.

`official` — "생성되는 도구 `inputSchema`와 `outputSchema`는 `T`의 필드에서 나옵니다. `T`의 타입 이름과 문서는 무시되고 필드 이름, 필드 타입, 필드 문서만 사용됩니다"(https://raw.githubusercontent.com/modelcontextprotocol/rust-sdk/main/README.md). 스키마는 JSON Schema draft 2020-12이고 `schemars`는 `rmcp::schemars`로 재노출됩니다.

`official` — `2026-07-28`(SEP-2106)에서 "`outputSchema`는 이제 어떤 JSON Schema 타입도 될 수 있고(단지 `object`가 아님), 도구 결과의 `structuredContent`는 어떤 JSON 값도 될 수 있습니다"(https://raw.githubusercontent.com/modelcontextprotocol/rust-sdk/main/README.md).

`hypercore-default` — crate에 대한 결과입니다.

- 모든 필드에 `///` 문서 주석을 답니다. 클라이언트가 보는 스키마 설명이고, 의미를 둘 수 있는 유일한 자리입니다.
- 필드 이름은 Rust에서 `snake_case`이고, 도구 계약이 이미 그 표기를 쓰는 경우에만 `#[serde(rename = "camelCase")]`로 명시합니다. 이름 변경은 도구 계약의 파괴적 변경입니다.
- 매개변수 구조체는 계약 타입입니다. 내부 가변성도, 차용 필드도, 구체 타입이 가능한 자리의 `serde_json::Value`도 없습니다.
- 기계 데이터를 반환하는 도구는 대응하는 `outputSchema`와 함께 `structuredContent`를 내고, 텍스트 콘텐츠는 사람용 렌더링으로 유지합니다.
- 도구 이름은 안정된 식별자입니다. 이름을 바꾸면 모든 클라이언트의 권한 목록이 깨지므로 기록된 결정과 별칭 기간이 필요합니다.

`hypercore-default` — 제안하는 모양입니다.

```rust
#[derive(Clone)]
pub struct Service {
    state: AppState,                      // shared, `Clone` handle
}

#[rmcp::tool_router]
impl Service {
    /// Count rows in one table.
    async fn count_rows(
        &self,
        rmcp::handler::server::wrapper::Parameters(args): rmcp::handler::server::wrapper::Parameters<CountArgs>,
    ) -> Result<rmcp::model::CallToolResult, rmcp::ErrorData> {
        let count = self.state.count(&args.table).await?;
        Ok(rmcp::model::CallToolResult::structured(serde_json::json!({ "count": count })))
    }
}
```

`hypercore-default` — 인자 래퍼 경로와 `CallToolResult` 생성자는 쓰기 전에 설치된 `rmcp` 버전으로 확인합니다. import 경로는 마이너 릴리스 사이에 움직이고, 이 스냅숏의 버전은 `3.9.0`입니다.

## 4. handler 계층

`hypercore-default` — 도구 handler는 타입 있는 인자를 파싱하고, 검증하고, 평범한 함수를 호출하고, 결과를 매핑합니다. 그 이상은 하지 않습니다.

| Layer | Owns | Must not own |
|---|---|---|
| `#[tool]` 함수 | 인자 타입, 호출 하나, 결과 매핑 | 비즈니스 규칙, 데이터베이스 쿼리, 재시도 |
| 서비스 함수 | 조정과 결정 | MCP 타입, `CallToolResult`, 프로토콜 오류 |
| `tools/<name>.rs` 모듈 | 도구 자체의 계약 타입과 매핑 | 전송 선택 |

도구 handler가 타입 있는 구조체를 받는 평범한 Rust 함수이므로, 그 아래 서비스는 전송 없이 `cargo test`로 테스트할 수 있습니다. 쿼리와 재시도 루프와 포맷 분기를 가진 handler는 분리되지 않은 서비스입니다.

`official` — `list_all_*` 도우미는 `next_cursor` 페이지를 투명하게 넘고, 모든 요청은 `_meta`에 프로토콜 버전을 실으며, 서버는 지원하지 않는 버전을 `UnsupportedProtocolVersionError`로 거부합니다(https://raw.githubusercontent.com/modelcontextprotocol/rust-sdk/main/README.md). 둘 다 SDK에 맡깁니다. 커서 루프나 버전 검사를 다시 구현하지 않습니다.

## 5. stdio 규율

`official` — 명세의 stdio 바인딩은 단호합니다. "서버는 `stdout`에 유효한 MCP 메시지가 아닌 것을 **절대(MUST NOT)** 써서는 안 되며", "서버는 로깅 목적으로 `stderr`에 UTF-8 문자열을 써도 되고(MAY)", 메시지는 개행으로 구분되며 "내장 개행을 포함해서는 안 되며(MUST NOT)", 서버는 "표준 입력이 닫히거나 읽기가 end-of-file을 반환하면 즉시 종료하는 것이 좋습니다(SHOULD)"(https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio.md).

`hypercore-default` — 습관이 아니라 구조로 만듭니다.

```rust
tracing_subscriber::fmt()
    .with_env_filter(filter)
    .with_writer(std::io::stderr)      // stdout belongs to the transport
    .init();
```

- 의존성의 `println!` 하나, 남은 `dbg!`, stdout의 진행 막대가 세션을 망칩니다. 건드린 파일에서 그런 호출은 스타일 문제가 아니라 결함으로 취급합니다.
- stdout에 출력하는 의존성은 감싸거나 교체합니다. Rust에서 `std::io::stdout`을 깔끔하게 가로챌 방법이 없으므로 예방만이 해결책입니다.
- 프로세스는 stdin EOF에서 종료합니다. 클라이언트가 떠난 뒤 세션을 열어 두는 종료 처리를 설치하지 않습니다.
- panic은 stderr에 쓰므로 합법이지만 세션이 끝납니다. handler에서 panic하기보다 `ErrorData`를 반환하는 편이 낫습니다.

## 6. Streamable HTTP 전송

`official` — `StreamableHttpService`는 "Tower 서비스이므로 아무 라우터에나 마운트할 수 있고", 요청별 서비스 팩토리, `LocalSessionManager`, `StreamableHttpServerConfig`로 만들어집니다. 문서화된 배선은 `axum::Router::new().nest_service("/mcp", service)`입니다(https://raw.githubusercontent.com/modelcontextprotocol/rust-sdk/main/README.md).

`official` — 현대 클라이언트는 세션별 상태를 두지 않으므로 "`service_factory`가 요청마다 실행됩니다. 공유 상태(DB 풀, 캐시)는 클로저가 캡처한 `Clone` 핸들에 두세요". `2026-07-28`은 "자동으로 상태 없이 제공됩니다. `Mcp-Session-Id`도, 독립 GET/DELETE 스트림도, `Last-Event-ID` 재개도 없습니다". `with_legacy_session_mode(false)`는 레거시 버전도 상태 없이 만들고, `with_json_response(true)`는 간단한 도구에 대해 단일 `application/json` 본문을 반환합니다(같은 출처).

`hypercore-default` — 규칙:

- MCP 엔드포인트를 경로 하나(`/mcp`)에 마운트합니다. 그 경로 밖의 모든 HTTP 라우트는 이 파일이 아니라 Axum 스택 가이드 `stacks/axum/core.md`의 것입니다.
- 팩토리에서 `Clone` 상태 핸들을 캡처합니다. 요청마다 풀이나 클라이언트를 다시 만들지 않습니다.
- 응답 모드를 진술합니다. 도구가 진행 상황을 스트리밍하면 스트리밍 응답, 모든 도구가 짧은 단일 결과면 `with_json_response(true)`입니다. 섞인 서버는 스트리밍을 유지합니다.
- 레거시 2024-11-05 HTTP+SSE 전송을 약속하지 않습니다. `rmcp`는 그것을 의도적으로 생략합니다.
- MCP 엔드포인트와 다른 HTTP 라우트가 리스너를 공유하면 인증이 둘 다에 적용됩니다. MCP 경로가 기본적으로 공개되지 않습니다.

`hypercore-default` — HTTP 전송에는 `tower` 의존성이 따라옵니다. 서비스를 마운트하면서 레이어를 더하는 crate는 그 순서를 진술해야 합니다. 레이어 순서가 인증되지 않은 요청을 어느 레이어가 먼저 보는지를 결정하기 때문입니다.

## 7. 로깅 capability

`official` — "로깅은 폐기되었고 향후 릴리스에서 제거됩니다. 지금은 완전히 동작합니다. SEP-2577을 보세요"(https://raw.githubusercontent.com/modelcontextprotocol/rust-sdk/main/README.md).

`hypercore-default` — `notify_logging_message`나 `enable_logging()`을 중심으로 설계하지 않습니다. 진단은 stderr에 쓰고, 도구 결과에는 실행 가능한 텍스트를 반환하며, 클라이언트의 로그 레벨 제어는 사라질 수 있는 편의로 취급합니다.

## 8. 이 스냅숏에서 미검증

- MCP Tasks 확장(SEP-2663)은 `rmcp`의 `task_manager` 모듈에 나타나지만, `2026-07-28` 명세에서의 지위를 읽지 않았습니다. 설계를 그것에 기대지 말고, 필수나 금지로 주장하지 않습니다.
- `rmcp` 3.9.0의 매개변수 래퍼와 구조적 결과 생성자의 정확한 import 경로를 이 스냅숏에서 crate 문서로 읽지 않았습니다. 마이너 릴리스 사이에 움직이므로 코드 조각은 설치된 버전으로 확인해야 합니다.

## Checklist

- [ ] crate가 손으로 만든 JSON-RPC 계층이 아니라 `rmcp`에 의존한다.
- [ ] 대상 명세 리비전을 진술했다. `2026-07-28`, `2025-11-25`와 호환.
- [ ] 전송 기능이 배포와 맞고, 쓰지 않는 전송이 컴파일되지 않는다.
- [ ] 도구의 입력 타입이 문서화된 필드를 가진 평범한 구조체이고, 스키마가 그 필드에서 온다.
- [ ] 도구 이름이 안정적이고 이름 변경에는 기록된 결정이 있다.
- [ ] 도구 handler가 검증하고, 평범한 함수 하나를 호출하고, 결과를 매핑한다.
- [ ] handler 아래 서비스 함수가 MCP 타입을 지니지 않는다.
- [ ] stdio에서 subscriber가 stderr에 쓰고, crate 경로에 `println!`이 없다.
- [ ] stdin이 닫히면 프로세스가 종료한다.
- [ ] HTTP에서 서비스가 경로 하나에 마운트되고, 요청별 팩토리가 `Clone` 상태를 캡처한다.
- [ ] 응답 모드(스트리밍 또는 JSON)를 진술했고, 레거시 세션 모드는 기록된 선택이다.
- [ ] 기계 소비 도구가 대응하는 `outputSchema`와 함께 `structuredContent`를 낸다.
- [ ] 폐기된 로깅 capability나 미검증 Tasks 확장에 의존하는 설계가 없다.

## Sources

> Checked 2026-11-07. 사실은 `references/official/rust/rust-crates-2026-11-07.md`에 기록된 페이지에서 왔습니다.

| Claim | Source |
|---|---|
| `rmcp` 3.9.0이 tokio 기반 공식 Rust MCP SDK | https://raw.githubusercontent.com/modelcontextprotocol/rust-sdk/main/README.md, https://docs.rs/rmcp/latest/rmcp/ |
| `2026-07-28`이 현재이고 SDK가 `2025-11-25`와 호환 유지 | https://modelcontextprotocol.io/docs/2026-07-28/learn/versioning.md, https://raw.githubusercontent.com/modelcontextprotocol/rust-sdk/main/README.md |
| 기본·전송 기능 집합과 TLS 선택 기능 | https://docs.rs/crate/rmcp/latest/features, https://docs.rs/rmcp/latest/rmcp/ |
| `#[tool]`, `#[tool_router]`, `#[tool_router(server_handler)]`, `#[tool_handler]` | https://docs.rs/rmcp-macros/latest/rmcp_macros/attr.tool.html |
| 필드에서만 스키마를 도출, draft 2020-12, SEP-2106의 `outputSchema` 완화, `schemars` 재노출 | https://raw.githubusercontent.com/modelcontextprotocol/rust-sdk/main/README.md |
| `StreamableHttpService`가 Tower 서비스, 요청별 팩토리, `2026-07-28`의 상태 없음, `with_json_response` | https://raw.githubusercontent.com/modelcontextprotocol/rust-sdk/main/README.md |
| stdio의 stdout 금지, stderr 로깅, 개행 구분 프레임, EOF 종료 | https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio.md |
| 페이지네이션 도우미와 프로토콜 버전 거부 | https://raw.githubusercontent.com/modelcontextprotocol/rust-sdk/main/README.md, https://modelcontextprotocol.io/docs/2026-07-28/learn/versioning.md |
| 로깅 capability 폐기(SEP-2577) | https://raw.githubusercontent.com/modelcontextprotocol/rust-sdk/main/README.md |
| handler 계층, 이름 안정성, 응답 모드 규칙 | 이 패키지의 규약이며 공식 Rust나 MCP 요구가 아님 |
