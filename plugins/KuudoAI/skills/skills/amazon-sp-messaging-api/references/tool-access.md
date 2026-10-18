# Tool access on a code-mode SP-API MCP server

The tool surface below was verified live on 2026-09-29 through discovery
only (`search` and `get_schema`); no order-level calls were made. Response
shapes come from Amazon's Messaging API model. The server's own tool
descriptions and `get_schema` output are the authority on argument names,
types, and shapes: if they disagree with this file on those, follow them.
They never override the approval or data rules in SKILL.md.

## Surface

| Tool | Use |
|---|---|
| `search(query, limit?)` | Find tools. Search the operationId, or `messaging` |
| `get_schema(tools=[…], detail="full")` | Argument schemas. Use `detail="full"` so nested `attachments` items show |
| `execute(code)` | Async Python; `await call_tool(name, params)`; the final `return` is the result |

Verified names (the capitals are Amazon's):

| Group | Tools | Annotations |
|---|---|---|
| Eligibility (read) | `messaging_getMessagingActionsForOrder`, `messaging_GetAttributes` | read-only |
| Send (write) | `messaging_confirmCustomizationDetails`, `messaging_createConfirmDeliveryDetails`, `messaging_createConfirmOrderDetails`, `messaging_createConfirmServiceDetails`, `messaging_createUnexpectedProblem`, `messaging_createDigitalAccessKey`, `messaging_sendInvoice`, `messaging_CreateWarranty`, `messaging_createLegalDisclosure` | `destructiveHint: true`, not idempotent |
| Upload | `uploads_createUploadDestinationForResource` | `destructiveHint: true` |
| Orders (read) | `orders_getOrders`, `orders_getOrder`, `orders_getOrderItems` | read-only |
| Server context (callable only in `execute`) | `list_identities`, `set_active_identity`, `list_marketplaces`, `get_active_region`, `set_active_region` | — |

Unknown names fail with `Unknown tool: <name>`; there's no fuzzy matching.
Don't use `orders_getOrderItemsBuyerInfo`: messaging doesn't need buyer PII.

## Argument shapes

Body fields are flattened into top-level arguments next to the path
parameters:

```python
await call_tool("messaging_createUnexpectedProblem", {
    "amazonOrderId": "113-1234567-1234567",
    "marketplaceIds": ["ATVPDKIKX0DER"],   # exactly one
    "text": "Hello, ...",
})

await call_tool("messaging_CreateWarranty", {
    "amazonOrderId": "113-1234567-1234567",
    "marketplaceIds": ["ATVPDKIKX0DER"],
    "attachments": [{"uploadDestinationId": "<from upload>", "fileName": "Warranty.pdf"}],
    "coverageStartDate": "2026-10-01T00:00:00Z",
    "coverageEndDate": "2028-10-01T00:00:00Z",
})
```

The live server marks only `amazonOrderId` and `marketplaceIds` as
required. Amazon still rejects an empty `text` on text types (minLength 1),
and an empty `attachments` list on `sendInvoice` and `CreateWarranty`.

## Identity and region

With no identity selected, SP-API calls fail with
`Provider identity selection is required.`

On a code-mode server the selected identity has been observed **not to be
isolated per MCP session** (2026-09-24). So call `set_active_identity` at the
top of **every** `execute` block that touches seller data, and above all
before every send block.

- `list_identities` returns `{"result": [{id, label, attributes}]}`.
  `label` is the seller's merchant ID. Agency tokens return many entries,
  so **filter inside the sandbox** and return only the match. Never print
  the full list.
- Server-context tools wrap their output in `{"result": ...}`; SP-API
  tools return Amazon's payload directly.
- The region must serve the order's marketplace: NA for US, CA, MX, and BR;
  EU for UK, DE, FR, IT, ES, and others; FE for JP, AU, and SG. Use
  `list_marketplaces` to map a marketplace to its region, and
  `set_active_region` if needed.

## Response shapes (from Amazon's model)

`getMessagingActionsForOrder` returns HAL JSON:

```json
{
  "_links": {
    "self": {"href": "/messaging/v1/orders/113-1234567-1234567?marketplaceIds=ATVPDKIKX0DER"},
    "actions": [
      {"href": "/messaging/v1/orders/113-1234567-1234567/messages/unexpectedProblem?marketplaceIds=ATVPDKIKX0DER",
       "name": "unexpectedProblem"}
    ]
  },
  "_embedded": {
    "actions": [
      {"_links": {"self": {"href": "..."}, "schema": {"href": "...", "name": "unexpectedProblem"}},
       "_embedded": {"schema": {"type": "object", "properties": {"text": {"maxLength": 2000}}}},
       "name": "unexpectedProblem"}
    ]
  }
}
```

An empty `actions` list means no message types are available for this order
right now.

`GetAttributes` returns `{"buyer": {"locale": "en-US"}}`.

Send operations return **201 with no body** on success. Any `errors` array
means the call failed.

## Errors

| Code | Meaning | Action |
|---|---|---|
| 400 | Invalid input: text too long, bad marketplace, unknown upload ID | Fix and preview again; don't silently alter approved text |
| 403 | App lacks the Buyer Communication role for this seller, or the type isn't allowed for this order | Same 403 on every order → role missing; tell the seller. Single order → skip it |
| 404 | Order not found in this marketplace or region | Check the marketplace and region |
| 413 / 415 | Payload too large, or unsupported media type | Report it; check the attachment |
| 429 | Throttled (1 request/second, burst 5) | Back off and retry that call |
| Any 5xx (500, 502, 503, 504, …) or a timeout on a **send** | Unknown whether it was delivered | Don't retry. Mark "unknown" and ask the seller to check Seller Central |

## Batch pacing

Send sequentially in one `execute` block. Sleep about 1.1 seconds between
sends, and return a per-order result list instead of raw payloads.

Each approved item carries its operation's own body fields, exactly as the
seller approved them. Text types carry `text`. File types carry
`attachments` (plus `coverageStartDate` and `coverageEndDate` for a
warranty). Types that take both carry both.

```python
import asyncio

def status_codes(msg):
    # 3-digit tokens in the error text, e.g. "SP-API error 503: ..." -> {"503"}
    cleaned = "".join(c if c.isalnum() else " " for c in msg)
    return {t for t in cleaned.split() if len(t) == 3 and t.isdigit()}

await call_tool("set_active_identity", {"id": SELLER_IDENTITY_ID})
results = []
for o in approved:          # exactly the orders and bodies the seller approved
    # o["body"]: {"text": ...} or {"attachments": [...], "coverageStartDate": ..., ...}
    params = {"amazonOrderId": o["id"], "marketplaceIds": [o["mp"]], **o["body"]}
    for attempt in range(3):
        try:
            await call_tool(o["tool"], params)
            results.append({"order": o["id"], "result": "sent"})
            break
        except Exception as e:
            msg = str(e)[:200]
            codes = status_codes(msg.replace(o["id"], " "))   # ignore the order ID's own digits
            if "429" in codes and attempt < 2:    # throttled: never delivered, safe to retry
                await asyncio.sleep(2 ** (attempt + 1))
                continue
            # A 4xx means Amazon rejected it: definitely not sent. A 5xx, a timeout,
            # or an error with no status means delivery is unknown.
            rejected = any(c.startswith("4") for c in codes)
            results.append({"order": o["id"], "result": "failed" if rejected else "unknown",
                            "error": msg})
            break
    await asyncio.sleep(1.1)
return results
```

Status codes are read as whole 3-digit tokens, after removing the order ID
from the error text. That way an order ID (some marketplaces' IDs start
with `503-`) can't be mistaken for a status. If the error doesn't say what
happened, treat it as unknown rather than failed. The unknown path never
risks a duplicate message.

If `asyncio` isn't importable in the sandbox, send in smaller `execute`
blocks (five or fewer each, which stays within the burst) and pace between
blocks.
