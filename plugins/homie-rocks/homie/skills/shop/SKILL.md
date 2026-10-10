---
name: shop
description: Sell things in a Homie studio's games with the studio's OWN Stripe - a supporter pack, cosmetics, a season pass, a one-time unlock, a tip - in real money, with Stripe Checkout, Stripe Tax or Stripe Managed Payments, refunds from the office, and optional studio policies with an open default; set up with Stripe's own agent tools (Stripe's MCP server and skills) with one browser approval and Payment Links by default, no human-handled key and no API key in the Worker. Use when someone asks to sell something, add a shop or store, take payments or donations, make money from a game, set up or connect Stripe, make the products in Stripe, asks "how are sales?", about tax or Managed Payments, to add a supporter badge, refund a player, or about chargebacks, referral shares or affiliate links between studios.
compatibility: The studio's own current toolkit with stripe_login or shop connect --renew, Wrangler, and the official Stripe CLI. Stripe's own agent plugin (MCP and skills) is optional for catalog work and analytics.
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

Check that the toolkit exposes `stripe_login`, or that `homie-studio --help` lists `shop connect` with `--renew` and `--manual`. An older toolkit's default is the paste page: upgrade before using this flow; do not send the owner to that old default.
The guide is `node_modules/@homie-rocks/studio/shop/SHOP.md`; the owner's plain words are `SELLING.md`.

**The model, said plainly to the person.** The studio sells with **its own Stripe account**. The studio is the
seller: its prices, its refunds, its disputes, its tax. Money goes straight from players to the studio's Stripe;
**homie.rocks never sees it, holds it or moves it, and Homie takes no cut.** The studio is responsible for the law where it sells and for Stripe's terms.

In a rules game, keep shop UI in the view. Do not turn a client character save, an
entity field or a command into proof of a purchase: grants still come from the shop's
verified server records. Room state is replicated to players; keep payment and private
customer data out of it. Read the game skill's RULES.md before changing game outcomes.

## Connect with Stripe's own browser approval

Use `stripe_login` (MCP) or `npx --no-install homie-studio shop connect`. Test mode and a
sandbox first. If the CLI is missing, run the one installation command the result gives:
`npm install -g @stripe/cli@latest`. The toolkit opens Stripe's page and completes its official
non-interactive login. Give the person the pairing code; they select their own account and approve.
Use `studio_job` for the background result. Do not call a raw CLI config command: it may print secrets.

The default is **keyless**: the toolkit uses the CLI's approved account to sync Products, Prices
(including custom amounts for tips), Payment Links and the webhook. It captures the signing secret
privately and installs it with the link configuration; it never exports the CLI credentials.
The Worker redirects buyers to Stripe and grants purchases from signed events. No desktop agent,
Homie service or API key is needed when someone pays. Run connect again after editing shop.json;
it updates changed objects and archives removed ones. Existing connections need no new approval.

Only when the person asks for combined carts, spending reservations, custom checkout expiry,
automatic recovery of lost webhooks or office refunds, explain one sentence:
“The fuller connection adds combined carts, spending limits, automatic recovery and refunds here.”
A pre-existing Worker key selects that path automatically. Never silently select `--manual` or ask
for a key: explain its remaining Dashboard step only if the person explicitly chooses that route.
Before relying on spending restrictions after switching, deactivate old Payment Links with the approved CLI and resolve in-flight checkouts; a credential change does not cancel them.
`shop connect` selects keyless again and removes an existing Worker API key after saving the links.

## Never

- Never ask a person for a Stripe key, a webhook secret or a password in chat. Never display a CLI
  config, credential response, environment value or raw login-completion output. The toolkit captures
  these privately. Keys belong to the studio; no Homie account or service takes payments.
- **Never make a webhook endpoint or an event destination through Stripe's MCP**: its signing secret
  would enter the conversation. `shop connect` handles endpoint creation and secret storage privately.
- Never silently select `--manual`. Only when the owner chooses the fallback, run
  `shop connect --manual` (or `--manual --live`) and give the local page link. The page explains the
  remaining Dashboard restricted-key step and creates the webhook automatically. This fallback
  requires copying a key and does not meet the one-approval target; say so plainly.
