---
name: frugal
description: "Find the cheapest honest way to get what the user wants before money is spent: free tiers, right-sized plans, annual billing, startup, student, open-source or nonprofit programs, verified promo codes, cashback, refurbished, price history, negotiation, and cheaper or open-source alternatives. Use whenever a task involves paying, even if the user did not ask to save: buying, ordering, subscribing, upgrading, renewing, adding seats, finding or booking flights and hotels, signing up for paid tools (including ones a video or tutorial recommends), choosing a paid SaaS, API, LLM model, cloud, hosting or domain, or when a pricing, billing, cart or checkout page is open. Also for: where to buy, cheaper way, promo code, coupon, discount, deal, too expensive, cut our bill, קופון, הנחה, יותר זול. Effort scales with the amount; never pays by itself."
license: MIT
metadata:
  author: Nir Feinstein
  version: "1.0.1"
  homepage: https://github.com/fainir/frugal
---

# Frugal

Before money moves, spend a proportionate amount of effort finding the cheapest honest way to get
the same outcome. Report it in a few lines, let the user choose, then carry on with the task.

The user rarely asks for this. That is the point: most overspending happens because nobody looked.
A good frugal check costs the user ten seconds of reading and often saves 20 to 100 percent.

## When it applies

Run a check when money is about to be committed, by the user or by you:

- The user wants to buy, order, subscribe, upgrade, renew, add seats, book travel or hire a service.
- You are about to pick or recommend something billed: a SaaS, an API, an LLM model, a cloud
  resource, hosting, a domain, a paid library, a paid plan of a tool you are setting up.
- A pricing, plans, billing, upgrade, cart or checkout page is open in a browser tool.
- The user asks for a cheaper way, a coupon, a deal, or says a bill is too high.
- The user brings a plan from a video, course or "best tools" list and wants to sign up for its tools.

Shopping, flights and personal purchases are in scope while this skill is installed, even for a
coding agent: use web search and fetch to check live prices instead of declining or only listing
websites.

Skip it when the user said "just buy it" or "skip frugal" for this item, when the item was already
checked earlier in this conversation, when the employer or the user has already fixed the vendor and
plan, or when the whole spend is under about 5 USD (or local equivalent) and not recurring.

## Golden rules

1. **Never invent.** Every price, discount, code and program you state comes from a page you opened
   in this session. Label each one: **verified** (seen on the official page or applied in a cart),
   **reported** (recent user reports, with date), or **unverified**. Never make up a promo code.
   The files in `references/` are a map of where to look, not current facts: re-check them live.
2. **Honest eligibility only.** Offer a program only if the user qualifies or might ("if you are a
   student..."). Never suggest multiple accounts to repeat trials, false student, military or
   employee status, leaked or internal codes, a VPN to dodge regional pricing where the terms forbid
   it, exploiting price errors, or chargebacks. A saving that risks the user's account is not a saving.
   Never suggest opening a credit card, loan or buy-now-pay-later plan to get a discount: that is a
   financial decision with costs of its own. Offers on cards the user already has are fine.
3. **Same outcome.** A cheaper option counts only if it does the job the user needs. Always name its
   catch: missing feature, worse support, slower delivery, lock-in, migration work, used condition.
4. **Total cost, not sticker price.** Compare what the user really pays over the period that matters:
   renewal price after the intro offer, tax, shipping, currency and card fees, seat minimums, overage
   and egress, setup time, cancellation terms and auto-renewal.
5. **Effort in proportion.** Never spend more of the user's attention or your tool calls than the
   saving is worth. A 4 USD saving that needs a new account and 20 minutes is not worth suggesting.
6. **Money stays the user's call.** You find, compare, recommend and prepare. You never pay, enter
   card or bank details, or accept terms. Follow the host's purchase rules (most require an explicit
   yes in chat before any purchase). Entering a public promo code at a checkout the user asked you to
   complete is fine once they have said yes to that checkout.
