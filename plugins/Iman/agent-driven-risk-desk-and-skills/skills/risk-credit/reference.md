# Reference: portfolio credit VaR

Loaded only when a number has to be interpreted or defended.

Source read from bis.org on 4 November 2026: CRE31, IRB approach: risk weight functions,
version effective 1 January 2022 (chapter PDF), and CRE99, Application guidance, version
effective 1 January 2023 (chapter PDF), Table 1.

## Notation

EAD_i exposure, PD_i probability of default over the horizon, LGD_i loss given default, R_i
asset correlation, a_i factor loading, q confidence, N the standard normal distribution
function, G its inverse (CRE31.2 uses the same N and G), Z the systematic factor, e_i the
idiosyncratic factor, both independent standard normal.

## One-factor default model

Obligor i defaults when its asset value X_i falls below G(PD_i):

    X_i = sqrt(R_i) Z + sqrt(1 - R_i) e_i      (ASRF, R_i = a_i^2)
    X_i = a_i Z + sqrt(1 - a_i^2) e_i          (copula)

Conditional on the factor, defaults are independent with probability

    p_i(Z) = N[(G(PD_i) - sqrt(R_i) Z) / sqrt(1 - R_i)]

which falls as Z rises.

Portfolio loss is L = sum_i EAD_i * LGD_i * 1{default_i}. Expected loss is
EL = sum_i EAD_i * LGD_i * PD_i.

## ASRF (Vasicek) loss quantile

For an infinitely granular portfolio, L converges to its conditional mean
L(Z) = sum_i EAD_i * LGD_i * p_i(Z). Every p_i(Z) falls as Z rises, so L(Z) falls as Z rises,
and the q quantile of L is L evaluated at the (1 - q) quantile of Z, that is at Z = -G(q):

    VaR_q = sum_i EAD_i * LGD_i * N[(G(PD_i) + sqrt(R_i) G(q)) / sqrt(1 - R_i)]

The obligor terms add up exactly, and each one is reported as a contribution. The bracketed
default rate is the term inside the CRE31.5 capital requirement,
N[G(PD) / sqrt(1 - R) + sqrt(R / (1 - R)) G(0.999)], at a general q. CRE31.5 then computes
K = [LGD * N[...] - PD * LGD] * (1 + (M - 2.5) b) / (1 - 1.5 b), so unexpected loss as reported
here is K * EAD before the maturity adjustment.

Checks in the tests:

- CRE99 Table 1, corporate exposures, LGD 40%, turnover EUR 50 million, M = 2.5: all 18
  published risk weights from PD 0.05% to 20% are reproduced within 0.005 percentage points
  (the table is rounded to 0.01) as RW = 12.5 * (UL / EAD) / (1 - 1.5 b) * 100, with the
  CRE31.5 corporate correlation R = 0.12 w + 0.24 (1 - w), w = (1 - e^(-50 PD)) / (1 - e^(-50)),
  and b = (0.11852 - 0.05478 ln PD)^2. Those supervisory formulas appear only in the test as
  the published reference; the tool takes R as an input.
- A three-obligor heterogeneous portfolio: the quantile matches one million samples of L(Z)
  within 1%, which checks the additivity argument above without relying on it.

## Copula Monte Carlo

Each scenario draws Z and every e_i, flags defaults where X_i < G(PD_i), and sums
EAD_i * LGD_i over defaulted obligors. Draws come from NumPy's `default_rng(seed)`, in chunks
of at most two million normals, so the same request reproduces the same numbers.

VaR and Expected Shortfall come from the desk's historical tail calculation (`risk_tail`,
skfolio) applied to the simulated losses as P&L. VaR is the empirical order statistic and ES
integrates fractional tail mass, exactly as for market VaR. Unexpected loss is VaR minus the
simulated expected loss. `analytic_expected_loss` is the exact sum_i EAD_i LGD_i PD_i for
comparison.

Checks in the tests:

- Exact finite pool: for a homogeneous pool of n names the number of defaults is binomial
  given Z, so its distribution is the binomial mixed over the normal factor, computed by
  400-point Gauss-Legendre quadrature on [-10, 10]. With n = 1,000, PD 1%, R 12%, LGD 45%,
  q = 99% and 200,000 scenarios, the simulated VaR is within two defaults of the exact VaR,
  ES within 2%, and the mean loss within four standard errors of n * PD * LGD.
- Convergence to Vasicek: the exact finite-pool VaR exceeds the ASRF VaR by a gap that falls
  from 100 to 1,000 to 5,000 names (measured on 4 November 2026: 33%, 2.8% and 0.5%). At 5,000
  names and 40,000 scenarios the simulated VaR is within 2% of the ASRF VaR (measured 0.9%).

## Not implemented

- Rating migration: it needs a user-supplied transition matrix and a revaluation per rating;
  none is accepted, so it is left out.
- Random LGD, several factors, IRB capital, PD and LGD floors, and the CRE31.7 multiplier.
