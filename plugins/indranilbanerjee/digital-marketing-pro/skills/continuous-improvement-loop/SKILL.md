---
name: continuous-improvement-loop
description: "Run Part 12 — the continuous improvement loop. Aggregates market + operating signals into product/offering recommendations. Runs alongside live operations, not as a one-time activity."
user-invocable: true
triggers:
  - run the continuous improvement loop
  - run part 12
  - aggregate market and operating signals
  - feed back into product offering decisions
  - quarterly business review feed-back
  - product offering improvement recommendations
allowed-tools: Read Write Edit Bash Glob Grep
engagement-part: "12"
view-preference: both
---

# /digital-marketing-pro:continuous-improvement-loop — Part 12 Continuous Loop

Part 12 is the continuous improvement loop that runs alongside live operations from go-live onwards. It aggregates market signals and operating signals into recommendations that feed back into the brand's product, offering, and service decisions.

## Context efficiency

Heavy skill. **Grep before Read** any referenced file, then `Read` only matched ranges with `offset` + `limit`. List the brand's workspace at `~/.claude-marketing/brands/{slug}/` (or `$CLAUDE_PLUGIN_DATA/digital-marketing-pro/brands/{slug}/` when that env var is set) before opening files. On re-invocation mid-session, skip files already in context.

This is **not a one-time activity**. It runs perpetually once Part 11 is complete, with formal output at each Quarterly Business Review (QBR) and ad-hoc output when significant signals warrant.

## Why this exists

Without an explicit feedback loop, marketing operates on assumptions made months ago. Markets shift, customers evolve, competitors move, products are refined — but if these shifts do not flow back into the strategy, the engagement silently grows stale.

Part 12 closes the loop:

- Market signals → strategy refresh
- Operating signals → tactical optimisation
- Product / offering signals → recommendations to product / business teams

## The 4 Signal Sources

### Source 1: Quarterly Business Reviews

Every quarterly review (per [reporting-cadence.md](../context-engine/reporting-cadence.md)) generates structured signals:

- KPIs vs targets (which targets were missed; which were beaten; pattern across quarters?)
- Channel-mix performance (any channel consistently outperforming or underperforming the v2 plan?)
- Audience segment performance (any segment showing different behaviour than the personas predicted?)
- Competitive shifts (any competitor moves that materially change the landscape?)
- Strategy alignment audit (is what we are executing still what the v2 strategy says we should be executing?)

### Source 2: Customer Feedback Themes

Feedback from across customer touchpoints:

- Customer service tickets (volume by topic, sentiment trend)
- ORM (Online Reputation Management) — review sites, social mentions
- Sales team conversations (objections heard repeatedly, requests not yet met)
- Customer journey friction observations (where customers drop off, where they ask for help)
- Survey / NPS responses
- Customer interviews

### Source 3: Competitive Intelligence

From the ongoing competitor monitoring (existing `/digital-marketing-pro:competitor-monitor` skill):

- Product / offering shifts at competitors
- Pricing changes
- Positioning shifts (messaging, target audience)
- New entrant emergence
- Acquisitions / partnerships changing the competitive landscape

### Source 4: Team-Discovered Patterns

Insights from execution that the team surfaces:

- Campaigns that consistently underperform — may indicate product-market mismatches
- Audiences requesting features the product does not yet offer
- Conversion friction points that recur across many campaigns
- Channel performance patterns that suggest the buyer journey has shifted

## Cadence

Part 12 is active continuously, with structured outputs:

| Cadence | Trigger | Output |
|---------|---------|--------|
| **Daily / weekly** | Automated signal capture as part of normal operations | Signals logged to `part-12-continuous-improvement/signals.jsonl` |
| **Monthly** | Monthly performance report | "Signals This Month" section in the report; logged to signals.jsonl |
| **Quarterly** | QBR | Structured Part 12 deliverable — see below |
| **Ad-hoc** | Significant signal (e.g., competitor product shift, sales team flagging recurring objection, KPI suddenly cratering) | Ad-hoc Part 12 brief produced within 1 week |

## The Quarterly Part 12 Deliverable

Each quarter, the continuous loop produces a structured deliverable for the brand business owners — not just marketing leadership.

### Structure

