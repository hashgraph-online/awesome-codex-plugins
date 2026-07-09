---
name: roi-calculator
description: "Calculate marketing ROI. Use when: measuring campaign ROAS, CAC, CPL, LTV, or multi-channel attribution returns."
argument-hint: "[campaign-name]"
---

# /digital-marketing-pro:roi-calculator

## Purpose

Campaign ROI calculator with multi-touch attribution models. Produces a comprehensive ROI analysis across channels for budget justification, optimization recommendations, and executive reporting.

## Input Required

The user must provide (or will be prompted for):

- **Campaign spend by channel**: Dollar amounts invested per channel (paid search, paid social, email, SEO, content, events, etc.)
- **Conversions and revenue by channel**: Number of conversions and total revenue attributed to each channel
- **Time period**: The date range for the analysis (week, month, quarter, year)
- **Attribution model preference**: Last-touch, first-touch, linear, time-decay, or position-based (or compare all models)
- **Customer LTV**: Optional -- average customer lifetime value for long-term ROI projection
- **Industry vertical**: For benchmark comparison context
- **Conversion definitions**: What counts as a conversion (purchase, lead, signup, demo request, trial start, etc.)
- **Cost inputs beyond ad spend**: Optional -- agency fees, tool costs, creative production costs, team time

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply voice, compliance, industry context. Check `guidelines/_manifest.json` for restrictions, messaging, channel styles, voice-and-tone rules, and templates. If a template matching this command exists in `~/.claude-marketing/brands/{slug}/templates/`, apply its format. If no brand exists, prompt for `/digital-marketing-pro:brand-setup` or proceed with defaults.
2. **Check campaign history**: Run `python campaign-tracker.py --brand {slug} --action list-campaigns` to pull historical campaign data for trend comparison and period-over-period analysis.
3. **Run ROI calculator**: Execute `scripts/roi-calculator.py` with spend, revenue, and conversion data to compute channel-level and blended metrics.
4. **Calculate channel-level ROI and ROAS**: For each channel, compute ROI ((revenue - cost) / cost), ROAS (revenue / cost), CPA (cost / conversions), CPL (cost / leads), and contribution margin percentage.
5. **Apply attribution model**: Redistribute credit across channels using the selected attribution model. If the user wants a comparison, run all five models (last-touch, first-touch, linear, time-decay, position-based) and show how each model shifts credit between channels.
6. **Calculate blended ROI**: Aggregate all channels into a total campaign ROI, blended ROAS, and overall CPA. Factor in LTV if provided to project short-term vs long-term ROI and payback period.
7. **Compare against industry benchmarks**: Reference `skills/context-engine/industry-profiles.md` to contextualize whether channel performance is above, at, or below industry averages for the brand's vertical.
8. **Identify efficiency opportunities**: Flag channels with declining marginal returns, channels where increased spend could yield disproportionate gains, and channels where CPA exceeds LTV (unsustainable spend).
9. **Calculate payback period**: If LTV data is provided, compute the months to break even on customer acquisition cost per channel, identifying which channels pay back fastest and which require patience for long-term value.
10. **Model budget reallocation scenarios**: Generate 2-3 reallocation scenarios shifting budget from underperformers to high-performers, with projected impact on total ROI, total conversions, and blended CPA.
11. **Log results to campaign tracker**: Record the ROI analysis in `campaign-tracker.py` so future analyses can compare period-over-period trends and validate whether recommended reallocations improved performance.
12. **Compile executive report**: Format the analysis for stakeholder presentation with clear takeaways, data tables ready for visualization, and actionable next steps.

## Output

A structured ROI analysis report containing:

- Channel-by-channel performance table (spend, revenue, conversions, ROI, ROAS, CPA, CPL)
- Blended campaign ROI and overall ROAS with total spend and revenue summary
- Attribution model comparison showing credit distribution shifts across models
- LTV-adjusted ROI projection and payback period analysis (if customer LTV was provided)
- Industry benchmark comparison with above/at/below performance ratings per channel
- Efficiency analysis identifying diminishing returns and scaling opportunities
- Budget reallocation recommendations with 2-3 modeled scenarios and projected outcomes
- Underperforming channel diagnosis with specific improvement actions
- Period-over-period trend comparison (if historical data is available from campaign tracker)
- Executive summary with top 3 insights and recommended next steps
- Visualization-ready data tables formatted for Google Sheets or slide deck export

## Agents Used

- **analytics-analyst** -- ROI computation, attribution modeling, benchmark comparison, efficiency analysis, payback period calculation, and data-driven recommendations
- **marketing-strategist** -- Budget optimization strategy, channel mix recommendations, reallocation scenario design, and executive-level insight framing for stakeholder communication
