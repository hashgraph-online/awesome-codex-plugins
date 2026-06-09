---
name: calle
description: Use CALL-E from Codex through the calle CLI. Use for CALL-E setup checks, authentication recovery, phone call planning, planned call execution, and call status checks.
license: MIT
---

# CALL-E

Use this skill when the user wants Codex to use CALL-E through the `calle` CLI.
This plugin version intentionally calls the CLI instead of configuring Codex to
connect directly to the remote MCP server.

## When to use

Use this skill for:

- verifying CALL-E setup in Codex
- checking whether the `calle` CLI is available
- recovering from missing or expired CALL-E authentication
- listing available CALL-E MCP tools through the CLI
- planning a phone call
- running a planned call after planning returns complete run credentials
- checking a call run status
- reporting the final call summary, details, and transcript when a call reaches
  a terminal status

Do not use this skill when the user only wants a call script, roleplay,
simulated conversation, or general contact lookup that does not require CALL-E.

## Tool routing

When this Codex plugin skill is active, use only the `calle` CLI flow documented
below. Do not call ChatGPT App or connector tools, including tool namespaces
prefixed with `mcp__codex_apps__`, even if a ChatGPT App has the same visible
name, tool names, or MCP service behind it.

If a same-name ChatGPT App is available, treat it as a separate integration.
This Codex plugin still routes through the local CLI so Codex plugin
authentication, attribution, and safety behavior remain isolated from ChatGPT
App execution.

## Safety and consent

- Real phone calls may contact external people or businesses.
- Do not place a real call unless the user clearly intends to do so.
- Always plan first.
- If the user asked to place a call, run it immediately after planning returns
  a valid `plan_id` and `confirm_token`.
- If the user asked only to verify setup or only to plan, do not run the call.
- Do not guess phone numbers, country codes, language, region, `plan_id`,
  `confirm_token`, or `run_id`.
- Do not print, request, or expose access tokens.

## CLI selection

All CLI commands run from this Codex plugin must include the CALL-E integration
attribution environment:

```bash
env CALLE_SOURCE=codex CALLE_INTEGRATION=codex_plugin CALLE_INTEGRATION_VERSION=0.1.10
```

Use the first command form that works.

Prefer the repository-local CLI when the current workspace contains it:

```bash
env CALLE_SOURCE=codex CALLE_INTEGRATION=codex_plugin CALLE_INTEGRATION_VERSION=0.1.10 node packages/cli/bin/calle.js
```

If the repository-local CLI is unavailable, use the global command:

```bash
env CALLE_SOURCE=codex CALLE_INTEGRATION=codex_plugin CALLE_INTEGRATION_VERSION=0.1.10 calle
```

If neither command works, use the npm package through `npx`:

```bash
env CALLE_SOURCE=codex CALLE_INTEGRATION=codex_plugin CALLE_INTEGRATION_VERSION=0.1.10 npx -y @call-e/cli
```

Only tell the user to install the CLI globally if `npx` is unavailable,
network access is blocked, or the user explicitly wants a persistent global
command.

## Readiness flow

Use this flow whenever this Codex plugin is actively invoked for a CALL-E
request. Run it before call planning, before tool listing, when setup is
uncertain, when auth fails, or when the user asks to verify CALL-E setup:

1. Check CLI availability with `--help`.
2. Run `auth status`.
3. If `auth status` reports `usable: false`, do not continue to call planning
   or `mcp tools` yet. Run blocking `auth login` and keep that command running
   until it exits. Do not use `auth login --start-only --no-browser-open` for
   the default Codex plugin flow.
4. When `auth login` prints the brokered login URL to command output or stderr,
   immediately show the first authorization help with that URL. Keep waiting
   for the same `auth login` command to complete; do not ask the user to reply
   after browser authorization.
5. If the successful `auth login` JSON included `assistant_hint.message`, show
   that post-auth success message in the next user-facing reply. If the user
   already gave a call goal, continue the original workflow after the message;
   otherwise ask for the phone number and call goal, or offer a test call.
6. After login completes, run `mcp tools`.
7. Confirm that `plan_call`, `run_call`, and `get_call_run` are available.

Setup verification must not place a real phone call. Use only help, auth, and
tool-listing commands until the user asks for a call workflow.

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

## Call flow

1. Use `call plan` first.
   If the user has not provided enough explicit fields for `call plan`, use
   `mcp call plan_call --args-json '{"user_input":"<latest user message verbatim>"}'`
   so CALL-E can ask for the missing details.
2. Read the returned `plan_id` and `confirm_token`.
3. If the user's request is to place a call, immediately use `call run` with
   the exact `plan_id` and `confirm_token` returned by planning.
4. Do not ask for a second confirmation between `call plan` and `call run`.
5. Read the returned `run_id` and latest call status. In `call run` output, the
   latest call state is in `status_result.structuredContent`. In `call status`
   output, the latest call state is in `result.structuredContent`.
6. If the latest status is not terminal, immediately show a user-visible
   progress update from the latest activity data before polling again. Use
   `status_result.structuredContent.activity` after `call run`, or
   `result.structuredContent.activity` after `call status`.
7. Keep using `call status` with that exact `run_id` until the call reaches a
   terminal status or the user asks you to stop. Poll every 10 seconds: after
   each non-terminal response, show the latest activity progress, wait 10
   seconds, then fetch `call status` again. Do not stay silent until a terminal
   status.
8. Use `call status` only with a known `run_id`.

Terminal statuses include `COMPLETED`, `FAILED`, `NO_ANSWER`, `DECLINED`,
`CANCELED`, `CANCELLED`, `VOICEMAIL`, `BUSY`, and `EXPIRED`.

For non-terminal statuses, reply with progress in this shape:

```text
Phone call is in progress! Progress:
- <HH:MM:SS message>
```

Use one bullet per `activity` item, preserving the order returned by the CLI.
For each item, prefer the event `ts` formatted as `HH:MM:SS` plus `message`.
If `ts` is missing, use the message by itself. If there is no activity, use
`- Status: <status>` when a status exists; otherwise use
`- Waiting for the next status update.` Do not include the final summary,
details, or transcript until a terminal status is returned.

The polling cadence is: show progress, wait 10 seconds, run `call status`, show
new progress if still non-terminal, then repeat. Stop polling immediately when
the user asks you to stop, when a terminal status is returned, or when command
execution is interrupted.

When the call reaches a terminal status, reply with the final call result,
including these sections in this order:

```text
[Status]
<status>

[Call Summary]
<post_summary or summary or message>

[Details]
Callee Number: <primary callee or Not available>
Duration: <duration or Not available>
Time: <start/end time or Not available>
Call id: <call_id or Not available>

[Transcript]
<transcript or Not available.>
```

If the user asked for extra final content, such as key takeaways or next steps,
add it after `[Transcript]` under a short heading. Base all final sections only
on the JSON returned by `call run` or `call status`; do not invent a transcript.

If any command returns `auth_required`, switch to the readiness flow, complete
login, and then retry the original operation after login completes.

Use `references/commands.md` for exact command examples, supported options, and
JSON handling rules.
