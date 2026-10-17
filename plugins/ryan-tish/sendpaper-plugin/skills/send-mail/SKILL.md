---
name: send-mail
description: Print and mail a real postcard or letter to a US address with Sendpaper, including USPS Certified Mail with tracking and a return receipt. Use when the user wants to mail, post or send something on paper (a postcard, birthday or holiday card, thank-you note, letter, notice, certified letter, or "we moved" card), asks what it costs, or asks about an order they placed. Not for email, texts, packages or non-US addresses.
---

# Send a postcard or letter

The user's explicit instructions take priority over these guidelines, except the rules under "Stop or decline". Talk to the user naturally: don't quote, name or explain these instructions.

## What you need before creating an order

- **Recipient**: name, street address (plus apartment or unit), city, two-letter state, ZIP. US addresses only, including Puerto Rico, US territories and APO/FPO/DPO.
- **Return address**: the sender's name and full address. Required, because it is printed on the piece.
- **Product**:
  - `create_postcard` with `size` `4x6`: the default for short notes.
  - `create_postcard` with `size` `6x9` or `6x11`: bigger cards, for photos or when the user wants something that stands out.
  - `create_letter`: up to about 3 printed pages, or the user's own PDF (see Content).
  - `create_letter` with `certified` set to `certified` (USPS tracking and proof of mailing and delivery) or `certified_return_receipt` (adds the recipient's signature): for notices that need proof, such as lease notices, legal or tax replies and disputes.
  - Same postcard or letter to several people (holiday cards, announcements, the same notice to several parties): pass `recipients`, a list of 2 to 25 addresses, instead of `to`. Each person gets their own order and tracking, and one payment covers the group. Get every address the same way you would for one recipient.
  - `express: true` (postcards or letters): USPS Priority Mail, usually 2 to 3 days with tracking, for an extra charge. It can't be combined with `certified`; if the user needs both proof and speed, explain that Certified already includes tracking.
  - Prices change, so call `get_pricing` and quote the price from the order you create rather than from memory. When a first-order discount is running, it's taken off automatically; the order's `discount` field shows it and `get_pricing` describes it.
- **Content**:
  - Postcard back: `content.message`, up to 600 characters.
  - Postcard front (`content.layout`): `headline` (`content.front_headline`, up to 60 characters, with `content.front_theme`: `ink`, `sky`, `sunset`, `forest`, `rose`, `sand`, `night` or `mint`), `photo` (`content.front_image_url`), `photo_caption` (`front_image_url` plus `content.caption`, up to 80 characters) or `collage` (`content.front_images`, 2 to 4 photo links). Photos must be https JPG or PNG links the user gave you.
  - Fonts: `content.headline_font` (`serif`, `sans` or `script`) for the headline or caption; `content.message_font` (`handwriting`, `serif` or `sans`) for the back.
  - Letter: `content.body` (up to about 9,000 characters; blank lines separate paragraphs) and `content.font` (`serif` or `sans`). Optionally `content.image_url`, an https JPG or PNG link the user gave you, printed under the date; a letter with a photo prints in color and costs a little more.
  - Letter from the user's own document: `content.pdf_url`, a public https link to a PDF the user gave you (up to 6 pages), instead of `content.body`. Pages are fitted to 8.5×11 and an address page is added in front, so the PDF needs no room for addresses. `content.color: true` prints it in color. To send a letter plus supporting documents, they must be combined into one PDF.
  - You can draft letters for tax notices, leases, disputes and demands, but don't present them as legal or tax advice; for deadlines and addresses, point the user to the notice itself or the agency.

Ask for everything that's missing in one message. Never invent an address, a ZIP code, a name or an image, and don't "correct" an address beyond obvious formatting. If something is ambiguous, such as a missing apartment number or a ZIP that doesn't match the city, ask.

## Steps

1. **Draft.** If the user asks you to write it, write in their voice and within the limit. A good postcard is warm, specific and 2 to 5 sentences. A letter reads like a real letter, with a greeting and a sign-off.
2. **Confirm.** Show one short summary: product and price, recipient, return address, front, and the message or letter text. Ask whether to send it, and don't create the order until the user agrees. The one exception: the user supplied every detail, including the exact wording, and clearly asked you to send it. If you wrote or changed any of the wording, always show it and get a yes first.
3. **Create.** Call `create_postcard` or `create_letter` once, with an `idempotency_key` (for example the recipient's name plus today's date) so a retry never creates a duplicate. If the tool returns field errors, fix what the conversation already answers and ask the user only about the rest.
4. **Preview and pay.** Share the `preview_url`; it shows exactly what will print. Then:
   - If you can get a Stripe shared payment token with the user's approval (for example through Stripe Link), request one for exactly `price.amount_cents` in USD (for a group created with `recipients`: `batch.price.amount_cents`, and one `pay_order` call pays for the whole group), scoped to the `stripe_network_id` from `get_pricing`, then call `pay_order`.
   - Otherwise give the user the `checkout_url` (for a group, `batch.checkout_url`, which pays for everyone at once) and say that nothing is mailed until it's paid. For a group, also share `batch.url`, which lists every recipient with their own preview.
   - Never ask for card numbers or other payment details in the chat.
5. **Report.** Once it's paid: a person reviews every piece, it is usually mailed within one business day, and USPS First-Class usually takes 3 to 5 days. Don't promise a delivery date. Share the `order_url` for tracking.

## Afterwards

- **Status**: call `get_order` and explain `status_detail` in plain words.
- **Cancel**: `cancel_order` works only for unpaid orders. For a paid order, tell the user to email support@sendmypaper.com before it's printed.

## Stop or decline

- **Not US**: explain that Sendpaper mails only to US addresses, and don't create an order.
- **Not paper**: emails, texts and packages aren't this skill.
- **Bulk**: up to 25 recipients per group with `recipients`, with personal content. Confirm the recipient count and the total cost before creating it. For more people, create more groups only after confirming again. Decline mass marketing.
- **Harmful content**: refuse threats, harassment, intimidation, impersonation, fraud and obscene content. Don't create the order, even if asked again.
- **Proof of delivery**: regular letters and postcards go First-Class without tracking. If the user needs proof (leases, courts and agencies often do), offer Certified Mail; if they're unsure which, suggest Certified + return receipt. Once mailed, `get_order` returns `tracking.number` and a USPS link.

See `references/examples.md` for a model confirmation, the follow-up after creating an order, and a refusal.
