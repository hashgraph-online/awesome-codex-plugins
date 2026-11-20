# Candor Finance

Candor is a personal finance app that helps you reach your money goals with ChatGPT, Claude, or the AI agent you already use. Your agent works from your real bank, card, loan, and investment accounts: it sets up goals and a budget with you, finds money you are losing to fees, price increases, or missed refunds, and remembers your plan and decisions between conversations. Candor reviews your spending, bills, debt, savings, and investments and tells your agent what's worth talking through and why. Candor never moves money.

[![Reach your money goals with your AI agent](https://candor.money/og/candor-og-home.png)](https://candor.money)

**[Start free](https://app.candor.money/signup)** ·
[See how it works](https://candor.money) ·
[Security](https://candor.money/security)

- Works with ChatGPT, Codex, Claude, Claude Code, Grok Bot, Gemini CLI,
  OpenClaw, Hermes, and any agent that supports MCP and Agent Skills.
- Free to try with your own transactions. Bring your history
  over from Monarch, YNAB, Copilot, or any bank, and your agent adds your
  accounts from the file.
- The Personal plan connects your US banks, cards, and brokerages read-only,
  so everything comes in automatically. [See pricing](https://candor.money/#pricing).
- Your data is not sold or used to train models.
- Every agent action is recorded with its reason.

## Add Candor to your agent

| Agent | Where to get it |
| --- | --- |
| ChatGPT and Codex | [Candor Finance in ChatGPT's directory](https://chatgpt.com/plugins/plugin_asdk_app_6a74cd40f53c8191905b51d8706da78d) |
| Claude | [Candor Finance in Claude's directory](https://claude.ai/directory/candor-money) |
| Claude Code | [Install from this repo's marketplace](https://candor.money/connect/claude-code) |
| Gemini CLI, OpenClaw, Hermes, and others | Send your agent [START.md](https://candor.money/START.md) |

Your agent asks you to approve its access once, then takes its first look.
Setup guides for each agent are at
[candor.money/connect](https://candor.money/connect).

## What stays true

- **Candor never moves money.** Accounts connect read-only through a
  bank-grade connection provider. Your agent acts outside Candor only with
  your okay.
- **Figures come from your records.** Candor computes totals, budgets, and
  goal paces from your accounts, so your agent isn't guessing a plausible
  number.
- **You can see what your agent did and why.** Every action is recorded with
  its reason, and your plans and decisions stay saved when you switch agents.
- **Your data isn't sold or used to train models.** No ads. You're the
  customer. See [Privacy](https://candor.money/privacy).

## What this plugin runs and sends

- **No hooks, commands, agents, or background processes.** The plugin adds
  skills and one MCP server, nothing else.
- **Skills are instructions.** Each skill is Markdown, with no scripts.
- **One MCP server, Candor's own.** It is the hosted server at
  `https://api.candor.money/mcp`, which your agent authorizes with OAuth. Through it the
  agent reads and saves your Candor workspace. It cannot move money or change
  anything at a financial institution.
- **Two non-secret headers.** Requests to that server carry
  `Candor-Agent-Package-Version` and, where the host supports it,
  `Candor-Agent-Package-Route`, naming the package version and where it
  was installed from. Neither holds a credential or personal data.
- **No local secrets.** The plugin reads no environment variables,
  credentials, or local files.
- **`openclaw/` is separate.** That subtree is a CLI-based skill for OpenClaw
  only and is not part of this plugin.

## For agents: connection materials

The official package for [Candor](https://candor.money). It gives the AI agent
you already use the person's records, the figures Candor computes from them,
the goals, budget, rules, and notes it keeps, and Candor's review of what's
worth talking through, plus one skill per job: getting started, planning a
goal, budgeting, check-ins, a full checkup, sorting transactions, finding money, tax prep, and
adding records.

Give your agent [START.md](https://candor.money/START.md). It has the MCP
connection, skill download, and supported package options. The agent uses its
own harness's setup workflow and asks you only for steps it cannot complete.

- **MCP:** `https://api.candor.money/mcp`, Streamable HTTP with OAuth discovery and dynamic
  client registration. Your harness obtains its own client ID; no shared client
  secret is needed.
- **Skills:** every directory under [skills/](./skills). `candor-finance` is the
  front door and the rest are workflows. START also links a single-skill ZIP
  that carries all of them for hosts that upload one skill.
- **Supported packages:** Agent Plugins 1.0.0 (`plugin.json`, `skills/`,
  `mcp.json`), Claude and Codex marketplaces (`.claude-plugin/` and
  `.codex-plugin/`), and a Gemini CLI extension (`gemini-extension.json`).
  Use whichever format your harness supports, or install skill and MCP separately.

Your harness owns installation, authorization, skill locations, and reloads.
Keep working installations. Once the skill and tools are available, call
`candor_open` for MCP or run `candor open` for the CLI, then continue into
the user's financial task. Use a private runtime or per-user account isolation
before authorizing personal financial access on a shared host.

Grok Bot installs the `cursor/` plugin from the Cursor Marketplace. It pairs
the same MCP-based skill with the remote MCP server and is listed for Grok Bot
only; `.cursor-plugin/marketplace.json` points the marketplace at it.

The root skill uses MCP, including for capable OpenClaw and Hermes hosts.
The separate `openclaw/skills/` projection uses the Candor CLI and is only for
CLI installations. Keep the skill matched to the connection it operates.
Candor continues to enforce sign-in, access, and financial-data permissions.

Manage your Candor account and subscription at
[app.candor.money](https://app.candor.money). When Candor gives the agent a
secure account link, it explains the required step and opens that exact page.

- [Installation materials and guides](https://candor.money/START.md)
- [Connector support](https://candor.money/support)
- [Terms](https://candor.money/terms)

Except for the scoped MIT-0 OpenClaw skill subtree and the scoped MIT
`cursor/` plugin, Copyright 2026 Candor Systems, Inc. All rights reserved.
See [LICENSE](LICENSE).

## Release notes

See [the changelog](./CHANGELOG.md) for changes by package version.
