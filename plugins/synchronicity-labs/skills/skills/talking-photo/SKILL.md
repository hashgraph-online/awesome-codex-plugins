---
name: talking-photo
description: Make a still image talk with sync. labs (sync.so). Turns a photo, portrait, headshot, or an illustrated or AI-generated character with a human-like face into a lip-synced video from a typed script (sync. voices it) or the user's own audio. Use for "make this photo talk", "make this picture say…", talking avatars, talking headshots, animating a portrait or character with speech, or image-to-video with dialogue, including when the user has no picture yet and wants one made first. Not for moving video footage (lipsync or ai-video-to-talking), translation (translate-and-dub) or changing words in an existing video (edit-dialogue).
license: MIT
compatibility: Needs the sync. MCP server or a SYNC_API_KEY. See references/connect.md.
---

# Make a photo talk

Delivers one MP4 of the picture speaking the user's words. The video is as long as the speech.

If no sync. tools are available, follow [references/connect.md](references/connect.md) first. Without the MCP tools, use the REST requests in [references/api.md](references/api.md) for the same steps.

## Inputs

- **Picture:** a local image, an image attached in chat, a public URL, or a sync. image asset ID. If the user has no picture and you can generate images, offer to make one: one clear face, looking at the camera, mouth closed, head and shoulders, plain background. Otherwise ask for one.
- **Speech:** a script, which needs a voice, or an audio file, URL or asset.

Ask only for what's missing. Never invent the words. If the user asks you to write them, draft a short script and get approval before quoting.

## Tools

| Step | Tool |
| --- | --- |
| Save files | `assets_upload` (chat apps), or `assets_create-upload-url` then `assets_create` (local files) |
| Pick a voice (script only) | `voices_list` |
| Quote | `generations_estimate-cost` |
| Create | `lipsync_create` |
| Wait | `generations_get` |

## Steps

1. **Save the inputs.** Follow [references/media-input.md](references/media-input.md) for the picture and any audio. Public URLs and asset IDs need no upload. Before spending money, check that the image shows exactly one clear, reasonably large human or human-like face. Animals and non-humanoid characters aren't supported.
2. **Voice.** For a script, call `voices_list`. Unless the user named a voice, suggest two or three that fit the character, each with a few words on its style. Use the chosen voice's `id` as `voiceId`; never invent one.
3. **Quote.** Call `generations_estimate-cost` with `model: "sync-3"`, `visualType: "image"`, and either the `script` or the audio's `audioDuration`. This prices the lipsync only. For a script, say the length is approximate and that speech synthesis is billed separately.
4. **Confirm.** Show the picture, the script or audio, the voice and the estimate, and wait for approval. Skip the wait only if the user already approved this exact request and cost.
5. **Create.** Call `lipsync_create` once with the picture (`imageAssetId` or `imageUrl`), the speech (`script` with `voiceId`, or `audioAssetId` or `audioUrl`), `model: "sync-3"`, a new `idempotencyKey`, a new random UUID as `projectCreationKey`, and a short `projectName` such as "Talking portrait". Images work only with sync-3, and `sync_mode` doesn't apply to them. Save the keys before calling. If the response is lost or times out, retry once with the same keys and inputs, which returns the original generation if it exists.
6. **Wait and deliver.** Call `generations_get` with the returned `id` and `wait: true`, repeating until the status is final. Give the exact `outputMediaUrl` unchanged, and offer one next step: another line, another voice, or dubbing it into another language.

## When something fails

- **The picture is rejected** (no clear face, several faces, too small): explain why and suggest a clearer head-and-shoulders picture.
- **Out of credits or over a plan limit:** quote the message plainly, without promoting plans.
- **Any other rejection:** quote the message, say no video was created, and stop. Don't retry with different inputs unless the user asks.
- **A timeout or unclear outcome:** the job may still have started. Say so, keep the keys, and retry once with the identical request instead of reporting a failure.

## Rules

- Assume the user has the rights to their own media, and don't ask about consent on routine requests. Decline only when the request is to make a real, identifiable person, such as a politician or celebrity, appear to say something they didn't say, in order to deceive.
- Never start a second paid generation to check progress.
