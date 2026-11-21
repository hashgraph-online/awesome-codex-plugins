# Promo codes, cashback and stacking

Checked 2026-10-29. Re-check any specific site or program before relying on it.

## Where codes come from, best first

| Tier | Sources | Treat as |
|------|---------|----------|
| Best | The merchant itself: site banner, cart promotions, first-order, newsletter or SMS sign-up offers, app-only deals, the merchant's own student, teacher or military pages, verification partners the merchant names (UNiDAYS, Student Beans, SheerID, ID.me) | verified once seen on the merchant's page |
| Good | Deal communities with dates, votes and "worked for me" replies: Slickdeals (US), the Pepper network (HotUKDeals UK, mydealz DE, Dealabs FR), OzBargain (AU), RedFlagDeals (CA), the brand's or category's subreddit | reported, with the date of the last confirmation |
| Fine | Codes a creator or partner publishes openly for their audience (podcast, newsletter, YouTube sponsor codes) | reported until tested |
| Weak | Big coupon aggregators and long-tail coupon sites | unverified: many list "codes" that never existed; list at most two |
| Never | Leaked employee, internal or single-use codes, "code generators", code dumps in chat groups, someone else's student code | do not use: merchants cancel these orders and it breaks their terms |

Red flags: no date, discounts far beyond what the brand ever offers (70 to 90 percent sitewide),
a site that requires installing an extension to "reveal" the code, codes behind surveys.

## Verifying a code without buying

Only in a cart the user asked you to prepare, and stop before payment:

1. Rank candidates (merchant-issued, then community posts confirmed in the last 7 days, 30 at most,
   then aggregators). Try about 5 to 10. Never brute-force codes: it is abuse and can trigger fraud locks.
2. Add the item, enter the code in the cart or checkout code field, read the new total, note it,
   then remove the code or the item if the user has not decided yet. Never place the order, enter
   payment details or accept terms.
3. If the code field only appears after entering an email or address, ask the user first: that is
   their personal data.
4. **Shopify stores** (very common): `https://<store>/discount/<CODE>` applies a code to the
   session but fails silently when invalid, so always confirm on the cart total. The cart AJAX API
   also accepts `POST /cart/update.js` with a `discount` field; read `/cart.js` afterwards.
5. Record: store, code, date and time, subtotal before and after, conditions (minimum spend,
   excluded items, new customers only, stackable or not).

## Cashback portals

- Rakuten, TopCashback (US and UK) and Quidco (UK) are the large ones; many countries have local
  portals, and some banks run their own.
- Only the last click tracks: use **one** portal per order, click through it right before buying,
  and do not click other deal links afterwards.
- Ad blockers and coupon extensions can break or override tracking.
- A code not listed on the portal can void the cashback: read the portal's terms for that store.
- Rates change daily; compare at purchase time.

## Card-linked offers and card benefits

- Card issuers run targeted merchant offers (for example Amex Offers, Chase Offers). They must be
  **added to the card before paying**, often stack with a portal and normal card rewards, and
  credits can take weeks to post.
- Card price protection has mostly disappeared; check the card's own benefits guide before
  promising it. Extended warranty and purchase protection are still common: mention them before
  the user buys a store's extended warranty.

## Discounted gift cards

- Buying a gift card below face value, then paying with it, stacks with most other savings.
- CardCash buys and sells gift cards with a buyer guarantee. Raise now sells gift cards that earn
  rewards, and the discounted peer-to-peer marketplace that used to be Raise is now GCX.
- Risks: partial balances, cards already used, merchant rules on gift card payments. Prefer
  sellers with a guarantee and use the card soon.

## Coupon browser extensions

Do not recommend coupon-finding extensions by default. Honey (PayPal) faces a consolidated US
lawsuit, past its motion to dismiss in 2026, over overwriting creators' affiliate cookies and
hiding better codes. Capital One Shopping settled a similar case in 2026. Chrome Web Store rules
now allow affiliate injection only when the user gets a direct, visible benefit. The user can
choose to use one; you should not.

Never strip, replace or add affiliate parameters to links yourself.

## Stacking order

Check each step's terms; skip any step the terms forbid.

1. The right product at the right seller (comparison, refurbished, timing).
2. Program or eligibility price (student, employer, membership).
3. Promo code.
4. Cashback portal click-through.
5. Card-linked offer added to the card.
6. Paying with a discounted gift card, where allowed.
7. After purchase: price adjustment or rebooking if the price drops within the window.
