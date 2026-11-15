# 08 — Bot with several conversation topics

Registry rows: `10.4-X07` (`recipes/registry.json`). Verified 2026-11-12, Bot API 10.4.

1. **Request and visible result.** “Users open several topics with our assistant. Answers mix up and Stop stops the wrong one.” — Two answers stream in parallel in two topics; Stop in topic 12 stops only that answer; a “Go to topic” button jumps from topic 11 to topic 12.
2. **Why the new feature.** 10.3 Stop updates carry `message_thread_id`; 10.4 adds `https://t.me/<bot>/<thread>` links that open a topic of the user's private chat. Forum topics and channel DM topics use different fields.
3. **Requirements.** Bot API ≥ 10.4 for links (Stop: 10.3). Production. Private chats with the bot's topic mode; the link works only for that user.
4. **Payload.** Full request sequence: `examples/payloads/r08-multi-topic-bot.json` (generated from the code); incoming fixture: `examples/fixtures/stopped_message_generation_topic.json`. Key part:
   ```json
   {"chat_id": 111111111, "message_thread_id": 11, "text": "The other answer was stopped — open it to continue:",
    "reply_markup": {"inline_keyboard": [[{"text": "Go to topic", "url": "https://t.me/orders_demo_bot/12"}]]}}
   ```
5. **Code.** `examples/python/tgkit/topics.py` (`Address`, `private_topic_link`), `generation.py::OperationRegistry`, `examples/python/recipes/r08_multi_topic_bot.py`, TS `examples/ts/recipes.ts::multiTopic`.
6. **Sequence and state.** message in topic → Address.of(message) → Generation keyed (chat, thread, draft) → Stop update → find_for_stop → only that op stops → second op in a busy topic refused → link to another topic.
7. **Result.** Mock-up: topic 11 — full answer + [Go to topic]; topic 12 — partial answer “stopped”.
8. **Typical mistake, limits, alternative.** Keying state by chat only; using `message_thread_id` in channel DM chats; posting topic links publicly; drafts in groups. Alternative: one conversation with a “New question” reset.
9. **Run and verify.** py -3 examples/python/recipes/r08_multi_topic_bot.py · tests/test_generation.py::Endings. Evidence: offline contract.
10. **Adapt.** Copy `Address` and key every per-conversation store by `conversation_key`. Related: 01, `topics-and-contexts.md`.
