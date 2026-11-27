---
name: pushary-chatgpt
version: 0.3.2
description: Reach the user on their phone through Pushary while ChatGPT or Codex works on a task. Use it to get a plan approved before starting, to ask before a step the user has not approved, and to send one summary when the work is done or fails. Use for requests such as get my approval on my phone first, ask me on my phone before anything you can't undo, I'm stepping away, ping me when it's done, send me a summary, or remind me later. Honor approvals the user already gave and follow the server's delivery policy.
metadata:
  tags: planning, approvals, human-in-the-loop, notifications, push, chatgpt, codex
---

# Pushary for ChatGPT and Codex

Pushary connects this chat to the user's phone. You send a question or an update, the user gets a push, and their answer comes back to you. Yes or no questions can be answered from the lock screen where the phone supports it; choices and typed answers open the Pushary app. Every question and answer is recorded in Pushary.

You decide when to call Pushary. It does not watch or block your actions, so the rules below are yours to follow.

## Tools

| Tool | Use it to |
| --- | --- |
| `ask_user` | Ask one question and get the answer: `confirm` for yes or no, `select` for two to six options, `input` for a fact only the user knows. |
| `wait_for_answer` | Keep waiting for a question that is still pending, with its `correlationId`. |
| `cancel_question` | Withdraw a question that is no longer needed. |
| `send_notification` | Tell the user something: a finished task, a failure, or an update they asked for. |
| `schedule_reminder` | Set a one-time personal reminder, when the user asks to be reminded later. |
| `propose_scope` | Record the boundary of a run so the user can agree to it. |

Pass `agentName` on every call as the host and the task, for example `ChatGPT - Q3 board deck` or `Codex - invoice audit`. Pass the same `sessionId` for the whole conversation. Do not call yourself another host.

## What the user asks for, and what to do

| The user says | Do this |
| --- | --- |
| "Plan this first, then get my approval on my phone." | Write the plan. Send it as one `confirm` question with the steps in `question`. Start only after a yes. On a no, ask what to change. |
| "Ask me on my phone before anything you can't undo." "I'm stepping away." | Work. Before each step in the list below, ask with `ask_user`. Keep going with work that does not depend on the answer. |
| "Ask me at every decision." | Ask each real choice as one `select` question with your recommended option first. |
| "Ping me when it's done." "Send me a summary." | When the work ends, send one `send_notification` with `context.type` set to `task_complete` and the result in `summary`. |
| "Tell me if something breaks." | On a failure you cannot fix, send `send_notification` with `context.type` set to `error`. |
| "Remind me in 30 minutes." | Call `schedule_reminder`. Tell the user the time it returns. |
| "Send a test question." | Send one harmless `confirm` question and report what the user answered. |

The user does not have to say "Pushary". "Ask me on my phone", "get my approval" and "ping me" mean these tools.

## Before the task: get the plan approved when asked

Ask for plan approval only when the user asked for it, or when the plan goes beyond what they asked you to do. A task with many steps does not need a plan approval by itself. Start `question` with a short line the lock screen can show, such as "Approve the plan for the Q3 board deck?", then list the steps after it. `question` holds up to 8,000 characters; `context` holds only 500, so use `context` for one line of background, never for the plan.

## During the task: ask before a step the user has not approved

Ask with `ask_user` before any of these, unless the user already approved it in this conversation:

- **Something that cannot be undone.** Deleting, overwriting or replacing something the user made.
- **Something that leaves this chat.** Sending an email or message, posting, publishing, or sharing with someone else.
- **Money.** A purchase, a booking, a paid plan, or anything billable.
- **A decision that belongs to the user.** A product, naming, pricing or wording choice they would want to make themselves.
- **A real fork when the user is away.** Two good readings of the task, where the wrong one wastes the work.

How to ask well:

- **Ask in the chat when the user is here.** If the user is in this conversation and has not asked to be reached on their phone, ask in the chat. Use Pushary when they asked for it, said they are stepping away, or the work runs on without them. Their delivery setting decides the rest; do not force a phone prompt.
- **Find the decisions first.** Settle what you can from the conversation or a tool. Ask only what is left.
- **One question per stop.** Put related choices in one `select` question with your recommendation first, rather than several yes or no questions.
- **Be exact.** "Send the renewal email to the 14 customers on the list?" beats "Should I continue?"
- **Ask once, on one channel.** Do not repeat a question in chat while it is live on the phone.
- **Do not ask again for what the user already approved** in this conversation. Do not turn your step list into a question.

## After the task: send one summary

When the work ends, send one `send_notification`:

```json
{
  "title": "Board deck ready",
  "body": "12 slides drafted. Two numbers need your check.",
  "agentName": "ChatGPT - Q3 board deck",
  "context": {
    "type": "task_complete",
    "summary": "Drafted 12 slides from the Q3 numbers you shared.",
    "nextSteps": "Check the churn and CAC figures on slides 7 and 9."
  }
}
```

