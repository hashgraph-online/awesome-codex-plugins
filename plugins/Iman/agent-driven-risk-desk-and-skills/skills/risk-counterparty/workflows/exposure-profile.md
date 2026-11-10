# Workflow: summarise an ORE exposure profile

1. Run the ORE project with `risk_xva` (skill risk-xva), or take a netting-set exposure report
   the user already has. The adapter keeps every report named `exposure_...`; the netting-set
   one is `exposure_nettingset_<id>`. Trade-level reports (`exposure_trade_...`) are refused.
2. Take that report's `rows` exactly as ORE wrote them. Do not rename, rescale or change the
   sign of any column.
3. Build the request: `as_of` and `currency` from the ORE run (the base currency), `source`
   naming the ORE run, `data_mode`, and `rows`.
4. Run `risk_exposure_profile` (or `riskdesk exposure-profile --input PATH`). Save the result.
5. Run `scripts/check_artifact.py RESULT.json`.
6. Report degraded first. If the grid has no date at one year, say that EPE and Effective EPE
   cover only `averaging_horizon_years`, and suggest adding a one-year date to the ORE grid.
7. Report Effective EPE, EPE, the horizon, and peak PFE with its time. Say that PFE is at the
   quantile set in the ORE configuration.
8. Do not present alpha times Effective EPE as an EAD: that is the internal model method and
   needs supervisory approval (CRE53.1, CRE53.11).
