# 37 — Broadcast mailing with throttling and per-recipient outcomes

Registry rows: none (channel publishing combines existing methods; see `references/publishing-pipeline.md`). Verified 2026-11-15, Bot API 10.4 (newest on that date).

1. **Request and visible result.** “Send the event alert to all 40,000 subscribers of the bot without getting banned, and don't message people twice if the job restarts.” — Each subscriber gets one personalized message; blocked users are recorded and skipped; a flood wait pauses and resumes; a restart skips delivered messages.
2. **Why these features.** Bots FAQ: ~30 messages/s for bulk notifications, 1/s per chat; `429` carries `retry_after`; `allow_paid_broadcast` raises the limit to 1000/s for 0.1 Star per message.
3. **Requirements.** Any Bot API. Production. Private chats of users who started the bot. Throttle below the ceiling (`per_second=25`).
4. **Payload.** `examples/payloads/r37-broadcast-mailing.json`. Key part:
   ```json
   {"chat_id": 202, "text": "Hi, <b>Bo_b*</b>! The winter market opens on Saturday.\n\n…", "entities": [{"type": "bold", "offset": 4, "length": 12}],
    "reply_markup": {"inline_keyboard": [[{"text": "Unsubscribe", "callback_data": "alerts:off"}]]}}
   ```
5. **Code.** `examples/python/tgkit/publish.py` (`FanOut`, `FanOutReport`, `Ledger`), `examples/python/tgkit/errors.py` (`call_with_policy`, `RetryPolicy`), `examples/python/recipes/r37_broadcast_mailing.py`.
6. **Sequence and state.** per recipient: key `campaign:id` → `pending` → throttle → send → `sent` / 403 `blocked` (never retried) / 400 `invalid` (retried after a fix) / timeout `unknown` (not resent) / 429 → sleep `retry_after` → retry; a wait above `max_wait` → `deferred` for the rest.
7. **Result.** Report `{"sent": 3, "blocked": 1, "invalid": 1, "unknown": 1, "deferred": 0, "skipped": 0}`; the re-run skips the 3 delivered.
8. **Typical mistake, limits, alternative.** Parallel sends without a limiter; retrying immediately after 429; aborting the whole run on one 403; HTML templates with raw names; logging tokens or full texts. Alternative: post to a channel once instead of mailing everyone; paid broadcasts for urgent alerts.
9. **Run and verify.** `py -3 examples/python/recipes/r37_broadcast_mailing.py` · `tests/test_publishing.py` (`RateLimits`). Evidence: offline contract.
10. **Adapt.** Keep the ledger in your DB with a unique (campaign, recipient) key; spread big campaigns over hours; add an unsubscribe action. Related: `references/errors-and-fallbacks.md`.
