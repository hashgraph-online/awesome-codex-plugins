---
name: churn-risk
description: "Assess customer churn risk. Use when: churn scoring, at-risk segment identification, intervention playbook generation."
---

# /digital-marketing-pro:churn-risk

## Purpose

Assess churn risk across customer segments and generate intervention strategies. Score segments using behavioral signals — email engagement decline, purchase frequency drops, login pattern changes, support ticket escalations — to categorize each segment into risk tiers and produce actionable intervention playbooks. This command bridges the gap between knowing customers are churning and knowing what to do about it. Instead of reactive "win-back" campaigns after customers have already left, it identifies at-risk segments early enough to intervene while the relationship is still recoverable. Each intervention playbook includes specific actions, timing windows, channel recommendations, and messaging approaches calibrated to the risk tier and customer value.

## Input Required

The user must provide (or will be prompted for):

- **Customer segments to score**: The segments to evaluate — can be predefined CRM segments (e.g., "Enterprise accounts," "Monthly subscribers," "First-time buyers") or behavioral cohorts (e.g., "Users who haven't purchased in 60 days," "Users with declining email opens"). Each segment should include available behavioral signals: email engagement trends (open rate, click rate, unsubscribe rate over time), purchase frequency and recency, login or product usage patterns, support ticket volume and sentiment, and any other engagement indicators tracked in the CRM
- **CRM data source**: Which CRM system holds the customer data — Salesforce, HubSpot, or another connected CRM MCP. The command will pull behavioral data directly from the CRM if connected, or the user can provide exported data
- **Intervention budget (optional)**: Total budget available for retention interventions — used to prioritize which segments and actions to focus on based on LTV-at-risk versus intervention cost. If not provided, all recommendations are generated without budget filtering
- **Lookback period (optional)**: How far back to analyze behavioral trends — defaults to 90 days. Shorter windows catch rapid deterioration, longer windows identify slow-burn churn patterns
- **Custom churn signals (optional)**: Brand-specific behavioral indicators beyond the defaults — e.g., "stopped using feature X," "downgraded plan tier," "removed payment method," "decreased order size" — that have historically preceded churn for this brand

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply customer lifecycle data, historical churn rates, known retention patterns, and industry benchmarks. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load any communication frequency limits or channel restrictions that constrain intervention options. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with industry defaults.
2. **Gather customer behavioral data**: Connect to the CRM MCP (Salesforce or HubSpot) and pull behavioral signal data for each segment — email engagement metrics over the lookback period, purchase history with frequency and recency calculations, product usage or login patterns, support interactions with sentiment indicators, and any custom churn signals the user specified. If CRM MCP is not connected, prompt the user to provide exported segment data or configure the integration.
3. **Score each segment for churn risk**: Execute `python "${CLAUDE_PLUGIN_ROOT}/scripts/churn-predictor.py" --brand {slug} --action score-segment --segment-name {name} --signals '{...behavioral signals...}'` with the behavioral signal data. The scoring model applies weighted signals — recent engagement decline is weighted more heavily than historical patterns, and signals are combined using a composite risk score. Each signal contributes based on its predictive strength: purchase recency (highest weight), engagement trend direction and velocity, support sentiment trajectory, and usage pattern breaks. Scores are normalized to 0-100 for comparability across segments.
4. **Categorize into risk tiers**: Map composite scores to four risk tiers — Low (0-25, stable engagement, no intervention needed beyond standard nurture), Medium (26-50, early warning signals present, proactive engagement recommended), High (51-75, multiple deteriorating signals, targeted intervention required within 2 weeks), and Critical (76-100, imminent churn risk, immediate high-touch intervention needed within 48 hours). **These cutoffs are fixed heuristic bands, not learned from your data** — the script computes the 0-100 score and these bands map score→tier. Recalibrate the band edges against your own realized churn before treating a tier as predictive; apply brand-specific thresholds where historical data suggests different cutoffs.
5. **Generate intervention playbook per tier**: For each risk tier with active segments, create a specific intervention playbook — the actions to take (personalized outreach, special offer, product education, account review, executive touch), timing window (how quickly to act and how long the intervention sequence runs), channels to use (email, phone, in-app, direct mail based on segment preferences and tier urgency), messaging approach (tone, value proposition emphasis, urgency level), and escalation path if the initial intervention doesn't shift engagement within the defined window.
6. **Calculate LTV at risk**: For each segment, estimate the lifetime value at risk if churn occurs — based on segment average LTV, segment size, and churn probability from the risk score. Aggregate to show total LTV at risk across all segments and per tier. This quantifies the business case for intervention investment.
7. **Prioritize interventions by LTV impact**: Rank all interventions by the ratio of LTV-at-risk to intervention cost — high-value segments in Critical and High tiers that can be retained with relatively low-cost interventions rank highest. If the user provided an intervention budget, apply it as a constraint and show which interventions fit within budget and which require additional investment, ordered by expected retention ROI.

## Output

A comprehensive churn risk assessment containing:

- **Churn risk scorecard**: All segments ranked by composite risk score — showing segment name, size, risk score (0-100), risk tier (Low/Medium/High/Critical), primary churn signals driving the score, and trend direction (improving, stable, or deteriorating)
- **Risk tier distribution**: Summary view showing how many customers and what percentage of total base fall into each tier — with comparison to industry benchmarks and the brand's historical distribution if available
- **Contributing factors per segment**: For each scored segment, the specific behavioral signals driving the risk assessment — which signals are deteriorating, how fast, and how they compare to the segment's historical baseline and to healthy-segment benchmarks
- **Intervention playbook per tier**: Detailed action plans for Medium, High, and Critical tiers — each with specific actions (what to do), timing (when to act and sequence duration), channels (where to reach them), messaging framework (what to say and how to say it), success metrics (what improvement looks like), and escalation triggers (when to escalate to the next intensity level)
- **LTV at risk calculation**: Total lifetime value at risk across all segments, broken down by tier — quantifying the business impact of inaction and the maximum justifiable investment in retention for each tier
- **ROI estimate for intervention programs**: Projected retention lift and revenue saved per intervention, based on industry retention benchmarks and the brand's historical win-back rates — showing expected ROI for each playbook to justify budget allocation

## Agents Used

- **marketing-scientist** — Churn scoring model design with weighted behavioral signal analysis, composite risk score calculation and tier threshold calibration, LTV-at-risk estimation using segment value and churn probability, intervention prioritization by retention ROI, and statistical validation of signal predictive strength against historical churn outcomes
- **crm-manager** — CRM data extraction from Salesforce or HubSpot via connected MCP servers, customer segment definition and behavioral data structuring, engagement metric aggregation over lookback periods, and data quality validation to ensure scoring inputs are complete and reliable
