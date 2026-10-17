---
name: plori
description: Runs tasks on Plori cloud agents that continue after the chat ends, such as background or parallel builds, scheduled automations, long jobs and research saved as files. Not for quick tasks.
---

# Using plori from an agent

If you were asked to set up plori, follow Connect below: add the plori MCP server to this
client, have the account owner sign in, and confirm the tools respond before you report
success.

Plori runs AI agents in cloud Workspaces. Several agents can work on one project at once, and
Plori merges their changes back into the Workspace. A Workspace holds a project's files under
`/workspace`, saved versions of those files, a main conversation and the run history.

## Connect

If this client already lists Plori tools and `list_workspaces` answers, skip this section.

MCP: Streamable HTTP at `https://api.plori.ai/mcp`.

- OAuth 2.1: an unauthenticated request returns 401 with the discovery chain (RFC 9728
  metadata at https://api.plori.ai/.well-known/oauth-protected-resource, dynamic client
  registration, authorization code + PKCE). The account owner signs in with an email code.
- API key: the account owner creates one at https://plori.ai. Send
  `Authorization: Bearer plori_sk_...`.

### Claude Code: connect from this conversation

Read these instructions in the current conversation before starting authentication.
Installing a skill or plugin is optional. Use this flow only in interactive Claude Code
when its Plori MCP client exposes both `authenticate` and `complete_authentication`.
Other clients use their ordinary OAuth or API-key setup above.

If this Claude Code build does not expose both `authenticate` and
`complete_authentication`, use `/mcp` instead. Pick plori, choose Authenticate, then
sign in with the emailed code. If the browser cannot reach the localhost callback,
Claude Code prompts for it directly in its own dialog, never in chat. Then verify with
`list_workspaces`.

1. Check the current MCP configuration and active tools. Reuse an existing Plori server
   at `https://api.plori.ai/mcp`; do not add duplicate entries or replace a different
   server with the same name. If missing, configure it once with
   `claude mcp add --transport http plori https://api.plori.ai/mcp`.
   Confirm the server is available in this conversation before authenticating. Saving
   configuration alone does not prove that it loaded. If its tools are missing, ask
   the user to type `/reload-plugins` in this Claude Code conversation, then resume
   these steps in the same session. This also refreshes MCP configuration when no
   plugins are installed. It is a user command; do not try to invoke it through the
   Skill tool. Confirm the authentication tools are available before proceeding. If they
   are still missing, use `/mcp` instead (above).
2. If Plori tools already work, the connection is complete. Otherwise, call the
   client's Plori `authenticate` tool using its exposed schema. Keep the returned
   authorization URL intact. Do not construct a new OAuth request or change its state,
   redirect URI, or PKCE challenge.
3. POST JSON `{"authorization_url":"<the exact client URL>"}` once to
   `https://api.plori.ai/oauth/pair`. The response contains `user_code`,
   `verification_uri`, `verification_uri_complete`, `device_code`,
   `expires_in` (seconds), and `interval` (seconds). Keep `device_code` private.
   If a permission rule, hook, or tool denies this request, stop and use the fallback below.
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
   If a permission rule, hook, or tool denies a poll request, stop and use the fallback below.
6. On `status: "approved"`, pass the returned `callback_url` directly to the same client's
   `complete_authentication` tool using its exposed schema. Do not navigate to the
   loopback URL or exchange the code yourself: the client owns the PKCE verifier.
   Then discover Plori tools and call `list_workspaces` to confirm the connection before
   reporting success. This verification does not create a Workspace or start paid work.

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
4. Discover Plori tools and call `list_workspaces` before reporting success. This check
   does not create a Workspace or start paid work.

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

#### Switch accounts or sign out

To connect a different Plori account or sign out, use `/mcp`. Pick plori, choose Clear
authentication, then Authenticate again with the new account's email code.
`claude mcp remove` does not clear the stored token.

### CLI and REST

CLI: `curl -fsSL https://plori.ai/install.sh | sh` (Windows: `irm https://plori.ai/install.ps1 | iex`),
`npm i -g @plori/cli`, or `npx -y @plori/cli`. The shell installer writes to
`~/.local/bin` and edits no rc file, so run `export PATH="$HOME/.local/bin:$PATH"` first.
`plori login` signs in through the browser; headless callers use
`plori login --key plori_sk_...` or set `PLORI_API_KEY`. Piped output and `--json` give
JSON.

REST: `https://api.plori.ai/v1` with the same bearer token. Detail: https://plori.ai/auth.md

## Tools

The MCP server has 23 tools. Invitees use their own login, API keys and OAuth
sessions. Workspace calls resolve access to the owning account from the resource.

### Workspaces

- `list_workspaces` lists your own and shared Workspaces with `account`
  (`user_id`, `email`) and your `role` (`owner`, `member` or `viewer`).
  Pass `workspace_id` for one. `storage_readiness` is present while its storage starts.
