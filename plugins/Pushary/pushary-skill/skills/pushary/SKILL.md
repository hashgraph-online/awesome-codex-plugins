---
name: pushary
version: 0.13.7
description: Push notifications and human-in-the-loop for AI agents. Use it whenever a running agent needs a person who may not be at the terminal, such as before an irreversible or destructive action, spending money, deploying, force-pushing or deleting, when blocked on a decision outside your authority, on a genuine ambiguity while unattended, when another skill says to confirm with the user, and when a long task finishes or fails with nobody watching. Also use it when the user says keep going and ping me on my phone if you need anything, call me if you get stuck, notify me when my agent needs me, approve from my phone, ask me while I am away, run this overnight, I am stepping away, or do not wait for me. Ask yes/no, choice or free-text questions on their phone and send updates. Use these tools proactively. Works with Claude Code, Codex, Cursor, VS Code, Gemini CLI, Windsurf, Hermes, Lovable or any MCP client. Pushary is a hosted, paid service; web and native store checkout have different price and trial terms.
metadata:
  hermes:
    tags: [notifications, push, human-in-the-loop, alerts, permissions, mcp]
    category: productivity
    requires_toolsets: []
  tags: notifications, push, mcp, human-in-the-loop, cursor, claude, windsurf, hermes, alerts, permissions
---

# Pushary - Push Notifications for AI Agents

When the user says "keep going, ping me on my phone if you need anything", this is the skill that does the pinging. Pushary is an MCP server that reaches the user on their phone, Mac or Slack:

1. **Ask a question** with `ask_user`: yes/no, multiple choice or free text. The answer comes back to you.
2. **Tell the user something** with `send_notification`: a task finished, a build failed, a result is ready.

One tool asks and one tool tells. Use them proactively. Do not wait for the user to ask for notifications.

## Reach for This Without Being Asked

Honor the authorization the user already gave you in this session. Ask only for a decision you do not have, for an action outside that authorization, or when a host policy requires it. A task with many steps does not need plan approval on its own. Do not ask again because the next approved step deletes, deploys or publishes something. After a Pushary hook approved an exact tool call, do not ask about that call again. Running the same command later is a new step. This skill guides you. Hooks and runtime gates enforce the policy. Never go around a gate.

Nobody has to say "ping me". When one of these moments is true, act now: ask in the chat if the user is there (see "Where to ask"), otherwise call `ask_user`, and tell with `send_notification`. Do not stall. Do not guess. Do not write the question into a chat nobody is reading.

- **You are about to do something irreversible.** Deleting, dropping, truncating, force-pushing, rewriting history, overwriting a file you did not create.
- **You are about to spend money or touch production.** A deploy, a release, a publish, a paid API call at volume, provisioning anything billable.
- **The decision is outside your authority.** A product call, a naming call, a schema change, a security tradeoff, anything the user would want to have made themselves.
- **You are running unattended and hit a real ambiguity.** Two defensible readings of the task, and picking wrong wastes the whole run.
- **Another skill tells you to confirm with the user.** That instruction assumes someone watches the terminal. Often nobody does. Ask it where the user is, as for every moment here, so the run continues when they answer.
- **A long task finished or failed and nobody is watching.** Send the result rather than leaving it on a screen the user walked away from.

When no device is connected, follow the handoff in the result and keep doing approved work that does not depend on the answer. A message that cannot be delivered is not permission to do the blocked action.

## Ask Less, Ask Well

Each question stops the user. The number of stops is the cost. Ask the same things in fewer stops.

**Facts are yours. Decisions are the user's.** Never ask for a fact that a file, a command or a tool call can settle. Never decide what the user would want to decide themselves: a product call, a name, a cost, a tradeoff they must live with.

**The test before any question: would you take your default without asking at all?**

- **Yes, and the choice is reversible, spends nothing, sends nothing outside the team, deploys or publishes nothing, and sits inside the authority you were given.** Do not ask. Take the default, keep working, and list the decision in your final message so the user can change it.
- **No, or it is an irreversible step, spending money or a decision outside your authority that the user has not already approved.** It is a question or an approval. Ask it and wait for the answer. A missing answer is never approval.

