# 04 — Shared card and personal panels in a group

Registry rows: `10.4-E01`, `10.4-E02`, `10.3-E01`, `10.3-E03` (`recipes/registry.json`). Verified 2026-11-12, Bot API 10.4.

1. **Request and visible result.** “In our team chat everyone taps ‘My order’ on the lunch card and the bot posts everyone's order publicly. Make it private per person.” — The shared card stays as is; each person who taps sees *their* order in an ephemeral panel only they can see, with Refresh / Close. Nobody else sees it. If private delivery fails, the person gets a private alert or a link to the bot — never a public message.
2. **Why the new feature.** Ephemeral messages (10.2) became one parameter object in 10.3 (`EphemeralMessageParameters`, also on `sendRichMessage`, `replace_callback_query_message`), and 10.4 allows callback replies without `receiver_user_id`/`chat_id` in any chat except channel DMs.
3. **Requirements.** Bot API ≥ 10.3 (10.4 short form). Production. Groups/supergroups (any chat except channel DM chats for the 10.4 form). Within 15 s of the tap. `answerCallbackQuery` still required.
4. **Payload.** Full request sequence: `examples/payloads/r04-shared-card-personal-panel.json` (generated from the code); incoming fixture: `examples/fixtures/callback_card_user_a.json`. Key part:
   ```json
   {"ephemeral_message_parameters": {"callback_query_id": "4382000000000000001"},
    "text": "Your order: Margherita, no olives — $9.50",
    "reply_markup": {"inline_keyboard": [[{"text": "Refresh", "callback_data": "panel:refresh"}, {"text": "Close", "callback_data": "panel:close"}]]}}
   ```
5. **Code.** `examples/python/tgkit/ephemeral.py` (`ephemeral_params`, `guard_audience`, `PersonalPanels`, `migrate_ephemeral_10_2`), `examples/python/recipes/r04_shared_card_personal_panel.py`, TS `examples/ts/recipes.ts::personalPanels`.
6. **Sequence and state.** callback (from A) → render(A's data) → sendMessage + ephemeral params → Message{message_id: 0, ephemeral_message_id} stored per (chat, user) with TTL → answerCallbackQuery → panel button → ownership check (`from` vs panel owner / `receiver_user`) → editEphemeralMessageText / deleteEphemeralMessage.
7. **Result.** Mock-up (A's screen only): `Your order: Margherita, no olives — $9.50 [Refresh] [Close]`.
8. **Typical mistake, limits, alternative.** Falling back to `sendMessage` in the group; skipping `answerCallbackQuery`; `replace_callback_query_message` on a callback from an ephemeral message; `web_app`/`login_url` buttons in ephemeral messages; promising delivery. Alternative: `answerCallbackQuery` alert (≤ 200 chars) or a deep link to the private chat.
9. **Run and verify.** py -3 examples/python/recipes/r04_shared_card_personal_panel.py · tests/test_ephemeral.py (all failure classes; randomized two-user interleavings). Evidence: offline contract.
10. **Adapt.** Copy `ephemeral.py`; adapt `render(user_id)` to your data access with server-side authorization; choose the 10.3 or 10.4 form per your SDK. Related: `ephemeral-and-personal.md`, 02.
