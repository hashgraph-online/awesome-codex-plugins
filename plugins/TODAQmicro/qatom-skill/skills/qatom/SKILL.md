---
name: qatom
description: "Use and publish Qatom marketplace tools. Use when: calling paywalled API tools from the Qatom marketplace, checking wallet balance, managing your agent twin wallet, or helping a user register as a Qatom provider to earn per-call payments from their own tools. Connects to the hosted Qatom MCP server at mcp.m.todaq.net via Qatom OIDC. NOT for: direct payment API calls or free tools."
homepage: https://github.com/todaqmicro/qatom-skill
license: MIT
mcp:
  qatom:
    type: "http"
    url: "https://mcp.m.todaq.net/mcp"
    oauth:
      clientId: "mcp.m.todaq.net"
      scopes: ["openid", "profile", "email", "twin"]
metadata:
  {
    "openclaw":
      {
        "emoji": "💎"
      }
  }
---

# Qatom Marketplace Skill

Access paywalled API tools from the Qatom marketplace. An agent (sandbox) twin wallet handles payments transparently, so no manual approval steps interrupt your workflow. Providers can register their own APIs and earn per-call revenue automatically.

## When to Use

✅ **USE this skill when:**
- User asks to call a tool from the Qatom marketplace
- A tool requires Qatom wallet payment
- Checking wallet balance or twin info
- Managing your agent (sandbox) twin wallet, funding, or transfers
- Registering as a Qatom provider to earn per-call revenue from your tools
- Managing provider twins, configuring upstream APIs, or updating registered tools

❌ **DON'T use this skill when:**
- User wants to interact with the payment API directly
- Tool is free and doesn't require a wallet

## Connecting

The Qatom MCP server is hosted at `https://mcp.m.todaq.net`. Connect using any MCP-compatible client with OAuth 2.0 support.

**claude.ai (built-in OAuth):**
Add `https://mcp.m.todaq.net` as a remote MCP server. The platform handles OAuth redirect and token management automatically.

**Claude Desktop:**
Add the server to your `claude_desktop_config.json` with OAuth configuration. The desktop client will open your browser for the Qatom OIDC login flow and store the resulting token.

**Other MCP clients:**
Connect to `https://mcp.m.todaq.net` using standard OAuth 2.0. The authorization server is at `https://pay.m.todaq.net`. Request the `twin` scope to receive agent twin credentials alongside your access token.

After connecting, all available Qatom tools appear in the client's tool list automatically.

## Auth Flow

1. **OAuth redirect** — MCP client redirects to Qatom OIDC login at `pay.m.todaq.net`
2. **User authenticates** — email + 2FA (TOTP) via the Qatom Flutter app or web
3. **Twin auto-provisioning** — OIDC returns user identity including `twin_hostname` and `agent_twin_hostname` + `agent_twin_key`. The agent twin is a sandbox wallet auto-provisioned for MCP use. If no agent twin exists, one is created during the first connection.
4. **Token introspection** — every tool call validates the Bearer token against the OIDC introspection endpoint (result cached for 60 seconds)
5. **Session persistence** — tokens stored by the MCP client persist across tool calls and sessions, so re-auth is rare
6. **MFA skipped for Bearer** — agent-initiated calls use a Bearer token (service-to-service). The paywall skips MFA entirely for Bearer calls, so payments execute immediately without manual approval

## Available Tools

### Wallet Tools

These 4 tools are always available and manage your TODAQ wallet:

| Tool | Description |
|------|-------------|
| `agent_wallet_info` | Get your TODAQ twin hostname and current USD TDN balances. No input required — uses your authenticated session. |
| `check_wallet_balance` | Get all your TODAQ twins and their current USD TDN balances. No input required — uses your authenticated session. |
| `fund_agent_wallet` | Get the URL to add funds to your primary wallet via the web UI. Only use this when the primary wallet has insufficient balance to transfer to the agent wallet. After adding funds, use transfer_to_agent_wallet to move them to the agent wallet. The chargeup URL is `https://load.m.todaq.net`. |
| `transfer_to_agent_wallet` | Transfer USD TDN balance from your primary wallet to your agent (sandbox) wallet. Only call this when explicitly requested by the user. |

### Dynamic Tools

Additional tools appear dynamically from the marketplace catalog, fetched from the payment API at connection time (cached for 60 seconds). The agent sees them alongside the static wallet tools in its tool list. Tool names use snake_case (e.g., "Current Weather" registers as `current_weather`).

### Provider Admin Tools

These 8 tools let you create and manage provider twins, register API tools in the marketplace, and earn per-call revenue:

| Tool | Description |
|------|-------------|
| `twin_status` | Get the status and balances of your provider twins used for receiving payments. Use this to check if you have a provider twin and what its hostname is. |
| `create_twin` | Create a new provider twin to receive payments for your APIs. Providers can have multiple twins. |
| `configure_twin` | Link your provider twin to the real upstream API it will proxy to, and set your price per call. |
| `register_tool` | Register a new API tool in the marketplace. Run configure_twin first to set up your provider twin, then provide the tool details here. The service URL is derived automatically from your twin hostname. |
| `list_my_tools` | List all dynamic tools you have registered in the marketplace. |
| `update_tool` | Update an existing dynamic tool in the marketplace. |
| `deactivate_tool` | Deactivate a tool from the marketplace. It will be hidden from consumers immediately (note: MCP agent discovery catalogs cache for 60 seconds). |
| `test_tool` | Test a dynamic tool you created by executing it through the paywall exactly as a consumer would. Note: Your agent sandbox twin will pay your provider twin for this test call. |

## Payment Flow

