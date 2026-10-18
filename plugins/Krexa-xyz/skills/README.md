# Krexa skills

Skills that let your AI agent use [Krexa](https://krexa.xyz): turn a trading
idea, post or video into a tested strategy, backtest it, paper-trade it, and,
when you approve, run it as a live agent with hard limits.

Works with Hermes, OpenClaw, Claude Code, Codex, Cursor and any agent that
reads `SKILL.md` files and speaks MCP.

## Install

```bash
npx skills add krexa-xyz/skills --skill krexa -g
```

- `-g` installs for your user (all projects). Leave it out to install in the
  current project only.
- Add `-a hermes` or `-a openclaw` to install for one agent only.

### Claude Code

```text
/plugin marketplace add Krexa-xyz/skills
/plugin install krexa@krexa
```

Claude Code asks for your Krexa key when you enable the plugin, stores it in secure storage, and connects the MCP server for you.

Or tell your agent: *"Install the Krexa skill from github.com/Krexa-xyz/skills
and set it up."*

## Connect your Krexa account

The skill uses the Krexa MCP server. Your agent needs a key once.

1. Open **https://krexa.xyz/mcp/link?client=Hermes** (use your agent's name).
2. Log in, pick the wallet the agent may act for, and copy the key (`kxm_…`).
3. Put it in your agent's env as `KREXA_AGENT_KEY`:
   - Hermes: add `KREXA_AGENT_KEY=kxm_…` to `~/.hermes/.env`
   - OpenClaw: `skills.entries.krexa.apiKey` in `openclaw.json`, or export it
   - Others: export `KREXA_AGENT_KEY` in your shell
4. Add the MCP server (your agent can do this for you):

   | | |
   |---|---|
   | URL | `https://www.krexa.xyz/mcp` |
   | Transport | Streamable HTTP |
   | Header | `Authorization: Bearer ${KREXA_AGENT_KEY}` |

   Use `www`: bare `krexa.xyz` redirects, and most clients drop the key on a
   redirect. The old URL `https://api.krexa.xyz/api/v1/mcp` still works.

   Exact config for each agent: [skills/krexa/references/setup.md](skills/krexa/references/setup.md).
5. Reload the agent (Hermes: `/reload-mcp`) and ask: *"Who am I on Krexa?"*

Paste the key only in a private chat with your own agent, never in a group.
Revoke a key any time at https://krexa.xyz/mcp/link under **Connected agents**.

## What you can ask

- "Here is a post: <link>. What is the rule, and does it hold up?"
- "Backtest it, then run the deep test with real fees."
- "Paper-trade it with $1,000."
- "Deploy it. Max $50 a trade, $200 a day, stop at -$20 a day."
- "How is my agent doing?" · "Stop it."

## What the agent can and cannot do

| Can | Cannot |
|---|---|
| Read your agents, P&L and trades | Withdraw, transfer or fund money |
| Extract rules, backtest, run deep tests and research | Resume an agent or raise a limit |
| Start and stop paper trading | Deploy without you |
| Pause a live agent at once | Hold any wallet key |
| Ask for a live deploy | |

Every live deploy returns an approval link. Nothing trades until **you** open
it, check the rule and limits, and sign with your own wallet. Limits are
checked in code on Krexa's servers on every order; a prompt cannot change
them. Details: [skills/krexa/references/limits.md](skills/krexa/references/limits.md).

Backtests and paper results use past prices or pretend money. They are not a
promise of future returns.

## Skills in this repo

| Skill | What it does |
|---|---|
| [`krexa`](skills/krexa/SKILL.md) | Research, backtest, paper-trade and run Krexa trading agents |

## Contributing

The source of these files is the Krexa monorepo (`skills/krexa`). Open issues
here; changes are copied over from there.

License: MIT-0.
