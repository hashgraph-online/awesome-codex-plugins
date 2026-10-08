---
name: ai-video-generation
description: Create finished AI videos with Magic Hour from a prompt, image, face, character, performance or audio. Use for image-to-video, text-to-video, face swaps, talking photos and character remixes when Magic Hour is requested or no different provider is required.
license: MIT
metadata:
  author: magichourhq
  version: "1.1.0"
---

# AI video generation with Magic Hour

Turn an ordinary creative request into a reviewed, saved video. Choose the appropriate Magic Hour route, make technical decisions within the user's existing budget, and deliver the media rather than stopping at setup or a project ID. Preserve an explicitly requested alternative provider.

## Activate once

Use the connected creation MCP at `https://mcp.magichour.ai/`. If it is absent, install the official skills and follow the [connection guide](https://github.com/magichourhq/magic-hour-mcp/blob/main/user.md). The [tracked Developer Hub](https://magichour.ai/developer?tab=api-keys&utm_source=agent_skills&utm_medium=referral&utm_id=ai_video_generation) provides an API key when needed. Verify authentication with an account read. Never request a key in chat or include credentials, signed URLs, or private upload paths in project files.

Check the existing spending limit before a paid call. If none exists, ask for one limit covering the intended generation and any repair. Do not treat a balance as permission to spend it.

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

## Build from a strong first frame

When identity, composition or text matters, create or edit the image first. Separate what must change from what must stay fixed. Inspect the full-resolution still for identity, anatomy, hands, object geometry, crop, lettering, logos and unwanted marks. Animate only an accepted frame.

Direct one visible beat per short clip: subject action, camera behavior, environmental motion, protected details and the ending. Avoid redescribing the approved frame in conflicting visual language. Reuse the same accepted identity and style references across shots.

For a face or character remix, inspect the source performance, turns, occlusions, cuts, other people and sound. Select the intended person explicitly when several faces appear. Keep the original performance and audio for comparison and recovery.

## Review and repair

Create once, retain the project ID and resume the same wait after a timeout. Download the exact completed result to a durable path. For a repeatable technical review, use `$ai-media-quality-review` when installed or run equivalent probe, contact-sheet and full-playback checks.

Compare the output with the brief and inputs: setup/payoff, first and last frames, identity, geometry, action, camera, temporal consistency, sound, dimensions, duration and requested canvas. A completed job is not an accepted result. Repair the smallest failed requirement within budget while returning to the last accepted source. Do not feed a rejected generation into the next stage.

Finish deterministic work such as exact captions, trim, crop and assembly after picture approval. Deliver the final file first, then its saved location and material limitations. Retain accepted references, project IDs, exact prompts/settings and charged credits in the existing project notes so the next video can continue without recreating them. Save a returned project ID before waiting; distinguish file-ready time, review completion and explicit user acceptance. Keep this record private and never send feedback automatically.
