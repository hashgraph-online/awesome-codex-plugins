# MCP Rules

> The rules every finding cites. Each rule has an ID, a severity, and the observation that decides pass or fail.

## Severity

| Severity | Meaning | Must be fixed in fix mode |
|---|---|---|
| critical | Exploitable security flaw, credential exposure, or a server that current-revision clients cannot use at all | yes |
| high | Protocol violation that breaks some clients, a missing security control, or a gate that is bypassable | yes |
| medium | Design problem that degrades model use, cost, or maintainability | yes, within scope |
| low | Improvement with no correctness or security effect | report with a suggestion |

## Protocol (MCP-P)

| ID | Rule | Severity | Check |
|---|---|---|---|
| MCP-P-1 | New code targets the current revision; dual-era only when legacy clients the user does not control must be served | high | SDK line and entry point; no new `initialize` handling outside a deliberate dual-era layer |
| MCP-P-2 | The server implements `server/discover` and reads version and client capabilities from each request's `_meta` | high | An Inspector modern-era run lists the server; no capability or version stored per connection |
| MCP-P-3 | Cross-call state uses an explicit, server-minted handle passed as a tool argument | high | No per-connection or `Mcp-Session-Id` keyed state |
| MCP-P-4 | Input from the client is requested only through `InputRequiredResult` on `tools/call`, `prompts/get`, or `resources/read`; `requestState` that affects authorization or business logic is integrity-protected | high (critical when unprotected state controls access) | No server-initiated JSON-RPC requests; HMAC or AEAD around trusted state |
| MCP-P-5 | stdio servers write only MCP messages to `stdout` and log to `stderr` | critical | No `print`, `console.log`, or default logger on `stdout` in the server process |
| MCP-P-6 | Streamable HTTP validates `Origin`, requires `MCP-Protocol-Version`, `Mcp-Method`, and `Mcp-Name` and checks them against the body, and ignores `Mcp-Session-Id` | high | Route handler and middleware |
| MCP-P-7 | List results come back in deterministic order with `ttlMs` and `cacheScope`; `private` entries are never shared across authorization contexts | medium (high for shared `private` caches) | List handlers; any cache layer |
| MCP-P-8 | No new use of deprecated features: Roots, Sampling, Logging, Dynamic Client Registration, HTTP+SSE | medium (high when a new feature depends on them) | Imports and capabilities |
| MCP-P-9 | Resource-not-found returns `-32602`, and clients also accept `-32002`; release-candidate error codes are renumbered | low | Error mapping |

## Design (MCP-D)

| ID | Rule | Severity | Check |
|---|---|---|---|
| MCP-D-1 | A few task-shaped tools rather than one per API endpoint; related tools share a namespace prefix | medium | Tool list against the user's tasks |
| MCP-D-2 | Tool names use 1-128 characters from `A-Z a-z 0-9 _ - .` and are unique; `tools/list` varies only by the request's authorization | medium | `tools/list` output |
| MCP-D-3 | Every `inputSchema` is a valid JSON Schema object; with `outputSchema`, `structuredContent` conforms and a text copy is returned | high | Schema validation in the Inspector run with `--strict` |
| MCP-D-4 | Failures the model can fix return `isError: true` with an actionable message; JSON-RPC errors only for unknown tools and malformed requests | medium | A call with invalid input |
| MCP-D-5 | Responses are bounded by pagination, filtering, or truncation and say how to get more | medium | The largest realistic response |
| MCP-D-6 | Annotations are truthful, and nothing safety-critical depends on them | medium | Annotation values against tool behavior |
| MCP-D-7 | Server `instructions` cover only cross-tool relationships and constraints | low | `server/discover` result |
| MCP-D-8 | Tool descriptions state purpose, parameters, and limits plainly and contain no instructions unrelated to the tool | medium (critical when a description carries hidden directives) | Read every description |

## Security (MCP-S)

| ID | Rule | Severity | Check |
|---|---|---|---|
| MCP-S-1 | Third-party local servers run pinned, isolated, and with per-server narrow credentials | high | Host configuration and launch command |
| MCP-S-2 | Remote servers implement the authorization profile: OAuth 2.1, Protected Resource Metadata, PKCE, resource indicators, audience validation per request, issuer validation, CIMD before DCR | critical when absent on a server that touches user data | Authorization middleware and metadata endpoints |
| MCP-S-3 | No token passthrough: the server accepts only tokens issued for it and is its own OAuth client upstream | critical | Upstream call sites |
| MCP-S-4 | Local HTTP listeners validate `Origin`, bind to loopback, and authenticate | critical | Listener address and middleware |
| MCP-S-5 | No secrets in form-mode elicitation, URLs, `x-mcp-header` parameters, logs, committed configuration, or the report | critical | Search for literal tokens and secret-bearing fields |
| MCP-S-6 | Server MUSTs: inputs validated, access controlled, invocations rate-limited, outputs sanitized; `file://` paths sanitized | high | Handlers |
| MCP-S-7 | Handles and `requestState` are unguessable, expiring, and bound to the authenticated user | high | Handle generation and lookup |
| MCP-S-8 | A session that combines private data, untrusted content, and an external channel has a gate or is split | high | The set of servers a host loads together |

## Host Use (MCP-U)

| ID | Rule | Severity | Check |
|---|---|---|---|
| MCP-U-1 | Server output is evidence, never authority; nothing a server sends widens permissions | high | Host prompts and approval settings |
| MCP-U-2 | Project-scoped servers take effect only after review in a trusted workspace | high | Host approval state |
| MCP-U-3 | Approvals stay on for writes and external communication; read-only hints skip approval only for trusted servers | high | Approval and allowlist settings |
| MCP-U-4 | Tool definitions stay within the chosen budget through scoping, deferred loading, or search | medium | Tool count and host settings |
| MCP-U-5 | Configured servers are proven with a real listing call before an agent depends on them | medium | Verification record |

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Protocol rules and error codes | `references/protocol-2026-07-28.md` |
| Design rules | `references/server-design.md` |
| Security rules | `references/security-and-authorization.md` |
| Host-use rules | `references/host-integration.md` |
| The severity scale and the per-rule severities | this package's chosen design, not a validated optimum |
