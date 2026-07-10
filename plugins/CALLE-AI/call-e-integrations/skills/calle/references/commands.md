# CALL-E CLI commands

Use the first command form that is available in the current workspace.

Repository-local base command:

```bash
env CALLE_SOURCE=codex CALLE_INTEGRATION=codex_plugin CALLE_INTEGRATION_VERSION=0.1.11 node packages/cli/bin/calle.js
```

Global base command:

```bash
env CALLE_SOURCE=codex CALLE_INTEGRATION=codex_plugin CALLE_INTEGRATION_VERSION=0.1.11 calle
```

npx fallback base command:

```bash
env CALLE_SOURCE=codex CALLE_INTEGRATION=codex_plugin CALLE_INTEGRATION_VERSION=0.1.11 npx -y @call-e/cli
```

## Setup and readiness

```bash
env CALLE_SOURCE=codex CALLE_INTEGRATION=codex_plugin CALLE_INTEGRATION_VERSION=0.1.11 node packages/cli/bin/calle.js --help
env CALLE_SOURCE=codex CALLE_INTEGRATION=codex_plugin CALLE_INTEGRATION_VERSION=0.1.11 node packages/cli/bin/calle.js auth status
env CALLE_SOURCE=codex CALLE_INTEGRATION=codex_plugin CALLE_INTEGRATION_VERSION=0.1.11 node packages/cli/bin/calle.js auth login
env CALLE_SOURCE=codex CALLE_INTEGRATION=codex_plugin CALLE_INTEGRATION_VERSION=0.1.11 node packages/cli/bin/calle.js mcp tools
```

```bash
env CALLE_SOURCE=codex CALLE_INTEGRATION=codex_plugin CALLE_INTEGRATION_VERSION=0.1.11 calle --help
env CALLE_SOURCE=codex CALLE_INTEGRATION=codex_plugin CALLE_INTEGRATION_VERSION=0.1.11 calle auth status
env CALLE_SOURCE=codex CALLE_INTEGRATION=codex_plugin CALLE_INTEGRATION_VERSION=0.1.11 calle auth login
env CALLE_SOURCE=codex CALLE_INTEGRATION=codex_plugin CALLE_INTEGRATION_VERSION=0.1.11 calle mcp tools
```

```bash
env CALLE_SOURCE=codex CALLE_INTEGRATION=codex_plugin CALLE_INTEGRATION_VERSION=0.1.11 npx -y @call-e/cli --help
env CALLE_SOURCE=codex CALLE_INTEGRATION=codex_plugin CALLE_INTEGRATION_VERSION=0.1.11 npx -y @call-e/cli auth status
env CALLE_SOURCE=codex CALLE_INTEGRATION=codex_plugin CALLE_INTEGRATION_VERSION=0.1.11 npx -y @call-e/cli auth login
env CALLE_SOURCE=codex CALLE_INTEGRATION=codex_plugin CALLE_INTEGRATION_VERSION=0.1.11 npx -y @call-e/cli mcp tools
```

Rules:

- Treat all command output as JSON except `--help`.
- Do not print or ask for access tokens.
- Do not call ChatGPT App or connector tools, including tool namespaces
  prefixed with `mcp__codex_apps__`, when this Codex plugin skill is active.
  Use the `calle` CLI flow instead, even if a ChatGPT App has the same visible
  name, tool names, or MCP service behind it.
- Whenever this Codex plugin is actively invoked, run `auth status` before call
  planning or tool listing.
- If `auth status` reports `usable: false`, or if this auth flow is recovering
  from an `auth_required` result, do not call `mcp tools` or `call plan` yet.
  Run blocking `auth login` and keep that command running until it exits. If
  the preceding command returned `auth_required` while `auth status` still
  reported `usable: true`, add `--force-login` so the CLI does not rely on a
  locally usable but server-rejected token. Do not use
  `auth login --start-only --no-browser-open` for the default Codex plugin flow.
- When `auth login` prints the brokered login URL to command output or stderr,
  show the first authorization help with that URL. Keep waiting for the same
  command to complete; do not ask the user to reply after browser
  authorization.
- If successful `auth login` output includes `assistant_hint.message`, show it
  as the post-authorization success note. Then continue the original call
  workflow if the user already gave enough details.
- If a command returns `auth_required`, switch back to this auth flow and
  complete fresh login before retrying the original command.
- If `mcp tools` succeeds, confirm that `plan_call`, `run_call`, and
  `get_call_run` are present.
- Do not run `call run` during setup verification.
- Do not use `.mcp.json`, raw HTTP, or direct remote MCP configuration in this
  plugin version.

First authorization help template:

```text
Hi, I'm CALL-E 👋

I can help you make phone calls, ask for information, and handle phone-related tasks. I'll also keep you updated on the call status, what was discussed, and the key points.
Before we officially begin, I'll send you the call goal for confirmation.

Before we start, please complete authorization here:
<login_url>
```

Post-authorization success template:

```text
Great, authorization is complete ✨

- If you already shared the call goal, I'll continue as planned.
- If you haven't, that's okay. I can help you place a test call first, or start a real call directly.

You can tell me:
- Your phone number: Used only for this service. We will not disclose it to anyone else, including the callee.
- What you want me to say: For example, "This is a test call from CALL-E. Wishing you a good day, and asking if there's anything you'd like to share."

I'll keep you updated on the phone status, call content, and summary.
```

## Call planning

