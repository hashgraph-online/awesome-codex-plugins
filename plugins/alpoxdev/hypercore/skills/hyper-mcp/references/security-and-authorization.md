# Security and Authorization

The threat model for MCP servers, clients, and the hosts that combine them, and the authorization rules a remote server must implement under `2026-07-28`. Read it before exposing a server over HTTP, installing a third-party server, or approving a tool that touches private data.

> Korean version: [`security-and-authorization.ko.md`](security-and-authorization.ko.md)

## Contents

- What the protocol can and cannot promise
- Measured threat evidence
- Session-level risk: the lethal trifecta
- Authorization for remote servers
- Attack-specific mitigations
- Running local servers
- Server checklist

## What the protocol can and cannot promise

The official local-server guide states the limit plainly: "**no check proves what a server will do.** The protocol cannot guarantee that a server is what it claims or does only what it promises" (checked 2026-11-07). Treat the rest of this document as risk reduction, never as proof of safety.

| Layer | Covered by normative text in `2026-07-28` | Not covered |
|---|---|---|
| Transport and authorization | Token audience, no token passthrough, PKCE, resource indicators, `Origin` validation, state-handle binding | — |
| Tool metadata | Clients **MUST** treat **annotations** as untrusted unless the server is trusted | No equivalent rule for tool **descriptions**; definition pinning is "a property worth choosing a client for", not a protocol requirement |
| Composition | Name-collision disambiguation (**SHOULD**) | Cross-server influence through the shared model context |
| Process isolation (stdio) | None: "the client and a stdio server share one trust domain" | Everything; isolation is the host's and operator's job |

## Measured threat evidence

| Threat | Evidence (checked 2026-11-07) | What it implies |
|---|---|---|
| Tool poisoning — directives hidden in tool names or descriptions | MCPTox: 45 live servers, 353 real tools, 1,348 generated cases; highest attack success 72.8% (o1-mini); highest refusal rate below 3% (arXiv 2508.14925, v2 2026-09-29). A laboratory benchmark, not an in-the-wild exploitation rate. | Model alignment is not the control. Review descriptions and keep the roster small. |
| Influence without invocation | Trail of Bits (2025-04-21): servers "can manipulate model behavior *without ever being invoked*" because the model relays instructions between servers. | Connection isolation between servers does not isolate their effects. |
| Rug pull | Definitions can change after approval; "a one-time consent dialog and package pinning do not cover this surface" (local-server guide). | Prefer hosts that re-prompt on definition changes. |
| Injection through a trusted server | A malicious GitHub issue steered an agent into leaking private-repository data; Invariant Labs called it "not a flaw in the GitHub MCP server code itself" (2025-05-26). | Trusted servers still deliver untrusted content. |
| Over-privileged credentials | Supabase MCP running as `service_role` copied integration tokens into an attacker-visible ticket without violating any permission (General Analysis, 2025-07-08). | Least privilege is the server operator's job, not the protocol's. |
| Unauthenticated local listener | CVE-2025-49596: MCP Inspector below 0.14.1 exposed an unauthenticated proxy reachable from a web page (published 2025-06-13). | Loopback binding is not authentication. |
| Server-controlled URL reaches a shell | CVE-2025-6514, CVSS 9.6: `mcp-remote` 0.0.5–0.1.15 allowed OS command injection through a crafted `authorization_endpoint` (published 2025-07-09). | Clients **MUST NOT** open URLs through a shell. |

The OWASP MCP Top 10 (MCP01–MCP10) is a usable checklist vocabulary; the project marks itself as a beta release, so cite it as a taxonomy, not a standard.

## Session-level risk: the lethal trifecta

A session that combines access to private data, exposure to untrusted content, and the ability to communicate externally can be steered into exfiltration by one piece of attacker-controlled content (Willison, 2025-06-16). The MCP maintainers adopt the same framing: "the risk profile is a property of the session, not of any single server" (tool-annotations post, 2026-03-16). Evaluate the set of servers a host loads together, not each server alone.

## Authorization for remote servers

Authorization is optional and transport-scoped. HTTP-based servers **SHOULD** follow the authorization specification; "Implementations using an STDIO transport **SHOULD NOT** follow this specification, and instead retrieve credentials from the environment" (authorization spec, checked 2026-11-07).

