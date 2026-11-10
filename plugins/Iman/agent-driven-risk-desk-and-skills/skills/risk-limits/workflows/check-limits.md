# Workflow: check a book against its limits

1. Run the results the limits need, all with the same `as_of` and
   `currency`: `risk_exposure` for exposure, leverage and share limits;
   `risk_tail` for VaR and ES; `risk_stress` for named scenario losses.
2. Build the request: provenance, `limits`, and `results` holding those
   results unchanged under `exposure`, `tail`, `stress`. Do not edit or
   round the results; the check reads them as they are.
3. Call `risk_limits` (or `riskdesk limits --input PATH`).
4. Run `python3 scripts/check_artifact.py RESULT.json`. Report FAIL as a
   defect, not as a result.
5. Report in the order given in SKILL.md: degraded first, then overall
   status and counts, then breaches and warnings, then not_evaluated
   limits with their reasons.

## Before reporting

If any limit is not_evaluated, say which and why; overall cannot be within.
If a result's as-of date differs, give both dates.
Quote VaR and ES limits with their confidence and horizon.
