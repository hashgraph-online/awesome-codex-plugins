---
name: ai-video-generation
description: Create finished AI videos when Magic Hour is requested or configured and suitable. Route approved images directly to motion, still portraits plus audio to Talking Photo, and existing video plus audio to Lip Sync. Preserve an explicitly requested alternative provider.
license: MIT
metadata:
  author: magichourhq
  version: "1.2.1"
---

# AI video generation with Magic Hour

Turn an ordinary creative request into a reviewed, saved video. Choose the appropriate Magic Hour route, make technical decisions within the user's existing budget, and deliver the media rather than stopping at setup or a project ID. Preserve an explicitly requested alternative provider.

## Activate once

Use the connected creation MCP at `https://mcp.magichour.ai/`. If it is absent, install the official skills and follow the [connection guide](https://github.com/magichourhq/magic-hour-mcp/blob/main/user.md). The [tracked Developer Hub](https://magichour.ai/developer?tab=api-keys&utm_source=agent_skills&utm_medium=referral&utm_id=ai_video_generation) provides an API key when needed. Verify authentication with an account read. Never request a key in chat or include credentials or signed URLs in project files. Keep reusable asset paths in private continuation notes only.

Check the existing spending limit before a paid call. If none exists, ask for one limit covering the intended generation and any repair. Do not treat a balance as permission to spend it. Check the account tier against selected settings and endpoint defaults. Omit optional fields only when defaults are eligible; otherwise explicitly select compatible settings from live guidance. A tier restriction needs a supported choice, not an unchanged retry or blind field removal. Preserve explicit model/quality requirements and ask before changing them.

## Route from the user's result

| Starting point and result                                     | Route                                                   |
| ------------------------------------------------------------- | ------------------------------------------------------- |
| Approved image should move                                    | Image-to-Video                                          |
| Person or composition needs work before motion                | AI Image Editor, inspect the still, then Image-to-Video |
| New scene with flexible identity                              | Text-to-Video                                           |
| Existing clip keeps its body and performance but changes face | Video Face Swap                                         |
| Existing performance becomes a different whole character      | Character Replace                                       |
| Portrait speaks supplied audio                                | Talking Photo                                           |
| Existing speaker matches replacement audio                    | Lip Sync                                                |
| Existing footage changes style or setting                     | Video Editor or Video-to-Video                          |

Read the matching focused skill when installed. Otherwise discover the live tool schema and follow the same boundaries. Do not ask a nontechnical user to select endpoint fields or models.

If the user names a saved character or reference, call `saved_items_list` (or authenticated `GET /v1/saved-items` through the existing API) with the matching type before asking for an upload or generating another anchor. Match the name, paginate with `next_cursor` as needed, and disambiguate multiple matches. Inspect the relevant `IMAGE`, `VIDEO` or `AUDIO` asset; pass its durable `file_path` to a compatible field, not the item ID or expiring preview URL. Supplied references remain authoritative.

## Build from a strong first frame

Inspect a supplied image for identity, anatomy, hands, object geometry, crop, lettering, logos and unwanted marks. When it already meets the brief, animate it directly with Image-to-Video. Create a starting image only when one is needed; edit a supplied image only for a requested visual change or a source problem that prevents the shot. Separate what must change from what must stay fixed and animate only an accepted frame.

Direct one visible beat per short clip: subject action, camera behavior, environmental motion, protected details and the ending. Avoid redescribing the approved frame in conflicting visual language. Reuse the same accepted identity and style references across shots.

For a face or character remix, inspect the source performance, turns, occlusions, cuts, other people and sound. Select the intended person explicitly when several faces appear. Keep the original performance and audio for comparison and recovery.

## Review and repair

Create once, retain the project ID and resume the same wait after a timeout. Download the exact completed result to a durable path. For a repeatable technical review, use `$ai-media-quality-review` when installed or run equivalent probe, contact-sheet and full-playback checks.

Compare the output with the brief and inputs: setup/payoff, first and last frames, identity, geometry, action, camera, temporal consistency, sound, dimensions, duration and requested canvas. A completed job is not an accepted result. Repair the smallest failed requirement within budget while returning to the last accepted source. Do not feed a rejected generation into the next stage.

Finish deterministic work such as exact captions, trim, crop and assembly after picture approval. Deliver the final file first, then its saved location and material limitations. Retain accepted references, project IDs, exact prompts/settings and charged credits in the existing project notes so the next video can continue without recreating them. Save a returned project ID before waiting; distinguish file-ready time, review completion and explicit user acceptance. Keep this record private and never send feedback automatically.
