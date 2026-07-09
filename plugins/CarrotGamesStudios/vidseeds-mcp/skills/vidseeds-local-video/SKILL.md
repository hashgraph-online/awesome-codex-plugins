---
name: vidseeds-local-video
description: Use when the user's video is on disk - VidSeeds MCP probe, frame/clip extraction, ffmpeg recipes, precision trim, and midroll analysis. Hosted tools return commands/recipes to run locally; media stays on the user's machine.
license: MIT
---

# Local video media (MCP)

VidSeeds.ai follows **client-first** media: the hosted MCP server does not read files from the user's computer. Tools return **recipes** (ffmpeg/ffprobe commands) or accept **base64 frames** the agent extracted locally.

## Probe a file

- `vidseeds_probe_local_video` - duration, resolution, codecs; use before trim or thumbnail frame picks.

## Frames and clips

| Goal                        | Tool                               |
| --------------------------- | ---------------------------------- |
| Still frames for thumbnails | `vidseeds_extract_video_frames`    |
| Short clip for context      | `vidseeds_extract_video_clip`      |
| Generic transcode recipe    | `vidseeds_transcode_format_recipe` |
| Media helper commands       | `vidseeds_get_local_media_recipe`  |

Run returned shell commands on the **user's machine** (requires ffmpeg/ffprobe installed). Pass results back into thumbnail tools as `frames` on `vidseeds_generate_thumbnail` when needed.

## Precision trim

1. `vidseeds_analyze_precision_trim` - suggested cut points, segment catalog, seed cost preview.
2. `vidseeds_plan_precision_trim` - AI edit plan (CritiquePlan) with genre-aware processing.
3. `vidseeds_execute_precision_trim` - export recipe/commands for local ffmpeg.

### V3 Genre-Aware Processing (2026-06-27)

Precision Trim V3 adds **genre classification** + **soundscape analysis** + **motion profile** + **hook detection** + **semantic boundaries** as parallel client-side signals. These are passed as optional metadata in `vidseeds_analyze_precision_trim` / `vidseeds_plan_precision_trim` inputs:

- `detectedGenre` - overrides automatic genre detection (speech_driven, action_dynamic, ambient_relax, visual_primary, mixed_narrative, tutorial)
- `soundscape` - spectral classification from PCM (silence/speech/music/ambient/noise)
- `motionProfile` - frame-by-frame pixel diff analysis (static/slow/action/scene_change)

**How it affects plans:**

- **ambient_relax**: high silence tolerance (15s+), preserves zero-word scenes, < 20% cut ratio
- **action_dynamic**: aggressive pause trimming (500ms+), up to 40% cut ratio
- **speech_driven**: cut at semantic boundaries, moderate trimming
- **visual_primary**: preserves scenes without speech, cut only on true silence
- **mixed_narrative**: uses all signals - only cuts when multiple agree
- **tutorial**: precision trimming, no speed around instructions

## Midroll placement

- `vidseeds_analyze_midroll_opportunities` - suggested mid-roll times from transcript/context (analysis only; user edits in their editor).

## Thumbnails from local file

Prefer the **vidseeds-local** stdio MCP tool `vidseeds_generate_thumbnail_from_video` when the whole pipeline should run on-disk (see `vidseeds-thumbnails`).

## YouTube-hosted source (not local path)

- `vidseeds_get_youtube_video_transcript`, `vidseeds_get_youtube_video_captions` - text from YouTube without downloading video to the server.

## Do not

- Expect hosted tools to accept arbitrary filesystem paths for upload/processing.
- Re-run probe/extract in a loop - cache probe results for the session.