- Live mode only when the owner says go live. Account activation, tax, bank details and Stripe
  approval links are the owner's. Never approve a Stripe confirmation link for them.
- The studio chooses its settings. Omitted policies are open; choose a preset only when requested.

## The owner's steps, for a creator with a fresh Stripe account

With an existing Stripe account and deployed studio, there is **one Stripe approval** for the CLI;
if that CLI profile is already connected, there are **zero new approvals**. An existing MCP-only
consent is not a CLI login and is not exported or borrowed. Account creation/activation, an administrator
enabling CLI access, and an initial Cloudflare sign-in are separate Stripe/hosting requirements.

| The owner | You |
|---|---|
| Approves Stripe's browser page, selecting their studio account and sandbox. | Create/check shop.json; run stripe_login / shop connect; follow studio_job to completion. |
| Nothing. | Sync all items and the webhook, install the signing secret and links privately, then verify a test purchase and grant. |
| Requests a refund in Stripe or asks their connected AI. | Use the official Stripe connection, honor any confirmation link, verify the signed refund event removes the item. |
| Says “go live” and completes Stripe activation if needed. | shop connect --live in the authorized account; verify only an authorized real purchase. |

`shop connect --renew` restarts the approval flow when needed. CLI OAuth refresh is the CLI's job;
there is no runtime API credential to expire. `shop catalog` remains the optional older catalog planner
for keyed shops; keyless shops use connect for the complete catalog, links and webhook sync.

## Optional Stripe agent tools

For catalog work, analytics and advice, `stripe agent setup` installs Stripe's own agent plugin and
skills; its OAuth MCP is `https://mcp.stripe.com`. This is optional and separate from Worker credentials.
Check `get_stripe_account_info` before writes; confirm the account and mode match the studio.
For CLI refunds or event resends, use the non-secret `profile` returned by connect with `stripe --project-name <profile>`; preserve its test/live context. Do not read credentials.
The tools include `stripe_api_read`, `stripe_api_write`, API discovery and `stripe_analytics`.
From **2026-10-31**, MCP rejects API keys without the Agent tag; OAuth remains supported. Agent keys
can put refunds behind Stripe approval. A returned confirmation link belongs to the owner; wait
for approval before retrying. Do not silently replace the payment runtime with MCP; a separate persistent MCP client would need its own production verification.

## Do

