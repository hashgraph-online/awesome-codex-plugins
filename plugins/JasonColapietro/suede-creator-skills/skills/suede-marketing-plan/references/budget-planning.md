# Budget Planning: Traceable Scenario Methods

Marketing budgets need dated inputs, explicit assumptions, accountable approval,
and downside stops. This reference helps build scenarios; it does not provide
financial advice, predict revenue, or prescribe spend from company stage.

Before calculating anything, record the source and as-of date for:

- cash, runway, and approved burn;
- gross margin, ARPC, and retention;
- blended CAC by comparable cohort;
- sales, onboarding, support, and channel capacity;
- committed contracts, payment timing, and cancellation terms.

If an input is missing, show a range and label it `unverified assumption`.
Have the accountable finance owner approve the assumptions, maximum spend,
review date, and stop conditions before any allocation becomes operational.

## Method 1: Capacity-Based Scenario

**Direction:** approved capacity → outcome range.

Start from the amount the accountable owner has approved within runway and burn
constraints. Model what that capacity could test using measured CAC and funnel
ranges. Do not infer a budget from ARR percentage, funding stage, or a generic
industry benchmark.

### Required inputs

- maximum approved spend and payment schedule;
- downside limit and runway floor;
- measured blended CAC range, cohort, and date;
- funnel and delivery capacity;
- gross-margin and retention ranges;
- review cadence and pause conditions.

Produce low, base, and high cases. For every case, show which assumption creates
the difference. A model that exceeds operational capacity is infeasible even if
the arithmetic works.

## Method 2: Goal-Based Sensitivity Model

**Direction:** target → implied capacity and spend.

Use this when an accountable owner has already set a target and wants to inspect
what it would require. With sourced inputs:

```text
Scenario spend =
  (New ARR / (ARPC × 12) / annual retention rate) × blended CAC
```

This is a sensitivity model, not a revenue forecast. Run it over sourced ranges,
then test whether sales, onboarding, support, gross margin, and channel capacity
can absorb the implied customer volume. If historical CAC or retention is
missing, the output is not execution-ready.

### Experiment capacity

Do not append a universal buffer percentage. Ask the owner to approve a bounded
test amount the company can lose without breaching runway. Name:

- the hypothesis and decision it informs;
- maximum cash exposure and any vendor commitment;
- success, pause, and stop conditions;
- owner and next review date.

## Calculating Blended CAC

Use a dated cohort and include all acquisition costs attributable to it:

- marketing salaries and loaded employment cost;
- advertising and sponsorship spend;
- content, creative, agency, and contractor cost;
- CRM, automation, analytics, and data tools;
- outbound labor when it serves acquisition.

Divide the included cost by acquired customers in the matching period and
cohort. Document exclusions. Do not substitute plan price for CAC or mix a
short cost window with a longer acquisition window.

## Scenario Evidence Table

| Input | Low | Base | High | Source | As of | Confidence |
|---|---:|---:|---:|---|---|---|
| Approved spend | | | | | | |
| Blended CAC | | | | | | |
| ARPC | | | | | | |
| Annual retention | | | | | | |
| Gross margin | | | | | | |
| Capacity ceiling | | | | | | |

Every number in the plan must trace to this table or be explicitly labeled as
an illustrative assumption.

## Reality Check

- Annual targets are decision scenarios, not promises.
- Month-by-month projections are illustrative unless backed by a mature,
  validated forecasting process.
- Update the model when actual CAC, retention, capacity, or cash changes.
- Never initiate spend, sign a contract, change billing, or publish a target
  without the accountable owner's explicit approval.

## How This Flows Into the Plan

| Section | What to include |
|---|---|
| **3 (Current state)** | Dated current spend, cash/runway boundary, owners, and known data gaps. |
| **8 (Revenue)** | The source-backed scenario evidence table and sensitivity range. |
| **10 (12-month outlook)** | Low/base/high scenarios, capacity checks, downside stops, and approval state. |
| **11 (Ops stack)** | Approved allocation by workflow and owner; no stage-derived defaults. |
| **13 (Open decisions)** | Missing or contested inputs and the smallest test that resolves each one. |

Choose the method from evidence availability and the decision being made, not
from company stage.
