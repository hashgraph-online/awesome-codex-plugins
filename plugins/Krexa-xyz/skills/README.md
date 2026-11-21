# Krexa skills

**Give your AI agent any trading idea. It tells you if the idea works, then runs
it for you, inside a loss limit the agent cannot break.**

Do it all from the chat you already use: Claude Code, Codex, Cursor, Hermes,
OpenClaw. You open the Krexa app for just one thing: signing. Nothing goes live,
and no money moves, until you do.

```bash
npx skills add krexa-xyz/skills --skill krexa -g
```

Then ask your agent:

> **"Here is a post: \<link\>. Does it hold up?"**

## What it looks like

> **You:** x.com/… is this strategy real?
>
> **Agent:** The rule: buy SOL when the 4h RSI drops below 30, sell 8% higher or
> 5% lower. Over the last 6 months: +14% vs +9% for just holding SOL, worst
> drop −11%, 23 trades. Want the deep test with real fees and slippage? It
> takes about 6 minutes.

*(Numbers are illustrative. Backtests use past prices and are not a promise.)*

## Start wherever you are

| You have… | Say |
|---|---|
| A post, reel or video | "Here is a link: \<link\>. What is the rule, and does it hold up?" |
| Your own rules | "Buy ETH when it closes above the 50-day average, sell below. Test it." |
| No strategy yet | "Copy Alpha Desk." · "What is working on SOL this month?" · "Show me the Krexa leaderboard." |
| A Binance, Bybit, OKX, Kraken or Coinbase account | "What do I hold on Binance?" |

**Alpha Desk** is Krexa's own strategy, trading Polymarket sports markets on the
same harness. Back it from the [Vault](https://www.krexa.xyz/app/strategies),
where every rule, trade, skip and P&L is public, wins and losses. Krexa takes 20%
of the net profit it makes you. Losses carry forward, so you never pay to get
back to where you started, and if it never profits you pay nothing.

## From curious to live, one step at a time

Each step costs a little more and tells you more. Stop at any of them.

| Step | You say | Costs | Takes |
|---|---|---|---|
| 1. Check | "Does this hold up?" | Free | 30 sec |
| 2. Backtest | "Backtest it." | Free | 1 min |
| 3. Deep test | "Run the deep test with real fees." | Free | ~6 min |
| 4. Paper trade | "Paper-trade it with $1,000." | Pretend money | As long as you like |
| 5. Go live, small | "Deploy it. Max $50 a trade, stop at −$20 a day." | Fund from $2 (Polymarket) or $15 (Hyperliquid). No Krexa fee. | Ongoing |

Then: *"How is my agent doing?"* · *"Why was that order blocked?"* · *"Stop it."*

## You chat. The app is only where you sign.

| In your agent's chat | In the Krexa app (on purpose) |
|---|---|
| Decode, check, backtest, deep test, research | Get your key, once |
| Paper trade, start and stop | **Approve and sign each live deploy** |
| Ask for a live deploy, with your limits | **Fund the agent** |
| Check P&L, trades and blocked orders | Add an exchange key |
| Pause a live agent at once | Withdraw, resume, raise a limit |
| | Back a desk such as Alpha Desk in the [Vault](https://www.krexa.xyz/app/strategies) |
| | Trade by hand in the [Terminal](https://www.krexa.xyz/app/terminal) |

The right-hand column is the safety, not a gap in the chat. The key your agent
holds **cannot** withdraw, transfer, fund, resume or raise a limit. Your limits
are checked in code on Krexa's servers on every order, and no prompt can talk
the agent past them. When an order breaks a limit, it is refused and you see
why:

> *Blocked: today's loss reached your $20 cap, so the agent stopped buying. Sells still run.*

Exchange keys never go through chat. If you paste one, the agent tells you to
delete it on the exchange and add a new one in the app.

**Trading by hand?** The [Terminal](https://www.krexa.xyz/app/terminal) is
Krexa's manual trading screen for Hyperliquid markets: chart, order book, market
and limit orders. Those trades are yours, not an agent's, so your agent limits
don't apply. Krexa sets no stop-loss there, and a leveraged position can be
liquidated. Your agent can't place Terminal orders.

## What it costs

| | Krexa's fee |
|---|---|
| Checking, backtesting, deep tests, paper trading | Free |
| Running your own agent live | Free |
| Trading by hand in the Terminal | Free |
| Backing Alpha Desk | 20% of the net profit it makes you. Losses carry forward, so no profit means no fee. |

Network, venue and slippage costs go to the chain or venue, not to Krexa.
Details: [krexa.xyz/pricing](https://www.krexa.xyz/pricing).

## Set up (about 2 minutes)

Your agent walks you through this the first time. In short:

1. Open **https://krexa.xyz/mcp/link?client=Hermes** (use your agent's name),
   log in, pick the wallet, and copy the key (`kxm_…`).
2. Save it as `KREXA_AGENT_KEY` yourself, rather than pasting it into chat:
   - Hermes: add `KREXA_AGENT_KEY=kxm_…` to `~/.hermes/.env`
   - OpenClaw: export it, or set `skills.entries.krexa.apiKey` in `openclaw.json`
   - Others: export `KREXA_AGENT_KEY` in your shell
3. Add the MCP server (your agent can do this for you):

   | | |
   |---|---|
   | URL | `https://www.krexa.xyz/mcp` |
   | Transport | Streamable HTTP |
   | Header | `Authorization: Bearer ${KREXA_AGENT_KEY}` |

   Use `www`. Bare `krexa.xyz` redirects, and most clients drop the key on a
   redirect. The old URL `https://api.krexa.xyz/api/v1/mcp` still works.
   Exact config for each agent: [skills/krexa/references/setup.md](skills/krexa/references/setup.md).
4. Reload the agent (Hermes: `/reload-mcp`) and ask: *"Who am I on Krexa?"*

**Claude Code:** `/plugin marketplace add Krexa-xyz/skills` then
`/plugin install krexa@krexa`. It asks for the key, stores it in secure
storage, and connects the server for you.

Install flags: `-g` installs for your user (all projects); leave it out to
install in the current project only. Add `-a hermes` or `-a openclaw` to
install for one agent only.

Paste the key only in a private chat with your own agent, never in a group.
Revoke it any time at https://krexa.xyz/mcp/link under **Connected agents**.

## Where it trades

From your agent: Solana spot and tokenized stocks (xStocks such as NVDAx),
Hyperliquid, Jupiter Perps, Polymarket and Polymarket Perps, and perps in your
own Binance, Bybit, OKX, Kraken or Coinbase account. Full limits:
[skills/krexa/references/limits.md](skills/krexa/references/limits.md).

The Krexa app covers more venues, including Hyperliquid HIP-4 outcomes, Jupiter
Predict, OKX DEX, Pump.fun and exchange spot. See
[all venues](https://www.krexa.xyz/marketplace).

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
