---
name: simulate
description: "Simulate revenue impact via Monte Carlo. Use when: testing channel mix changes, budget shifts, or new channel launches."
---

# /digital-marketing-pro:simulate

## Purpose

Run Monte Carlo simulation of marketing scenarios to predict revenue outcomes with probability distributions. Test channel mix changes, budget reallocations, new channel launches, and spending adjustments before committing real budget. This command models uncertainty explicitly — instead of single-point forecasts that hide risk, it generates thousands of simulated outcomes per scenario to show the full range of what could happen, with calibrated confidence intervals. Use it when the stakes are high enough that "expected ROI" alone isn't sufficient and you need to understand downside risk, upside potential, and the probability of hitting specific revenue targets.

## Input Required

The user must provide (or will be prompted for):

- **Scenarios to simulate**: One or more marketing scenarios to model — each defined by a set of channel budgets and assumptions. A scenario might be "shift 30% of paid search budget to TikTok" or "launch YouTube Ads at $15K/month while maintaining current spend" or "cut display by 50% and redistribute to email and SEO." Each scenario must include channel-level budget allocations and can optionally include custom ROI assumptions per channel
- **Channel parameters per scenario**: For each channel in each scenario: monthly budget allocation, expected ROI with mean and standard deviation (e.g., "3.2x +/- 0.8x" for a channel with historical variance), and saturation point if known (the spend level beyond which returns diminish sharply). If the user doesn't provide standard deviations, estimate from historical brand data or industry benchmarks
- **Projection period**: Number of months to simulate forward — typically 3, 6, or 12 months. Longer projections carry wider confidence intervals due to compounding uncertainty
- **Revenue target (optional)**: A specific revenue figure the user wants to evaluate probability of achieving — e.g., "What's the probability we hit $2M in Q3?" The simulation will calculate the exact probability of reaching this target per scenario
- **Number of simulations (optional)**: How many Monte Carlo iterations to run per scenario — defaults to 10,000 which balances statistical precision with speed. Can increase to 50,000+ for high-stakes decisions where tighter confidence intervals matter
- **Constraints (optional)**: Minimum or maximum spend per channel, total budget cap, or required channel presence — the simulation respects these constraints when modeling outcomes

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply historical performance data, channel benchmarks, known saturation curves, and seasonality patterns from past campaigns. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load any budget or channel constraints. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with industry defaults.
2. **Define scenario parameters**: For each scenario, structure the channel-level inputs — budget, ROI mean, ROI standard deviation, saturation point, and any interaction effects between channels (e.g., paid search lifts organic CTR, email amplifies content performance). Where the user hasn't provided standard deviations, calibrate from the brand's historical campaign data or, failing that, fall back to industry-specific defaults derived from `skills/context-engine/industry-profiles.md` (16 industries with typical channel performance ranges) and the channel-family benchmarks in `skills/context-engine/channel-families.md`. Validate that all scenarios are internally consistent — budgets sum correctly, no negative allocations, saturation points are above current spend.
3. **Run Monte Carlo simulation**: Execute `revenue-simulator.py` with the structured scenario parameters. For each scenario, run N simulations (default 10,000) where each iteration samples channel ROIs from their probability distributions, applies diminishing returns near saturation points, models channel interaction effects, accounts for time-lag effects (SEO and content ramp over months, paid delivers immediately), and applies seasonal adjustment factors. Aggregate results into probability distributions per scenario.
4. **Calculate probability-weighted outcomes**: For each scenario, compute expected revenue (mean of all simulations), median revenue (P50), pessimistic case (P10 — 90% chance of exceeding this), optimistic case (P90 — only 10% chance of exceeding this), and probability of hitting the user's revenue target if one was specified. Calculate risk-adjusted return using the Sharpe-like ratio of expected return divided by outcome variance.
5. **Compare scenarios side-by-side**: Build a comparison matrix showing all scenarios against the current baseline. Rank by expected revenue, by risk-adjusted return, and by probability of hitting the revenue target. Identify the dominant scenario (best on most metrics) and flag any scenarios that are strictly dominated (worse on every metric than another option).
6. **Run sensitivity analysis**: For the top 2-3 scenarios, identify which input variables have the highest impact on outcomes — which channel's ROI uncertainty drives the most variance, whether the result is sensitive to saturation assumptions, and how much the recommendation changes if a key assumption shifts by 20%. Present as a tornado chart ranking variables by impact.

## Output

A comprehensive simulation report containing:

- **Per-scenario results**: Expected revenue (mean), median revenue (P50), pessimistic case (P10), optimistic case (P90), probability of hitting the revenue target, risk-adjusted return score, and revenue probability distribution visualization description
- **Scenario comparison table**: All scenarios ranked side-by-side on expected revenue, risk-adjusted return, target probability, and delta versus current baseline — with the recommended scenario highlighted and dominance relationships noted
- **Sensitivity analysis**: Tornado-chart breakdown of which variables drive the most outcome variance in the top scenarios — ROI assumptions, saturation points, channel interactions, and seasonal factors ranked by impact magnitude
- **Channel contribution breakdown**: Per scenario, how each channel contributes to total expected revenue with confidence intervals — showing where the value is generated and where the uncertainty lives
- **Optimal scenario recommendation**: The recommended scenario with confidence level, reasoning that accounts for both expected return and risk profile, and specific conditions under which the recommendation would change
- **Simulation metadata**: Number of iterations, convergence check (did results stabilize), key assumptions documented, and data sources used for calibration

## Agents Used

- **marketing-scientist** — Monte Carlo simulation design including distribution selection and correlation modeling, parameter estimation from historical data and industry benchmarks, channel interaction and saturation curve modeling, sensitivity analysis and tornado chart construction, result interpretation with statistical rigor including confidence interval calibration, scenario dominance analysis, and risk-adjusted return calculation for recommendation ranking
- **analytics-analyst** — Historical performance data extraction and trend analysis for ROI calibration, seasonal pattern identification from past campaign data, benchmark sourcing and validation against brand actuals, and convergence verification of simulation outputs
