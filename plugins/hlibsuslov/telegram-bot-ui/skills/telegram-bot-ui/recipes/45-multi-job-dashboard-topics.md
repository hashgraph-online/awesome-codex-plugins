# 45 — Multi-job dashboard with private-chat topics

Agent-operated bot recipe; no changelog rows of its own (see `references/agent-operated-bots.md`). Verified 2026-11-15, Bot API 10.4.

1. **Request and visible result.** “Three agent jobs run in parallel and their messages are a mess.” — Each job gets its own topic in the operator's private chat; the main chat has one live widget listing every job; a message typed in a topic reaches only that job.
2. **Why the new feature.** Private-chat topics (`createForumTopic` in a private chat, topic links in 10.4) and HTML widgets (10.4) for one live overview.
3. **Requirements.** Bot API ≥ 10.4 for widgets and topic links (private-chat topics since 9.4). Widgets in production: private chats only; groups, inline and forwards: test server only. The operator's app must support topics in bot chats.
4. **Payload.** Full request sequence: `examples/payloads/r45-multi-job-dashboard-topics.json` (generated from the code). Key part:
   ```json
   {"method": "createForumTopic", "params": {"chat_id": 111111111, "name": "build-142"}}
   {"method": "editMessageWidgetData", "params": {"chat_id": 111111111, "message_id": 1003, "chat_data": "{\"r\":2,\"j\":[…]}"}}
   ```
5. **Code.** `examples/python/recipes/r45_multi_job_dashboard_topics.py` (`Dashboard`), `AgentBridge.progress(thread_id=…)`, `tgkit.widgets.check_widget`, `tgkit.topics.private_topic_link`.
6. **Sequence and state.** createForumTopic per job → card per topic → widget once (caption + chat_data) → edits only when the state changed and ≥ 2 s apart → inbound message routed by `message_thread_id`.
7. **Result.** Widget rows `build-142 Test · running`, `migrate-7 Migrate · failed`; topics `build-142`, `migrate-7`.
8. **Typical mistake, limits, alternative.** A widget to a group in production; state in the HTML; editing the widget every second; no caption; mixing jobs in one thread. Alternative: one text card per job.
9. **Run and verify.** `py -3 examples/python/recipes/r45_multi_job_dashboard_topics.py` · scripts/validate_widget.py. Evidence: offline contract (no real client rendering).
10. **Adapt.** Keep `chat_data` ≤ 1024 bytes (limit): ids and states only. Related: `references/widgets.md`, `references/topics-and-contexts.md`, recipe 08.
