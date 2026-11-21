# MCP Server

> Build the server on `rmcp`, state the specification revision, keep stdout for protocol frames, and let the tool layer stay a thin adapter over testable functions.

Rules here are `official` when an opened page in `references/official/rust/rust-crates-2026-11-07.md` states them and `hypercore-default` when this package chose the default. Protocol-level design decisions — capability negotiation, content model, pagination semantics — are the MCP specification's concern; this file covers the Rust crate that implements them.

## 1. SDK and revision

`official` — `rmcp` 3.9.0 (published 2026-11-05) is "An official Rust Model Context Protocol SDK implementation with tokio async runtime", living in `github.com/modelcontextprotocol/rust-sdk` with the companion `rmcp-macros` crate (https://raw.githubusercontent.com/modelcontextprotocol/rust-sdk/main/README.md).

`official` — "This SDK implements the stable MCP `2026-07-28` specification while remaining fully compatible with the `2025-11-25` release and earlier versions" (https://raw.githubusercontent.com/modelcontextprotocol/rust-sdk/main/README.md). The specification itself lists `2026-07-28` as the current protocol version, labels revisions Draft, Current, or Final, and allows a deprecation window of at least twelve months, or at least ninety days under the expedited exception (https://modelcontextprotocol.io/docs/2026-07-28/learn/versioning.md).

`hypercore-default` — State the target in one place, the crate docs or a constant beside the server name: "MCP `2026-07-28`, backward compatible to `2025-11-25`". A server that cannot name its revision cannot decide which schema rules apply.

`hypercore-default` — Do not hand-roll JSON-RPC framing, initialize negotiation, or capability advertisement. `rmcp` owns the protocol; a bespoke transport is a bug surface with no upside unless a host environment forbids the SDK, which is a recorded decision.

## 2. Features and transports

`official` — Defaults are `base64`, `macros`, `server`, `schemars`, `transport-async-rw`, and `uuid`. Transports are feature-gated and must be added explicitly: `transport-io` (server over stdio), `transport-child-process` (client spawn), `transport-streamable-http-server`, `transport-streamable-http-client-reqwest`, and `transport-worker` (https://docs.rs/crate/rmcp/latest/features).

`official` — TLS selector features are `reqwest` using rustls (documented as the "recommended default"), `reqwest-native-tls`, and `reqwest-tls-no-provider` (https://docs.rs/rmcp/latest/rmcp/).

```toml
[dependencies.rmcp]
version = "3.9"
features = ["server", "transport-io"]          # add "transport-streamable-http-server" for HTTP

[dependencies.tracing-subscriber]
version = "0.3"
features = ["env-filter"]
```

`hypercore-default` — Enable only the transport the deployment uses. A stdio server that also compiles the HTTP transport ships a router it never mounts, and a reviewer cannot tell which path is live.

## 3. Tools and schemas

`official` — `#[tool]` generates an `rmcp::model::Tool` with `name` (defaults to the function name), `description` (defaults to the doc comment), `input_schema` (defaults to the JSON schema of a `Parameters<T>` argument), and `annotations` (https://docs.rs/rmcp-macros/latest/rmcp_macros/attr.tool.html). `#[tool_router]` builds the router from an `impl` block; `#[tool_router(server_handler)]` elides a separate `ServerHandler` implementation for a tools-only server; `#[tool_handler(name = ..., version = ..., instructions = ...)]` is the explicit form when custom metadata or several capabilities are needed.

`official` — "The generated tool `inputSchema` and `outputSchema` are derived from the fields of `T`. The type name and documentation on `T` are ignored; only field names, field types, and field documentation are used" (https://raw.githubusercontent.com/modelcontextprotocol/rust-sdk/main/README.md). Schemas are JSON Schema draft 2020-12, and `schemars` is re-exported as `rmcp::schemars`.

`official` — Under `2026-07-28` (SEP-2106), "`outputSchema` may now be any JSON Schema type (not just `object`), and a tool result's `structuredContent` may be any JSON value" (https://raw.githubusercontent.com/modelcontextprotocol/rust-sdk/main/README.md).

`hypercore-default` — Consequences for the crate:

- Every field carries a `///` doc comment; it is the schema description a client sees, and it is the only place the semantics can live.
- Field names are `snake_case` in Rust and stated explicitly with `#[serde(rename = "camelCase")]` only when the tool contract already uses that spelling. A rename is a breaking tool change.
- The parameter struct is a contract type: it has no interior mutability, no borrowed fields, and no `serde_json::Value` where a concrete type is possible.
- A tool that returns machine data emits `structuredContent` with a matching `outputSchema`, and keeps its text content as the human-readable rendering.
- Tool names are stable identifiers. Renaming one breaks every client's permission list, so it needs a recorded decision and an alias period.

`hypercore-default` — Suggested shape:

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

`hypercore-default` — Verify the exact argument-wrapper path and `CallToolResult` constructor against the installed `rmcp` version before writing them; the import paths move between minor releases, and the version in this snapshot is `3.9.0`.

## 4. Handler layering

`hypercore-default` — A tool handler parses its typed argument, validates it, calls a plain function, and maps the result. Nothing more.

| Layer | Owns | Must not own |
|---|---|---|
| `#[tool]` function | Argument type, one call, result mapping | Business rules, database queries, retries |
| Service function | Orchestration and decisions | MCP types, `CallToolResult`, protocol errors |
| `tools/<name>.rs` module | The tool's own contract type and mapping | Transport selection |

Because a tool handler is a normal Rust function over a typed struct, the service underneath is testable with `cargo test` and no transport. A handler with a query, a retry loop, and a formatting branch is a service that has not been separated out.

`official` — `list_all_*` helpers walk `next_cursor` pages transparently, and every request carries its protocol version in `_meta`; a server rejects an unsupported version with `UnsupportedProtocolVersionError` (https://raw.githubusercontent.com/modelcontextprotocol/rust-sdk/main/README.md). Let the SDK do both; do not re-implement cursor loops or version checks.

## 5. stdio discipline

`official` — The specification's stdio binding is absolute: "The server **MUST NOT** write anything to its `stdout` that is not a valid MCP message", "The server **MAY** write UTF-8 strings to `stderr` for any logging purposes", messages are newline-delimited and "MUST NOT contain embedded newlines", and servers "SHOULD exit promptly when their standard input is closed or reads return end-of-file" (https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio.md).

`hypercore-default` — Make it structural, not a habit:

```rust
tracing_subscriber::fmt()
    .with_env_filter(filter)
    .with_writer(std::io::stderr)      // stdout belongs to the transport
    .init();
```

- A single `println!` in any dependency, a stray `dbg!`, or a progress bar on stdout corrupts the session. Treat such a call in a touched file as a defect, not a style issue.
- A dependency that prints to stdout is wrapped or replaced; there is no way to intercept `std::io::stdout` cleanly in Rust, so prevention is the only fix.
- The process exits on stdin EOF; do not install a shutdown that keeps a session open after the client is gone.
- A panic writes to stderr, which is legal, but the session ends. Prefer returning `ErrorData` from a handler over panicking.

## 6. Streamable HTTP transport

`official` — `StreamableHttpService` "is a Tower service — mount it on any router", built from a per-request service factory, `LocalSessionManager`, and `StreamableHttpServerConfig`; the documented wiring is `axum::Router::new().nest_service("/mcp", service)` (https://raw.githubusercontent.com/modelcontextprotocol/rust-sdk/main/README.md).

`official` — Because modern clients keep no per-session state, "the `service_factory` runs per request. Keep shared state (DB pools, caches) in a `Clone` handle captured by the closure". `2026-07-28` "is served statelessly automatically: no `Mcp-Session-Id`, no standalone GET/DELETE stream, and no `Last-Event-ID` resumption"; `with_legacy_session_mode(false)` also makes legacy versions stateless, and `with_json_response(true)` returns a single `application/json` body for simple tools (same source).

`hypercore-default` — Rules:

- Mount the MCP endpoint at one path (`/mcp`). Every HTTP route outside that path belongs to the Axum stack guide, `stacks/axum/core.md`, not to this file.
- Capture a `Clone` state handle in the factory; do not rebuild a pool or a client per request.
- State the response mode: streaming responses when a tool streams progress, `with_json_response(true)` when every tool is a single short result. A mixed server keeps streaming.
- Do not promise the legacy 2024-11-05 HTTP+SSE transport; `rmcp` deliberately omits it.
- When the MCP endpoint and other HTTP routes share a listener, authentication applies to both; the MCP path is not public by default.

`hypercore-default` — A `tower` dependency comes with the HTTP transport; a crate that mounts the service but adds layers must state their order, because layer order decides which layer sees an unauthenticated request first.

## 7. Logging capability

`official` — "Logging is deprecated and will be removed in a future release. It remains fully functional for now. See SEP-2577" (https://raw.githubusercontent.com/modelcontextprotocol/rust-sdk/main/README.md).

`hypercore-default` — Do not design around `notify_logging_message` or `enable_logging()`. Write diagnostics to stderr, return actionable text in the tool result, and treat the client's log-level control as a convenience that may disappear.

## 8. Unverified for this snapshot

- The MCP Tasks extension (SEP-2663) appears in `rmcp`'s `task_manager` module, but its status in the `2026-07-28` specification was not read. Do not build a design on it or claim it is required or forbidden.
- The exact `rmcp` 3.9.0 import paths for the parameter wrapper and the structured result constructor were not read from the crate docs for this snapshot; they change between minor releases, so a code snippet must be checked against the installed version.

## Checklist

- [ ] The crate depends on `rmcp`, not a hand-rolled JSON-RPC layer.
- [ ] The target specification revision is stated: `2026-07-28`, compatible with `2025-11-25`.
- [ ] Transport features match the deployment, and no unused transport is compiled in.
- [ ] A tool's input type is a plain struct with documented fields; the schema comes from those fields.
- [ ] Tool names are stable and a rename has a recorded decision.
- [ ] A tool handler validates, calls one plain function, and maps the result.
- [ ] Service functions below the handler carry no MCP types.
- [ ] On stdio, the subscriber writes to stderr and no `println!` exists in the crate's paths.
- [ ] The process exits when stdin closes.
- [ ] On HTTP, the service is mounted at one path with a `Clone` state captured by the per-request factory.
- [ ] The response mode (streaming or JSON) is stated, and legacy session mode is a recorded choice.
- [ ] Machine-consumed tools emit `structuredContent` with a matching `outputSchema`.
- [ ] No design depends on the deprecated logging capability or on the unverified Tasks extension.

## Sources

> Checked 2026-11-07. Facts come from the pages recorded in `references/official/rust/rust-crates-2026-11-07.md`.

| Claim | Source |
|---|---|
| `rmcp` 3.9.0 is the official Rust MCP SDK, built on tokio | https://raw.githubusercontent.com/modelcontextprotocol/rust-sdk/main/README.md, https://docs.rs/rmcp/latest/rmcp/ |
| `2026-07-28` is current and the SDK stays compatible with `2025-11-25` | https://modelcontextprotocol.io/docs/2026-07-28/learn/versioning.md, https://raw.githubusercontent.com/modelcontextprotocol/rust-sdk/main/README.md |
| Default and transport feature sets; TLS selector features | https://docs.rs/crate/rmcp/latest/features, https://docs.rs/rmcp/latest/rmcp/ |
| `#[tool]`, `#[tool_router]`, `#[tool_router(server_handler)]`, `#[tool_handler]` | https://docs.rs/rmcp-macros/latest/rmcp_macros/attr.tool.html |
| Schema derivation from fields only, draft 2020-12, `outputSchema` relaxation under SEP-2106, `schemars` re-export | https://raw.githubusercontent.com/modelcontextprotocol/rust-sdk/main/README.md |
| `StreamableHttpService` as a Tower service, per-request factory, stateless `2026-07-28`, `with_json_response` | https://raw.githubusercontent.com/modelcontextprotocol/rust-sdk/main/README.md |
| stdio stdout prohibition, stderr logging, newline-delimited frames, EOF exit | https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio.md |
| Pagination helpers and protocol-version rejection | https://raw.githubusercontent.com/modelcontextprotocol/rust-sdk/main/README.md, https://modelcontextprotocol.io/docs/2026-07-28/learn/versioning.md |
| Logging capability deprecated (SEP-2577) | https://raw.githubusercontent.com/modelcontextprotocol/rust-sdk/main/README.md |
| Handler layering, name stability, and response-mode rules | this package's convention, not an official Rust or MCP requirement |
