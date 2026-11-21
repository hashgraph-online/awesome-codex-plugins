# Workflow: desk eligibility (PLA test and desk backtesting)

For one trading desk, over the most recent 250 trading days, oldest first.

1. Check there are exactly 250 days of RTPL and HPL. The PLA test refuses
   gaps. If a day is missing, report that rather than filling it in.
2. `frtb_pla` (see `examples/frtb_pla.json`). Report `zone`, `spearman` and
   `ks`. KS is a multiple of 0.004; `ks_count` is the integer behind it.
3. `frtb_backtest` with `level: "desk"`, using APL, HPL, 99% VaR and 97.5%
   VaR (see `examples/frtb_backtest.json`). Missing days may be null, and
   each counts as an exception.
4. Combine the two under MAR32.19 and MAR32.43:
   - PLA red, or `passes` false: the desk is capitalised under the
     standardised approach.
   - PLA amber and `passes` true: the desk stays on the IMA and adds to the
     MAR33.45 capital surcharge.
   - PLA green and `passes` true: the desk is eligible.
5. Run `scripts/check_artifact.py` on both saved results.

## Before reporting

Give APL and HPL exception counts separately, then the overall count (the
greater of the two) at each confidence level. Say that the zone is this
quarter's test only: returning to green from amber or red also needs 12
months of satisfactory backtesting (MAR32.43, MAR32.44), which this tool
does not track. Say that no exception was disregarded as NMRF-driven
(MAR32.6).
