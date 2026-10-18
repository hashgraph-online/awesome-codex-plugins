# Step 5: Create Tactic Ad Groups

**Tool:** `allv1_CreateAdGroup`

Create one ad group per eligible `(primaryInventoryType, tacticType)` combination from Step 4. Use [inventory_type_mapping.md](inventory_type_mapping.md) to translate `primaryInventoryType` → ad group `inventoryType` — the API uses different enum names at the campaign vs ad-group level for the same concept, and this is the most common source of "INVALID_ARGUMENT" rejections on Step 5.

## Strict field allowlist (the most important constraint)

For P+/B+ tactic ad groups, the API only accepts the fields listed below. **Including any other field will cause the request to be rejected** with `INVALID_ARGUMENT`. The reason is that budgets, bids, pacing, viewability, dates, etc. are auto-managed by the system for tactic ad groups — passing them is the wrong layer.

Specifically these fields, common in regular DSP ad-group creation, must **not** appear in P+/B+ tactic ad-group payloads:

`bid`, `budgets`, `pacing`, `optimization`, `startDateTime`, `endDateTime`, `creativeRotationType`, `advertisedProductCategoryIds`, `amazonViewability`, `timeZoneType`, `userLocationSignal`, `videoCompletionTier`, `tacticsConvertersExclusionType`.

If a previous workflow run included these and got rejected, the failure is "extra fields", not "wrong values" — strip them.

## Required tool arguments

| Argument | Where | Source | Value |
|---|---|---|---|
| `Amazon-Ads-AccountId` | header (top-level tool arg) | Step 1 | `dspAdvertiserId` |
| `adGroups[]` | body (top-level tool arg) | composed | One ad-group object per call — see below |

## Ad group object fields (the entire allowlist)

| Field | Source | Value |
|---|---|---|
| `adProduct` | FIXED | `"AMAZON_DSP"` |
| `campaignId` | Step 2 | `campaignId` |
| `name` | DEFAULT | `DSP\|PB\|{inventoryType}\|{tactic} yyyy-MM-dd_HH-mm-ss` |
| `state` | FIXED | `"PAUSED"` |
| `inventoryType` | DERIVED | from the eligible combo, translated via [inventory_type_mapping.md](inventory_type_mapping.md) |
| `targetingSettings.automatedTargetingTactic` | DERIVED | `tacticType` from the eligible combo |

That's it. Nothing else.

## Payload

```json
{
  "Amazon-Ads-AccountId": "<dspAdvertiserId>",
  "adGroups": [
    {
      "adProduct": "AMAZON_DSP",
      "campaignId": "<campaignId>",
      "name": "<ad_group_name>",
      "state": "PAUSED",
      "inventoryType": "<inventory_type>",
      "targetingSettings": {
        "automatedTargetingTactic": "<tactic>"
      }
    }
  ]
}
```

## Response → extract

- `adGroupId` — used in Step 6 (creating ads) and Step 7 (activation).

## Verification (read-after-write)

After each create call returns, wait 100ms then call:

```
allv1_QueryAdGroup
  Amazon-Ads-AccountId: <dspAdvertiserId>
  body: {
    "adProductFilter": {"include": ["AMAZON_DSP"]},
    "adGroupIdFilter": {"include": ["<adGroupId>"]}
  }
```

Retry up to 3 times with 1-second delays if the ad group isn't found. Do not proceed to Step 6 (or activate this ad group in Step 7) until verification succeeds.

## Batch vs serial

`allv1_CreateAdGroup` accepts an array of ad groups in `adGroups[]`, but the verification pattern works best one-at-a-time so failures are attributable to a specific tactic combo. Recommend: one ad group per call, sequenced through the eligible list.

On failure: stop and report **which `(inventoryType, tactic)` combination failed and the API's error code**. Don't continue creating the remaining ad groups — a partial Step 5 is hard to clean up.
