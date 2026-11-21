# Measurement and Experiments

Measurement exists to decide what to repeat, change, or stop. Do not optimize a
proxy that is disconnected from the account objective.

## Objective map

| Objective | Primary measure candidates | Diagnostics |
|---|---|---|
| Awareness | accounts reached in target cohort | view distribution, non-follower reach, profile visits |
| Qualified growth | follows attributed to post / reach | profile visits, audience fit, unfollows when available |
| Education | saves / reach | carousel completion, average watch time, qualified questions |
| Distribution | shares / reach | sends, reposts, new-audience reach |
| Conversation | qualified comments or DMs / reach | objection themes, response burden |
| Leads | attributed leads / reach | profile actions, site taps, DM keyword starts |
| Sales | attributed sales or revenue / reach | checkout starts, lead quality, offer and margin |
| Search discovery | search-sourced views / total views | search terms in caption and on-screen text, profile visits from search |

The table supplies candidates, not mandatory metrics. Use only measures the
current account exposes and the user is authorized to access.

## Experiment card

```text
Question:
Comparable baseline: format / date range / n / median
Hypothesis:
One variable changed:
Constants held:
Primary metric:
Diagnostics:
Guardrail:
Minimum review checkpoint:
Decision rule: repeat | iterate | stop
Confounders:
```

Set the review checkpoint from the account's normal reach curve and publishing
cadence. Do not use a universal 24-hour, seven-day, or 10,000-view threshold.

## Readback table

```text
Post ID | format | pillar | hook family | test variable | published at
Reach | views | average watch time | saves | shares | comments | follows
Profile actions | site taps | DMs | leads | sales | source captured at
Comparable baseline | result | next decision
```

## Diagnosis rules

- High views plus low average watch time: inspect whether starts or replays
  inflate views; test the opening and message-format fit.
- Adequate retention plus low follows: inspect audience fit, profile promise,
  series continuity, and follow CTA.
- Saves without site actions: treat the post as an assist unless education is
  the primary objective.
- Shares with negative or off-target comments: inspect who is sharing and why;
  distribution is not automatically desirable.
- Site taps without leads: route to `suede-analytics` and
  `suede-site-alchemy`; do not blame the post before checking attribution and
  landing-page friction.
- Leads without sales: inspect lead quality, offer, pricing, follow-up, and
  attribution before changing content.

## Reporting

Always separate:

1. observed values;
2. computed rates and formulas;
3. comparable baseline;
4. experiment result;
5. inference and confidence;
6. the next smallest test.