- `create_workspace` (`name`, `idempotency_key`) returns `id` and `default_agent_id`,
  the Workspace's agent. Without `default_manager_agent_id` it creates that agent, which
  counts against the agent limit. Optional `account` selects a shared account by user id.
  Omit it for your own account. Members can create there. Viewers cannot. The result
  includes `account` and `role`. Names are not unique: reuse a Workspace.
- `delete_workspace` permanently deletes its files, saved versions, copies and
  conversations.
- `get_credits` returns the balance. Check it before long work.

### Send a task

`send_workspace_message` (`workspace_id`, `message`) runs a task in the Workspace's main
conversation, or in the one named by `session_id`. Use it for most work, including work
that can be split: the Workspace's own agent splits it between several agents, merges their
changes and fixes conflicts.

- For a new or continued run, the call holds until the run ends, pauses for input,
  or the hold ends. The server picks a hold that fits your client. Use that default.
- If the result is `running`, call `get_run_result` (`workspace_id`, `run_id`) after
  `poll_after_seconds`. Repeat until the run completes or is `awaiting_input`.
- `get_run_result`, `cancel_run`, `list_runs`, `list_pending_inputs` and
  `schedule_run` take the `workspace_id`.
- Reuse `session_id` to keep context. An idle conversation starts a run. While running,
  plain text returns `status: "steering"` or `"queued"` with `steer_id`.
- If the paused run has exactly one ordinary question assigned to you, your message
  answers it. Otherwise it queues, and `pending_inputs` names the request and assignee.
  A message never cancels a pending request. If the result has `status: "answered"`
  and `continuation_pending: true`, read the paused run until it reports
  `continuation_run_id`. Do not submit the answer again.
- A queued or steering receipt returns immediately, regardless of `wait`. It includes
  `run_id`, `session_id`, `agent_id`, `workspace_id`, `url` and `poll_after_seconds`.
  Its `run_id` is the running or paused run, not a result for this message. Use
  `list_runs` to find a later queued turn. No lookup connects `steer_id` to that run.
- 409 `conversation_busy` still applies to attachments or run options in a busy
  conversation, and to working-copy conflicts. Send attachments and options when idle.
- A retry with the same `idempotency_key` returns the original run or message receipt for 24 hours.
  `max_turn_tokens` sets an optional token ceiling for the turn. `cancel_run` stops a run.

### Files

- Only files under `/workspace` persist between runs. Software installed elsewhere and
  processes a run starts do not. Use `TMPDIR` for temporary files.
- A completed run does not prove its files are saved: wait for `file_source.state`
  `ready` with no `save_failure`.
- A completed run's `files` are URLs readable with the same bearer token.
  `read_workspace_file` reads a saved version: `current_revision`, an agent's
  `saved_revision_id`, or a changeset's `base_revision`, `incoming_revision` or
  `result_revision`. A path such as `/workspace/a.md` is not a URL.

### Approvals and questions

- A run started through MCP or a schedule pauses before each action outside the Workspace
  (connected-account and MCP writes, outbound HTTP writes, git push, publishing, deploys,
  email, public tunnels, irreversible browser actions, workflow activation) until the
  account owner approves that one action in the Plori web app.
- `awaiting_input` is an approval or a question. Show it to the human, with the approval's
  `approve_url`.
- You cannot approve or grant `always_allow`. `answer_pending_input` can only deny a
  request or answer a question. Never send secrets through it.
- Then follow the `continuation_run_id` from `get_run_result`. `answer_pending_input`
  returns the continuation's `run_id`, or `continuation_pending: true` while files save;
  then poll the paused run until `continuation_run_id` is set.
- `list_pending_inputs` is the current queue; an old run can keep `awaiting_input`. A
  `consent_tool` row is an outward write: only the human approves it or grants standing
  consent, in the web app.
- Requests go to the worker's creator, or to the owner for the manager. The owner can
  also answer a worker's request. Other members can read it and may answer after the
  account's timeout, 30 minutes by default. Viewers never answer. Standing grants and
  secret answers stay owner-only. `list_pending_inputs` includes `assigned_to`,
  `open_to_members_at` and `can_act` for the caller. Credential restrictions still apply.
- A member's monthly spend cap can refuse a new run with 402. Schedules, previews,
  workflows, Workspace settings and deletion are owner-only in M1.
- Clients with the MCP Tasks extension get a task handle instead. A returned call does not
  report later changes: poll, or keep a subscription.

### Scheduled runs

`schedule_run` (`workspace_id`, `prompt`, `delay_seconds` or an RFC3339 `fire_at`) returns
`status: "awaiting_confirmation"` and a `confirm_url`. Show the human the prompt, the time
and the `confirm_url`. The run is queued only after the owner confirms in the web app.

### Run several agents yourself

