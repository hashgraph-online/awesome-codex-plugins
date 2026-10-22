# Message types

Source: Amazon's Messaging API v1 model (`messaging.json` in
`amzn/selling-partner-api-models`), cross-checked against the live tool
schemas on 2026-09-29. Every operation's rate is 1 request/second, burst 5.
All take `amazonOrderId` (path) and `marketplaceIds` (one ID).

## Contents

- [Matching eligibility to a tool](#matching-eligibility-to-a-tool)
- [Summary](#summary)
- [Per-type guidance](#per-type-guidance)
- [Stale or removed types](#stale-or-removed-types)

## Matching eligibility to a tool

`getMessagingActionsForOrder` returns HAL-style links. Each available type
appears in `_links.actions[]` with an `href` such as
`/messaging/v1/orders/113-1234567-1234567/messages/unexpectedProblem?marketplaceIds=ATVPDKIKX0DER`
and usually a `name`. `_embedded.actions[]` carries each type's JSON schema,
including the `text` and `attachments` constraints. **Match on the last path
segment of the `href`** (before the query string), which maps to a tool as
follows:

| Path segment | Tool | Body | Text limit | Attachments |
|---|---|---|---|---|
| `confirmCustomizationDetails` | `messaging_confirmCustomizationDetails` | text, attachments | 800 | 0–5 |
| `confirmDeliveryDetails` | `messaging_createConfirmDeliveryDetails` | text | 2000 | — |
| `confirmOrderDetails` | `messaging_createConfirmOrderDetails` | text | 2000 | — |
| `confirmServiceDetails` | `messaging_createConfirmServiceDetails` | text | 2000 | — |
| `unexpectedProblem` | `messaging_createUnexpectedProblem` | text | 2000 | — |
| `digitalAccessKey` | `messaging_createDigitalAccessKey` | text, attachments | 400 | 0–5 |
| `invoice` | `messaging_sendInvoice` | attachments | — | 1–5 |
| `warranty` | `messaging_CreateWarranty` | attachments, coverageStartDate, coverageEndDate | — | 1–5 |
| `legalDisclosure` | `messaging_createLegalDisclosure` | attachments | — | 0–5 |

If `_embedded` gives a tighter limit than this table, the embedded schema
wins: it's specific to the order and marketplace.

The same path, without the query string, is the `resource` for an
attachment upload. See [attachments.md](attachments.md).

## Summary

- **Text types** carry a message written by the seller.
- **File types** (`invoice`, `warranty`, `legalDisclosure`) carry only
  documents, with no free text. Any text inside the document must be in the
  buyer's language.
- **Critical types** (`unexpectedProblem`, `legalDisclosure`) are delivered
  even when the buyer has opted out of other messages. That is why Amazon
  scrutinizes their misuse most.

## Per-type guidance

### Unexpected problem: `createUnexpectedProblem`

A problem that affects completing the order: stock ran out after purchase,
the item was damaged before shipping, a carrier or weather delay, an address
the carrier can't deliver to.

- Say what happened, what it means for the buyer (new date, options), and
  what, if anything, the buyer needs to do.
- Not for good news, confirmations, or anything that isn't a problem.
- Amazon documents this type for NA and FE only.

### Confirm order details: `createConfirmOrderDetails`

An order-related question that must be answered **before shipping**, such
as which of two ambiguous options the buyer meant, or a required detail
missing for a regulated item. Not for post-shipment follow-ups.

### Confirm delivery details: `createConfirmDeliveryDetails`

Arranging delivery or confirming contact details for making it: scheduling
a freight or large-item delivery, or a delivery window. Links are allowed
only if they relate to the delivery (for example, a carrier scheduling
page).

### Confirm customization details: `confirmCustomizationDetails`

Verifying personalization before production: name spelling, initials,
engraving text, a buyer-supplied image. Up to 800 characters, plus up to 5
attachments, such as a proof image for the buyer to check.

### Confirm service details: `createConfirmServiceDetails`

Home Services orders only: arranging the service call or gathering
information needed before it.

### Digital access key: `createDigitalAccessKey`

Delivering a code or key the buyer needs to use digital content in the
order. The text is capped at 400 characters, so keep it to the key and
short redemption steps. Attachments (for example, a PDF with instructions)
are optional.

### Invoice: `sendInvoice`

Sending the buyer an invoice for the order as a file (1–5 attachments).
Some marketplaces have their own invoicing programs (for example, VAT
Calculation Service in EU, or Amazon's invoicing in some FE marketplaces).
If the seller is enrolled in one, Amazon may already provide the invoice,
so check before sending a duplicate.

### Warranty: `CreateWarranty`

Warranty documents for items in the order (1–5 attachments), optionally
with `coverageStartDate` and `coverageEndDate` as ISO 8601 date-times, for
example `2026-10-01T00:00:00Z`. Work the dates out from what the seller
states. When the seller states both the start date and a whole-year term,
the dates are theirs, only written in ISO form: "2 years from delivery on
Sept 28, 2026" gives `2026-09-28T00:00:00Z` to `2028-09-28T00:00:00Z`, the
same calendar date two years on. Any date you have to work out beyond that
is computed: a start date you look up in the order data, a term in months
or days, an end-of-day choice, or anything else that takes a judgment call.
Show both dates in the preview and wait for a yes before uploading or
sending, even when the seller has already said send. Never only report
them after the send. If the seller gives no term at all, ask. Don't take a
term from the document or guess one.

### Legal disclosure: `createLegalDisclosure`

"A critical message that contains documents that a seller is legally
obligated to provide to the buyer. This message should only be used to
deliver documents that are required by law." Examples: a legally mandated
safety or regulatory notice for the product. Ask the seller which law
requires the document. If they can't say, it probably doesn't qualify, and
a warranty or invoice type may fit instead.

## Stale or removed types

- `CreateAmazonMotors` still appears on Amazon's Messaging overview page,
  but it isn't in the current model or on the live server. Don't try to call
  it.
- `createNegativeFeedbackRemoval` was removed from the API. Asking a buyer
  to change or remove feedback isn't something this skill does.
- The Send a Message tutorial shows `text` as required for every type. The
  model says otherwise: file types have no `text` field. Follow the model
  and the live schema.
