---
name: espn-automation
description: Connect the ESPN companion for browser drafts or HTTP season operation. Run continuous analysis and submit exact transactions within saved user limits.
license: MIT
---

# ESPN automation

Use the `fantasy-football-espn` companion supplied by this plugin for live ESPN drafts.
Use `season-manager` for HTTP lineups, acquisitions, waiver claims, drops, and IR through the same companion.
Use the manager MCP for saved configuration and strategy.
The published v0.4.0 preview adds HTTP season operation and exposes 16 ESPN tools.
Version 0.3.3 retains 13 ESPN tools, browser drafts, and one-swap lineup proposals.
Check the current release evidence before claiming live account acceptance.
Distinguish installed-package checks, authenticated reads, live submissions, and fictional HTTP or browser tests.
Trade execution remains unavailable.

## Connect and verify a draft

1. Read `get_capabilities`, `get_manager_config`, and `espn_get_status`.
2. Identify the requested league ID, team ID, and season.
3. Call `espn_connect` with that context and `phase="draft"`.
4. Have the user complete ESPN sign-in in the browser when required.
5. Call `espn_sync` to obtain a complete current board.
6. Read `espn_get_status` before starting submissions.

Draft phase uses the existing browser adapter and a dedicated local Chrome profile.
The source `browser` extra supplies Playwright. Installed Chrome is also required.
The old draft Chrome extension is not required.
It does not copy cookies from an existing profile.
The optional `cdp_url` must identify a loopback debugging endpoint.
Do not request passwords or cookies through tool arguments.
ESPN Autopick must be verified disabled before direct submission.

## Connect a season without a browser

Use the `season-manager` workflow for the exact season action and its required evidence.
HTTP mode requires a protected session file with only `SWID` and `espn_s2`.
Configure the file path through `FFM_ESPN_CREDENTIAL_FILE` or the server `--credential-file` option.
Never send credential values through tool arguments or prompts.
The optional Linux `v10` importer reads an existing authorized session without starting Chromium.
It does not supply password sign-in or renew an expired session.

Connect with `phase="season"`, `transport="http"`, and the requested `week`.
Call `espn_sync` before analysis. Verify account ownership, targeted roster locks, current period, and pending claims.
HTTP operation requires neither a browser process nor Playwright.
It rejects `cdp_url`. Do not use browser control as an implicit fallback.
Use explicit browser season mode only when that workflow is authorized.

Use separate state directories for separate team contexts.
Both MCP servers for one context must use the same directory.
HTTP controllers sharing an account must use one credential directory to share team leases.
The same league and team cannot have two active controllers through that directory.
Different teams have independent leases.

## Continuous operation

Use the user's authorized mode and limits. Preserve unrelated configuration fields.
Use `update_manager_config` with the current revision for an authorized policy change.
A strategy change does not grant submission authority.

Call `espn_start_automation` for continued observations and simulation batches.
Only the `draft_pick` action mode `automatic` permits the loop to select and submit picks itself.
Do not request per-pick confirmation when the user has already authorized automatic mode.
Review mode requires exact proposal confirmation as described below.

The ordinary loop runs inside the MCP process.
Use `espn_start_standalone_worker` when the user requests operation after Codex closes.
The standalone worker uses saved policy. Draft mode stops when the selected roster is complete.
HTTP season mode follows the explicit week unless authorized `auto_rollover=true` enables verified current-period changes.
Unresolved submissions and pending waivers retain their original week. Backward or unverified periods stop rollover.
Legacy browser season mode requires an explicit reconnect for another week.
Read status before starting another worker.

Call `espn_stop_automation` to pause new actions across processes sharing the data directory.
Clear `automation.paused` through an authorized configuration update when resuming.
Use `espn_disconnect` to release this process's connection after its work ends.
Disconnect is not a shared pause for another worker.

## Exact picks and verification

Use `espn_prepare_draft_pick(player_id)` to refresh the board and prepare a specific pick.
Show its player, pick number, league, mode, and required confirmation.
Use `espn_submit_draft_pick(proposal_id, confirmation=true)` after required review confirmation.
Automatic mode can submit without per-pick confirmation within the user's authorization.

A proposal can grant only one click claim.
If a response reports `awaiting_verification`, call `espn_reconcile_draft_pick`.
Never retry an uncertain submission as a new click or proposal.
Missing, empty, or failed browser results do not prove success.
Report `confirmed` only after the platform identifies the expected player at the expected pick.
Report `not_selected` when that pick identifies another player.

For HTTP season actions, use `espn_prepare_season_action`, `espn_submit_season_action`, and `espn_reconcile_season_action`.
Authorization records one durable claim before its POST. Repeated submission cannot send another request for that proposal.
`pending_waiver` does not establish ownership. A dependent lineup change must wait for confirmed acquisition.
`not_submitted` identifies a proved preflight failure before the transaction request.
Correct its cause before preparing another authorized proposal.
An uncertain result requires reconciliation without a new submission or replacement proposal.
Named coverage repairs require saved player authorization. Unknown projections must remain unknown.

Read `espn_get_status` for worker health, pending claims, and current recommendations.
Report actual trials and source age. Treat model scores and availability as estimates.
Do not claim championship odds or unverified live write acceptance.
Report the actual transport, action modes, unresolved results, and verified scope of automatic operation.
