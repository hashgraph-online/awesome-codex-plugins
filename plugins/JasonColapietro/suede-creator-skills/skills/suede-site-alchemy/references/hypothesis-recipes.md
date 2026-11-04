# Suede AI Site Alchemy Skills: Hypothesis Recipes

## A/B Test Hypothesis Generator

For any CTA, headline, or section that needs improvement, generate a testable
hypothesis before rewriting. Read `references/experiment-design.md` and copy a
row into `assets/cro-hypothesis-ledger.csv` before launch.

Format:
```
For [eligible population], if we change [specific element] from [control] to
[treatment], we hypothesize [primary metric] will change because [mechanism].
Randomization unit: [visitor, account, session, or other justified unit].
Guardrails: [harm metrics]. Data quality: [SRM, exposure, event health].
MDE: [smallest business-useful effect, not expected uplift].
Decision rule: [pre-registered rule using estimate, uncertainty, guardrails,
and operational constraints].
```

Examples:

```
For eligible new visitors, if we change the hero CTA from "Learn more" to the
verified action-and-outcome label, we hypothesize qualified CTA starts will
change because the treatment reduces ambiguity.
Randomization unit: visitor ID. Guardrails: completion rate, error rate, and
support contacts. Data quality: allocation, SRM, exposure, and event parity.
MDE/sample/duration: calculate from the observed baseline, business threshold,
alpha, power, traffic, and the chosen analysis plan before launch.
```

After the Friction Audit, generate at most three hypotheses. Rank them by the
quality of the underlying evidence, size of the affected population, decision
value, effort, and risk. Do not rank by invented projected lift. A directional
result is inconclusive until assignment, exposure, SRM, metric health,
uncertainty, and guardrails have been checked.
