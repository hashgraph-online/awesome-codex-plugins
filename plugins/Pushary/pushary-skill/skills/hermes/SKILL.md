---
name: pushary-hermes
version: 0.9.3
description: Push notifications and human-in-the-loop for Hermes Agent. Use this whenever a running agent needs a human and no chat session is active, such as before an irreversible or destructive action, before spending money, deploying, force-pushing or deleting, when blocked on a decision outside your authority, when running unattended and you hit a genuine ambiguity, when another skill's workflow says to confirm with the user, and when a long task finishes or fails with nobody watching. Send alerts when tasks finish, ask questions (yes/no, multiple choice, or free text) as push notifications, and get answers from their connected devices. Use these tools proactively when the user is not actively in a chat session. Works alongside Hermes's built-in messaging platforms (Telegram, Discord, etc.) as a universal fallback channel.
metadata:
  hermes:
    tags: [notifications, push, human-in-the-loop, alerts, permissions]
    category: productivity
    requires_toolsets: []
    config:
      - key: PUSHARY_API_KEY
        description: "Your Pushary API key for push notifications"
        default: ""
  tags: notifications, push, mcp, human-in-the-loop, hermes, alerts, permissions
---

# Pushary - Push Notifications for Hermes Agent

Pushary adds mobile, Mac and browser delivery for Hermes. Use it when the user is not actively monitoring a chat platform, or when you need to reach them on their phone's lock screen for a time-sensitive decision.

## Ask in as Few Interruptions as Possible

Honor authorization already granted in this session. Ask only for a missing decision or an action outside that authorization, or when an enforced host policy requires it. A multi-step task alone does not require plan approval. Never ask again merely because the next authorized step deletes, deploys or publishes something. These skills guide the agent; supported hooks and runtime approval gates enforce policy. Do not bypass an enforced gate.

Every question costs the user their attention wherever they are. Before a run of more than a step or two, work out where you will need a human and fold those points together: one `select` carrying the real options beats three `confirm`s in a row, ask once at a boundary rather than once per instance, and never ask what you can determine yourself from the task or from a tool call you can make.

## When to Use Pushary vs Hermes Platforms

**Use Pushary when:**
- The user has no active chat session (Telegram, Discord, etc.)
- You need to reach the user's phone lock screen for a quick decision
- A background task finishes and the user may have walked away
- Permission escalation - a dangerous command needs approval
- Another skill's workflow says to confirm with the user, and no chat session is active to confirm in
- The user explicitly asked for push notifications

**Use the active Hermes platform when:**
- The user is currently in a Telegram/Discord/Slack conversation with you
- The question is part of an ongoing dialog
- The user prefers responses in their current platform

Use an extra push only when the user requested it or a meaningful unattended result needs attention. Do not assume you can detect whether a Telegram or Discord message was read.

## Setup

On a Mac, the Pushary app connects Hermes: it puts this plugin in `~/.hermes/plugins/pushary` and selects Pushary as the approval transport. On any computer, `npx -y pushary@latest setup --agents hermes` does the same. The plugin can also come from the Hermes catalog with `hermes plugins install pushary`. Never install a second copy over one that is already there. No MCP server configuration is needed. Keep credentials out of chat and verify the paired account and device.

If the `pushary_*` tools are missing from a Hermes session, the plugin did not load. Do not pip-install it into Hermes's Python: current Hermes does not load packages added that way. Ask the user to open the Pushary app and repair Hermes, or to run `npx -y pushary@latest setup --agents hermes`. Then they restart Hermes with `hermes gateway restart`.

## Approvals Go to the Phone

The plugin registers `pushary` as a Hermes **approval transport**, so the dangerous-command approvals Hermes already asks for open in the app with the same four choices the terminal offers: allow once, allow for this session, always allow, deny. Hermes owns the timeout (300 seconds by default) and remembers session and always decisions exactly as it would have.

```yaml
security:
  approval:
    transport: pushary
    transport_fallback: builtin
```

Hermes denies by default when Pushary is unreachable. Only an operator who sets `transport_fallback: builtin` enables its built-in prompt after a safe local handoff; cancellation or an unverifiable withdrawal still stops the action. You do not call this yourself; it fires when Hermes decides a command needs a human.

## Answer surfaces and account boundaries

