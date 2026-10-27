# Output contract

Size the reply to the question. Every reply opens with the answer. The cards below appear only when the question calls for them, and a card field that doesn't apply is left out rather than filled with a placeholder. Unknowns go into one "What I need from you" list. Prose states evidence and verdicts in plain words; the codes appear only inside cards and previews.

## Every reply

1. **The answer**, in the first paragraph: what to do or not do, and the main reason.
2. **The reasoning**, in prose, saying in plain words what each key claim rests on: your account data, Amazon's current rules, someone else's result, or a starting guess to test.
3. **What I need from you**: the missing facts, access, or decisions, each with why it matters. Budget, bid, and campaign choices are listed here as the user's to make, with your recommendation.
4. **Verdict**, in plain words (proceed to analysis, proceed to review, hold, or no-go), with a line on whether the evidence is only correlational and which writes wait for approval. Each pending write appears once, with its rollback.

## Shape A: a decision question

"Should we shift budget?", "Did this audience work?", "Is this agency claim right?"

Add the test or analysis that would settle it: the comparison, primary metric, guardrails, and how long until the data matures. No definition or action cards unless the user asked for a plan.

## Shape B: an audience plan or build

Add, in this order:

### Readiness

Only the checks still open that could change the plan, one line each, and where the plan stands (ready for analysis, ready to draft, ready for approval, or on hold). Name the checks, not the tool calls.

### Audience definition card

```yaml
draft_name: <naming convention from 05-audience-design.md>
purpose: <the decision this audience serves>
type: RULE_BASED | LOOKALIKE
include: <events, scope, and window>
exclude: <events, scope, and window>
lookback: <value, label, and the analysis it came from or will come from>
window_mode: ROLLING | FIXED          # pin event dates in the SQL either way
marketplace: <one per card>
asin_or_brand_scope: <value>
seed: <LOOKALIKE: definition, size bounds 500-500,000, seed exclusion plan>
expected_reach_tier: <LOOKALIKE: MOST_SIMILAR | SIMILAR | BALANCED | BROAD | MOST_BROAD>
estimated_size: <from the sizing companion, or "not yet sized">
refresh_rate_days: <chosen deliberately; the API default is 21>
activation_target: DSP | SPONSORED_DISPLAY | SP_BID_BOOST | SB_BID_BOOST | NONE
review_date: <date, plus what ends the audience: delete, or a rolling window passing the event>
```

### Draft SQL

The audience query and its sizing companion, adapted from a playbook in `07-playbooks.md` or a retrieved instructional query. Say which source it came from and whether it has passed a dry run on this instance. The run itself is listed under pending writes.

### Action card, one per change

```yaml
change: <one audience, one bid adjustment, one exclusion, one lookalike, or one window/refresh change>
where: <campaign or line item>
current_value: <value>
proposed_value: <number, labeled HYPOTHESIS with its reason>
rollback_value: <recorded original>
existing_adjustments: <other bid adjustments on the campaign, so the effective bid is known>
baseline_window: <dates>
measurement_window: <dates, plus attribution lag>
holdout: <method, the strongest available>
primary_metric: <metric>
guardrails: <profit, frequency, spend, inventory>
stop_conditions: <conditions>
```

### Measurement plan

Baseline metrics, the one holdout design you recommend and why, the maturity date, lift reported as absolute and relative with sample sizes, and the review date with what happens then (keep, iterate, roll back, or retire).

## Shape C: the approval preview before a write

Show every value the write will use, then stop and wait for an explicit yes. SKILL.md → Guardrails defines the preview for `amc_*` writes. For audience writes it includes:

```yaml
write: <create audience | run sizing query | add audience to campaign | set bid adjustment | delete audience>
advertiser_id: <verified>
amc_instance_id: <verified>
names_reconciled: <account / profile / instance names>
marketplace: <value>
audience_name: <value>
sql: <full text>
time_window: <start and end, or relative window>
refresh_rate_days: <value>
destination: <DSP advertiser, or Sponsored Ads campaign and ad group>
rollback: <how this write is undone>
```

One preview covers one write, except that several read-only sizing runs may share one itemized preview.