| Step | Requirement |
|---|---|
| Base standard | Authorization servers **MUST** implement OAuth 2.1 for confidential and public clients. |
| Resource discovery | MCP servers **MUST** publish OAuth 2.0 Protected Resource Metadata (RFC 9728); clients **MUST** use it, reading the `WWW-Authenticate` resource metadata URL when present and falling back to the well-known path. |
| Authorization-server discovery | Servers provide RFC 8414 or OpenID Connect discovery; clients **MUST** support both. The `issuer` in fetched metadata **MUST** equal the issuer used to build the URL, or the client **MUST NOT** use it. |
| Client registration | Clients **MUST** obtain a client ID; priority is pre-registration, then Client ID Metadata Documents (CIMD), then Dynamic Client Registration, then asking the user. DCR is deprecated in `2026-07-28` and kept only for authorization servers without CIMD. |
| PKCE | Clients **MUST** implement PKCE and **MUST** refuse to proceed when the server's metadata does not advertise it. |
| Resource indicator | Clients **MUST** send the RFC 8707 `resource` parameter naming the MCP server in both authorization and token requests. |
| Issuer validation | Authorization servers **SHOULD** return `iss` (RFC 9207); clients **MUST** validate a present `iss` before redeeming the code. |
| Credential binding | Clients **MUST** key stored credentials by issuer and **MUST NOT** reuse them with another authorization server. |
| Token use | Tokens travel only in `Authorization: Bearer`, never in the query string. Servers **MUST** validate that a token was issued for them as audience. |
| No passthrough | Servers **MUST NOT** accept or forward tokens issued for anything else; to call an upstream API the server acts as its own OAuth client. |
| Scopes | Servers **SHOULD** name the needed `scope` in the `WWW-Authenticate` challenge and answer insufficient scope with `403` and `insufficient_scope`; clients request the challenged scopes first. Avoid omnibus scopes such as `*` or `all`. |

The official authorization tutorial for `2026-07-28` still walks through pre-registration and DCR only and never mentions CIMD. The specification and the client-registration page are authoritative; follow them where the tutorial disagrees. OAuth 2.1 and CIMD are themselves Internet-Drafts, so expect wording to move.

Machine-to-machine and enterprise single sign-on are opt-in extensions — OAuth Client Credentials and Enterprise-Managed Authorization (ID-JAG). Both "require explicit support from the MCP client — they are never active by default"; client secrets in the former are "long-lived credentials", so prefer JWT assertions where the extension allows (auth extensions page, checked 2026-11-07).

## Attack-specific mitigations

| Attack | Required control (source: security best practices, checked 2026-11-07) |
|---|---|
| Confused deputy through an OAuth proxy | Proxies with a static upstream client ID **MUST** obtain per-client consent before forwarding, show client name, scopes, and `redirect_uri`, protect the consent page against CSRF and framing, match `redirect_uri` exactly, and set `state` only after consent. |
| Token passthrough | **MUST NOT** accept tokens not issued for the server. |
| SSRF during discovery | Clients deployed server-side **MUST** consider SSRF when fetching OAuth URLs; **SHOULD** require HTTPS, block private, loopback, and link-local ranges, and validate redirect targets. Prefer an egress proxy to hand-written IP checks. |
| State handle hijacking | Servers **MUST** verify every inbound request and **MUST NOT** treat possession of a handle as authentication; **SHOULD** use random, expiring handles bound to the authenticated user (`<user_id>:<handle>`). This replaces the session-hijacking guidance that applied to `2025-11-25` and earlier. |
| `requestState` tampering | Integrity-protect state that affects authorization or business logic ([`protocol-2026-07-28.md`](protocol-2026-07-28.md)). |
| Dangerous authorization URLs | Clients **MUST** allow only `http`/`https` (`https` in production), reject `javascript:`, `data:`, `file:`, and similar schemes, and **MUST NOT** open URLs through a shell. |
| One-click local install | Clients offering one-click configuration **MUST** show the exact command without truncation, flag it as code execution, and require explicit approval. |
| DNS rebinding against local HTTP servers | Servers **MUST** validate `Origin` (`403` on mismatch) and **SHOULD** bind to `127.0.0.1`; still require real authentication, because "Binding to 127.0.0.1 is not an authentication boundary" (local-server guide). |
| Secrets in elicitation | Servers **MUST NOT** request passwords, API keys, tokens, or payment credentials through form-mode elicitation; such input goes through URL mode, and the server **MUST** verify that the user completing the URL flow is the user who started it. |

## Running local servers

The local-server guide's principle: "treat a third-party local server as untrusted code with exactly the privileges you hand it — and hand it as few as possible" (checked 2026-11-07).

