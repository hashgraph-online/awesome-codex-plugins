# 30 — News autoposter from a feed item

Registry rows: none (channel publishing combines existing methods; see `references/publishing-pipeline.md`). Verified 2026-11-15, Bot API 10.4 (newest on that date).

1. **Request and visible result.** “Post every new item from our city news feed to the channel — and never twice.” — Each item becomes one post: bold headline as line 1 (it is what the notification and pinned bar show), a short summary, a source link, one button “Read the full story”, a large preview of the article. A timeout on send never produces a duplicate.
2. **Why these features.** `link_preview_options` (`url`, `prefer_large_media`) picks the card instead of whatever link comes first; entities instead of `parse_mode` make hostile titles (`<`, `&`, `_`) harmless; the idempotent publisher turns a lost response into `unknown`, not a re-post.
3. **Requirements.** Any Bot API with `link_preview_options` (7.0+). Production. Channel; bot admin with `can_post_messages`. Scheduling (poll the feed every N minutes) is the caller's job: the Bot API has no scheduled send.
4. **Payload.** `examples/payloads/r30-news-autoposter.json`. Key part:
   ```json
   {"chat_id": -1001500000001, "text": "Tram line 4 <reopens> & runs until 01:00\n\n…",
    "entities": [{"type": "bold", "offset": 0, "length": 40}, {"type": "text_link", "offset": 135, "length": 21, "url": "https://example.com/news/4821?…"}],
    "link_preview_options": {"url": "https://example.com/news/4821?…", "prefer_large_media": true},
    "reply_markup": {"inline_keyboard": [[{"text": "Read the full story", "url": "https://example.com/news/4821?…"}]]}}
   ```
5. **Code.** `examples/python/tgkit/publish.py` (`Post`, `to_entities`, `plan`, `Publisher.publish`, `Publisher.reconcile`), `examples/python/recipes/r30_news_autoposter.py`, TS `examples/ts/publishing/publish.ts`.
6. **Sequence and state.** feed item → key `feed:<sha(guid)>` → `post_from_item` → `validate` → ledger `pending` → `sendMessage` → timeout → ledger `unknown` → next poll returns `unknown` without a request → operator confirms post 5001 → `reconcile` → `sent` → next poll `already_sent`.
7. **Result.** Mock-up: **Tram line 4 <reopens> & runs until 01:00** / Repairs on Bridge Street… / Source: City Transport Office / [large article card] / [Read the full story].
8. **Typical mistake, limits, alternative.** Retrying a timed-out `sendMessage` (duplicate post); keying by publish time instead of `guid`; HTML-escaping by hand and missing `&`; leaving the preview to chance (random image from a footer link). Text ≤ 4096 chars; a longer item becomes a rich long read (R31). Alternative: `copyMessage` from a staging channel when an editor prepares posts by hand.
9. **Run and verify.** `py -3 examples/python/recipes/r30_news_autoposter.py` · `tests/test_publishing.py` (`Idempotency`, `Escaping`). Evidence: offline contract.
10. **Adapt.** Map your feed fields in `post_from_item`; keep the key stable per item; store the ledger in your DB; send the same plan to an editor chat first if a human must see it (R35). Related: `references/publishing-pipeline.md`, `references/channel-post-design.md`.
