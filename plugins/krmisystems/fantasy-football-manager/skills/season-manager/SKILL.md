---
name: season-manager
description: Manage ESPN season lineups, acquisitions, waiver claims, and IR through authenticated HTTP. Preserve user limits and reconcile every transaction.
license: MIT
---

# Season manager

Read `get_capabilities` and `get_manager_config` before selecting a season workflow.
Read `espn_get_status` and discover the installed companion tools.
The published v0.4.0 preview supplies 16 ESPN tools and HTTP season operation.
Version 0.3.3 has 13 ESPN tools and browser lineup swaps.
Use the installed version's capabilities. Do not infer a live write from source code or fictional tests.
The manager provides weekly analysis and synthetic execution. The ESPN companion owns real submissions.
Trade execution remains unavailable.
For live ESPN drafts, use the included `espn-automation` skill and companion tools.

## Review the week

1. Read `get_team` when a snapshot is loaded.
2. Identify the league, team, season, and week.
3. Use `load_demo(mode="season")` for a requested synthetic demonstration.
4. Use `import_league_snapshot` for supplied weekly observations.
5. Call `recommend_lineup` for a legal weekly comparison.
6. Call `rank_waiver_candidates` to compare additions and required drops.
7. Use `get_power_rankings` as a projection-based comparison.

Read `get_source_status` after an import.
Report missing projections, eligibility, locks, ownership, and pending claims.
Do not divide season totals into invented weekly projections.
Floor and upside comparisons require supplied bounds.
Projection rankings do not establish matchup or championship probabilities.
Use a separate data directory for demonstrations when real league state is loaded.

## Policy and proposals

Preserve the user's authorized action modes and hard limits.
Use `update_manager_config` with the current revision for an authorized configuration change.
Strategy changes do not grant action permission.

Use `prepare_action` for supported synthetic lineup, acquisition, waiver, or drop proposals.
Review the complete add/drop transaction and its budget effects.
An empty drop list permits no drops in `listed_only` mode.
Protected players and pending commitments remain hard checks.

Use `execute_demo_action` only within current authorization and required confirmation.
Read the resulting state and `get_action_history` after execution.
For a supported live season action, use the HTTP companion workflow below.
For a trade request, report the unavailable execution adapter and provide only supported analysis.
Do not describe a synthetic result as a change to the real league.

## HTTP season connection

1. Verify that the HTTP companion and protected session file are configured.
2. Call `espn_connect` with the selected context, `phase="season"`, `transport="http"`, and the requested `week`.
3. Call `espn_sync` and verify source completeness, current week, and own-team locks.
4. Verify authenticated ownership and pending transaction evidence.
5. Preserve the user's authorized action modes, strategy, and limits.
6. Call `espn_start_automation` for continuous operation when requested.

HTTP season operation does not start or control a browser. It requires neither Chrome nor Playwright.
The protected file contains only `SWID` and `espn_s2`.
Configure its path through `FFM_ESPN_CREDENTIAL_FILE` or the server `--credential-file` option.
Never request or return credential values through prompts or tool arguments.
The optional Linux `v10` importer reads an existing authorized session without starting Chromium.
It does not renew an expired session or support all operating-system encryption formats.
If authentication fails, report the failed prerequisite. Do not silently switch to browser control.

Use the same state directory for both MCP servers that manage one context.
Use one credential directory for controllers that share the same account.
The HTTP team lease blocks simultaneous control of the same league and team through that directory.
Different teams can hold separate leases. A connection close releases its lease.

## Exact season transactions

Use `espn_prepare_season_action` with one of these actions:

- `set_lineup`: provide the complete starter map, including unchanged starters.
- `free_agent_add` or `waiver_claim`: provide `player_id`, an optional `drop_id`, and `bid`.
- `drop_player`, `move_to_ir`, or `activate_from_ir`: provide `player_id` only.

Traditional waivers and free-agent additions require a zero bid.
Use a whole-number FAAB bid within league and saved user limits.
A required drop must have separate permission. Protected players and pending commitments remain hard checks.
Unknown counters or incomplete budget evidence cannot establish unused capacity.

Review the returned action, exact payload, mode, revisions, and confirmation requirement.
Use `espn_submit_season_action` for that proposal.
Set `confirmation=true` only after required approval of the exact review-mode proposal.
Do not request per-action confirmation for actions already authorized in automatic mode.
Use `espn_reconcile_season_action` for another observation of an uncertain result.

An HTTP lineup proposal can contain several legal positional changes.
An acquisition and a later starter assignment require separate confirmed transactions.
The automatic loop evaluates one admitted transaction per cycle before observing again.
Automatic FAAB claims use the league minimum. A different bid requires an exact proposal.

## Coverage and IR

Missing projections remain unknown. Never substitute zero or divide season totals into a weekly estimate.
Ordinary changes require a known improvement that meets the saved limit.
A coverage exception requires the current starter in `limits.coverage_repair_ids`.
A nonempty `limits.coverage_repair_add_ids` restricts replacement candidates to that list.
For a manual repair proposal, pass the named starter through `repair_player_id`.
The repair must replace that starter's verified coverage gap only.
Preserve eligibility, locks, available projections for the replacement, drop permission, and budgets.
Do not expand repair lists without user authorization.

An IR move requires ESPN's explicit `injured=true`, IR slot eligibility, clear locks, and available IR capacity.
An injury label or `eligibleSlots` membership alone is insufficient.
Activation requires bench eligibility and an active roster vacancy.
Do not drop a player without authorization to create that vacancy.

## Results, rollover, and lifetime

`confirmed` requires the observed result. An acquisition requires observed ownership.
`pending_waiver` means a queued claim. Do not start that player or report ownership before later confirmation.
`not_submitted` proves that preflight ended before the transaction request began.
Correct that cause before preparing a new authorized proposal.
`awaiting_verification` requires more observation. Never retry it as a new proposal.
`rejected`, `cancelled`, and `conflict` require inspection of the saved receipt and actual state.
Read `espn_get_status` and `get_action_history` after submission.

Set `auto_rollover=true` only when the user authorizes continued operation across scoring periods.
The service follows ESPN's verified current period. Backward or unknown periods stop rollover.
Unresolved submissions and pending waivers retain their original week.
Use `espn_start_standalone_worker` for operation after the MCP client closes, when requested.
Use `espn_stop_automation` for a shared pause.
Disconnecting one process does not pause another worker. A bounded in-flight operation can finish after a pause request.

## Legacy browser lineup operation

Use explicit `transport="browser"` only for an authorized browser workflow.
This adapter requires the `browser` extra and Chrome.
Use `espn_prepare_lineup`, `espn_submit_lineup`, and `espn_reconcile_lineup` for one legal swap per proposal.
Each intermediate swap must meet the improvement limit.
Do not report a full optimized lineup as applied after one swap.
Reconnect explicitly for another week. This adapter does not execute HTTP acquisitions, IR moves, or automatic rollover.
