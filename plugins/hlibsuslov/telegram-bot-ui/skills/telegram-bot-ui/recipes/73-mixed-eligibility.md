# 73 — Mixed eligibility: icons in private chats, Unicode in the channel

Registry rows: none of its own — 9.4 owner-Premium route. Verified 2026-11-15, Bot API
10.4. Background: `references/custom-emoji.md#eligibility-per-send-context`.

1. **Request and visible result.** “Same order update goes to customers, a group, our news
   channel and business replies.” — Icons in private, group and supergroup chats; the
   channel copy, the business reply and the inline result use the Unicode screen.
2. **Why the new features.** 9.4 made custom emoji available to owners with Premium, but only
   for messages the bot sends directly to private, group and supergroup chats.
3. **Requirements.** Owner Premium, no Fragment usernames. "Directly sent by the bot" is
   read conservatively: business sends (on behalf of a user) and inline results (sent by
   the user) are excluded.
4. **Payload.** `examples/payloads/r73-mixed-eligibility.json`.
5. **Code.** `examples/python/recipes/r73_mixed_eligibility.py`, `tgkit/icons.py`
   (`Eligibility.route`, `Eligibility.explain`, `SendContext`).
6. **Sequence and state.** one handler → for each destination `icons.send(t, method, params,
   SendContext(chat_type, business=…, inline=…))` → the view decides for the whole message.
7. **Result.** Mock-up: private `[icon] Order #1042`; channel `📦 Order #1042`.
8. **Typical mistake, limits, alternative.** A global "icons on" flag that also hits the
   channel; per-button decisions that mix styles. Alternative: buy Fragment usernames to
   cover every destination.
9. **Run and verify.** `py -3 examples/python/recipes/r73_mixed_eligibility.py` · tests in
   `tests/test_emoji_icons.py`. Evidence: offline contract; the business/inline reading is
   an interpretation of the API wording.
10. **Adapt.** Build the `SendContext` where you already know the chat type and whether a
    `business_connection_id` is used. Related: 72, 74.
