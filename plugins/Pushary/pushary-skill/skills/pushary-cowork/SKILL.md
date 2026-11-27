---
name: pushary-cowork
version: 0.7.1
description: Use Pushary in Claude Chat, Cowork, or Claude Code when the user asks for phone updates, a missing decision blocks work, an action needs approval outside existing authorization, or meaningful unattended work finishes or fails. Send task updates and confirm, choice, or text questions to the user's connected devices, then read the returned answer and handoff. Requires the Pushary connector and a paid Pushary account. This skill does not install native permission hooks.
metadata:
  tags: notifications, push, mcp, human-in-the-loop, cowork, claude, alerts, approvals
---

# Pushary for Claude

Pushary is connected as a custom connector. It reaches the user on their phone, where confirm notifications can offer lock-screen actions; choices and text open the app. Use it proactively. Do not wait for the user to ask.

## Ask in as few interruptions as possible

Honor authorization already granted in this session. Ask only for a missing decision or an action outside that authorization, or when an enforced host policy requires it. A multi-step task alone does not require plan approval. Never ask again merely because the next authorized step deletes, deploys or publishes something. These skills guide the agent; supported hooks and runtime approval gates enforce policy. Do not bypass an enforced gate.

Every question costs the user their attention wherever they are. Before a run of more than a step or two, work out where you will need a human and fold those points together: one `select` carrying the real options beats three `confirm`s in a row, ask once at a boundary rather than once per instance, and never ask what you can determine yourself from the task or from a tool call you can make. If you would take your default without asking at all, and it is reversible, spends nothing and stays inside the task, do not ask: take it and list the decision in your final message so the user can change it. An irreversible step, spending money or a decision outside your authority still gets a question unless the user already approved it.

## When to reach out

For a personal reminder later, call `schedule_reminder` with `body` and `inMinutes`, or `at` with an explicit UTC offset. Never guess the timezone; confirm the returned time. Pushary saves the reminder and delivers after this conversation ends. It does not reopen Claude or perform future agent work. No arguments lists pending reminders; `cancelReminderId` cancels a scheduled one. Delivery can be about a minute late and requires a connected phone. Do not use `ask_user` for reminders.

- **You need a decision or a clarifying answer.** Call `ask_user` instead of guessing or stalling. Use type `confirm` for yes or no, `select` for a fixed set of options, and `input` for free text.
- **An action outside your existing authorization is risky or irreversible.** Deleting or overwriting files, spending money, sending anything external, bulk changes: call `ask_user` with type `confirm` first and wait for approval.
- **Meaningful work finishes while the user is away, or they requested an alert.** Call `send_notification` with a short summary of what changed, and pass `context.type` as `task_complete`. That is what marks it a task update, and the user's setting for where task updates land can only route one that says so. Ask before you stop only for a specific unresolved decision needed to finish, as described below.
- **You are blocked or hit an error you cannot resolve.** Call `send_notification` with `context.type` as `error` so the user knows, and `ask_user` if you need a decision to continue.
- **Another skill's workflow says to confirm with the user.** That instruction assumes someone is watching the session. Often nobody is. Route the confirmation through `ask_user` so the run continues when they answer, instead of stalling on a prompt they never see.

## Hand back with a way to reply

The connector carries only the updates and questions you send. Once your turn ends, this connector is no longer listening for answers. It cannot start a new Chat, Cowork, or Claude Code task, so a reply that says "now do X" reaches nobody unless you asked for it before you stopped.

When a specific unresolved decision is needed before you can finish, ask it before you stop:

1. Call `ask_user` with the decision, such as "Which of these two drafts should I publish?".
2. While it is pending, keep waiting with `wait_for_answer`, then follow its handoff. A question from this connector closes 10 minutes after it is sent; most answers arrive within a minute.
3. Act on the answer in this same session. If it closes unanswered, that is not approval: ask in the chat instead.

Do not create a question just to keep the turn alive or ask for optional feedback after every result. Once this turn ends, the user must send follow-up work in Claude.

## How to wait for answers

