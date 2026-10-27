# Step 6b: Associate Ad with Ad Group (Optional)

**Tool:** `allv1_CreateAdAssociation`

Only execute if Step 6a was completed or the user provided an existing `adId`. If the user deferred creatives entirely, skip this step and proceed to Step 7.

Links an ad (from Step 6a or user-provided) to an ad group (from Step 5). Without an association, an ad exists in the account but isn't actually wired into the delivery path of the ad group.

## Required tool arguments

| Argument | Where | Source | Value |
|---|---|---|---|
| `Amazon-Ads-AccountId` | header (top-level tool arg) | Step 1 | `dspAdvertiserId` |
| `adAssociations[]` | body (top-level tool arg) | composed | See below |

## Association object fields

| Field | Source | Value |
|---|---|---|
| `adId` | Step 6a (or user) | `adId` |
| `adGroupId` | Step 5 | `adGroupId` |
| `state` | FIXED | `"PAUSED"` (Step 7 enables it after the Gate 2 yes) |

## Payload

```json
{
  "Amazon-Ads-AccountId": "<dspAdvertiserId>",
  "adAssociations": [
    {
      "adId": "<adId>",
      "adGroupId": "<adGroupId>",
      "state": "PAUSED"
    }
  ]
}
```

## Response → extract

- `adAssociationId` — needed in Step 7 to enable the association with `allv1_UpdateAdAssociation`; also shown in the Gate 2 preview and the Step 8 summary.

## Verification (read-after-write)

After the create call returns, wait 100ms then call:

```
allv1_QueryAdAssociation
  Amazon-Ads-AccountId: <dspAdvertiserId>
  body: {
    "adIdFilter": {"include": ["<adId>"]},
    "adGroupIdFilter": {"include": ["<adGroupId>"]}
  }
```

Retry up to 3 × 1s on miss.

On failure: stop and report the error and which `(adId, adGroupId)` pair failed.
