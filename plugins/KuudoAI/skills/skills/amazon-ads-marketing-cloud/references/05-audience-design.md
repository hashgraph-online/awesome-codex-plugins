# Audience patterns

Each pattern below is a starting shape, not a recipe. Fill in the include rules, exclude rules, and windows from this account's analyses. Draft the SQL from the playbook named (in `07-playbooks.md`), and when Amazon Agent Atlas is available, pull the listed playbook from its `amazon_ads` domain first; it wins on table and column names.

## Contents

- Definition card fields
- Rule-based or lookalike
- Patterns: engaged non-buyers, seasonal and event audiences, intent tiers, lifecycle and cross-sell, suppression, lookalike seeds
- Full-funnel tiering
- Naming
- Lifecycle: refresh, review, retire
- No-code templates
- Atlas document map

## Definition card fields

```text
purpose | marketplace | include | exclude | lookback (rolling or fixed) | ASIN/brand scope | type | size status | refresh | activation target | review date
```

Write include and exclude rules as conditions a reviewer can check ("viewed a detail page for ASIN X in the last 30 days AND no purchase of brand Y in the last 30 days"). Take the window from this account's time to conversion, repurchase cycle, or season, not from a case default. The full card template is in `11-reply-formats.md`.

## Rule-based or lookalike

- **Rule-based** fits clear behaviors: viewed or clicked without buying, bought A but not B, reached during an event without converting. It is explainable. Its risk is that a narrow rule falls under the minimum audience size, so check the current minimum.
- **Lookalike** extends reach from a seed. Use a seed that is high quality, compliant, and between 500 and 500,000 users. Reach runs in tiers from most similar to broadest; small, high-value goals start narrow, while exploration widens one tier at a time. Similarity doesn't replace product and creative fit.
- Test an include, an exclude, and a lookalike as separate changes. Don't widen the seed, window, and bid together.

## Patterns

### Engaged non-buyers

Shoppers who showed intent but didn't purchase in the window: viewed a detail page, added to cart, added to a wish list, clicked a sponsored ad, or searched a related term.

