# Step 6a: Create Ad (Optional)

**Tool:** `allv1_CreateAd`

This step is optional. There are three paths:
1. **User provides creative details** (asset IDs, creative sizes, etc.) → create the ad, then proceed to Step 6b.
2. **User provides an existing `adId`** → skip this step, use the provided `adId` directly in Step 6b.
3. **User wants to defer creatives** → skip both Step 6a and 6b, proceed to Step 7.

Create ads only from an approved plan: either the Gate 1 plan included these creative details, or you showed them afterwards (ad type, asset ID and version, sizes, callToAction URL, target ad groups) and got a yes.

## Inputs

**Collect from the user (when they opt to create ads):**

| Input | For ad type | Required | Notes |
|---|---|---|---|
| `assetId` | ALL | Yes | Asset ID from the Asset Library (image for DISPLAY, video for VIDEO) |
| `assetVersion` | ALL | Yes | Asset version string (e.g., `version_v1`) |
| `creativeSizes` | DISPLAY only | Yes | Array of `{height, width}` integers (e.g., `300x250`) |
| `adChoicesPosition` | DISPLAY only | No | Default: `BOTTOM_RIGHT`. Enum: `TOP_LEFT`, `TOP_RIGHT`, `BOTTOM_LEFT`, `BOTTOM_RIGHT` |

**Auto-derived (no user input needed):**

| Field | Source |
|---|---|
| `adProduct` | FIXED: `"AMAZON_DSP"` |
| `adType` | DERIVED: `"DISPLAY"` for DISPLAY inventory, `"VIDEO"` for VIDEO_OLV / VIDEO_STV |
| `name` | DEFAULT: `DSP\|PB\|Ad\|{adType} yyyy-MM-dd_HH-mm-ss` |
| `state` | FIXED: `"PAUSED"` (created paused like the campaign and ad groups, so nothing is live before Gate 2; Step 7 enables it) |
| `marketplaces` | DERIVED: `["<marketplace>"]` from Step 0 |
| `callToAction` / `callToActions` URL | DERIVED: `https://www.amazon.com/dp/<ASIN>` from Step 0 ASINs |
| `deepLinkingBehavior` | FIXED: `"ENABLED"` |
| `products` (VIDEO only) | DERIVED: reuse the ASINs from Step 0 |
| `language` | DERIVED: from `marketplace` — see locale table below |

## Required tool arguments

| Argument | Where | Source |
|---|---|---|
| `Amazon-Ads-AccountId` | header (top-level tool arg) | Step 1 (`dspAdvertiserId`) |
| `ads[]` | body (top-level tool arg) | One ad object per call — payloads below |

## Payload — DISPLAY inventory

```json
{
  "Amazon-Ads-AccountId": "<dspAdvertiserId>",
  "ads": [
    {
      "adProduct": "AMAZON_DSP",
      "adType": "DISPLAY",
      "name": "<ad_name>",
      "state": "PAUSED",
      "marketplaces": ["<marketplace>"],
      "creative": {
        "displayCreative": {
          "standardDisplaySettings": {
            "adChoicesPosition": "<ad_choices_position>",
            "creativeSizes": [{"height": "<height>", "width": "<width>"}],
            "customImages": [
              {
                "assetId": "<asset_id>",
                "assetVersion": "<asset_version>",
                "formatProperties": [{"applyBorder": true}]
              }
            ],
            "language": "<language_from_marketplace>",
            "callToAction": {
              "clickToUrlDisplayCallToActionSettings": {
                "url": "https://www.amazon.com/dp/<ASIN>",
                "deepLinkingBehavior": "ENABLED"
              }
            }
          }
        }
      }
    }
  ]
}
```

## Payload — STREAMING_TV inventory (`VIDEO_STV`)

```json
{
  "Amazon-Ads-AccountId": "<dspAdvertiserId>",
  "ads": [
    {
      "adProduct": "AMAZON_DSP",
      "adType": "VIDEO",
      "name": "<ad_name>",
      "state": "PAUSED",
      "marketplaces": ["<marketplace>"],
      "creative": {
        "videoCreative": {
          "streamingTvSettings": {
            "videos": {"assetId": "<asset_id>", "assetVersion": "<asset_version>"},
            "language": "<language_from_marketplace>",
            "products": [{"productIdType": "ASIN", "productId": "<ASIN>"}],
            "callToActions": [
              {
                "clickToUrlVideoCallToActionSettings": {
                  "url": "https://www.amazon.com/dp/<ASIN>",
                  "deepLinkingBehavior": "ENABLED"
                }
              }
            ]
          }
        }
      }
    }
  ]
}
```

## Payload — ONLINE_VIDEO inventory (`VIDEO_OLV`)

```json
{
  "Amazon-Ads-AccountId": "<dspAdvertiserId>",
  "ads": [
    {
      "adProduct": "AMAZON_DSP",
      "adType": "VIDEO",
      "name": "<ad_name>",
      "state": "PAUSED",
      "marketplaces": ["<marketplace>"],
      "creative": {
        "videoCreative": {
          "onlineVideoSettings": {
            "videos": {"assetId": "<asset_id>", "assetVersion": "<asset_version>"},
            "language": "<language_from_marketplace>",
            "products": {"productIdType": "ASIN", "productId": "<ASIN>"},
            "callToActions": [
              {
                "clickToUrlVideoCallToActionSettings": {
                  "url": "https://www.amazon.com/dp/<ASIN>",
                  "deepLinkingBehavior": "ENABLED"
                }
              }
            ]
          }
        }
      }
    }
  ]
}
```

Note: `streamingTvSettings.products` is an array, `onlineVideoSettings.products` is a single object. This is a quirk in the v1 schema, not a typo — preserve the shapes exactly.

## Language locale

Derive `language` from the user's marketplace country code. Format: `{language}_{COUNTRY}` (ISO-639 + ISO-3166).

| Marketplace | Locale |
|---|---|
| US, CA, UK, AU, IN | `en_US` |
| DE | `de_DE` |
| FR | `fr_FR` |
| ES, MX | `es_ES` |
| IT | `it_IT` |
| NL | `nl_NL` |
| SE | `sv_SE` |
| JP | `ja_JP` |
| BR | `pt_PT` |
| AE, SA | `ar_AE` |
| TR | `tr_TR` |

## Response → extract

- `adId` — used in Step 6b.

## Verification (read-after-write)

After each `allv1_CreateAd` returns, wait 100ms then call `allv1_QueryAd` filtered by the new `adId`. Retry up to 3 × 1s on miss. Do not proceed to Step 6b until verification succeeds — Step 6b will reject an association against an `adId` it can't yet see.

On failure: stop and report the error and which ad-group context the ad was being created for.
