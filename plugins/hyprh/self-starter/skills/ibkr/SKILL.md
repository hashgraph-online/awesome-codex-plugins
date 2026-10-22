---
license: MIT
name: ibkr
description: Keep an eye on an Interactive Brokers (IBKR) account or prices and speak up when something changes - new executions, prices crossing a level, option assignments and exercises, deposits and withdrawals, big moves in net asset value. Use when the user wants Codex to watch their IBKR account or IBKR market data, and when handling a fire of an IBKR trigger.
---

# Watch IBKR

Read the skill `self-starter:triggers` first for how triggers and fire messages work. There are two ways to watch IBKR; pick by what the user has.

## With IB Gateway and the ibkr skill (real time)

If the user runs IB Gateway or TWS on this machine and has the `ibkr` skill installed (Python scripts on `ib_async`, usually in a skills folder such as `~/.codex/skills/ibkr`; look for `scripts/trade/get_executions.py`), write a probe that runs its read-only scripts with `--json`. Probes run as the user, so they can call Python and reach the Gateway on 127.0.0.1.

- New executions (event mode): `python3 <skill>/scripts/trade/get_executions.py --json` prints `{"account", "count", "fills": [{"time", "contract", "side", "shares", "price", "exec_id", ...}]}` for today. Use `exec_id` as the event key.
- A price level (state mode): `python3 <skill>/scripts/quote/get_snapshot.py NVDA --json` prints `{"data": [{"symbol", "last", "close", "bid", "ask", ...}]}`.
- Positions and P&L: `scripts/trade/get_portfolio.py --json`, `scripts/trade/get_pnl.py --json`.
- Pass `IB_CLIENT_ID` in the command's environment with a number of its own (such as 2061), so the probe does not disconnect the user's own session, which uses the default. `IB_GATEWAY_PORT` picks paper (4002, the default) or live (4001); ask which one.
- On failure the scripts print `{"error": "..."}` and exit non-zero; throw it, so the user hears when the Gateway is down or logged out.
- A probe only reads. Never call `place_order.py`, `modify_order.py`, `cancel_order.py` or other trading scripts from a probe. If the user wants Codex to trade when the trigger fires, say that a fire in a background thread cannot ask for the confirmation live orders need, and make the task prepare the order and ask in the origin thread instead.
- Check every 1 to 5 minutes during market hours and slow down outside them (return `next_check_in`).

```ts
// New IBKR executions, through the ibkr skill's read-only script.
const input = JSON.parse(await new Response(Deno.stdin.readable).text());
const { skill_dir, account } = input.params; // absolute path of the ibkr skill
const args = [`${skill_dir}/scripts/trade/get_executions.py`, "--json", ...(account ? ["--acc-id", account] : [])];
const out = await new Deno.Command("python3", { args, env: { IB_CLIENT_ID: "2061" } }).output();
const result = JSON.parse(new TextDecoder().decode(out.stdout) || "{}");
if (!out.success || result.error) throw new Error(result.error ?? (new TextDecoder().decode(out.stderr).trim() || "get_executions.py failed"));
console.log(JSON.stringify({
  events: result.fills.map((fill: { exec_id: string; side: string; shares: number; contract: string; price: number }) => ({
    key: fill.exec_id,
    summary: `${fill.side === "BOT" ? "Bought" : "Sold"} ${fill.shares} ${fill.contract} at ${fill.price}`,
    data: fill,
  })),
  summary: `${result.count} fill(s) today in ${result.account}`,
}));
```

## Without a Gateway: the Flex Web Service recipe

This sets up a trigger from the ready-made recipe `ibkr-account`. It reads Interactive Brokers' Flex Web Service with a read-only token: it can read reports, it cannot trade or move money, and nothing needs to run on this machine. It is not real time (see the limits below).

### What the user sets up once (about 5 minutes, in IBKR)

Walk the user through these steps; they happen in the IBKR Client Portal and a terminal, not in the chat.