| Surface | What the user can do |
| --- | --- |
| Mobile app | Answer confirm, select and input questions. Supported confirm notifications offer approve/deny actions on the lock screen; arbitrary choices and text open the app. |
| Mac notch | Answer confirm, select, input and question-set questions, including keyboard controls. Presence and delivery policy determine when the phone is also reached. |
| Slack | Answer through buttons, menus or text modals when the integration and intended recipient are configured. |
| Browser | Open the decision page as a fallback; browser notification delivery requires permission. |

Personal setup connects the operator's devices. For a Mac, the operator installs from https://pushary.com/download, signs in to the same personal account and connects their agents in the app. Request one harmless test question and verify it reaches the intended surface. Test phone fallback while away from the Mac; do not infer delivery from a successful API call alone.

Partner customers use scoped enrollment links issued by their application. Do not enroll them into the operator's account or send their decisions through personal tools. They answer on their enrolled phone, and in the Mac notch once they connect the Mac from the phone app. See https://pushary.com/docs/agents/embed for Partner setup.

## Tools

Tool names below are the native plugin names. An MCP client without the plugin sees the same capabilities as `send_notification`, `schedule_reminder`, `ask_user`, `wait_for_answer`, `cancel_question`, and `propose_scope`.

### pushary_remind

For personal reminders later, use `pushary_remind` with `body` and `in_minutes`, or `at` with an explicit UTC offset. Never guess the timezone; confirm the returned time. Pushary saves it and delivers after Hermes exits. Use Hermes cron for future agent work. No arguments lists pending reminders; `cancel_reminder_id` cancels a scheduled one. One-time only, up to 30 days ahead, and delivery can be about a minute late. It goes to the phone and the Pushary Mac app; with no phone connected, only to the Mac app if they have one. Tell the user any `warning`. Do not use `pushary_ask` for reminders.

### pushary_notify


Send a one-way push notification. Optionally include structured context for a rich detail page.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| title | string | Yes | Notification title (max 100 chars, aim for under 60) |
| body | string | Yes | Notification body (max 500 chars; the phone shows the first 180) |
| agent_name | string | No | Identifies this Hermes instance (e.g., "Hermes - daily-briefing") |
| context_type | "task_complete" / "error" / "info" | Yes for task updates | Marks the notification for task-update routing. |
| summary | string | No | Short summary of the result. |
| details / files_changed | string[] | No | Result details or changed paths. |
| error_message / next_steps | string | No | Error or suggested follow-up. |

**Example - cron task completed:**

```json
{
  "title": "Daily briefing ready",
  "body": "Compiled 12 news items and 3 calendar events",
  "agent_name": "Hermes - daily-briefing",
  "context_type": "task_complete",
  "summary": "Morning briefing compiled from RSS feeds and Google Calendar",
  "details": ["12 tech news items", "3 meetings today", "2 PRs awaiting review"],
  "next_steps": "Say 'read briefing' in Telegram to hear the full summary"
}
```

### pushary_ask

Ask a question via push notification and **wait for the answer** (blocks by default). Three question types: confirm (yes/no), select (multiple choice), input (free text).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| question | string | Yes | The complete question (max 8000 chars; notifications show a short preview) |
| type | "confirm" / "select" / "input" | No | Question type (default: confirm) |
| options | string[] | No | Choices for select type (2-6 options) |
| placeholder | string | No | Placeholder text for input type |
| context | string | No | What you're working on, shown above the question |
| agent_name | string | No | Identifies this Hermes instance |
| wait | boolean | No | Wait for answer before returning (default: true) |
| timeout_ms | integer | No | Max wait in ms (max 55000). Defaults to 30000 per poll attempt; server policy may hand off earlier. |

**Returns:**
- `{ "answered": true, "value": "yes" }` - user responded
- `{ "answered": false, "timedOut": true }` - no response within timeout

**Example - dangerous command approval:**

```json
{
  "question": "Allow: rm -rf /tmp/build-artifacts/*",
  "type": "confirm",
  "context": "Cleaning up 2.3GB of stale build artifacts from last week",
  "agent_name": "Hermes - server-maintenance",
  "timeout_ms": 12000
}
```

### pushary_wait

Poll once for a response when `pushary_ask` was called with `wait: false`. Not needed with default blocking mode.

