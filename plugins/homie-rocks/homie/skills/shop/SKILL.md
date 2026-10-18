---
name: shop
description: Sell things in a Homie studio's games with the studio's OWN Stripe - a supporter pack, cosmetics, a season pass, a one-time unlock, a tip, a round of several items to a table, a paid booking with slot capacity, monthly giving or a membership - in real money, with Stripe Checkout, Stripe Tax or Stripe Managed Payments, refunds from the office, and optional studio policies with an open default; set up with Stripe's own agent tools (Stripe's MCP server and skills) with one browser approval and Payment Links by default, no human-handled key and no API key in the Worker. Use when someone asks to sell something, add a shop or store, take payments or donations, take paid bookings, set up monthly giving or memberships, make money from a game, set up or connect Stripe, make the products in Stripe, asks "how are sales?", about tax or Managed Payments, to add a supporter badge, refund a player, or about chargebacks.
compatibility: Stripe's official OAuth MCP/plugin, Homie's stripe_shop_plan and stripe_webhook tools, and Wrangler. Stripe CLI is used privately for webhook setup and local forwarding.
metadata:
  providers: stripe
---

Customer AIs can buy through the studio's own `/mcp`. Read the toolkit's `tools/TOOLS.md`
and use the `tools` skill for `studio_catalogue`, cart quotes, standard agent payments,
private purchase claims, and human Stripe checkout approval. Priced studio tools sell
services through that same purchase engine; `shop connect` synchronizes their Payment Links.
Keep orders, grants and refunds in the existing shop. For order/refund follow-up code, use
Studio functions (`functions/FUNCTIONS.md`), with the event ID as the idempotency key.


# The shop

Check that the toolkit exposes `stripe_shop_plan` and `stripe_webhook`; upgrade older toolkits first.
The guide is `node_modules/@homie-rocks/studio/shop/SHOP.md`; the owner's plain words are `SELLING.md`.

**The model, said plainly to the person.** The studio sells with **its own Stripe account**. The studio is the
seller: its prices, its refunds, its disputes, its tax. Money goes straight from players to the studio's Stripe;
**homie.rocks never sees it, holds it or moves it, and Homie takes no cut.** The studio is responsible for the law where it sells and for Stripe's terms.

In a rules game, keep shop UI in the view. Do not turn a client character save, an
entity field or a command into proof of a purchase: grants still come from the shop's
verified server records. Room state is replicated to players; keep payment and private
customer data out of it. Read the game skill's RULES.md before changing game outcomes.

## Default: Stripe's official plugin

Use Stripe's official plugin, authenticated with its browser OAuth approval, for Products,
Prices, Payment Links, menu links, per-slot booking links, monthly giving and the customer
portal. Install with `stripe agent setup` if needed; the MCP URL is
`https://mcp.stripe.com`. Current tools are `stripe_api_search`, `stripe_api_details`,
`stripe_api_read` and `stripe_api_write`. Discover the operation and its schema before
calling it; tool argument shapes can change. See https://docs.stripe.com/mcp.

1. Create/check `shop.json`. Read the app's published slot records and supply the complete
   slot manifest described below. Select the owner's account and sandbox in Stripe's plugin;
   read `/v1/account` to record its account ID. Live mode only after the owner requests it.
2. Call Homie's `stripe_shop_plan` with `account`, `mode: "test"`, `slots` and
   `observations: []`. CLI equivalent: `homie-studio shop plan --have plan-input.json`.
   That JSON file contains the same fields. `operations` contains every independent
   operation currently ready, with method, path, parameters and create idempotency key.
   Execute the batch through Stripe's official plugin, then replan for dependent work.
   `next` remains the first operation for older clients.
3. Append `{ "method": "POST", "path": "…", "params": {…}, "body": <Stripe response> }`
   for **writes as well as reads**. Keep this setup's observations across batches.
   Product creation includes its default Price; link creation expands line items.
   Product and Price Search use studio/origin metadata. Payment Links use paginated
   list reads with `expand[]=data.line_items`, then filter studio/origin metadata locally;
   Stripe has no Payment Link metadata search. There is no per-link read loop.
   The planner saves public observations in `.studio/stripe-mcp-observations.json` and
   reuses them on the next call; send only new responses. Keep that file and
   `.studio/stripe-mcp.json` when moving computers. Changed shop/slot settings refresh
   mutable links while retaining product/price discovery. Account, mode and origin
   changes start separate reads. Pass `refresh: true` for Dashboard changes or a fresh
   verification before webhook installation (CLI: include it in `--have` input).
   Follow search `next_page` and list `starting_after` cursors. On an uncertain write,
   retry its exact idempotency key; never discard successful responses or invent IDs.
