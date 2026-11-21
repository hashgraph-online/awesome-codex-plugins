# Funnel Hack

Funnel Hack mode in full: buy from the target the way a customer or fan would, and map every step from the first ad to the last follow-up. It extends `go-inside.md`, and all of its rules apply: the user approves each action, the user's real identity, a dedicated inbox on the user's domain, and no payment without an explicit yes.

## Contents
- Before you buy
- Map the money path
- Check the urgency
- Find their tests
- Read their paid search
- Build the swipe file
- The funnel map deliverable

---

## Before You Buy

- **Set a purchase budget with the user** before the first purchase: the total, the products, and whether to take upsells. Every purchase needs an explicit yes with the amount. The purchase budget is separate from the $5 data cap.
- **Buy to keep.** Refund only under the seller's published policy and for a real reason. Don't plan purchases around refunds.
- **Use the user's payment method and name.** No virtual cards in made-up names.
- **Don't exploit bugs.** If a checkout misprices something or a discount stacks by mistake, note it and don't use it.
- **Pick the entry point a real buyer would use:** an active ad from the ad libraries, a lead magnet, a creator's link-in-bio, or the homepage. Record which one, because funnels differ by entry.

## Map the Money Path

Screenshot and record each step in `teardowns/<target-slug>/funnel/steps.csv`:

`step,url,screenshot,offer,price,anchor_price,cta,timer_or_scarcity,notes`

| Step | What to capture |
|---|---|
| **Ad or post** | Hook, offer, and the exact landing page with its UTM parameters |
| **Landing page** | Headline, offer stack, proof, guarantee, CTA, page speed |
| **Opt-in** | Fields, lead magnet, consent language, SMS opt-in |
| **Thank-you page** | The immediate next offer, often a low-price first purchase |
| **Checkout** | Order bump, payment options, shipping threshold, subscribe-and-save, bundles, trust badges |
| **Upsells and downsells** | Each one-time offer after checkout: product, price, and what happens on decline |
| **Confirmation** | Post-purchase offers, referral prompt, account creation |
| **Follow-up** | Every email and SMS for 30 days, logged as in go-inside.md |

Side paths:

- **Abandoned cart:** add to cart, enter the email, leave. Log messages, timing, and whether the discount grows.
- **Abandoned opt-in:** start the quiz or opt-in and stop halfway, if the flow captures the email early.
- **Popups:** what triggers each (time, scroll, exit intent), the offer, and whether it changes on a second visit.
- **Webinar funnels:** registration, confirmation, reminders, replay page, the minute the pitch starts, the offer, and the deadline.
- **Quiz funnels:** every question, the branches, each result page, and the offer each result gets.
- **Creator funnels:** link-in-bio order, the free-to-paid path (newsletter to course, Discord to membership, pre-save to merch bundle), and the bundle or presale code each channel uses.

## Check the Urgency

Open each countdown timer, "only N left", and "offer ends tonight" message in two clean browser sessions a few hours apart, and again after the stated deadline. Record exactly what you saw as **Observed**: "the timer restarted in a new session", "the count stayed at 7 for three days". Whether the scarcity is staged is **Inferred**: a count that never moves can mean no sales, and a restarting timer can be a disclosed per-visitor offer. Either way, don't copy urgency as if it's what converts. False scarcity runs into the FTC's rules on deceptive practices and their equivalents elsewhere.

## Find Their Tests

- **Testing tools:** read the page source of the landing, pricing, and checkout pages for client-side testing scripts. Some expose readable experiment names in their config (for example `pricing_annual_default_v3`). A name can belong to a paused or finished test; label it **Inferred**.
- **Variant check:** load the landing page, pricing page, and checkout in three or four fresh sessions and compare. Different headlines, prices, or bumps suggest a live test or personalization (**Inferred**). Screenshot each variant.
- **Dynamic text:** change `?keyword=`, `?utm_term=`, or `?q=` on an ad landing page and see if the headline changes to match.
- **Geo pricing:** only if the session's browser tool offers country settings as a normal feature; never use a tool to disguise location past a block.

## Read Their Paid Search

Search results with ads, from an authorized SERP data tool or by hand:

| Query | What it shows |
|---|---|
| Their brand or name | Whether they protect it, and who bids on it |
| The user's brand | Whether they bid on the user, and their copy against the user |
| Other competitors' names | Who they treat as rivals |
| Category terms ("best X", "X near me") | The copy and landing pages they pay for |
| "[their brand] alternative", "[their brand] pricing" | How they defend their own funnel |

Record copy and landing page for each, dated. Hand conquesting findings to `$suede-ads` and `$suede-competitors`.

## Build the Swipe File

One file, `teardowns/<target-slug>/funnel/swipe.md`, grouped by type, every item linked and dated:

- **Hooks:** first lines of ads, emails, posts, and landing pages
- **Headlines and subheads**
- **Offer stacks:** bonuses, guarantees, payment plans, price anchors, bundles
- **Proof:** testimonial formats, numbers, logos, review widgets
- **CTAs and button copy**
- **Email subject lines** with their send day

Hand it to `$suede-offers`, `$suede-copy`, and `$suede-emails`. Copy the structure, never the words: their copy, images, and recordings are protected.

## The Funnel Map Deliverable

`teardowns/<target-slug>/funnel/map.md`:

1. **The diagram:** each step as a box with its price, in order, with branches for declines and abandons
2. **The offer stack table:** every product and offer, its price, its anchor, and where it appears
3. **The follow-up calendar:** day by day, email and SMS, with offers
4. **Tests seen:** tools, config names, variants
5. **Urgency check results**
6. **What to copy and what not to:** with the Suede skill that runs each copied piece (`$suede-offers`, `$suede-site-alchemy`, `$suede-emails`, `$suede-sms`, `$suede-pricing`, `$suede-paywalls`)
7. **Spend:** what was bought, the total, and any refunds under the published policy
