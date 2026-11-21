# Workflow: IMA capital from ES cascades to RWA

Run in order. Each step's output feeds the next, and each is checked before
the next starts.

1. Gather the 10-day ES cascades at 97.5% for the portfolio and for each
   broad risk class with exposure. Each cascade is five values, for the
   reduced set in the stress period, the full set now and the reduced set now.
   Every class must use the portfolio-wide stress period (MAR33.15). If a
   cascade is missing, ask for it. Do not substitute zeros for a class that
   has exposure.
2. `frtb_imcc` (see `examples/frtb_imcc.json`). Read `degraded`, then
   `imcc`. Note any class whose `ratio` is below 1, because the floor raised
   it (`ratio_floored`).
3. `frtb_backtest` with `level: "bank"` over the last 250 days of bank-wide
   APL, HPL and 99% VaR. Report `exceptions_99` (APL and HPL separately),
   `zone` and `backtesting_multiplier`.
4. Collect the remaining inputs: the 60-day IMCC and SES averages (IMCC from
   step 2 on each day), latest and 12-week average DRC, the supervisor's
   qualitative add-on, each approved desk's SA and PLA zone, SA_G,A, C_U and
   SA for all desks. These come from the bank, not from this tool.
5. `frtb_ima_capital` with the step 3 count as
   `bankwide_backtesting_exceptions` (see `examples/frtb_ima_capital.json`).
6. Save the result and run `scripts/check_artifact.py` on it. Only an `OK`
   or `DEGRADED` verdict is reportable.

## Before reporting

State the degraded flag first, then `aggregate_capital` and `rwa` with the
currency and as-of date. Say which side of C_A's maximum bound it: the latest
IMCC plus SES, or m_c times the IMCC average plus the SES average. Name any
amber desk and the surcharge. Say that ES, SES, DRC and every SA figure were
supplied by the caller and were not checked here.