When an agent calls a marketplace tool, the MCP server orchestrates payment transparently:

1. **Token validation** — MCP server validates the Bearer token via OIDC introspection. Identifies the user's agent twin for payment.
2. **Bearer skips MFA** — Bearer token calls bypass MFA entirely. Payment executes immediately.
3. **Paywall request** — MCP server POSTs to `/v4/paywall` on the payment API with:
   - `amount` — the tool's price in USD TDN
   - `serviceUrl` — the upstream API URL
   - `serviceMethod` — `GET`, `POST`, or `PUT`
   - `additionalParams` — tool arguments, present only for `POST`/`PUT` tools
4. **GET tools** — arguments are injected as query string parameters on `serviceUrl`. No `additionalParams` field in the paywall body.
5. **POST/PUT tools** — arguments are packed into the `additionalParams` field and forwarded as the request body to the upstream API.
6. **TODA protocol payment** — the payment API calls the agent twin node directly. The agent twin transfers the tool's price to the provider twin via the TODA protocol.
7. **Upstream proxy** — the provider twin proxies the request to the upstream service URL. The response flows back through the provider twin → payment API → MCP server → agent.
8. **Response delivered** — the agent receives the upstream API response as the tool call result.

## Agent Twin Wallet

Every MCP-authenticated user gets an agent (sandbox) twin, separate from their primary human wallet. This twin is auto-provisioned during the first OAuth connection and is used exclusively for agent-initiated marketplace payments.

### Primary vs Sandbox Twin

| | Primary Twin | Agent (Sandbox) Twin |
|---|---|---|
| **Purpose** | Your main wallet, controlled via the Qatom Flutter app | Dedicated wallet for agent marketplace spending |
| **Provisioning** | Created when you register your Qatom account | Auto-provisioned on first MCP connection |
| **Key** | `twin_hostname` + `twin_key` | `agent_twin_hostname` + `agent_twin_key` |
| **Control** | Human-managed (Flutter app, web UI) | Agent-managed (MCP tool calls only) |
| **Spending** | Manual, MFA-gated | Automatic, no MFA (Bearer token flow) |

### Fund → Transfer → Spend Lifecycle

```
1. FUND       Primary wallet gets TDN
                → Use fund_agent_wallet to get the chargeup URL (https://load.m.todaq.net)
                → Add funds through the web UI
                ↓
2. TRANSFER   Move TDN from primary to agent sandbox wallet
                → Use transfer_to_agent_wallet with amount and dq_type
                → Only do this when the agent wallet balance is too low
                ↓
3. SPEND      Agent calls marketplace tools
                → Each call deducts the tool's price from the agent sandbox twin
                → Payment goes to the provider twin automatically
```

### Edge Cases

- **Pre-existing sessions** — sessions created before agent twin auto-provisioning may have `agentTwinHostname` as `undefined`. The MCP server falls back to the primary `twinHostname` in this case. On the next tool call, the token is re-validated and the agent twin claims are restored automatically.
- **Token expiry** — OAuth tokens expire after a set duration. When this happens, the MCP client re-authenticates and agent twin claims are refreshed. Wallet balances and twin hostnames remain stable across token refreshes.
- **Insufficient sandbox balance** — if the agent twin lacks funds for a tool call, the paywall returns an error. The agent should tell the user to add funds and use `transfer_to_agent_wallet` before retrying.

## Become a Qatom Provider

Register your own API endpoints as marketplace tools and earn per-call revenue. Payments flow via TODA protocol from consumer agent twins to your provider twin, with no manual invoicing or settlement.

Just tell your agent: **"Help me register as a Qatom provider."** The agent will walk you through these steps using the provider admin tools:

### Step 1 — Create a Provider Twin

The agent calls `create_twin`, which provisions a new provider twin to receive payments. Providers can have multiple twins, each linked to a different upstream API or pricing tier. The twin hostname is returned and used in the next steps.

### Step 2 — Configure the Twin

The agent calls `configure_twin` with three parameters:
- **hostname** — your provider twin hostname (from step 1 or `twin_status`)
- **target_url** — the real upstream API URL (must use `https`)
- **price_per_call** — minimum USD TDN charged per call

This links your provider twin to the upstream API it will proxy traffic to.

### Step 3 — Register the Tool

The agent calls `register_tool` to list your API in the marketplace. Required parameters:
- **twin_hostname** — your provider twin hostname
- **name** — tool name in snake_case (e.g., `get_weather_current`)
- **description** — what the tool does, shown to AI agents during discovery
- **provider** — your display name shown in the marketplace
- **price_per_call** — price per call in USD TDN (should match `configure_twin`)
- **service_method** — `GET`, `POST`, or `PUT` (the HTTP method your upstream API expects)
- **input_schema** — JSON Schema object describing the parameters consumers must pass

The service URL is derived automatically from your twin hostname.

### Step 4 — Test Your Tool

The agent calls `test_tool` with your tool's ID and sample arguments. This executes the tool through the full paywall exactly as a consumer would experience it. Your agent sandbox twin pays your provider twin for this test call, so you can verify the end-to-end flow including payment.

After testing, your tool is live in the marketplace. Any authenticated MCP agent can discover and call it. The catalog refreshes every 60 seconds, so new tools are visible almost immediately.

### Managing Your Tools

Once registered, you can use the provider admin tools to manage your marketplace presence:
- `list_my_tools` — see all your registered tools with their IDs
- `update_tool` — change name, description, price, or toggle active/inactive
- `deactivate_tool` — hide a tool from consumers (visible in the catalog within 60 seconds)
- `twin_status` — check provider twin balances (the TDN you've earned from tool calls)
