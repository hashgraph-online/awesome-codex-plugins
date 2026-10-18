# Step 3: ASIN Conversion Tracking

**Tool:** `campconv_DspPostProductConversionTrackingV1`

Adds products (ASINs) to a DSP campaign to enable product-related conversion metrics. Newly added products are appended to any existing list — the call is additive, not destructive. The API accepts 1–2,000 products per call; a campaign can track up to 500,000 products total.

This step is what unlocks P+ eligible tactics in Step 4. The campaign's `eligibleAutomatedTargetingTactics[]` is computed asynchronously based on the products attached here — without conversion tracking products, most P+ tactics will come back as ineligible with `reasonCode: EMPTY_INPUT`.

This POST is a write, covered by the user's Gate 1 yes: post exactly the ASINs, `domain`, and `productAssociation` shown in that plan. Adding ASINs that weren't in it (variations, halo ASINs) needs a fresh yes.

## Required tool arguments

| Argument | Where | Source | Value |
|---|---|---|---|
| `Amazon-Ads-AccountId` | header (top-level tool arg) | Step 1 | `dspAdvertiserId` |
| `campaignId` | path (top-level tool arg) | Step 2 | newly-created campaign ID |
| `productTrackingList[]` | body (top-level tool arg) | INPUT | One entry per ASIN — see below |

The hosted MCP wraps these as `pathParameters.campaignId` + `body.accessRequestedAccount.advertiserAccountId` + `body.productTrackingList`. This repo flattens all three to top-level tool arguments and uses the `Amazon-Ads-AccountId` header instead of a body field for account scoping.

## productTrackingList item shape

| Field | Required | Value |
|---|---|---|
| `productId` | Yes | ASIN, exactly 10 characters |
| `domain` | Yes | `AMAZON_{countryCode}` derived from the user's marketplace |
| `productAssociation` | Yes | `FEATURED` for all user-provided ASINs (see below for alternatives) |

### Valid `domain` values (full enum)

`AMAZON_AE`, `AMAZON_AU`, `AMAZON_BR`, `AMAZON_CA`, `AMAZON_DE`, `AMAZON_ES`, `AMAZON_FR`, `AMAZON_IN`, `AMAZON_IT`, `AMAZON_JP`, `AMAZON_MX`, `AMAZON_NL`, `AMAZON_SA`, `AMAZON_SE`, `AMAZON_TR`, `AMAZON_UK`, `AMAZON_US`, `FRESH_STORES_US`, `WHOLE_FOODS_MARKET_US`

Derive from the user's `marketplace` input: `US` → `AMAZON_US`, `UK` → `AMAZON_UK`, etc. The `FRESH_STORES_US` and `WHOLE_FOODS_MARKET_US` values are for cross-banner tracking and aren't used in the default P+/B+ flow.

### Valid `productAssociation` values

| Value | When to use |
|---|---|
| `FEATURED` | Product is promoted in creatives within this campaign. **Use this for all user-provided ASINs in the default flow.** |
| `FEATURED_WITH_VARIATION` | Featured product including its variations (parent + child ASINs). Use when the user explicitly says "include variations." |
| `NOT_FEATURED` | Tracked for conversion attribution but not promoted in creatives. Use for "halo" ASINs the user wants to measure but isn't advertising. |

The Amazon docs note that tracking non-featured and variation ASINs in addition to the featured ones prevents data loss that isn't recoverable once a campaign starts. If the user wants comprehensive measurement, suggest they add variation/non-featured ASINs as separate `productTrackingList` entries with the appropriate `productAssociation`.

## Payload

```json
{
  "Amazon-Ads-AccountId": "<dspAdvertiserId>",
  "campaignId": "<campaignId>",
  "productTrackingList": [
    {
      "productId": "<ASIN>",
      "domain": "<AMAZON_{countryCode}>",
      "productAssociation": "FEATURED"
    }
  ]
}
```

For multiple ASINs, add multiple entries to `productTrackingList[]` — batch in a single call (up to 2,000 per call) rather than calling once per ASIN. The endpoint is designed for batch use; per-ASIN calls would waste round trips.

## Response → extract

The response itself doesn't return per-ASIN status — success means the batch was accepted. For confirmation that each ASIN actually landed, use the verification read below.

## Verification (read-after-write)

After the POST returns, wait 100ms then call:

```
campconv_DspGetCampaignConversionTrackingProductsV1
  Amazon-Ads-AccountId: <dspAdvertiserId>
  campaignId:           <campaignId>
```

The response shape:
```json
{
  "productTrackingList": [
    {"productId": "B0EXAMPLE1", "domain": "AMAZON_US", "productAssociation": "FEATURED"},
    ...
  ],
  "nextToken": "..."   // present only if results exceed page size
}
```

Confirm every ASIN you POSTed appears in the returned `productTrackingList[]`. If some are missing, retry up to 3 × 1s — the API is eventually consistent and propagation usually completes within ~1 second. If still missing after retries, report which ASINs didn't land.

If the list is paginated (`nextToken` present), continue paging until you've verified every POSTed ASIN — but for the typical case (a handful of ASINs per campaign), a single page is enough.

## On failure

- **Total batch failure** (e.g., 4xx response): stop and report. The campaign exists but has no conversion tracking — Step 4 will return zero eligible P+ tactics. Suggest the user re-run with a corrected payload (most common cause: invalid `domain` for the marketplace, or a non-ASIN `productId`); show the corrected list and get a fresh yes before posting it.
- **Partial verification failure** (some ASINs missing after retries): report which ASINs didn't land. Let the user decide whether to proceed with the partial list or stop and re-attempt the missing ones.
- **Throttling** (`429 / THROTTLED`): back off with exponential delay (start at 2s, double up to 30s) and retry the same batch. The endpoint has per-account rate limits.

## Why this step is additive, not idempotent

Each POST appends to the campaign's existing tracking list. Re-running this step with the same ASINs creates duplicate entries — not necessarily an error, but it can waste a slot in the 500k cap. If you suspect tracking is partially configured, call the GET first to see what's already there before deciding whether to POST again.

For deleting products, use `campconv_DspDeleteProductConversionTrackingV1` (POST to `.../products/delete`) with the same `productTrackingList` shape — but this skill's workflow doesn't use it. If the user asks to remove products, show the exact list and get its own yes first.
