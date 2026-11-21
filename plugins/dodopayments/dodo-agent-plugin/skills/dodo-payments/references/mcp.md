# The `dodopayments` MCP server

## Contents

- [Tools](#tools)
- [Workflow](#workflow)
- [How `execute` works](#how-execute-works)
- [Safety](#safety)
- [Sign-in](#sign-in)
- [Connect a client by hand](#connect-a-client-by-hand)
- [Troubleshooting](#troubleshooting)

One server, `dodopayments`, at `https://mcp.dodopayments.com/mcp` (Streamable HTTP). The Dodo Payments agent plugin registers it. Installing only this skill does not connect it: check the tool list, and if the tools are missing, connect the server by hand (below) or fall back to `docs.dodopayments.com`.

## Tools

| Tool | Does |
|---|---|
| `search_docs` | Searches guides and docs pages; returns short ranked results with links |
| `read_docs_page` | Returns one docs page as Markdown |
| `search` | Searches the SDK and API reference: method names, parameters, response fields, webhook payloads |
| `execute` | Runs a TypeScript script against the `dodopayments` SDK on the user's account |
| `feedback` | Sends a note about docs or tool results that were wrong, missing or confusing. The Dodo Payments team reads and triages each one |

Every tool needs sign-in. A client that cannot do OAuth can connect to `https://mcp.dodopayments.com/mcp?auth=optional` instead: the docs tools and `search` then work without an account, and `execute` and `feedback` return 401.

## Workflow

1. **Before writing integration code, call `search_docs`** with the framework in the query ("Next.js verify webhook signature"). Read the best hit with `read_docs_page` when the snippet is not enough. Docs win over memory.
2. **Before `execute`, call `search`** for each SDK method the script uses, so names and fields are real.
3. **Use `execute` only for account actions**: list products, look up a payment or subscription, create a test checkout session, register a webhook endpoint. Do not use it to answer "how does X work".
4. **Call `feedback`** when docs were wrong or missing something you needed. Do not include API keys, tokens, emails or customer data.

## How `execute` works

`execute` runs your script in an isolated sandbox with an authenticated `dodopayments` client. There is no network or filesystem access; what the script returns or prints is the tool result.

- Batch related calls into one script, and return only the fields you need (IDs, statuses, counts).
- The server authenticates every call with the user's sign-in. Never pass or print an API key or token.
- There are no per-endpoint tools such as `create_product`.

## Safety

1. **Ask which mode the session uses before the first write.** The mode (test or live) is chosen on the consent page and is not visible in the tool list. During development, suggest test mode.
2. **Read before write.** Fetch the resource, show the user what will change, then act.
3. **Confirm every live-mode write** with the exact resource ID and effect: refunds, cancellations, plan changes, charges, anything that moves money, deleting or archiving products and discounts, and changing webhook endpoints.
4. **Never return secrets** (API keys, tokens, webhook secrets, card or bank details) from a script.
5. **Do not retry writes blindly.** After an error or timeout, read the current state (list the payment's refunds, fetch the subscription) before trying again.
6. **Least privilege.** For read-only work, suggest granting read permissions only on the consent page.

## Sign-in

The server returns 401 until the client signs in, so the client opens a Dodo Payments consent page when the server is added (or when the user runs the sign-in command). The user signs in, picks the business, the mode and the permissions, and the client retries. The client stores the token. Review or revoke access in the dashboard under **Settings > Connected Apps**. To switch business or mode, sign out of the server in the client and sign in again.

Client sign-in commands: `/mcp` in Claude Code, `codex mcp login dodopayments`, `opencode mcp auth dodopayments`.

## Connect a client by hand

| Client | Configuration |
|---|---|
| Claude Code | `claude mcp add --transport http dodopayments https://mcp.dodopayments.com/mcp` |
| Cursor (`.cursor/mcp.json`) | `{"mcpServers": {"dodopayments": {"url": "https://mcp.dodopayments.com/mcp"}}}` |
| Other `.mcp.json` clients | `{"mcpServers": {"dodopayments": {"type": "http", "url": "https://mcp.dodopayments.com/mcp"}}}` |
| VS Code (`.vscode/mcp.json`) | `{"servers": {"dodopayments": {"type": "http", "url": "https://mcp.dodopayments.com/mcp"}}}` |
| Codex CLI | `codex mcp add dodopayments --url https://mcp.dodopayments.com/mcp` |
| OpenCode (`opencode.json`) | `{"mcp": {"dodopayments": {"type": "remote", "url": "https://mcp.dodopayments.com/mcp"}}}` |
| Claude.ai | Settings > Connectors > Add custom connector, then the URL |

A client that cannot speak Streamable HTTP or MCP OAuth can run `npx -y mcp-remote@latest https://mcp.dodopayments.com/mcp` as a stdio server.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| 401, "needs authentication", or the server shows as not connected | Not signed in, expired, or revoked. Run the client's sign-in command and retry. `mcp-remote` caches tokens in `~/.mcp-auth`; delete it to force a new sign-in |
| 403 on one call while others work | The granted permissions do not cover it. Sign out, sign in again and grant the missing permission |
| Empty list or "not found" for an ID the user gave | Wrong mode. Test and live data are separate; check which mode the ID came from |
| A script fails | Read the API error, which usually names the field. Check the method with `search`, fix the script |
| 429 | Slow down and batch work into fewer scripts. Never loop on writes |