```bash
env CALLE_SOURCE=codex CALLE_INTEGRATION=codex_plugin CALLE_INTEGRATION_VERSION=0.1.11 node packages/cli/bin/calle.js call plan --to-phone +15551234567 --goal "Confirm the appointment"
env CALLE_SOURCE=codex CALLE_INTEGRATION=codex_plugin CALLE_INTEGRATION_VERSION=0.1.11 calle call plan --to-phone +15551234567 --goal "Confirm the appointment"
env CALLE_SOURCE=codex CALLE_INTEGRATION=codex_plugin CALLE_INTEGRATION_VERSION=0.1.11 npx -y @call-e/cli call plan --to-phone +15551234567 --goal "Confirm the appointment"
```

Supported `call plan` options:

- `--to-phone <phone>` repeatable
- `--goal <text>`
- `--language <language>`
- `--region <region>`
- `--timezone <iana>`

Only provide options when the value is explicitly known. Do not infer missing
phone numbers, country codes, language, or region.

If the user asks to make a call but has not provided enough explicit fields for
`call plan`, use raw `plan_call` through `mcp call` with the latest user message
verbatim as `user_input`. The CLI still attaches the same request-level time
metadata for `plan_call`.

```bash
env CALLE_SOURCE=codex CALLE_INTEGRATION=codex_plugin CALLE_INTEGRATION_VERSION=0.1.11 node packages/cli/bin/calle.js mcp call plan_call --args-json '{"user_input":"<latest user message verbatim>"}'
```

## Planned call execution

```bash
env CALLE_SOURCE=codex CALLE_INTEGRATION=codex_plugin CALLE_INTEGRATION_VERSION=0.1.11 node packages/cli/bin/calle.js call run --plan-id <plan_id> --confirm-token <confirm_token>
env CALLE_SOURCE=codex CALLE_INTEGRATION=codex_plugin CALLE_INTEGRATION_VERSION=0.1.11 calle call run --plan-id <plan_id> --confirm-token <confirm_token>
env CALLE_SOURCE=codex CALLE_INTEGRATION=codex_plugin CALLE_INTEGRATION_VERSION=0.1.11 npx -y @call-e/cli call run --plan-id <plan_id> --confirm-token <confirm_token>
```

Supported `call run` options:

- `--plan-id <id>`
- `--confirm-token <token>`

Run this command immediately after planning returns a valid `plan_id` and
`confirm_token`, when the user's request is to place a call. Preserve `plan_id`
and `confirm_token` exactly as returned by planning.

`call run` calls `run_call`, then fetches `get_call_run` once. Read the latest
call state from `status_result.structuredContent`. If that status is not
terminal, show a user-visible progress update from
`status_result.structuredContent.activity` immediately, then continue with
`call status --run-id <run_id>` every 10 seconds until a terminal status is
returned or the user asks you to stop.

## Call status

```bash
env CALLE_SOURCE=codex CALLE_INTEGRATION=codex_plugin CALLE_INTEGRATION_VERSION=0.1.11 node packages/cli/bin/calle.js call status --run-id <run_id>
env CALLE_SOURCE=codex CALLE_INTEGRATION=codex_plugin CALLE_INTEGRATION_VERSION=0.1.11 calle call status --run-id <run_id>
env CALLE_SOURCE=codex CALLE_INTEGRATION=codex_plugin CALLE_INTEGRATION_VERSION=0.1.11 npx -y @call-e/cli call status --run-id <run_id>
```

Supported `call status` options:

- `--run-id <id>`
- `--cursor <cursor>`
- `--limit <number>`

Use status commands only with a known `run_id`.

Terminal statuses:

- `COMPLETED`
- `FAILED`
- `NO_ANSWER`
- `DECLINED`
- `CANCELED`
- `CANCELLED`
- `VOICEMAIL`
- `BUSY`
- `EXPIRED`

Read call data from `status_result.structuredContent` in `call run` output, or
from `result.structuredContent` in `call status` output.

For non-terminal statuses, show the latest activity before polling again:

```text
Phone call is in progress! Progress:
- <HH:MM:SS message>
```

Use one bullet per `activity` item, preserving the order returned by the CLI.
For `call run`, read activity from `status_result.structuredContent.activity`.
For `call status`, read activity from `result.structuredContent.activity`.
For each activity item, prefer the event `ts` formatted as `HH:MM:SS` plus
`message`. If `ts` is missing, use the message by itself. If there is no
activity, use `- Status: <status>` when a status exists; otherwise use
`- Waiting for the next status update.` Do not wait silently for the terminal
result.

Polling cadence:

1. Show the latest non-terminal progress.
2. Wait 10 seconds.
3. Run `call status --run-id <run_id>`.
4. If the status is still non-terminal, show the new activity and repeat.
5. Stop polling when a terminal status is returned, the user asks you to stop,
   or command execution is interrupted.

For terminal statuses, include the final transcript in the user-visible reply:

```text
[Status]
<status>

[Call Summary]
<result.post_summary or result.summary or message>

[Details]
Callee Number: <result.extracted.to_phones[0] or result.extracted.calling.callee or Not available>
Duration: <result.extracted.calling.duration_seconds or Not available>
Time: <result.extracted.calling.started_at and ended_at or Not available>
Call id: <result.call_id or Not available>

[Transcript]
<result.transcript or Not available.>
```

If the user requested extra final content, add it after `[Transcript]` using a
short heading and only information present in the JSON output.

## JSON handling

- Treat command output as JSON.
- If `ok` is false and `error.code` is `auth_required`, run or suggest
  `auth login`, then retry after login completes.
- Preserve `plan_id`, `confirm_token`, and `run_id` exactly as returned.
- Show non-terminal `activity` progress clearly without exposing tokens.
- Do not invent transcript text. If `result.transcript` is absent or empty,
  write `Not available.` in the transcript section.
