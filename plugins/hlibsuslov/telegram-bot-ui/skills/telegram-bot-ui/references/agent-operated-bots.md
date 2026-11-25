---
summary: "An AI agent working through its own Telegram bot: notifications, status cards, streaming, approvals, ask-and-wait, artifacts, topics, update intake, hooks; read when the bot is the agent's interface."
verified: "2026-11-15"
bot_api: "10.4"
---

# Agent-operated bots: an AI agent working through its own Telegram bot

> Verified 2026-11-15 against Bot API **10.4** (2026-11-09; still the newest version in
> the official changelog on that date), the Claude Code hooks reference and the Codex
> hooks/config reference. Tags: **[API]** = Bot API requirement, **[Official]** =
> official recommendation, **[Heuristic]** = design heuristic of this skill.

## Contents

- [Pick the pattern](#pick-the-pattern)
- [One-way notification](#one-way-notification)
- [Status card for a long task](#status-card-for-a-long-task)
- [Streamed answer with Stop](#streamed-answer-with-stop)
- [Approval request](#approval-request)
- [Ask and wait for an answer](#ask-and-wait-for-an-answer)
- [Choices and forms](#choices-and-forms)
- [Delivering artifacts](#delivering-artifacts)
- [Live dashboard widget](#live-dashboard-widget)
- [Parallel jobs in private-chat topics](#parallel-jobs-in-private-chat-topics)
- [Working in a team group](#working-in-a-team-group)
- [Receiving commands and free text](#receiving-commands-and-free-text)
- [Update intake: polling, webhook, restart](#update-intake-polling-webhook-restart)
- [Coding-agent hooks](#coding-agent-hooks)
- [Recipes](#recipes)

This file is for the case where **the bot is the agent's interface**: a coding agent,
CI job or autonomous worker reports to its human operator, asks, waits, requests approval
and takes commands over Telegram. (Building a bot *product* for end users is the rest of
this skill.) Security rules are in `agent-bot-security.md` — read both.

Code: `examples/python/agent_bridge/` (library + CLI `py -3 -m agent_bridge …`, run from
`examples/python`), MCP server `examples/mcp/telegram-bridge/`, TypeScript core
`examples/ts/agent-bridge/`. Recipes 40–49: [index](#recipes).

## Pick the pattern

| Need | Pattern | API |
|---|---|---|
| "FYI, done" | [one-way notification](#one-way-notification) | `sendMessage` (+ `disable_notification`) |
| Long job, several stages | [status card](#status-card-for-a-long-task) | `sendMessage` once, then `editMessageText` |
| Long generated answer | [streamed answer with Stop](#streamed-answer-with-stop) | `sendMessageDraft` / `sendRichMessageDraft` + `can_stop` |
| Must not proceed without a human | [approval request](#approval-request) | inline buttons, `style`, `disabled`, `answerCallbackQuery` |
| Need a fact or a choice | [question and wait](#ask-and-wait-for-an-answer) | `force_reply` (ForceReply or on InlineKeyboardMarkup) |
| Several fields | [choices and forms](#choices-and-forms) | buttons + `force_reply`, recipe 03 |
| Files, diffs, logs, tables | [artifacts](#delivering-artifacts) | `sendDocument`, `sendRichMessage` |
| Live overview of running jobs | [dashboard widget](#live-dashboard-widget) | `sendWidget`, `editMessageWidgetData` |
| Parallel jobs | [one topic per job](#parallel-jobs-in-private-chat-topics) | `createForumTopic` in the private chat, `message_thread_id` |
| Team chat | [group mode](#working-in-a-team-group) | ephemeral replies (`ephemeral_message_parameters`) |
| Operator steers the agent | [commands and free text](#receiving-commands-and-free-text) | fixed command table; text as data |
| Getting updates at all | [intake](#update-intake-polling-webhook-restart) | `getUpdates` + `allowed_updates`, or webhook + `secret_token` |

## One-way notification

* Plain text by default (no `parse_mode`): agent output must never become markup. If you
  format, escape with the format's own escaper (`references/security-and-escaping.md`).
* `disable_notification: true` for digests and "turn finished"; loud only when a human must act. **[Heuristic]**
* Text limit 1–4096 characters after entity parsing **[API]**. Longer: split at safe points
  (`tgkit.text.split_text`); more than ~3 parts → send a document instead **[Heuristic]**.
* Redact before sending (`agent_bridge.redact`): bot tokens, API keys, `password=…`.
* CLI: `py -3 -m agent_bridge notify "Deploy finished" --silent`.

## Status card for a long task

One message per job, edited in place (`AgentBridge.progress`, recipe 41):

* **Named real stages** (`Install → Compile → Unit tests → E2E → Package`) with ✅ / ⏳ / ▫️ /
  ❌ marks — never an invented percentage **[Heuristic]**.
* Throttle: a stage change waits ≥ 3 s after the previous edit, a note-only change ≥ 15 s;
  the final state is never throttled **[Heuristic]**. In recipe 41, 179 runner events become 45 edits.
* Skip no-op edits: compare the card *without* the elapsed-time clock. "message is not
  modified" is treated as success; "message to edit not found" (the operator deleted it) → send a new card.
* Edits do not notify, so finishing sends one short reply to the card ("CI #142: failed in 12m"). **[Heuristic]**
* Card ids live in the state file, so a restarted job edits the same card.
* Honour `retry_after` on 429 (shared policy: `tgkit.errors.call_with_policy`).

## Streamed answer with Stop

For a long generated answer in the **private chat** (drafts are private-only **[API]**):

* `sendRichMessageDraft` (or `sendMessageDraft`) with the same non-zero `draft_id` for the
  whole answer, `can_stop: true` to show Stop; Stop arrives as
  `Update.stopped_message_generation` → `MessageGenerationStopped{chat, message_thread_id?, draft_id}` **[API]**.
* A draft is "a temporary 30-second preview"; persist the result with `sendRichMessage` /
  `sendMessage` **[API]**. `keep_on_stop` keeps the draft only "for a short time".
* **What Stop must cancel in the agent's own work**: the model stream (close the generator /
  abort the request), queued tool calls, subprocesses started for this answer, and any
  follow-up messages. Then one final message (keep the partial answer marked as stopped).
  Recipe 44 asserts zero tokens and zero tool calls after Stop.
* Subscribe: `stopped_message_generation` in `allowed_updates` **[API]**.
* State machine and races: `tgkit.generation`, `references/streaming-and-editing.md`.

## Approval request

`AgentBridge.approve` / CLI `approve` (exit 0 approved, 3 rejected, 4 expired), recipe 40:

* Message: what will happen, scope, irreversibility, expiry ("Expires in 15 min. No answer = not approved").
* Buttons: **Approve** (`style: "success"`, or `"danger"` when the action is irreversible),
  **Reject** (no style), **Details** (never decides; short details as an alert ≤ 200 chars
  **[API]**, long ones as a message). `style` is only `primary`/`success`/`danger` **[API]**.
* Every tap is answered with `answerCallbackQuery` (wrong person: `show_alert: true`).
* After the decision, replace the keyboard with one disabled button that states the result —
  `{"text": "Approved by Alice", "disabled": {}}` (10.3, `DisabledButton` "does nothing") **[API]**.
* Binding, idempotency, who may approve, expiry: `agent-bot-security.md#approval-binding`.
* Only `approved` means go. `rejected`, `expired`, a crash or an unknown outcome → do not run. **[Heuristic]**

## Ask and wait for an answer

`AgentBridge.ask` / CLI `ask` (exit 0 answered, 4 timeout), recipe 43:

* Free text: `reply_markup: {"force_reply": true, "input_field_placeholder": "…"}`
  (placeholder 1–64 chars **[API]**). The answer is the reply whose
  `reply_to_message.message_id` is the question.
* Quick choices plus typing: inline buttons **and** `force_reply: true` on the
  `InlineKeyboardMarkup` (10.3). Its value "can't be changed when the inline keyboard is
  edited" **[API]** — keep it in the closing edit.
* Always a timeout; state the default in the question; one reminder (a reply to the question);
  on timeout close the question visibly ("No answer — continued with: main") and return
  `used_default: true`. **[Heuristic]**
* The answer is **untrusted data** (`content_is_untrusted_data`, `injection_signals`).
  Forwarded messages never answer.
* Resume after a restart: `wait <request_id>` with the same `--state` file.

## Choices and forms

One decision → buttons. Two or more fields → a form (recipe 03: `force_reply`, disabled
"Submit" until valid). Long forms → a Mini App. Never ask the operator for secrets in chat;
the agent reads them from its own environment.

## Delivering artifacts

| Artifact | Send as |
|---|---|
| Log, diff, patch, coverage file | `sendDocument` (multipart; bots upload ≤ 50 MB **[API]**), caption = one-line summary |
| Report, comparison, test table | Rich Message (`sendRichMessage`, blocks: heading, paragraph, `table` with `is_compact`, `list` with `has_checkbox`/`is_checked`, `details` + `pre` for a log tail) |
| A few lines | a message |
| Output > ~3 messages | a `.txt` document **[Heuristic]** |

Rich Message Limits: 32 768 characters, 500 blocks, 16 levels, 50 media, 20 table columns
**[API]**. Over the limit → document. Rich rejected (old server/SDK) → same content as plain
text, logged as a fallback. Files are secret-scanned and go only to the operator's private chat.

## Live dashboard widget

An HTML widget (10.4) for several running jobs (recipe 45): `sendWidget` with `chat_data`,
updated only via `editMessageWidgetData` when the state changed (≥ 2 s apart **[Heuristic]**).
**Production: "widgets can be sent only to private chats"** and are protected content **[API]**;
groups, inline and forwards are test-server only. Always a caption (shown where widgets
aren't) and a text path. Limits and runtime: `references/widgets.md`.

## Parallel jobs in private-chat topics

`createForumTopic` works in "a private chat with a user"; a link
`https://t.me/<bot_username>/<message_thread_id>` "opens the topic only for the user"
**[API]**. One topic per job → its card, questions and answers stay together; route incoming
messages by `message_thread_id`. Drafts take `message_thread_id` too. Recipe 45.

## Working in a team group

* Shared card for everyone; personal details as **ephemeral replies** to the presser
  (`ephemeral_message_parameters: {callback_query_id}`, 10.4 short form; not in channel DM
  chats) **[API]**; recipe 46, `references/ephemeral-and-personal.md`.
* Logs, files, secrets and approvals' details never go to the group. **[Heuristic]**
* Only operators' ids approve; members may read and press read-only buttons.
* Privacy mode: by default a bot in a group sees commands addressed to it, replies to its
  messages, inline messages via it and service messages; admin bots see everything
  **[Official, Bot Features]**. Design for privacy mode on: use commands, replies (`force_reply`) and buttons.

## Receiving commands and free text

* A **fixed command table** (`status`, `help`, `pause <job>`, `resume <job>`, `stop <job>`,
  `ack <incident>`); arguments validated (`^[A-Za-z0-9_-]{1,32}$`); `/cmd@other_bot` ignored.
* Everything else is data for the agent, flagged untrusted. Forwarded `/stop` is text, not a command.
* `listen` yields JSON lines: `py -3 -m agent_bridge listen --state s.json --live`.

## Update intake: polling, webhook, restart

* **Long polling** for an agent process (laptop, CI runner, behind NAT): `getUpdates` with
  `timeout` 25, explicit `allowed_updates`, `offset` = last `update_id` + 1 **[API]**.
* getUpdates "will not work if an outgoing webhook is set up"; updates are kept "not longer
  than 24 hours" **[API]**. One poller per token.
* `allowed_updates` is sticky; always send the full list: `message`, `callback_query`,
  `my_chat_member`, `stopped_message_generation` (+ `widget_query` if widgets take queries).
* **Webhook** only for an always-on HTTPS service: `secret_token` (1–256 chars) arrives as
  `X-Telegram-Bot-Api-Secret-Token` **[API]** — compare in constant time, 401 otherwise; answer fast.
* **Restart safety:** persist offset, recent `update_id`s (dedup), pending requests and card
  ids (`agent_bridge.store`, atomic writes). Mark an update seen only after its handler ran.

## Coding-agent hooks

Claude Code (`settings.json` → `hooks`): `Notification` (stdin `message`, `title`,
`notification_type`; can't block), `Stop` (`last_assistant_message`, `stop_hook_active`),
`PermissionRequest` (answer `hookSpecificOutput.decision.behavior` allow/deny; no decision →
normal prompt; default command-hook timeout 600 s). Codex (`hooks.json` / `[hooks]`,
`features.hooks`, hooks must be trusted): `Stop` expects JSON on stdout, `PermissionRequest`
uses the same decision shape; `notify` gets "a JSON payload" whose fields were not verified.
Commands and configs: recipe 48.

## Recipes

| # | Recipe | Shows |
|---|---|---|
| 40 | [Deploy approval gate](../recipes/40-deploy-approval-gate.md) | approve/reject/expire, binding, group approvers |
| 41 | [Long build with live status](../recipes/41-build-live-status.md) | throttled card, final report, log document |
| 42 | [Nightly digest](../recipes/42-nightly-digest.md) | silent rich report, loud on failure, plain fallback |
| 43 | [Ask and continue](../recipes/43-ask-and-continue.md) | choices + force_reply, reminder, default |
| 44 | [Streamed answer with Stop](../recipes/44-streamed-research-stop.md) | draft, Stop cancels own work |
| 45 | [Multi-job dashboard with topics](../recipes/45-multi-job-dashboard-topics.md) | topics, widget dashboard |
| 46 | [Team group, personal replies](../recipes/46-team-group-personal-replies.md) | ephemeral, no files in groups |
| 47 | [Incident alert](../recipes/47-incident-alert.md) | acknowledge/escalate, timed escalation |
| 48 | [Coding-agent hooks](../recipes/48-coding-agent-hooks.md) | Claude Code / Codex hook wiring |
| 49 | [Intake and security drill](../recipes/49-intake-security-drill.md) | polling, restart, strangers, webhook |