| Name | Type | Required | Description |
|------|------|----------|-------------|
| correlation_id | string | Yes | The correlationId from pushary_ask |
| timeout_ms | integer | No | How long to wait (default 30000, max 55000) |

### pushary_cancel

Cancel a pending question that's no longer relevant.

| Name | Type | Required | Description |
|------|------|----------|-------------|
| correlation_id | string | Yes | The correlationId to cancel |

### pushary_propose_scope

Agree the boundary of a multi-step run in one tap, before doing the work, instead of asking file by file. Use it once when a boundary needs agreement or the user requests an enforced scope. Skip a redundant proposal for already authorized work.

| Name | Type | Required | Description |
|------|------|----------|-------------|
| done_when | string | Yes | What "finished" means for this run |
| allowed_paths | string[] | No | Globs you intend to change, e.g. `["src/**"]` |
| off_limits_paths | string[] | No | Globs you promise not to touch; these win on overlap |
| promises | string[] | No | Boundaries that are not file paths: recipients, channels, spend, systems you will not open |
| agent_name | string | No | Identifies this Hermes instance |

Only file paths are enforced, and only on tool calls that carry one. Shell commands, reads, web requests and MCP tools carry no path, so the contract says nothing about them. A run that changes no files belongs in `promises`, which is shown to the user and recorded but never checked. A word that is not a path in `allowed_paths` matches no file and makes every change ask instead.

Read `enforces` in the result. An empty list means nothing here is checked automatically, and you must say so rather than report that a scope is in force.

Returns `ratified: true` only on an explicit yes. Anything else means proceed as if no scope was agreed; do not describe it as ratified.

## Human-in-the-Loop Flow

`pushary_ask` performs its initial wait and at most one server-directed poll within that tool call. If the returned status is still pending, continue with `pushary_wait` and the same correlationId. With `wait: false`, start that polling yourself. Follow an explicit handoff instead when one is returned.

Read `answered`, `status` and `handoffAction` (falling back to `nextAction`) on every response. Only `pending` is live; expired, cancelled, missing and unavailable are not new timeouts. Keep waiting with the same correlationId while pending. A poll ending does not expire the question; never cancel just because a poll returned without an answer. Before moving a live question to the current chat, cancel it. If cancellation says `stop`, stop; if it loses a race, poll once for one second and honor the winning answer. Silence is never consent. A select or input value containing “yes” is answer data, not approval of a separate action.

Delivery is controlled by the user's policy: `push_first` (When away) still sends your questions to the phone and lets only hook approvals skip it while the user is at the computer, `push_only` requests push every time, `notify_only` leaves the decision in the current client, and `terminal_only` avoids push. Do not override the mode or duplicate a question on every surface. The runtime owns delivery, expiry and settlement; do not claim that a reply can restart an ended agent turn.

Each call returns an answer, a pending wait, or an explicit handoff:

```
result = pushary_ask({
  question: "Deploy the updated config to production?",
  type: "confirm",
  context: "nginx config updated with new rate limits",
  tool_name: "terminal",
  tool_target: "systemctl reload",
  agent_name: "Hermes - devops"
})

if result.answered:
    if result.value == "yes":
        // proceed with deployment
    else:
        // abort and notify via active platform
else:
    // follow handoffAction when present, otherwise nextAction
```

Pass `tool_name` and `tool_target` whenever the question is about a specific operation. They are what let the user turn a repeated approval into a standing rule, and what group the decision in their ledger.

## Identifying Your Instance

Always pass `agent_name` so the user knows which Hermes profile or task is asking.

**Format:** `"Hermes - {profile or task}"`

**Examples:**
- `"Hermes - daily-briefing"`
- `"Hermes - server-maintenance"`
- `"Hermes - code-review"`
- `"Hermes - personal-assistant"`

## Notification Etiquette

- **Titles under 60 characters.** Phone lock screens truncate aggressively.
- **Bodies under 180 characters,** where the phone cuts them. Use the flat `summary`, `details` and `next_steps` fields.
- **Max 3 push notifications per task.** If the user is in an active chat, prefer that channel.
- **Don't duplicate.** If you already sent the message via Telegram/Discord, send another push only if requested or needed for an unattended result.
