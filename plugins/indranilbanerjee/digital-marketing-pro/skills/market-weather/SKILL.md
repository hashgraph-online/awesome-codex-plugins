---
name: market-weather
description: "Assess current market conditions. Use when: checking economic indicators, cultural moments, or competitive activity."
---

# /digital-marketing-pro:market-weather

## Purpose

Generate a Marketing Weather Report — a single-page assessment combining all external signals that affect marketing effectiveness right now. Score current conditions for marketing action (green, yellow, or red) across five dimensions: economic climate, cultural moments, industry and competitive activity, platform changes, and regulatory updates. This command gives marketers a quick go/no-go signal before launching campaigns, adjusting budgets, or making timing decisions. Instead of checking multiple dashboards and news sources, get one consolidated view of whether conditions favor aggressive marketing action, cautious optimization, or defensive positioning. Reports are time-horizon-aware — this week's weather may differ from this quarter's forecast.

## Input Required

The user must provide (or will be prompted for):

- **Industry context (optional)**: Specific industry or vertical to focus the assessment on. If omitted, uses the active brand profile's industry classification. Industry context determines which economic indicators, regulatory developments, and competitive signals are most relevant
- **Time horizon**: The planning window for the assessment — `this-week` (tactical, what to act on now), `this-month` (operational, what to prepare for), or `this-quarter` (strategic, what to plan around). Each horizon adjusts the signal weighting and recommendation specificity. If omitted, defaults to `this-month`
- **Specific concerns to check (optional)**: Particular areas the user wants assessed — e.g., "any platform algorithm changes this week", "regulatory developments in data privacy", "competitor product launches", or "economic indicators affecting ad spend". These get priority attention in the report alongside the standard five-dimension scan

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply industry classification, target markets, competitive set, and channel mix to focus the weather assessment on relevant signals. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Generate weather report**: Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/macro-signal-tracker.py" --brand {slug} --action weather-report` to pull the latest recorded signal data across all five dimensions. (The script reads the brand's industry from its profile; the time horizon is applied when you weight and phrase the recommendations, not as a script flag — there are no `--industry`/`--horizon` flags.) If specific concerns were provided, prioritize them in the analysis.
3. **Review and categorize signals**: Review all signals recorded in the last 30 days. Categorize each by dimension — economic (consumer confidence, ad market pricing, industry spending trends), cultural (holidays, awareness months, viral moments, social movements), industry (competitor launches, M&A, market shifts), platform (algorithm updates, new ad formats, policy changes, outages), and regulatory (privacy laws, advertising regulations, compliance deadlines). Weight recency and impact severity.
4. **Score each category and overall conditions**: Assign a condition score to each dimension — green (favorable for marketing action, no headwinds), yellow (proceed with caution, monitor specific risks, adjust tactics), or red (significant headwinds, delay non-essential launches, shift to defensive positioning). Calculate an overall marketing weather score as the weighted combination of all five dimensions, with weights adjusted by the brand's channel mix and market exposure.
5. **Generate recommendations based on conditions**: For each dimension and overall, provide specific actionable recommendations tied to the time horizon. Green conditions get acceleration recommendations. Yellow conditions get risk-mitigation tactics. Red conditions get defensive playbooks. All recommendations reference the specific signals driving the score.
6. **Highlight upcoming events and dates**: Surface events, dates, and deadlines within the time horizon that require preparation — holiday campaigns, platform migration deadlines, regulatory compliance dates, competitor event dates, and cultural moments worth leveraging or avoiding.

## Output

A structured Marketing Weather Report containing:

- **Overall marketing weather condition**: Green, yellow, or red with a one-sentence summary — the executive-level go/no-go signal for marketing action in the current time horizon
- **Per-category conditions**: Individual green/yellow/red scores for economic climate, cultural moments, industry and competitive activity, platform changes, and regulatory updates — each with the top signal driving the score and a brief rationale
- **Top signals requiring attention**: The 3-5 most impactful signals across all dimensions, ranked by urgency and potential impact on the brand's marketing effectiveness — the signals that should inform this week's decisions regardless of the time horizon selected
- **Upcoming events calendar**: Events, dates, and deadlines within the time horizon that need preparation — with lead time estimates and recommended actions for each
- **Recommendations for the time horizon**: Specific tactical, operational, or strategic recommendations matched to the selected time horizon and current conditions — what to launch, what to pause, what to prepare, and what to monitor
- **Comparison to previous report**: If a prior weather report exists for this brand, show trend direction for each dimension — improving, stable, or declining — so the user can see whether conditions are getting better or worse

## Agents Used

- **market-intelligence** — Signal assessment across all five dimensions with severity and recency weighting, condition scoring methodology calibrated to brand industry and channel mix, time-horizon-aware recommendation generation, upcoming event identification with preparation timelines, and trend comparison against previous reports for directional context
