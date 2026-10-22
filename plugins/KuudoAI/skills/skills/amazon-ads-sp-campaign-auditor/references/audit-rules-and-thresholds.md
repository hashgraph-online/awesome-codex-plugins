# Sponsored Products portfolio audit rules

Apply these rules after confirming report grain and field meanings. Prefer thresholds supplied by the user, agency SOP, or brand operating plan. When no threshold exists, report the measurement descriptively and label any comparison as an illustrative review threshold.

## Campaign-grain dataset

Use `campaign.id` as the grouping key and retain `campaign.name` as its label.

- Sum additive metrics such as cost, sales, impressions, and clicks across the selected window.
- Do not sum a daily budget repeated on every campaign-day row as though it were spend.
- Preserve currency boundaries. Do not combine monetary values across currencies without an explicit conversion method.
- State how campaigns with missing IDs, duplicate IDs, or changing names were handled.

## Spend concentration

Sort campaigns by window cost and calculate:

`top-N share = cost of the N highest-cost campaigns / total portfolio cost`

Use the user's `N` and alert threshold when supplied. Otherwise show a compact distribution such as top-5 and top-10 share without declaring that concentration is inherently healthy or unhealthy. When total cost is zero, mark concentration `N/A`.

## Budget fill

Only compare spend with budget when the denominator represents the same time window:

- **Daily budget with campaign-day rows:** derive one budget amount per campaign-day, then sum those amounts across eligible days.
- **Constant daily-budget snapshot:** multiply by included eligible days only when the user accepts that approximation and no budget changes occurred.
- **Lifetime budget:** compare window spend only when the lifetime budget and analysis window are meaningfully aligned.
- **Unknown or changing budget history:** report spend and the observed budget values separately; mark utilization `N/A`.

Call the result a budget fill rate unless the user's organization defines another term. Budget is a cap, so low fill is a diagnostic signal rather than proof of a problem.

## Delivery gaps

Classify campaign-window observations, not permanent campaign health:

- **No delivery:** zero impressions in the selected window.
- **Visible without engagement:** impressions greater than zero and zero clicks.
- **Clicks without cost:** treat as a data-quality or metric-definition question before classifying.
- **Impressions and clicks without meaningful cost:** apply only a user-defined minimum-cost threshold.

Filter by active eligibility only when the data supports it. `campaign.deliveryStatus` is a proxy and may not establish historical enabled state for the entire window. Present targeting, bids, eligibility, inventory, budget, seasonality, and launch timing as hypotheses to investigate.

## Targeting mix

Use an explicit targeting-type field when the validated report exposes one. Campaign-name tokens are naming evidence only. Report observed counts and spend shares; do not prescribe an auto/manual ratio without the user's strategy, maturity, and coverage objectives.

## Naming and duplicates

For exact normalized-name groups:

1. trim leading and trailing whitespace;
2. lowercase;
3. treat runs of whitespace, hyphens, and underscores as one separator; and
4. collapse repeated separators.

Groups containing two or more campaigns are review candidates, not automatic consolidation candidates. Preserve campaign IDs so intentionally versioned or marketplace-specific campaigns remain distinguishable.

## Threshold reporting

Every flag must include:

- measured value and population;
- analysis window;
- formula or classification rule;
- threshold and its source; and
- material caveats.

If no authoritative threshold is available, report the value without a pass/fail label.
