# Build, Test, and Ship

How to turn an MCP server or client design into running code against `2026-07-28`, prove it works with the reference tooling, and publish it. It owns SDK selection, the minimal skeleton, inspector-based checks, debugging order, and registry publishing; tool and resource design lives in [`server-design.md`](server-design.md).

> Korean version: [`build-test-ship.ko.md`](build-test-ship.ko.md)

## Contents

- Choose the deployment shape first
- Choose an SDK by tier and revision
- Minimal server contract
- Test with the inspector
- Debug in this order
- Publish

## Choose the deployment shape first

The official server-building guide routes by deployment model before code (agent-skills guide, checked 2026-11-07).

| Shape | Use when | Cost you accept |
|---|---|---|
| Remote, Streamable HTTP | The server wraps a cloud API or serves many users; the guide calls it "the default for anything wrapping a cloud API" | HTTP authorization ([`security-and-authorization.md`](security-and-authorization.md)), hosting, rate limits |
| Local, stdio | Prototyping, or the server needs the user's machine (files, local apps) | Runs with the host's privileges; no protocol boundary |
| Local, MCP Bundle (`.mcpb`) | A local server distributed to people who will not install a runtime | Packaging and signing per bundle |
| MCP App (extension) | The result is an interactive UI rendered inside the host | Only hosts that implement the extension render it |

## Choose an SDK by tier and revision

The SDK tier policy grades conformance and maintenance, not popularity (SDK tiers page, checked 2026-11-07).

| Tier | SDKs | What the tier promises |
|---|---|---|
| 1 | TypeScript, Python, C#, Go, Rust, Ruby | 100% conformance tests; new spec features before the spec release; triage within 2 business days; critical bugs within 7 days |
| 2 | Java | 80% conformance; new features within 6 months |
| 3 | Swift, PHP, Kotlin | No conformance floor |

- Tier is not revision support. "SDKs adopt new protocol revisions on their own schedules", so read each SDK's own documentation for the revision it speaks. The Java and Kotlin quickstarts still build `2025-11-25` servers, which a modern-only client cannot reach (SDK page and quickstarts, checked 2026-11-07).
- Extensions such as Tasks and MCP Apps are "not required for any tier"; an SDK in Tier 1 may lack them. The Python SDK v2 states the Tasks API is one "this SDK does not implement yet" (checked 2026-11-07).
- TypeScript: v2 ships as `@modelcontextprotocol/server` and `@modelcontextprotocol/client` and implements `2026-07-28`; v1 (`@modelcontextprotocol/sdk`) stays on a `v1.x` branch for at least six months after the v2 release on 2026-07-27 (SDK README, checked 2026-11-07).
- Python: v2 "implements the 2026-07-28 revision, and it serves **both** revisions at once"; `FastMCP` was renamed `MCPServer`; the server tutorial requires SDK 2.0.0 or higher (checked 2026-11-07).

## Minimal server contract

Whatever the SDK, a `2026-07-28` server is done only when all of these hold. Each item is a protocol rule from [`protocol-2026-07-28.md`](protocol-2026-07-28.md), not a style preference.

- [ ] `server/discover` answers with supported versions, capabilities, `serverInfo`, and caching hints.
- [ ] Every handler reads version and client capabilities from the request's `_meta`, not from connection state.
- [ ] On stdio, nothing but MCP messages reaches `stdout`. The build guide puts it bluntly: "Never write to stdout. Writing to stdout will corrupt the JSON-RPC messages and break your server" (checked 2026-11-07). Use `stderr` loggers (`console.error`, Python `logging`, SLF4J to stderr).
- [ ] Tool failures return `isError: true` with readable text; a client SDK reports them as a result, not an exception — "Check `result.isError` rather than expecting a failing tool to throw" (client guide, checked 2026-11-07).
- [ ] On HTTP, `Origin` is validated and the required `Mcp-*` headers are checked against the body.

SDK-specific wiring matters for era coverage. The TypeScript server guide says `serveStdio(createServer)` "negotiates the protocol revision with each client, so the same server answers both 2026-07-28 clients and clients that still open with the 2025-era `initialize` handshake", while a server wired by hand with `server.connect(new StdioServerTransport())` "only serves 2025-era clients" (checked 2026-11-07). The SDK README's own getting-started example still shows the hand-wired form without that caveat; treat the documentation site as the authority, and confirm with the modern-era inspector run below.

## Test with the inspector

The MCP Inspector ships three clients in one package — web, CLI, and terminal UI — and needs Node 22.19.0 or newer (inspector page, checked 2026-11-07).

- **Pin the era.** The inspector's default protocol era is `legacy`: "Plain `initialize`, no probing at all", because "A debugging tool must not auto-probe." Pass `--protocol-era modern` to exercise `2026-07-28`; a green run in the default era proves nothing about the current revision (protocol-eras page, checked 2026-11-07). A dual-era server needs one run in each era.
- **Script it.** The CLI runs exactly one method per process (`--method tools/list`, `tools/call`, `resources/read`, `prompts/get`, …), prints the result, and exits — the shape a CI job wants.
- **Branch on exit codes.** `0` success, `3` authorization required, `4` unreachable, `5` tool error or tool not found, `6` `--strict` found an error-severity tool-schema portability problem, `11` HTTP 429; every non-zero exit also writes one JSON line to `stderr` (CLI page, checked 2026-11-07).
- **Keep CI non-interactive.** `--stored-auth-only` never starts an interactive OAuth flow; `--format json` makes output machine-readable; `--strict` turns schema portability findings into failures.

