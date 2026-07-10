# UCP — Universal Commerce Protocol (May 2026)

UCP is a Google-led open standard, co-developed with Shopify and endorsed by
Etsy, Target, Walmart, Wayfair, plus payment partners (Stripe, Visa,
Mastercard, Adyen, Amex). Its purpose: let **AI agents discover, negotiate,
and transact with merchants without one-off integrations**.

For commerce sites, UCP sits next to **Google Merchant Center feeds** and
**Google Business Profile** as the third leg of agent-era discovery. Adoption
is early but the cost of declaring a profile is low.

**Primary source:** Google AI optimization guide references UCP; the spec
itself is co-published at developer.google.com / merchant.google.com (consult
Google for the current canonical URL — the standard is moving).

## What UCP is and isn't

| What it is | What it isn't |
|---|---|
| A capability-declaration + negotiation protocol | A new payment processor |
| Transport-agnostic (REST, MCP, A2A) | A replacement for Merchant Center feeds |
| Compatible with AP2 (Agent Payments Protocol) for cryptographic user-consent proof on autonomous purchases | A way to skip being merchant of record |
| Adopted by AI Mode in Search and Gemini today | A "ranking factor" — Google has not framed it that way |

Merchants stay **Merchant of Record** under UCP — they keep customer
relationships and post-purchase ownership.

## How to declare a UCP profile

Publish a profile at `/.well-known/ucp` describing capabilities and versions.
The general shape (consult the live spec for exact field names):

```jsonc
{
  "version": "1.0",
  "capabilities": [
    {
      "id": "dev.ucp.shopping.checkout",
      "version": "1.0",
      "endpoint": "https://api.example.com/ucp/checkout"
    },
    {
      "id": "dev.ucp.shopping.fulfillment",
      "version": "1.0",
      "endpoint": "https://api.example.com/ucp/fulfillment"
    },
    {
      "id": "dev.ucp.shopping.discount",
      "version": "1.0",
      "endpoint": "https://api.example.com/ucp/discount"
    }
  ],
  "merchant": {
    "name": "Example Co.",
    "id": "merchant-center-id-here"
  }
}
```

Platforms (AI Mode in Search, Gemini, and eventually others) auto-discover
the profile and negotiate. Google has built a reference implementation
powering direct buying from AI Mode and Gemini.

## Common capabilities to declare

| Capability ID (shape) | Purpose |
|---|---|
| `dev.ucp.shopping.checkout` | Initiate checkout, return totals + payment intent |
| `dev.ucp.shopping.fulfillment` | Quote shipping options and delivery windows |
| `dev.ucp.shopping.discount` | Apply promo codes / loyalty discounts at quote time |
| `dev.ucp.shopping.cart` | Add / remove / update items in agent-managed carts |

Exact identifiers are governed by the live spec. The pattern is
`dev.ucp.<domain>.<verb>` with semantic versioning.

## What claude-seo audits

`/seo ecommerce <url>` should report:

1. **Presence:** does `/.well-known/ucp` resolve to a valid JSON document?
2. **Capability coverage:** which capabilities are declared? Flag missing
   checkout / fulfillment / discount as opportunities, not failures (the
   protocol is early).
3. **Endpoint reachability:** are declared endpoints HTTPS, valid TLS, not
   returning 5xx?
4. **Version coherence:** does the declared protocol version match a known
   release? Flag pre-release or unrecognized versions.

The audit should **not** score the absence of UCP as a critical failure today
— adoption is early. Frame it as a forward-looking opportunity, especially
for merchants already on Google Merchant Center.

## How UCP interacts with existing surfaces

| Existing surface | Relationship to UCP |
|---|---|
| Google Merchant Center feed | Required upstream — UCP capabilities reference Merchant Center products by ID |
| Google Business Profile | Independent — UCP is product / order; GBP is store / location |
| Product schema (`hasMerchantReturnPolicy`, `shippingDetails`) | Complementary — UCP exposes the same data at the API layer; schema exposes it at the page layer |
| AP2 (Agent Payments Protocol) | Pair — UCP handles discovery + checkout structure; AP2 handles cryptographic proof of user consent |

A merchant that already has clean Merchant Center feeds, complete Product
schema, and a checkout API can declare a UCP profile in a sprint.

## Audit posture

- **Tier 1 (e-commerce sites already on Merchant Center):** recommend
  declaring a UCP profile as a forward-looking opportunity.
- **Tier 2 (DTC sites not on Merchant Center):** do not recommend UCP yet —
  Merchant Center is the prerequisite to most flows.
- **Tier 3 (informational / B2B sites):** ignore UCP entirely.

## Last verified

2026-05-18. The standard is moving fast. Re-check when:

- The canonical spec URL stabilizes (currently published on Google developer
  docs, but exact path may change).
- AP2 reaches stable release.
- Additional platforms (beyond AI Mode + Gemini) announce UCP consumption.
