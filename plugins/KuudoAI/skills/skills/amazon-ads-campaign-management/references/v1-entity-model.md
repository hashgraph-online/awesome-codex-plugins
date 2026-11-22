# Unified v1 entity model

How campaign management works on the unified v1 API through the Kuudo Amazon Ads MCP. Product-specific rules live in `products/*.md`. Facts marked *observed* come from read-only calls on 2026-11-19; the rest come from the live tool schemas on the same date.

## Contents

- [Calling tools](#calling-tools)
- [Entities and hierarchy](#entities-and-hierarchy)
- [Request shapes](#request-shapes)
- [Queries and paging](#queries-and-paging)
- [State, pause, and delete](#state-pause-and-delete)
- [Targets](#targets)
- [Responses and errors](#responses-and-errors)
- [Which schema to trust](#which-schema-to-trust)

## Calling tools

- Tools run inside `execute` as `await call_tool("allv1_QueryCampaign", {...})`. A block allows at most 50 `call_tool` calls. Pass the request fields at the top level of the arguments: a `body` wrapper or an extra `skill` key is dropped without an error, so a filter inside `body` is silently ignored.
- **Account scope is session state.** Read it with `get_active_profile` and `get_active_account`. Sponsored ads (SP, SB, SD, ST) run under the selected profile; DSP runs under the selected DSP advertiser account. Changing the selection affects every later call in the session; do it only for the account the user confirmed, through `amazon-ads-accounts`.
- If a block fails partway, earlier calls in it may have succeeded. Query before retrying any write. On `OUTBOUND_RATE_WAIT_EXCEEDED`, wait `retry_after_seconds` and continue in smaller chunks.

## Entities and hierarchy

```
campaign ── ad group ──┬── ad            (SP, SB, SD, ST: ad belongs to one ad group)
   │                   ├── target        (keywords, negatives, product/category, themes, audiences…)
   │                   └── ad association ── ad   (DSP only: ads are standalone creatives)
   └── campaign-level target             (SP, SD campaign negatives and similar)
```

Create parents before children and stop children whose parent failed. Every entity has a string ID (`campaignId`, `adGroupId`, `adId`, `targetId`, `adAssociationId`).

| Entity | Tools |
|---|---|
| Campaign | `allv1_QueryCampaign`, `allv1_CreateCampaign`, `allv1_UpdateCampaign`, `allv1_DeleteCampaign` |
| Ad group | `allv1_QueryAdGroup`, `allv1_CreateAdGroup`, `allv1_UpdateAdGroup`, `allv1_DeleteAdGroup` |
| Ad | `allv1_QueryAd`, `allv1_CreateAd`, `allv1_UpdateAd`, `allv1_DeleteAd` |
| Target | `allv1_QueryTarget`, `allv1_CreateTarget`, `allv1_UpdateTarget`, `allv1_DeleteTarget` |
| Ad association (DSP) | `allv1_QueryAdAssociation`, `allv1_CreateAdAssociation`, `allv1_UpdateAdAssociation`, `allv1_DeleteAdAssociation` |

No v1 portfolio tool exists. Ad extensions (`allv1_*AdExtension`, SP and SB, open beta) support create, update, and query but not delete; they are outside this skill's references.

## Request shapes

| Operation | Arguments |
|---|---|
| Query | Filters at top level, each `{"include": [...]}`, plus `maxResults` and `nextToken` |
| Create | `{"campaigns" \| "adGroups" \| "ads" \| "targets" \| "adAssociations": [ {...}, ... ]}` |
| Update | Same list keys; each item needs only its ID plus the fields to change (partial update) |
| Delete | `{"campaignIds" \| "adGroupIds" \| "adIds" \| "targetIds" \| "adAssociationIds": [...]}` |

Common value shapes:

- Budget (SP shape): `{"budgetType": "MONETARY", "recurrenceTimePeriod": "DAILY", "budgetValue": {"monetaryBudgetValue": {"monetaryBudget": {"value": 50}}}}`. The product contracts take no currency; the account's currency applies. Sponsored Display omits `recurrenceTimePeriod`. The merged `allv1_*` budget item requires both `currencyCode` and `recurrenceTimePeriod`, so send budget writes through the product-scoped tool (see [Which schema to trust](#which-schema-to-trust)).
- Dates: ISO 8601 date-times (`startDateTime`, `endDateTime`). "Start now" still needs a timestamp: compute it at execution time.
- Tags: `[{"key": "...", "value": "..."}]`, up to 50 where supported (1 on DSP).
- Update is partial, but array fields (budgets, tags, flights, bid adjustments) should be treated as replaced: send the full intended list built from a fresh read.

## Queries and paging

- `adProductFilter` is required on campaign, ad group, ad, and target queries and takes **exactly one** product. Sending two is rejected by the MCP before it reaches Amazon (*observed*). Query each product separately.
- `allv1_QueryAdAssociation` has no required filter.
- Results come back as `{"<entities>": [...], "nextToken": "..."}`, for example `{"campaigns": [...], "nextToken": "..."}` (*observed*). Repeat with `nextToken` until it is absent.
- `maxResults` and ID-filter sizes are per product, and Amazon enforces them: SP targets with `maxResults: 5000` returned 400 `BAD_REQUEST` (*observed*). Check the product reference and chunk ID lists.
- Filters a product doesn't support are rejected, not ignored: an SD target query with `negativeFilter` returned 400 `FIELD_VALUE_IS_INVALID` (*observed*).
- `nameFilter`, `keywordFilter`, and `productIdFilter` take `queryTermMatchType: EXACT_MATCH | BROAD_MATCH`.

Read-side fields include `state`, `status.deliveryStatus` and `status.deliveryReasons[]`, `creationDateTime`, `lastUpdatedDateTime`, `marketplaces`, `retailerScope`, and on targets `targetLevel` (*observed*). `deliveryStatus` explains why an enabled entity isn't serving (for example `NOT_DELIVERING`); report it alongside `state` when the user asks whether something is live.

## State, pause, and delete

- Create and update accept `state` `ENABLED` or `PAUSED` only. DSP campaigns and ad groups must be created `PAUSED` and enabled by a separate update.
- Queries can also return `ARCHIVED`. Nothing can set `ARCHIVED` through update, and nothing documents a way back out of it.
- **Delete archives, permanently.** `allv1_Delete*` is annotated destructive and not idempotent. Treat it as irreversible and offer pause first.
- DSP and Sponsored TV have no campaign or ad group delete; DSP has no ad delete (remove the association). Pause instead.

## Targets

Everything that decides which shoppers or placements an ad reaches is a target:

| Field | Meaning |
|---|---|
| `targetType` | `KEYWORD`, `PRODUCT`, `PRODUCT_CATEGORY`, `THEME`, `AUDIENCE`, `PRODUCT_AUDIENCE`, `LOCATION`, `CONTENT_CATEGORY`, plus DSP-only types (domain, app, device, daypart, brand safety, inventory source, video and placement attributes, third party) |
| `targetDetails` | One variant key matching the type: `keywordTarget`, `productTarget`, `productCategoryTarget`, `themeTarget`, `audienceTarget`, `productAudienceTarget`, `locationTarget`, and DSP variants |
| `negative` | `true` for negatives. Required on create, immutable |
| Level | Set by the parent: `adGroupId` → ad group level; `campaignId` without `adGroupId` → campaign level. Read back as `targetLevel` (`CAMPAIGN` observed). There is no level filter |
| `bid.bid` | Per-target bid where the product supports it (not ST or DSP) |

Update accepts only `targetId` with `bid`, `state`, and `tags` (product-dependent). Changing keyword text, match type, target type, negative flag, or parent requires creating a new target and pausing or archiving the old one. Present that as one change in the preview, and create the replacement before retiring the original so coverage never drops.

Category refinements are double-nested: `targetDetails.productCategoryTarget.productCategoryRefinement.productCategoryRefinement.productCategoryId`.

## Responses and errors

- **Query errors** arrive as an exception carrying HTTP 400 and a body `{"code": "...", "message": "..."}`, for example `BAD_REQUEST` or `FIELD_VALUE_IS_INVALID` (*observed*). Report the code and message; `message` text is not stable enough to branch on.
- **MCP validation errors** ("Invalid arguments for allv1_…: … must satisfy …") mean the request broke the merged schema and never reached Amazon. Fix the request; nothing was written.
- **Write responses** report per-item outcomes. Correlate each result with the item you sent by its position in the submitted array, not by name: names are not unique and created items have no ID until the response returns. Partial success is normal; one rejected item does not roll back the others.
- Error codes describe a condition together with the field they point at. Use code plus field location to explain a failure, never code alone.
- After any write, read the entities back. The read-back, not the write response, is what you report as the final state.

If a write response doesn't match these expectations, report it verbatim (without credentials or signed URLs) and reconcile by query before doing anything else.

## Which schema to trust

The `allv1_*` input schema is the union of every product, including `FULL_FUNNEL` and `RMS`, so it accepts fields and enum members your product rejects (`IMPRESSION` budgets, `GLOBAL` marketplace scope, `marketplaceConfigurations`, `retailerScope`, extra bid strategies). The MCP validates against that union only. Amazon validates against the product contract. Build requests from the product reference; when it doesn't cover a field, `get_schema` on the product-scoped tool for the same operation (`spv1_SPCreateTarget`, `dspv1_DSPUpdateCampaign`, …) is authoritative. Don't send fields that appear only in the merged schema.

The union is not looser everywhere. The merged campaign budget item, including DSP flight budgets, *requires* `monetaryBudget.currencyCode` and `recurrenceTimePeriod`. The product contracts take no currency, and Sponsored Display has no recurrence. A correct product-shaped budget therefore fails MCP validation on `allv1_CreateCampaign` and `allv1_UpdateCampaign`, and never reaches Amazon. `FULL_FUNNEL` is the exception: it has no product-scoped tool, so see [its reference](products/full-funnel.md). For every other product, send any campaign create or update that carries `budgets` or `flights` through the product-scoped tool: `spv1_SPCreateCampaign` / `spv1_SPUpdateCampaign`, `sbv1_SB…`, `sdv1_SD…`, `stv1_ST…`, `dspv1_DSP…`. It posts to the same `/adsApi/v1/create|update/campaigns` endpoint and validates against the product contract. Name that tool in the preview. The same rule applies to any other field the merged schema requires and the product contract lacks. Target bids are not affected: `allv1_UpdateTarget` `bid.bid` needs no currency (checked 2026-11-21). For any other write, compare the merged required lists with the product tool before sending.
