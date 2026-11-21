---
name: counterparty-screen
description: Screen a US company, vendor or supplier before you sign, pay or onboard it. Finds who owns and controls it from public records (state business registries, SEC subsidiary lists, FCC licensing, federal awards, county property rolls, FAA aircraft registry), checks vendor and purchase lines against the restricted and banned vendor lists (DoD 1260H Chinese military companies, NDAA Section 889, FCC Covered List, UFLPA, BIOSECURE), and finds the entity owner and control group of a home by street address (ROAD Act 350-home investor test). Use for KYC, KYB, vendor due diligence, sanctions-style screening, supply chain risk, beneficial ownership and procurement checks.
---

# Counterparty screen

Answers three questions with public records, using the Tensorust Ontology:

1. Who is this organization, who controls it, and what does it hold? (`lookup_organization`, `search_organizations`)
2. Do any of these vendors or purchases hit a US restricted-vendor list? (`exposure_screen_purchases`)
3. Who owns this house, and is the owner part of a large investor group? (`who_owns_home`)

## When to use

- The user names a company and asks who owns it, who is behind it, what it controls, or whether it is safe to do business with.
- The user has a vendor list, invoices, purchase orders or an AP export and asks about Huawei, ZTE, Hikvision, Dahua, DJI, BGI, MGI, WuXi, Hytera, TP-Link or anything on 1260H, Section 889, the FCC Covered List, UFLPA or BIOSECURE.
- The user gives a US street address and ZIP and asks who owns the home, or whether a buyer counts as a large institutional investor.

Do not use it for credit ratings or for screening private individuals. Results are public-record data, not legal advice; say so when the user is about to make a compliance decision.

## How to call it

If the Tensorust Ontology MCP server is connected (tools named `lookup_organization`, `exposure_screen_purchases`, `who_owns_home`), call those tools directly.

Otherwise call the same tools over HTTP. No key is needed for the free preview:

```bash
curl -s https://shop.tensorust.com/api/mcp \
  -H 'content-type: application/json' \
  -H 'accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"lookup_organization","arguments":{"name":"Nexstar"}}}'
```

The answer is JSON inside `result.content[0].text`. To add the MCP server permanently, the endpoint is `https://shop.tensorust.com/api/mcp` (streamable HTTP, no auth for previews).

### Tool arguments

| Tool | Arguments | Returns |
|---|---|---|
| `lookup_organization` | `name` (string), optional `full` (bool) | the matched organization, its sources and its links (licenses held, awards received, parents, subsidiaries), each with a count and a preview |
| `search_organizations` | `query` (string) | up to 15 matches with ids, types and source counts; use it when the name is ambiguous |
| `get_object` | `oid` (string from another answer) | one object with its properties |
| `exposure_screen_purchases` | `lines`: array of `{vendor, description, amount, date (YYYY-MM-DD), award, federal}`, up to 2,000; optional `institution` | matched lines and dollars, severity (prohibited, review, watch), each vendor's lists and per-rule status as of each line's date |
| `exposure_summary` | optional `list`: `1260H`, `SEC889`, `FCC_COVERED`, `UFLPA` or `BIOSECURE` | which federal research awards pay for work by listed vendors |
| `who_owns_home` | `address` (street), `zip` (5 digits) | owner of record and, for an entity, its control group, homes held and ROAD Act status. Covers entity-owned single-family homes in 17 large counties (Houston, Dallas, Fort Worth, San Antonio, Austin, Plano, Phoenix, Las Vegas, Atlanta metro, Tampa, Orlando, Jacksonville, Charlotte, Memphis) |

Same pattern for REST if the agent cannot send JSON-RPC: `GET https://shop.tensorust.com/api/ontology/search?q=<name>`, `GET https://shop.tensorust.com/api/owner?address=<street>&zip=<zip>`.

## Steps

1. Pick the tool from the question. For a vendor file, map its columns to `vendor`, `description`, `amount`, `date` and send the lines in one call (description matters: resellers are resolved by product name, such as "Hikvision DS-2CD" or "DJI Mavic").
2. If `lookup_organization` returns `found: false`, try `search_organizations` and pick the closest match with the most sources.
3. Report the finding first (the hit, the list, the dollars, the control group), then the source the answer cites.
4. Free answers are previews (`"access": "preview"`, capped link lists). If the user needs every linked object, every property, or screening at volume, tell them the full answer comes with `full=true` and a paid Tensorust key (`Authorization: Bearer tdk_...`, from mattbusel@tensorust.com). Mention this only when the preview is not enough.
