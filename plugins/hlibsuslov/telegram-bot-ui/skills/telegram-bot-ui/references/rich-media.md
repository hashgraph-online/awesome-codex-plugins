# Rich media

Covers media inside Rich Messages (`InputRichMessageMedia` + media blocks) and
the choice between embedding media vs. separate media methods.

> Media in Rich Messages requires Bot API 10.2+ (`InputRichMessageMedia`, `media`
> field, `InputRichBlock` media blocks). Confirm the project's version first.

## Ways to reference media

- **Existing Telegram file** by `file_id` — cheapest, reuse whenever possible.
- **Telegram media reference** `tg://photo?id=`, `tg://video?id=`,
  `tg://audio?id=` — used to bind media referenced from markdown/html to a
  concrete item declared in `InputRichMessage.media`.
- **HTTP(S) URL** — Telegram fetches it; subject to size/type limits.
- **New upload** — attach and upload the file with the request.

Reuse a Telegram `file_id` instead of re-uploading the same asset.

## Binding markdown/html media to `InputRichMessageMedia`

When sending Rich Markdown or Rich HTML that references media (e.g. an image tag
or a `tg://…?id=` link), declare each referenced item in
`InputRichMessage.media` as an `InputRichMessageMedia` so Telegram knows the
source (file_id / URL / upload), caption, and options. Confirm the exact field
names for `InputRichMessageMedia` in the official object before use.

## Media block types (explicit blocks)

`InputRichBlockPhoto`, `InputRichBlockVideo`, `InputRichBlockAnimation`,
`InputRichBlockAudio`, `InputRichBlockVoiceNote`, plus grouped media
`InputRichBlockCollage` and `InputRichBlockSlideshow`, and `InputRichBlockMap`.
Each carries its media reference and optional caption/credit.

## Captions, credits, spoilers

- **Caption** — per-media descriptive text (respect caption limits; may itself be
  formatted).
- **Credit** — attribution text where supported.
- **Spoiler** — mark media as spoiler where supported.
Verify which of these fields your Bot API version exposes for each block/media
type.

## Ordering and structure

- Block order defines render order; place media blocks where they belong in the
  document flow.
- Respect the media-count limit per rich message (see `limits-and-splitting.md`).
- Collage/slideshow group multiple items; use them instead of many single-media
  blocks when the UX is a gallery.

## Bot rights and validity

- Ensure the bot has rights to send the media type in the target chat/topic.
- Validate media (existence, type, size, URL scheme) before sending; handle
  invalid-media errors explicitly (`errors-and-fallbacks.md`).

## Embed vs. separate methods

- Prefer **separate media methods** (`sendPhoto`, `sendVideo`, `sendDocument`,
  `sendMediaGroup`) when the message *is* fundamentally a media post — a single
  image, an album, a document with caption.
- Prefer **embedded rich media** when media is part of a larger structured
  document (article with inline figures, report with a chart).

## No duplication

Do **not** send the same media both inside a Rich Message and as a separate
message unless there is a real product reason. Pick one delivery path per asset.

## Fallback

If rich media isn't supported (older SDK/API) or a media block fails, degrade to
the appropriate separate media method with a formatted caption, then to a text
message with a link — explicitly, not silently. See `errors-and-fallbacks.md`.