7. **No affiliate games.** Link official pages. Never add referral or affiliate links of your own,
   and warn about tools known to swap affiliate codes or bury better coupons.
8. **Recommendations may be paid ads.** When the plan comes from a video, course, blog or "best
   tools" list, keep the ideas but check every paid tool pick against alternatives, price it after
   the trial, and redo any profit math with all costs in. Keep the creator's pick only if it wins.
   See [references/sponsored-advice.md](references/sponsored-advice.md).

## Step 0: Size it

Work out the annual cost: one-time price, or monthly price x 12 x seats or units. Pick the tier:

| Tier | Annual cost | Your budget | What the user sees |
|------|-------------|-------------|--------------------|
| Quick | under ~50 USD | 1 to 3 lookups | one line, maybe two |
| Standard | ~50 to 1,000 USD | 5 to 15 lookups | a short table, 2 to 5 options |
| Deep | over ~1,000 USD, a contract, team-wide or multi-year | 15+ lookups, parallel subagents if you have them | table plus negotiation plan and timing |

The budget is a cap, not a target. Count your searches and page fetches; when you reach the cap,
stop and report what you have, naming what you did not check. No subagents below the Deep tier.

For an open-ended "what should I get?" question, first pick two or three candidate products from one
or two trusted review sources, then price-check only those. Do not survey the whole market.

Use the user's currency and region. When the spend is a side effect of a coding task, keep the
check short and do not derail the main task.

## Step 1: Pin down the need (no lookups yet)

- **Exactly what:** product or plan, quantity, seats, usage level, region and currency, deadline.
- **What they already have:** subscriptions and bundles that may include it (Google One, Apple One,
  Amazon Prime, Microsoft 365, GitHub, a telecom plan), unused credits, credit card perks, employer
  perk portals, memberships (Costco, AAA, unions, alumni), a library card.
- **Eligibility facts:** student or teacher, startup (incorporated? funded? accelerator?),
  open-source maintainer, nonprofit, country, age, veteran. Read what is already known first: the
  profile file `~/.config/frugal/profile.md` if it exists, the agent's memory, CLAUDE.md or AGENTS.md.
- **Hard constraints:** brand, compliance, delivery date, what the team already uses.

Ask at most **one** question, and only when the answer could change the best option a lot (for
example "Are you a student? Figma would be free."). Otherwise show conditional options and move on.

## Step 2: Climb the ladder, cheapest first

Stop climbing when a rung already gives a clearly good answer for this tier.

1. **Don't pay.** Free tier that covers the real usage, open-source or self-hosted equivalent,
   something the user already owns or gets in a bundle, a public or library resource, a free trial
   that covers a one-off need (with a reminder to cancel).
2. **Pay less for the same thing.** Right-size the plan (seats, tier, usage band), annual vs monthly,
   usage-based vs flat, a cheaper seller of the identical item, refurbished, open-box or used for
   goods, timing (price history, sale calendar, end of quarter for B2B).
3. **Programs.** Startup credits, student and education, open-source maintainer, nonprofit,
   government, military and first responder, employer and membership discounts.
   See [references/programs/README.md](references/programs/README.md): it points to one file per
   audience and lists programs that closed or got worse.
4. **Codes and stacking.** Official promo pages, newsletter or first-order codes, referral credits,
   partner codes; then cashback portal, card-linked offers, discounted gift cards, price protection.
   See [references/promo-codes.md](references/promo-codes.md).
5. **Ask.** Sales discount for annual or multi-seat, startup or nonprofit discount on request,
   retention offer before cancelling, price match or price adjustment.
   See [references/negotiation.md](references/negotiation.md).
6. **Switch.** A cheaper product or service with the same outcome, or a different approach (an
   open-source tool, a different architecture, a cheaper model).
   See [references/alternatives.md](references/alternatives.md).

Category playbooks, read only the one you need:

