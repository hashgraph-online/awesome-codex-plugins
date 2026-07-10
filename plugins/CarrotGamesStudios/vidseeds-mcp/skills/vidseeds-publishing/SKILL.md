---
name: vidseeds-publishing
description: Use for VidSeeds MCP publishing - platform connections, OAuth connect URLs, activate YouTube channel, update connection settings, preflight/confirm/cancel publish, publish status, direct YouTube upload, and updating live YouTube metadata.
license: MIT
---

# Publishing & connections (MCP)

## Connect platforms

1. `vidseeds_list_platform_connections` - see what is connected (no OAuth secrets returned).
2. `vidseeds_get_platform_connect_url` - OAuth URL for a platform the user must open in a browser.
3. After OAuth completes, list again to get `connectionId`.

**YouTube channel selection (multi-channel accounts):**

- `vidseeds_set_active_youtube_channel` - which channel is active for uploads/metadata.

**Settings:**

- `vidseeds_update_connection_settings` - per-connection options (e.g. content language, description footer, and per-asset generation guidelines for titles/descriptions/tags/thumbnails). Read current values via `vidseeds_get_platform_connection`. Guidelines are sent to the model on every generation by default; generation tools accept `applyGuidelines: false` to ignore them for one call.
- `vidseeds_disconnect_platform_connection` - remove a connection.

## Publish a project

Typical sequence:

1. `vidseeds_get_project_snapshot` - verify per-platform config (`vidseeds_update_project_platform_config` if needed).
2. `vidseeds_preflight_publish` - compatibility checks before spend.
3. `vidseeds_confirm_publish` or `vidseeds_publish_project` - start publish (see tool descriptions for `now` vs `scheduled`).
4. `vidseeds_get_publish_status` - poll until platforms complete or fail.
5. On failure: `vidseeds_retry_publish_target`; to abort schedule: `vidseeds_cancel_or_unschedule_publish`.

## Direct YouTube upload (bypassing manual Studio upload)

For large files the user uploads from their machine through VidSeeds:

1. `vidseeds_prepare_youtube_upload` - session/upload instructions.
2. User/agent completes bytes per returned guidance.
3. `vidseeds_complete_youtube_upload` - finalize.

Pair with project metadata from `vidseeds-projects`.

## Organic promo campaign packs

For product URL or product brief workflows, keep generation, draft creation, and publishing separate:

1. `vidseeds_generate_promo_campaign_pack` - generate one reviewable organic campaign pack.
2. Select the variants the user wants to use.
3. `vidseeds_create_social_posts_from_campaign_pack` - convert only selected variants into Social Planner drafts.
4. `vidseeds_preflight_social_post` - check each draft against platform rules and required media/context.
5. `vidseeds_approve_social_post` - approve only after user review.
6. `vidseeds_schedule_social_post` or `vidseeds_publish_social_post_now` - schedule or publish after explicit approval.

## Update live YouTube video metadata

- `vidseeds_update_youtube_metadata` - patch title/description/tags on an existing video (connected channel).

## Thumbnail on YouTube

- `vidseeds_publish_thumbnail_to_youtube` - set thumbnail on a published video (see `vidseeds-thumbnails`).

## Channel description

- `vidseeds_publish_channel_description` - update channel-level description when supported.

## History republish

- `vidseeds_republish_history_item` - re-send from optimization history (check tool inputs).

## Before publishing

- Confirm seeds and quota: `vidseeds-efficiency` (`vidseeds_get_seed_balance`).
- Ensure the right `connectionId` is set on each enabled platform in project config.
