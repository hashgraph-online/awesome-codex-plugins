# Workflow: SA-CCR exposure at default for one netting set

1. Collect the netting set from the user: every trade's asset class, notional on the basis the
   class needs, market value, maturity, direction, and the class fields in SKILL.md. Ask for a
   missing field; do not fill one in. One request is one legally enforceable netting set
   (CRE52.1). Trades outside netting are each their own netting set.
2. Convert every amount to one currency before the request. The tool does no conversion.
3. Decide margined or unmargined. Margined means the counterparty posts variation margin to the
   bank (CRE52.2). For a margined set collect threshold, minimum transfer amount, NICA, the
   remargining period and the MPOR in business days. If the user's MPOR should be 20 days
   (over 5,000 trades, illiquid collateral, hard-to-replace trades, disputes; CRE52.51) or is a
   central counterparty floor (CRE54), they must supply that MPOR: the tool enforces only the
   CRE52.50 floor.
4. Apply collateral haircuts first; `collateral` is the haircut value of net collateral held.
5. Run `risk_saccr` (or `riskdesk saccr --input PATH`). Save the result as JSON.
6. Run `scripts/check_artifact.py RESULT.json`. Do not report a FAIL.
7. Report in the order SKILL.md gives: degraded first, then EAD with currency, RC, multiplier,
   PFE, add-ons by asset class, and the cap for a margined set.
8. Name what is outside the model if the book has it: basis or volatility trades, CDO tranches,
   nth-to-default, several margin agreements.

## Checks before reporting

- The add-on by asset class sums to `addon_aggregate`.
- A large negative `netting_set_value` with zero RC is expected to lower the multiplier.
- An option's `supervisory_delta` sign should match its direction: positive for a bought call
  or a sold put, negative for a sold call or a bought put.