```markdown
---
document: part-12-quarterly-improvement-brief
engagement: {engagement-id}
quarter: {YYYY-Qn}
produced: {iso-timestamp}
audience: brand business leadership
---

# Quarterly Product & Offering Improvement Brief — {Quarter}

## Executive Summary

(3-5 sentences. The signals that matter most. The recommendations that follow.)

## Signal Aggregation

### Market signals
{Macro market shifts observed in the quarter}

### Customer signals
{Aggregated themes from customer feedback, ORM, sales conversations}

### Competitive signals
{Competitor moves that warrant response or reflection}

### Operating signals
{Patterns from execution — campaigns that under/outperformed; audience surprises; channel shifts}

## Implications

### For the brand strategy
{What in the v2 strategy looks confirmed by the quarter? What looks weakened? Anything that warrants v2.x update-back?}

### For the channel mix
{Any channel reweighting recommended?}

### For the product / offering
{This is the unique Part 12 contribution. What signals suggest the product or offering itself should change?}

## Recommendations

### To the marketing team
{Tactical adjustments — typically already in flight from monthly optimisation, but formalised here}

### To the product / business team
{The substantive Part 12 output — recommendations about product, offering, pricing, distribution that flow from marketing's vantage point}

### To leadership
{Strategic considerations that span functions}

## Triggers for v2.x Update-Back

(If any of the signals warrant a source-document version bump per the [update-back-rule.md](../context-engine/update-back-rule.md), list them here. The actual update-back happens via /digital-marketing-pro:engagement update-back.)

## Open Questions Raised This Quarter

(Things the data raises but cannot answer without further investigation.)
```

### Output location

```
engagements/{id}/part-12-continuous-improvement/quarterly-briefs/{YYYY-Qn}-quarterly-improvement-brief.md
```

Plus PDF export for distribution to leadership.

## The Ad-hoc Part 12 Brief

When a significant signal lands between QBRs, the loop produces an ad-hoc brief:

- A competitor launches a product that materially threatens the brand's positioning
- A regulatory change affects the addressable market
- A KPI suddenly drops outside the conservative scenario floor
- The sales team flags an objection that has appeared in 5+ deals in 2 weeks
- A piece of content unexpectedly goes viral, creating a unique moment

Ad-hoc briefs are short (1–3 pages), fast (within a week of the signal), and action-oriented (recommend a specific response).

Output location:
```
engagements/{id}/part-12-continuous-improvement/ad-hoc-briefs/{YYYY-MM-DD}-{slug}.md
```

## Production Process

### For Quarterly Part 12 deliverable

1. **Trigger:** the quarter ends; QBR is being prepared
2. **Read inputs:**
   - All monthly performance reports for the quarter
   - Signals logged in `signals.jsonl` for the quarter
   - Competitor monitoring outputs for the quarter
   - Customer feedback aggregations
   - Living Project Instruction File (current truth)
3. **Aggregate signals** into the four categories
4. **Synthesise implications** for strategy, channels, and product/offering
5. **Draft recommendations** for marketing, product/business, leadership
6. **Identify v2.x update-back triggers** if any
7. **Save** to `quarterly-briefs/`
8. **Update LIF** with quarter's verdict + recommendations
9. **Brief:** "Quarterly Improvement Brief produced. {N} signals aggregated. {N} recommendations. {N} update-back triggers identified — review and run /digital-marketing-pro:engagement update-back if approved."

### For ad-hoc Part 12 brief

1. **Trigger:** significant signal observed (logged with timestamp + source)
2. **Confirm significance** with engagement owner before producing the brief (avoid noise-driven ad-hoc briefs)
3. **Read targeted inputs** relevant to the specific signal
4. **Draft 1–3 page brief** with: signal, evidence, implications, recommended response, decision deadline
5. **Save** to `ad-hoc-briefs/`
6. **Distribute** per engagement's approval chain — typically marketing leadership + relevant product / business stakeholder

## Signal Capture Mechanism

The plugin captures signals continuously via:

