# 40 — Deploy approval gate

Agent-operated bot recipe; no changelog rows of its own (see `references/agent-operated-bots.md`). Verified 2026-11-15, Bot API 10.4.

1. **Request and visible result.** “The agent must not deploy to production until I say so — from my phone.” — The operator gets one message: plan, scope, “Expires in 15 min. No answer = not approved.”, red **Approve**, plain **Reject**, **Details**. After a tap the buttons become one disabled button “Approved by Alice” and the status card moves on. Reject or silence: nothing runs.
2. **Why the new feature.** Disabled buttons (10.3, `disabled: {}`) close the card honestly after the decision; `style` (9.4) colours the irreversible action by meaning; `answerCallbackQuery` alerts tell a wrong presser privately.
3. **Requirements.** Bot API ≥ 10.3 for `disabled` (older: remove the keyboard instead). Production, operator's private chat (group variant: allowlisted group, operator ids as approvers). `allowed_updates` includes `callback_query`.
4. **Payload.** Full request sequence: `examples/payloads/r40-deploy-approval-gate.json` (generated from the code); incoming fixture: `examples/fixtures/agent_approve_tap.json`. Key part:
   ```json
   {"reply_markup": {"inline_keyboard": [[{"text": "Approve", "callback_data": "ap:081da789:n6d6976b:a", "style": "danger"},
     {"text": "Reject", "callback_data": "ap:081da789:n6d6976b:r"}], [{"text": "Details", "callback_data": "ap:081da789:n6d6976b:d"}]]}}
   ```
   After the decision: `{"inline_keyboard": [[{"text": "Approved by Alice", "disabled": {}}]]}`.
5. **Code.** `examples/python/agent_bridge/approvals.py` (`ApprovalBook`), `bridge.py` (`request_approval`, `wait`), `examples/python/recipes/r40_deploy_approval_gate.py`; CLI `py -3 -m agent_bridge approve "…" --details … --ttl 900 --destructive` (exit 0 approved, 3 rejected, 4 expired); TS `examples/ts/agent-bridge/agent-bridge.ts::ApprovalBook`.
6. **Sequence and state.** create request (rid, nonce, approvers, expires) → persist → sendMessage → attach message_id → poll → callback → binding checks (nonce, message, chat, approver, expiry, still open) → answerCallbackQuery → editMessageText with one disabled result button → run only on `approved`.
7. **Result.** `Deploy shop-api v1.4.0 → production … [Approve] [Reject] [Details]` (a destructive request puts the red Approve alone in the last row: `[Reject] / [Details] / [Approve]`) → `[Approved by Alice]` (disabled).
8. **Typical mistake, limits, alternative.** Accepting typed “approve”; trusting the username; one callback_data for every request; letting Details decide; treating timeout as consent; skipping `answerCallbackQuery`. Alternative: the coding agent's own permission prompt through hooks (recipe 48).
9. **Run and verify.** `py -3 examples/python/recipes/r40_deploy_approval_gate.py` · tests/test_agent_bridge.py::ApprovalBinding (forged nonce, garbage, copied message, non-approver, stale, duplicate, Details, typed approve). Evidence: offline contract.
10. **Adapt.** Set `AGENT_BRIDGE_OPERATOR_ID`; keep `--state` so a restarted gate resolves the same request; use `--destructive` only for irreversible actions. Related: `references/agent-bot-security.md`, `references/buttons-and-styles.md`.
