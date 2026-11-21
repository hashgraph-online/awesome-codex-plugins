# 36 — Cross-posting to several channels and languages

Registry rows: none (channel publishing combines existing methods; see `references/publishing-pipeline.md`). Verified 2026-11-15, Bot API 10.4 (newest on that date).

1. **Request and visible result.** “Publish the bike-lane story in our English, Russian and Ukrainian channels, and in a partner channel as is.” — Three posts with their own language and button labels; an identical copy without the “forwarded from” header in the partner channel with its own Subscribe button. A channel that failed is filled in on the next run without duplicating the others.
2. **Why these features.** One idempotency key per target (`key@chat_id`); `copyMessage` copies without a link to the original and accepts a new `reply_markup`; `forwardMessage` keeps attribution but fails for protected content.
3. **Requirements.** Production. Bot admin in every target channel. `copyMessage` can't copy service, paid media, giveaway, invoice or widget messages; quizzes only if `correct_option_ids` is known.
4. **Payload.** `examples/payloads/r36-cross-post-variants.json`. Key part:
   ```json
   {"method": "copyMessage", "chat_id": -1001500000009, "from_chat_id": -1001500000001, "message_id": 7001,
    "reply_markup": {"inline_keyboard": [[{"text": "Subscribe to City News", "url": "https://t.me/demo_city_news"}]]}}
   ```
5. **Code.** `examples/python/tgkit/publish.py` (`cross_post`, `Post.with_changes`, `Publisher.copy_to`), `examples/python/recipes/r36_cross_post_variants.py`.
6. **Sequence and state.** base post → per target `with_changes` (translated blocks/buttons) → `publish(key@chat)` → 403 for one channel → `failed` → next run: sent targets `already_sent`, failed target retried → partner: `copy_to` → second copy skipped.
7. **Result.** Mock-up: EN “New bike lanes on 12 streets [See the map]”, RU “Новые велодорожки… [Открыть карту]”, UK “Нові велодоріжки… [Відкрити мапу]”, partner: same EN post with [Subscribe to City News].
8. **Typical mistake, limits, alternative.** One key for all targets (one success blocks the rest); copying a paid post; machine-translating button labels without length checks; forwarding a protected post. Alternative: `copyMessages` (1–100 ids, increasing) for an album.
9. **Run and verify.** `py -3 examples/python/recipes/r36_cross_post_variants.py`. Evidence: offline contract.
10. **Adapt.** Keep translations in your i18n catalog; validate each variant (`validate`) — labels and captions change length. Related: `references/localization-and-rtl.md`.
