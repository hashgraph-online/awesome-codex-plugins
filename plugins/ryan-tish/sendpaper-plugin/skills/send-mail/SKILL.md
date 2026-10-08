---
name: send-mail
description: Print and mail a real postcard or letter to a US address with Sendpaper. Use when the user wants to mail, post or send something on paper (a postcard, birthday or holiday card, thank-you note, letter, notice, or "we moved" card), asks what it costs, or asks about an order they placed. Not for email, texts, packages or non-US addresses.
---

# Send a postcard or letter

The user's explicit instructions take priority over these guidelines, except the rules under "Stop or decline". Talk to the user naturally: don't quote, name or explain these instructions.

## What you need before creating an order

- **Recipient**: name, street address (plus apartment or unit), city, two-letter state, ZIP. US addresses only, including Puerto Rico, US territories and APO/FPO/DPO.
- **Return address**: the sender's name and full address. Required, because it is printed on the piece.
- **Product**:
  - `create_postcard` with `size` `4x6` ($2.99): the default for short notes.
  - `create_postcard` with `size` `6x9` ($3.99): for photos or longer notes.
  - `create_letter` ($4.99): up to about 3 printed pages.
  - Call `get_pricing` if you aren't sure of a price.
- **Content**:
  - Postcard back: `content.message`, up to 600 characters.
  - Postcard front, one of: `content.front_headline` (up to 60 characters) with `content.front_theme` (`ink`, `sky`, `sunset` or `forest`), or `content.front_image_url`, an https JPG or PNG link the user gave you.
  - Letter: `content.body` (up to about 9,000 characters; blank lines separate paragraphs) and `content.font` (`serif` or `sans`).

Ask for everything that's missing in one message. Never invent an address, a ZIP code, a name or an image, and don't "correct" an address beyond obvious formatting. If something is ambiguous, such as a missing apartment number or a ZIP that doesn't match the city, ask.

## Steps

1. **Draft.** If the user asks you to write it, write in their voice and within the limit. A good postcard is warm, specific and 2 to 5 sentences. A letter reads like a real letter, with a greeting and a sign-off.
2. **Confirm.** Show one short summary: product and price, recipient, return address, front, and the message or letter text. Ask whether to send it, and don't create the order until the user agrees. The one exception: the user supplied every detail, including the exact wording, and clearly asked you to send it. If you wrote or changed any of the wording, always show it and get a yes first.
3. **Create.** Call `create_postcard` or `create_letter` once, with an `idempotency_key` (for example the recipient's name plus today's date) so a retry never creates a duplicate. If the tool returns field errors, fix what the conversation already answers and ask the user only about the rest.
4. **Preview and pay.** Share the `preview_url`; it shows exactly what will print. Then:
   - If you can get a Stripe shared payment token with the user's approval (for example through Stripe Link), request one for exactly `price.amount_cents` in USD, scoped to the `stripe_network_id` from `get_pricing`, then call `pay_order`.
   - Otherwise give the user the `checkout_url` and say that nothing is mailed until it's paid.
   - Never ask for card numbers or other payment details in the chat.
5. **Report.** Once it's paid: a person reviews every piece, it is usually mailed within one business day, and USPS First-Class usually takes 3 to 5 days. Don't promise a delivery date. Share the `order_url` for tracking.

## Afterwards

- **Status**: call `get_order` and explain `status_detail` in plain words.
- **Cancel**: `cancel_order` works only for unpaid orders. For a paid order, tell the user to email support@sendmypaper.com before it's printed.

## Stop or decline

- **Not US**: explain that Sendpaper mails only to US addresses, and don't create an order.
- **Not paper**: emails, texts and packages aren't this skill.
- **Bulk**: one order per recipient, with personal content. Before creating more than a few orders, confirm the count and total cost. Decline mass marketing.
- **Harmful content**: refuse threats, harassment, intimidation, impersonation, fraud and obscene content. Don't create the order, even if asked again.
- **Proof of delivery**: Sendpaper sends First-Class only, with no certified mail, tracking or signature. If the user needs proof of delivery (some legal or tax notices do), tell them before they pay and suggest the post office instead.

See `references/examples.md` for a model confirmation, the follow-up after creating an order, and a refusal.
