<p align="center">
  <img src="assets/logo-512.png" alt="SwapWallet" width="96" height="96">
</p>

<h1 align="center">SwapWallet MCP Server</h1>

<p align="center">
  The official remote MCP server for <a href="https://swapwallet.app">SwapWallet</a>.<br>
  Let your AI assistant read your crypto balances, P&amp;L and history, and request swaps, transfers and withdrawals that run only after <b>you approve them in Telegram</b>.
</p>

<p align="center">
  <a href="https://cursor.com/install-mcp?name=swapwallet&config=eyJ1cmwiOiJodHRwczovL3N3YXB3YWxsZXQuYXBwL21jcCJ9"><img src="https://cursor.com/deeplink/mcp-install-dark.svg" alt="Add SwapWallet MCP server to Cursor" height="32"></a>
  <a href="https://vscode.dev/redirect/mcp/install?name=swapwallet&config=%7B%22type%22%3A%22http%22%2C%22url%22%3A%22https%3A%2F%2Fswapwallet.app%2Fmcp%22%7D"><img src="https://img.shields.io/badge/VS_Code-Install_Server-0098FF?style=for-the-badge&logo=visualstudiocode&logoColor=white" alt="Install in VS Code" height="32"></a>
</p>

<p align="center">
  <a href="https://glama.ai/mcp/connectors/app.swapwallet/mcp"><img src="https://glama.ai/mcp/connectors/app.swapwallet/mcp/badges/score.svg" alt="SwapWallet MCP connector on Glama"></a>
  <a href="https://registry.modelcontextprotocol.io/v0.1/servers/app.swapwallet%2Fmcp/versions/latest"><img src="https://img.shields.io/badge/MCP_Registry-app.swapwallet%2Fmcp-2563eb" alt="Official MCP Registry: app.swapwallet/mcp"></a>
  <img src="https://img.shields.io/badge/auth-OAuth_2.1-16a34a" alt="OAuth 2.1">
  <img src="https://img.shields.io/badge/transport-Streamable_HTTP-7c3aed" alt="Streamable HTTP">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-lightgrey" alt="MIT license"></a>
</p>

```
https://swapwallet.app/mcp
```

Hosted by SwapWallet: there is nothing to install or run. Add the URL to any MCP client that supports remote servers, sign in once with OAuth, and pick what the assistant may do.

## Contents

