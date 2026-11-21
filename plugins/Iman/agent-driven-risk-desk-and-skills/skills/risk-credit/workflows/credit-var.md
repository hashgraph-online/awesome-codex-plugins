# Workflow: credit VaR for a loan or bond book

1. Collect, per obligor: id, exposure in one currency, PD over one stated horizon, LGD, and the
   correlation (ASRF) or factor loading (copula). Ask for any missing value. All PDs must be
   for the same horizon; that horizon is `horizon_days`.
2. Run `risk_credit_asrf` first. It is instant and gives the granular benchmark and the
   per-obligor contributions.
3. If the book is concentrated (a few names hold much of the exposure) or ES is wanted, run
   `risk_credit_copula` with the same obligors, loadings a_i = sqrt(R_i) for the same model,
   and enough scenarios that at least 20 fall in the tail: scenarios * (1 - confidence) >= 20,
   and preferably far more. A first run of 100,000 scenarios suits 99% to 99.9%.
4. If the copula result is degraded, rerun with more scenarios; do not report the degraded
   number as final.
5. Run `scripts/check_artifact.py RESULT.json` on each saved result.
6. Report as SKILL.md says: degraded first, then credit VaR with confidence, horizon and
   currency, then expected and unexpected loss, ES and the seed for the copula.
7. When the two disagree, the copula figure is the finite-portfolio one; the gap is the
   concentration the ASRF ignores. Do not average them.
