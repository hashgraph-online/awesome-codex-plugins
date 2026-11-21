# 39 — Correcting a published post: edit or delete-and-repost

Registry rows: none (channel publishing combines existing methods; see `references/publishing-pipeline.md`). Verified 2026-11-15, Bot API 10.4 (newest on that date).

1. **Request and visible result.** “We posted the wrong time. Fix it — and next time we also need to add a map photo to a post.” — A typo is fixed in place (views, reactions and comments stay); a repeated fix sends nothing; a young post that must become a photo post is deleted and reposted; an older one gets a visible correction note as a reply.
2. **Why these features.** `editMessageText` / `editMessageCaption` / `editMessageMedia` keep the post; `deleteMessage(s)` works only for 48 hours; paid posts can't be edited and must stay 24 h; approved/declined suggested posts can't be edited.
3. **Requirements.** Production. Channel; `can_post_messages` (delete own posts) / `can_edit_messages`.
4. **Payload.** `examples/payloads/r39-correct-published-post.json`. Key part:
   ```json
   {"method": "editMessageText", "chat_id": -1001500000001, "message_id": 1001, "text": "Water outage on Monday\n\n… From 09:00 to 13:00."}
   {"method": "sendMessage", "chat_id": -1001500000001, "text": "Correction: the closure is on Wednesday, not Tuesday.", "reply_parameters": {"message_id": 1003}}
   ```
5. **Code.** `examples/python/tgkit/publish.py` (`decide_correction`, `Publisher.edit`, `Publisher.delete`), `examples/python/recipes/r39_correct_published_post.py` (`Corrector`).
6. **Sequence and state.** new version → fingerprint equal → `unchanged`; same layout → `edit` (only changed parts); layout change and age < 15 min → `delete` + `publish(key#r1)`; else `append_note` (reply). Ledger: old record `deleted`, new record `sent`.
7. **Result.** Mock-up: the post shows “edited” with the right time; or a reply “Correction: …” under the old post.
8. **Typical mistake, limits, alternative.** Delete-and-repost for a typo (loses engagement, notifies again); editing a poll (only `stopPoll`); deleting after 48 h (fails); editing a paid post. Alternative: `editMessageMedia` when only the media changes.
9. **Run and verify.** `py -3 examples/python/recipes/r39_correct_published_post.py` · `tests/test_publishing.py` (`Editing`). Evidence: offline contract.
10. **Adapt.** Tune `repost_window_s` to your editorial policy; always state what changed in the correction note. Related: `references/publishing-pipeline.md`.
