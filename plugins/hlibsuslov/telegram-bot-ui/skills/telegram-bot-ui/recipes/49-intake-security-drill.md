# 49 — Intake and security drill

Agent-operated bot recipe; no changelog rows of its own (see `references/agent-operated-bots.md`). Verified 2026-11-15, Bot API 10.4.

1. **Request and visible result.** “Make sure nobody else can steer my agent through its bot.” — One polling loop meets a stranger with the operator's name, an injection pasted by the operator, an unknown group, a restart with redelivered updates, and webhook requests without the secret.
2. **Why the new feature.** Explicit `allowed_updates` incl. `stopped_message_generation`; `my_chat_member` for unknown chats; webhook `secret_token`.
3. **Requirements.** Any Bot API version; long polling (no webhook set) or a webhook with `secret_token`. Updates are kept at most 24 hours.
4. **Payload.** Full request sequence: `examples/payloads/r49-intake-security-drill.json` (generated from the code); incoming fixture: `examples/fixtures/agent_stranger_message.json`. Key part:
   ```json
   {"method": "getUpdates", "params": {"offset": 910106, "limit": 100, "timeout": 25,
    "allowed_updates": ["message", "callback_query", "my_chat_member", "stopped_message_generation"]}}
   ```
5. **Code.** `examples/python/agent_bridge/intake.py` (`PollingSource`, `Intake`, `SenderGate`, `webhook_events`), `security.classify`, `store.JsonStore`, `examples/python/recipes/r49_intake_security_drill.py`.
6. **Sequence and state.** getUpdates(offset) → per update: dedup → classify → handle → mark seen + save → next offset. Webhook: verify header (constant time) → dedup → 200 fast.
7. **Result.** Operator `/status` → command; stranger → nothing; pasted injection → text event with `injection_signals`; unknown group → leaveChat + alert by ids.
8. **Typical mistake, limits, alternative.** Trusting usernames; omitting `allowed_updates`; saving the offset before handling; replying to strangers; plain `==` for the webhook secret.
9. **Run and verify.** `py -3 examples/python/recipes/r49_intake_security_drill.py` · tests/test_agent_bridge.py::Allowlisting, ::RestartSafety, ::Intake. Evidence: offline contract.
10. **Adapt.** Run this drill against your own handlers. Related: `references/agent-bot-security.md`.
