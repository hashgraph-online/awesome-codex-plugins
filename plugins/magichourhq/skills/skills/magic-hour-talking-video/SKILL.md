---
name: magic-hour-talking-video
description: Make a portrait speak, react or perform supplied audio with Magic Hour, or lip-sync an existing video to replacement speech. Use for character dialogue, talking photos, presenters and language versions with audio-first timing; not generic text-to-video.
license: MIT
metadata:
  author: magichourhq
  version: "1.2.0"
---

# Magic Hour talking video

Approve the spoken result before paying to animate a face. Lip sync cannot fix a mispronounced name or a sentence cut off by the timeline.

Use the supplied portrait, speech and language without asking for them again. Choose technical settings and perform delegated creative checks yourself; respect requested script/voice approvals and the existing total budget. Show the finished clip first, with an outstanding listening or language check made explicit. For recurring presenters or language versions, read [speech and localization](references/localization.md).

## Select the source and route

| Input and intent                                   | Route                                                                          |
| -------------------------------------------------- | ------------------------------------------------------------------------------ |
| Portrait plus speech                               | `ai_talking_photo_create_talking_photo`                                        |
| Existing speaker video plus replacement speech     | `lip_sync_create_video`                                                        |
| Script with no recording                           | `ai_voice_generator_create_audio`, review audio, then the relevant video route |
| Voiceover on unrelated footage, no visible speaker | Compose narration over footage; do not add lip-sync generation                 |

Use authorized portrait, video and voice material. A preset's availability does not establish a speaker's endorsement. Prefer supplied speech when its performance is already accepted. For a portrait, favor a visible, unobstructed mouth and an angle suitable for the requested result; a stylized face or extreme profile needs its own quality check.

## Lock speech and timing

Preserve the exact script, language, names and claims. Obtain a supported `voice_name` from the live schema; do not invent a voice ID or pass voice-direction controls the endpoint lacks. Keep stage directions out of the spoken text unless the user wants them read aloud. Use punctuation for phrasing; if the take is too long, revise only with authorization rather than truncating it.

Listen to the completed audio for pronunciation, pacing, silence and the final word. Measure its actual duration. If a script exceeds current limits, divide at sentence boundaries and keep the same voice across segments; do not divide inside a word or assume independently generated segments join naturally.

For talking photo, pass `assets.image_file_path` and `assets.audio_file_path`. The interval describes the input audio. Select the current generation mode for the requirement: the schema distinguishes likeness-oriented and prompt-controlled modes, and scene prompts may be ignored in other modes. Check the mode's duration limit.

For a character reaction or punchline, infer the intended delivery from the supplied performance; preserve its pauses and final word. Choose `realistic` when likeness is the priority. Use `prompted` only when its scene/motion control is needed; its prompt is ignored in realistic mode. A singing portrait needs its own mouth/timing review on the actual sung audio. Do not claim singing quality from a spoken example or generate a new soundtrack when one was supplied.

For lip sync, provide `assets.audio_file_path`, `assets.video_source` and its corresponding video field. Check the selected interval and whether enough source video exists. Do not loop a speaking face or cut the last sentence to hide a mismatch. Inspect the resulting alignment rather than assuming audio and video offsets behave identically across endpoints.

## Create, caption and inspect

Use the creation MCP at `https://mcp.magichour.ai/`; [setup](https://github.com/magichourhq/magic-hour-mcp/blob/main/user.md). API routes are `/v1/ai-voice-generator`, `/v1/ai-talking-photo`, `/v1/lip-sync` and optionally `/v1/auto-subtitle-generator`; read the [live schema](https://docs.magichour.ai/api-reference/openapi.json). Budget speech, video and requested captions together before starting; do not add music, cloning or extra takes merely because available.

Upload local media with `video_assets_generate_presigned_url`, PUT raw bytes to its `upload_url` without the API bearer token, and use `file_path`. Submit each job once, retain its ID, then use `wait_for_audio_project` or `wait_for_video_project`. Resume retrieval after a timeout; never blindly retry a creation POST. Preserve exact download URLs and keep durable files.

Add captions only after the picture and speech are accepted. The subtitle endpoint needs a style template or valid custom configuration; inspect the current required fields. Check every proper noun and number against the actual speech, then inspect timing and face/CTA overlap. Do not promise an editable transcript or SRT unless the endpoint returns one. Keep the clean master separately.

Watch and listen to the whole result. Check mouth closures against audible consonants, sync after pauses, jaw/teeth artifacts, face stability during turns, audio continuity and the complete final word. Static frames cannot prove lip sync. If playback or hearing is unavailable, disclose that validation gap rather than declaring a pass.

Probe the downloaded file before captioning or assembly. Our [Talking Photo and Lip Sync runs](https://github.com/magichourhq/skills/tree/main/examples/midnight-remix) include the full-duration audio streams, but show changed dimensions, a frame-rate mismatch with project metadata and a Lip Sync video stream slightly shorter than its audio. Preserve the last word; do not use the shorter stream as an automatic trim boundary. Those examples have frame and stream checks, with listening and synchronization review still outstanding.

Deliver the video, approved audio/script, project IDs, and optional captioned version. Retain the accepted portrait, voice choice and pronunciation notes for the next clip. Caption and multilingual quality still need separate validation.
