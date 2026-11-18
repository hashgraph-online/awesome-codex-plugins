# StalkChain for Claude

Crypto research in plain English. Ask Claude to check a coin before you buy it, vet a trader before you copy them, see what the top traders are buying right now, review a wallet, or alert you when a price is crossed. It works across Solana, Ethereum, Base, BNB Chain, Monad, Hyperliquid and Robinhood Chain, plus the StonkFun launchpad.

The plugin never trades, moves funds or signs anything. The only thing it can change is your own StalkChain alerts, and only after you confirm.

## What's inside

**The StalkChain connector** (`.mcp.json`) connects Claude to StalkChain's live data: tracked traders and their real wallets, profit, positions and trades, smart-money holders, dev and insider positions, buy and sell flow, on-chain safety checks, wallet histories, DeFi yields and hacks, and StonkFun launches.

**Skills** teach Claude how to research, not just which tool to call. Each one checks the cheapest data first and answers in a consistent format. In Claude Code and Cowork you can also run them as commands, for example `/stalkchain:token-check <address>`.

| Skill | Ask something like |
| --- | --- |
| `token-check` | "Is this coin safe? Is it a honeypot? Is the dev selling?" |
| `trader-check` | "Should I copy this trader? Compare these three." |
| `trader-playbook` | "How does this trader actually trade? How long do they hold?" |
| `universal-trade-review` | "Review @trader's last week trade by trade" or "review my own trades and draft rules for next week." |
| `smart-money-radar` | "What did the top traders buy in the last hour?" |
| `whale-watch` | "Any big buys or sells over $50K today? Who are the biggest Hyperliquid whales?" |
| `perps-check` | "Is SOL funding positive on Hyperliquid, and higher than Binance? Are TSLA longs crowded?" |
| `launch-screener` | "Any new launches worth a look today?" |
| `narrative-tracker` | "What are the narratives right now?" |
| `token-compare` | "Compare these three coins side by side." |
| `rug-post-mortem` | "What happened to this coin? Was it a rug?" |
| `holder-tracker` | "Who joined or left this token's holders since yesterday?" |
| `wallet-lookup` | "What does this wallet hold, and how old is it?" |
| `portfolio-review` | "What's risky in my bags?" |
| `price-alerts` | "Email me when BONK goes above $0.00005." |
| `defi-safety` | "Where can I earn on USDC? Has this protocol been hacked?" |
| `liquidity-pools` | "Does burning a v3/v4 LP NFT lock the principal? Who controls launch liquidity and fees?" |
| `stonkfun-research` | "What's trending on StonkFun? Show this token's burns." |
| `stonkfun-launch-guide` | "Help me plan a StonkFun launch paired with an xStock." |

**Agents** handle longer jobs in Cowork and Claude Code:

| Agent | What it does |
| --- | --- |
| `crypto-researcher` | Multi-coin or multi-trader research that ends in a written report. |
| `watchlist-analyst` | Works through `watchlist.md` or `watchlist.json` in your project and writes a dated daily brief to `briefs/`. Pairs well with a scheduled task. |
| `due-diligence-reviewer` | A second opinion: re-checks a research report against fresh data and flags claims the data doesn't support. |

**Interactive cards.** In Claude and ChatGPT, token analysis and safety checks, trader reports and comparisons, multi-trader entries, the leaderboard, wallet portfolios, the live trade feed, DeFi yields and StonkFun token reports appear as interactive cards: switch a chart's timeframe or the leaderboard's window in place, or tap through to the next question. Claude adds the interpretation on top.

## Get started

1. In Claude Code, add this repository as a plugin marketplace and install StalkChain. A public listing in each app is a separate review; repository installation does not mean the plugin is approved in that app's directory:

   ```
   /plugin marketplace add StalkC/stalkchain-plugin
   /plugin install stalkchain@stalkchain
   ```
