# Amazon DSP on v1

`adProduct`: `AMAZON_DSP`. Product-scoped schemas: `dspv1_DSP*`. Read from the live server on 2026-11-19; when a field you need is not listed here, run `get_schema` on the `dspv1_DSP*` tool for that operation.

**Launching a Performance+ or Brand+ campaign end to end** (account resolution, conversion tracking, eligible tactics, ad groups, two approval gates) belongs to `amazon-ads-create-dsp-campaign`. Use this reference for reading DSP entities and for targeted edits to existing ones.

**Account scope:** DSP calls run under the DSP advertiser account selection (`set_active_account` with the `dspAdvertiserId`), not a sponsored-ads profile. Resolve it with `amazon-ads-accounts`.

## Capabilities

| Entity | Query | Create | Update | Delete |
|---|---|---|---|---|
| Campaign | yes | yes, `PAUSED` only | yes | **no**; pause instead |
| Ad group | yes | yes, `PAUSED` only | yes | **no**; pause instead |
| Ad (creative) | yes, `adIdFilter` only | yes | creative, marketplaces, name, state, tags | **no product-scoped tool**; remove the association instead |
| Ad association | yes | yes | dates, state, weight | yes |
| Target | yes, no campaign/target ID filter | yes | **no**; delete and recreate | yes |

## Batch and page limits

| Operation | Campaigns | Ad groups | Ads | Associations | Targets |
|---|---|---|---|---|---|
| Create / update / delete per call | **5** | **20** | **10** | **20** | 1000 |
| Query `maxResults` (max) | 100 | 100 | 100 | 100 | 5000 |

## Campaign

**Create requires:** `adProduct`, `name`, `state: PAUSED`, `flights`, `optimizations.bidSettings.bidStrategy`.

- There is no campaign `startDateTime` or `marketplaceScope`. Dates and budgets live on `flights` (1–150): each has `startDateTime`, `endDateTime`, `budget {budgetType: MONETARY, budgetValue}`, optional `name`.
- `bidStrategy`: `PRIORITIZE_KPI_TARGET`, `SPEND_BUDGET_IN_FULL`, `USE_CAMPAIGN_STRATEGY`.
- `optimizations.goalSettings {kpi, kpiValue}`: KPIs include `ROAS`, `ROAS_COMBINED`, `ROAS_PROMOTED`, `TOTAL_RETURN_ON_AD_SPEND`, `COST_PER_CLICK`, `COST_PER_ACTION`, `COST_PER_DETAIL_PAGE_VIEW`, `DETAIL_PAGE_VIEW_RATE`, `CLICK_THROUGH_RATE`, `REACH`, `FREQUENCY_AVERAGE`, `COST_PER_VIDEO_COMPLETION`, `VIDEO_COMPLETION_RATE`, `COST_PER_INSTALL`, `COST_PER_FIRST_APP_OPEN`, `COST_PER_SIGN_UP`, `COST_PER_CONVERSION_OFF_AMAZON`, `RETURN_ON_AD_SPEND`. `COMBINED_RETURN_ON_AD_SPEND` is deprecated: use `ROAS_COMBINED`.
- `optimizations.budgetSettings`: `budgetAllocation` (`AUTO` | `MANUAL`), `flightBudgetRolloverStrategy` (`NO_ROLLOVER`, `PRIOR_BUDGET_ROLLOVER`, `CUMULATIVE_BUDGET_ROLLOVER`). `optimizations.primaryInventoryTypes`: `AUDIO`, `DISPLAY`, `VIDEO_OLV`, `VIDEO_STV`.
- Optional: campaign `budgets` (0–2; `DAILY`, `LIFETIME`, `MONTHLY`), `fees` (one agency fee, percentage of budget; **locked once an ad group exists**), `frequencies` (up to 3 caps), `adomains`, `countries`, `marketplaces`, `purchaseOrderNumber`, `skanAppId`, `tags` (**1** only).

**Update:** `campaignId` plus `name`, `state`, `flights`, `budgets`, `optimizations`, `frequencies`, `fees` (if no ad group yet), `adomains`, `purchaseOrderNumber`, `skanAppId`, `tags`. `countries` and `marketplaces` are immutable.