Keep `title` under 60 characters and `body` under 180; the phone cuts the body there. Use `context.type` `task_complete`, `error` or `info`. Send at most three notifications for one task unless the user asked for more. Skip a notification for a trivial task or when the user is reading the chat. Do not add a question just to keep the turn open.

When you would take your own recommendation without asking at all, and the step is reversible, spends nothing and stays inside what the user asked for, do not ask. Make the choice and list it in your summary so the user can change it. An irreversible step, spending money or a decision outside your authority still gets a question unless the user already approved it. Ask with `ask_user`, not with `context.askQuestion`. When the work the user asked for is done, report it and stop; do not ask what to do next unless they asked you to.

## Waiting for an answer

Read `answered`, `status` and `handoffAction` (falling back to `nextAction`) on every response. `ask_user` waits up to 48 seconds, or returns at once, depending on the user's delivery policy. When a call returns with the question still `pending`, keep waiting with `wait_for_answer` and the same `correlationId`. A poll ending does not end the question; never cancel just because a poll returned without an answer.

When you are connected by signing in to Pushary, as in ChatGPT, a question stays open for 10 minutes. Only `pending` is live. `expired`, `cancelled`, `missing` and `unavailable` are not new timeouts. An expired question was not answered: do not take the step it asked about, and follow `nextAction`, which asks you to put the question to the user in this chat instead. Silence is never consent. A `select` or `input` answer containing "yes" is the answer's data, not approval of some other action.

If your reply has to end while a question is still pending, say so plainly: the question is on their phone, and when they have answered they can tell you here to continue. On the next turn, call `wait_for_answer` with that `correlationId` before anything else. Never claim that an answer on the phone restarts a reply that has already ended.

If the user answers in chat instead, and the question is still live on the phone, call `cancel_question` before acting. If cancellation returns `handoffAction: "stop"`, stop. If it returns `cancelled: false`, call `wait_for_answer` once for one second and honor whichever answer won.

Delivery is the user's setting, not yours: `push_first` (When away) still sends your questions to the phone and lets only hook approvals skip it while the user is at the computer, `push_only` sends a push every time, `notify_only` leaves the decision in the current client, and `terminal_only` sends no push. Do not override the mode or send the same question on every surface. Show `answerUrl` when it is present and useful; it is not on every response.

## When Pushary cannot reach the user

- **Pushary refuses the connection because the account has no site yet.** Pass that message to the user exactly as it is, with its link. Wait until they say setup is finished. Do not call Pushary again before then. When they do, send one harmless test question first, then carry on with what they asked. If it reaches no device or stays pending, tell them to install the Pushary phone app and sign in with the same account; a pending question waits there.
- **Pushary refuses because the account is a viewer.** Pass the message as it is. A workspace owner or admin has to change the role.
- **The result has `noDevices: true`, or says no phone received it.** Tell the user to install the Pushary phone app from https://pushary.com/download and sign in with the same Pushary account this chat is connected to. Follow `handoffAction`, or `nextAction` when there is none. Undelivered is not permission to take the step.
- **Pushary says the account is not active.** Tell the user Pushary cannot reach their phone until their Pushary account is active again, and stop calling it in this conversation.
- **Pushary says to answer or cancel an existing question first.** Wait for the open question, or cancel it if it is no longer needed, before asking another.

Never ask the user for payment details, do not mention prices or plans, and do not pass on an upgrade link.

## A boundary for the run

Use `propose_scope` when the user asks for an agreed boundary, or one is still open. Pass `doneWhen` and `sessionId`. In ChatGPT, which changes no files on the user's computer, put the whole boundary in `promises`: who you will contact, what you will publish, what you will not spend. Only `ratified: true` means the user agreed; a yes in chat is not a ratified scope. Read `enforces` in the result. An empty list means nothing is checked automatically, and you must say so rather than call the boundary enforced. In Codex, `allowedPaths` and `offLimitsPaths` are enforced only on file edits and only with the Pushary hook installed; shell commands stay under the host's own approval rules.

## Answer surfaces and account boundaries

| Surface | What the user can do |
| --- | --- |
| Mobile app | Answer confirm, select and input questions. Supported confirm notifications offer approve and deny actions on the lock screen; choices and text open the app. |
| Mac notch | Answer confirm, select, input and question-set questions. Presence and delivery policy decide when the phone is also reached. |
| Slack | Answer through buttons, menus or text forms when the integration and the right recipient are set up. |
| Browser | Open the decision page as a fallback. Browser notifications need permission. |

Partner customers use scoped enrollment links issued by their application. Do not enroll them into the operator's account or send their decisions through personal tools. They answer on their enrolled phone, and in the Mac notch once they connect the Mac from the phone app. Partner setup: https://pushary.com/docs/agents/embed.
