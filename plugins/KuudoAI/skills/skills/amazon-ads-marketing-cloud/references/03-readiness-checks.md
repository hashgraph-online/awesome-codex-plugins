# Readiness and scope

Run this before any analysis or audience draft. List anything you can't confirm under "What I need from you"; don't infer it. Being able to see an Ads report, for example, says nothing about AMC or audience access.

## 1. Account binding and access

Confirm, and record where each answer came from:

- The advertiser, Ads profile, and AMC instance belong together, and the instance covers the marketplace in question. Multi-brand sellers and agencies often have names that differ across the account, the profile, and the instance; reconcile them as SKILL.md → Pre-Flight Setup describes.
- Which of these states are actually in place. Each is independent of the others:
  1. The AMC instance is visible and finished provisioning.
  2. AMC terms are accepted for the advertiser. Accepting them is a binding legal action with its own flow (SKILL.md → Terms acceptance flow); never accept them as a side effect of planning.
  3. The user can edit the campaigns the plan would change.
  4. AMC audiences are available in the target console (DSP, Sponsored Display, or Sponsored Products and Sponsored Brands bid boosts) for this advertiser and marketplace.
- Who owns approval for audience creation and for campaign changes. They may be different people.

## 2. Data coverage

Record at least:

- The data's start and end dates, the query run time, the time zone, the currency, and the marketplace.
- Which ad products the instance holds, from its advertiser types rather than its table list. An instance with only sponsored ads may still list the DSP tables, and queries on them compile, but they hold no DSP data, so a question that needs DSP exposure can't be answered there.
- Which paid AMC features the instance has. Sizing or measuring on base `conversions_all` (purchases from shoppers with no recent ad exposure) needs one; audience queries on `conversions_all_for_audiences` don't. Without it, size on `conversions` and say the estimate covers ad-exposed shoppers only.
- How long the instance has existed. New instances backfill sponsored ads data over a few days.
- Conversion maturity. Attributed conversions keep arriving for up to two weeks, and some conversion tables lag longer. SKILL.md → Troubleshooting lists the current lags. Don't read a window that hasn't matured.
- The campaigns, ASINs, brand, and conversion event in scope, and the attribution or lookback rule behind each metric.
- Breaks in the series: campaigns renamed, rebuilt, or paused; promotions; price changes; stockouts; listing suppressions. Each one can masquerade as an audience effect.
- Audience size status and whether the current minimum audience size is met.

"No results returned" can come from filters, column choice, the table, the window, permissions, data latency, or aggregation thresholds (AMC drops output groups behind fewer than about 100 shoppers, so a small account over a short window often returns nothing). Check those before treating it as a business result, and don't assume the data must exist elsewhere.

## 3. Multi-marketplace accounts

Treat each marketplace as its own unit by default. This applies to the EU (UK, DE, FR, IT, ES, NL, SE, PL, BE, and others), North America (US, CA, MX), and the Far East (JP, AU, SG, and others) alike.

- Confirm instance, profile, currency, and time zone separately for each marketplace.
- Keep local language, price and tax basis, shipping, returns behavior, holidays, and promotional calendars distinct. A tentpole event (Prime Day, Black Friday, Singles Day, a national holiday) may fall on different dates or carry different weight in each marketplace.
- Compare within a marketplace first. Combine marketplaces only after defining the exchange-rate date, a pre-tax or post-tax revenue basis, and the same conversion definition. Without that, report each marketplace separately.
- A high order value or a long decision cycle in one marketplace is a reason to investigate, not a reason to raise retargeting frequency everywhere.

## 4. Retail readiness

Before drafting an audience that will send traffic, confirm:

- The listing, Buy Box, inventory, and shipping speed can support more traffic.
- Contribution margin after returns, and the break-even cost per acquisition or ROAS that follows from it.
- The creative, landing page, and local language match the audience's intent.
- The event end date, restock timing, and audience and attribution latency fit the plan's timeline.
- A comparable baseline, a holdout, or a staged rollout is possible.

If retail readiness fails, keep the analysis but set activation to `HOLD`. Audiences sent to an out-of-stock or unprofitable listing produce a bad result that says nothing about the audience.

## 5. Verdict

Return exactly one:

- `READY_FOR_ANALYSIS`: read-only analysis can run.
- `READY_FOR_AUDIENCE_DRAFT`: the audience can be defined, but creating it isn't approved yet.
- `READY_FOR_APPROVAL`: parameters, risks, guardrails, and rollback are complete and can go to the approver.
- `HOLD`: list each gap and the condition that lifts it.