- **Daily performance pulls** (when configured) flag anomalies
- **Monthly report production** captures "Insights & Learnings" entries
- **Competitor monitor** flags significant changes
- **Manual capture** — append the signal to `signals.jsonl` and record it in the Living Project Instruction File via `engagement-state.py lif-log-change` (there is no `engagement signal` subcommand; log the observation through `lif-log-change` so it enters the engagement's current-truth record)

All signals append to `signals.jsonl`:

```json
{"timestamp":"...","source":"customer_feedback","signal":"3 sales reps reported customers asking for X integration","severity":"medium"}
{"timestamp":"...","source":"competitor_monitor","signal":"Competitor Y launched freemium tier","severity":"high"}
{"timestamp":"...","source":"performance_anomaly","signal":"LinkedIn CPL dropped 35% week over week","severity":"high","investigate":true}
```

## Quality Discipline

1. **Signals are evidenced.** No vague "the team feels" — cite the source (which sales rep, which review platform, which monitoring run, which performance metric).
2. **Recommendations are specific.** "Marketing should optimise" is useless. "Reduce LinkedIn brand-awareness budget by 20%, redeploy to retargeting + email lifecycle" is actionable.
3. **Product / offering recommendations are framed as suggestions, not demands.** Marketing's vantage point is one of several inputs to product decisions.
4. **Update-back triggers are flagged but not auto-executed.** The `/digital-marketing-pro:engagement update-back` command is invoked separately after explicit approval.
5. **The audience for quarterly briefs is leadership, not marketing alone.** Write for that audience.

## Examples

### Example 1: Quarterly Part 12 brief

```
User: Q2 ended last week. Produce the quarterly improvement brief.

Skill response:
1. Grep first across the Q2 monthly reports (April, May, June) for the metrics you need; targeted Read with offset+limit on the matching lines — do not bulk-Read all three reports
2. Stream signals.jsonl line-by-line for Q2 (87 signals) — use head/tail/grep, not full Read
3. Grep the competitor monitor outputs (3 significant changes); targeted Read on the matching findings
4. Grep customer feedback aggregation (47 reviews + 12 sales-rep notes) for the themes you need; targeted Read on the matches
5. Aggregate into 4 signal categories
6. Identify implications:
   - Strategy: v2 positioning held up — confirmed by 12 customer testimonials echoing the positioning language
   - Channels: LinkedIn over-performed (CPL 30% below moderate scenario); Meta under-performed (CPL 40% above)
   - Product: 8 customer signals + 4 sales-rep notes suggest Feature X is consistently asked for
7. Recommendations:
   - Marketing: shift 25% of Meta budget to LinkedIn next quarter
   - Product: prioritise Feature X for Q3 roadmap (8 named customer asks)
   - Leadership: consider a freemium tier (competitor moved here; 5 sales-rep notes about price-sensitive prospects)
8. Identify update-back triggers: Core Doc 3.4 (channel mix) needs v2.1 to reflect LinkedIn's higher allocation
9. Save quarterly-briefs/2026-Q2-quarterly-improvement-brief.md (~8 pages)
10. Brief: "Q2 Improvement Brief produced. 1 update-back trigger flagged. Run /digital-marketing-pro:engagement update-back --doc 3.4 --reason 'Q2 evidence: LinkedIn outperformed; Meta underperformed; recommend channel reweight' after leadership approval."
```

### Example 2: Ad-hoc brief

```
User: Three customers in the past two weeks have switched to a competitor that just launched a freemium tier. We need a fast read on this.

Skill response:
1. Confirm significance with engagement owner ✓
2. Read inputs: the 3 churn cases, competitor monitor on the competitor's freemium launch, last 90 days of churn data for pattern check
3. Draft brief:
   - Signal: 3 churns to Competitor Y in 14 days; pattern check shows churn rate to Y up 4x vs prior 90 days
   - Evidence: churn interview notes (2 of 3 cited price); Competitor Y launched freemium 2026-04-15
   - Implications: short-term — defensive offer for at-risk segment; long-term — pricing strategy review warranted
   - Recommended response: (1) marketing — defensive offer to current at-risk customers within 7 days; (2) product/leadership — assess freemium response within 30 days
   - Decision deadline: response plan by 2026-05-12
4. Save ad-hoc-briefs/2026-05-05-competitor-y-freemium-response.md (2 pages)
5. Distribute per approval chain
```

## Related skills

- `engagement-workflow` — engagement orchestration
- Existing skills: `competitor-monitor`, `performance-monitor-agent`, `intelligence-curator`, `quality-assurance`

## Related references

- [reporting-cadence.md](../context-engine/reporting-cadence.md) — quarterly cadence context
- [update-back-rule.md](../context-engine/update-back-rule.md) — when Part 12 signals warrant source doc updates
- [engagement-flow-methodology.md](../context-engine/engagement-flow-methodology.md) — Part 12 in 12-Part flow
- [living-instruction-file-spec.md](../context-engine/living-instruction-file-spec.md) — where current-truth lives