- Include the engagement signal; exclude purchasers of the ASIN or brand over the same window.
- Window: about the length of the consideration cycle, from time to conversion.
- Activation: Sponsored Products or Sponsored Brands bid boost on campaigns already targeting the ASIN, Sponsored Display or DSP retargeting.
- Guardrails: frequency, profit after returns, and the shoppers who would have bought anyway. The holdout matters most here because this group converts at a high rate on its own.
- Playbooks: A1 (cart abandoners), A2 (detail-page viewers who didn't buy).

### Seasonal and event audiences

Shoppers reached during a tentpole event (Prime Day, Black Friday and Cyber Monday, back to school, Singles Day, a local holiday) who didn't convert, retargeted after the event.

1. Pin the event's start and end, the comparison off-peak period, and the time zone for each marketplace. Put the event dates inside the audience SQL, converted to UTC (playbook A3). A rolling lookback alone drifts off the event as the audience refreshes, so a 30-day lookback refreshed a month after the event no longer sees it at all.
2. Include shoppers your ads reached during the event. Exclude anyone who purchased from the event start through each refresh, and those already saturated with exposure if frequency data supports it.
3. Treat three uses as separate hypotheses: post-event retargeting, excluding low-value exposure from the next event, and using converters as a lookalike seed.
4. Give each hypothesis a maturity window, a frequency guardrail, and a profit guardrail.

Phase the work around the event:

| Phase | Goal | Audience shape | Guardrails |
|---|---|---|---|
| Before the event | Build intent signals | Broad but relevant category or use-case engagement | Frequency, relevance, retail readiness |
| During the event | Put budget on high intent | Engaged non-buyers, cart adds, high-converting queries | Inventory, contribution margin, stacked bid adjustments |
| After the event | Capture delayed conversions, then wind down | Event-reached non-buyers, cart abandoners, repeat and cross-sell | Review date, fatigue, purchases that would have happened anyway |

Budget splits and phase percentages from courses or case studies are `EXTERNAL_BENCHMARK`.

Instructional queries: "Tentpole phase overlap", "Seasonal advertising exposure analysis", "Seasonal advertising exposure off-peak audience".

### Intent tiers

Group shoppers by what their behavior says they are looking for, then match content to it:

| Tier | Behavioral signal | Content job | Candidate activation |
|---|---|---|---|
| Category explorers | Broad category searches or browsing, no purchase | Category education, core use cases | Sponsored Brands video, Sponsored Products, DSP |
| Problem-aware | Feature or solution searches | Benefits and product evidence | Sponsored Brands, Sponsored Display, Sponsored Products |
| Use-case or occasion | Searches for a specific user group or occasion | Fit for that use, proof of use | Sponsored Brands, Sponsored Products, retargeting |
| Competitor-engaged | Engagement with competing brands or ASINs | Clear, provable differences | Sponsored Products, Sponsored Brands, DSP |

Use only claims the product can support and assets localized for the marketplace. Targeting competitor terms or ASINs must follow current trademark, advertising, and detail page policies; never disparage a competitor.

Instructional queries: "Audience based on sponsored ads keywords", "Sponsored ads targeted keyword to purchase path".

### Lifecycle and cross-sell

- **Replenishment:** bought a consumable and are approaching its repurchase cycle. Exclude anyone who bought again recently.
- **Cross-sell:** bought A but not the complementary B. Exclude shoppers for whom B doesn't apply.
- **Upgrade:** own an older or entry model and fit an upgrade path.
- **Lapsed:** bought before but not within a window longer than the normal repurchase cycle.

Take each window from the repurchase interval (playbook M4). Playbooks: A4 and its bought-A-not-B variant, A5, A6. Instructional queries: "Audience ready to upgrade", "Audience who purchased main products but not accessories", "Customer long term value by exposure group".

### Suppression

Some of the best audiences are exclusions:

- Recent purchasers, kept out of acquisition and retargeting spend until their repurchase window opens.
- Shoppers already exposed at high frequency, when frequency analysis shows diminishing returns.
- Existing customers, excluded from campaigns meant only for new-to-brand shoppers.

Measure a suppression by the spend it saves and whether conversions held, not by the excluded group's own conversion rate. Playbook: A4.

### Lookalike seeds

- Good seeds: repeat buyers, high-value tiers, NTB buyers who went on to repeat, converters from a successful event.
- Weak seeds: anyone who clicked, broad event reach, groups dominated by deal-seekers if the goal is full-price buyers.
- Size the seed before creating the lookalike, and test seed definitions separately rather than blending conditions into one narrow seed (playbook A5).
- The seed's members already buy. Keep them, or recent purchasers, out of the lookalike's spend with a campaign exclusion, unless the lookalike's settings already exclude the seed (check as `CURRENT_POLICY`).
- Instructional queries: "Introduction to AMC lookalike audiences", "Identify high value customer segments", "Audiences based on high value customer segments".

## Full-funnel tiering

- **Awareness:** category, interest, or video reach. Measure by effective reach, branded search, or the upper-funnel metrics currently available.
- **Consideration:** detail page views, repeat engagement, related searches. Measure with current definitions such as detail page view rate.
- **Conversion:** viewed or clicked without buying, engaged with competitors or your own product. Measure by profit after returns, conversion, and incremental lift.
- **Retention and cross-sell:** bought A but not B, repurchase cycle due. Exclude shoppers it doesn't fit and recent buyers.

Map product terms from external material (Performance+, Brand+, frequency targets, and the like) to current Amazon names and this account's capabilities before using them.

Instructional queries: "Campaign performance by user funnel stages", "Audience frequently exposed to your campaigns".

## Naming

`<marketplace>_<brand-or-asin>_<intent>_<include>_<exclude>_<lookback>_v<n>`, for example `DE_brandx_cartabandon_atc_nopurch_30d_v1`. Never put personal data or sensitive identifiers in a name.

## Lifecycle: refresh, review, retire

- AMC audiences refresh on a schedule and overwrite themselves on each refresh. The API default is every 21 days, so an audience created without an explicit cadence keeps refreshing until someone deletes it.
- A rolling window (a relative time window) moves forward on each refresh. A fixed window keeps the same historical slice, and refreshing it changes little apart from shoppers aging out of eligibility.
- There's no expiry date to set. A rule-based audience with `refreshRateDays: 0` deactivates after 30 days; otherwise it refreshes until deleted. Put a review date on the card and decide `KEEP`, `ITERATE`, `ROLLBACK`, or `EXPIRE` then.
- Deleting an AMC audience also removes it from the DSP and Sponsored Ads consoles. A deletion is a write with its own ask.

## No-code templates

AMC's no-code audience templates vary by instance and change over time, and the counts and names in external material go stale. When the user wants a template:

1. Check whether it is visible on this instance (`amc_listDataSources` or the AMC console).
2. If it isn't, keep the business definition from the patterns above and mark it `TEMPLATE_NOT_VERIFIED`.
3. Never invent a template name or the SQL behind one.

Instructional query: "How to use template analytics".

## Atlas document map

Each playbook in `07-playbooks.md` names the Atlas instructional query it came from, and `01-atlas-knowledge-base.md` lists the AMC guides and instructional queries by title, with how to find and read them. Look documents up by title, never by a stored ID: Atlas IDs change with every reindex. If a title returns nothing, search for the need; if that fails too, say Atlas doesn't have it.
