# Workflow: replay a historical window

1. Choose the window. For a named episode, call `risk_scenario_library`
   and take `start` and `end` from the window. Tell the user the reason
   and the source in one line. For the Lehman window, say that its end
   date is a library convention inside the source's "late October".
2. Get the prices from the user. One series per portfolio asset, dated
   levels, containing both window dates exactly. Ask which series stands
   for an asset that has no history of its own and pass it in `proxies`.
   Do not supply, remember or invent levels.
3. Choose the measure with the user: `end_over_start` (what the window
   did from start to end) or `worst_peak_to_trough` (each asset's worst
   fall inside it). Never switch measure silently.
4. Call `risk_stress_replay` (CLI `riskdesk replay --input PATH`).
5. If it refuses, the message names the missing series or date. Ask for
   that one thing; do not shift the window to dates that happen to exist
   without telling the user.
6. Save the result and run `scripts/check_artifact.py RESULT.json`.

## Before reporting

- `degraded` first; a proxy makes the result degraded.
- Window, measure, currency, as-of and the price source.
- Loss, stressed NAV, then contributions if asked.
- For peak-to-trough, say the falls need not coincide and are gains for
  shorts.
- No probability is attached to a replayed window.