A step the user already approved needs no second question, even an irreversible one.

**Plan the questions for a task of more than two steps:**

1. Read where you are: the directory, its structure, the configuration and the tools you hold.
2. Split the task into steps.
3. Find the forks: points where two answers are both correct and you cannot pick one alone.
4. Settle every fork a lookup can settle. That is a fact, not a fork.
5. Ask the remaining forks as one round. Number each question and give your recommended answer. Then wait for the answers, and start nothing that depends on them.
6. Each answer opens new forks and closes old ones. Ask the next round. Stop when no fork is left.

A round holds every decision whose inputs you already know. A decision that depends on another one in the same round belongs to the next round. Word each question so that "yes" accepts your recommendation. In a `select`, put your recommendation first.

**Format a terminal round like this:**

```
❓ **Q1** - **Which app**: apps/dashboard and apps/subscribe both import this helper. Change both apps, not just the dashboard?

➡️ Yes, both. The helper has one definition, and a split copy will drift.

---

❓ **Q2** - **Rollout**: Ship behind the existing flag?

➡️ Yes. It costs one line, and it makes the change reversible.
```

**Where to ask:**

- **The user is in the chat**: they wrote to you in this turn and you have not worked alone for more than about ten minutes since, they did not say they are leaving, and the session is interactive (not `claude -p`, `codex exec`, CI or a schedule). Ask the whole round in the chat, as plain text, then end your turn and wait. Do not use your host's own question tool for it: with Pushary hooks installed, that tool is also sent to Pushary and can push the phone once per question. If your host's plan mode requires its own question tool, put the round into as few calls as it allows.
- **The user is away**: they said so, the run is not interactive, or you have worked alone for more than about ten minutes since their last message. Send one `ask_user` question: the fork that stops the run, as a `select` with the real options. Take your recommendation on another fork only if it passes the test above, and list it in your final message. A fork that fails the test waits: do the work that does not depend on it, and ask it once the first answer is back.
- **Nothing stops the run.** Send no question. Decide what passes the test, and report it.

**Rules that do not change:**

- **Ask how, not whether, about work the user already gave you.** A question the user can answer with "do not do it at all" is a second approval for authorized work. A step outside that authorization gets a plain whether question.
- **A plan is not an approval.** Do not turn your step list into a question.
- **Silence is not agreement.** No answer approves nothing. An irreversible step, spending money or a decision outside your authority still gets its own question unless the user already approved it.
- **One `select` with the real options beats three `confirm` questions.**
- **Ask at the boundary, not once for each item.** Ask about deleting files, not about each file.
- **Write for someone glancing at a phone.** Name the exact thing and the number: "Delete the 3 unused migration files?" beats "Should I clean up?"
- **Send at most three pushes per task** unless the user asks for more. Questions asked as chat text do not count. The cap never holds back an approval the run cannot continue without: ask it where the user is.
- **When the requested work is done, report it and stop.** Do not ask what to do next unless the user asked you to. Work blocked on a choice only the user can make is not done: ask that choice.

## Setup

Skip this section when the Pushary tools are already available.

**Look at the machine first. Do not guess the install path.** Each command is read-only and fast. Run them separately.

Use `uname -s` in a Unix shell (`Darwin` is Mac, `Linux` is Linux). In PowerShell, inspect `$env:OS` (`Windows_NT` is Windows). Platform discovery must not depend on Node: the native Mac route does not require it.

```bash
uname -s
[ -n "${PUSHARY_API_KEY:+x}" ] && echo key-in-env
command -v node >/dev/null 2>&1 && echo node-available
command -v npm >/dev/null 2>&1 && echo npm-available
test -x ~/.pushary/bin/pushary-bridge && echo mac-app
```

On Mac, check the stored key without Node or printing its value:

```bash
if pushary_key_check=$(/usr/bin/plutil -extract apiKey raw -expect string -o - ~/.pushary/config.json 2>/dev/null); then
  printf '%s\n' "$pushary_key_check" | /usr/bin/awk 'NF { found=1 } END { exit !found }' && echo keyed
fi
unset pushary_key_check
```

