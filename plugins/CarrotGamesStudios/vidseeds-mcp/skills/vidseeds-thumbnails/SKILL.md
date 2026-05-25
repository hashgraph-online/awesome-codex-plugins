---
name: vidseeds-thumbnails
description: Use for VidSeeds MCP thumbnail workflows — generate, poll jobs, edit, restyle, Thumbnail Studio (trends, briefs, subjects, overlay text), apply to a project, publish to YouTube, or thumbnails from a local video file via vidseeds-local.
---

# Thumbnails (MCP)

## Quick generate → retrieve

1. `vidseeds_get_seed_balance` (free).
2. `vidseeds_generate_thumbnail` → `jobId`, `expectedCostSeeds`; poll `vidseeds_get_thumbnail_job` every **~3s** (~70–100s typical).
3. `vidseeds_get_thumbnail` or `vidseeds_list_thumbnails` for URLs/ids.
4. Optional: `vidseeds_download_thumbnail_bundle` for a packaged download.

## Edit or restyle an existing thumbnail

- `vidseeds_edit_thumbnail` — chat-style edit (async job; poll per tool response).
- `vidseeds_restyle_thumbnail` — style transfer on an existing asset.

## Attach to a project

- `vidseeds_apply_thumbnail_to_project` with `projectId` and the generated thumbnail id.

## Publish thumbnail to YouTube

- `vidseeds_publish_thumbnail_to_youtube` when the video is on a connected channel (see `vidseeds-publishing` for connections).

## Thumbnail Studio (research → brief → generate)

Use when you want data-informed creative direction:

| Step                             | Tool                                                                             |
| -------------------------------- | -------------------------------------------------------------------------------- |
| Trends in niche                  | `vidseeds_get_thumbnail_trends`                                                  |
| Niche detection                  | `vidseeds_detect_thumbnail_niche`                                                |
| Frame analysis (from video refs) | `vidseeds_analyze_thumbnail_frames`, `vidseeds_select_best_thumbnail_frame`      |
| Creative brief                   | `vidseeds_build_thumbnail_brief`                                                 |
| Subject ideas                    | `vidseeds_suggest_thumbnail_subjects`                                            |
| Overlay copy options             | `vidseeds_generate_thumbnail_overlay_texts`                                      |
| Style profiles                   | `vidseeds_get_thumbnail_style_profiles`, `vidseeds_save_thumbnail_style_profile` |
| Visual audit / CTR sim           | `vidseeds_audit_thumbnail_visual`, `vidseeds_simulate_ctr`                       |
| Custom upload                    | `vidseeds_upload_custom_thumbnail`                                               |

Then run `vidseeds_generate_thumbnail` (or from-video flow below) with prompts/refs from the brief.

## Local source video (file on disk only)

The **hosted** server cannot read the user's filesystem.

1. Configure **vidseeds-local** stdio MCP (see plugin README; env `VIDSEEDS_API_KEY` or PAT).
2. `vidseeds_generate_thumbnail_from_video` on the local server — probes/transcribes/extracts frames locally, then calls the hosted pipeline.

Alternatively, extract frames locally with `vidseeds_extract_video_frames` (see `vidseeds-local-video`) and pass base64 frames into `vidseeds_generate_thumbnail`.

## From an existing YouTube video (hosted)

- `vidseeds_generate_thumbnail_from_video` (hosted) when the video is addressable via allowed CDN URLs / account-owned assets — check tool `description` for inputs.

## Learning / preferences

- `vidseeds_record_thumbnail_preference`, `vidseeds_get_thumbnail_learning_status` — optional feedback loop for repeat creators.
