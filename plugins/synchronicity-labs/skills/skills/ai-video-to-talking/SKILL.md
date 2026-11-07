---
name: ai-video-to-talking
description: Add or replace dialogue in AI-generated video with sync. labs (sync.so). Takes a clip from Veo, Kling, Sora, Runway, Hailuo, Luma, Seedance, Wan or any other video generator, with the user's audio or a line that sync. voices, and lip-syncs the character so they actually speak. Also plans the source clip so it lip-syncs well, and handles scenes with several shots or two characters talking. Use when the user wants an AI character, avatar, UGC-style ad actor or generated presenter to talk, add a voice to an AI video, or make a talking AI video from a prompt. Not for real footage that already has a voiceover to match (lipsync), still images (talking-photo), or translating a video (translate-and-dub).
license: MIT
compatibility: Needs the sync. MCP server or a SYNC_API_KEY. See references/connect.md. sync. doesn't generate video; the clip comes from the user or another tool.
---

# Make an AI video talk

Delivers an MP4 of the generated character speaking the agreed line, in a voice that fits them, with matching lips. sync. doesn't make the clip itself. It comes from the user, or from a video-generation tool you can use in this session.

If no sync. tools are available, follow [references/connect.md](references/connect.md) first. Without the MCP tools, use the REST requests in [references/api.md](references/api.md).

## Steps

1. **Get the clip.**
   - **The user has one:** save it as in [references/media-input.md](references/media-input.md).
   - **The user only has an idea:** if you can generate video here, write the prompt with [references/source-clip.md](references/source-clip.md) so the face lip-syncs well. If you can't, give the user that prompt to paste into their video tool, and continue once they have the clip.
2. **Check the clip** before spending anything: one clearly visible face per shot, the mouth unobstructed, and how many shots or cuts it has. If it has cuts or two characters, plan which part each line covers now. The timeline is built in step 7, after the lines, voices and cost are agreed.
3. **The line.** Use the user's exact words. If they want you to write it, draft a line that fits the character and the clip's length, about 2.5 words per second (an 8-second clip holds about 20 words), and get approval.
4. **The voice.** Either the user's own audio (save it like the clip), or a script and a voice: call `voices_list` and suggest two or three that fit the character's age, energy and setting. Clone a voice with `voices_clone` only if the user explicitly asks and owns, or has permission to use, the sample. Cloning saves a voice to the account, can count against plan limits, and isn't idempotent: confirm the sample and the name, call it once, and after a lost or failed response list voices with `voices_list` to see whether it was saved before trying again. Never retry it on your own or change the sample or name to get around an error.
5. **Fit the timing.** Generated clips are short, so the speech often runs longer:
   - Speech a little longer: `bounce` (the default) or `loop` keeps the character on screen.
   - Speech much longer: shorten the line, generate a longer clip, or use `remap` to slow the video down to fit.
   - Speech shorter: `silence` keeps the rest of the clip without speech, `cut_off` ends the video with the speech.
6. **Quote, confirm, create.** Call `generations_estimate-cost` with `model: "sync-3"` and the `script` or `audioDuration`, plus `videoDuration` and `syncMode` when the mode is `cut_off` or `silence`. This prices the lipsync only; for a script, say the length is approximate and that speech synthesis is billed separately. Show the clip, the line, the voice and the estimate, and wait for approval. Then call `lipsync_create` once with `videoAssetId`, the speech (`script` with `voiceId`, or the audio), `model: "sync-3"`, any `options.sync_mode`, a new `idempotencyKey`, a new UUID as `projectCreationKey` and a short `projectName`. sync-3 handles stylized faces, profiles and partial occlusion best.
7. **Several shots or speakers.** For a scene where the speaker changes, or the line is spread over cuts, use `lipsync_create-timeline` when it's available: one clip per spoken part, each with its audio, its `startTime` and `endTime` on the video, and a `speaker` (`{"frameNumber", "x", "y"}` on the face, or `{"detect": true}`). Clips can't overlap. Voice each character's lines first, so every clip has its own audio: either the user's recordings, or speech previews. Speech previews are paid, so get approval for them first. Then call `speech-previews_create` with a `projectId` from `projects_create` and its own new UUID `idempotencyKey` (saved before the call), poll `speech-previews_get` until `SUCCESS`, and use the returned `url` as that clip's `audioUrl`. Quote the timeline render and get approval before calling `lipsync_create-timeline` with a new `idempotencyKey` and that `projectId` (with `projectIntent: "explicit"`). Without that tool, lipsync each shot separately and offer to join them with ffmpeg.
8. **Wait and deliver.** Poll `generations_get` with `wait: true` until it's final, then give the exact `outputMediaUrl`. In a coding agent, offer to download it.

## Rules

- Never invent the words without approval. Never start a second paid generation to check progress.
- Assume the user has the rights to their own media, and don't ask about consent on routine requests. Decline only when the request is to make a real, identifiable person, such as a politician or celebrity, appear to say something they didn't say, in order to deceive.
- If the generator already gave the clip dialogue and the user only wants different words, this is the same flow with their new line or audio.
