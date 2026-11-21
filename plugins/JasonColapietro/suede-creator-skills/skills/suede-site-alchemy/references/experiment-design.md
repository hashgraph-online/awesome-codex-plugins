# Evidence-Grade CRO Experiment Design

Use this reference whenever a page recommendation is described as an A/B test,
experiment, expected lift, or revenue opportunity. The goal is a decision that
survives instrumentation, statistical, and business-quality checks.

## 1. Separate Evidence Types

Label every input:

- **Observed:** measured on the named product, population, metric, and date
  range.
- **Sourced prior:** external evidence with source, date, population, metric,
  and known comparability limits.
- **Hypothesis:** a proposed mechanism that has not been established here.
- **Scenario:** arithmetic using explicit assumptions. It is not a forecast.
- **Unknown:** unavailable or untrustworthy. Keep it unknown until measured.

Do not turn a heuristic into a benchmark, a benchmark into an expectation, or
an experiment result into a universal design rule.

## 2. Instrumentation Readiness

Before experiment design, write the funnel as events and denominators:

```text
eligible -> assigned -> exposed -> CTA start -> task complete -> qualified outcome
```

For each event, record:

- exact definition and counting unit;
- client/server source and timestamp behavior;
- deduplication and identity rules;
- consent, ad-blocking, bot, internal-traffic, and cross-device effects;
- validation query or dashboard;
- owner and last-verified timestamp.

Run an A/A test or equivalent invariant check when assignment, exposure, or a
new metric pipeline is unproven. If event definitions differ across variants,
repair measurement before reading performance.

## 3. Pre-Register the Decision

Complete `../assets/cro-hypothesis-ledger.csv` before launch. At minimum define:

1. Decision owner and decision date.
2. Eligible population and exclusion rules.
3. Randomization unit and why interference is acceptably low.
4. Control, treatment, allocation, and exposure event.
5. One primary decision metric with numerator, denominator, window, and unit.
6. Guardrails for harm: errors, latency, accessibility, refunds/cancellations,
   support contacts, downstream quality, or retention as relevant.
7. Data-quality metrics: assignment counts, exposure counts, missingness,
   event parity, and sample-ratio mismatch (SRM).
8. Smallest business-useful effect (MDE), significance level, power, sample
   requirement, planned duration, and analysis method.
9. Stopping rules for user harm, technical failure, and data-quality failure.
10. Ship, iterate, or reject rule, including operational cost and reversibility.

Do not choose the MDE after seeing results. MDE is a design threshold: the
smallest effect the team needs the experiment to detect with the selected
power. It is not an expected treatment effect.

## 4. Sample Size and Duration

Calculate sample size with the current baseline, chosen metric model, MDE,
significance level, power, allocation, and planned analysis. Record the tool or
formula used. For clustered units, repeated observations, rare events, or
ratio metrics, use an analysis that matches the data-generating process.

Duration must account for:

- expected eligible and exposed traffic, not total sessions;
- full business cycles and known seasonality;
- delayed outcomes and attribution windows;
- ramp time and operational monitoring;
- mutually exclusive tests or known interaction risks.

Do not promise a fixed two-week test. Do not stop when a conventional p-value
first crosses a threshold unless the pre-registered sequential design permits
that look. If traffic cannot support the MDE in a useful timeframe, simplify
the question, use stronger qualitative evidence, aggregate only when valid, or
state that the experiment is infeasible.

## 5. Assignment, Exposure, and SRM

- Assign with a stable unit that matches the decision: visitor, signed-in
  account, organization, device, session, or another justified unit.
- Analyze eligible assigned units or exposed units according to the
  pre-registered estimand. Do not switch silently.
- Bind exposure to the treatment actually rendered, not merely route entry.
- Keep variant logic and event names symmetric.
- Check allocation and SRM before interpreting treatment effects.

SRM means observed allocation materially disagrees with expected allocation.
It can indicate assignment, eligibility, logging, bot, redirect, caching, or
delivery defects. Treat unresolved SRM as a data-quality block, not a result to
explain away.

## 6. Metrics and Guardrails

Prefer a primary metric close enough to respond but deep enough to represent
the decision. A CTA click can be diagnostic while qualified completion,
retention, refund, or revenue quality determines whether the change helped.

Metric contract:

```text
name:
population and unit:
numerator:
denominator:
attribution window:
direction of improvement:
known failure modes:
```

Use guardrails to prevent local optimization. Examples include page/task
errors, abandonment, performance, accessibility failures, support contacts,
low-quality leads, refund/cancellation, spam/abuse, and downstream retention.
Pick only those relevant to the decision, but pre-register them.

## 7. Multiple Tests, Segments, and Peeking

- Name the single primary metric. Label secondary metrics exploratory unless
  the plan controls the family of decisions.
- Pre-specify segments only where a mechanism and adequate power exist. Do not
  mine many segments and present the largest difference as confirmed.
- Record concurrent experiments and possible interactions.
- Use a pre-selected fixed-horizon, sequential, Bayesian, or other valid
  analysis plan. Do not mix stopping and interpretation rules after seeing the
  data.
- If accounts, teams, inventory, creators, or network interactions can expose
  one unit to both variants, randomize at the shared boundary or use a justified
  cluster/switchback design. Record interference and carryover risks.
- Pre-register any variance reduction (for example, a pre-treatment covariate
  or CUPED-style adjustment). Never use a post-treatment variable as a
  covariate merely because it improves significance.
- Distinguish novelty/learning effects from durable behavior when a design
  change is unfamiliar or repeated use matters.

## 8. Readout

Report:

- enrollment and exposure dates;
- assigned/exposed counts and exclusions by arm;
- SRM and event-health results;
- primary effect in absolute and relative terms;
- uncertainty interval and the pre-registered decision threshold;
- guardrail effects and missing/delayed outcomes;
- operational cost, risks, and external-validity limits;
- decision: ship, staged rollout, iterate/retest, reject, or inconclusive.

"Not statistically significant" does not prove no effect. "Statistically
significant" does not prove the effect is material, durable, causal for an
unplanned segment, or worth shipping. Interpret the estimate, uncertainty,
MDE, harms, and product economics together.

After shipping, use a staged rollout when risk warrants it and monitor the same
primary/guardrail metrics. A controlled result from one population and period
does not automatically generalize to every channel, device, geography, or
season.

## 9. Source and Verification Baseline

Verified 2026-07-19. Recheck platform behavior and standards when a decision
depends on them.

- Google Analytics experiment measurement overview:
  <https://support.google.com/analytics/answer/13468470>
- Microsoft Experimentation Platform guidance on SRM and alerting:
  <https://www.microsoft.com/en-us/research/articles/alerting-in-microsofts-experimentation-platform-exp/>
- WCAG 2.2 target size minimum (24 CSS pixels or listed exceptions):
  <https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html>
- WCAG enhanced target size (44 CSS pixels, AAA):
  <https://www.w3.org/WAI/WCAG22/Understanding/target-size-enhanced.html>

These sources support measurement and accessibility mechanics. They do not
supply a universal expected conversion uplift for a design change.