| The person says | Run | What happens |
|---|---|---|
| "Sell a supporter pack for $5" | `npx --no-install homie-studio shop init --supporter` (then `shop check`) | `shop.json` with a US$5 Supporter pack (a badge on their profile and beside their name in rooms, for a year; it changes nothing about play) and `SELLING.md`. Commit both. |
| "Sell a skin / a season pass / the full game" | edit `shop.json` `items` (`kind`: `cosmetic`, `pass`, `unlock`; `price` in Stripe currency units; `gives`: the keys the game reads), `shop check`, then `shop connect` again | Kinds are studio labels, without a fixed list. `"advantage": true` follows the studio policy for beginner and kids servers. Homie sets no price ceiling. |
| "Let people tip" | an item `{ "kind": "tip", "price": "choose", "min": 200, "max": 5000 }` | Pay what you want; amounts follow Stripe currency requirements, and max is optional and chosen by the studio. |
| "Make the products in Stripe" | `shop connect` | Idempotent Product, Price, Payment Link and webhook sync from shop.json; no secret enters tool output. |
| "Connect my Stripe" / "turn the shop on" | `stripe_login` or `shop connect` | Approve Stripe once if needed; the Worker receives links and the signing secret only. Follow the single next step returned. Live only when requested. |
| "Is tax set up?" | `stripe_api_read` `GET /v1/tax/settings`, and `GET /v1/tax/registrations` | Seller "stripe": Stripe Tax needs `status: active` (the business address in Settings, Tax), or checkouts fail; with no registrations it collects no tax anywhere: say so, the accountant decides where to register. Seller "stripe-managed": Stripe files the tax; the connect page's test checkout said whether Managed Payments is on. Change nothing yourself. |
| "Is the shop working?" | `npx --no-install homie-studio shop` | Open (test or live) or exactly what is missing, the last 30 days, the webhook address. |
| "How are sales?" / "Show me the sales" | `shop` and `shop orders` first (the studio's own books); with Stripe's MCP, read-only: `stripe_analytics`, or `stripe_api_read` on `/v1/balance`, `/v1/payouts`, `/v1/checkout/sessions` | Counts, money and payouts in a few lines; never a buyer's name, email or card. Never a write to answer a question. The owner's `/_studio/office/shop` links every Stripe page and gives the accountant a CSV. |
| "Refund that player" | The owner’s official Stripe connection, or link their Stripe Dashboard payment | Honor Stripe’s confirmation link; signed events update the books and revoke fully refunded items. The keyed way still offers office refunds. |
| "Someone charged back" | nothing to undo: the owner answers it in Stripe (the office links it) | While open nothing changes; lost: that one item goes; won: it stays. **The account is never locked or deleted over a dispute.** |
| "Show the item in the game" / "the supporter badge" | in the game: `createShop()` from `@homie-rocks/studio/shop`; `shop.has('skin:ember')`, `shop.on('change', …)`, `shop.open('ember-skin')` from a button the player pressed, `shop.used(key)` when equipped | The play shell answers for the signed-in player; a badge rides on their seat as `peer.badge` (the Worker sets it, never a hello). |
| "Pay studios that send us players" / "affiliate links" | `shop.json` `referrals` (rate, window, hold), `shop statements [--send]` | A `?via=<host>` link from another site (homie.rocks is one more referrer, on the same terms) counts for a new player's purchases; statements are signed with the studio's key; the referrer invoices the studio; the owner pays and marks it paid (an ASK from you). Nothing moves through Homie. |

## Your shop, your choices

The default is open: guests buy repeatedly without an age question, with any wording or kind, from any page.
`shop init` writes no policy. A released shop file without a preset now uses the open default.
Write `"policy": { "preset": "protective" }` to retain earlier account and age behavior.
`adults-only` is another optional bundle. Neither scans content. SHOP.md lists individual overrides.

The studio can set items, quantities, prices, tip ranges, entitlements, sale dates, currency, optional
`automaticTax`, `capPerPlayerMonth`, `refundDays`, referral terms and configurable flood protection.
No toolkit amount or duration ceiling applies. Stripe currency constraints and safe integer arithmetic apply.
A refund window includes used items unless `policy.refundUsedItems` is false. A player cannot refund a tip;
the owner can refund through Stripe; keyed shops also offer office refunds. Guest purchases stay owned when the buyer signs in later.

For keyed shops, carts: `shop.add(item, quantity, amount?)`, then `shop.checkout()`; `shop.buy(item)` buys directly.
Free and paid lines share one order and one Stripe Session. The studio chooses where to open the shop.

## The first sale (the acceptance)

In test mode: buy the supporter pack on a phone with Stripe's test card `4242 4242 4242 4242`, see "It's yours",
see the badge on the account page and beside the name in a room (from the next room the player joins), refund it
in Stripe (or through the connected AI), and see the badge go. With the protective preset, a kids server's room shows no shop and `/<game>/tv` shows only a code.

Keyless purchases buy one item type at a time, with quantity confirmed on Stripe. Tips choose the
amount on Stripe and always have quantity one. Free orders grant locally without Stripe.
Refund and dispute snapshots are stored by provider object ID and tolerate retries and reordering.
A missing webhook stays pending: ask Stripe to resend the event (Dashboard or official CLI
`stripe events resend <event> --webhook-endpoint <endpoint>`). Never grant based on the return URL.
Payment Links are public and reusable; do not promise that local sale dates, repeat-purchase or
eligibility checks revoke a previously opened link. Deactivation stops new sessions after re-sync;
already opened sessions may still complete. Strict pre-payment enforcement needs the keyed way.
Stripe always enables Adaptive Pricing on Payment Links; the buyer can use the original currency.
Keyless has no per-session expiry or provider-read reconciliation. The keyed path retains both,
carts, cap reservations, local refunds. Managed Payments is supported on Payment Links when Stripe enables it for the account. The studio chooses its needs.
