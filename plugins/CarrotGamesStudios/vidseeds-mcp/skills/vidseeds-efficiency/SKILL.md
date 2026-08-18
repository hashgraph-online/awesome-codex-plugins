---
name: vidseeds-efficiency
description: Use before expensive VidSeeds MCP workflows - seeds, daily MCP call quotas, async jobId polling, when to call vidseeds_get_seed_balance, and avoiding retry loops on MCP_QUOTA_EXCEEDED or insufficient seeds.
license: MIT
---

# VidSeeds MCP efficiency

Read this before multi-step or charge-bearing workflows.

## Orient first (free)

New to this server, or unsure which tool does the job? Call **`vidseeds_guide`** - it returns the capability map, the recommended tool chain for a stated `goal`, and what VidSeeds does not do. It is free and quota-exempt, so it never costs seeds or a call-bucket token. The server's `initialize` instructions and the `vidseeds://guide` resource carry the same orientation; workflow **prompts** (e.g. `optimize-youtube-video`, `make-thumbnail`) hand you the ready-made tool chain. Reach for these before concluding a capability is missing. **Parameter-level field docs are intentionally omitted from `tools/list` JSON schemas to save context** - use `vidseeds_guide` (with a `goal`) or read `vidseeds://guide` when you need argument semantics beyond types/enums.

## Two cost layers

1. **Per-tool seeds** - Some tools spend seeds (thumbnails, intelligence, translation, etc.). Read-only tools are free. Charge-bearing tools state their seed cost in the first sentence of their compressed `tools/list` description; when it is not there, call `vidseeds_guide` with the tool name for the confirmed cost. Confirm with the user before charge-bearing calls. (2026-06: use `fields: ["description","tags"]` on regenerate for light/correct-price partials; thumbnail edits cost more than generation when using input reference image.)
2. **Daily MCP call quota** - Almost every tool call counts toward a plan bucket (continuous refill, not midnight reset). When the bucket is empty, each extra call costs **1 seed** on top of any per-tool cost.

| Plan    | Refill / day | Bucket cap |
| ------- | ------------ | ---------- |
| Sprout  | 1,000        | 2,000      |
| Growth  | 3,000        | 6,000      |
| Harvest | 8,000        | 16,000     |
| Agency  | 20,000       | 40,000     |
| Trial   | 1,000        | 1,000      |

**Free and quota-exempt:** `vidseeds_get_seed_balance`, `vidseeds_get_seed_balance_and_subscription`, `vidseeds_guide`.

## Before expensive work

1. `vidseeds_get_seed_balance` - seeds, remaining included MCP calls, overage rate (free).
2. Tell the user expected per-tool seed cost (from the tool's compressed description, or `vidseeds_guide` when the description omits it).
3. Prefer **async + poll** for long jobs instead of hammering sync tools that may time out at the edge.

Promo campaign note: `vidseeds_generate_promo_campaign_pack` is seed-charged on successful AI generation; conversion to drafts with `vidseeds_create_social_posts_from_campaign_pack` is not the billable AI step.

## Async job pattern

Many writes return immediately with `jobId` (and often `pollTool` or a named poll tool in the response):

1. Call the async or generate tool → capture `jobId` and `expectedCostSeeds` if present.
2. Poll the indicated tool every **~3s** until `completed` or `failed`.
3. On `failed`, surface the error once; do not retry in a tight loop.

Examples:

| Start                                        | Poll                                           |
| -------------------------------------------- | ---------------------------------------------- |
| `vidseeds_generate_thumbnail`                | `vidseeds_get_thumbnail_job`                   |
| `vidseeds_regenerate_project_metadata_async` | `vidseeds_get_regenerate_project_metadata_job` |
| `vidseeds_create_project_metadata_async`     | `vidseeds_get_create_project_metadata_job`     |
| `vidseeds_optimize_marketing_metadata_async` | `vidseeds_get_optimize_marketing_metadata_job` |

Thumbnail generation is typically **70–100s**. Project metadata regeneration can be **60–130s** - prefer async variants for production.

## Errors - do not spin

| Code / message                | Action                                                                          |
| ----------------------------- | ------------------------------------------------------------------------------- |
| `AUTH_REQUIRED` / 401         | PAT missing - see `vidseeds-setup`                                              |
| `SUBSCRIPTION_REQUIRED` / 402 | Trial ended - user must subscribe                                               |
| `MCP_QUOTA_EXCEEDED`          | Stop retrying; show top-up link from error; wait for bucket refill or add seeds |
| Insufficient seeds            | `vidseeds_get_seed_balance`; user tops up at <https://vidseeds.ai/seeds>        |

## Minimize round-trips

- Use `vidseeds_get_project_snapshot` when you need project + platform rows in one call instead of many `get_project` loops.
- For connections, `vidseeds_list_platform_connections` before per-id fetches unless you already have `connectionId`.
- Batch discovery: `vidseeds_get_bulk_video_metadata` when comparing many videos.
- Reuse the same `requestId` / idempotency keys on retries the tool docs allow - avoids double billing.

## When `tools/list` is enough

`tools/list` descriptions are compressed (first sentence + safety signals: seed cost, destructive warnings, async polling); parameter shapes and full argument semantics live in **`vidseeds_guide`** / `vidseeds://guide`. Skills teach composition; do not duplicate the full catalog here.
