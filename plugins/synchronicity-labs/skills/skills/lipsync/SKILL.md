---
name: lipsync
description: Lip-sync one existing video of a real person to new speech with sync. labs (sync.so), so their mouth matches a new voiceover, re-recorded take, song, or a typed script that sync. voices. Accepts local files, URLs, sync. assets and YouTube, TikTok, Instagram or Facebook links. Use whenever the user wants to lipsync, lip sync or sync lips, match mouth movement to audio, "make him say…", replace the audio in a talking-head clip, or sync a clip to a song, even if they don't say "lipsync". Not for AI-generated characters or clips from Veo, Kling, Sora and similar tools (ai-video-to-talking), still pictures (talking-photo), translation (translate-and-dub), changing a few words in the original voice (edit-dialogue), or many videos at once (batch-lipsync).
license: MIT
compatibility: Needs the sync. MCP server or a SYNC_API_KEY. See references/connect.md.
---

# Lipsync a video

[sync. labs](https://sync.so) | [Lipsync guide](https://sync.so/docs/plugins-and-extensions/agent-skills/lipsync)

Delivers one MP4 of the video with the lips matched to the new speech.

If no sync. tools are available, follow [references/connect.md](references/connect.md) first. Without the MCP tools, use the REST requests in [references/api.md](references/api.md) for the same steps.

## Inputs

- **Video:** a local file, a public URL, a sync. video asset ID, or a social link.
- **Speech:** an audio file, URL or asset, or a script plus a voice.

Ask only for what's missing. Never invent the words.

## Tools

| Step | Tool |
| --- | --- |
| Save files | `assets_upload` (chat apps), or `assets_create-upload-url` then `assets_create` (local files) |
| Import a social link | `projects_create`, `assets_create` |
| Pick a voice (script only) | `voices_list` |
| Quote | `generations_estimate-cost` |
| Shorten long audio | `audio-trims_create`, `audio-trims_get` |
| Create | `lipsync_create` |
| Wait | `generations_get` |

## Steps

1. **Save the inputs.** Follow [references/media-input.md](references/media-input.md). Save each file once, and reuse the returned asset ID for every later step and retry. Check the input-quality list there and mention problems now, such as several faces or music under the voice.
2. **Voice.** For a script, call `voices_list`. Unless the user named a voice, suggest two or three that fit, and use the chosen voice's `id` as `voiceId`.
3. **Length.** When the speech and the video differ noticeably in length, ask how to handle it and pass the answer as `options.sync_mode`:
   - `bounce` (default): play the video forward, then in reverse, to cover longer speech
   - `loop`: repeat the video from the start
   - `cut_off`: stop the speech when the video ends
   - `silence`: keep the video going silently after the speech ends
   - `remap`: speed the video up or slow it down to fit the speech exactly

   If the audio is over the plan's length limit, offer `audio-trims_create` to keep its first part.
4. **Speaker.** If more than one face is visible, ask who should speak. Leave `options.active_speaker_detection` unset unless the user picks someone.
5. **Quote.** Call `generations_estimate-cost` with the model (`sync-3` unless the user chose another) and the speech's `audioDuration`, or the `script`. For `cut_off` or `silence`, also pass `videoDuration` and `syncMode`. This prices the lipsync only. For a script, say the length is approximate and that speech synthesis is billed separately.
6. **Confirm.** Show the video, the speech, the voice, any sync mode and the estimate, and wait for approval. Skip the wait only if the user already approved this exact request and cost.
7. **Create.** Call `lipsync_create` once with the video (`videoAssetId` or `videoUrl`), the speech (`audioAssetId`, `audioUrl`, or `script` with `voiceId`), the model, any `options`, a new `idempotencyKey`, and either the `projectId` of a project you created in step 1 (with `projectIntent: "explicit"`) or a new random UUID as `projectCreationKey` plus a short `projectName`. Save the keys before calling. If the response is lost or times out, the job may still have started: retry once with the same keys and inputs, which returns the original generation if it exists.
8. **Wait and deliver.** Call `generations_get` with the returned `id` and `wait: true`, repeating until the status is `COMPLETED`, `FAILED` or `REJECTED`. Most jobs take a few minutes. Give the exact `outputMediaUrl` unchanged. In a coding agent with a shell, offer to download it next to the source, for example `curl -L -o clip_lipsync.mp4 "<url>"`.

## Rules

- Use `sync-3` unless the user picks another model, and take model names only from `models_list`.
- Never start a second paid generation to check progress or to refresh a link.
- Start a new project for new work. Reuse an existing project only when the user asks for it.
- On a plan, credit or length error, quote the message and stop. On a rejected input, explain which input and why.
- Assume the user has the rights to their own media, and don't ask about consent on routine requests. Decline only when the request is to make a real, identifiable person, such as a politician or celebrity, appear to say something they didn't say, in order to deceive.