1. **Ask whether it must run locally.** A server that only wraps a remote API gains nothing from local execution; prefer its remote Streamable HTTP version.
2. **Check provenance.** Identify the publisher, verify the exact package name, and pin the version. A launcher pin (`npx`, `uvx`) fixes only the top-level package; a container image pinned by digest fixes the whole dependency tree.
3. **Read the tool list** — through the inspector, with no model in the loop — and remove any server whose descriptions carry instructions unrelated to the tool's job.
4. **Isolate the process.** Run third-party servers in a container or VM with nothing mounted beyond the directory they need.
5. **Isolate credentials.** Pass each server its own narrowly scoped token through per-server configuration, never through globally exported shell variables, and keep long-lived secrets in the OS secret store.
6. **Limit the filesystem.** Grant the narrowest root, read-only where possible; configuration allowlists are cooperative, the container is the boundary.
7. **Keep the roster small.** Every configured server shares the model context with every other.

## Server checklist

- [ ] Inputs validated, access controlled, invocations rate-limited, outputs sanitized — the four server **MUST**s on the tools page.
- [ ] `file://` resources sanitize paths against traversal; prompts validate inputs and outputs against injection.
- [ ] Remote: OAuth flow per the table above, audience check on every request, no token passthrough, least-privilege scopes.
- [ ] Local HTTP: `Origin` validation, loopback binding, and authentication.
- [ ] Handles and `requestState` are unguessable, expiring, user-bound, and integrity-protected.
- [ ] No secret or PII marked with `x-mcp-header`, and none placed in elicitation URLs.
- [ ] Annotations describe the tool truthfully; nothing safety-critical depends on a client honoring them.

## Sources

> All links checked 2026-11-07; specification and documentation pages are the `2026-07-28` revision, and advisory and research dates are as printed on each page.

| Claim | Source | Published |
|---|---|---|
| Authorization scope, OAuth 2.1, RFC 9728, audience and passthrough rules | <https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization> | rev. 2026-07-28 |
| Discovery order and issuer equality | <https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/authorization-server-discovery> | rev. 2026-07-28 |
| Registration priority, CIMD, DCR deprecation | <https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/client-registration> | rev. 2026-07-28 |
| PKCE, resource indicators, no passthrough | <https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/security-considerations> | rev. 2026-07-28 |
| `iss` validation, issuer-bound credentials, DCR deprecated | <https://modelcontextprotocol.io/specification/2026-07-28/changelog> | rev. 2026-07-28 |
| Attack catalog and mitigations | <https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices> | rev. 2026-07-28 |
| Local trust domain, "no check proves", rug pulls, isolation | <https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/local-server-security> | rev. 2026-07-28 |
| Tutorial covers only pre-registration and DCR | <https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/authorization> | rev. 2026-07-28 |
| Annotation trust rule, server security MUSTs | <https://modelcontextprotocol.io/specification/2026-07-28/server/tools> | rev. 2026-07-28 |
| Form-mode secret prohibition, URL-mode rules | <https://modelcontextprotocol.io/specification/2026-07-28/client/elicitation> | rev. 2026-07-28 |
| Auth extensions opt-in, long-lived client secrets | <https://modelcontextprotocol.io/extensions/auth/overview> | undated |
| Session-level risk framing | <https://blog.modelcontextprotocol.io/posts/2026-03-16-tool-annotations/> | 2026-03-16 |
| Lethal trifecta | <https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/> | 2025-06-16 |
| Tool-poisoning benchmark | <https://arxiv.org/abs/2508.14925> | 2025-08-19, rev. 2026-09-29 |
| Influence without invocation | <https://blog.trailofbits.com/2025/04/21/jumping-the-line-how-mcp-servers-can-attack-you-before-you-ever-use-them/> | 2025-04-21 |
| Tool poisoning, rug pulls, shadowing | <https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks> | 2025-04-01 |
| Injection through the GitHub server | <https://invariantlabs.ai/blog/mcp-github-vulnerability> | 2025-05-26 |
| Over-privileged Supabase credential | <https://generalanalysis.com/blog/supabase-mcp-blog> | 2025-07-08 |
| CVE-2025-49596 (Inspector) | <https://github.com/advisories/GHSA-7f8r-222p-6f5g> | 2025-06-13 |
| CVE-2025-6514 (`mcp-remote`) | <https://github.com/advisories/GHSA-6xpm-ggf7-wc3p> | 2025-07-09 |
| Threat taxonomy (beta) | <https://owasp.org/projects/mcp-top-10> | beta |
