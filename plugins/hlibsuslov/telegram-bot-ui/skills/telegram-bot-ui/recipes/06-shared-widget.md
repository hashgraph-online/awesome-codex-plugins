# 06 — Shared widget: one poll in many chats, revisions, coalesced updates

Registry rows: `10.4-W03`, `10.4-W05`, `10.4-W09`, `10.4-W10`, `10.4-W11` (`recipes/registry.json`). Verified 2026-11-12, Bot API 10.4.

1. **Request and visible result.** “Run a lunch poll that everyone sees live, wherever it's shown.” — The same poll widget in several private chats; bars move for everyone; each person votes once (a new vote replaces the old one). On the test server also: forwards that keep counting, inline results, groups.
2. **Why the new feature.** 10.4 shared widgets keep one public state for every message showing them (`sendSharedWidget`, `editSharedWidgetData`); before, each message had to be edited separately.
3. **Requirements.** Bot API ≥ 10.4. Production: private chats (create once with `is_shared`, re-send by `widget_id`). **Test server only:** forwards (`shared_widget_query`), inline (`InputWidgetMessageContent` / `InputSharedWidgetMessageContent`), groups (`can_send_other_messages`).
4. **Payload.** Full request sequence: `examples/payloads/r06-shared-widget.json` (generated from the code); incoming fixture: `examples/fixtures/shared_widget_query_vote.json`. Key part:
   ```json
   {"chat_id": 111111111, "widget_id": "77700…", "caption": "Poll: Lunch on Friday? Tap to vote.", "chat_data": "{\"u\":111111111}"}
   ```
5. **Code.** `examples/widgets/shared-poll.html` (`watchPublicData`, revision check), `examples/python/recipes/r06_shared_widget.py` (`Poll`, `SharedWidgetWriter`), TS `examples/ts/recipes.ts::sharedWidget`.
6. **Sequence and state.** sendWidget(is_shared, allow_queries) to the bot owner's chat → widget.id → sendSharedWidget × N → vote queries (widget_query / shared_widget_query) keyed by (widget_id, from.id) → answer with the voter's new state at once → editSharedWidgetData ≤ 1/s with r → copyMessage refused → sendSharedWidget instead.
7. **Result.** Mock-up: `Lunch on Friday? [Pizza ▓░░ 0] [Sushi ▓▓▓ 2] [Salad ░░░ 0]`.
8. **Typical mistake, limits, alternative.** Editing per vote (flood wait), forgetting `watchPublicData()`, trusting a forward's location (it has none), selling forwards/inline/groups as production features. Alternative: native poll (`sendPoll`) or an inline keyboard with counts.
9. **Run and verify.** py -3 examples/python/recipes/r06_shared_widget.py · tests/test_widgets.py::Coalescing. Test-server parts: reproduce with TELEGRAM_TEST_ENV=1 and examples/python/live_send.py. Evidence: offline contract.
10. **Adapt.** Copy `SharedWidgetWriter` and the vote keying; adapt the poll model and texts. Related: 05, `widgets.md#shared-widgets`.