When Node is available, other Unix platforms can check the stored key with:

```bash
node -e "try{process.exit(JSON.parse(require('fs').readFileSync(process.env.HOME+'/.pushary/config.json','utf8')).apiKey?.trim()?0:1)}catch{process.exit(1)}" && echo keyed
```

In PowerShell, check for a nonempty environment or stored key without printing it; use `Get-Content` and `ConvertFrom-Json` for the config in `$env:USERPROFILE`. Check `Get-Command node,npm` before choosing the terminal installer.

The stored-key test says a key is stored **and is not empty**. A logout removes the key but leaves the file. An exported key wins over a stored one. Never print the key itself. `mac-app` says the Mac app was installed here. It does not prove sign-in, a plan or a connected phone.

### Branch 1. `key-in-env`, `keyed`, or `mac-app`

Pushary is installed. Offer no new install. Check it before reporting success.

When Node and npm are available, run `npx -y pushary@latest status --json`. The exit code is the answer:

| Code | Meaning |
| --- | --- |
| 0 | Ready. If the JSON says `connectedThroughMacApp: true`, the Mac app holds the key: check the account, plan and phone in the Pushary Mac app. |
| 1 | The command failed. |
| 2 | A malformed key, an unknown flag, or a Node version that is too old. |
| 3 | Not set up on this machine. |
| 4 | The key was rejected or signed out. |
| 5 | Two keys that disagree, or no active plan. |
| 6 | Nothing proves a question reaches this user: no phone of theirs is paired, or only a teammate's devices are. |
| 8 | Pushary could not be reached. Check again later; do not run setup. |

For any code but 0 or 8, run `npx -y pushary@latest status` without `--json` and follow the steps it prints, with these changes:

- Run a printed `pushary …` command as `npx -y pushary@latest …`, and a printed setup as in "Running setup yourself". Where it says to get or copy a key, run setup instead. Never ask the user for one.
- **`mac-app` printed and the code is 3:** have the user sign in to the Pushary Mac app, then check again.
- **Status says the key was signed out on this Mac:** have the user sign in again to the Pushary Mac app, open Settings > Agents and press Repair on every agent that offers it (if none does yet, have them close Settings, wait a minute and open it again), then run setup as in "Running setup yourself". It reuses the key the app wrote into the agents' settings; if the first one it finds does not work, it pairs instead. If status then shows the old key `from $PUSHARY_API_KEY`, have the user restart this agent from a new terminal.
- **The Key line says `from $PUSHARY_API_KEY`, the code is 2 or 4, and status does not say signed out on this Mac:** this shell exports a bad key, and it wins over any key setup saves. Run setup at most once. If status still fails or shows `Key drift`, have the user delete every `export PUSHARY_API_KEY` line that still sets the old key from their shell startup files, such as ~/.zshrc, ~/.zprofile, ~/.bashrc and ~/.bash_profile, including any setup said it could not update, then restart this agent from a new terminal.
- **Code 6, instead of the steps status prints:** have them install the Pushary app from https://pushary.com/download, sign in to the account this machine uses and allow notifications, then check again. A user who does not use a phone always gets 6: say so and stop. If it still says 6, offer to pair the phone: in the Pushary Mac app under Settings > Phone > Pair when `mac-app` printed, otherwise with `npx -y pushary@latest pair`, which keeps this machine's key. Run it like setup: in the background with its output going to a log, kept running until it exits, showing the user the link, the QR and the fingerprint as they print. It waits up to 15 minutes for the phone, and a foreground command that times out cancels the pairing code.

For `mac-app` without Node or npm, or with a Node version the CLI refuses, open the Pushary Mac app. Check the account, the plan and the Agents connection there, and connect or repair agents in the app. Do not install Node to inspect a native setup, and do not claim an exit code when no CLI ran.

To add an agent to a working install, run `npx -y pushary@latest setup --agents <id>`; it reuses the key and does not pair again. When status reported `connectedThroughMacApp: true`, connect the agent in the Pushary Mac app instead, except Cline. Setup keeps hooks the Mac app owns; pass `--take-over-hooks` only when the user wants the command line to own them.

