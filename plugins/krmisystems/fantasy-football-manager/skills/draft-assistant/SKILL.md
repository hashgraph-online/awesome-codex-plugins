---
name: draft-assistant
description: Compare legal draft candidates and run continuous simulations with the manager MCP. Route live ESPN draft requests to the included ESPN companion workflow.
license: MIT
---

# Draft assistant

The plugin includes the manager MCP and ESPN companion MCP.
Read `get_capabilities` and `get_manager_config` before selecting the workflow.
For a real ESPN draft, use the included `espn-automation` skill and its companion tools.
The manager's `execute_demo_action` tool is for synthetic state only.

The published v0.4.0 preview preserves the browser draft adapter.
The source `browser` extra and installed Chrome are required for that adapter.
Its new HTTP transport applies to season operation and does not replace draft submission.
Use `season-manager` after an explicit season connection. Completing a draft does not authorize new season action modes.
Distinguish historical live draft evidence from new source changes and fictional tests.

## Imported drafts and demonstrations

1. Identify the league, team, season, and current board revision.
2. Use `load_demo(mode="draft")` for a requested synthetic demonstration.
3. Use `import_league_snapshot` for supplied JSON observations.
4. Preserve the expected revision when replacing existing state.
5. Call `recommend_draft` for a bounded calculation.
6. Use `start_draft_monitor` for continued calculations from imported observations.
7. Read `get_draft_recommendations` for current results.
8. Use `stop_draft_monitor` when that monitoring task ends.

The imported-state monitor does not read a browser. Use `espn_start_automation` for live ESPN observation.
`load_demo` refuses to replace imported real state or reset confirmed picks.
Use a separate data directory for demonstrations when a real league is loaded.

## Report estimates

Report source age, board revision, actual trial count, and legal alternatives.
Explain that availability is conditional on the modeled opponent selections.
The score compares the next two selections. It is not a championship probability.
More trials do not repair an incomplete board or incorrect projection.
Strategy preferences cannot override roster rules or action limits.

For synthetic actions, use `prepare_action` and `execute_demo_action` within the returned policy requirements.
For live ESPN picks, use `espn_prepare_draft_pick`, `espn_submit_draft_pick`, and `espn_reconcile_draft_pick`.
Do not substitute synthetic execution for a requested live draft action.
