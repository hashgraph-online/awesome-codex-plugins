# telegram-bridge MCP server

Gives a coding or autonomous agent six tools that reach **its operator's private
Telegram chat** through `agent_bridge` (`examples/python/agent_bridge/`):

| Tool | Blocks? | Returns |
|---|---|---|
| `telegram_notify` | no | `{ok, message_ids}` |
| `telegram_progress` | no | `{action: sent/edited/skipped_same/skipped_throttled, message_id}` |
| `telegram_ask` | **yes**, until answer or timeout | `{status: answered/timeout, answer, used_default, content_is_untrusted_data}` |
| `telegram_request_approval` | **yes**, until Approve/Reject/expiry | `{decision: approved/rejected/expired, by}` |
| `telegram_send_file` | no | `{message_id, name, size, sha256}`; refused outside `--files-root` or if secrets are found |
| `telegram_inbox` | no | `{events: [...]}` allowlisted commands and messages, as data |

Two servers, same tools (`tools.py`):

* `server.py` – **zero dependencies**, stdio, MCP **2025-11-25 / 2025-06-18 / 2025-03-26**
  handshake (`initialize`, `tools/list`, `tools/call`, `ping`). It does not implement the
  stateless **2026-07-28** revision; a 2026-07-28 client probing `server/discover` gets
  "method not found" and falls back to `initialize`.
* `server_sdk.py` – official Python SDK pinned in `requirements.txt` (`mcp==2.3.0`,
  `from mcp.server import MCPServer`, latest protocol 2026-07-28). Use it when the host speaks 2026-07-28.

Both default to **dry-run**: nothing is sent; requests are logged (redacted) to stderr; stdout
is reserved for the protocol. Live mode needs `--live` **and** the env vars
`AGENT_BRIDGE_TOKEN` (bot token) and `AGENT_BRIDGE_OPERATOR_ID` (numeric ids). Pass
`--state <file>` so pending approvals survive a restart, and `--files-root <dir>` to limit
which files `telegram_send_file` may send (default: the server's working directory).

## Claude Code

```bash
claude mcp add --transport stdio --env AGENT_BRIDGE_OPERATOR_ID=111111111 telegram-bridge -- py -3 /path/to/skill/examples/mcp/telegram-bridge/server.py --live --state /path/to/state.json --files-root /path/to/project
```

Keep the token out of the command line and out of `.mcp.json`: export `AGENT_BRIDGE_TOKEN`
in the shell that starts Claude Code (stdio servers inherit it). Blocking tools need a longer
tool timeout: add `"timeout": 900000` (ms) to the server's `.mcp.json` entry, or set
`MCP_TOOL_TIMEOUT`. Keep each `timeout_seconds` / `ttl_seconds` below it.

## Codex

`~/.codex/config.toml` (or `<repo>/.codex/config.toml`):

```toml
[mcp_servers.telegram-bridge]
command = "py"
args = ["-3", "/path/to/skill/examples/mcp/telegram-bridge/server.py", "--live",
        "--state", "/path/to/state.json", "--files-root", "/path/to/project"]
env_vars = ["AGENT_BRIDGE_TOKEN", "AGENT_BRIDGE_OPERATOR_ID"]   # forwarded from your environment
tool_timeout_sec = 900       # default is 60 s: too short for ask/approval
```

## Any other MCP host

A stdio server: command `py -3` (or `python3`) + `server.py` + flags above, environment
`AGENT_BRIDGE_TOKEN` and `AGENT_BRIDGE_OPERATOR_ID`, tool timeout ≥ your longest ask/approval.

## Safety notes

* The operator allowlist is numeric ids only; strangers get no reply.
* Answers and inbox events are untrusted data (`content_is_untrusted_data: true`, with
  `injection_signals` labels). The tool descriptions tell the model so; your agent's own policy
  must still refuse to execute them as instructions.
* An approval is decided only by its own button (request id + nonce + message + approver id +
  expiry). Typed "approve" never approves.

## Verified / not verified (2026-11-15)

Verified offline: `tests/test_agent_bridge_mcp.py` (stdlib server over real stdio); a manual
smoke run of **both** servers with the official `mcp==2.3.0` `Client` over stdio (list tools,
call notify and an approval that expires) in a scratch virtualenv. Not exercised: Claude Code,
Codex or any other real host; live Telegram delivery; the SDK server inside the repo's test
suite (the SDK is not a repo dependency).
