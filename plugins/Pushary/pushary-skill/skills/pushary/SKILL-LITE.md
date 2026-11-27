---
name: pushary
version: 0.7.1
description: Push notifications and human-in-the-loop for AI agents. Use this whenever a running agent needs a human and nobody is at the terminal, such as before an irreversible or destructive action, before spending money, deploying, force-pushing or deleting, when blocked on a decision outside your authority, when running unattended and you hit a genuine ambiguity, when another skill's workflow says to confirm with the user, and when a long task finishes or fails with nobody watching. Also use it when the user says ping me on my phone, notify me when my agent needs me, approve from my phone, or run this overnight. Ask questions, send alerts, get answers from connected devices.
metadata:
  tags: notifications, push, mcp, human-in-the-loop
---

# Pushary - Push Notifications for AI Agents

Honor authorization already granted in this session. Ask only for a missing decision or an action outside that authorization, or when an enforced host policy requires it. A multi-step task alone does not require plan approval. Never ask again merely because the next authorized step deletes, deploys or publishes something. These skills guide the agent; supported hooks and runtime approval gates enforce policy. Do not bypass an enforced gate.

Reach for them without being asked when: you are about to do something irreversible, spend money, or touch production; the decision is outside your authority; you are unattended and hit a real ambiguity; another skill's workflow says to confirm with the user; or a long task finished with nobody watching.

## schedule_reminder

For “remind me later,” call with `body` and `inMinutes`, or `at` as an ISO timestamp with explicit UTC offset. Never guess the timezone; confirm the returned time. Pushary delivers to the creator's phone after the agent exits, normally within about a minute of the due time. One-time only, within 30 days. No arguments lists pending reminders; `cancelReminderId` cancels a scheduled one. Do not use `ask_user` for reminders.

## ask_user

Ask a question via push and **wait for the answer** (blocks by default).

```json
{ "question": "Delete unused migrations?", "type": "confirm", "agentName": "Codex - myproject" }
```

Returns `{ "answered": true, "value": "yes" }` or `{ "answered": false, "timedOut": true }`.

Types: `confirm` (yes/no), `select` (2-6 options via `options` array; add `allowOther: true` unless the options cover every answer), `input` (free text).

## send_notification

One-way alert. Use when a task completes, errors, or needs attention.

Always pass `context.type`: `task_complete`, `error`, or `info`. It is what marks
the notification as a task update, and the user's setting for where task updates
land can only route one that says so.

```json
{ "title": "Build complete", "body": "All tests passing", "agentName": "Codex - myproject",
  "context": { "type": "task_complete", "summary": "17 tests, 0 failures" } }
```

## cancel_question

Cancel a pending question: `{ "correlationId": "..." }`

## propose_scope

Agree the boundary of a multi-step run up front, once: `{ "doneWhen": "tests pass", "sessionId": "...", "allowedPaths": ["src/**"], "offLimitsPaths": [".env*"] }`

Blocks until the user answers. `ratified: true` means it is live, and after that a file outside the scope becomes a "widen scope?" question instead of a silent approval, so the user is asked once per boundary rather than once per file.

Only file paths are enforced, and only on tool calls that carry one (`Edit`, `Write`, `MultiEdit`). Shell commands, reads, web requests and MCP tools carry no path, so the contract says nothing about them. A boundary that is not a path (recipients, channels, spend, systems) goes in `promises`, which is shown and recorded but never checked; never put one in `allowedPaths`, where it matches no file and makes every edit ask instead. Read `enforces` in the result: an empty array means nothing here is checked automatically, and you must say so rather than report that a scope is in force. Enforcement also needs the Pushary hook; without it the contract is recorded but not gated.

## list_sessions

Read-only: see your live agent sessions and pending questions (no notification sent). Useful to check if a parallel session is blocked.

## Rules

- `agentName` format: `"{Agent} - {project}"` (e.g., `"Cursor - api-server"`)
- Use `propose_scope` only for an unresolved or requested boundary, not redundant plan approval; a boundary that is not a file path goes in `promises`
- Max 3 notifications per task
- Ask for confirmation before risky actions outside existing authorization; preserve enforced host gates
- If `answered: false`, follow `handoffAction` when present, otherwise `nextAction`; keep waiting with the same correlationId while pending; cancel only for an explicit handoff or when the answer is no longer needed

Read `answered`, `status` and `handoffAction` (falling back to `nextAction`) on every response. Only `pending` is live; expired, cancelled, missing and unavailable are not new timeouts. Keep waiting with the same correlationId while pending. A poll ending does not expire the question; never cancel just because a poll returned without an answer. Before moving a live question to the current chat, cancel it. If cancellation says `stop`, stop; if it loses a race, poll once for one second and honor the winning answer. Silence is never consent. A select or input value containing “yes” is answer data, not approval of a separate action.

Delivery is controlled by the user's policy: `push_first` (When away) still sends your questions to the phone and lets only hook approvals skip it while the user is at the computer, `push_only` requests push every time, `notify_only` leaves the decision in the current client, and `terminal_only` avoids push. Do not override the mode or duplicate a question on every surface. The runtime owns delivery, expiry and settlement; do not claim that a reply can restart an ended agent turn.

Confirm notifications can offer lock-screen actions; arbitrary choices and text open the app. Partner customers answer on their enrolled phone, and in the Mac notch once they connect the Mac from the phone app. A completed turn cannot be restarted by a late phone reply. Notify only on meaningful unattended results or requested updates.