Editing `flights` replaces the list: read the current flights, change the one the user means, keep each existing `flightId`, and send the full list. Shortening or removing a flight that has spent is a business decision; show it explicitly.

## Ad group

**Query:** `adProductFilter`, `adGroupIdFilter`, `campaignIdFilter`, `stateFilter`, `maxResults`, `nextToken`. There is no `nameFilter` (the merged schema accepts it; the DSP contract does not): find an ad group by name by paging and matching client-side, ideally within a known campaign.

**Create requires (13 fields):** `adProduct`, `campaignId`, `name`, `state: PAUSED`, `startDateTime`, `endDateTime`, `inventoryType`, `advertisedProductCategoryIds` (1–500; for `VIDEO`, one parent category or its subcategories), `bid.baseBid`, `creativeRotationType` (`RANDOM` | `WEIGHTED`), `optimization.bidStrategy`, `pacing.deliveryProfile` (`ASAP`, `EVEN`, `PACE_AHEAD`), and `targetingSettings {amazonViewability {viewabilityTier, includeUnmeasurableImpressions}, timeZoneType: ADVERTISER_REGION | VIEWER, userLocationSignal: CURRENT | MULTIPLE_SIGNALS}`.

- `inventoryType`: `DISPLAY`, `STANDARD_DISPLAY`, `AMAZON_MOBILE_DISPLAY`, `AAP_MOBILE_APP`, `VIDEO`, `ONLINE_VIDEO`, `STREAMING_TV`, `STREAMING_TV_AMAZON_DEAL`, `AUDIO`, `AUDIO_AMAZON_DEAL`, `PODCAST`, `LIVE_EVENTS`.
- `includeUnmeasurableImpressions` must be `false` when `viewabilityTier` is `ALL_TIERS`.
- Optional: `targetingSettings.automatedTargetingTactic` (`CUSTOMER_ACQUISITION`, `REMARKETING`, `RETENTION`, `MAXIMIZE_PERFORMANCE`, `PROSPECTING`, `AWARENESS`, `SEARCH`), `bid.maxAverageBid`, `budgets`, `fees`, `frequencies` (ad group max 500 events), `tags` (1).

**Immutable:** `inventoryType`, `automatedTargetingTactic`, `campaignId`.

## Ads and associations

DSP ads have no `adGroupId`. An ad is a standalone creative (`adType` `DISPLAY`, `VIDEO`, `AUDIO`, `COMPONENT`, `THIRD_PARTY`; `name` required; product IDs are ASIN only). It serves only through an ad association:

- `allv1_CreateAdAssociation`: `{adAssociations: [{adGroupId, adId, state, weight?, startDateTime?, endDateTime?}]}`, max 20. No `adProduct` field.
- `allv1_QueryAdAssociation`: no required filter; filter by `adGroupIdFilter`, `adIdFilter`, or `adAssociationIdFilter`. This is the only way to list a DSP ad group's ads.
- To stop an ad in one ad group, pause or delete its association, not the ad.

## Targets

**Create requires:** `adProduct`, `adGroupId`, `negative`, `state`, `targetType`, `targetDetails`. No bid field.

DSP target types cover audiences (`audienceTarget` with `groupId` numeric string and `inGroupOperator`/`acrossGroupOperator`), products (`PRODUCT_EXACT`, `PRODUCT_SIMILAR`, `PRODUCT_COMPLEMENTS`, `PRODUCT_REMARKETING`), categories (`productCategoryId` with `MULTISIGNAL_BROAD`), keywords (`BROAD` only), domains, apps, devices, dayparts (`HH:MMZ`), locations, content, brand safety, inventory sources, video and placement attributes, and third-party segments. Supported content genres depend on the ad group's `inventoryType`. Read `get_schema` on `dspv1_DSPCreateTarget` for the variant you need.

DSP targets **cannot be updated at all, including `state`**, so a DSP target cannot be paused. To stop one, either delete it (permanent; recreate later if needed) or pause the whole ad group; let the user choose. To change one, the preview shows create-replacement-then-delete-original as one change, in that order, so targeting never lapses.

**Query:** filters are `adGroupIdFilter`, `targetTypeFilter`, `stateFilter`, and inventory-source filters. There is no `campaignIdFilter`, `targetIdFilter`, or `negativeFilter`; split negatives client-side.
