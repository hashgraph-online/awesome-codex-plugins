---
name: token-harbor
description: Open Token Harbor, report stored Sail Power and harbor progress, or help the user configure local Codex token tracking.
---

# Token Harbor

Use the bundled `token-harbor` MCP tools whenever the user asks to open the harbor, check Sail Power, inspect port progress, or troubleshoot the companion game.

## Main workflow

1. Call `open_harbor` when the user wants to play or see the harbor.
2. Return the local URL as a clickable link. Do not narrate token usage after every Codex response.
3. Call `harbor_status` for a concise progress summary when a full game view is unnecessary.
4. Treat the harbor as one global world shared by every Codex project.

## Privacy

- Token Harbor stores numeric usage totals and game state locally under `PLUGIN_DATA`.
- It must not collect raw prompts, assistant text, file contents, or tool output.
- Token telemetry is opt-in. Keep `otel.log_user_prompt = false` when helping with configuration.

## Attention handoff

The game may be active while Codex works. When a task needs approval or finishes, the harbor pauses its active voyage and highlights the task status so the user can return to Codex immediately.
