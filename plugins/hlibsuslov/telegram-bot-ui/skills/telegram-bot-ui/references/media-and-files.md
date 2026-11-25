---
summary: "Sending files (upload, file_id, URL), size limits, albums, InputMedia, thumbnails, live photos, getFile downloads, local Bot API server; read when a bot sends or receives media."
verified: "2026-11-15"
bot_api: "10.4"
---

# Media and files

Sending files (upload vs `file_id` vs URL), size limits, albums, `InputMedia*`,
thumbnails and covers, live photos, downloading with `getFile`, and what changes
with a local Bot API server. Paid media: `payments-and-stars.md#paid-media`;
media inside rich messages: `rich-media.md`. Checked against Bot API 10.4 on
**2026-11-15**: https://core.telegram.org/bots/api#sending-files,
https://core.telegram.org/bots/api#inputmedia,
https://core.telegram.org/bots/api#using-a-local-bot-api-server.
Every JSON block passes `scripts/validate_payload.py`.

Labels: **[API]** spec; **[Heuristic]** this skill's advice.

## Three ways to send a file

| Way | How | Limits (cloud Bot API) |
|---|---|---|
| `file_id` | pass the id string from an earlier `Message` / `File` | no size limit; **[API]** |
| HTTP URL | pass the URL; Telegram downloads it | photos 5 MB, other types 20 MB; correct MIME type required; `sendDocument` by URL only for `.PDF` and `.ZIP`; **[API]** |
| Upload | `multipart/form-data` part | photos 10 MB, other files 50 MB; **[API]** |

