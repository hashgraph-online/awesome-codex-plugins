---
name: droplinked
description: Use the droplinked hosted MCP server to discover verified merchants and inventory, run an agent-initiated checkout (cart, quote-and-hold, payment), and read droplinked's onchain trust fabric — brand, credit-risk, and repayment attestations — as source-grounded, verification-first commerce context.
license: MIT
---

# droplinked — Verified-Inventory Agentic Commerce

droplinked is onchain agentic commerce exposed to Codex over a hosted MCP
server at `https://mcp.droplinked.com/mcp` (streamable HTTP). Reach for it when
a task needs to find real, in-stock merchandise from KYB-verified merchants,
transact on the user's behalf, or read the onchain trust state behind a brand,
a lender, or a merchant's credit history.

droplinked is **verification-first**: every discovery and product result carries
a verification block (brand-verified flag, KYB tier, EAS attestation UID/chain).
When you cite a merchant, product, or recommendation, surface that trust state —
per the droplinked model, the agent IS the verification UX.

## Access & auth (two-tier)

The server uses **per-tool, two-tier auth**:

- **Read-only tools are public — no key needed.** All the discovery, catalog,
  and trust/verify/get read tools below work with no API key set. A fresh
  install can list and call them immediately.
- **Write tools require an `X-MCP-API-Key`.** The mutating tools (checkout,
  payment, cart edits, and lending/attestation actions) return `401` without a
  valid key. The key is supplied from the `DROPLINKED_MCP_API_KEY` environment
  variable — never hardcode it. Request a write key from droplinked
  (ops@droplinked.com).

A subset of write tools (lending applications, partner referral, business-buyer
search) additionally require a two-header model: `X-MCP-API-Key` authorizes the
request to the server, and `Authorization: Bearer <agent-or-merchant-jwt>`
carries the caller's identity to backend tools guarded by AgentIdentityGuard.

## When to use droplinked

- The user wants to find or buy a real product from a verified merchant.
- The user wants an agent to run a checkout: build a cart, apply a discount,
  hold stock, and take payment.
- The user asks whether a brand/merchant is verified, or wants its trust dossier.
- A lender/underwriter agent needs a merchant's credit-risk, repayment, or
  underwriting signals, or wants to quote terms.
- A creator wants affiliate programs, or a merchant wants a WMS/3PL or lender
  recommendation.

## Tools

### Discovery
- `find_merchant` — find a merchant by slug, name, or category (MerchantCards).
- `find_inventory` — discover SKU-level inventory by query/brand, with region,
  price, in-stock, and verified-brand filters.
- `search_products` / `get_product` / `list_shop_products` — search the public
  catalog and fetch product/shop detail. Each response carries a parallel
  `verifications` / `verification` block.
- `find_affiliate_programs` — affiliate programs by vertical, commission, payout,
  and on-chain-attestation status.
- `get_feed` — URL of the droplinked product feed (verification metadata inline).

### Agent-initiated checkout
- `start_checkout` — mint a cart and get a hosted checkout URL (default) or a
  Stripe client_secret (`managed` mode).
- `cart.addLine` / `cart.updateLineQuantity` / `cart.removeLine` /
  `cart.applyDiscount` — build and edit the cart incrementally.
- `quote_inventory_available` — atomically quote price + delivery and **hold**
  stock so two agent sessions can't double-allocate the last unit.
- `process_payment` — finalize an order against a Stripe ACP payment intent
  (idempotent on the intent id).

### Trust fabric (onchain attestations)
- `verify_brand_attestation` — resolve a shop's brand attestation (EAS Schema A).
- `request_brand_attestation` / `get_brand_attestation_status` — submit and poll
  a brand attestation request.
- `get_trust_dossier` — compose brand + credit-risk + repayment into one
  envelope with a conservative `trustLevel` (UNVERIFIED → T0…T3).
- `get_trust_fabric_stats` — aggregate, no-PII platform counts.

### Credit, underwriting & lending
- `verify_credit_risk` / `verify_repayment_history` / `verify_cross_attestation`
  — read Schema B/C/D attestations for a merchant.
- `verify_lender` / `get_lender_history` / `verify_methodology` /
  `get_methodology_timeline` / `get_methodology_versions` — forensic lender and
  methodology lookups behind a credit-risk attestation.
- `get_underwriting_signals` / `get_upgrade_preview` — one-round-trip
  underwriting envelope and the aspirational tier-ladder preview.
- `recommend_lender` / `recommend_service_provider` — ranked recommendations by
  jurisdiction/archetype.
- `find_business_buyer` — search the KYB cohort grid by tier (two-header auth).
- `quote_credit_terms` / `report_repayment` — lender-side draft quote and
  repayment event (some endpoints are scaffolded; the tool degrades gracefully).
- `get_lending_application_status` / `get_document_checklist` /
  `list_lending_applications_for_merchant` / `request_partner_referral` —
  lending-application lifecycle (two-header auth for merchant-scoped reads/writes).

## Recommended workflow

1. **Discover → verify → transact.** Start with `find_merchant` / `find_inventory`
   (or `search_products`), prefer `verifiedBrand=true` results, then round-trip
   the `attestationUid` through `verify_brand_attestation` (or pull
   `get_trust_dossier`) before recommending or buying.
2. **Checkout loop.** `find_inventory` → `quote_inventory_available` (hold) →
   `start_checkout` / `cart.*` to assemble the order → `process_payment` (or hand
   back the hosted checkout URL). Surface the hold TTL and total to the user.
3. **Underwriting.** For lender/credit questions, `get_underwriting_signals` in
   one call; drill into `verify_credit_risk` / `verify_repayment_history` and the
   lender/methodology forensic chain when you need to justify a decision.

## Output discipline

- Always surface verification state (brand-verified, KYB tier, attestation UID)
  when citing a merchant, product, or recommendation.
- Treat credit tiers and trust levels as **attestation reads**, not your own
  scoring — report what the on-chain record says.
- Confirm price, quantity, and any stock hold with the user before
  `process_payment`. Prefer the smallest set of calls that answers the task.
