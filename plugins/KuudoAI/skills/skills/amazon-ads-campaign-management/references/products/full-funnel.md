# Full-Funnel campaigns on v1

`adProduct`: `FULL_FUNNEL`. A Full-Funnel campaign is one Amazon-orchestrated campaign that runs sponsored ads, display, video, and streaming TV together. The advertiser supplies budget, products, and creative, plus an optional ROAS threshold. Amazon's AI chooses the formats, audiences, bids, and how the budget is split. Amazon announced it on 2026-09-29 as available to US advertisers, built and managed in Amazon Ads Agent at advertising.amazon.com. One agency report from November 2026 still describes it as beta, limited to one active Full-Funnel campaign per advertiser.

## What the server exposes (checked 2026-11-21)

- `FULL_FUNNEL` appears only in the merged `allv1_*` schemas. There is **no product-scoped tool family** (no `ffv1_*`), and the non-merged `cm_*` tools leave it out of their `adProduct` enum. So unlike the other products, there is no authoritative per-product schema to build or check a request against.
- *Observed:* Amazon accepts `adProductFilter: {include: [FULL_FUNNEL]}` on `allv1_QueryCampaign`, `allv1_QueryAdGroup`, `allv1_QueryAd`, and `allv1_QueryTarget`. On a profile with no Full-Funnel campaign, each returned an empty list, not an error.
- No Amazon API documentation for Full-Funnel was found. Required fields, mutable fields, and batch limits are unknown.

## Capabilities

| Operation | Status | How |
|---|---|---|
| Query campaigns, ad groups, ads, targets | **Supported** (filter accepted, observed) | `allv1_Query*` with `adProductFilter` `FULL_FUNNEL`; the other filters as for any product |
| Create a campaign | **Not through this skill** | No documented API contract. Point the user to Amazon Ads Agent in the console |
| Update an existing campaign | **Unverified contract**; gated, see below | `allv1_UpdateCampaign` |
| Edit ad groups, ads, targets | **Don't** | Amazon manages them; hand edits fight the orchestration |
| Delete (archive) | **Unverified**; pause is the safe default | Offer pause first, as for every product |

## Reading

Query the campaign, then its children by `campaignIdFilter`, and report them as Amazon-managed. Expect structure you can't set yourself: channel or format-level ad groups and Amazon-chosen audiences. Read rows can contain fields that no other product uses. Report them verbatim and don't infer meaning beyond the field name. Results such as spend, sales, new-to-brand, and long-term sales belong to `amazon-ads-reporting`.

## Updating an existing campaign

Only campaign-level settings the user owns are candidates: `state`, `name`, `endDateTime`, and the budget. Each update needs the normal gate plus three extra conditions:

1. **Read the campaign first** and change only fields that appear on that read-back. Don't send a field that is merely in the merged schema; the merged schema is a union across products, not the Full-Funnel contract.
2. **Budget: mirror the read-back object.** With no product-scoped tool, the write goes through `allv1_UpdateCampaign`, whose budget item requires `recurrenceTimePeriod` and `monetaryBudget.currencyCode`. Copy the `budgets` array exactly as read, including recurrence and currency, and change only `value`. If the read-back lacks either required field, stop: the write can't satisfy the merged schema without guessing, so say so and point the user to the console. Amazon's reported daily minimum ($100 per day in third-party coverage, not confirmed on an Amazon page) may reject a lower value.
3. **Say the contract is unverified in the preview.** Tell the user that Full-Funnel has no published API contract on this server, that Amazon may reject the field, and that the read-back is the only proof of the result. Amazon's AI needs about two weeks to recalibrate after changes, so flag that frequent edits can reset learning.

If Amazon rejects the update, report the code and field and stop. Don't retry with other field shapes: the console is the supported editing surface.

## Routing

- "Launch a Full-Funnel campaign": explain that creation lives in Amazon Ads Agent in the console. No API path is documented, and `amazon-ads-create-dsp-campaign` covers DSP Performance+ and Brand+, not Full-Funnel.
- Full-Funnel performance and results: `amazon-ads-reporting`.
