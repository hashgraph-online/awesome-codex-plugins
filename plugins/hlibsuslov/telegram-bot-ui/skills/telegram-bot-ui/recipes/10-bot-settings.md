# 10 — Bot settings from code

Registry rows: `10.5-S01`, `10.5-S02`, `10.5-S03`, `10.5-S04`, `10.5-S05`, `10.5-S06`, `10.5-S07`, `10.5-S08`, `10.5-G01`, `10.5-G02` (`recipes/registry.json`). Verified 2026-11-22, Bot API 10.5.

1. **Request and visible result.** “Stop clicking through BotFather: our topics, inline placeholder and privacy should live in the repo. Also let me invite five testers.” — On start the bot sends one `setMySettings` with only what changed; private chats get topics in a sidebar; the inline field reads “Search orders…”; the owner gets an “Invite people” button; an invited tester is greeted with the owner's name; buttons keep working when callbacks arrive with `inline_message_id`.
2. **Why the new feature.** 10.5 adds `setMySettings` (inline mode, location, feedback share, groups, privacy, business, managed bots, guest and join-request queries, topics + `has_topic_sidebar`, bot-to-bot, `callback_query_mode`) and returns `BotFullInfo` from `getMe`, so settings can be read, compared and written by code. Owners invite up to 10 users with `https://t.me/botinvite/<username>`; `WriteAccessAllowed.inviter` marks those chats.
3. **Requirements.** Bot API ≥ 10.5. Production. Typed SDKs without 10.5: call `setMySettings` raw and read `getMe` raw. The invite link works only for the bot's owner.
4. **Payload.** Full request sequence: `examples/payloads/r10-bot-settings.json` (generated from the code); fixtures `examples/fixtures/get_me_bot_full_info.json`, `message_write_access_invited.json`, `callback_bot_message_inline_mode.json`. Key part:
   ```json
   {"inline_query_placeholder": "Search orders…", "has_topics_enabled": true, "allows_users_to_create_topics": true,
    "has_topic_sidebar": true, "inline_feedback_share_denominator": 10, "callback_query_mode": "auto"}
   ```
5. **Code.** `examples/python/tgkit/settings.py` (`validate`, `plan`, `apply`, `callback_target`, `addressed_to_me`, `invite_link`, `inviter_of`), `examples/python/recipes/r10_bot_settings.py`.
6. **Sequence and state.** start → getMe (BotFullInfo) → plan = desired − current → validate → one setMySettings (or none) → `/invite` from the owner → botinvite URL button → invited user's `write_access_allowed.inviter` → greeting + owner notice → callback with `inline_message_id` → answer → edit by that id, state keyed by `from.id`.
7. **Result.** Mock-up: owner — “Invite up to 10 people at once…” [Invite people]; tester — “Alex invited you to try Orders. Pick where to start:” [Track an order] [How it works]; settings message edited in place to “Topics are on…” [Turn off].
8. **Typical mistake, limits, alternative.** Calling `setMySettings` with every field on every start (write-only fields can't be compared; readable ones can); turning privacy off or inline location on without a human's yes; reading `can_join_groups` from a `User`; routing an `inline_message_id` callback by chat; showing the invite link to non-owners; broadcasting to invited users. Alternative: keep BotFather as the only owner of the settings and only read them via `getMe`.
9. **Run and verify.** py -3 examples/python/recipes/r10_bot_settings.py · tests/test_bot_settings.py. Evidence: offline contract.
10. **Adapt.** Put `DESIRED` in your config, call `settings.apply` in the deploy step, and switch your callback router to `settings.callback_target` before choosing `auto` or `inline`. Related: 08, 60, 23, `bot-settings.md`.
