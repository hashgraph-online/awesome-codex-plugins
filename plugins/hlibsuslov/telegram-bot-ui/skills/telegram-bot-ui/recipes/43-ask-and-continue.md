# 43 — Ask the operator and continue

Agent-operated bot recipe; no changelog rows of its own (see `references/agent-operated-bots.md`). Verified 2026-11-15, Bot API 10.4.

1. **Request and visible result.** “When the agent is unsure, it should ask me and keep going if I don't answer.” — A question with three quick choices and a reply field, the default stated up front, one reminder at 10 min, the question closed visibly at 15 min with the default used.
2. **Why the new feature.** 10.3 allows `force_reply` on an inline keyboard: tap or type in the same message. A disabled result button closes the question.
3. **Requirements.** Bot API ≥ 10.3 (older: ForceReply only, or buttons only). Private chat. `force_reply` on an inline keyboard cannot change in an edit.
4. **Payload.** Full request sequence: `examples/payloads/r43-ask-and-continue.json` (generated from the code); incoming fixture: `examples/fixtures/agent_operator_reply.json`. Key part:
   ```json
   {"reply_markup": {"inline_keyboard": [[{"text": "Skip them for now", "callback_data": "aq:081da789:n6d6976b:0"}], "…"], "force_reply": true}}
   ```
5. **Code.** `AgentBridge.request_answer` / `ask` / `wait(remind_after=…)`, `examples/python/recipes/r43_ask_and_continue.py`; CLI `ask "…" --choice A --choice B --default A --timeout 900 --remind-after 600` (exit 0 answered, 4 timeout).
6. **Sequence and state.** create ask (rid, nonce, expiry, default) → sendMessage → wait: bound tap or reply to the question (operator id, not forwarded) → one reminder → expiry → close with default → JSON (`used_default`, `content_is_untrusted_data`).
7. **Result.** `The payments tests are flaky … [Skip them for now] [Fix the flakiness first] [Stop and wait for me]` + reply field.
8. **Typical mistake, limits, alternative.** Blocking forever; no default; executing the typed answer as an instruction; changing `force_reply` in the closing edit. Alternative: an approval (recipe 40) when the answer is a consequential yes/no.
9. **Run and verify.** `py -3 examples/python/recipes/r43_ask_and_continue.py` · tests/test_agent_bridge.py::Asking. Evidence: offline contract.
10. **Adapt.** Pick the least destructive path as the default. Related: recipe 03, `references/reply-keyboards.md`.
