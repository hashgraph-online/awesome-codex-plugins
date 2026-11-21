# 72 — Channel post series with premium accents and fallback

Registry rows: none of its own — custom emoji entities (6.2), RichTextCustomEmoji (10.3
rich messages). Verified 2026-11-15, Bot API 10.4. Background: `references/emoji-in-posts.md`.

1. **Request and visible result.** “Our channel posts should look as polished as the bot.”
   — Three posts with one accent before the headline, one per section, bullets in the first
   list only and one before the call to action; a rich-message variant with icons in
   headings; the same posts with Unicode accents when the bot is not eligible.
2. **Why the new features.** Custom emoji give a channel one recognisable mark set; rich
   messages accept `RichTextCustomEmoji` nodes with `alternative_text`.
3. **Requirements.** API: the owner-Premium route covers only private, group and supergroup
   chats, so **a channel needs Fragment usernames**. Fallback: Unicode accents (same text).
4. **Payload.** `examples/payloads/r72-channel-post-series.json`. Key part:
   ```json
   {"type": "heading", "size": 1, "text": [{"type": "custom_emoji", "custom_emoji_id": "<id>", "alternative_text": "📣"}, " Version 2.4 is out"]}
   ```
5. **Code.** `examples/python/recipes/r72_channel_post_series.py` (`POSTS`, `rich_post`),
   `tgkit/icons.py` (`decorate_post`, `IconSystem.rich_label`, `density_warnings`).
6. **Sequence and state.** post model → `view = icons.for_context(SendContext.channel())` →
   `decorate_post(post, view)` → `icons.send(..., decorate=False)`; one decision per post.
7. **Result.** Mock-up: `[icon] Version 2.4 is out / Faster sync… / [icon] New / [icon]
   Offline drafts / … / [icon] Read the changelog`.
8. **Typical mistake, limits, alternative.** An emoji on every line; custom emoji inside the
   link text; assuming owner Premium covers channels. Limits: heuristic budget of 8 accents
   per post, 1 per line. Alternative: words-only headings.
9. **Run and verify.** `py -3 examples/python/recipes/r72_channel_post_series.py` ·
   `py -3 scripts/audit_icons.py --payload examples/payloads/r72-channel-post-series.json --post`
   · tests in `tests/test_emoji_posts.py`. Evidence: offline contract; synthetic ids.
10. **Adapt.** Call `icons.for_context(SendContext.channel()).prepare(method, params)` right
    before your publishing code sends (see `references/emoji-in-posts.md#integration-with-the-publishing-helper`).
    Related: 73.
