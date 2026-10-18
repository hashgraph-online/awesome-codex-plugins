# Step 4: Query Eligible Tactics

**Tool:** `allv1_QueryCampaign`

Re-queries the campaign after conversion tracking is configured to extract which automated targeting tactics are eligible for ad-group creation. Eligibility is populated asynchronously after Step 3 — even though Step 3 itself verified the products landed, the eligibility recomputation that watches for that change has its own propagation lag — so this step usually requires a brief retry loop.

## Request

```json
{
  "Amazon-Ads-AccountId": "<dspAdvertiserId>",
  "adProductFilter": {"include": ["AMAZON_DSP"]},
  "campaignIdFilter": {"include": ["<campaignId>"]}
}
```

| Field | Where | Source | Value |
|---|---|---|---|
| `Amazon-Ads-AccountId` | header (top-level tool arg) | Step 1 | `dspAdvertiserId` |
| `adProductFilter.include` | body | FIXED | `["AMAZON_DSP"]` |
| `campaignIdFilter.include` | body | Step 2 | `["<campaignId>"]` |

Filtering by both `adProductFilter` and `campaignIdFilter` keeps the response payload small and unambiguous.

## Response → extract

From the matched campaign object:
- `eligibleAutomatedTargetingTactics[]` — array of `{primaryInventoryType, tacticType}` pairs you can create ad groups for.
- `ineligibleAutomatedTargetingTactics[]` — array of `{tacticKey: {primaryInventoryType, tacticType}, reasons: [{reasonCode}]}` pairs explaining why each combo is unavailable.

## Determine which tactics to create

1. Filter `eligibleAutomatedTargetingTactics[]` to entries whose `primaryInventoryType` is in the user's requested `primaryInventoryTypes`.
2. If the user specified particular tactics (e.g., "REMARKETING only"), intersect with that list too.

Then:

- **All requested tactics are eligible** → proceed to Step 5 for the full set.
- **Some are eligible, some aren't** → present the user with which are unavailable (include the `reasonCode`) and what eligible alternatives exist. Let the user decide whether to proceed with the eligible subset only, swap to alternatives, or attempt the ineligible tactics anyway (ad groups can be created but won't deliver until eligibility is met — usually not advised).
- **User did not specify tactics** → use all eligible combos that match `primaryInventoryTypes`.

## Eventual consistency

Eligibility is populated asynchronously after conversion tracking is configured in Step 3. If the first query returns an empty `eligibleAutomatedTargetingTactics`, wait 100ms and retry up to 3 times with 1-second delays.

If still empty after retries, the most likely causes are:

1. **Conversion tracking propagation lag** — Step 3's POST succeeded and the GET verification confirmed the ASINs landed, but the eligibility recomputation hasn't caught up yet. Wait 5–10 seconds and try again manually.
2. **Goal-KPI / inventory-type mismatch** — the campaign's `goal_kpi` is incompatible with any P+ or B+ tactic for the requested `primaryInventoryType`. Cross-check against the tactic↔KPI table in [step0_gather_inputs.md](step0_gather_inputs.md). For example, a B+ `PROSPECTING` tactic on `DISPLAY` inventory needs an awareness KPI (e.g., `REACH`); pointing it at a conversion KPI (`ROAS`) will leave the eligible list empty.
3. **Conversion tracking not actually configured** — if the user manually skipped Step 3, or it returned partial success and the unsuccessful ASINs were the ones the tactic needed, eligibility computation may find nothing usable. Re-run Step 3 with the full ASIN list.

## Common `reasonCode` values

| `reasonCode` | Meaning |
|---|---|
| `NOT_ELIGIBLE_GOAL` | The tactic isn't compatible with the campaign's goal KPI. Cross-check against [step0_gather_inputs.md](step0_gather_inputs.md) tactic↔KPI table. |
| `EMPTY_INPUT` | Conversion tracking is not configured (no products attached). If you see this after Step 3 ran successfully, the most likely cause is propagation lag — wait a few seconds and re-query. If it persists, re-verify Step 3 with `campconv_DspGetCampaignConversionTrackingProductsV1` to confirm the products are actually on the campaign. |

Other codes the API may return; treat unknown codes as opaque and surface the raw value to the user.

On failure: stop and report the error. A failed Step 4 means the workflow has no eligible tactics to create ad groups for.
