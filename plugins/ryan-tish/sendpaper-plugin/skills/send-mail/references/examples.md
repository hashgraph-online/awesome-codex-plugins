# Examples

Use these as a model for tone and structure, not as fixed text.

## Confirmation before creating an order

> Here's the postcard. Want me to send it?
>
> - **4×6 postcard, $2.99** (printing and postage included)
> - **To:** Dana Kim, 12 Oak St, Austin, TX 78701
> - **From:** Alex Kim, 88 Pine Ave, Denver, CO 80202
> - **Front:** "Happy birthday, Mom!" on the sunset color
> - **Back:** "Happy birthday! I hope your day is full of good food and better company. I'll call you Sunday. Love, Alex"

## After `create_postcard` succeeds (no payment token available)

> Done. Here's exactly what will print: [preview](preview_url).
> Pay $2.39 here to send it (that includes your first-order discount): [checkout](checkout_url). Nothing is mailed until it's paid. After that, a person checks it and it's usually in the mail within one business day.

## After creating a group with `recipients`

> Done: 3 postcards, one each for your parents, Jo and Sam. Each has its own preview here: [group](batch.url).
> Pay $8.97 once for all three: [checkout](batch.checkout_url). Nothing is mailed until it's paid; then each card is checked and mailed separately, with its own tracking page.

## After `pay_order` succeeds

> Paid. Your postcard to Dana Kim is in the print queue and usually goes out within one business day; First-Class mail typically takes 3 to 5 days. Track it here: [order](order_url).

## Missing details

> Happy to send that. I just need two things: Dana's ZIP code, and your return address (it's printed on the card).

## Refusal

> I can't send that. Sendpaper won't mail threatening or harassing messages. If you want to reach out about something else, I'm happy to help write it.
