---
name: magic-hour-media
description: Generate, edit, and retrieve images, video, and audio with Magic Hour, including recovery of existing projects. Use when Magic Hour is requested or is the project's chosen media provider; preserve an explicitly requested alternative provider.
license: MIT
metadata:
  author: magichourhq
  version: "1.5.0"
---

# Magic Hour media

Deliver a usable image, video, or audio result. A queued project ID is an intermediate result unless the user asked only to submit a job.

Requires network access and either a connected Magic Hour MCP server or a Magic Hour API key with an HTTPS-capable runtime. Generation consumes Magic Hour credits.

## Work from the user's goal

Accept ordinary requests such as “put me in this clip,” “make my character do this” or “turn this portrait into an impossible scene.” Infer the placement and creative direction from supplied context; recommend one direction when needed. Ask only for missing information that changes the result or spending authority, not model names, schema fields or a completed prompt template. When creative choices are delegated, inspect and accept suitable intermediate assets yourself and continue. Respect requested review points and the existing budget. Lead delivery with the actual media; keep IDs and technical records in the project unless they are needed to explain a failure. For transformations or recreating a visual format, read [the remix workflow](references/remix.md); for music, read [music and performance](references/music.md).

## Connect to the right service

Use an already-connected Magic Hour creation MCP if available. Its hosted endpoint is `https://mcp.magichour.ai/`. The separate `https://docs.magichour.ai/mcp` searches documentation; it does not generate media.

If creation tools are unavailable, read `references/setup.md` in this skill for setup and the API fallback. Do not silently replace an existing client configuration. Never request an API key in chat or put it in source code; use the client's credential flow or `MAGIC_HOUR_API_KEY` in the local environment.