1. Client Portal > Performance & Reports > Flex Queries.
2. Create a **Trade Confirmation Flex Query**: section Trade Confirmations, format XML, period Today. Note its Query ID. This reports new executions 5 to 10 minutes after they happen.
3. Optional, recommended: create an **Activity Flex Query** with Open Positions, Cash Transactions, Net Asset Value (NAV) in Base, Change in NAV and Trades; format XML; period Last Business Day. Note its Query ID. This adds deposits and withdrawals, position changes and NAV moves, once a day after the close.
4. On the Flex Queries page, open Flex Web Service Configuration, enable it and generate a token.
5. In a terminal: `self-starter secret set IBKR_FLEX_TOKEN --hosts ndcdyn.interactivebrokers.com,gdcdyn.interactivebrokers.com` and paste the token when asked. The token must never be pasted into the chat; if the user offers it, tell them to use the command instead.
6. Optional: `self-starter channel email <their address>` to also get the results by email.

Query IDs are not secret; the user can tell you them in the chat.

### Create the trigger

Call `trigger_recipes` to see the recipe's parameters, then `trigger_draft` with `recipe: "ibkr-account"` and a definition like this (no code, no permissions: the recipe supplies them):

```json
{
  "id": "ibkr-watch",
  "name": "IBKR account watch",
  "intent": "<the user's words>",
  "probe": { "params": { "trade_query_id": "123456", "activity_query_id": "123457", "nav_move_pct": 3 } },
  "action": { "type": "agent", "prompt": "<see below>", "sandbox": "read-only" },
  "target": { "kind": "dedicated", "cwd": "<a notes folder, or leave out>" },
  "notify": { "when": "receipt", "channels": ["desktop", "email"] }
}
```

- Parameters: `trade_query_id` and/or `activity_query_id` (at least one), `nav_move_pct` (default 3), `large_trade_value` (only report executions worth at least this much; default 0 = all), `cash_types` (default `["Deposits/Withdrawals"]`; add `"Dividends"` if the user wants those), `watch` (default all of `trades`, `cash`, `positions`, `nav`).
- Leave `channels` out unless the user asked for email; `"email"` only works after `self-starter channel email` (`service_status` shows which channels are set up).
- If the user only wants to be told, use `"action": {"type": "notify"}`: every change becomes a notification, without Codex.
- A good `action.prompt` (adapt it to what the user asked): "Something changed in my IBKR account. For each change, say what it is (my own order filling, an option assignment or exercise, a dividend, a transfer), whether it looks expected or unusual, and what I should check. Put anything that could be unauthorized, such as a trade or withdrawal I did not make, first. Do not place orders or change anything. Keep it short."
- Checks run every 15 minutes around US market hours and every 2 hours otherwise; IBKR asks clients not to poll more often. The first check only records what is there; changes after that fire.

Tell the user, before `trigger_activate`: what is watched, how quickly they hear about each kind of change (executions 5 to 10 minutes; cash, positions and NAV the morning after), where results go, and that the token is read-only.

## Handling a fire

With the Flex recipe, the `<trigger-data>` block lists events with keys such as `trade:U1234567:...`, `cash:...`, `position:...`, `nav:...`; with a Gateway probe, whatever that probe reports.

- Group by account. Lead with anything that could be unauthorized or risky: a trade or withdrawal the user may not have made, an option assignment, a large NAV drop.
- For each event, say in plain words what happened and whether it looks expected. If the action prompt mentions the user's notes or plans, compare with them.
- Never place orders, move money, or log in anywhere; IBKR data here is read-only. Suggest what the user should check in IBKR instead.
- Set `notify` to true when something needs the user's attention, false for routine fills they clearly expect.

## Limits to mention when relevant

- Flex recipe: not real time. Executions arrive 5 to 10 minutes late, and positions, cash and NAV once a day; intraday prices need the Gateway way. Accounts with more than 100 changes in one check report the latest 100.
- Gateway probes: only work while this machine is on and the Gateway is running and logged in (IB Gateway logs out once a day unless set to restart automatically). Market data needs the matching IBKR subscriptions.
