<!-- Generated from shared/media-input.md by scripts/sync_shared.py. Edit the shared file, not this copy. -->

# Getting media into sync.

Every generation needs its visual input (video or image) and its speech (audio, or a script plus a voice) as one of these: a public URL, a sync. asset ID, or a file saved into sync. storage first. Save each file once and reuse the returned asset ID for every later step and every retry. A file uploaded again becomes a different asset, and the retry stops matching the original request.

## Pick the route for each input

| What the user has | Route |
| --- | --- |
| A public `https://` media URL | For `lipsync_create`, pass it as `videoUrl`, `imageUrl` or `audioUrl`. Translation, Edit Dialogue and timeline lipsync need a saved asset: register the URL with `assets_create` and use the returned `id`. Signed URLs that expire soon are risky; save them as an asset too. |
| A sync. asset ID | Pass it as `videoAssetId`, `imageAssetId` or `audioAssetId`. |
| A file attached in a chat app (ChatGPT, Codex) | If the `assets_upload` tool is available, call it once per file with `mediaType` `video`, `image` or `audio`, and use the returned asset ID. |
| A file on disk | Upload it, as described below. |
| A YouTube, TikTok, Instagram or Facebook link | Import it, as described below. |

## Upload a local file

1. Read the file's size in bytes and its MIME type, such as `video/mp4`, `video/quicktime`, `audio/mpeg`, `audio/wav` or `image/png`.
2. Call `assets_create-upload-url` with `fileName`, `contentType` and `size`. It returns `uploadUrl` and `url`.
3. Upload the bytes with exactly the same content type:

   ```bash
   curl -sS --fail -X PUT -H "Content-Type: video/mp4" --data-binary @"./clip.mp4" "<uploadUrl>"
   ```

4. Call `assets_create` with the returned `url`, `type` (`VIDEO`, `AUDIO` or `IMAGE`), `wait: true`, and the `projectId` with `projectIntent: "explicit"` when the workflow already has a project. Use the returned `id` as the asset ID.

Without MCP tools, the same three steps are `POST /v2/assets/upload`, the `PUT`, then `POST /v2/assets` (see `references/api.md`). Files can be up to 5 GB, but plans cap file size lower. Upload URLs expire, so upload right after creating one.

## Import a social link

1. Create a project first: `projects_create` with a new random UUID as `id`, a short `name` and the workflow's `defaultWorkflow`. Keep that UUID for retries.
2. Call `assets_create` with the link, `type: "VIDEO"`, the `projectId` and `projectIntent: "explicit"`.
3. A 409 `import_in_progress` means the import is still running. Wait `retryAfterMs` (15 seconds if it's missing) and repeat the identical call until it returns an asset. Never pass an `importJobId` as an asset ID.
4. On `import_failed`, `import_not_enabled`, `import_unavailable`, `import_daily_limit_reached` or a size limit, explain the reason, offer a file upload instead, and stop.

## Input quality

Lipsync quality depends mostly on the source. Mention a problem before the user spends money, not after.

- **Face:** clearly visible, front-facing or close to it, well lit, with the mouth unobstructed. sync-3 handles profiles and partial occlusion best. Human faces only; animals aren't supported.
- **One speaker per track.** If several faces are visible, ask who should speak.
- **Resolution:** at least 480p, 1080p recommended, at most 4096×2160. Use a constant frame rate (24, 25 or 30 fps).
- **Audio:** clean speech. Music, noise and a second voice all hurt the result; for a song, isolate the vocal first.
- **Length:** keep audio and video close in length, or choose a sync mode (see the lipsync skill). Very long or heavily cut videos are slower and more likely to fail; split them at scene cuts.
- **Formats:** video mp4, mov, webm or avi; audio wav, mp3, ogg, flac or m4a; images jpg, png or webp.
