# MCP Workflow

> Detect the MCP surface from files, pick one mode, run that mode's phases inside the side-effect gates, and save one Korean report.

## 1. Detect the Surface

Read only the files a signal names. Record each fact with the file that proves it.

| Fact | Where to look | Signals |
|---|---|---|
| Server or client SDK and its line | `package.json`, `pyproject.toml` / `requirements*.txt`, `go.mod`, `*.csproj`, `Cargo.toml`, `Gemfile`, `pom.xml` / `build.gradle*` | TypeScript `@modelcontextprotocol/server` or `@modelcontextprotocol/client` (v2, current revision) versus `@modelcontextprotocol/sdk` (v1, handshake era); Python `mcp` at 2.x versus 1.x; the official Go, C#, Rust, Ruby, Java, Kotlin, Swift, or PHP SDK |
| Role | Imports and entry points | A server object registering tools, resources, or prompts; a client object calling `callTool`, `listTools`, or their equivalents |
| Transport | Server start code, host configuration | stdio (`serveStdio`, stdio transport, `command`/`args` in host config) or Streamable HTTP (an HTTP route, `url` in host config); HTTP+SSE (`/sse` endpoints, `type: sse`) is deprecated |
| Era | Source and dependencies | Modern: per-request `_meta`, `server/discover`. Legacy: `initialize` handlers, `Mcp-Session-Id`, server-initiated `sampling`/`elicitation`/`roots` requests, `resources/subscribe`. Dual-era: both |
| Host configuration | Repository root and user-level files the request names | `.mcp.json`, `.vscode/mcp.json`, `.cursor/mcp.json`, `.codex/config.toml`, `claude_desktop_config.json` |
| Registry metadata | Repository root | `server.json`, `mcpName` in `package.json`, `mcp-name:` lines in a README |

With no MCP signal at all and a request that is not a build, stop: the request has no MCP surface. Report what was searched.

## 2. Choose the Mode

| Mode | Choose it when | Edits allowed |
|---|---|---|
| build | The user asks for a new server, client, or new tools | New and changed MCP code, tests, and the host entry the user asked for |
| audit | The user asks for a review, check, or report only, or a caller passes "audit only; report findings; do not edit" | None outside `.hyper/mcp/<slug>/` |
| fix | The user asks to review and correct | Changes that close findings in scope |
| migrate | The target is legacy or dual-era and the user asks to update it, or build/fix touches legacy code that cannot stay | Changes that implement the migration checklist |
| connect | The user asks to add, scope, secure, or repair MCP servers in a host | Host configuration files and the environment-variable names they reference |
| publish | The user asks to prepare or publish registry metadata | `server.json` and ownership markers |

Report-only words ("점검만", "고치지 말고", "report only", "audit only") force audit mode. A request that names two modes runs them in this order and records both: migrate, then fix, then connect, then publish.

## 3. Mode Phases

### build

1. Choose the deployment shape (remote Streamable HTTP for anything wrapping a remote API; local stdio only when the server needs the user's machine) and record why. `references/build-test-ship.md` owns the table.
2. Choose an SDK whose documentation states support for the current revision, preferring the target repository's language. Record the SDK's tier and the revision it supports.
3. Design the tool surface before code: a few task-shaped tools, names, input and output schemas, error messages, and response bounds (`references/server-design.md`). Write the design into the report.
4. Implement with the SDK's current-revision entry point; on TypeScript stdio that is the factory-based serve function the documentation names, not a hand-wired transport.
5. Add the security controls the deployment shape needs (`references/security-and-authorization.md`): authorization for remote servers, `Origin` validation and loopback binding for local HTTP, environment-provided credentials for stdio.
6. Verify (`rules/validation.md`), then repair within the loop budget.

### audit

1. Walk `rules/mcp-rules.md` in order: protocol, design, security, host use.
2. For each rule that applies, record `pass`, a finding, or `not applicable`, with evidence.
3. Run read-only checks that need no credential: listing methods through the Inspector against a server built from this repository, schema and configuration reads, dependency version reads.
4. Rank findings by severity and write the report. Edit nothing else.

### fix

Run audit phases 1-3, then fix critical, high, and medium findings in that order within scope, verify, and repair within the loop budget. Low findings are reported with a suggested change unless the user asked for everything.

### migrate

1. Inventory every legacy dependency: `initialize`, sessions, per-connection state, server-initiated requests, `resources/subscribe`, `ping`, `logging/setLevel`, `Last-Event-ID`, and release-candidate error codes.
2. Decide modern-only or dual-era. Choose dual-era only when clients the user does not control still speak a legacy revision, and record which.
3. Upgrade the SDK line, then apply the migration checklist in `references/protocol-2026-07-28.md` item by item, recording each item in the report.
4. Verify in every era the target will claim.

### connect

1. Read the host's configuration surface and scope rules (`references/host-integration.md`). Put shared, reviewed servers in the project file and personal or experimental servers in user scope.
2. Prefer a server's remote Streamable HTTP endpoint when it only wraps a remote API.
3. For a local server: identify the publisher, the exact package name, and a pinned version or image digest; show the exact launch command in the report.
4. Reference credentials by environment variable or the host's secret store; never write a token value into a file.
5. Narrow the tool list (allowlists, disabled tools) to what the user's task needs, and keep approvals on for tools that write or communicate externally.
6. Verify that the host can list the server's tools; call only a read-only tool, and only when the user approved running that server.

### publish

1. Check that the namespace matches the planned authentication method and that the ownership marker for the package type is present.
2. Write or update `server.json` with a unique, immutable version that matches the package version; list remote endpoints only when they are publicly reachable over Streamable HTTP.
3. Validate the metadata locally. Run the publish command only when the user explicitly asked to publish in this request; otherwise report the exact command for the user to run.

## 4. Side-Effect Gates

| Action | Gate |
|---|---|
| Installing dependencies inside the target repository | Allowed in build, fix, and migrate; pin versions the way the repository already does |
| Starting a server built from this repository for verification | Allowed; bind to loopback; stop it when the check ends |
| Starting a third-party server | Only a server the user named, at a pinned version, after its tool descriptions were read; otherwise stop and ask |
| OAuth login, using a real token, or calling a production endpoint | Stop and ask; the user performs the login |
| Calling a tool that writes, deletes, sends, or spends | Never during verification |
| Publishing to a registry or package index | Only on the user's explicit request in this run |
| Committing or pushing | Not this skill's action; report the changed files |

## 5. Report

Write `.hyper/mcp/<slug>/report.md`. `<slug>` is a short kebab-case name of the target and job; add `-2`, `-3` when the file exists for another job. Write it in Korean except for code, paths, rule IDs, and commands.

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

Audit mode leaves the `변경` table with one row: `없음 (점검 전용)`.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| SDK package names, the current-revision lines, and the TypeScript serve entry point | `references/build-test-ship.md` |
| Legacy markers, the migration checklist, and era selection | `references/protocol-2026-07-28.md` |
| Host configuration files and scope rules | `references/host-integration.md` |
| Local-server vetting, credential handling, and gated actions | `references/security-and-authorization.md` |
| The modes, the phase order, the gate table, and the report shape | this package's chosen design, not a validated optimum |