2. Connect **StalkChain** (the plugin's **Connectors** tab, or `/mcp` in Claude Code) and sign in with your StalkChain account. You'll need credits, which you can buy at [data.stalkchain.com](https://data.stalkchain.com).
3. Ask a question, for example "What are the top traders buying on Solana right now?"

### Install StalkChain in Codex

Add the StalkChain marketplace from this repository and install the plugin:

```sh
codex plugin marketplace add StalkC/stalkchain-plugin
codex plugin add stalkchain@stalkchain
```

Open the plugin in Codex and connect StalkChain Data. Sign in with your
StalkChain account before making a lookup. Lookups use account credits.

### Install an individual skill in Codex

From the project where you want to use the skill, install it with the
[Skills CLI](https://www.skills.sh/docs/cli):

```bash
npx skills add https://github.com/StalkC/stalkchain-plugin --skill trader-check --agent codex
```

Choose another name from the skills table to install a different skill. In Codex,
connect [StalkChain Data](https://data.stalkchain.com/docs/guides/getting-started)
and sign in separately. StalkChain lookups use account credits.

### Build a ChatGPT upload archive

For a manual upload in a compatible ChatGPT workspace, build an Agent Plugins
archive from a committed checkout. This includes the existing provider-neutral
manifest and MCP definition; upload/review availability depends on the workspace.

```bash
mkdir -p dist
git archive --format=zip --output=dist/stalkchain-chatgpt.zip HEAD \
  plugin.json mcp.json skills agents assets/icon.png assets/logo.png README.md LICENSE
```

Upload `dist/stalkchain-chatgpt.zip` where your workspace offers **Upload plugin
archive**. `mcp.json` keeps the remote server URL unchanged; the client discovers
OAuth sign-in from the server's protected-resource and authorization metadata.
An upload is not public directory approval. The archive-building command is a
manual maintainer step; the plugin does not run it on installation.

### Package maintenance

The distributed plugin contains Markdown, JSON, license text and PNG images.
Keep build helpers outside the package and use the PNG logo when adding a new
client manifest. This lets the remote MCP and skills be reviewed without shipping
an executable helper or an SVG asset. The catalog still performs its own safety
and policy review; a local validation pass does not guarantee directory approval.

### Hermes Agent

Plugin page: https://hermes-agent.nousresearch.com/docs/plugins/stalkchain

From the Hermes plugin catalog:

```bash
hermes plugins install stalkchain
hermes plugins enable stalkchain
```

Or directly from this repository:

```bash
hermes plugins install StalkC/stalkchain-plugin --no-enable
hermes plugins enable stalkchain
```

Then connect your StalkChain account. Hermes signs in only to MCP servers you
add yourself, so add the StalkChain server once:

```bash
hermes mcp add stalkchain --url https://data.stalkchain.com/mcp/directory --auth oauth --connect-timeout 300
```

Your browser opens the StalkChain sign-in page. Sign in with email or X and
approve access; the command waits up to five minutes. Hermes then lists the
StalkChain tools; press Enter to keep them all. The tools are available from
your next session (or after `/reload-mcp`). To sign in again later, run
`hermes mcp login stalkchain`. On a remote or headless host, use the paste-back
prompt or an SSH port forward described in the Hermes MCP docs.

In **Hermes Desktop**, open **Capabilities → Connectors**, choose **Add your
own** and enter:

| Field | Value |
| --- | --- |
| Name | `stalkchain` |
| Type | Streamable HTTP |
| URL | `https://data.stalkchain.com/mcp/directory` |
| Auth | OAuth |

Save, then choose **Authenticate** on the StalkChain card.

Keep the name `stalkchain`. Your own entry then takes the place of the server
entry in the plugin, and the plugin keeps providing the skills (find them with
`skills_list`).

**Unattended runs (cron, messaging gateway).** OAuth tokens refresh on their
own. If a refresh ever fails, Hermes parks the server instead of waiting for a
browser; run `hermes mcp login stalkchain` once to reconnect.

**What Hermes loads from this package.** `mcp.json` (the StalkChain server) and
the 19 skills under `skills/`. The `agents/` folder and the `.claude-plugin/`
files are for Claude, `.cursor-plugin/` is for Cursor, and Hermes ignores them.
There is no Python, no
executable and no self-updating code. OAuth tokens are stored by Hermes itself
(`~/.hermes/mcp-tokens/stalkchain.json`), not by this plugin.

### Cursor

**Install.** Open **Customize** in Cursor, search for **StalkChain** and choose
**Install** (project or user scope). Until it's listed in the Cursor
Marketplace, you can install it either of these ways:

- **Team marketplace** (Teams and Enterprise): **Dashboard → Plugins & MCPs →
  Team Marketplaces → Add Marketplace → Import from Repo**, and paste
  `https://github.com/StalkC/stalkchain-plugin`.
- **Locally:** clone it into Cursor's local plugin folder, then run
  **Developer: Reload Window**.

  ```bash
  git clone https://github.com/StalkC/stalkchain-plugin ~/.cursor/plugins/local/stalkchain
  ```

**Connect.** In **Customize**, find the **stalkchain** MCP server, switch it on
and choose **Connect**. Your browser opens the StalkChain sign-in page; sign in
with email or X and approve access. Then ask in Agent chat, for example "What
are the top traders buying on Solana right now?" The skills load when your
question matches; run one directly with `/token-check <address>` and the like.
The three agents are available as subagents.

**Just the connector, without the skills:** use this install link, or add the
server to `~/.cursor/mcp.json` yourself.

```text
cursor://anysphere.cursor-deeplink/mcp/install?name=stalkchain&config=eyJ1cmwiOiJodHRwczovL2RhdGEuc3RhbGtjaGFpbi5jb20vbWNwL2RpcmVjdG9yeSJ9
```

```json
{ "mcpServers": { "stalkchain": { "url": "https://data.stalkchain.com/mcp/directory" } } }
```

**What Cursor loads from this package.** `.cursor-plugin/plugin.json`, the 19
skills under `skills/`, the three agents under `agents/` and the server in
`.mcp.json`. No rules, hooks, commands or scripts.

## Data and privacy

Educational liquidity-pool questions can use the bundled read-only references without a connector call. Historical examples are not live verification; specific pool assessments require fresh evidence and may remain unknown.

When Claude uses the StalkChain connector, it sends requests to `https://data.stalkchain.com/mcp/directory`. Each call sends only the name of the tool and its inputs, such as a token address, a trader handle or a wallet address. Your conversation is never sent. Each call spends credits from your StalkChain account.

Alerts created through this plugin go to the email address on your StalkChain account. You can also list and delete existing alerts.

The plugin itself has no scripts and no hooks. The holder-tracker skill and the watchlist-analyst agent save snapshots and briefs as files in your own project, and nowhere else. Universal trade review can save append-only, trader/account-isolated review records locally at the caller-approved path; drafts never change live trading rules. Data returned describes public blockchain activity and public posts by traders. See the [privacy policy](https://data.stalkchain.com/privacy) and [terms](https://data.stalkchain.com/terms).

Nothing here is financial advice.

## Support

Questions and issues: [stalkchain.com/mcp](https://stalkchain.com/mcp), or open an issue in this repository.
