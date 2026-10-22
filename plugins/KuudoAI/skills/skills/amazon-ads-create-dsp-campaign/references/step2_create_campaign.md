# Step 2: Create DSP Campaign

**Tool:** `allv1_CreateCampaign`

Creates the DSP campaign in `PAUSED` state. We deliberately do not create in `ENABLED` — the campaign must exist before conversion tracking and ad groups can attach, and we don't want it to start spending until everything downstream succeeds. Activation happens in Step 7, after a second yes at Gate 2.

`PAUSED` stops spend, but the create is still a write to the advertiser's account. Call it only after the user's explicit yes to the Gate 1 plan, which shows the advertiser, name, flight dates, budget, goal KPI, inventory types, and ASINs that go into this payload.

## Required tool arguments

| Argument | Where | Source | Value |
|---|---|---|---|
| `Amazon-Ads-AccountId` | header (top-level tool arg) | Step 1 | `dspAdvertiserId` from `alternateIds[]` |
| `campaigns[]` | body (top-level tool arg) | composed | Single campaign object — see below |

The hosted MCP shape nests these under `body.accessRequestedAccount` + `body.campaigns`. This repo's `allv1_CreateCampaign` does not — `Amazon-Ads-AccountId` is a header parameter the OpenAPI spec declares directly, and the body is flattened to `campaigns[]` at top level.

## Campaign object fields

| Field | Source | Value |
|---|---|---|
| `adProduct` | FIXED | `"AMAZON_DSP"` |
| `name` | DEFAULT | `DSP\|PB\|Campaign yyyy-MM-dd_HH-mm-ss` |
| `countries` | INPUT | `["<marketplace>"]` |
| `state` | FIXED | `"PAUSED"` |
| `flights[0].startDateTime` | INPUT | ISO 8601 with `Z` suffix (e.g. `2026-10-01T00:00:00Z`) |
| `flights[0].endDateTime` | INPUT | ISO 8601 with `Z` suffix |
| `flights[0].budget.budgetType` | FIXED | `"MONETARY"` |
| `flights[0].budget.budgetValue.monetaryBudgetValue.monetaryBudget.value` | INPUT | campaign budget |
| `optimizations.bidSettings.bidStrategy` | DEFAULT | `"SPEND_BUDGET_IN_FULL"` |
| `optimizations.goalSettings.kpi` | INPUT/DEFAULT | goal KPI (default `ROAS`) |
| `optimizations.primaryInventoryTypes` | INPUT | from user, e.g. `["DISPLAY"]` |
| `fees`, `frequencies`, `tags`, `purchaseOrderNumber` | OPTIONAL | include only if the user provided them |

There is no campaign-level budget field — budget is flight-level only. The skill maps the user's single budget/start/end inputs to a single flight; if the user later wants multiple flights, that's a separate update operation.

## Payload

```json
{
  "Amazon-Ads-AccountId": "<dspAdvertiserId>",
  "campaigns": [
    {
      "adProduct": "AMAZON_DSP",
      "name": "<campaign_name>",
      "countries": ["<marketplace>"],
      "state": "PAUSED",
      "flights": [
        {
          "startDateTime": "<campaign_start_date>",
          "endDateTime": "<campaign_end_date>",
          "budget": {
            "budgetType": "MONETARY",
            "budgetValue": {
              "monetaryBudgetValue": {
                "monetaryBudget": {
                  "value": "<campaign_budget>"
                }
              }
            }
          }
        }
      ],
      "optimizations": {
        "bidSettings": {
          "bidStrategy": "<bid_strategy>"
        },
        "goalSettings": {
          "kpi": "<goal_kpi>"
        },
        "primaryInventoryTypes": ["<primaryInventoryTypes>"]
      }
    }
  ]
}
```

All datetime values must include the `Z` UTC suffix — the API rejects naive datetimes.

## Response → extract

- `campaignId` — used in every later step (conversion tracking, ad group create, activation).
- `ineligibleAutomatedTargetingTactics` — surfaced here as a first signal, but the authoritative read happens in Step 4 after conversion tracking is configured.

## Verification (read-after-write)

After the create call returns, wait 100ms then call:

```
allv1_QueryCampaign
  Amazon-Ads-AccountId: <dspAdvertiserId>
  body: {
    "adProductFilter": {"include": ["AMAZON_DSP"]},
    "campaignIdFilter": {"include": ["<campaignId>"]}
  }
```

Retry up to 3 times with 1-second delays if the campaign isn't found. Do not proceed to Step 3 until verification succeeds — Step 3 requires the campaign to exist server-side, and the API's eventual consistency means it may take a moment.

On any failure: stop and report. A failed Step 2 means the workflow has no campaign to attach anything to.
