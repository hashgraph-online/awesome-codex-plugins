---
name: portfolio-manager
description: Inspect all configured fantasy teams, saved players, lineup analysis, and transaction proposals through the portfolio MCP. Open the local dashboard for visual review and exact proposal approval.
license: MIT
---

# Portfolio manager

Use the portfolio MCP for requests that span managed teams.
Use the manager and ESPN companion for operations on one selected team.

## Read the portfolio

1. Call `list_managed_teams` to discover configured team keys.
2. Call `get_managed_team` for the selected roster, policy, and limits.
3. Call `get_managed_analysis` for a calculation from its saved snapshot.
4. Call `search_managed_players` to search owned players or the saved player pool.
5. Call `list_managed_proposals` to inspect saved transaction status.

These five tools read local state. They do not contact ESPN or submit transactions.
Use `FFM_PORTFOLIO_MANIFEST` or the command's `--manifest` argument to select a private configuration.
An existing server coordinator manifest is accepted. The tools do not search disks for team stores.

## Interpret results

Check source age, completeness, verified locks, and proposal revisions before describing an action as ready.
Unknown projections remain unknown. Saved pool membership does not prove current player availability.
Keep calculated recommendations separate from prepared proposals.
Keep synthetic results separate from live confirmations.
`pending_waiver` means ESPN accepted a queued claim. It does not establish player ownership.
Check `truncated` before describing proposal history as complete.
The first implementation supports football. Provider and sport fields do not establish support for other sports.

## Dashboard and submissions

Run `fantasy-football-dashboard --demo` for a fictional workspace.
Run the dashboard with the private manifest to inspect actual saved teams.
The dashboard requires `--enable-actions` before it permits submissions.
Its review flow binds approval to one exact saved HTTP season proposal.
It applies the existing team policy and HTTP transaction checks.
Do not treat a read request or dashboard setup as permission to submit a live transaction.

For actions through MCP, select the existing ESPN companion for the exact team context.
Preserve saved modes, limits, protected players, and pending commitments.
Use the season-manager workflow for HTTP transactions and draft-assistant for drafts.
Do not start a browser to service portfolio reads or HTTP season submissions.
An uncertain result requires reconciliation. Do not submit the same transaction again.
