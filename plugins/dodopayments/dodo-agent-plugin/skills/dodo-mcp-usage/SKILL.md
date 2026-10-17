---
name: dodo-mcp-usage
description: How and when to use the Dodo Payments MCP servers (dodo-knowledge for docs search, dodopayments-api for the live API via Code Mode) safely. Use when looking up current Dodo payloads or event names, or inspecting or changing real products, checkouts, customers, subscriptions, webhooks or refunds.
---

# Using the Dodo Payments MCP servers

The [Dodo Payments agent plugin](https://github.com/dodopayments/dodo-agent-plugin) ships two MCP servers. They do different jobs, so pick the right one before you call anything.

**Prerequisite:** this skill is useful only when the servers are connected. Installing these skills on their own (for example with `npx skills add`) does **not** connect them. Check your tool list for the Dodo tools; if they are missing, install the agent plugin, which registers both servers, or add them by hand as described under [Authentication](#authentication). Without them, fall back to the other skills and the docs at docs.dodopayments.com.

| Server | URL | Auth | Use it for |
|--------|-----|------|------------|
| `dodo-knowledge` | `https://knowledge.dodopayments.com/mcp` | None | Semantic search over Dodo Payments docs, API reference and SDK docs |
| `dodopayments-api` | `https://mcp.dodopayments.com/mcp` | OAuth in the browser, or a local API key | Reading and changing real resources in your Dodo account |

## When to call which

### Call `dodo-knowledge` first, before writing integration code

Your memory of the Dodo API can be stale. Search the docs whenever you need:

- Request and response shapes (for example checkout session fields, subscription plan change params).
- Webhook event names and payload fields.
- SDK method names and which endpoints are deprecated.
- Base URLs (`https://test.dodopayments.com` for test mode, `https://live.dodopayments.com` for live mode).

Prefer a docs result over what you remember. If the docs and your memory disagree, the docs win. Put the framework or language in the query for sharper results, for example "Next.js webhook handler verify signature".

### Call `dodopayments-api` to act on real data

Use it when the task needs the user's actual account:

- List or create products and prices.
- Create a checkout session to test a flow end to end.
- Look up a customer, payment or subscription by ID.
- Inspect or register webhook endpoints.
- Issue a refund or cancel a subscription (only after confirmation, see Safety).

Don't use the API server to answer "how does X work" questions. That's what `dodo-knowledge` is for.

## How the API server works: Code Mode

The Dodo Payments MCP server uses **Code Mode**. Instead of one tool per endpoint, it exposes two tools:

1. **Docs search**: query the API and SDK documentation.
2. **Code execution** (`execute`): write TypeScript against the `dodopayments` SDK. It runs in an isolated sandbox with no network or filesystem access, and whatever the code returns or prints comes back as the tool result.

What this means for you:

- Look at the tool list your client exposes for the exact tool names. Don't invent per-endpoint tool names like `create_product`; they don't exist in Code Mode.
- The API key is injected server-side. You never pass a key in tool parameters, and you shouldn't try to read one from inside the sandbox.
- Batch related calls into one script and return only what you need (IDs, statuses, counts), not whole objects. One script with 20 calls beats 20 round trips.
- Search docs (either server) for the SDK method shape before writing the script, then execute.

Typical read-only flow:

1. Search docs for the method, for example "list subscriptions for a customer".
2. Run a short `execute` script that calls it and returns a trimmed summary.
3. Report the result to the user.

## Safety rules

These are non-negotiable when the API server is connected.

1. **Default to test mode.** For the local server, `DODO_PAYMENTS_ENVIRONMENT` defaults to `live_mode` when unset, so set `test_mode` explicitly during development. Use `dodo_test_` keys with test mode and `dodo_live_` keys with live mode.
2. **Know which mode you're in before any write.** With the local server, it is `DODO_PAYMENTS_ENVIRONMENT`. With the remote OAuth server the mode follows the account the user signed in to and is not visible in the tool configuration, so **always ask the user to confirm test or live mode before the first write in a session**. A read can help you check: for example, if the user gives an ID, retrieving it succeeds only in the mode it was created in.
3. **Read before write.** Retrieve the resource first, show the user what will change, then act.
4. **Confirm every live mode write with the user**, naming the exact resource ID and the effect. This is mandatory for:
   - refunds (full or partial),
   - subscription cancellations and plan changes,
   - anything that moves money or affects payouts,
   - deleting or archiving products and discounts,
   - changing or deleting webhook endpoints.
5. **Never print secrets.** Don't echo API keys, webhook signing keys, or full card or bank details into chat, logs, or files. Don't return them from `execute` scripts.
6. **Don't retry writes blindly.** If a create or refund call errors or times out, read the current state first (list refunds for the payment, fetch the subscription) before trying again, so you don't double-refund or create duplicates.
7. **Least privilege.** Dodo API keys can be created with a read-only access level. For inspection-only work with the local server, suggest a read-only key.

## Authentication

### Remote server (recommended)

The plugin points at `https://mcp.dodopayments.com/mcp`. The first time a tool is called, the client opens a browser window to sign in to Dodo Payments. Finish sign-in there, then retry the call.

Both servers speak Streamable HTTP, so clients connect to the URL directly (no bridge process). Client setup, if the user is wiring it up by hand:

- **Claude Code**: `claude mcp add --transport http dodopayments-api https://mcp.dodopayments.com/mcp`
- **Cursor and other `.mcp.json` clients**: `{"mcpServers": {"dodopayments-api": {"type": "http", "url": "https://mcp.dodopayments.com/mcp"}}}`
- **VS Code** (`.vscode/mcp.json` uses a top-level `servers` key): `{"servers": {"dodopayments-api": {"type": "http", "url": "https://mcp.dodopayments.com/mcp"}}}`
- **Codex CLI**: `codex mcp add dodopayments-api --url https://mcp.dodopayments.com/mcp`, then `codex mcp login dodopayments-api`
- **Claude.ai**: Settings, Connectors, Add Custom Connector, paste the URL.

`dodo-knowledge` is configured the same way with `https://knowledge.dodopayments.com/mcp` and needs no sign-in.

For a client that cannot dial Streamable HTTP or run MCP OAuth itself, the `mcp-remote` bridge still works as a fallback: run `npx -y mcp-remote@latest https://mcp.dodopayments.com/mcp` as a stdio server.

### Local stdio server

Run the server on the user's machine with an API key:

```json
{
  "mcpServers": {
    "dodopayments_api": {
      "command": "npx",
      "args": ["-y", "dodopayments-mcp@latest"],
      "env": {
        "DODO_PAYMENTS_API_KEY": "dodo_test_...",
        "DODO_PAYMENTS_WEBHOOK_KEY": "your_webhook_key",
        "DODO_PAYMENTS_ENVIRONMENT": "test_mode"
      }
    }
  }
}
```

| Variable | Required | Notes |
|----------|----------|-------|
| `DODO_PAYMENTS_API_KEY` | Yes | From the dashboard, Developer, API Keys |
| `DODO_PAYMENTS_WEBHOOK_KEY` | No | Webhook signing key |
| `DODO_PAYMENTS_ENVIRONMENT` | No | `test_mode` or `live_mode`; defaults to `live_mode` |

The local `execute` tool needs Deno on `PATH` (Deno 2.8 or earlier for now) and works on macOS and Linux only. On Windows, use WSL2 or the remote server. Docs search still works without Deno.

Tell the user to keep the key in their client config or environment, never in a committed file.

## Troubleshooting

**"Needs authentication" or 401 from the remote server**
The OAuth sign-in hasn't happened or has expired. Ask the user to complete the browser sign-in and retry. If it keeps failing, sign out and back in from the client's MCP menu (for example `/mcp` in Claude Code, `codex mcp login`), then restart the client. Clients that still use the older `mcp-remote` bridge cache tokens in `~/.mcp-auth`; clearing that folder forces a fresh sign-in.

**Authentication errors with the local server**
The key and environment don't match. A `dodo_test_` key needs `DODO_PAYMENTS_ENVIRONMENT=test_mode`; a `dodo_live_` key needs `live_mode`. If it still fails, have the user generate a new key in the dashboard.

**Empty lists or "not found" for an ID the user just gave you**
You're probably in the wrong mode. Test mode and live mode data are fully separate. Confirm which mode the ID came from before concluding it doesn't exist.

**`execute` errors locally but docs search works**
Deno is missing, too new, or you're on Windows. See the local server notes above.

**Tool execution failures**
Read the API error in the result; it usually names the bad field. Re-check the method shape with `dodo-knowledge`, then fix the script. You can also have the user reproduce the call with curl against `https://test.dodopayments.com` to rule out the MCP layer.

**Rate limiting (429)**
Slow down, batch work into fewer scripts, and back off before retrying. Don't loop on writes.

## Related skills

- `checkout-integration`: building checkout sessions in app code.
- `webhook-integration`: verifying and handling webhook events.
- `testing-and-go-live`: moving from test mode to live mode safely.
- `dodo-best-practices`: overall integration guidance.
