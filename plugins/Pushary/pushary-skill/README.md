<p align="center">
  <h1 align="center">Pushary: human-in-the-loop for AI agents</h1>
  <p align="center">
    Get a ping when your agent needs you. Answer from your phone and the agent picks up where it paused.
    <br />
    <a href="https://pushary.com/ai-agents?utm_source=github&utm_medium=oss-skill&utm_campaign=pushary-skill&utm_content=readme"><strong>Get started</strong></a>
    &nbsp;&middot;&nbsp;
    <a href="https://skills.sh/Pushary/pushary-skill/pushary">Skills directory</a>
    &nbsp;&middot;&nbsp;
    <a href="https://github.com/Pushary/pushary-skill/issues">Report a bug</a>
  </p>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License" /></a>
  <a href="https://skills.sh/Pushary/pushary-skill/pushary"><img src="https://img.shields.io/badge/skills.sh-listed-brightgreen" alt="skills.sh" /></a>
  <a href="https://www.npmjs.com/package/pushary"><img src="https://img.shields.io/npm/v/pushary" alt="npm" /></a>
  <a href="https://pypi.org/project/hermes-plugin-pushary/"><img src="https://img.shields.io/pypi/v/hermes-plugin-pushary" alt="PyPI" /></a>
  <a href="https://glama.ai/mcp/servers/Pushary/pushary-skill"><img src="https://glama.ai/mcp/servers/Pushary/pushary-skill/badges/score.svg" alt="Glama score" /></a>
</p>

## Start here

Claude Code is writing a fix when you step away. It needs to know which test to run. Pushary sends the question to your phone. With calls enabled, a missed push can turn into a phone call. Say “run the checkout test” and Claude gets your answer in the same session.

