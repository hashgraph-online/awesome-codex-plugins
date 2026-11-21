# 48 — Coding-agent hooks call the bridge

Agent-operated bot recipe; no changelog rows of its own (see `references/agent-operated-bots.md`). Verified 2026-11-15, Bot API 10.4.

1. **Request and visible result.** “Tell me on Telegram when Claude Code or Codex needs me, and let me approve risky commands from my phone.” — Notification and Stop hooks forward a short message; a PermissionRequest hook becomes a Telegram approval and answers allow/deny; no answer falls back to the local prompt.
2. **Why the new feature.** Approval cards (recipe 40) behind the coding agent's own permission flow.
3. **Requirements.** Claude Code hooks (`Notification`, `Stop`, `PermissionRequest`; command hooks, default timeout 600 s). Codex hooks (`Stop` expects JSON on stdout; `PermissionRequest`; hooks must be trusted; `features.hooks`). Verified 2026-11-15 from the official docs; the Codex `notify` payload fields were NOT verified.
4. **Payload.** Full request sequence: `examples/payloads/r48-coding-agent-hooks.json` (generated from the code); incoming fixture: `examples/fixtures/agent_approve_tap.json`. Key part:
   Claude Code `settings.json`:
   ```json
   {"hooks": {"PermissionRequest": [{"matcher": "Bash", "hooks": [{"type": "command", "timeout": 300,
     "command": "py -3 \"$SKILL/examples/python/agent_bridge\" --live --state \"$HOME/.agent_bridge/state.json\" hook claude-permission --ttl 240"}]}],
     "Stop": [{"hooks": [{"type": "command", "command": "py -3 \"$SKILL/examples/python/agent_bridge\" --live hook claude-stop"}]}]}}
   ```
   Codex `hooks.json`: same shape with `hook codex-stop` / `hook codex-permission`. Hook answer: `{"hookSpecificOutput": {"hookEventName": "PermissionRequest", "decision": {"behavior": "allow"}}}`.
5. **Code.** `examples/python/agent_bridge/hooks.py` (adapters), `examples/python/recipes/r48_coding_agent_hooks.py` (configs as data); CLI `hook claude-notification|claude-stop|claude-permission|codex-stop|codex-permission|codex-notify` (stdin JSON).
6. **Sequence and state.** hook fires → CLI reads stdin → notify (Notification, Stop: never blocks) or approve (PermissionRequest; TTL below the hook timeout) → print decision JSON or `{}`.
7. **Result.** `Approval needed: Bash in shop-api: npm run db:migrate -- --env=staging [Approve] [Reject] [Details]`.
8. **Typical mistake, limits, alternative.** A TTL longer than the hook timeout (hook cancelled, output discarded); a silent allow on timeout; the token in the hook command; exit 2 for PermissionRequest (not honoured — use the JSON decision); notifying on `stop_hook_active`.
9. **Run and verify.** `py -3 examples/python/recipes/r48_coding_agent_hooks.py` · tests/test_agent_bridge_cli.py::Hooks. Evidence: offline contract; hooks were not run inside a real Claude Code or Codex session.
10. **Adapt.** Replace `$SKILL` with the install path; export `AGENT_BRIDGE_TOKEN` and `AGENT_BRIDGE_OPERATOR_ID` where the agent starts. MCP alternative: `examples/mcp/telegram-bridge/README.md`.