- [What you can ask](#what-you-can-ask)
- [Nothing moves without your approval](#nothing-moves-without-your-approval)
- [Tools](#tools)
- [Connect](#connect)
- [Authentication and scopes](#authentication-and-scopes)
- [For agent developers](#for-agent-developers)
- [About this repository](#about-this-repository)

## What you can ask

- "What's my total SwapWallet balance, and how much of it is USDT?"
- "Show my profit and loss on BTC and TON."
- "List my last 10 transactions from this week."
- "Give me my USDT deposit address on TRON."
- "Swap 50 USDT to TON." *(creates a request you approve in Telegram)*
- "Withdraw 2,000,000 toman to my verified bank account." *(creates a request you approve in Telegram)*

## Nothing moves without your approval

Read tools answer directly. Tools that would move money never do it themselves:

1. The assistant calls `request_swap`, `request_transfer`, `request_crypto_withdraw` or `request_fiat_withdraw`.
2. SwapWallet prices the action and sends you a preview in Telegram (the SwapWallet bot) with **Approve** and **Cancel** buttons.
3. Only when you tap Approve is the action re-priced and executed. Unanswered requests expire after 15 minutes.
4. The assistant checks the outcome with `get_action_request`.

There is no scope that lets an agent move funds without you: `withdraw:execute` exists and can never be granted. With two-factor authentication on, crypto withdrawals and transfers can't be requested over MCP at all; make those in the app.

## Tools

| Tool | What it does | Scope | Annotations |
|---|---|---|---|
| `get_total_balance` | Total portfolio value plus a per-token breakdown | `wallet:read` | read-only |
| `get_balance` | Balance and value of the given tokens | `wallet:read` | read-only |
| `get_user_info` | Profile, verification level, limits and settings | `wallet:read` | read-only |
| `get_deposit_address` | Deposit address for a token on a network (created if needed) | `wallet:read` | idempotent |
| `get_profit_and_loss` | Realized and unrealized P&L, all assets or chosen tokens | `portfolio:read` | read-only |
| `get_transactions` | Deposits, withdrawals, transfers and trades, newest first, with filters | `transactions:read` | read-only |
| `get_contacts` | Saved SwapWallet contacts, 10 per page | `contacts:read` | read-only |
| `get_ibans` | Verified bank accounts (IBANs) for toman withdrawals | `contacts:read` | read-only |
| `get_action_request` | Status of a request: `PENDING`, `EXECUTED`, `REJECTED`, `EXPIRED` or `FAILED` | any | read-only |
| `request_swap` | Prices a swap between two tokens and asks for approval | `swap:request` | needs approval |
| `request_transfer` | Transfer to one of your saved SwapWallet contacts | `transfer:request` | needs approval |
| `request_crypto_withdraw` | Crypto withdrawal to an external address | `withdraw:request` | needs approval, open world |
| `request_fiat_withdraw` | Toman (IRT) withdrawal to a verified IBAN | `withdraw:request` | needs approval, open world |

Every tool ships MCP annotations (`readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`). No tool is destructive: a `request_*` tool only adds a request that you approve or cancel. The full definitions, with input schemas, are in the server card at [`/.well-known/mcp/server-card.json`](https://swapwallet.app/.well-known/mcp/server-card.json).

## Connect

<details open>
<summary><b>Claude</b> (claude.ai, desktop)</summary>

Settings → Connectors → **Add custom connector** → URL `https://swapwallet.app/mcp`.
</details>

<details>
<summary><b>Claude Code</b></summary>

```bash
claude mcp add --transport http swapwallet https://swapwallet.app/mcp
```

Or install it as a plugin from this repository:

```
/plugin marketplace add SwapWallet/swapwallet-mcp
/plugin install swapwallet@swapwallet
```
</details>

<details>
<summary><b>Cursor</b></summary>

Use the **Add to Cursor** button above, or add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "swapwallet": { "url": "https://swapwallet.app/mcp" }
  }
}
```
</details>

<details>
<summary><b>VS Code</b> (GitHub Copilot)</summary>

Use the **Install in VS Code** button above, or run:

```bash
code --add-mcp '{"name":"swapwallet","type":"http","url":"https://swapwallet.app/mcp"}'
```
</details>

<details>
<summary><b>Windsurf</b></summary>

Add to `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "swapwallet": { "serverUrl": "https://swapwallet.app/mcp" }
  }
}
```
</details>

<details>
<summary><b>Gemini CLI</b></summary>

```bash
gemini mcp add --transport http swapwallet https://swapwallet.app/mcp
```

Or as an extension, which also loads the agent rules in [`GEMINI.md`](GEMINI.md):

```bash
gemini extensions install https://github.com/SwapWallet/swapwallet-mcp
```
</details>

<details>
<summary><b>Codex CLI</b></summary>

```bash
codex mcp add swapwallet --url https://swapwallet.app/mcp
```
</details>

<details>
<summary><b>Any other client</b></summary>

Add `https://swapwallet.app/mcp` as a remote **Streamable HTTP** server. The client discovers OAuth on its own from the `401` response.
</details>

## Authentication and scopes

OAuth 2.1 with dynamic client registration (RFC 7591) and PKCE (S256); public clients, no secret, no API keys. You sign in on SwapWallet's consent page with your phone number and an SMS code, review the scopes, untick any you don't want, and approve. Revoke access any time from the app.

| Scope | Grants |
|---|---|
| `wallet:read` | balances, account info, deposit addresses |
| `portfolio:read` | profit and loss |
| `transactions:read` | transaction history |
| `contacts:read` | saved contacts and verified IBANs |
| `swap:request` | request swaps (you approve in Telegram) |
| `transfer:request` | request transfers to saved contacts (you approve in Telegram) |
| `withdraw:request` | request crypto and toman withdrawals (you approve in Telegram) |

`tools/list` returns only the tools your granted scopes allow, and scopes are checked again on every call. Access tokens last 1 hour; refresh tokens last until you revoke the grant.

**Requirements:** a SwapWallet account (sign up at [swapwallet.app](https://swapwallet.app) with a phone number; trading and withdrawals need identity verification), and a linked Telegram account for the `request_*` tools.

## For agent developers

- Endpoint `https://swapwallet.app/mcp`: Streamable HTTP, JSON responses only, stateless (no session, no SSE, no batches). Protocol versions `2025-06-18`, `2025-03-26` and `2024-11-05`.
- Discovery: `/.well-known/oauth-protected-resource`, `/.well-known/oauth-authorization-server`, and the [server card](https://swapwallet.app/.well-known/mcp/server-card.json).
- Amounts are decimal strings; `token` and `network` are enums listed in each tool's input schema.
- Never report a swap, transfer or withdrawal as done until `get_action_request` says `EXECUTED`. `PENDING` means "waiting for the user in Telegram". The full rules are in [`skills/swapwallet/SKILL.md`](skills/swapwallet/SKILL.md).

Full reference: **[swapwallet.app/docs/mcp](https://swapwallet.app/docs/mcp)** · REST API: [docs.swapwallet.app](https://docs.swapwallet.app)

## About this repository

The server runs inside SwapWallet's backend; this repository holds its public description and client configs, so you can install it from tools that work with repositories:

| File | For |
|---|---|
| [`server.json`](server.json) | Official MCP Registry entry (`app.swapwallet/mcp`) |
| [`.mcp.json`](.mcp.json) | Claude Code and other clients that read a project MCP config |
| [`llms-install.md`](llms-install.md) | Step-by-step setup for agents that install servers themselves (Cline) |
| [`.claude-plugin/`](.claude-plugin) | Claude Code plugin and marketplace |
| [`.codex-plugin/`](.codex-plugin) | Codex plugin (same MCP server and skill) |
| [`skills/swapwallet/`](skills/swapwallet/SKILL.md) | Claude skill: how an agent should use the tools safely (ships with the plugin) |
| [`gemini-extension.json`](gemini-extension.json), [`GEMINI.md`](GEMINI.md) | Gemini CLI extension and its context file |
| [`SECURITY.md`](SECURITY.md) | How to report a vulnerability |

Found an issue with the docs or a client config? Open an issue or a pull request.

## About SwapWallet

[SwapWallet](https://swapwallet.app) (سواپ‌ولت) is an Iranian crypto exchange with a wallet-style app: buy, sell, swap, hold and send crypto, and deposit and withdraw toman. It is custodial, and is operated by Zanjireh Tabdil Soba. Web app, Android apps and a [Telegram mini app](https://t.me/swapwalletbot/app).

- Support: support@swapwallet.app · [live chat](https://swapwallet.app/contact)
- [Privacy policy](https://swapwallet.app/privacy) · [Terms of service](https://swapwallet.app/terms) · [Fees](https://swapwallet.app/fee)

## Security

Please report vulnerabilities in the MCP server or the OAuth flow privately, as described in the [security policy](https://swapwallet.app/security) ([security.txt](https://swapwallet.app/.well-known/security.txt)), not in a public issue.

## License

The contents of this repository are released under the [MIT license](LICENSE).
