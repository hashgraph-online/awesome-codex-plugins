# scrapely-mcp

<!-- mcp-name: ly.scrape/scrapely-mcp-server -->

An [MCP](https://modelcontextprotocol.io) server for [Scrape.ly](https://scrape.ly). It gives AI agents and MCP clients
access to a Scrape.ly account: search the Store for Actors, read their README and input schema, run them, follow the
runs, and read the results from datasets, key-value stores and logs. It can also manage saved tasks and search the
Scrape.ly and Crawlee documentation.

Full documentation: [scrape.ly/docs/mcp](https://scrape.ly/docs/mcp).

The same package runs in two ways:

- **Hosted**: `scrapely-mcp-http`, a multi-tenant streamable HTTP server. Scrape.ly runs it behind the API at
  `https://mcp.scrape.ly`. Most users connect to that URL and never install anything.
- **Local**: `scrapely-mcp-server`, a stdio server started by a desktop MCP client on your machine.

## Connect to the hosted server

Point your client at `https://mcp.scrape.ly`.

[![Add to Claude](https://img.shields.io/badge/Claude-Add_connector-D97757?logo=claude&logoColor=white)](https://claude.ai/customize/connectors?modal=add-custom-connector&connectorName=Scrape.ly&connectorUrl=https%3A%2F%2Fmcp.scrape.ly)
[![Add to Cursor](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en/install-mcp?name=scrapely&config=eyJ1cmwiOiJodHRwczovL21jcC5zY3JhcGUubHkifQ%3D%3D)
[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_Server-0098FF?logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect/mcp/install?name=scrapely&config=%7B%22type%22%3A%22http%22%2C%22url%22%3A%22https%3A%2F%2Fmcp.scrape.ly%22%7D)
[![Install in VS Code Insiders](https://img.shields.io/badge/VS_Code_Insiders-Install_Server-24bfa5?logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=scrapely&config=%7B%22type%22%3A%22http%22%2C%22url%22%3A%22https%3A%2F%2Fmcp.scrape.ly%22%7D)
[![Add to Kiro](https://kiro.dev/images/add-to-kiro.svg)](https://kiro.dev/launch/mcp/add?name=scrapely&config=%7B%22url%22%3A%22https%3A%2F%2Fmcp.scrape.ly%22%7D)

Command-line clients:

```bash
# Claude Code
claude mcp add --transport http --scope user scrapely https://mcp.scrape.ly
claude mcp login scrapely

# Codex CLI
codex mcp add scrapely --url https://mcp.scrape.ly
codex mcp login scrapely

# Gemini CLI
gemini extensions install https://github.com/scrapely-app/scrapely-mcp
```

- Clients that support MCP authorization find the OAuth flow on their own and ask you to sign in.
- Otherwise send your API token as a header: `Authorization: Bearer <token>`.
- Clients that cannot set headers can append `?token=<token>` to the URL. URLs tend to end up in logs, so prefer
  the header.

Example for a client that takes a JSON config:

```json
{
  "mcpServers": {
    "scrapely": {
      "url": "https://mcp.scrape.ly",
      "headers": { "Authorization": "Bearer YOUR_TOKEN" }
    }
  }
}
```

## Run locally (stdio)

Requires Python 3.11 or newer.

```bash
uvx --from scrapely-mcp scrapely-mcp-server
# or
pip install scrapely-mcp
scrapely-mcp-server
```

The token comes from `SCRAPELY_TOKEN`, or from the `token` field of `~/.scrapely/credentials.json` or
`~/.scrapely/auth.json`. A token is required unless every selected tool works without one
(`search-actors`, `fetch-actor-details` and the docs tools).

```json
{
  "mcpServers": {
    "scrapely": {
      "command": "uvx",
      "args": ["--from", "scrapely-mcp", "scrapely-mcp-server"],
      "env": { "SCRAPELY_TOKEN": "YOUR_TOKEN" }
    }
  }
}
```

Options:

| Flag | Meaning |
| --- | --- |
| `--tools a,b` | Tool categories or tool names to enable. Replaces the default set. |
| `--actors user/actor,...` | Expose these Actors as their own tools. |
| `--ui auto\|apps\|default` | MCP Apps widget mode (widgets are disabled in this release, see below). |
| `--telemetry-enabled` | Opt in to usage telemetry (also needs a write key, see below). |
| `--telemetry-env PROD\|DEV` | Which telemetry write key variable to use. |

## Tools

Default categories: `actors`, `docs`, `runs`, `storage`, `tasks`, `automations`. The `dev` category (`report-problem`) is off by
default.

| Category | Tools |
| --- | --- |
| actors | `search-actors`, `fetch-actor-details`, `call-actor` |
| docs | `search-scrapely-docs`, `fetch-scrapely-docs` |
| runs | `get-actor-run`, `get-actor-output`, `get-actor-run-list`, `get-actor-log`, `abort-actor-run` |
| storage | `get-actor-output`, `get-dataset`, `get-dataset-items`, `get-dataset-schema`, `get-key-value-store`, `get-key-value-store-keys`, `get-key-value-store-record`, `get-dataset-list`, `get-key-value-store-list` |
| tasks | `create-actor-task`, `get-actor-task`, `update-actor-task`, `publish-actor-task`, `unpublish-actor-task` |
| automations | `list-saved-inputs`, `run-saved-input`, `list-automations`, `run-automation` |
| dev | `report-problem` |

`search-scrapely-docs` searches the Scrape.ly docs at [scrape.ly/docs](https://scrape.ly/docs) by default
(`docSource: "scrapely"`), or the Crawlee docs (`crawlee-js`, `crawlee-py`). `fetch-scrapely-docs` returns a page as
Markdown; it accepts pages under `https://scrape.ly/docs` and `https://crawlee.dev`.

Whenever `call-actor`, `get-actor-run` or an Actor tool is enabled, `get-actor-run`, `get-actor-output`,
`get-dataset-items`, `get-key-value-store-record` and `abort-actor-run` are added as well.

`call-actor` waits up to `waitSecs` (0 to 45, default 30) and returns the run status and storage IDs; the agent then
fetches the results with `get-actor-output` (pass the `runId`, or a `datasetId`). It returns a page of dataset items
(`offset`, `limit` up to 1000, default 100, and `fields` with dot notation) plus the run's `OUTPUT` record. Long text
values are cut and a page may hold fewer items than `limit` so the reply stays small; `hasMore` and `nextOffset` say
where to continue. `get-dataset-items` remains available for finer control. Clients that support protocol tasks can run `call-actor` as a long-running task
and collect the result when the run ends. Progress notifications are sent while a run is awaited, and cancelling the
request aborts the run.

Any Scrape.ly API `GET` endpoint can also be read with `resources/read` using its full URL, for example
`https://api.scrape.ly/v2/datasets/<id>/items?limit=20`.

## Hosted server

```bash
scrapely-mcp-http --host 0.0.0.0 --port 8000
```

| Path | Purpose |
| --- | --- |
| `/mcp` (and any other path) | MCP endpoint (streamable HTTP; 2026-07-28 stateless requests are also served) |
| `/.well-known/oauth-protected-resource` | OAuth protected-resource metadata (also under `/mcp` suffix) |
| `/healthz` | Health check, `{"status":"ok"}` |

URL parameters on the MCP endpoint: `tools`, `actors`, `maxActorMemoryBytes`, `ui`, `payment` (`skyfire` or
`x402`), `telemetry-enabled`, `token`. `telemetry-enabled` can only turn telemetry off: when the server has telemetry
disabled, `telemetry-enabled=true` does not turn it on.

When an API call of a tool fails, the tool result carries the API's standard error message (`error.message`), cut to
300 characters; any other error body (a proxy page, a framework error) is replaced by `HTTP <status>`. The full text
stays in the session log and telemetry.

Each session gets its own server instance bound to the SHA-256 fingerprint of the credential that opened it; a
request with a different credential is answered as if the session did not exist. `SCRAPELY_TOKEN` is never used by
the HTTP server.

A container image definition is in `Dockerfile` (`docker build --build-arg SOURCE=local -t scrapely-mcp .`).

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `SCRAPELY_TOKEN` | none | Token for the stdio server |
| `SCRAPELY_API_BASE_URL` | `https://api.scrape.ly` | API origin used for outbound calls |
| `SCRAPELY_PUBLIC_API_BASE_URL` | derived | API origin shown to clients and used as OAuth issuer |
| `SCRAPELY_STORE_URL` | `https://scrape.ly/store` | Base of Store links |
| `SCRAPELY_STANDBY_BASE_URL` | API origin | Base for MCP-server Actors |
| `SCRAPELY_MCP_HOST` / `SCRAPELY_MCP_PORT` | `0.0.0.0` / `8000` | HTTP bind address |
| `SCRAPELY_ACTORS` / `SCRAPELY_TOOLS` | none | Default tool selection of the HTTP server |
| `SCRAPELY_MCP_UI` / `UI_MODE` | `auto` | Widget mode |
| `SCRAPELY_MCP_SESSION_IDLE_TIMEOUT_SECS` | `1800` | Idle session timeout |
| `SCRAPELY_MCP_MAX_SESSIONS` | `10000` | Session limit |
| `SCRAPELY_MCP_MAX_SESSIONS_PER_CREDENTIAL` | `50` | Open sessions per presented token; over it the caller's own oldest idle session is closed, or the request gets 429 |
| `SCRAPELY_MCP_MAX_SESSIONS_PER_IP` | `100` | Open sessions per client IP (last `X-Forwarded-For` hop, set by the API server's `/mcp` proxy) |
| `SCRAPELY_MCP_MAX_SESSIONS_PER_IPNET` | `400` | Open sessions per client IPv6 /48 (the per-IP cap groups IPv6 by /64) |
| `SCRAPELY_MCP_MAX_SELECTED_ACTORS` | `50` | Most distinct Actors one `?actors=` / `?tools=` selection may name (400 above it) |
| `SCRAPELY_MCP_VALIDATION_BUDGET_SECS` | `2` | Time one tool call's argument validation may take; a call over it is refused as too large or complex |
| `SCRAPELY_MCP_MAX_REMOTE_RESPONSE_BYTES` | `10485760` | Byte limit for what one connection to an MCP-server Actor may return |
| `SCRAPELY_MCP_MAX_REMOTE_TOOL_LIST_BYTES` | `4194304` | Byte limit for one `tools/list` connection to an MCP-server Actor |
| `SCRAPELY_MCP_MAX_ACTOR_TOOL_BYTES` | `1048576` | Tool definitions one Actor may add to a session; an Actor over it is skipped |
| `SCRAPELY_MCP_MAX_SESSION_TOOL_BYTES` | `4194304` | Actor tool definitions one session may keep; Actors past it are skipped |
| `SCRAPELY_MCP_MAX_TOTAL_TOOL_BYTES` | `67108864` | Actor tool definitions all sessions may keep together; a new session or request that does not fit gets 503 |
| `SCRAPELY_MCP_MAX_REMOTE_INFLIGHT_BYTES` | `67108864` | Bytes all open connections to MCP-server Actors may hold together (task results until they are stored); a connection over it fails with a retry hint |
| `SCRAPELY_MCP_MAX_TOOL_RESULT_BYTES` | `4194304` | Largest result one tool call (or task) may return; a larger one becomes an error |
| `SCRAPELY_MCP_MAX_DATASET_PAGE_BYTES` | `1048576` | Bytes of one dataset page the storage tools read; a page is cut after its last complete item |
| `SCRAPELY_MCP_MAX_RECORD_BYTES` | `1048576` | Bytes of one key-value record read inline; a larger record is returned as a download link |
| `SCRAPELY_MCP_MAX_TASKS_PER_SCOPE` | `100` | Protocol tasks kept per session/credential; oldest finished ones are dropped first |
| `SCRAPELY_MCP_MAX_TASKS_TOTAL` | `10000` | Protocol tasks kept in total |
| `SCRAPELY_MCP_MAX_TASK_RESULT_BYTES_PER_SCOPE` | `16777216` | Task results kept per session/credential; the oldest are released first |
| `SCRAPELY_MCP_MAX_TASK_RESULT_BYTES_TOTAL` | `134217728` | Task results kept in total; the oldest are released first |
| `SCRAPELY_MCP_TASK_RESULT_GRACE_SECS` | `60` | A task result is released this long after `tasks/result` first returned it |
| `SCRAPELY_MCP_TASK_RETENTION_SECS` | `900` | Finished tasks are dropped this long after they finish (or after their `ttl`) |
| `SCRAPELY_MCP_REPORT_PROBLEM_BLOCKED_CLIENTS` | `anthropic,claude` | Clients that do not see `report-problem` |
| `SCRAPELY_OFFICIAL_USERNAMES` | `scrapely` | Usernames shown as maintained by Scrape.ly, only when the API sends no `maintainedByScrapely` flag (older API servers) |
| `SCRAPELY_DOCS_URL` | `https://scrape.ly/docs` | Scrape.ly docs: searched through its `search-index.json`, pages read as Markdown |
| `SCRAPELY_DOCS_CRAWLEE_JS_*`, `SCRAPELY_DOCS_CRAWLEE_PY_*` | public Crawlee DocSearch values | Crawlee docs search |
| `SCRAPELY_CONSOLE_BASE_URL` / `SCRAPELY_CONSOLE_TOKEN_PREFIX` | disabled | Personalised dashboard links |
| `SCRAPELY_MCP_WIDGETS_ENABLED` / `SCRAPELY_MCP_WIDGET_ASSETS_DIR` | off | MCP Apps widgets (experimental) |
| `SCRAPELY_SEND_LEGACY_PAYMENT_HEADER` | `true` | Also send the legacy payment-protocol header |
| `SKYFIRE_SELLER_SERVICE_ID` | none | Shown in Skyfire payment hints |
| `SCRAPELY_MCP_SESSION_LOG` | `true` | Session log sent to the Scrape.ly API (see below); `false` turns it off |
| `TELEMETRY_ENABLED`, `SCRAPELY_TELEMETRY_WRITE_KEY`, `SCRAPELY_TELEMETRY_ENDPOINT` | off | Opt-in telemetry |
| `SENTRY_DSN` | none | Error reporting (install the `sentry` extra) |
| `LOG_LEVEL` | `info` | Log level (logs go to stderr) |

Telemetry is off unless it is enabled **and** a write key is configured; the package ships no keys. Logs never
contain tokens, payment tokens or payment signatures.

### Session log and the `context` parameter

Every tool accepts an optional `context` string: one or two sentences from the AI on what the user wants and why it
calls the tool. It is removed before the arguments are validated and never reaches the tool or the Actor; clients that
do not send it work as before.

The server reports each session's activity to the Scrape.ly API with your own token, so Scrape.ly can see how the MCP
server is used and what fails: the client name and version, the transport, each tool call with its arguments, the
`context`, the status, the duration and a short summary of the result. Values are sent and stored as they are,
nothing is masked, so do not put secrets in tool arguments you do not want Scrape.ly to see. Set
`SCRAPELY_MCP_SESSION_LOG=false` to turn it off.

### Widgets

MCP Apps widget tools (`search-actors-widget`, `fetch-actor-details-widget`, `call-actor-widget`,
`get-actor-run-widget`) are implemented but disabled by default, and no widget HTML is bundled. With widgets
disabled every client gets the plain tool set.

## Development

```bash
uv venv && uv pip install -e ".[test]"
pytest
```

## Privacy and support

- Privacy policy: https://scrape.ly/legal/privacy
- Support: hello@scrape.ly

## License

MIT, see [LICENSE](LICENSE). Third-party notices are in [NOTICE](NOTICE).
