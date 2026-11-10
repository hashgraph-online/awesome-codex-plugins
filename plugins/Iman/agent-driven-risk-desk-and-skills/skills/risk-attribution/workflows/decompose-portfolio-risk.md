# Workflow: decompose a portfolio's risk

Run in order. Each step reads only what the user supplied or what an earlier
step returned.

1. Collect the inputs. You need the positions (signed market values in one
   base currency, linear only), a return history with one column per held
   asset, oldest row first, and the horizon one row spans. For factors, you
   also need factor returns on the same rows. Ask for anything missing. Do
   not fill gaps, do not drop rows, and do not convert currencies yourself.
2. Covariance: call `risk_covariance`. Choose `sample` unless the user
   asks for recency weighting (`ewma`, with the decay the user states) or the
   history is short against the number of assets (`ledoit_wolf`). If
   `positive_definite` is false, report it, and re-run with `ledoit_wolf`
   when the user agrees.
3. Normal VaR and ES: pass the returned `assets` and `covariance`, with the
   positions, confidence and the same `horizon_days`, to `risk_var_attribution`.
   Put the covariance result's `input_sha256` in `source`, so the link can
   be traced.
4. Historical ES: call `risk_es_attribution` with the same positions and
   history. This step needs no covariance.
5. Factors, if asked: call `risk_factor_exposure`.
6. Save each result and run `scripts/check_artifact.py` on it. FAIL means
   do not report the numbers. Say what failed.

## Before reporting

- Give `degraded` and its reason first, for every result that has one.
- State currency, horizon and as-of date. Name the method on every number:
  normal VaR is not historical VaR.
- Rank positions by component, and show the sign. Negative is a hedge.
- Give incremental VaR separately from components, and say that it does
  not sum to the total.
- For factors, quote the systematic share and the largest factor exposures.
  Say that this is in sample.
- Do not compute any figure yourself that the result does not contain.
