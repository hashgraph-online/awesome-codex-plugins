# 41 — Long build/test run with live status and a final report

Agent-operated bot recipe; no changelog rows of its own (see `references/agent-operated-bots.md`). Verified 2026-11-15, Bot API 10.4.

1. **Request and visible result.** “My CI agent sends 200 messages per run.” — One status card with named stages that changes in place, one short notice when it ends, a Rich Message report (table, checklist, collapsed log tail) and the full log as a document.
2. **Why the new feature.** Rich Messages give a real table (`is_compact`, 10.3) and a `details` block for the log tail; edits keep one message per job.
3. **Requirements.** Bot API ≥ 10.1 for rich messages (fallback: plain text). Production, the operator's private chat.
4. **Payload.** Full request sequence: `examples/payloads/r41-build-live-status.json` (generated from the code). Key part:
   ```json
   {"chat_id": 111111111, "message_id": 1001, "parse_mode": "HTML",
    "text": "<b>CI #142 · shop-api</b> — failed · 12m 03s\n✅ Install\n✅ Compile\n✅ Unit tests\n❌ E2E tests\n▫️ Package"}
   ```
5. **Code.** `AgentBridge.progress` (stage change ≥ 3 s apart, note-only change ≥ 15 s, identical content skipped, final never throttled), `report(data=…)`, `send_file`; `examples/python/recipes/r41_build_live_status.py`; CLI `progress --key ci-142 --stage "Unit tests"`, `report --json …`, `send-file …`.
6. **Sequence and state.** start → card sent, id persisted → runner events update the card → edit when the throttle allows → failed/done → final edit + reply notice → sendRichMessage report → sendDocument log.
7. **Result.** Card `CI #142 — failed · 12m … ❌ E2E tests`; report: heading, summary, 4-row table, checklist, “Log tail” details. 179 runner events → 45 edits.
8. **Typical mistake, limits, alternative.** Editing per log line; a fake percentage; pasting a 2 000-line log as messages; re-sending identical text. Limits: 4096 characters per message, 32 768 per rich message, 50 MB per upload.
9. **Run and verify.** `py -3 examples/python/recipes/r41_build_live_status.py` · tests/test_agent_bridge.py::Progress. Evidence: offline contract.
10. **Adapt.** Map your runner's steps to stage names people understand (≤ 8). Related: `references/agent-operated-bots.md`, `references/dynamic-feedback-and-streaming.md`.
