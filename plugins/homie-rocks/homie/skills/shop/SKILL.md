---
name: shop
description: Sell things in a Homie studio's games with the studio's OWN Stripe - a supporter pack, cosmetics, a season pass, a one-time unlock, a tip - in real money, with Stripe Checkout, Stripe Tax or Stripe Managed Payments, refunds from the office, and the kids rules built in; set up with Stripe's own agent tools (Stripe's MCP server and skills) so the owner only makes the account, approves Stripe's pages and pastes one key. Use when someone asks to sell something, add a shop or store, take payments or donations, make money from a game, set up or connect Stripe, make the products in Stripe, asks "how are sales?", about tax or Managed Payments, to add a supporter badge, refund a player, or about chargebacks, referral shares or affiliate links between studios.
compatibility: The studio's own pinned toolkit (@homie-rocks/studio 0.24.3 or later) and Wrangler. Stripe's own agent plugin (its MCP server and skills) once the studio sells, signed in by the owner on Stripe's page.
metadata:
  providers: stripe
---

# The shop

Needs `@homie-rocks/studio` 0.24.3 or later (`npx --no-install homie-studio upgrade --apply`, then deploy).
The guide is `node_modules/@homie-rocks/studio/shop/SHOP.md`; the owner's plain words are `SELLING.md`.

**The model, said plainly to the person.** The studio sells with **its own Stripe account**. The studio is the
seller: its prices, its refunds, its disputes, its tax. Money goes straight from players to the studio's Stripe;
**homie.rocks never sees it, holds it or moves it, and Homie takes no cut.** There is no shared currency between
studios. This is not legal or tax advice; for selling for real, the owner asks an accountant where to register.

## Stripe's own tools (set up when the studio starts selling)

Homie leans on Stripe's official agent tooling instead of copying it. Nothing is installed up front; when a studio
first sells (`shop.json` exists, and `setup status` shows a **Stripe** row), offer:

```sh
npm install -g @stripe/cli@latest && stripe agent setup
```

It installs **Stripe's agent plugin** for the agents on this computer (Claude Code: `stripe@claude-plugins-official`;
Codex: `stripe@openai-curated`): Stripe's MCP server (`https://mcp.stripe.com`) and Stripe's skills, kept up to date.
The person approves the install. By hand instead: `claude mcp add --transport http stripe https://mcp.stripe.com/`, or
`codex mcp add stripe --url https://mcp.stripe.com`; in the Claude app, Stripe's connector. Then the person signs in
once on **Stripe's consent page** (Claude Code: `/mcp`, stripe) and gives access to **a sandbox first**: a live account
only when they say the shop goes live, and then read access is enough for everything but the catalog.

- **Already connected in the Claude app?** Stripe's connector there is the same MCP server, and a Claude Code session
  signed in to the same Claude account lists it (its tools are named `claude_ai_Stripe`): no plugin is needed. If
  there it offers only an `authenticate` tool, its answer is Stripe's page for the owner to approve, once; you never
  approve it for them.
- **Before any write, check where you are:** `get_stripe_account_info`, and say in one line which account it is and
  whether it is a sandbox. If the grant reaches the wrong account (another business of the owner's), or live when you
  are setting up test mode, stop and ask; the owner changes it on Stripe's page (user settings, OAuth sessions).
- **OAuth is the way.** An agent that cannot do OAuth uses an **Agent key** (a restricted key Stripe marks "Agent",
  made for "Authorizing agent access"), from an environment variable, never pasted in the chat. **From 2026-10-31
  Stripe's MCP refuses every other key** (full secret keys, restricted keys without the Agent tag). That date does not
  touch the shop's own key in the Worker, which is a plain restricted key and must stay one.
- The MCP's tools here: `stripe_api_read` / `stripe_api_write` (any API method; `stripe_api_search` and
  `stripe_api_details` find them), `stripe_analytics`, `get_stripe_account_info`, `search_stripe_documentation`.
- **Stripe asks a person before risky writes** (refunds, money going out): its answer is a link. Give the link to the
  owner, wait until they say they approved it, then make the same call again. Never route around it.

## Never

- Never ask for a Stripe key, a webhook secret or any password in the chat, and never write one into a file, a
  command line, a commit or a log. The shop's key goes in only through `homie-studio shop connect` (a page on the
  owner's own computer).