Inspector itself was a security incident: versions below 0.14.1 exposed an unauthenticated proxy reachable from a web page (CVE-2025-49596, published 2025-06-13). Keep it current and bound to loopback ([`security-and-authorization.md`](security-and-authorization.md)).

Inspector checks cover protocol conformance. Whether the model picks the right tool and recovers from errors is a separate evaluation; see [`server-design.md`](server-design.md).

## Debug in this order

The debugging guide orders the tools; follow it rather than starting in the host (checked 2026-11-07).

1. **Inspector** against the server alone, in the right era. It isolates server bugs from host bugs.
2. **Server logs.** stdio servers log to `stderr`; hosts often capture it (Claude Desktop writes `mcp-server-SERVERNAME.log`). Streamable HTTP has no captured `stderr`, so use your own log aggregation or OpenTelemetry. Protocol-level logging via `notifications/message` is deprecated and gated on the request's `logLevel`.
3. **Host configuration.** Use absolute paths — a stdio server's working directory may be undefined — and pass required environment variables explicitly, because stdio servers inherit only a limited environment subset.
4. **Error codes.** `-32022` unsupported version (read its `supported` list), `-32602` missing `_meta` fields or invalid params, `-32021` the server needs a client capability you did not declare.

## Publish

### MCP Registry

The registry is the project's metadata catalog for public servers (registry pages, checked 2026-11-07).

| Fact | Consequence |
|---|---|
| "The MCP Registry is currently in preview." | Expect breaking changes in the publishing flow. |
| It stores metadata, not code, and "does not support private servers." | Internal servers need a private catalog or an aggregator. |
| It "is not intended to be directly consumed by host applications." | Hosts read it through aggregators that add their own curation. |
| The namespace follows the authentication method: GitHub login → `io.github.<user-or-org>/*`; DNS or HTTP domain proof → reverse-DNS names. | Pick the namespace before the first publish. |
| Ownership is proven per package type: `mcpName` in `package.json` for npm, a visible `mcp-name:` line in the README for PyPI, NuGet, and crates.io, an OCI image label, or a URL containing "mcp" plus `fileSha256` for MCPB. | Add the marker before publishing the package itself. |
| A version "**MUST** be unique for each publication" and cannot change afterwards; version ranges are prohibited. | Treat a published `server.json` as immutable; fix forward. |
| Moderation removes "illegal content, malware, spam, and completely broken servers" and explicitly does not remove servers with security vulnerabilities. | A registry listing is not a security review. |

The `server.json` schema carries its own date (`2025-12-11` in the quickstart). It versions the registry format, not the protocol revision.

### Before you publish

- [ ] The server answers `server/discover` and passes inspector runs in every era it claims.
- [ ] Remote servers listed under `remotes` are publicly reachable over Streamable HTTP; the registry still accepts the deprecated `sse` type, but do not publish new SSE endpoints.
- [ ] Tool names, descriptions, and annotations are final for this version; hosts and prompt caches key on them, so a later change costs every connected host a cache miss.
- [ ] The security checklist in [`security-and-authorization.md`](security-and-authorization.md) passes.

## Sources

> All links checked 2026-11-07; documentation pages are the `2026-07-28` set unless the URL says otherwise.

| Claim | Source | Published |
|---|---|---|
| Deployment paths and the remote default | <https://modelcontextprotocol.io/docs/2026-07-28/develop/build-with-agent-skills> | undated |
| Server skeleton, `stdout` rule, `serveStdio` era coverage, Python SDK 2.0.0 | <https://modelcontextprotocol.io/docs/2026-07-28/develop/build-server> | undated |
| Client lifecycle, `isError` returned not thrown | <https://modelcontextprotocol.io/docs/2026-07-28/develop/build-client> | undated |
| SDK list and revision caveat | <https://modelcontextprotocol.io/docs/2026-07-28/sdk> | undated |
| Tier definitions, conformance floors, extensions not required | <https://modelcontextprotocol.io/community/sdk-tiers> | undated |
| TypeScript v2 packages and v1 support window | <https://github.com/modelcontextprotocol/typescript-sdk> | v2 2026-07-27 |
| Python v2 dual-revision support, `MCPServer` rename, Tasks not implemented | <https://py.sdk.modelcontextprotocol.io/whats-new/> | undated |
| Inspector clients and Node requirement | <https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector> | undated |
| CLI method model, exit codes, CI flags | <https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector/cli> | undated |
| Default `legacy` era, no auto-probe | <https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector/protocol-eras> | undated |
| Debugging order, log locations, absolute paths | <https://modelcontextprotocol.io/docs/2026-07-28/tools/debugging> | undated |
| Registry preview status, no private servers, not for direct host use | <https://modelcontextprotocol.io/registry/about> | undated |
| Ownership markers per package type | <https://modelcontextprotocol.io/registry/package-types> | undated |
| Namespace by authentication method | <https://modelcontextprotocol.io/registry/authentication> | undated |
| Immutable versions, ranges prohibited | <https://modelcontextprotocol.io/registry/versioning> | undated |
| Host log file name for stdio `stderr`, absolute paths in configuration | <https://modelcontextprotocol.io/docs/2026-07-28/develop/connect-local-servers> | undated |
| Moderation scope | <https://modelcontextprotocol.io/registry/moderation-policy> | undated |
| Inspector unauthenticated-proxy RCE, fixed in 0.14.1 | <https://github.com/advisories/GHSA-7f8r-222p-6f5g> | 2025-06-13 |
