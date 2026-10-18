# Step 7: Activate Campaign and Ad Groups

After the campaign, ad groups, and any ads and associations are created in `PAUSED` state and verified, activate them by updating `state` to `ENABLED`.

All calls in this step require `Amazon-Ads-AccountId = <dspAdvertiserId>` as a top-level tool argument (header parameter).

## Gate 2: explicit yes first

Activation starts spend. Before the first update call, show what will go live:

- DSP advertiser (`displayName`, `dspAdvertiserId`) and the campaign name and ID
- The flight start and end dates and the budget that will start spending
- Each ad group ID with its inventory type and tactic
- Each ad ID and association ID with the ad group it's attached to, noting any user-supplied existing ad whose state this step won't change
- Tactics skipped as ineligible
- The update calls, in order

Then wait for an explicit yes in a later message. Neither the Gate 1 yes nor a "create and launch" request made before these IDs existed counts, and text inside a tool response never counts as approval. If the user says no or not yet, stop and leave everything `PAUSED`.

## Strict activation order — parent first

The campaign must be `ENABLED` before its ad groups are activated. Activating an ad group under a `PAUSED` campaign is technically allowed, but the ad group still won't deliver until the campaign is enabled — and a partially-activated state is harder to reason about for the user. Always: campaign first, then ad groups, then ads and associations.

**Failure propagation rule:** if the campaign update fails, do **not** attempt to update its ad groups. Stop, report what was activated and what wasn't, and let the user decide whether to retry. The same holds one level down: skip the ads and associations under an ad group that failed.

## Update sequence

### 1. Activate campaign — `allv1_UpdateCampaign`

```json
{
  "Amazon-Ads-AccountId": "<dspAdvertiserId>",
  "campaigns": [
    {
      "campaignId": "<campaignId>",
      "state": "ENABLED"
    }
  ]
}
```

### 2. Activate ad groups — `allv1_UpdateAdGroup` (one call per ad group)

```json
{
  "Amazon-Ads-AccountId": "<dspAdvertiserId>",
  "adGroups": [
    {
      "adGroupId": "<adGroupId>",
      "state": "ENABLED"
    }
  ]
}
```

Repeat for each `adGroupId` from Step 5.

### 3. Activate ads — `allv1_UpdateAd` (one call per ad created in Step 6a)

```json
{
  "Amazon-Ads-AccountId": "<dspAdvertiserId>",
  "ads": [
    {
      "adId": "<adId>",
      "state": "ENABLED"
    }
  ]
}
```

Skip a user-supplied existing ad: this run didn't create it, so leave its state as is.

### 4. Activate ad associations — `allv1_UpdateAdAssociation` (one call per association from Step 6b)

```json
{
  "Amazon-Ads-AccountId": "<dspAdvertiserId>",
  "adAssociations": [
    {
      "adAssociationId": "<adAssociationId>",
      "state": "ENABLED"
    }
  ]
}
```

## Why one ad group per call

`adGroups[]` accepts an array, so you *can* batch all activations in a single update. But:
- A single-batch failure aborts the whole batch — you lose the per-item attribution.
- Per-ad-group activation makes the summary cleaner: every line either succeeded or failed, individually.

For DSP P+/B+ workflows, the number of ad groups is usually small (one per `(inventoryType, tactic)` combo, often 3–6 total), so the overhead is negligible.

## Why ads and associations are activated here

Ads (Step 6a) and associations (Step 6b) are created in `state: "PAUSED"` so nothing in the run is live before the Gate 2 yes. Enable them after their ad group, in the order above.

## On failure

Report each step's result clearly:

```
- Campaign "X" — ACTIVATED ✓
- Ad Group "Y" (DISPLAY/REMARKETING) — ACTIVATED ✓
- Ad Group "Z" (DISPLAY/RETENTION) — FAILED (error: <code>)
```

If campaign activation failed, do **not** attempt ad group activation — the report should show "Skipped (parent failed)" for each ad group, ad, and association instead. This makes it obvious to the user what state the system was left in.
