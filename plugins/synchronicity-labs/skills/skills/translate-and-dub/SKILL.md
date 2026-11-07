---
name: translate-and-dub
description: Translate one source video's speech into another language with sync. labs (sync.so) and re-sync the speaker's lips to the dubbed audio, from a local file, URL, or YouTube, TikTok, Instagram or Facebook link, into one or several languages. Use for "dub this video into Spanish", "translate my YouTube video to Japanese", AI dubbing, video translation, or a multilingual version of one video. Not for subtitles or captions only, translating a text document, lip-syncing audio the user already has (lipsync), or a whole campaign of several videos across markets (localize-campaign).
license: MIT
compatibility: Needs the sync. MCP server or a SYNC_API_KEY. See references/connect.md.
---

# Translate and dub a video

Delivers one dubbed MP4 per target language, with lips matched to the new audio. The dubbed voice follows the original speaker's.

If no sync. tools are available, follow [references/connect.md](references/connect.md) first. Without the MCP tools, use `dubParams` on `POST /v2/generate` as shown in [references/api.md](references/api.md).

## Inputs

- **Video:** a local file, a public URL, a sync. video asset ID, or a social link. It needs its original speech on the audio track.
- **Target languages:** ask if none were given. Use `sourceLang: "auto"` unless the user names the spoken language.

## Tools

| Step | Tool |
| --- | --- |
| Check languages | `dubbing_get-options` |
| Create the project | `projects_create` |
| Save the video | `assets_upload`, `assets_create-upload-url` + `assets_create`, or `assets_create` with a link |
| Quote | `generations_estimate-cost` |
| Create | `dubbing_create`, or `jobs_create-many` for 2 or more languages |
| Wait | `generations_get`, or `jobs_get-many` for a set |

## Steps

1. **Languages.** Call `dubbing_get-options` and check every requested language. For any that isn't supported, name the closest supported option.
2. **Project.** Call `projects_create` with a new random UUID as `id`, a short `name` and `defaultWorkflow: "translate_and_dub"`. Save the returned `id` as `projectId`. Pass it wherever a tool asks for `projectId`, and add `projectIntent: "explicit"` only on tools that take that field.
3. **Save the video** into that project. Follow [references/media-input.md](references/media-input.md).
4. **Quote.** Call `generations_estimate-cost` with `workflow: "translate-and-dub"`, `model: "sync-3"` and the video's length as `duration` in seconds. Show the returned estimate and its breakdown per language and in total. If it reports external provider charges as excluded, say they're extra.
5. **Confirm.** Show the video, the languages and the estimate, and wait for approval. Skip the wait only if the user already approved this exact request and cost.
6. **Create.** Each language is one `dubbing_create` with `videoAssetId`, `targetLang`, `sourceLang`, `model: "sync-3"`, the `projectId` with `projectIntent: "explicit"`, and its own new `idempotencyKey`, saved before the call.
   - **One language:** call `dubbing_create` once. If a response is lost, retry once with the same key and inputs.
   - **2 or more languages, with `jobs_create-many` listed:** save a new UUID for the set, then call `jobs_create-many` once with `tool: "dubbing_create"`, that UUID as `idempotencyKey`, and one item per language holding exactly those arguments. The one approval covers every language. If the response is unclear, send the identical call again. When it returns `remaining`, send `remaining` again exactly as returned once running languages finish; if the tool refuses a single remaining item, send that language with `dubbing_create` and the same key. A failed item with a 5xx or no status may still have started, so send it again with the same keys.
   - **2 or more languages without it:** call `dubbing_create` once per language, as for one language.
7. **Wait and deliver.** Poll `generations_get` with each `id` and `wait: true` until each is final, or pass the set's `jobs` to `jobs_get-many` with `wait: true` and call it again while some are still running. Dubbing takes longer than plain lipsync, so tell the user it may take several minutes. Give each exact `outputMediaUrl`, unchanged and labelled with its language.

## Rules

- One paid job per language. Never resubmit a language to check progress.
- Several source videos across languages or markets is a campaign: hand it to the localize-campaign skill, which plans the matrix and pilots one version first.
- If one language fails, report it and keep the others.
- Text on screen isn't translated, and the output is dubbed video only. Don't offer subtitles or a translated transcript as a substitute.
- If dubbing fails with a voice-provider error and the user connected their own ElevenLabs key to sync., the cause is usually that key's credits or validity. Say so.
