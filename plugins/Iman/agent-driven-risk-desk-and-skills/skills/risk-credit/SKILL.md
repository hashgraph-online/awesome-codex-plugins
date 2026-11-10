---
name: risk-credit
description: Calculate portfolio credit VaR from obligor exposure, PD and LGD, either with the Vasicek asymptotic single risk factor quantile (the model behind the Basel IRB formula, CRE31) or with a seeded default-mode one-factor Gaussian copula Monte Carlo for a finite portfolio, giving expected loss, unexpected loss, credit VaR and Expected Shortfall. Use for default loss on a loan or bond book. Not for counterparty exposure (use risk-counterparty), not for market VaR (use risk-tail), not for IRB capital or risk weights, and not for rating migration.
---

# Risk Credit

Two tools, both read-only.

- `risk_credit_asrf`: the Vasicek asymptotic single risk factor loss quantile. Fast and exact
  for an infinitely granular portfolio; it ignores name concentration. CLI:
  `riskdesk credit-asrf --input PATH`.
- `risk_credit_copula`: a seeded Monte Carlo of the same one-factor model for the actual,
  finite list of obligors. It captures concentration and gives Expected Shortfall. CLI:
  `riskdesk credit-copula --input PATH`.

Examples: `examples/credit_asrf.json` and `examples/credit_copula.json` (one six-obligor book).

## The contract, in short

Both take `as_of`, `currency`, `source`, `data_mode`, `confidence` (strictly between 0 and 1),
`horizon_days` (the horizon over which every PD applies) and `obligors`, each with a unique
`id`, positive `exposure` (EAD in the request currency), `pd` (strictly between 0 and 1) and
`lgd` (0 to 1).

- ASRF obligors add `correlation` R (strictly between 0 and 1), the asset correlation with the
  single factor.
- Copula obligors add `factor_loading` a (strictly between -1 and 1). The pairwise asset
  correlation is a_i * a_j, so R = a^2 for a homogeneous pool. The request adds `scenarios`
  (1,000 to 1,000,000) and `seed` (non-negative integer). Scenarios times obligors may not
  exceed 200,000,000.

PD, LGD, correlation and loadings are inputs. The tools do not estimate them, and you must not
invent them. A supervisory correlation (the CRE31.5 corporate formula, for example) may be used
only if the user asks for it; say so when you do.

## What to report first

1. `degraded` and `degraded_reason`. For the copula, degraded means fewer than 20 scenarios of
   tail probability mass: raise `scenarios`.
2. `credit_var` at `confidence` over `horizon_days`, with currency.
3. `expected_loss`, `unexpected_loss` (credit VaR minus expected loss), and for the copula
   `expected_shortfall`, `scenarios` and `seed`.
4. For the ASRF, the largest `contributions`. They add up to the credit VaR.

## Sign conventions

Loss is positive. Credit VaR and Expected Shortfall are losses at and beyond the quantile.
Unexpected loss here is credit VaR minus expected loss, the quantity the IRB formula capitalises
before its maturity adjustment. It is not the standard deviation of loss, which the copula
reports separately as `loss_standard_deviation`.

## What not to claim

- Neither tool gives IRB capital or a risk weight. They apply no maturity adjustment, no
  CRE31.7 correlation multiplier and no PD or LGD floor.
- The ASRF result assumes infinite granularity. For a concentrated book it understates the
  loss quantile; the copula shows by how much.
- The copula result carries Monte Carlo error. Quote the seed and scenario count with it.
- Default mode only. Rating migration and spread loss are not modelled. LGD is fixed, not
  random. There is one systematic factor, so sector concentration is not captured beyond what
  the loadings express.
- A loss quantile is a model output, not a forecast that has been backtested.

## Going deeper

- `reference.md`: the formulas, the derivation of quantile additivity, the CRE31.5 source,
  and the published and exact checks the tests use.
- `workflows/credit-var.md`: which tool to run and in what order.
- `scripts/check_artifact.py RESULT.json`: one-line verdict on a saved result.
