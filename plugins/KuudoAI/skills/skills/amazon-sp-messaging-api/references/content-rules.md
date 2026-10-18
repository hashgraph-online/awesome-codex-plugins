# Content rules for buyer messages

Two sources apply to every message:

1. **The live tool schema.** Each `text` field says: only links related to
   that message type's purpose; no HTML; no email addresses; written in the
   buyer's language of preference (from `GetAttributes`). Length limits
   come from the schema too.
2. **Amazon's Buyer-Seller Communication Guidelines** in Seller Central.
   What follows is a working summary, not the policy. If the seller quotes
   current policy that differs, follow the policy.

## Allowed purposes

A proactive message is allowed only when it's **needed to complete the order
or resolve a problem with it**. The Messaging API's types encode those
purposes, so a message that doesn't fit a type almost always isn't allowed.

## Not allowed in any message

| Rule | Examples to catch |
|---|---|
| Marketing or promotion | discount codes, "check out our new…", other products, newsletters, loyalty programs |
| Review or feedback requests, in any form | "leave us a review", "how many stars…", "let us know how we did", "if you're happy tell others", incentives for reviews |
| Asking to change or remove a review or feedback | "please update your review", offering a refund in exchange |
| Messages with no order-completion purpose | "thank you for your order", "your order has shipped" (Amazon sends these) |
| Contact redirection | email addresses, phone numbers, links to the seller's site, social profiles, WhatsApp, "contact us directly at…" |
| Unrelated links | any link not needed for this message type's purpose; tracking or scheduling links only when they serve delivery |
| HTML, logos, or embedded images in the text | `<b>`, `<a href>`, image markup |
| Buyer data the seller shouldn't have | copying the buyer's full address or phone number into the text |
| Pressure or disparagement | threats about the order, comments about Amazon or competitors |

## Draft checklist

Run this before every preview; for a batch, run it on each rendered text.

- [ ] The type matches the purpose (see [message-types.md](message-types.md))
- [ ] The length is within the type's limit, in characters
- [ ] It's in the buyer's `locale` language, with a translation shown to the
      seller if that's different
- [ ] It has no marketing, no review or feedback asks, and no
      thank-you-only filler
- [ ] It has no email addresses, phone numbers, or off-Amazon contact
      routes
- [ ] Every link, if any, is needed for this purpose; with no clear need,
      remove it
- [ ] It's plain text, with no HTML
- [ ] It has concrete facts the buyer needs (dates, options, what to do
      next) and nothing invented. Dates, amounts, and promises come from the
      seller or the order data, not from you

## Rewriting non-compliant text

When the seller's own text breaks a rule, show what breaks which rule, then
a compliant rewrite that keeps their intent. Example:

> **Seller:** "Sorry your mug is delayed! Use code SORRY10 for 10% off next
> time, and if you liked it, a 5-star review would mean the world. Email me
> at jo@mugshop.com with questions."
>
> **Problems:** discount code (marketing), review request, email address.
>
> **Rewrite for `createUnexpectedProblem`:** "Hello, we're sorry: your
> order is delayed because the glaze batch failed quality checks. We now
> expect to ship it by October 8. If you'd rather not wait, you can request
> a cancellation from Your Orders on Amazon. We apologize for the
> inconvenience."

Don't send the original even if the seller insists. Explain that it risks
their account, and offer the rewrite.
