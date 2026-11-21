# Workflow: SBM FX delta and vega capital

1. Confirm the reporting currency. It goes in `currency`, and no sensitivity
   may be to it.
2. Collect FX delta sensitivities (MAR21.24) per currency and FX vega
   sensitivities (MAR21.25) per currency and option maturity. All are in the
   reporting currency. Map option maturities to 0.5, 1, 3, 5 or 10 years
   before calling; the tool refuses any other tenor rather than
   interpolating.
3. Ask whether the bank elects the MAR21.88 square-root-of-two reduction for
   specified pairs, and set `apply_specified_pair_reduction`. Do not assume
   either answer.
4. `frtb_sbm_fx` (see `examples/frtb_sbm_fx.json`).
5. Run `scripts/check_artifact.py` on the saved result.

## Before reporting

If `degraded` is true, say first that curvature is missing, so the charge is
understated for any option book. Then give `capital` and `binding_scenario`.
Show all three scenario totals. When buckets have opposite signs, the cross
term is negative, so the low correlation scenario gives the larger charge. Call it the FX
delta and vega SBM charge, not the standardised approach capital: other risk
classes, curvature, the default risk charge and the residual risk add-on are
not included.
