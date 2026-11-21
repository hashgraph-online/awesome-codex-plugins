# 32 — Media album post (and paid media)

Registry rows: none (channel publishing combines existing methods; see `references/publishing-pipeline.md`). Verified 2026-11-15, Bot API 10.4 (newest on that date).

1. **Request and visible result.** “Post three photos of the winter market with a caption and a ‘Map’ button; and a paid backstage set for supporters.” — An album with the caption above the photos, one photo behind a spoiler, then a silent short message carrying the button. A paid post with 2 photos + a video for 50 Stars.
2. **Why these features.** `sendMediaGroup` has no `reply_markup` — buttons need their own message; `show_caption_above_media` and `has_spoiler` per item; `sendPaidMedia` credits Stars to the channel balance; live photos are allowed in albums since 10.0.
3. **Requirements.** Production. Channel; `can_post_messages`. Albums 2–10 items, documents/audio only with their own type; captions ≤ 1024 chars. Paid media: `star_count` 1–25000, ≤ 10 items, `payload` ≤ 128 bytes, `ChatFullInfo.can_send_paid_media`; paid media can't be copied.
4. **Payload.** `examples/payloads/r32-media-album-post.json`. Key part:
   ```json
   {"method": "sendMediaGroup", "media": [{"type": "photo", "media": "AgAC…1", "caption": "Winter market opens on Saturday\n\n…", "caption_entities": [{"type": "bold", "offset": 0, "length": 31}], "show_caption_above_media": true}, {"type": "photo", "media": "AgAC…2"}, {"type": "photo", "media": "AgAC…3", "has_spoiler": true}]}
   {"method": "sendMessage", "text": "Plan your visit:", "disable_notification": true, "reply_markup": {"inline_keyboard": [[{"text": "Map and opening hours", "url": "https://example.com/market"}]]}}
   ```
5. **Code.** `examples/python/tgkit/publish.py` (`plan` album / paid branches, `_caption_split`, `check_media_ref`, `Publisher.copy_to` refusal), `examples/python/recipes/r32_media_album_post.py`.
6. **Sequence and state.** post → `validate` (2–10, type mix, refs: file_id / URL / `attach://`, never local paths) → `sendMediaGroup` → ids of every item → follow-up `sendMessage` with buttons (silent) → all ids in the ledger. Caption > 1024 → whole blocks that fit stay in the caption, the rest + buttons go to the follow-up (no extra preview).
7. **Result.** Mock-up: caption above [photo][photo][spoiler photo] · then “Plan your visit: [Map and opening hours]”.
8. **Typical mistake, limits, alternative.** Captions on several items (shown per photo, confusing); `reply_markup` on the album (the method has none); mixing documents with photos; uploading from a local path in JSON mode; trying to `copyMessage` a paid post. Alternative: a single photo with buttons, or a rich message with a collage block.
9. **Run and verify.** `py -3 examples/python/recipes/r32_media_album_post.py` · `tests/test_publishing.py` (`PayloadShapes.test_album`, `Splitting.test_caption_overflow_moves_buttons_to_the_follow_up`). Evidence: offline contract.
10. **Adapt.** Upload once, reuse `file_id`s; put the headline in the first caption line; keep the follow-up text short and in the channel's language. Related: `references/rich-media.md`, `references/channel-post-design.md`.
