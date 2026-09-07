# droplinked Codex Plugin

A Codex plugin that wraps [droplinked](https://droplinked.com)'s hosted MCP
server — **onchain agentic commerce**. Install it to give Codex verified-
inventory discovery, agent-initiated checkout, and droplinked's onchain **trust
fabric**: EAS-backed brand, credit-risk, and repayment attestations, all as
source-grounded, verification-first commerce context.

droplinked is **verification-first**: every discovery and product result carries
a verification block (brand-verified flag, KYB tier, EAS attestation UID/chain).
When the agent cites a merchant or product, it surfaces that trust state — the
agent is the verification UX.

## What droplinked is

droplinked is onchain agentic commerce: KYB-verified merchants list real,
in-stock inventory; agents discover it, transact on the user's behalf, and read
an onchain trust fabric that backs brands, lenders, and merchant credit history
with [EAS](https://attest.org) attestations. This plugin exposes that surface to
Codex over a single remote MCP endpoint.

## What the MCP server exposes

- **Discovery** — verified merchants and SKU-level inventory, catalog search,
  product/shop detail, affiliate programs, and the product feed
  (`find_merchant`, `find_inventory`, `search_products`, `get_product`,
  `list_shop_products`, `find_affiliate_programs`, `get_feed`).
- **Agent-initiated checkout** — mint and edit a cart, apply a discount, quote
  and **hold** stock, and finalize payment (`start_checkout`, `cart.addLine`,
  `cart.updateLineQuantity`, `cart.removeLine`, `cart.applyDiscount`,
  `quote_inventory_available`, `process_payment`).
- **Trust fabric** — brand attestations and a composed merchant trust dossier
  (`verify_brand_attestation`, `request_brand_attestation`,
  `get_brand_attestation_status`, `get_trust_dossier`, `get_trust_fabric_stats`).
- **Credit, underwriting & lending** — credit-risk / repayment / cross
  attestations, lender and methodology forensics, underwriting signals, and the
  lending-application lifecycle (`verify_credit_risk`, `verify_repayment_history`,
  `get_underwriting_signals`, `recommend_lender`, `quote_credit_terms`,
  `get_lending_application_status`, and more).

## Add it to Codex

This plugin connects to droplinked's hosted MCP server over **streamable HTTP**
with a **two-tier auth model**, and no credentials are bundled in this repo:

- **Read-only tools are public — no key required.** Discovery, catalog, and
  trust-read tools (`find_merchant`, `find_inventory`, `search_products`,
  `get_product`, `list_shop_products`, `find_affiliate_programs`, `get_feed`,
  `verify_brand_attestation`, `get_trust_dossier`, `get_trust_fabric_stats`,
  `verify_credit_risk`, `get_underwriting_signals`, and the other verify/get
  reads) work out of the box, even with no API key set.
- **Write tools require an `X-MCP-API-Key`.** Checkout, payment, cart edits, and
  lending/attestation actions (`start_checkout`, `process_payment`, `cart.*`,
  `quote_inventory_available`, `request_brand_attestation`, `quote_credit_terms`,
  `report_repayment`, `request_partner_referral`) return `401 unauthorized`
  without a valid key.

The server is configured in [`.mcp.json`](./.mcp.json):

```json
{
  "mcpServers": {
    "droplinked": {
      "type": "http",
      "url": "https://mcp.droplinked.com/mcp",
      "headers": {
        "X-MCP-API-Key": "${DROPLINKED_MCP_API_KEY}"
      }
    }
  }
}
```

The `${DROPLINKED_MCP_API_KEY}` placeholder is resolved from your environment at
connect time. It is **optional**: if the variable is unset, the empty header is
ignored and all read-only tools still work — it only unlocks the write tools.
**Never commit a real key.**

### Add a key to unlock write tools (optional)

Read-only tools need no setup. To enable the write tools (checkout, payment,
cart edits, lending/attestation actions), **request an MCP API key from
droplinked** (email [ops@droplinked.com](mailto:ops@droplinked.com); see the
[MCP server docs](https://docs.droplinked.com/agentic/mcp-server)), then expose
it to Codex as an environment variable before connecting:

```bash
export DROPLINKED_MCP_API_KEY="your-droplinked-mcp-api-key"
```

Some tools (lending-application reads/writes, partner referral, business-buyer
search) additionally use a two-header identity model: `X-MCP-API-Key` authorizes
the request to the server, and `Authorization: Bearer <agent-or-merchant-jwt>`
carries the caller's identity to backend tools guarded by AgentIdentityGuard.

Install this repo as a Codex plugin (via the HOL registry or by pointing a
marketplace source at this repository), and the `droplinked` MCP server plus the
bundled [`droplinked` skill](./skills/droplinked/SKILL.md) become available to
your agent.

## Example prompts

- "Find a verified droplinked merchant in this category and search their
  inventory for an in-stock item, preferring brand-verified results."
- "Start a droplinked checkout for this SKU: build the cart, quote and hold the
  stock, then hand me the hosted checkout URL."
- "Pull the droplinked trust dossier for this merchant — brand attestation,
  credit-risk tier, and repayment history — and summarize the trust state before
  I proceed."

## Contents

```
.codex-plugin/plugin.json        # plugin manifest
.mcp.json                        # remote MCP server (streamable HTTP) configuration
skills/droplinked/SKILL.md       # skill teaching agents how/when to use droplinked
assets/icon.png                  # composer icon (512x512)
assets/logo.svg                  # droplinked mark
assets/screenshot-droplinked.png # preview card
SECURITY.md                      # vulnerability disclosure policy
LICENSE                          # MIT
```

## Security

See [`SECURITY.md`](./SECURITY.md). Report vulnerabilities privately to
[support@droplinked.com](mailto:support@droplinked.com). This repo ships **no
executable code and no bundled credentials** — the API key is supplied from your
environment at runtime.

## Links

- Website: [https://droplinked.com](https://droplinked.com)
- MCP server docs: [https://docs.droplinked.com/agentic/mcp-server](https://docs.droplinked.com/agentic/mcp-server)
- MCP endpoint: `https://mcp.droplinked.com/mcp`
- MCP discovery doc: [`https://mcp.droplinked.com/.well-known/mcp.json`](https://mcp.droplinked.com/.well-known/mcp.json)

## License

[MIT](./LICENSE) © 2026 droplinked