Only for a client that manages the agents itself. Each agent works on its own copy of the
files; your client completes or discards each merge.

1. `create_workspace_worker` (`workspace_id`, `task`, `idempotency_key`) returns
   `agent_id` and `task_group_id` at once; the agent queues while capacity is busy. Pass
   `task_group_id` to later calls to group their costs and stop request;
   `get_workspace_costs` reports cost. Worker agents do not count against the agent limit.
2. Poll `get_workspace_worker` or `list_workspace_workers` until `save_state` is `ready`.
   `get_run_result` (`run_id`, `workspace_id`) reads the reply and approval requests.
   `steer_workspace_worker` messages a running turn (409 `run_not_running` if it has not
   started, is paused or has ended). `cancel_run` stops one agent,
   `stop_workspace_task_group` a group.
3. `submit_workspace_changeset` submits the saved files; Plori merges them with the current
   files.
4. Poll `get_workspace_changeset` until `compared` is true. `phase` `review_ready`: ready
   to complete. `needs_resolution`: conflicts. `recompare_required`: submit again.
5. `accept_workspace_changeset` completes the merge (`expected_current_revision` = the
   `comparison_current_revision`; `validation_evidence` = 1-32 short statements of the
   checks you made). `reject_workspace_changeset` discards it. After accept, poll until
   `state` is `accepted` and `result_revision` is set.

Accept errors:

- 409 `current_revision_conflict`: another merge landed first. Submit again, then repeat
  steps 4 and 5.
- 409 `workspace_changeset_unresolved`: not computed yet, or it has conflicts. A merge with
  conflicts cannot be completed through MCP. To have conflicts fixed, send the task to the
  Workspace with `send_workspace_message`; its agent fixes conflicts.
- 409 `workspace_changeset_busy`: a run or file operation is active. Accept after it ends.

These agents pause before outward actions like other runs. Workflows, usage and disk
reports, trash and connected accounts are not on MCP; use the web app, REST or the CLI.

### Workspace CLI commands

The CLI also covers what MCP does not. Use exact IDs; there is no implicit active Workspace.
Groups: `workspace`, `independent-agent`, `copy`, `revision`, `workspace-files`,
`worker`, `task-group`, `changeset`, `operation`; `plori GROUP --help` lists actions and
flags. Commands that create something take `--idempotency-key KEY`. To complete a merge:
`plori changeset accept WORKSPACE_ID CHANGESET_ID --current-revision REVISION_ID
--evidence TEXT --idempotency-key KEY` with the `comparison_current_revision`. Writes to a
copy need the `--if-match` ETag you read. Use `--yes` (`agent-retire`,
`workspace delete`) only when the human authorized the action. Examples:
https://plori.ai/docs/cli

## Long runs

Use the default wait. If the result is `running`, call `get_run_result` after
`poll_after_seconds`, until the run completes or is `awaiting_input`.

Troubleshooting, optional: if your client drops the results of long calls, pass
`wait_seconds` with a shorter hold, or `wait=false`. In Codex, `tool_timeout_sec` on the
plori entry in `config.toml` sets how long a call can last. `plori watch` in a background
shell prints run endings and input requests.

## CLI commands

Agents are addressed by name or ID. Every command accepts `--json`.

- `plori run <name> "message"` waits for the reply; `--no-wait` returns a run ID.
  `plori result <name> <run-id> --wait` (bounded by `--wait-seconds`) reads the result.
- `plori watch` prints run endings and input requests as JSON lines. `plori inbox` lists
  what ended and what waits on you.
- `plori inputs <name>`; `plori answer <run-id> <tool-call-id> --approve|--deny|--value <v>`.
  Add `--always-allow` only on the human's explicit instruction.
- `plori schedules create <workspace> "prompt" --in <seconds>` (or `--at <rfc3339>`).
- `plori attach` is for a human at the keyboard; an agent uses `--read-only` to tail.

Exit codes of `run`, `result --wait` and `watch`: 0 succeeded, 1 API or runtime failure,
2 usage error, 3 credentials missing, rejected or expired, 4 control plane unreachable, 10
awaiting human input, 20 run error, 30 cancelled, 40 wait ran out with the run still going.

## Costs and limits

Runs spend credits. The plan sets included credits, disk, agent count, workflow limits and
the length of one run. Registered accounts have no limit on concurrent agent runs.
Anonymous trials allow at most 2 concurrent agent runs across their agents.
A third run makes `send_workspace_message` return 429 with advice to register free.
Registered accounts have no token ceiling per turn unless `max_turn_tokens` sets one.
`max_turn_seconds` sets a turn's time budget.

## More

- Integration entry point: https://plori.ai/agents.md
- MCP connect guide: https://plori.ai/mcp
- CLI on npm: https://www.npmjs.com/package/@plori/cli
- Authentication detail: https://plori.ai/auth.md
- Site map for agents: https://plori.ai/llms.txt