- **Never make a webhook endpoint or an event destination through Stripe's MCP**: Stripe answers its signing secret
  in that call, and it would land in the conversation (the Homie mod in Claude Code and Homie's hooks in Codex refuse the call). The connect
  page makes the webhook with the shop's key, and the secret goes straight to the Worker. Never make or reveal an API
  key through any tool either: keys are made by the owner in Stripe's Dashboard.
- Never touch a Stripe account with the Stripe CLI's own login, an `sk_`/`rk_` key in the environment, or any other
  login you find on the computer. Only the owner's own pages, Stripe's MCP as the owner signed it in, and the
  studio's own Worker talk to Stripe.
- Never refund, mark a referrer paid, or switch to live keys by yourself: you **ask**, the owner taps. Never write to
  a live account, change tax settings or registrations, Managed Payments, payouts or bank details: those are the
  owner's, in Stripe. Reading them is fine.
- Never sell anything random (loot boxes, mystery crates, spins), never a currency (gems, coins, points), never a
  countdown, never pay-to-win on a beginner or kids server, never anything on a kids server or in a studio made for
  children. The kit refuses these anyway; do not look for a way around it.
- Never put a buy button on the play, start or wake button, never open the shop on a timer, never word a sale at
  children ("ask your parents!"). The television never sells.

## The owner's steps, for a creator with a fresh Stripe account

Say these as they come, one or two at a time. Everything else is yours.

| # | The owner | You |
|---|---|---|
| 1 | Makes a Stripe account (https://dashboard.stripe.com/register) and confirms the email. A sandbox works at once; selling for real waits for step 7. | `shop init --supporter` (or their items), `shop check`, commit, `npm run deploy` (migration 0008; the shop stays closed). |
| 2 | Approves Stripe's sign-in page once and picks **a sandbox** (or has connected Stripe's connector in the Claude app already). | `npm install -g @stripe/cli@latest && stripe agent setup` (they approve the install), then `/mcp` (Claude Code); with the Claude app's connector, nothing to install. Then `get_stripe_account_info`: the right account, its sandbox. |
| 3 | Nothing. | The catalog: `shop catalog`, the read it names with `stripe_api_read`, then `shop catalog --have <saved answer>` and each `stripe_api_write` it lists, until it says in sync (shop.json gets `"catalog": ["test"]`; commit, deploy). Then the tax check below. |
| 4 | Makes **one restricted key** in the sandbox (Developers, API keys, Create restricted key; not "Authorizing agent access") with the permissions the page lists, and pastes it into the page on this computer. Optional, recommended: afterwards sets the key's Webhook Endpoints back to None. | `shop connect` (test mode) and give them the 127.0.0.1 link. The page makes the webhook with that key; key and secret go straight to the Worker. Then `stripe_api_read` `/v1/webhook_endpoints`: the endpoint it named (`we_…`) must be there; if not, the MCP is signed in to another account or sandbox than the key. |
| 5 | Buys their own item on a phone with Stripe's test card `4242 4242 4242 4242`, then presses **Refund** in `/_studio/office/shop`. | `shop` (open, TEST MODE), and the acceptance below. |
| 6 | Picks who the seller is (on the connect page): the studio (Stripe Tax) or Stripe (Managed Payments). | For Managed Payments: the connect page tried one test checkout with it and said whether Stripe took it. |
| 7 | **Live, only when they say so:** activates the account in Stripe (business, bank, identity: theirs alone; Managed Payments also needs its terms accepted and Stripe's eligibility review), gives Stripe's MCP access to the live account, and makes a **live** restricted key on the connect page. | `shop catalog --mode live` the same way (writes to live only now), then `shop connect --live`. A real purchase and a refund from the office. |

## Do

| The person says | Run | What happens |
|---|---|---|
| "Sell a supporter pack for $5" | `npx --no-install homie-studio shop init --supporter` (then `shop check`) | `shop.json` with a US$5 Supporter pack (a badge on their profile and beside their name in rooms, for a year; it changes nothing about play) and `SELLING.md`. Commit both. |
| "Sell a skin / a season pass / the full game" | edit `shop.json` `items` (`kind`: `cosmetic`, `pass`, `unlock`; `price` in cents; `gives`: the keys the game reads), `shop check`, then `shop catalog` again | Real money only. An item that changes how the game plays gets `"advantage": true`: never sold or counted on beginner servers. Under US$3 the check warns: fees eat it. |
| "Let people tip" | an item `{ "kind": "tip", "price": "choose", "min": 200, "max": 5000 }` | Pay what you want between min and max. |
| "Make the products in Stripe" | `shop catalog`, then the read with `stripe_api_read`, then `shop catalog --have <file>` | The exact `stripe_api_write` calls still needed (one Product an item, id `homie_<studio>_<item>`, with a tax code and a default Price of shop.json's amount); a changed price is a new Price made the default; a removed item is archived, never deleted. In sync, shop.json `catalog` records the mode and checkouts name the Products. shop.json's price is always what is charged. |
| "Connect my Stripe" / "turn the shop on" | `npm run deploy`, then `npx --no-install homie-studio shop connect`; give the owner the 127.0.0.1 link | One restricted key (Checkout Sessions: Write, Charges: Write, PaymentIntents: Read, Disputes: Read, Webhook Endpoints: Write), pasted on the page; the page makes the webhook to `<site>/api/shop/hook` with it and asks **who is the seller**: the studio (Stripe Tax on) or Stripe (Managed Payments: 3.5% more). TEST keys only; `--live` only when the owner says the shop is ready to sell for real. A key without Webhook Endpoints: the page takes a webhook secret the owner made themselves. |
| "Is tax set up?" | `stripe_api_read` `GET /v1/tax/settings`, and `GET /v1/tax/registrations` | Seller "stripe": Stripe Tax needs `status: active` (the business address in Settings, Tax), or checkouts fail; with no registrations it collects no tax anywhere: say so, the accountant decides where to register. Seller "stripe-managed": Stripe files the tax; the connect page's test checkout said whether Managed Payments is on. Change nothing yourself. |
| "Is the shop working?" | `npx --no-install homie-studio shop` | Open (test or live) or exactly what is missing, the last 30 days, the webhook address. |
| "How are sales?" / "Show me the sales" | `shop` and `shop orders` first (the studio's own books); with Stripe's MCP, read-only: `stripe_analytics`, or `stripe_api_read` on `/v1/balance`, `/v1/payouts`, `/v1/checkout/sessions` | Counts, money and payouts in a few lines; never a buyer's name, email or card. Never a write to answer a question. The owner's `/_studio/office/shop` links every Stripe page and gives the accountant a CSV. |
| "Refund that player" | `npx --no-install homie-studio shop refund <ord_…> --note "<why>"` | An ASK: give the owner the one-tap link (in the office their own Refund button does it at once). The item leaves the player's account; the money goes back in 5 to 10 days. If the owner asks you to refund through Stripe's MCP instead, Stripe answers with its confirmation link: theirs to approve; the webhook takes the item back when Stripe refunds. If a refund comes back "held", the shop's key is an Agent key: the owner approves it in Stripe (Settings, Approvals) and reconnects with a plain restricted key. |
| "Someone charged back" | nothing to undo: the owner answers it in Stripe (the office links it) | While open nothing changes; lost: that one item goes; won: it stays. **The account is never locked or deleted over a dispute.** |
| "Show the item in the game" / "the supporter badge" | in the game: `createShop()` from `@homie-rocks/studio/shop`; `shop.has('skin:ember')`, `shop.on('change', …)`, `shop.open('ember-skin')` from a button the player pressed, `shop.used(key)` when equipped | The play shell answers for the signed-in player; a badge rides on their seat as `peer.badge` (the Worker sets it, never a hello). |
| "Pay studios that send us players" / "affiliate links" | `shop.json` `referrals` (rate, window, hold), `shop statements [--send]` | A `?via=<host>` link from another site (homie.rocks is one more referrer, on the same terms) counts for a new player's purchases; statements are signed with the studio's key; the referrer invoices the studio; the owner pays and marks it paid (an ASK from you). Nothing moves through Homie. |

## Who may buy (the kit decides; tell the person)

A guest makes an account first (a passkey). Every account answers one neutral question once: the year they were
born (no default; kept only as adult, teen or child). Under 13: nothing, ever. 13 to 17: a one-time link a parent
opens on their own phone and pays in their own name. Adults: Stripe's own hosted page, one item at a time, with a
monthly cap (US$50 at most). A kids server shows no shop. A TV's store sheet is a code to buy on a phone.

## The first sale (the acceptance)

In test mode: buy the supporter pack on a phone with Stripe's test card `4242 4242 4242 4242`, see "It's yours",
see the badge on the account page and beside the name in a room (from the next room the player joins), refund it
from `/_studio/office/shop`, and see the badge go. A kids server's room shows no shop; `/<game>/tv` shows only a code.
