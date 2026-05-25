---
name: vidseeds-projects
description: Use for VidSeeds MCP project workflows — create a project from YouTube, list/get/snapshot, regenerate metadata (sync or async), translate metadata, apply thumbnails, and update per-platform config before publish.
---

# Projects (MCP)

A **project** is the workspace for one video across YouTube, TikTok, Instagram, Facebook, LinkedIn, and X.

## Discover projects

- `vidseeds_list_projects` — browse with limits/filters per tool schema.
- `vidseeds_get_project` — single project record.
- `vidseeds_get_project_snapshot` — project + platform config in one call (prefer over many gets).

## Create from YouTube

1. `vidseeds_create_project_from_youtube` with the YouTube video id/URL (see tool inputs).
2. If metadata generation is async, poll `vidseeds_get_create_project_metadata_job` until `completed`.
3. Confirm with `vidseeds_get_project_snapshot`.

## Regenerate platform metadata

Re-runs optimized titles/descriptions/tags per platform from the stored transcript.

| Mode         | Tool                                           | Notes                                           |
| ------------ | ---------------------------------------------- | ----------------------------------------------- |
| Fast / small | `vidseeds_regenerate_project_metadata`         | Can exceed ~100s edge timeout on large projects |
| Production   | `vidseeds_regenerate_project_metadata_async`   | Returns `jobId` immediately                     |
| Poll         | `vidseeds_get_regenerate_project_metadata_job` | Same result shape as sync when done             |

**Voice:** If the user has multiple YouTube channels, pass `channelId` (`UC…`). With one connection, omit for auto-resolve. `voiceBlendRatio` optional (tool default documented in `tools/list`).

Reuse the same `requestId` on transport retries to avoid double seed charges when the tool allows it.

## Optimize metadata without a full project (standalone)

- `vidseeds_optimize_marketing_metadata` / `vidseeds_optimize_marketing_metadata_async` — needs transcript (e.g. from `vidseeds_transcribe_audio` or YouTube transcript tools).
- Poll: `vidseeds_get_optimize_marketing_metadata_job`.

## Translate project metadata

- `vidseeds_translate_project_metadata` — localization across supported languages (no voice dubbing on VidSeeds.ai).

## Thumbnail on project

- Generate per `vidseeds-thumbnails`, then `vidseeds_apply_thumbnail_to_project`.

## Per-platform publish config

- `vidseeds_update_project_platform_config` — enable platform, title/description/tags, schedule, connection, thumbnail URL override.

## Publish

After config is ready, use `vidseeds-publishing` (`vidseeds_preflight_publish` → `vidseeds_confirm_publish` / `vidseeds_publish_project`).

## History

- `vidseeds_list_optimization_history`, `vidseeds_get_optimization_history_item`, `vidseeds_reoptimize_history_item` — past runs and re-run from history.
