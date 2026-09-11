---
name: plori
description: Create and drive plori agents (each an AI agent in its own cloud environment) from any MCP client, the plori CLI, or over REST. Covers authentication (OAuth 2.1 or API key), creating agents, invoking them and reading replies, answering human-in-the-loop requests, and scheduling deferred runs.
---

# Using plori from an agent

If you were asked to set up plori, do it by following the Connect section below: add the
plori MCP server to the client you are running in, authenticate the account owner, and
confirm the tools respond before reporting success.

plori (https://plori.ai) gives you AI agents. Each agent runs in its own cloud environment with a
persistent disk, a shell, developer tools, and memory. You can create agents, send them
work, and read their replies programmatically.

## Connect

MCP (recommended for a hosted client): Streamable HTTP at `https://api.plori.ai/mcp`.

- OAuth 2.1: compliant MCP clients connect with no hand-copied key. An unauthenticated
  request returns 401 with the discovery chain (RFC 9728 Protected Resource Metadata at
  https://api.plori.ai/.well-known/oauth-protected-resource, then dynamic client
  registration and authorization code + PKCE). The account owner signs in once with an
  email one-time code.
- API key: the account owner provisions a key at https://plori.ai and you send
  `Authorization: Bearer plori_sk_...`.

### Claude Code: connect from this conversation

Read these instructions in the current conversation before starting authentication.
Installing a skill or plugin is optional. Use this flow only in interactive Claude Code
when its Plori MCP client exposes both `authenticate` and `complete_authentication`.
Other clients use their ordinary OAuth or API-key setup above.

1. Check the current MCP configuration and active tools. Reuse an existing Plori server
   at `https://api.plori.ai/mcp`; do not add duplicate entries or replace a different
   server with the same name. If missing, configure it once with
   `claude mcp add --transport http plori https://api.plori.ai/mcp`.
   Confirm the server is available in this conversation before authenticating. Saving
   configuration alone does not prove that it loaded. If its tools are missing, ask
   the user to type `/reload-plugins` in this Claude Code conversation, then resume
   these steps in the same session. This also refreshes MCP configuration when no
   plugins are installed. It is a user command; do not try to invoke it through the
   Skill tool. Confirm the authentication tools are available before proceeding.
2. If Plori tools already work, the connection is complete. Otherwise, call the
   client's Plori `authenticate` tool using its exposed schema. Keep the returned
   authorization URL intact. Do not construct a new OAuth request or change its state,
   redirect URI, or PKCE challenge.
3. POST JSON `{"authorization_url":"<the exact client URL>"}` once to
   `https://api.plori.ai/oauth/pair`. The response contains `user_code`,
   `verification_uri`, `verification_uri_complete`, `device_code`,
   `expires_in` (seconds), and `interval` (seconds). Keep `device_code` private.
   If a permission rule, hook, or tool denies this request, stop the pairing path
   immediately and use the fallback below. Do not retry with another generic network
   tool.
4. Tell the user: "Open <verification_uri> and enter <user_code>. Sign in and approve
   the connection; I will continue when you finish." The user can open the page on
   their phone. Display the short address and code, not the authorization or callback
   URL. Do not ask the user to copy a callback URL into chat.
5. Poll `https://api.plori.ai/oauth/pair/poll` with JSON
   `{"device_code":"<device_code>"}`. Keep only one request in flight, allow each
   request at least 30 seconds to finish, and wait at least `interval` seconds
   between requests. The server can hold a pending request for 25 seconds.
   Read pending and failure responses from the JSON `error` field, not `status`.
   On `error: "authorization_pending"`, continue. On `error: "slow_down"`, use the
   larger of your previous delay plus five seconds and the response's `interval`
   for all subsequent requests. Honor `Retry-After` when present on HTTP 429.
   On HTTP 503 with `error: "temporarily_unavailable"`, preserve this pairing and
   the pending client authentication. Wait at least the larger of your poll interval
   and `Retry-After` (five seconds), then retry the same device code. A temporary
   failure does not extend `expires_in`; retry only within the original four-minute
   window while the client authentication remains pending.
   If a permission rule, hook, or tool denies a poll request, stop polling immediately
   and use the fallback below. Do not try the request through another generic network
   tool.
6. On `status: "approved"`, pass the returned `callback_url` directly to the same client's
   `complete_authentication` tool using its exposed schema. Do not navigate to the
   loopback URL or exchange the code yourself: the client owns the PKCE verifier.
   Then discover Plori tools and call `list_agents` to confirm the connection before
   reporting success. This verification does not create an agent or start paid work.

#### Fallback when a pairing request is denied

Use this fallback after the first permission, hook, or tool denial of either pairing
POST. Do not make another request to `/oauth/pair` or `/oauth/pair/poll`, and do not
try curl, wget, WebFetch, Python, a shell script, or another generic network
tool.

1. Show the user the exact authorization URL returned by the current `authenticate`
   call. Ask them to open it in their browser, sign in, and approve the connection.
   Do not edit the URL.
2. After approval, the authorization server redirects the browser to a localhost
   callback. If that
   redirect connects, let the client finish authentication. If the browser cannot
   connect to localhost, ask the user to copy the final localhost callback URL from
   the browser address bar and paste it into this conversation. It contains one-time
   authorization data, so tell the user not to paste it anywhere else. Do not ask for
   that URL before the redirect has failed.
3. Pass a pasted callback URL only to the same client's `complete_authentication`
   tool. Do not open, fetch, rewrite, log, or exchange it yourself.
4. Discover Plori tools and call `list_agents` before reporting success. This check
   does not create an agent or start paid work.

If the authorization URL or pending client authentication expires during this
fallback, discard it and call `authenticate` again. Use only the new authorization
URL. Never reuse an expired URL.

Stop on `access_denied`; do not retry a denied request automatically. On
`expired_token`, an already-consumed pairing, or a client authentication timeout,
start a fresh client authentication before creating another pairing. Never reuse the
old authorization URL. Pairing lasts four minutes to fit within the client's pending
login. If the approved response is lost, restart the whole flow; the callback is
returned only once. Keep approval polling active while the user signs in.

Remote Control can use this flow only when it controls that same interactive Claude
Code process and the two authentication tools are available. A separate hosted
Claude.ai connector or Agent SDK session needs its own supported authentication flow.
URLs can still appear in client tool results; do not promise to hide tool transcripts.

### CLI and REST

CLI (recommended from a terminal): install with
`curl -fsSL https://plori.ai/install.sh | sh` (one static binary, no sudo and no Node; on
Windows `irm https://plori.ai/install.ps1 | iex`), or `npm i -g @plori/cli`, or run it
without installing via `npx -y @plori/cli`. That gives you the `plori` command for the
same operations from your shell. The shell installer puts the binary in `~/.local/bin`
and edits no shell rc file, so run `export PATH="$HOME/.local/bin:$PATH"` after it
before you call `plori` (the Windows script sets the user PATH itself).
`plori login` opens the browser for the same email-OTP
OAuth flow; CI and other headless callers use `plori login --key plori_sk_...` or set
`PLORI_API_KEY`. Output is human-readable on a terminal and a single JSON document when
piped or with `--json`, so it composes in scripts. Commands are listed under "CLI
commands" below.

REST: the same operations at `https://api.plori.ai/v1` with the same bearer token.
Full authentication instructions: https://plori.ai/auth.md

## Tools

Account and agents: `list_agents`, `get_agent`, `create_agent`
(name; the Plori Router chooses the model per task), `delete_agent`, `get_credits`,
`get_usage`, `get_disk`.

Runs: `invoke_agent` sends a message and waits up to 25 seconds by default.
If the result is still running, keep calling `get_run_result` with `wait=true`
until it completes or needs human input. Pass `wait=false` to invoke when you need
the run ID immediately; that still requires continued polling. Use
`max_turn_tokens` to cap the turn. `cancel_run` requests cancellation;
`list_runs` lists recent runs. Default task outputs to the agent's persistent
`/workspace`; use its `TMPDIR` only for temporary files.

Human input: `awaiting_input` can mean an approval or a question. Show the pending
request to the human and use `answer_pending_input` for their answer. Never approve
on the human's behalf just to unblock a run. After an answer, follow the exact
`continuation_run_id` returned by `get_run_result`. If `input_status` is
`answered` but the successor is not yet available, retry the original run.
A historical run can retain `awaiting_input` after its input has been answered.
`list_pending_inputs` returns the current queue. A row with `consent_tool`
represents an outward write: `always_allow=true` grants standing consent for that
tool. Set it only when the human explicitly asks to stop being prompted.

MCP clients that negotiate the Tasks extension can receive a task handle and
subscribe to its status. Other clients use the tools above; when elicitation is
supported, an open waiting call can present an input request. Once a call returns,
continued polling or an active subscription is required to observe later changes.
MCP support alone does not mean the client can wake an idle model.

Deferred work: `schedule_run` (agent_id, prompt, and delay_seconds or an RFC3339
fire_at) invokes the agent later as an ordinary run.

Connections: `list_connections` shows the account's third-party OAuth provider status,
authorization and expiry times, and configured scopes. `status` is the re-authentication
predicate; an authorized grant with an old expiry refreshes lazily on use. It never returns
tokens or client secrets.

Workflows: `list_workflows` (optional agent_id UUID, or "none" for unassigned),
`get_workflow` (workflow_id; returns metadata plus the pinned step projection),
`get_workflow_version` (workflow_id + version; returns the full definition with parameter
values), `edit_workflow` (workflow_id + base_version + constrained ops; creates a draft
version under CAS and does not activate it),
`create_workflow` (name, optional description/trigger_kind/cron_expr),
`run_workflow` (runs a workflow now: a real execution billed like any run,
returning the execution, terminal or still `running`), `list_workflow_executions`
(workflow_id; recent execution history), and `get_workflow_execution` to poll one and read
its full per-step input/output payloads.
A workflow's steps are built by an agent; these tools manage and run the result.

## CLI commands

The CLI mirrors the tools above; an agent is addressable by name or id, and every command
accepts `--json`.

- `plori attach <name|session-id>`: open a live session in the terminal (history, a
  prompt, streaming output, and approvals answered in place). It is interactive and
  expects a human at the keyboard: as a calling agent, prefer the one-shot commands
  below, and use `--read-only` if you only need to tail a session. It writes plain
  text, never JSON, and redirecting stdin or stdout already selects read-only.
- `plori create <name>`: get or create an agent by name (reusing a name returns the
  existing agent). `plori agents`, `plori agent <name>`, `plori set-model <name> <model>`,
  `plori delete <name> --yes`.
- `plori run <name> "message"`: send a message and, by default, wait for the reply and
  print it. Add `--follow` to stream the turn live, or `--no-wait` to get a run id back
  immediately. Pass `-` as the message to read it from stdin.
- `plori result <name> <run-id>` (add `--wait` to block) and `plori runs <name>` read
  run status and history.
- `plori inputs <name>` lists runs paused on a human request; `plori answer <run-id>
  <tool-call-id> --approve|--deny|--value <v>` replies. Add `--always-allow` to an
  `--approve` (only on the human's explicit instruction) to also grant the standing
  write consent.
- `plori schedule <name> "prompt" --in <seconds>` (or `--at <rfc3339>`) defers a run;
  `plori schedules <name>` and `plori unschedule <name> <id>` manage them.
- `plori workflows list [--agent <name|id|none>]`,
  `plori workflows create <name> [--trigger cron --cron <expr>]`,
  `plori workflows run <name|id>` (run it now), `plori workflows execution <name|id> <exec-id>`.
- `plori credits`, `plori usage`, `plori disk` read account state.

## Costs and limits

Running an agent spends credits; check `get_credits` before invoking. Agent count and
model tier follow the account's plan. Every call is scoped to the account that owns the
credential; there is no cross-account access.

## More

- Integration entry point: https://plori.ai/agents.md
- MCP connect guide: https://plori.ai/mcp
- CLI on npm: https://www.npmjs.com/package/@plori/cli
- Authentication detail: https://plori.ai/auth.md
- Site map for agents: https://plori.ai/llms.txt