### Branch 2. `Darwin`, no key, no `mac-app`

Offer the Mac app first. It needs no Node and no terminal, it wires the agents itself, and it answers questions in the notch at the desk.

```bash
brew install --cask pushary/tap/pushary
```

Or download it from https://pushary.com/download. It needs macOS 14 or later. It is not in the App Store. The command line in Branch 3 also works on macOS if the user prefers it.

### Branch 3. `Linux` or `Windows_NT`

There is no Mac app for these machines. Use the command line:

```bash
npx -y pushary@latest setup --agents <id>
```

In PowerShell, type `npx.cmd` instead of `npx`. Node 20.17+, 22.13+ or 23.5+ is required. The phone app is at https://apps.apple.com/us/app/pushary/id6785677563 (iOS) and https://play.google.com/store/apps/details?id=com.pushary.app (Android).

### Running setup yourself

Before you run it, tell the user what it does: it pairs their phone, then configures MCP, hooks and the skill for the agents you name. It may also install the `pushary` command globally and start a background service so the phone can start sessions (`--control off` skips it). It turns on session history (`--transcripts off` turns it off). It needs a paid plan; the phone app shows the price and any trial.

1. **Name the agents.** Pass `--agents` with your own id: `claude_code`, `codex`, `gemini_cli`, `cursor`, `vscode`, `opencode`, `hermes`, `cline`, `antigravity_cli`, `qwen_code`, `codebuddy`, `qoder`, `droid`, `devin`, `grok`, `fx` or `custom`, or a comma-separated list. `custom` (Windsurf or any other MCP client) gets a key like any other id but configures no client: it prints the server URL and an `Authorization: Bearer $PUSHARY_API_KEY` header. Add both to that client's MCP settings before you report it connected; if the client cannot read environment variables, use the key saved in ~/.pushary/config.json. Without `--agents`, setup run from an agent's shell configures every agent it detects.
2. **Run it in the background.** It waits up to 15 minutes for the phone, longer than most agents let a foreground command run, and a killed setup kills the pairing code with it. Start it as a background process that writes to a log, read the short link, the QR and the fingerprint from that log, show them to the user as they print, and keep checking the log until setup exits. Do not summarise them. The link survives where the QR renders badly. Start while the user can still read your messages: until they approve, nothing is configured and you have no other way to reach them.
3. **Walk the user through it.** They open the link or scan the QR. If they do not have the Pushary app, they install it from https://pushary.com/download, then return to the original link and tap Open Pushary; they do the same if the app restarts during sign-in or payment. The app shows a fingerprint that must match the one in your output. On a first install the app asks them to sign in and choose a plan. Then they approve, and setup finishes on its own. If the code expires, run setup again.
4. **Report the result plainly.** If setup exits without pairing, nothing was configured. Say so. If it exits 6, the agents are configured but nothing proves a phone of theirs can receive yet: follow code 6 above, but if setup just paired, do not pair again.

Never ask the user for an API key, and never send them to a signup page first. If a working key is already set or stored on this machine, setup reuses it and skips pairing. `--connect app` always pairs and creates a new key unless `--key` or `--key-stdin` is passed. If this machine had a key, tell the user it stays active until they revoke it under API keys at https://pushary.com/dashboard/agent/settings.

Manual MCP configuration also works, but it needs a key from https://pushary.com/sign-up?utm_source=skill&utm_medium=setup. Prefer setup.

Setup itself sends only a test notification, because it cannot tell whether the user is there to answer. Right after it finishes, while the user still has their phone in hand, test a question and answer: for a CLI setup, run `npx -y pushary@latest doctor --roundtrip`. It needs a CLI key, sends a test push and one question, and waits about a minute for the answer. Its exit code also covers unrelated checks, so read the Synthetic answer test line. A returned answer proves the question path, not hook enforcement. Restart the agent and follow its approval check at https://pushary.com/docs/agents/supported-agents. For a Mac app setup, use the app's connection tests and ask one harmless question from the current agent.