| Spending on | Playbook |
|-------------|----------|
| SaaS, software licenses, dev tools | [saas-and-software.md](references/playbooks/saas-and-software.md) |
| AI subscriptions, LLM APIs, coding agents | [ai-and-llm.md](references/playbooks/ai-and-llm.md) |
| Cloud, hosting, domains, email | [cloud-hosting-and-domains.md](references/playbooks/cloud-hosting-and-domains.md) |
| Electronics, goods, household | [shopping-and-electronics.md](references/playbooks/shopping-and-electronics.md) |
| Flights, hotels, cars | [travel.md](references/playbooks/travel.md) |
| Streaming, apps, phone, internet, insurance | [subscriptions-and-bills.md](references/playbooks/subscriptions-and-bills.md) |
| Starting an online store or dropshipping | [online-store-and-dropshipping.md](references/playbooks/online-store-and-dropshipping.md) |

## Step 3: Verify before you report

- Open the official pricing or product page and note the current price and today's date.
- **Promo codes:** official source first (vendor promo page, newsletter, partner page), then recent
  user reports (last 30 days, with "worked" confirmations), then aggregators. A code from an
  aggregator alone is **unverified**: list at most two and say so. Applying a code in a cart preview
  is the only way to mark it **verified**, and only if you are already allowed to use that cart.
- **Programs:** read the current eligibility rules and status. Programs change and close.
- **Alternatives:** confirm current pricing and that the must-have features exist.

## Step 4: Report

Quick tier: one or two lines, then continue the task.

```
Frugal check: Notion Plus is free for students with a school email (verified, notion.com/students). Want me to use that?
```

Every option, price and claim in the report needs a source you opened, or the label
**unverified**. Do not state hearsay as fact ("sales usually give 50 percent off"): either find a
source or phrase it as an untested ask ("worth asking sales for a startup discount").

Standard and Deep tiers:

```
Frugal check - <item>, baseline <price> (<annual cost>)

| # | Option | You pay | Saves | Effort | Catch | Source |
|---|--------|---------|-------|--------|-------|--------|
| 1 | ...    | ...     | ...   | 2 min  | ...   | link, verified |

Best pick: <option> - <one sentence why>.
Needs you: <one eligibility question or one approval, if any>.
```

If nothing beats the baseline, say so in one line and list what you checked:
`Frugal check: nothing cheaper that does the same job (checked: annual plan, startup program, two alternatives).`
That is a valid, useful result. Then carry on with what the user asked.

## Step 5: Follow through

- When the user takes a saving, append one line to `~/.config/frugal/savings.md` if that folder
  exists: `date | item | baseline | paid | saved | how`. If the user asks what frugal has saved them,
  total that file.
- Offer reminders that protect the saving: trial end, intro price expiry, renewal date, a price-drop
  watch. Use the host's scheduler if there is one, otherwise put the date in the reply.
- When the user reveals an eligibility fact (student, startup, country), offer to save it to the
  profile file so the next check is faster. Never store card numbers, IDs or passwords there.

## When you are the one spending (coding and ops work)

You choose paid things all the time while building. Apply the same rules without being asked:

- Prefer free tiers and cost-effective defaults. When you add anything billed, state the expected
  monthly cost at realistic usage in your plan or PR description.
- **LLM calls in code:** the cheapest model that passes the task's evals, prompt caching for
  repeated context, batch APIs for anything not interactive, capped output tokens, cached results.
- **Cloud:** smallest size that works, scale to zero, spot or preemptible for batch jobs, budgets
  and alerts on, storage chosen with egress in mind. Estimate cost before creating resources
  (for example with `infracost` for Terraform).
- Don't add a paid SaaS when a library, a built-in feature or a free tier does the job.

## Never

- Long reports for small spends, or repeating the check every message.
- Presenting a stale catalog value as current.
- Pushing the user to sign up for several services to save a few dollars.
- Fake urgency ("only today!") unless the deadline is real and sourced.
- Completing a purchase, entering payment details, or accepting terms yourself.