4. Call `stripe_shop_plan` with `verify: true` using those observations (CLI
   `homie-studio shop verify --have plan-input.json`). Verification checks real fields,
   line items, menus, slot limits and portal settings. It saves compact public Worker
   configuration and provenance to `.studio/stripe-mcp.json`, never API response history.
   Build writes public links to `site/dist/_site/stripe-shop-links.json`; deploy ships
   that asset, with only its path in Wrangler vars. Large catalogues never use a text
   binding. Deploy after verifying, including when setup began on an already-live site. Checkout then reports only `webhook-secret` missing;
   it cannot open until signed payment events can confirm orders. Changing shop.json,
   the slot manifest or origin requires verification again. Local test configuration
   goes to `.dev.vars`.
5. For a deployed HTTPS studio, run `stripe_webhook` (CLI `homie-studio shop webhook`).
   Follow `studio_job`. This uses Stripe CLI only for private webhook installation,
   checks the same account as the MCP, and installs only the signing secret through
   Wrangler stdin. If Stripe CLI is missing, the tool installs the official
   `@stripe/cli@latest` npm package automatically, checks the executable, then continues.
   An installation failure reports npm permissions/PATH and a retry command. The CLI
   needs one separate browser approval if its
   studio profile is not already connected. MCP approval cannot be reused or exported.
   Cloudflare authorization and an existing deployment are prerequisites.
6. After installation, perform the returned `retire` operations through Stripe MCP to
   archive replaced catalog objects. Use fresh scoped reads for later drift checks. Test a sandbox
   purchase and its signed event, order grant, booking capacity or recurring invoice;
   a browser return is never proof. Stripe CLI `trigger` can send a test event, and
   `events resend <event> --webhook-endpoint <endpoint>` retries a delivery. Check the
   endpoint's delivery result and the app's verified records. Do not type a card into
   a page for an automated proof; use Stripe's documented test PaymentMethods/fixtures.

Upgrades accept 0.51.6 verifications without a source fingerprint only when their
saved content fingerprint still matches the current shop, slots, site and mode.
Actual changes name the affected settings and require verification. An unfinished
setup still builds and deploys with checkout closed and one next step: finish
`stripe_shop_plan` with `verify: true`. Missing/unreadable assets also close checkout;
old link secrets cannot reopen it. Cached observations never renew the verification
time; use fresh reads if the private webhook tool requests them.

Never create a webhook through model-visible Stripe MCP: its response exposes the signing secret.

