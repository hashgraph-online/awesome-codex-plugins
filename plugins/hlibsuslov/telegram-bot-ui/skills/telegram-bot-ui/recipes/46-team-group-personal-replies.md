# 46 — The agent in a team group: personal replies

Agent-operated bot recipe; no changelog rows of its own (see `references/agent-operated-bots.md`). Verified 2026-11-15, Bot API 10.4.

1. **Request and visible result.** “Put the CI agent in our team chat, but don't dump everyone's failures and logs there.” — One shared card; “My failures” shows each member only their own tests; “Send me the log” never posts the log in the group.
2. **Why the new feature.** Ephemeral replies to callback queries (10.3 parameters object, 10.4 short form without receiver and chat).
3. **Requirements.** Bot API ≥ 10.4 for the short form (10.3 form also works). Groups and supergroups, not channel DM chats. Allowlisted group and member ids.
4. **Payload.** Full request sequence: `examples/payloads/r46-team-group-personal-replies.json` (generated from the code). Key part:
   ```json
   {"ephemeral_message_parameters": {"callback_query_id": "4382000000980002"}, "text": "Your failing tests:\n• search.spec.ts › filters by price …"}
   ```
5. **Code.** `tgkit.ephemeral.PersonalPanels` with the bridge as transport (so redaction applies), `security.Allowlist(members, group_chats)`, `examples/python/recipes/r46_team_group_personal_replies.py`.
6. **Sequence and state.** shared card → member taps → classify (allowlisted group + member) → render(member id) server-side → ephemeral sendMessage → answerCallbackQuery; non-member → dropped; log request from a member → private alert.
7. **Result.** Bob sees only his two search specs; Alice sees her checkout spec; the group sees one card.
8. **Typical mistake, limits, alternative.** A public fallback when the ephemeral send fails; logs or files in the group; operator actions open to members; replying to strangers.
9. **Run and verify.** `py -3 examples/python/recipes/r46_team_group_personal_replies.py` · tests/test_ephemeral.py. Evidence: offline contract.
10. **Adapt.** Group id in `AGENT_BRIDGE_GROUP_IDS`, members in `AGENT_BRIDGE_MEMBER_IDS`. Related: recipe 04, `references/ephemeral-and-personal.md`.
