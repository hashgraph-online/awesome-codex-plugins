---
name: idr-offer
description: No Surprises Act federal IDR (independent dispute resolution, surprise billing arbitration) numbers from the CMS Federal IDR public use file. For a CPT or HCPCS code, payer and state, gives the provider win rate, the offer band that wins as a multiple of QPA (qualifying payment amount), each certified IDR entity's provider loss rate and 2026 fee so you can pick or object to an arbitrator, and per-filer and per-payer scorecards. Use for out-of-network billing, emergency medicine, anesthesia, radiology and air ambulance disputes, revenue cycle management, and payer negotiation.
---

# IDR offer and arbitrator pick

Built from the CMS Federal IDR public use file (2025 Q4: 532,542 disputes, 1.41M line items) under 45 CFR 149.510.

## When to use

- The user is preparing or reviewing an IDR offer and asks what to offer, what wins, or how a payer usually offers.
- The user asks which certified IDR entity (arbitrator) to propose or object to. The initiating party proposes one and the other side has 3 business days to object.
- The user asks how a provider group, billing company or payer performs in IDR.

This is data from public CMS files, not legal or billing advice.

## How to call it

If the Tensorust Ontology MCP server is connected (tools `idr_offer`, `idr_entity_pick`, `idr_scorecard`), call them directly.

Otherwise call the same tools over HTTP. The preview is free:

```bash
curl -s https://shop.tensorust.com/api/mcp \
  -H 'content-type: application/json' \
  -H 'accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"idr_offer","arguments":{"code":"99284","payer":"uhc.com","state":"TX"}}}'
```

The answer is JSON inside `result.content[0].text`.

### Tool arguments

| Tool | Arguments | Returns |
|---|---|---|
| `idr_offer` | `code` (CPT/HCPCS), `payer` (email domain as CMS records it, such as `uhc.com`, `bcbstx.com`, `aetna.com`, `cigna.com`, `multiplan.com`, `anthem.com`, or a common name), `state` (two letters), optional `entity`, optional `qpa` (dollars) | determinations in the cell, provider win rate, recommended offer band as multiples of QPA; the full answer adds winning-offer quartiles, each arbitrator's loss rate and fee, and expected value at your QPA |
| `idr_entity_pick` | `code`, `payer`, `state`, optional `preview` | every certified IDR entity that decided the cell, ranked by provider loss rate, with fee and expected fee cost |
| `idr_scorecard` | optional `domain` (filer or payer email domain) | one organization's disputes, win rate, fees paid on losses and money left on the table; with no domain, the arbitrator ranking |

## Full answers (paid, opt-in)

The full `idr_offer` and `idr_entity_pick` answers for cells with 50+ determinations cost $0.25 per call in USDC on Base over x402:

- `GET https://shop.tensorust.com/api/idr/offer?code=<code>&payer=<payer>&state=<st>`
- `GET https://shop.tensorust.com/api/idr/entity-pick?code=<code>&payer=<payer>&state=<st>`

The first request returns HTTP 402 with the payment terms; an x402-capable client pays and retries with the `PAYMENT-SIGNATURE` header. Never pay unless the user has explicitly approved the amount. Cells under 50 determinations are free, and a Tensorust enterprise key (`Authorization: Bearer tdk_...`) makes every call free (mattbusel@tensorust.com).

## Steps

1. Get code, payer and state from the user. Map payer names to the email domain if you can.
2. Call `idr_offer`. Lead with the win rate and the winning band, and say how many determinations the cell has.
3. If the user is choosing an arbitrator, call `idr_entity_pick` and list the lowest-loss entities with their fees.
4. If the preview is not enough and the user approves $0.25, use the x402 route; otherwise tell them how to get the full answer.