**Why the separate approval (checked 2026-10-14).** Stripe's
[event destination API](https://docs.stripe.com/api/v2/core/event-destinations/create)
also returns its signing secret only in the private create response when explicitly
included. Thin events still require signature verification and authenticated retrieval
of event details; they do not supply a secret handoff to Wrangler. The
[official MCP](https://docs.stripe.com/mcp) documents no credential or secret transfer
to a studio Worker. Therefore the AI starts `stripe_webhook`, the owner clicks
Approve once in Stripe's CLI browser page if needed, and the tool completes endpoint
creation and Wrangler secret installation privately. MCP approval and CLI approval
are separate. No API key is requested, no secret enters chat, and Homie is never in
the money path. A connected studio CLI profile needs no further approval.


The owner never handles an API key or signing secret. No Homie backend handles payments.
The Worker needs only public link configuration and the signing secret; buyers pay
Stripe directly even when the AI and the owner's computer are offline. The old
`stripe_login` / `shop connect` flow remains an alternative that syncs everything
through Stripe CLI browser approval. `--renew` renews that approval; `--live` requires
the owner's go-live request. Never read CLI config or print login-completion output.

For local checkout, pass `url: "http://localhost:8787"` (or the private Wi-Fi address)
and `mode: "test"` to the same plan/verify flow; the official plugin makes the links.
Run `homie-studio shop listen --profile <sandbox-profile>` in a background terminal.
Stripe CLI is required for forwarding; one browser approval is enough if needed.
The command captures and saves the listener secret privately. Start/restart
`homie-studio dev --lan` once it reports ready and keep the listener running.
Never copy the listener's raw output into the conversation.

For a faster local iteration, `homie-studio build --quick` skips generated rules play
and the snapshot smoke-run, while retaining compilation, guards and type checks.
Run a full build before release; quick output is not evidence that play checks passed.

## Do

| The person says | Run | What happens |
|---|---|---|
| "Sell a supporter pack for $5" | `npx --no-install homie-studio shop init --supporter` (then `shop check`) | `shop.json` with a US$5 Supporter pack (a badge on their profile and beside their name in rooms, for a year; it changes nothing about play) and `SELLING.md`. Commit both. |
| "Sell a skin / a season pass / the full game" | edit `shop.json` `items` (`kind`: `cosmetic`, `pass`, `unlock`; `price` in Stripe currency units; `gives`: the keys the game reads), `shop check`, then the official MCP plan/verify flow again | Kinds are studio labels, without a fixed list. `"advantage": true` follows the studio policy for beginner and kids servers. Homie sets no price ceiling. |
| "Let people tip" | an item `{ "kind": "tip", "price": "choose", "min": 200, "max": 5000 }` | Pay what you want; amounts follow Stripe currency requirements, and max is optional and chosen by the studio. |
| "Make the products in Stripe" | `stripe_shop_plan` | Idempotent Product, Price, Payment Link and webhook sync from shop.json; no secret enters tool output. |
| "Connect my Stripe" / "turn the shop on" | `stripe_shop_plan`, then `stripe_webhook` | Approve Stripe once if needed; the Worker receives links and the signing secret only. Follow the single next step returned. Live only when requested. |
| "Is tax set up?" | `stripe_api_read` `GET /v1/tax/settings`, and `GET /v1/tax/registrations` | Seller "stripe": Stripe Tax needs `status: active` (the business address in Settings, Tax), or checkouts fail; with no registrations it collects no tax anywhere: say so, the accountant decides where to register. Seller "stripe-managed": Stripe files the tax; the connect page's test checkout said whether Managed Payments is on. Change nothing yourself. |
| "Is the shop working?" | `npx --no-install homie-studio shop` | Open (test or live) or exactly what is missing, the last 30 days, the webhook address. |
| "How are sales?" / "Show me the sales" | `shop` and `shop orders` first (the studio's own books); with Stripe's MCP, read-only: `stripe_analytics`, or `stripe_api_read` on `/v1/balance`, `/v1/payouts`, `/v1/checkout/sessions` | Counts, money and payouts in a few lines; never a buyer's name, email or card. Never a write to answer a question. The owner's `/_studio/office/shop` links every Stripe page and gives the accountant a CSV. |
| "Refund that player" | The owner’s official Stripe connection, or link their Stripe Dashboard payment | Honor Stripe’s confirmation link; signed events update the books and revoke fully refunded items. The keyed way still offers office refunds. |
| "Someone charged back" | nothing to undo: the owner answers it in Stripe (the office links it) | While open nothing changes; lost: that one item goes; won: it stays. **The account is never locked or deleted over a dispute.** |
| "Show the item in the game" / "the supporter badge" | in the game: `createShop()` from `@homie-rocks/studio/shop`; `shop.has('skin:ember')`, `shop.on('change', …)`, `shop.open('ember-skin')` from a button the player pressed, `shop.used(key)` when equipped | The play shell answers for the signed-in player; a badge rides on their seat as `peer.badge` (the Worker sets it, never a hello). |

## Your shop, your choices

The default is open: guests buy repeatedly without an age question, with any wording or kind, from any page.
`shop init` writes no policy. A released shop file without a preset now uses the open default.
Write `"policy": { "preset": "protective" }` to retain earlier account and age behavior.
`adults-only` is another optional bundle. Neither scans content. SHOP.md lists individual overrides.

The studio can set items, quantities, prices, tip ranges, entitlements, sale dates, currency, optional
`automaticTax`, `capPerPlayerMonth`, `refundDays` and configurable flood protection.
No toolkit amount or duration ceiling applies. Stripe currency constraints and safe integer arithmetic apply.
A refund window includes used items unless `policy.refundUsedItems` is false. A player cannot refund a tip;
the owner can refund through Stripe; keyed shops also offer office refunds. Guest purchases stay owned when the buyer signs in later.

For menus or explicitly keyed shops, carts: `shop.add(item, quantity, amount?)`, then `shop.checkout()`; `shop.buy(item)` buys directly.
Free and paid lines share one order and one Stripe Session. The studio chooses where to open the shop.

## The first sale (the acceptance)

In test mode: buy the supporter pack on a phone with Stripe's test card `4242 4242 4242 4242`, see "It's yours",
see the badge on the account page and beside the name in a room (from the next room the player joins), refund it
in Stripe (or through the connected AI), and see the badge go. With the protective preset, a kids server's room shows no shop and `/<game>/tv` shows only a code.

Keyless menus offer several fixed-price items with adjustable quantities on Stripe.
Custom amounts and monthly preset gifts have their own links. Free orders stay local.
A missing webhook stays pending; ask Stripe to resend it. Never grant from a return
URL. Keyless has no exclusive unpaid hold or custom session expiry. Consult SHOP.md
for menu limits, signed invoice fulfilment, slot sync and honest pending/full wording.

For a cause, use `shop init --giving --currency <organisation currency>`: one-time and monthly suggested gifts, no badge or game access. Read `giving.receiptText` from the organisation; leave it empty until provided. Local /shop/ previews before Stripe. Monthly gifts use the existing keyless Payment Links connection and Stripe handles renewals.

## App payment references

Create the booking/ticket/gift intention first. `shop.buy('full-tune', 1, undefined, { reference: booking.id })` or `shop.checkout({ reference: booking.id })` sends the app's own reference through checkout. Existing boolean returns are unchanged: checkout opened is not paid. The verified durable `order.paid` event carries `data.order`, `data.reference` (null if omitted) and `data.app`. Reopened Payment Links retain the reference. A reference is buyer-supplied correlation, not authorization: verify the record, app, amount and currency, deduplicate by event/order ID, then fulfil it. Keep personal data out of references. Before Stripe is connected, local prices and unpaid requests can be demonstrated; actual payment and recurring collection remain unverified. Test events must be labelled simulations.

For referrals, use Stripe Connect to split payments or a Stripe-based affiliate service; Homie builds none.

## Earning with the keyless default

Read SHOP.md for a round to table 7, `shop.book` and $20 monthly giving.
Menus let guests choose several quantities on Stripe; signed invoices provide actual
paid lines and the app reference. Slot Payment Links enforce completed-session
capacity. Pending guests do not block others. The owner's AI syncs published slots
with `stripe_shop_plan` and the complete slot manifest; the app shows Full from verified availability.
Recurring Prices provide monthly preset gifts and memberships. Connect enables the
no-code customer portal login through Stripe's API, without a Dashboard toggle.
Paid invoice periods govern membership; failed renewal never extends it.
The giving starter opens real keyless Checkout and shows a disabled preview before
connection. It never counts an intention as a gift.

For real sandbox acceptance use `startKeylessStripeSandbox` from the installed
`lib/dev-stripe-sandbox.mjs` as documented in SHOP.md. Only its explicitly authorised
sandbox CLI profile creates Stripe objects. No Worker API key. Keep returned signing
secret bindings private and temporary. Complete payments with Stripe's published
CLI fixture/API tokens; never enter card digits into a page. The local listener is
for development; production sends signed events directly to the studio's webhook.
The optional keyed fixture remains available for testing explicitly selected session
checkout. Label offline fixtures simulations.

## Local Stripe test payments

Use `shop connect --local --profile <sandbox-profile> --url http://<Wi-Fi-IP>:8787`
and Stripe CLI `listen --all-snapshot --forward-to http://localhost:8787/api/shop/hook`. The full
recipe is in the installed toolkit’s `apps/APPS.md`, “Real Stripe test checkout on
this computer”. It uses root `.dev.vars`, needs no public HTTPS or Cloudflare, and
keeps the existing approved Stripe CLI session. Do not write a stand-in checkout.

### Batch setup and reconciliation

Set each menu item's `maxQuantity` in `shop.json` when the studio has an order limit; the default is 99. Slot links support group quantities up to published remaining seats. Supply reviewed `confirmed` seat totals when resyncing: Stripe counts sessions, not people. The database confirms the entire paid group atomically. If a payment differs from the saved deposit/basket or a group no longer fits, inspect the `review` order and `payment.review` event, arrange fulfillment or refund, and show the customer the saved notice. Never discard a paid event.

Full `shop connect` and plugin verification both save public JSON assets; rebuild/deploy those assets before retiring replaced links. Checkout mode is a public Worker variable, not a secret. If a product search misses an existing deterministic ID, perform the planner's GET for that ID before creating it. Preserve Wrangler's diagnostic when setup fails.
