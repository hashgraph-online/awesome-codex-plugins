---
name: magic-hour-explainer-video
description: Turn a source document or brief into a finished narrated explainer using Magic Hour images, speech and video, with a coherent visual style and complete sentences. Use for educational, product and process explainers when Magic Hour is the chosen media provider.
license: MIT
metadata:
  author: magichourhq
  version: "1.0.0"
---

# Magic Hour explainer video

Deliver a watchable explanation with a beginning, a useful idea and an ending, plus its editable script. A folder of disconnected clips is not the finished video.

Use the connected Magic Hour MCP at `https://mcp.magichour.ai/` or the project's existing API integration. Use the [connection guide](https://github.com/magichourhq/skills/blob/main/docs/quickstart.md#connect-once) if needed. Verify `account_retrieve` and discover current image, audio and video tool schemas. Discover a local or connected compositor before promising an assembled video; Magic Hour generation tools do not imply a general-purpose assembly endpoint.

## Convert the brief into a clear story

Read the actual source material. Decide what the audience should understand or do afterward, then write a short script grounded in that source. Preserve uncertainty and distinguish an illustration from evidence. Keep source links alongside the relevant script passage so factual claims remain traceable.

Use the requested duration and audience. When choices are delegated, choose a fitting visual style, pace and available voice and proceed within the authorized budget. Ask only for a blocking source, rights/identity requirement or unresolved meaningful choice. Do not force a two-turn setup questionnaire, a one-minute minimum or identical ten-second scenes.

Plan natural beats: one idea and one visual purpose per beat. Estimate length from a read-through, then fit the cut to measured audio. For longer videos, read [timing and assembly](references/timing-and-assembly.md). Avoid writing more narration than can fit and compensating with unreadably fast speech.

## Make speech and visual identity first

Prefer an authorized supplied recording when it meets the brief. For TTS, call `ai_voice_generator_create_audio` with a voice actually listed in the live schema; do not invent a neutral narrator ID. If the available presets cannot meet a professional voice requirement, use an authorized reference with `ai_voice_cloner_create_audio` or explain the exact missing capability. Do not silently substitute a named person for a requested original narrator. Label a synthetic demonstration voice accurately.

Record each created audio ID and use `wait_for_audio_project`. Retrieve and measure the actual file. Listen when the environment supports it, checking pronunciation, missing words, pauses, noise and the final sentence. If listening was unavailable, state that limitation; duration and successful API status do not establish speech quality. Fix a mispronounced segment before paying for its visuals.

Create one style image with AI Image Generator, or edit an authorized reference with AI Image Editor. Inspect it before animation. Keep the same reference, palette, character details, line treatment and aspect ratio across scenes. Diagram labels and exact words belong in editable layout layers. Reuse an accepted still for a new scene when appropriate; avoid text-to-video when identity matters.

Animate approved stills with `image_to_video_create_video` only where motion helps explain the idea. A precisely composed diagram, still with a purposeful camera move or local timeline animation can communicate better than a paid generated clip. Keep those methods accurately labeled. Budget narration, stills, motion and repairs together, and do not add paid motion merely to use every tool.

## Assemble and deliver the whole explanation

Persist project IDs and poll the existing jobs; never blindly repeat a creation after an ambiguous response. Use the actual clip and audio durations in the compositor. Let every sentence finish, including a short tail after the final word. Add exact labels, source credits and transitions without covering important content. Use music only when suitable and authorized; keep speech clear.

Inspect the entire final cut for pacing, visual continuity, synchronization, legibility, clipped speech and accidental silent/black tails. Generate or align requested captions against the final narration and cut, not an earlier script. Export the requested aspect ratio and codec, reopen it, and return the video first, with the script, sources and editable timing/layout assets. Retain clean masters for future languages or revisions; changing one sentence should not recreate the entire project.