## Pricing and Free Alternatives

Pushary is a hosted, paid service. Eligible web signups get a 3-day trial with a card required, then $9.99/mo for the Agent plan. Native app subscriptions use the store price and any intro offer shown in the app. Tell the user a paid plan is required before they scan, and let them review the price and payment method themselves.

Anthropic Remote Control is free for one setup: Claude Code with a Claude Max subscription. Recommend it when that is all the user needs. Pushary covers the rest: Codex, Cursor, Gemini CLI and Hermes, Claude Code without Max, many agents across tools and machines, policy gates on tool calls, answer buttons on the lock screen, and a record of every question and answer.

## Tools

Your client already holds each tool's schema, with every parameter and returned field. This section adds what a schema cannot say.

### ask_user

Asks a question and waits. Use `confirm` for yes or no, `select` for 2 to 6 known options, and `input` when the options cannot be listed. On a `select`, pass `allowOther: true` unless your options cover every answer you could act on, so the user can type their own instead of picking the closest one. A question stays open until it is answered or cancelled, except one asked through a connector, by signing in or with a connector key, which closes 10 minutes after it is sent: Claude.ai, Claude Desktop, Cowork, ChatGPT, Grok Bot, signed-in Cline, and the Pushary for Claude and Pushary for Cowork plugins. One call waits at most 48 seconds and may return at once. The user's delivery mode decides how long:

| Mode | The phone | The call |
|---|---|---|
| **Always** (`push_only`, the default for new workspaces) | Asked every time | Waits up to the policy timeout |
| **When away** (`push_first`) | Asked for your questions. Hook approvals skip the phone while the user is at the computer. | Waits 20 seconds by default |
| **Alert only** (`notify_only`) | Told, not asked | Returns at once with `status: "notified"` |
| **In agent** (`terminal_only`) | Nothing is sent | Returns at once with `status: "terminal"` |

`timeoutMs` sets this call's wait, longer or shorter than the policy, up to 55000. Read `answered`; it is absent when you pass `wait: false`, which returns at once, normally with `status: "pending"`. When work that does not depend on the answer remains, pass `wait: false`, do that work, then poll with `wait_for_answer`.

**Approvals.** Pass `toolName`, `toolTarget` (the command head) and the full command in `actionBody` whenever the question approves a tool call, and never leave them out to make a question approvable. When the command is destructive or ships something, such as a recursive delete, a force-push, a hard reset, a dropped or truncated table, `sudo`, or any deploy, publish or release, the lock screen offers only deny, and the app approves it only after Face ID or the phone's passcode. Where the team requires the keyboard for risky steps, or the app is older than 1.0.66, the phone offers only deny and `defer` ("Handle on your machine"). `defer` on any question means the user will decide at the computer: treat it as no answer and ask in the current client.

