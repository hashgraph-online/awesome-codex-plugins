# 42 — Nightly job digest

Agent-operated bot recipe; no changelog rows of its own (see `references/agent-operated-bots.md`). Verified 2026-11-15, Bot API 10.4.

1. **Request and visible result.** “Tell me every morning how the night jobs went, but don't wake me when everything is green.” — One digest per night: silent when green, normal when something failed, plus one loud line naming the failure.
2. **Why the new feature.** A Rich Message table replaces the monospace grid; `disable_notification` separates FYI from action.
3. **Requirements.** Bot API ≥ 10.1 (rich), plain-text fallback on 404/unsupported. Production, private chat.
4. **Payload.** Full request sequence: `examples/payloads/r42-nightly-digest.json` (generated from the code); incoming fixture: `examples/fixtures/agent_report.json`. Key part:
   ```json
   {"chat_id": 111111111, "disable_notification": true, "rich_message": {"blocks": [{"type": "heading", "size": 2, "text": "Nightly jobs · 15 Nov · 3/3 passed"}, {"type": "table", "cells": "…", "is_bordered": true}]}}
   ```
5. **Code.** `agent_bridge.bridge.report_blocks`, `AgentBridge.report(silent=…)`, `examples/python/recipes/r42_nightly_digest.py`; CLI `py -3 -m agent_bridge report --json ../fixtures/agent_report.json`.
6. **Sequence and state.** scheduler → collect results → report_blocks → sendRichMessage (silent if green) → on failure one sendMessage → rich rejected: same digest as plain text, fallback logged.
7. **Result.** `Nightly jobs · 15 Nov · 3/4 passed` + table `Job | Result | Time`.
8. **Typical mistake, limits, alternative.** One message per job; a loud ping for green nights; tables as code blocks; secrets in job output (redacted: `password=…` → `[REDACTED]`).
9. **Run and verify.** `py -3 examples/python/recipes/r42_nightly_digest.py` · tests/test_agent_bridge_cli.py::TokenNeverLeaks. Evidence: offline contract.
10. **Adapt.** Feed your scheduler's results; ≤ 20 columns (limit), about 10 rows (heuristic). Related: `references/tables.md`.
