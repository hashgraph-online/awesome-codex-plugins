# 33 — Poll and quiz posts in a channel

Registry rows: none (channel publishing combines existing methods; see `references/publishing-pipeline.md`). Verified 2026-11-15, Bot API 10.4 (newest on that date).

1. **Request and visible result.** “Run a quiz about the report, only for our subscribers from Ukraine and Poland; and a survey that closes in three days.” — A quiz with the right answer and an explanation, limited to channel members and countries; a silent multiple-choice survey that closes itself; the survey can be stopped early.
2. **Why these features.** 10.0 added `members_only` and `country_codes` (channel chats only), media in polls and one-option polls; `correct_option_ids` (array) for quizzes; `description`; `close_date` / `open_period` close the poll without a scheduler.
3. **Requirements.** Bot API ≥ 10.0 for the channel-only fields. Production. Channel (polls can't be sent to channel DM chats). Question 1–300, 1–12 options of 1–100 chars, explanation 0–200 with ≤ 2 line feeds, description 0–1024, `open_period` 5–2628000 s xor `close_date`.
4. **Payload.** `examples/payloads/r33-poll-quiz-post.json`. Key part:
   ```json
   {"chat_id": -1001500000001, "question": "Which district fixed potholes fastest in Q3?", "options": [{"text": "Old Town"}, {"text": "Riverside"}],
    "type": "quiz", "correct_option_ids": [1], "explanation": "Riverside: median 3.1 days…",
    "members_only": true, "country_codes": ["UA", "PL", "FT"], "open_period": 86400}
   ```
5. **Code.** `examples/python/tgkit/publish.py` (`_validate_poll`, poll branch of `plan`, `edit` → `repost_required` for polls), `examples/python/recipes/r33_poll_quiz_post.py`.
6. **Sequence and state.** poll model → `validate(context="channel")` → `sendPoll` → ledger → (optional) `stopPoll` → results via `poll` updates for polls the bot sent.
7. **Result.** Mock-up: native quiz card with 4 options; after a wrong answer the explanation shows; survey card with checkboxes and a closing time.
8. **Typical mistake, limits, alternative.** `members_only` in a group (channel-only); `open_period` together with `close_date`; editing the question after sending (impossible — stop and repost); `allow_adding_options` on an anonymous poll. Whether `is_anonymous: false` is accepted in channels is not stated on the current page — keep the default. Alternative: callback buttons for a custom vote with server-side counts.
9. **Run and verify.** `py -3 examples/python/recipes/r33_poll_quiz_post.py` · `tests/test_publishing.py` (`ChannelRules.test_poll_contexts`). Evidence: offline contract.
10. **Adapt.** Use `FT` in `country_codes` to keep anonymous-number users; announce results in a follow-up post or edit the related long read. Related: `references/channel-post-design.md`.