[Pair your phone](#personal-setup-phone-first) to try this with your agent. Already paired? [Try it with three agents](examples/which-agent-is-waiting.md) and see which session gets your answer. You can also [try a browser simulation](https://pushary.com/try?utm_source=github&utm_medium=oss-skill&utm_campaign=pushary-skill&utm_content=demo) without signing up.

| What you want to build | Start with |
| --- | --- |
| Notifications, questions and approvals for your own AI agents, such as Claude Code or Codex | The setup instructions below |
| An enforced tool approval in the Vercel AI SDK | [Runnable AI SDK example](https://github.com/Pushary/pushary-ai-sdk/tree/main/examples) |
| A LangGraph workflow that branches on a human decision | [Runnable LangGraph example](https://github.com/Pushary/pushary-langgraph/tree/main/examples) |
| Another agent framework | [All Pushary integrations](https://github.com/Pushary) |
| When an agent should stop and ask a person, and how to add that step in any framework | The [`pushary-human-in-the-loop` skill](skills/pushary-human-in-the-loop/SKILL.md) |

The skill and adapters are MIT-licensed. Hosted phone delivery requires a Pushary
account; embedding approvals for your own users requires Partner access.
The two framework examples also run locally with simulated answers and no credentials.

If Pushary helped you, [star this repo](https://github.com/Pushary/pushary-skill).
Want to help? [Public issues and patches are welcome](CONTRIBUTING.md).

---

Pushary lets your AI agent send task updates and ask you for a decision on your phone. Supported host hooks also enforce approvals before an action runs.

Hosted delivery requires a paid [Pushary plan](https://pushary.com/pricing?utm_source=github&utm_medium=oss-skill&utm_campaign=pushary-skill&utm_content=readme). Connecting MCP lets your agent ask a person for a decision. A plain MCP client can still use its own tools independently. To require approval before a command runs, install a [supported host hook](https://pushary.com/docs/agents/supported-agents) or have your application run the protected action only after an explicit approval for that request. For host hooks, check the [timeout and handoff rules](https://pushary.com/docs/agents/unanswered) for your agent and policy.

## What you get after you sign in

1. Sign in and pick a plan. New customers start with a 3-day trial.
2. Run `npx -y pushary@latest setup` once. It connects Claude Code, Codex, Cursor, Gemini CLI, Hermes and the other agents it finds on this computer.
3. When an agent needs a yes or an answer, the question arrives on your phone (the Pushary app for iOS and Android), on your Mac, or in the dashboard.
4. You answer with one tap, or type a short reply, and the agent keeps going. The dashboard keeps a record of what each agent asked and what you answered.

Read the [quickstart](https://pushary.com/docs/agents/quickstart?utm_source=github&utm_medium=oss-skill&utm_campaign=pushary-skill&utm_content=readme) for each step, or see [what Pushary does for AI agents](https://pushary.com/ai-agents?utm_source=github&utm_medium=oss-skill&utm_campaign=pushary-skill&utm_content=readme).

## Plans

Each plan starts with a 3-day trial for new customers. During the trial, Agent, Agent Pro and Team include 5 call minutes.

| Plan | Price | What you get |
| --- | --- | --- |
| [Agent](https://pushary.com/pricing?utm_source=github&utm_medium=oss-skill&utm_campaign=pushary-skill&utm_content=readme) | $9.99 a month | One person and every AI agent they run. Approve, deny or answer from your phone or Mac. 10 call minutes a month. |
| [Agent Pro](https://pushary.com/pricing?utm_source=github&utm_medium=oss-skill&utm_campaign=pushary-skill&utm_content=readme) | $19.99 a month | Everything in Agent, plus unlimited notifications, budgets and priority support. 20 call minutes a month. |
| [Team](https://pushary.com/teams?utm_source=github&utm_medium=oss-skill&utm_campaign=pushary-skill&utm_content=readme) | $59 a month for 5 people, $12 for each extra person | Each person gets their own agent’s questions. On supported hooks, route a step such as a production deploy to the teammate who approves it. See who answered in the shared record. Includes export and 60 shared call minutes a month. |

Missed the push? Pushary can call you, by default within a minute of the push, and read the request. You approve it, say no or tell the agent what to do. Calls need a confirmed phone number and work in English, German, French and Dutch. Calls cover Claude Code, Codex, Gemini CLI, Hermes and the other agents listed on the calls page, not yet Cursor, VS Code, OpenCode or OpenClaw. [Phone calls](https://pushary.com/calls?utm_source=github&utm_medium=oss-skill&utm_campaign=pushary-skill&utm_content=readme) · [How calls work](https://pushary.com/docs/agents/phone-calls?utm_source=github&utm_medium=oss-skill&utm_campaign=pushary-skill&utm_content=readme)

## How It Works

```
AI Agent  ->  MCP Protocol  ->  Pushary API  ->  Push Notification  ->  Your Phone
```

Pushary is an [MCP server](https://modelcontextprotocol.io/) that connects your AI agent to push notifications. The agent calls Pushary's tools over the Model Context Protocol, and you receive notifications instantly on any device.

**Three question types** - yes/no confirmations, multiple choice, and free text input. Your agent picks the right one for the situation.

**Rich context notifications** - agents can include file changes, error details, and suggested next steps in a detail page you see when tapping the notification.

**Agent identification** - when you run multiple agents, each notification shows which agent is asking so you always know what you're responding to.

**Permission hooks** - route Claude Code's tool approval prompts through push notifications so you can approve or deny from your phone.

---

## Personal setup: phone first

Run the pairing setup in your agent's terminal:

```bash
npx -y pushary@latest setup
```

Install [Pushary on your phone](https://pushary.com/download), scan the QR or open the printed link, compare the fingerprints, and approve. Setup then configures the selected agent's tools, supported hooks and skill. You do not need to copy an API key first. Personal accounts require a [paid plan](https://pushary.com/pricing). Existing credentials are reused.

Verify setup:

```bash
npx -y pushary@latest doctor
```

Ask your agent for one harmless test question. Confirm the intended device receives it and the answer returns to the same task.

The [Claude Code guide](https://pushary.com/docs/agents/guides/claude-code?utm_source=github&utm_medium=oss-skill&utm_campaign=pushary-skill&utm_content=readme) covers its hooks and permission modes. [Supported agents](https://pushary.com/docs/agents/supported-agents?utm_source=github&utm_medium=oss-skill&utm_campaign=pushary-skill&utm_content=readme) shows what Pushary can do in each of the others.

For Hermes specifically:

```bash
npx -y pushary@latest setup --agents hermes
```

This writes the native plugin to `~/.hermes/plugins/pushary` and turns it on with `hermes plugins enable pushary` and `hermes config set`. Restart Hermes afterward with `hermes gateway restart`. The plugin provides notification, question, wait, cancel, reminder and scope tools, plus Partner enrollment and customer-question tools. Its parameters use snake_case; use the [Hermes skill](skills/hermes/SKILL.md), not MCP parameter names. The native approval transport preserves Hermes' session and standing approvals.

### Try OpenCode with your phone

Connect OpenCode with `npx -y pushary@latest setup --agents opencode`, then start a fresh session. Ask it to send “Did this reach your phone?” through Pushary and wait for your answer. Tap **No** and check that OpenCode reports your choice in the same session. On November 25, 2026, I ran this check with “Did the OpenCode test reach your phone?” One phone received the question. I answered **Yes** from the notification and OpenCode reported **yes** in the same session. For setup help, see the [OpenCode notification guide](https://pushary.com/opencode-notifications?utm_source=github&utm_medium=oss-adapter&utm_campaign=opencode-skill&utm_content=readme).

## Mac notch and other answer surfaces

Install [Pushary for Mac](https://pushary.com/download), sign in with the same personal account and connect your agents from the app. The notch provides confirm, choice, text and question-set controls with keyboard support. Keep the app running for presence and delivery; verify one harmless question there, then phone fallback while away from the Mac.

| Surface | Answers |
| --- | --- |
| Mobile | Confirm, choice and text in the app. Supported confirm notifications expose lock-screen approve/deny; arbitrary choices and text open the app. |
| Mac notch | Questions for the signed-in account, including keyboard answering, and Partner customers' questions once they connect the Mac from their phone. |
| Slack | Buttons, choice menus and text modals when the integration and recipient are configured. |
| Browser | Decision-page fallback and browser notifications when permission is enabled. |

Delivery follows your settings and presence. `push_first` uses presence, `push_only` requests push every time, `notify_only` keeps decisions in the current client, and `terminal_only` avoids push. A successful API call alone does not prove a device displayed the request.

## Team setup: send a risky step to a lead

On [Pushary for Teams](https://pushary.com/teams?utm_source=github&utm_medium=oss-skill&utm_campaign=pushary-skill&utm_content=team-setup), each person runs the same setup and connects their own agents. Their agents' questions go to them. An owner or admin can send a chosen step to someone else with a routing rule in **Policies**, under **Approval routing**:

| Field | Example |
| --- | --- |
| Tool pattern | `Bash(git push:*)` |
| Repository | `infra`, or all repositories |
| Route to | The Admins role, or one person |

Claude Code, Codex, Cursor and Gemini CLI shell calls all match a `Bash(...)` rule, so one rule covers a team that runs several agents. Whoever answers in the phone app, Mac app or dashboard is recorded by name, next to whose agent asked.

To test the route, pick a disposable repository and send its push requests to a teammate. Ask Claude Code to push a test branch there. Have your teammate decline in the Pushary app. In the dashboard, check whose session asked and who declined. The branch should stay local.

What a routing rule doesn't do:

- It doesn't lock the terminal. If nobody answers in time, the person running the agent can still approve at the agent's own prompt, and that yes isn't recorded.
- The phone can only deny risky steps such as a force push or `rm -r`. Approve those in the dashboard.
- It needs a second person. Routing starts once someone else joins the workspace.

Team is $59 a month for 5 people, plus $12 for each extra person. [How a routing rule works, step by step](https://pushary.com/blog/route-claude-code-permission-prompt-to-team-lead?utm_source=github&utm_medium=oss-skill&utm_campaign=pushary-skill&utm_content=team-setup).

## Partner setup: your own customers

Personal pairing connects you, the operator. Partner integrations enroll each of your application's customers through a scoped connection link and address decisions using your stable customer ID. Customers use the mobile enrollment flow; do not route their approvals to your personal Mac inbox or share an operator API key.

Start with the [Partner integration guide](https://pushary.com/docs/agents/embed), then a [Mastra agent example](https://github.com/Pushary/pushary-mastra/tree/main/examples), [AI SDK example](https://github.com/Pushary/pushary-ai-sdk/tree/main/examples) or [LangGraph example](https://github.com/Pushary/pushary-langgraph/tree/main/examples). Tools choose confirm, choice or text. Approving an action and supplying an answer are different operations; a text answer saying “yes” is not permission to execute another tool.

Partner plans start at $99 a month. Your customers install the Pushary app and need no Pushary account or plan of their own. [Partner plans](https://pushary.com/partners?utm_source=github&utm_medium=oss-skill&utm_campaign=pushary-skill&utm_content=readme) · [Try the browser demo](https://pushary.com/try?utm_source=github&utm_medium=oss-skill&utm_campaign=pushary-skill&utm_content=readme)

## Manual fallback

For a client that needs manual MCP configuration, obtain your key in the Pushary dashboard and configure:

```json
{
  "mcpServers": {
    "pushary": {
      "url": "https://pushary.com/api/mcp/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY"
      }
    }
  }
}
```

Keep the key private. Install the skill with `npx skills add Pushary/pushary-skill` if the client supports skills.sh. Manual MCP provides cooperative questions and notifications; enforced approvals require the supported host hooks/runtime integration.

Claude Code users can alternatively install this repository as a plugin:

```
/plugin marketplace add Pushary/pushary-skill
/plugin install pushary
```

The plugin carries the `pushary` and `pushary-human-in-the-loop` skills. The Hermes, ChatGPT and Cowork skills in `skills/` are for those hosts.

The plugin's MCP server sends `PUSHARY_API_KEY` from the environment Claude Code starts in. Claude Code opened from the Dock, an IDE or another app does not read your shell profile, so the Pushary tools are missing and `/mcp` shows "Server rejected the configured Authorization header (HTTP 401)". Put the key in the `env` block of `~/.claude/settings.json`, which Claude Code reads however it is started:

```json
{
  "env": {
    "PUSHARY_API_KEY": "YOUR_API_KEY"
  }
}
```

Then restart Claude Code.

Pick one installation path: installing the plugin on top of CLI-installed Claude hooks can run hooks twice. Use `npx -y pushary@latest clean` before switching paths.

The plugin starts each hook through `npx`, which is too slow for the hook that streams live reply previews to your phone, so the plugin leaves that hook out. For live previews, install with `npx -y pushary@latest setup` instead. Setup installs every hook as a local command.

The plugin also runs the hook through `npx` before every MCP, `WebFetch`, `Task` and `Agent` call, so the kill switch and standing denies cover those tools. That adds about 2 seconds to each of those calls when npx has the package cached, and about 8 seconds when it does not, which happens on the first call after each CLI release. The `WebFetch`, `Task` and `Agent` hook may run for up to 30 seconds so that a cold start still finishes the check. Setup's local hooks do not pay the `npx` start.

---

## Setup: Lovable

[Lovable](https://lovable.dev) is a hosted app builder, so there is no local install step (`npx skills add` does not apply). You connect the MCP server in Lovable's UI, then paste the skill into Lovable's Knowledge so the agent uses it on its own.

**1. Connect the MCP server.** In Lovable, go to **Settings -> Connectors -> Personal connectors** (paid Lovable plans), click **New MCP server**, set the URL to `https://pushary.com/api/mcp/mcp`, choose **Bearer token**, and paste your API key (`pk_xxx.xxx`).

**2. Add the skill to Knowledge.** Lovable cannot install skills via `npx`, so paste the skill guidance into **Settings -> Knowledge**. Use the condensed [`SKILL-LITE.md`](skills/pushary/SKILL-LITE.md) as the source. This makes the Lovable agent notify you when a build finishes and ask before risky changes, without you prompting each time.

Lovable gets notifications and questions only (no enforced gate, since it has no permission hook). Full walkthrough: [Lovable guide](https://pushary.com/docs/agents/guides/lovable).

---

## Setup: Claude Chat and Cowork

For Claude Chat or Claude Code, use [Pushary for Claude](https://github.com/Pushary/claude-plugin). In Chat, open **Customize > Plugins > Add > Add marketplace**, add `https://github.com/Pushary/claude-plugin`, and install **Pushary for Claude**. In Claude Code, run `/plugin marketplace add Pushary/claude-plugin`, then `/plugin install pushary@pushary-claude-plugin`.

For Cowork, the existing [Pushary for Cowork plugin](https://github.com/Pushary/cowork-plugin) remains available. Add `https://github.com/Pushary/cowork-plugin` as the marketplace and install **Pushary for Cowork**. Cowork also supports standing instructions under **Settings > Cowork**. Its existing plugin, marketplace, and [`pushary-cowork`](skills/pushary-cowork) skill identifiers are preserved.

Both bundles use the public OAuth connector and the same shared skill. Connect Pushary from the plugin's **Connectors** tab in Chat or Cowork, or `/mcp` in Claude Code, and sign in with the same Pushary account used by your phone or Mac. No CLI or API key is needed for either bundle.

If the connector is missing, add `https://pushary.com/api/mcp/mcp` under **Customize > Connectors > Add custom connector** and leave the OAuth Client ID and Secret fields empty. Enable Pushary in the conversation, ask one harmless test question, and verify your answer returns to Claude.

These bundles provide questions and notifications and install no native permission hooks. For Claude Code approval hooks, use the Claude Code setup above. Choose one installation path per app to avoid duplicate Pushary connectors. [Full Claude guide](https://pushary.com/docs/agents/guides/claude-desktop).

---

## Tools

The skill guides these MCP tools:

| Tool | Description |
|------|-------------|
| `send_notification` | Send a push notification with optional rich context (file changes, errors, next steps) |
| `ask_user` | Ask the user a question via push - yes/no, multiple choice, or free text |
| `wait_for_answer` | Long-poll for the user's response to a question |
| `cancel_question` | Cancel a pending question that's no longer relevant |
| `list_sessions` | Read-only view of your live agent sessions and pending questions |
| `propose_scope` | Ratify the boundary of a run: file globs, enforced on supported hosts, or a recorded promise when the run changes no files |

Full tool documentation with parameters, examples, and usage guidelines is in [`skills/pushary/SKILL.md`](skills/pushary/SKILL.md).

## Human-in-the-Loop

The agent can ask you decisions via push and wait for your answer:

```
Agent: "Which auth strategy should I use?"
  Options: JWT tokens / Session cookies / OAuth2 + PKCE
  -> push to your phone

You: tap "JWT tokens"

Agent: proceeds with JWT implementation
```

Supports three question types:
- **Confirm** - yes/no binary decisions
- **Select** - pick from 2-6 options
- **Input** - free text response

Read `answered`, `status` and `handoffAction` (or `nextAction`) from the tool result. Poll only as directed; cancel a live question before handing it to another surface and honor any winning answer. Expiry and waits follow server policy. Silence is not approval, and a late reply cannot restart an ended agent turn.

## Packages

| Package | Registry | Description |
|---------|----------|-------------|
| [`pushary`](https://www.npmjs.com/package/pushary) | npm | The Pushary CLI: setup, permission hooks and doctor. Also published as `@pushary/agent-hooks`, the same package |
| [`hermes-plugin-pushary`](https://pypi.org/project/hermes-plugin-pushary/) | PyPI | Hermes Agent native plugin |

## Related repositories

- [Pushary for Cursor](https://github.com/Pushary/cursor-plugin) and [Pushary for VS Code](https://github.com/Pushary/vscode-plugin): editor plugins with approval hooks.
- [Pushary for Claude](https://github.com/Pushary/claude-plugin): the Claude Chat and Claude Code plugin.
- [Pushary for Mac](https://github.com/Pushary/pushary-mac): the Mac app that answers from the notch.
- [Pushary plugin for Hermes](https://github.com/Pushary/hermes-plugin-pushary): the native Hermes Agent plugin.

## Compatible Agents

Start with the [supported agents guide](https://pushary.com/docs/agents/supported-agents). Find your agent to see how to connect it and which actions it can hold for approval. For example, Cursor needs its editor hooks to gate commands. Codex uses native permission hooks. A compatible MCP client can ask questions through Pushary even when its own permission prompts stay in the client.

For OpenHands Agent Canvas, choose either the CLI setup or the plugin. The [OpenHands guide](https://github.com/Pushary/openhands-plugin#install) walks you through denying a file creation and checking the result.

## Publishing the MCP registry entry

`server.json` is not published by merging it. The [MCP registry](https://registry.modelcontextprotocol.io) serves one record per version, so an edit here reaches nobody until the new version is pushed to the registry, and the old text keeps being what every agent reads.

Everyday path: bump `version` in `server.json`, merge to `main`, then sync the public skill mirror. Its release workflow publishes the new registry entry.

The release workflow publishes from the public Pushary repository so GitHub OIDC can prove ownership of the `io.github.Pushary/pushary` namespace. Verify the workflow and registry result after release.

Manual fallback, from this directory:

```
curl -L "https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_$(uname -s | tr '[:upper:]' '[:lower:]')_$(uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/').tar.gz" | tar xz mcp-publisher
./mcp-publisher login github
./mcp-publisher publish
```

Check what the registry actually serves, which is the only number that matters:

```
curl -s "https://registry.modelcontextprotocol.io/v0/servers?search=pushary"
```

That endpoint returns **every** version, oldest first. Read the entry whose `_meta."io.modelcontextprotocol.registry/official".isLatest` is `true`; the first row in the list is the oldest record, not the live one.

## Contributing

Contributions are welcome! Please read the [contributing guide](CONTRIBUTING.md) before submitting a pull request.

## Security

If you discover a security vulnerability, please report it responsibly. See [SECURITY.md](SECURITY.md) for details.

## Funding

This project is fully funded by **[RalphNex OU](https://ralphnex.com/)**, an Estonian software development agency.

## License

[MIT](LICENSE) - Copyright (c) 2025 RalphNex OU