Use live tool schemas, or the [API documentation index](https://docs.magichour.ai/llms.txt), for current models, allowed durations, resolutions, and prices. Web-app features and plans do not imply identical API support. Do not copy a remembered model catalog or price table.

## Choose the workflow

| User goal                                           | Creation tool                                              | Completion tool                |
| --------------------------------------------------- | ---------------------------------------------------------- | ------------------------------ |
| Original artwork, portrait, cover or product image  | `ai_image_generator_create_image`                          | `wait_for_image_project`       |
| Edit an existing image while preserving its content | `ai_image_editor_create_image`                             | `wait_for_image_project`       |
| Animate a supplied image                            | `image_to_video_create_video`                              | `wait_for_video_project`       |
| Put a supplied face into existing footage           | `face_swap_create_video`                                   | `wait_for_video_project`       |
| Replace a whole character or transfer a performance | `character_replace_create_video`                           | `wait_for_video_project`       |
| Generate video from a text description              | `text_to_video_create_video`                               | `wait_for_video_project`       |
| Match an existing video's mouth movement to audio   | `lip_sync_create_video`                                    | `wait_for_video_project`       |
| Animate a portrait using supplied speech            | `ai_talking_photo_create_talking_photo`                    | `wait_for_video_project`       |
| Generate speech from text                           | `ai_voice_generator_create_audio`                          | `wait_for_audio_project`       |
| Create visuals from a supplied soundtrack           | `audio_to_video_create_video`                              | `wait_for_video_project`       |
| Evolving visuals with audio-sync camera effects     | `animation_create_video`                                   | `wait_for_video_project`       |
| Replace a face or body in a still photo             | `face_swap_photo_create_image` or `body_swap_create_image` | `wait_for_image_project`       |
| Restyle existing footage                            | `ai_video_editor_create_video`                             | `wait_for_video_project`       |
| Reinterpret footage in an animation/art style       | `video_to_video_create_video`                              | `wait_for_video_project`       |
| Caption the final picture and speech                | `auto_subtitle_generator_create_video`                     | `wait_for_video_project`       |
| Exact headline, crop, trim or assembled layout      | Available local editor/compositor                          | Inspect the exported file      |
| Retrieve a known project                            | No new creation call                                       | Matching wait or retrieve tool |

Tool names can have a client-specific prefix. Discover their current input schemas before calling them.

For full-person photo placement, distinguish Body Swap's `person_file_path` and `scene_file_path` from face-only replacement. For Video-to-Video, a custom prompt is ignored under the default prompt mode. Music Video Generator's web scene-assembly workflow, Video Extender and Video Upscaler have no equivalent dedicated endpoints in the public schema as checked September 11, 2026. Recheck support; when still absent, prepare the accepted inputs and direct web handoff instead of inventing tools. The [complete use-case map](https://github.com/magichourhq/skills/blob/main/docs/use-cases.md) links those workflows.

When installed, use `ai-video-generation` for a broad video request, `creator-video-remix` for a supplied reference format and `ai-media-quality-review` before final delivery. Use the other focused skill for image-to-video, face/body swap, text-to-video, image editing, talking video, character replace, music video, existing-video editing, product visuals, campaign kits, character consistency or thumbnails. Distinguish face-only identity changes from whole-character replacement, and a portrait's new speech from an existing video's performance. Do not require the user to memorize a skill name or install a companion just to finish a supported task. Reuse the current connection, project brief and accepted media; only ask for missing information that changes the output or authorization.

## Set the quality target

Before generating, translate the request into a short quality brief:

- intended use, aspect ratio, resolution, and duration
- subject, composition, viewpoint or camera move, lighting, and visual style
- details that must remain accurate, such as identity, product shape, logo, colors, text, clothing, or background
- failure conditions that would make the result unusable

Infer these from the user's project when possible. For a website hero, leave deliberate negative space where the interface places text. When exact identity, product geometry, packaging, or branding matters, prefer editing an authorized reference image over recreating it from text alone. For image-to-video, use the source image to define appearance and prompt mainly for subject motion, camera motion, timing, and what must stay fixed. Keep short videos to one coherent action unless the chosen duration and model support a more complex sequence.

Choose the model from the live schema according to the requested result. Prefer the current recommended model for a general request. When the schema describes a model as better for the needed behavior—such as typography, identity preservation, reference control, motion, audio, or speed—use that evidence to select it. Do not select the cheapest or fastest model when the user prioritizes final quality. Match resolution to the placement and critical detail: a tiny preview cannot prove small text is accurate. Use a cheaper preview when it answers a specific appearance or motion question, and label it as a preview. Check the total cost against the existing authorized budget; ask only when that authorization does not cover the intended work. Preserve the user's model, resolution, and spending limit.

Write a concrete prompt in natural language. Describe the subject and action first, then composition or camera, lighting and materials, style, and required constraints. Avoid conflicting styles, long adjective lists, and unsupported negative-prompt syntax. For edits, state the requested change and the elements that must remain unchanged. Request only missing inputs that materially affect the result. Preserve the user's chosen model and budget.

## Create within the authorized scope

Generation spends credits. Use `account_retrieve` when balance or tier affects feasibility; its result contains private account data, so report only the relevant balance or eligibility. Select supported parameters from the current schema. Prefer one output for an initial asset unless the user requests a batch. An authorized generation does not authorize buying credits, upgrading a plan, or running an unrequested batch.

For face and voice inputs, use material the user is entitled to use and follow the host's applicable safety rules. Do not imply ownership or consent from a public URL alone.

When local input files are needed:

1. Call `video_assets_generate_presigned_url` for their actual media types and extensions.
2. Upload each file's raw bytes to its returned `upload_url` with an HTTPS `PUT` from a runtime that can read the user's file. A successful URL allocation does not upload anything.
3. Verify the upload succeeded, then pass the matching returned `file_path` to the creation tool. Never pass a local filesystem path as a hosted storage path.

The hosted MCP cannot read arbitrary files on the user's computer. If the client cannot upload bytes, use the API/SDK route or ask for an accessible input. Do not invent a hosted local-file upload tool. Existing uploaded paths and stable public URLs returning raw media bytes may also be accepted; consult the current endpoint schema.

Submit the creation request once and retain the returned project ID before doing more work. If the request times out before an ID is returned, do not blindly resubmit: the first request may already have created a paid job. Reconcile it through the user's dashboard or available project evidence first, or explain the uncertainty and obtain direction.

## Complete and deliver

Call the matching wait tool with the existing ID. A polling timeout is not proof that generation failed. If still pending, retrieve or wait for the same project within the user's time budget; do not create another project to recover a wait timeout.

Proceed to download only after the project reports `complete`. On `error` or `canceled`, return the project ID and actionable error; do not claim a usable output. If no download is present, report that proof gap.

Use `exact_download_urls[n]` or `downloads[n].url` exactly as returned. Preserve every signed query parameter; `expires_at` is separate metadata. For an expired URL, retrieve the existing project again before considering regeneration. Never attach the Magic Hour API key to a storage download or presigned upload request.

When the user needs an asset in their application, download it into the requested project location, verify its actual media type and dimensions or duration, and use that local file. Requested dimensions are not proof of delivered dimensions. If the model ignores the ratio, use a crop only if it preserves the subject and required copy area; otherwise identify a supported reframing route within budget. Never stretch the image or label a wrong-size file as complete. Avoid embedding an expiring signed URL into production code.

Preview the finished media whenever the environment supports it. Evaluate it against the quality brief before claiming success:

- images: composition, crop, subject accuracy, anatomy, hands and faces, requested text and logo integrity, unintended lettering or brand-like marks, and visible artifacts
- video: the first and last frames, subject and camera motion, temporal consistency, identity and object preservation, flicker, warping, and unwanted cuts
- lip sync or talking portraits: timing, mouth shapes, face stability, expression, audio continuity, and the requested duration
- audio: intelligibility, pronunciation, pacing, clipping, silence, and audible artifacts

For speech, keep stage directions out of text that will be read aloud, use a live-supported voice, listen through the final word, and measure duration before synchronizing pictures. Reuse accepted audio for visual revisions. Preserve pronunciation notes and the approved voice choice for later work; do not assume a preset implies endorsement or permission to impersonate someone.

If the result misses a required criterion, identify the specific failure and revise the prompt, input, model, or resolution that caused it. Change the smallest useful variable so the next result is informative. A new generation spends more credits, so iterate only within the user's authorized budget. If no further generation is authorized, return the best result with the failed criterion stated plainly.

Return the finished artifact or usable link, where it was saved, and any material limitation. A tool connection, schema match, or accepted request is not proof of completed generation.

For recurring work, retain accepted references, local output paths, project IDs and the few identity/voice/layout decisions needed next time in the project's existing brief. Do not create a competing registry or save signed URLs as permanent assets. On a later request, read that brief and reuse accepted work; copy, crop and download-link changes usually do not need a new generation.
