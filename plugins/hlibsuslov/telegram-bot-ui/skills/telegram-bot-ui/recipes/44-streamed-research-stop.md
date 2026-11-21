# 44 — Streamed research answer with Stop

Agent-operated bot recipe; no changelog rows of its own (see `references/agent-operated-bots.md`). Verified 2026-11-15, Bot API 10.4.

1. **Request and visible result.** “The research agent writes for two minutes and I can't stop it.” — The answer streams as a draft with Stop; Stop ends the model stream and the pending tool calls at once, and one final message keeps the partial answer marked as stopped.
2. **Why the new feature.** 10.3: `can_stop`, `keep_on_stop`, `Update.stopped_message_generation`.
3. **Requirements.** Bot API ≥ 10.3. Private chats only (drafts). `allowed_updates` must include `stopped_message_generation`.
4. **Payload.** Full request sequence: `examples/payloads/r44-streamed-research-stop.json` (generated from the code); incoming fixture: `examples/fixtures/agent_stop_generation.json`. Key part:
   ```json
   {"chat_id": 111111111, "draft_id": 40001, "can_stop": true, "rich_message": {"blocks": ["…"]}}
   ```
   Stop: `{"stopped_message_generation": {"chat": {"id": 111111111}, "draft_id": 40001}}`.
5. **Code.** `AgentBridge.stream_answer(chunks, on_cancel=…)` over `tgkit.generation.Generation`, `examples/python/recipes/r44_streamed_research_stop.py`; the generator's `close()` runs its `finally` (abort the model request there).
6. **Sequence and state.** draft start → chunks coalesced (≥ 1 s or sentence end) → poll for Stop before each chunk → Stop matches chat + thread + draft → on_cancel() + generator.close() → one final sendRichMessage.
7. **Result.** Draft with Stop → after Stop: the partial answer + “Stopped by you — the answer is incomplete.”
8. **Typical mistake, limits, alternative.** Ignoring Stop while the model keeps spending tokens; tool calls still running after Stop; one draft per token; leaving the draft as the only copy (a 30-second preview).
9. **Run and verify.** `py -3 examples/python/recipes/r44_streamed_research_stop.py` · tests/test_generation.py. Evidence: offline contract.
10. **Adapt.** Wire `on_cancel` to your agent's cancellation (abort controller, subprocess kill). Related: recipe 01, `references/streaming-and-editing.md`.