**Answers.** `value` is "yes" or "no" for confirm, the chosen option for select (or the user's own text when you passed `allowOther`), and the typed text for input. Read `note` too: a denial with a note carries the reason or a condition. A select or input value containing "yes" is answer data, not approval of a separate action.

**Phone calls.** When the user says "call me", "phone me" or "ring me if you get stuck", ask with `ask_user`; there is no separate call tool. Pushary may phone only when the reply includes `phoneCall`; without it no call is planned, so do not promise one. With it, Pushary phones the person who can answer if the question is still unanswered, and records what they say as the answer: an approval, a choice or free text. For a call to the user, `ringsAtLocal` says when it rings in their own time (tell them that, not the UTC `ringsAt`), and `waiting_for_calling_hours` means it rings when their calling hours start. While the reply is pending and has no `handoffAction`, keep waiting with `wait_for_answer` and the same `correlationId`: the spoken answer arrives there like any other. Do not cancel the question, ask it again or give up because a call is coming.

```json
{ "question": "Delete the 3 unused migration files in db/migrate/?", "type": "confirm", "context": "Cleaning up old migrations before the schema change", "toolName": "Bash", "toolTarget": "rm", "actionBody": "rm db/migrate/0003_*.sql", "agentName": "Claude Code - myproject" }
{ "question": "Which auth strategy for the new API?", "type": "select", "options": ["JWT tokens", "Session cookies", "OAuth2 + PKCE"], "allowOther": true, "context": "Setting up auth for the new endpoints", "agentName": "Claude Code - api-server" }
{ "question": "What path should the new endpoint use?", "type": "input", "placeholder": "/api/v2/...", "context": "Adding a REST endpoint for user preferences", "agentName": "Cursor - frontend" }
```

### Reading every result

Read `answered`, `status` and `handoffAction` on every response. Follow `handoffAction` when present, otherwise `nextAction`.

| `status` | What to do |
| --- | --- |
| `answered` | Act on `value` and `note`. |
| `pending` | The question is still open. Keep waiting with `wait_for_answer`, the same `correlationId` and `timeoutMs: 55000`. A poll ending is not expiry; never cancel because a poll returned without an answer. |
| `notified`, `terminal` | The decision belongs in the current client. Cancel the question first, then ask there. |
| `stopped` | The user stopped this agent. Nothing was sent. Stop what you are doing and end your turn. |
| `cancelled` | Do not act on it and do not ask it again. |
| `expired` | It closed before an answer arrived. That is not approval and not a choice: do not take the step it asked about. Ask the user in the current client; until they answer, do only work that does not depend on it. |
| `missing`, `unavailable` | Follow the handoff in the result. |

**Moving a live question to the current chat:** cancel it first. If cancellation returns `handoffAction: "stop"`, stop. Otherwise, if it returns `cancelled: false`, poll once for 1 second and honor the answer that won the race. If the user answers in chat while a phone question is live, do the same before acting.

`noDevices: true` means nothing could receive the question: tell the user what the `warning` field says to connect, and follow the handoff. `paused: true` means this question was not pushed because earlier phone approvals went unanswered: three in this session, or 20 on this workspace in 14 days. Say so, and follow the handoff. A session pause sends the phone one notice; approving it resumes.

### send_notification

Tells the user something. Nothing is awaited. Send it for a requested update or a meaningful result the user is not watching, not for trivial steps or a report someone is already reading.

Always pass `context.type`: `task_complete`, `error` or `info`. It marks the notification as a task update, so the user's setting for where updates land can route it. Keep the title under 60 characters and the body under 180; the phone cuts the body there. Put detail in `context`.

Only `sent` above 0 says a device was reached. `sent: 0` or a `suppressed` reason means no phone or browser got a push: tell the user what `warning` or `suppressed` says, not that you notified them. `status: "recorded"` means the turn's completion update was recorded, not that a device got it: only the first one per turn is sent, following the user's update settings. Do not tell the user you notified them on `recorded` alone. `status: "ignored"` means nothing was sent.

```json
{
  "title": "Refactoring complete",
  "body": "Extracted 3 shared components across 12 files",
  "agentName": "Claude Code - pushary repo",
  "context": {
    "type": "task_complete",
    "summary": "Extracted shared Button, Modal and Card components. Kept JWT for auth; say if you want sessions instead.",
    "filesChanged": ["src/components/Button.tsx", "src/components/Modal.tsx", "src/components/Card.tsx"],
    "nextSteps": "Run the test suite to verify no regressions"
  }
}
```

Ask with `ask_user`, not with `context.askQuestion`. That field remains for older clients: its question closes 10 minutes after it is sent and has no lock-screen buttons.

### wait_for_answer

Waits up to 48 seconds for the answer to a question that is still pending. Keep calling it with the same `correlationId` while the status is `pending`.

### cancel_question

Retracts a pending question, for example when you found the answer another way. A stale approval arriving later reads as consent to work that has moved on.

### schedule_reminder

When the user asks "remind me later", set a one-time personal reminder with `body` (180 characters at most, or the call fails) and either `inMinutes` or `at` (an ISO timestamp with an explicit UTC offset or Z). Confirm the returned `fireAt` in their local time and never guess their timezone. For example, `{"body":"Check the deploy","inMinutes":30}`. It goes to their phone and the Pushary Mac app; with no phone connected, only to the Mac app if they have one. Tell the user any `warning` in the result. It usually arrives within a minute of `fireAt`, even after you exit. It does not schedule agent work. Call it with no arguments to list pending reminders, or pass `cancelReminderId` to cancel one; `cancelled: false` means nothing was cancelled: it was not found, already settled, or already sending. Limits: 30 days ahead, 25 pending per user in each workspace. Do not use `ask_user` for reminders.

### propose_scope

Agree the boundary of a run once, before the first edit. The user sees the paths you will change, the paths you will leave alone, and your definition of done, and agrees to all three in one tap.

**Propose a scope when** the run edits files and the boundary is not yet agreed: more than one file, or files you cannot all name before you start. **Do not propose one** for a single known file, for files the user named this turn, or for a run that changes no files and makes no promise worth keeping. Do not propose a new scope mid-run to widen an old one; the gate asks for the exact path when an edit needs it.

**What is enforced.** Only the path of a file you change, on `Edit`, `Write`, `MultiEdit`, Codex `apply_patch` and VS Code patch tools, and only where the Pushary hook runs, such as Claude Code, Codex and Gemini CLI. An edit outside the agreed paths becomes a question instead of an automatic approval. Shell commands, reads, web requests and MCP tools carry no path and are not checked. `doneWhen` and `promises` are read by the user, not checked by code. A scope can only turn an automatic approval into a question; it never approves anything. Agreeing to a scope approves none of its promises: still ask before an outside action that cannot be undone, costs money or reaches someone outside the team.

**Write paths as globs.** The matcher compares text. A word like `hubspot` matches no file and makes every edit ask; it belongs in `promises`. Write `docs/**`, not `docs`. Letter case matters. Use forward slashes and no leading `./`. For a run that changes no files, call it with no paths and put the whole boundary in `promises`.

**Read the result.** An empty `enforces` means nothing is checked automatically: tell the user. `hookSeen: false` means no hook has reported this `sessionId`, so the contract will never be found: fix the id or say the boundary is only a promise. Answered but not `ratified` means the user declined: ask which boundary they want. A yes typed in the chat does not ratify a scope; the boundary is then only a promise. Use the `sessionId` your client reports for this run. If it reports none and you have `list_sessions`, call it and take the session whose working directory matches yours with the newest `lastSeenAt`. If another live session shares that folder, on this machine or another, or you cannot tell, skip the scope and tell the user the boundary is only a promise. Never invent an id.

A scope lasts for the session, up to 12 hours, and ends at session end. A later ratified proposal replaces it.

### list_sessions

Read-only. Shows your live agent sessions and any questions still waiting. If another session is already waiting on the user, a second question competes for the same attention. Connector keys do not have this tool.

## Limits

- 8 open questions per agent session and 25 per workspace. When a question is refused for this, answer or cancel an open one.
- 10 notifications per 5 minutes per workspace. Every `schedule_reminder` call, including a list or a cancel, counts toward it.

## Answer Surfaces and Account Boundaries

| Surface | What the user can do |
| --- | --- |
| Mobile app | Answer confirm, select and input questions. Confirm notifications offer approve and deny on the lock screen, except for risky commands, which the app approves after Face ID or the passcode. Choices and text open the app. |
| Mac notch | Answer confirm, select, input and question-set questions, including keyboard controls. |
| Slack | Answer through buttons, menus or text modals when the integration and recipient are configured. |
| Browser | Open the decision page as a fallback; browser notifications need permission. |

Partner customers use scoped enrollment links issued by their application. Do not enroll them into the operator's account or send their decisions through personal tools. They answer on their enrolled phone, and in the Mac notch once they connect the Mac from the phone app. See https://pushary.com/docs/agents/embed for Partner setup.

## Identifying Your Agent

Pass `agentName` on every call as `{Agent Type} - {project or context}`, for example `"Claude Code - pushary repo"`, `"Hermes - daily-briefing"` or `"Cursor - frontend refactor"`. It is the title the user sees, so they know which agent is asking.
