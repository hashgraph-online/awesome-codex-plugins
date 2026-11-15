# 34 — Daily digest edited in place and pinned

Registry rows: none (channel publishing combines existing methods; see `references/publishing-pipeline.md`). Verified 2026-11-15, Bot API 10.4 (newest on that date).

1. **Request and visible result.** “Keep one pinned ‘Today in the city’ post and update it during the day instead of posting ten times.” — One rich digest per day with a compact table, pinned; new items edit it in place; a run without changes sends nothing; the next day a new digest is pinned and yesterday's unpinned.
2. **Why these features.** `editMessageText(rich_message)` (10.1) edits rich posts; `is_compact` tables (10.3); pinning in channels needs `can_edit_messages` and never notifies; a fingerprint makes repeated runs free.
3. **Requirements.** Bot API ≥ 10.3. Production. Channel; `can_post_messages` + `can_edit_messages`. Scheduling of the runs is the caller's job.
4. **Payload.** `examples/payloads/r34-pinned-daily-digest.json`. Key part:
   ```json
   {"method": "editMessageText", "chat_id": -1001500000001, "message_id": 1001, "rich_message": {"blocks": [{"type": "heading", "size": 1, "text": "Today in the city — 15 Nov"}, {"type": "table", "is_compact": true}]}}
   {"method": "pinChatMessage", "chat_id": -1001500000001, "message_id": 1002}
   {"method": "unpinChatMessage", "chat_id": -1001500000001, "message_id": 1001}
   ```
5. **Code.** `examples/python/tgkit/publish.py` (`Publisher.edit` fingerprint, `pin`, `unpin`), `examples/python/recipes/r34_pinned_daily_digest.py` (`DigestDesk`).
6. **Sequence and state.** run(day, items) → key `digest:<day>` → no record: publish + pin + unpin previous → record: `edit` → fingerprint equal → `unchanged` (no request) / different → `editMessageText`.
7. **Result.** Mock-up: pinned bar “Today in the city — 15 Nov”; the post's table grows during the day.
8. **Typical mistake, limits, alternative.** Editing on every run (“message is not modified” errors, flood limits); `disable_notification` on channel pins (pointless); forgetting to unpin yesterday. The pinned bar shows only the start of line 1 — keep it short. Alternative: a regular text digest when there is no table.
9. **Run and verify.** `py -3 examples/python/recipes/r34_pinned_daily_digest.py` · `tests/test_publishing.py` (`Editing.test_unchanged_edit_sends_nothing`). Evidence: offline contract.
10. **Adapt.** Key per period (day, week); throttle edits (≤ 1 per few seconds per message); index posts for series use the same pattern with links `https://t.me/<channel>/<id>`. Related: `references/streaming-and-editing.md`.
