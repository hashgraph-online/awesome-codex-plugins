# 47 — Incident alert with acknowledge and escalate

Agent-operated bot recipe; no changelog rows of its own (see `references/agent-operated-bots.md`). Verified 2026-11-15, Bot API 10.4.

1. **Request and visible result.** “Page me when checkout breaks; if I don't react in 5 minutes, page the backup.” — A loud alert with Acknowledge / Escalate; silence or Escalate pages the secondary in their own chat; two silent pages end in an explicit fallback.
2. **Why the new feature.** Bound buttons (same binding as approvals) with per-page approver ids; disabled result buttons close each page.
3. **Requirements.** Bot API ≥ 10.3 (disabled buttons). Private chats of each on-call person (each must have started the bot).
4. **Payload.** Full request sequence: `examples/payloads/r47-incident-alert.json` (generated from the code). Key part:
   ```json
   {"chat_id": 111111111, "text": "🔴 INC-311 · checkout error rate 18% …", "reply_markup": {"inline_keyboard": [[{"text": "Acknowledge", "callback_data": "aq:…:0"}], [{"text": "Escalate", "callback_data": "aq:…:1"}]]}}
   ```
5. **Code.** `AgentBridge.request_answer(choices, allow_text=False, approvers={on_call})` + `wait`; escalation loop in `examples/python/recipes/r47_incident_alert.py`.
6. **Sequence and state.** page primary (5-min ack window) → ack → done | escalate or timeout → close page → page secondary → ack | fallback message.
7. **Result.** `[Acknowledge] [Escalate]` → `No answer — I stopped here.` (disabled) → secondary acknowledges.
8. **Typical mistake, limits, alternative.** Paging a group; anyone acknowledging anyone's page; silent alerts; no end state after the last page.
9. **Run and verify.** `py -3 examples/python/recipes/r47_incident_alert.py`. Evidence: offline contract.
10. **Adapt.** Keep the rotation in config (ids, ack window). Related: `references/channels-and-broadcasting.md`.