Read `answered`, `status` and `handoffAction` (falling back to `nextAction`) on every response. Only `pending` is live; expired, cancelled, missing and unavailable are not new timeouts. Keep waiting with the same correlationId while pending. A poll ending does not expire the question; never cancel just because a poll returned without an answer. Before moving a live question to the current chat, cancel it. If cancellation says `stop`, stop; if it loses a race, poll once for one second and honor the winning answer. Silence is never consent. A select or input value containing “yes” is answer data, not approval of a separate action.

Delivery is controlled by the user's policy: `push_first` (When away) still sends your questions to the phone and lets only hook approvals skip it while the user is at the computer, `push_only` requests push every time, `notify_only` leaves the decision in the current client, and `terminal_only` avoids push. Do not override the mode or duplicate a question on every surface. The runtime owns delivery, expiry and settlement; do not claim that a reply can restart an ended agent turn.

- If a poll ends while pending, keep waiting with the same question id. Cancel only when explicitly handing off or the answer is no longer needed. If cancellation returns `handoffAction: "stop"`, stop. Otherwise, if cancellation returns false, poll once for 1 second and honor the answer that won the race.
- Ask with `ask_user`, not with `send_notification` and `context.askQuestion`. Do not promise an overnight wait or a reply after the turn ends.
- Use `cancel_question` to retract a question that is no longer needed.

## Answer surfaces and account boundaries

| Surface | What the user can do |
| --- | --- |
| Mobile app | Answer confirm, select and input questions. Supported confirm notifications offer approve/deny actions on the lock screen; arbitrary choices and text open the app. |
| Mac notch | Answer confirm, select, input and question-set questions, including keyboard controls. Presence and delivery policy determine when the phone is also reached. |
| Slack | Answer through buttons, menus or text modals when the integration and intended recipient are configured. |
| Browser | Open the decision page as a fallback; browser notification delivery requires permission. |

Personal setup connects the operator's devices. The operator installs the Pushary phone or Mac app from https://pushary.com/download and signs in with the same account as the connector. In Chat or Cowork, connect Pushary from the plugin's Connectors tab or add `https://pushary.com/api/mcp/mcp` under Customize > Connectors. In Claude Code, check the connector with `/mcp` and follow its OAuth sign-in prompt. No CLI installer or API key is needed. Ask one harmless test question in the app being tested, answer it from Pushary, and verify Claude receives the answer. CLI doctor checks do not verify a hosted connector. Test phone fallback while away from the Mac; do not infer delivery from a successful API call alone.

Partner customers use scoped enrollment links issued by their application. Do not enroll them into the operator's account or send their decisions through personal tools. They answer on their enrolled phone, and in the Mac notch once they connect the Mac from the phone app. See https://pushary.com/docs/agents/embed for Partner setup.

## Conventions

- Reuse one opaque `sessionId` per conversation or task. Do not reuse it across parallel tasks or put credentials in it.
- Pass `agentName` as `Claude Chat - <task name>`, `Claude Cowork - <task name>`, or `Claude Code - <task name>` to match the current app. Use it on every call so the user knows which session is asking.
- Keep questions short and decision-shaped. One sentence of context, then the ask. The user is reading a lock screen, not a report.
- Send only the context needed for the decision or task update. Leave passwords, API keys, file contents, and private conversation history out of Pushary tool arguments.
- Do not ask through Pushary for things you can safely decide yourself. Reserve it for real decisions, risky steps, completions, and errors, so a ping always means something.

## Setup and capability boundary

Install Pushary for Claude to supply this skill and its remote MCP connector, or connect the public URL above. Sign in with the same Pushary account used by your phone and Mac. Enable the connector in the conversation and approve its tool access when Claude asks. Use this skill for proactive behavior. Cowork also supports standing instructions under Settings > Cowork; Chat and Cowork do not rely on a repository memory file.

This plugin uses the cooperative connector and installs no native permission hooks. Chat ignores hooks. Cowork and Claude Code can load hooks from other integrations, but that does not mean this bundle can enforce approvals. Native Claude permission prompts still need Claude's own approval surface unless a separately installed integration handles them.

## If the connector is missing

If no Pushary tools are available in this session, the connector is not enabled. Tell the user once: Pushary is not connected in this session. Enable it under Customize, Connectors, or set it up at https://pushary.com/docs/agents/guides/claude-desktop. Then continue the task without it.