- **[API]** A `file_id` is unique **per bot** (not transferable between bots), cannot change
  the file type when re-sent (a video can't become a photo), and the same file may
  have several valid `file_id`s. `file_unique_id` is stable across bots but cannot be
  used to send or download. Re-sending a photo by `file_id` sends all its sizes.
- **[API]** Thumbnails can't be re-sent by `file_id`; they are always new uploads.
- **[API]** `sendVoice` needs `audio/ogg` (OPUS) ≤ 1 MB to show as a voice note; 1-20 MB voice
  files are sent as files.
- **[Heuristic]** Upload once, store `file_id` (+ `file_unique_id` for dedupe), re-send by id
  forever. URL sending makes Telegram's servers fetch your URL — it must be public,
  fast and return the right `Content-Type`.

## Uploading

- **[API]** Uploads use `multipart/form-data`. Pass the file in its own part and reference it
  as `attach://<part_name>` inside JSON-serialized fields (`media` arrays,
  `InputMedia*.media`, `thumbnail`, `cover`). JSON request bodies cannot carry files.
- **[API]** `thumbnail`: JPEG, < 200 kB, width/height ≤ 320; ignored unless the main file is
  uploaded via multipart; must be a new upload (`attach://`).
- **[API]** `cover` (videos): `file_id`, URL or `attach://`; `start_timestamp` sets where
  playback starts.

```json
{"method": "sendMediaGroup", "params": {
  "chat_id": 111111111,
  "media": [
    {"type": "photo", "media": "attach://img1", "caption": "Сніданок · Breakfast menu", "show_caption_above_media": false},
    {"type": "photo", "media": "AgACAgIAAxkBAAIC"},
    {"type": "video", "media": "attach://clip", "thumbnail": "attach://clip_thumb", "supports_streaming": true}
  ]
}}
```

(multipart parts named `img1`, `clip`, `clip_thumb` carry the bytes.)

## Albums (`sendMediaGroup`)

- **[API]** 2-10 items. Photos, live photos and videos can mix; **documents only with
  documents, audio only with audio**. Returns an **array** of `Message`s; every message
  shares one `media_group_id`.
- **[API]** No `reply_markup` on `sendMediaGroup`: an album can't carry a keyboard. Send the
  keyboard in a separate message after the album. **[Heuristic]** for the workaround.
- **[Heuristic]** The album caption is the caption of the **first** item; clients show it
  under the album. Putting captions on several items shows each under its own media
  when opened, which reads as clutter.
- **[API]** Incoming albums arrive as **separate** updates with the same
  `media_group_id` and no "last item" marker. **[Heuristic]** Buffer by
  `media_group_id` for ~1 s after the last item before processing as one unit.
- Editing: `editMessageMedia` changes one item at a time; inside an album it can only
  stay audio for audio albums, document for document albums, and photo / live photo /
  video otherwise. **[API]**

## `InputMedia*` (for albums and `editMessageMedia`)

**[API]** `InputMedia` is one of `InputMediaAnimation`, `InputMediaAudio`,
`InputMediaDocument`, `InputMediaLivePhoto` (10.0), `InputMediaPhoto`,
`InputMediaVideo`; `type` selects it. Since 10.0/10.1 there are also
`InputMediaSticker`, `InputMediaLocation`, `InputMediaVenue`, `InputMediaLink`
(poll media) and `InputMediaVoiceNote` (10.2, rich messages) — they belong to other
unions (`InputPollMedia`, `InputPollOptionMedia`, rich media) and are **not** valid
in `sendMediaGroup`. `py -3 scripts/tg_api_lookup.py show InputMedia`.

```json
{"method": "editMessageMedia", "params": {
  "chat_id": 111111111, "message_id": 4021,
  "media": {"type": "photo", "media": "AgACAgIAAxkBAAID", "caption": "Updated price: 8.90 €", "has_spoiler": false}
}}
```

- **[API]** `editMessageMedia` can also turn a text or rich message into a media message.
  For inline messages a new upload is impossible (use `file_id`/URL) and the result is
  `True`.

## Live photos (10.0)

- **[API]** `sendLivePhoto(chat_id, live_photo, photo, …)`: the video ≤ 10 s and ≤ 10 MB;
  both parts by `file_id` or upload — **sending by URL is unsupported**.
  `InputMediaLivePhoto` works in albums and `editMessageMedia`;
  `InputPaidMediaLivePhoto` in paid media. Incoming: `Message.live_photo`
  (`LivePhoto`).

## Downloading (`getFile`)

```json
{"method": "getFile", "params": {"file_id": "BQACAgIAAxkBAAIE"}}
```

- **[API]** Cloud Bot API downloads are limited to **20 MB**. The response `File` has
  `file_path`; download from `https://api.telegram.org/file/bot<token>/<file_path>`. The
  link is valid **at least 1 hour**; call `getFile` again when it expires.
- **[API]** `getFile` may not preserve the original name and MIME type — save them from the
  incoming `Document`/`Audio`/`Video` object.
- **[API]** `file_size` can exceed 2³¹ (≤ 52 significant bits): use 64-bit integers.
- **[Heuristic]** The download URL contains the token: never log it, never hand it to a
  user or a front-end; proxy the bytes instead.

## Local Bot API server

Run https://github.com/tdlib/telegram-bot-api yourself and point the bot at it. **[API]**:

- downloads without a size limit; uploads up to **2000 MB**;
- upload by **local path** and `file://` URI;
- `getFile` returns an **absolute local path** in `file_path` (no download step);
- webhooks: HTTP URLs, any local IP, any port, `max_connections` up to 100000.

Switching: call `logOut` on the cloud server first (then you can't log back into the
cloud server for 10 minutes); `close` before moving between local servers. **[API]**
Keep the same code path for both by reading the API base URL from configuration.
**[Heuristic]**

## What the user sees

- `show_caption_above_media` puts the caption above; `has_spoiler` blurs until tapped;
  `supports_streaming` lets video play while downloading. **[API]**
- `sendChatAction` (`upload_photo`, `upload_video`, `upload_document`, …) shows a status
  for ≤ 5 s or until the next message — repeat it during long uploads
  (`dynamic-feedback-and-streaming.md`). **[API]** for the 5 s.

## Common mistakes

| Mistake | Fix |
|---|---|
| Uploading the same file every time | cache `file_id` |
| Sending a `file_id` from another bot | ids are per bot; upload again |
| JSON body with a file | multipart + `attach://` |
| `reply_markup` on an album | separate message with the keyboard |
| Mixing documents and photos in one album | documents only with documents |
| Processing album items as separate requests | buffer by `media_group_id` |
| Logging `file/bot<token>/...` URLs | log `file_id` only |
| `sendDocument` by URL for a `.docx` | upload it (URL works only for PDF/ZIP) |

## Error handling

- `wrong file identifier/HTTP URL specified`, `failed to get HTTP URL content`, `wrong
  type of the web page content`: the URL is private, slow, too big or mislabeled —
  fall back to upload. **[Heuristic]** (texts observed in practice; branch on
  `error_code` 400, not the text)
- `file is too big` from `getFile` on the cloud server: tell the user the 20 MB limit or
  move to a local server. **[Heuristic]**
