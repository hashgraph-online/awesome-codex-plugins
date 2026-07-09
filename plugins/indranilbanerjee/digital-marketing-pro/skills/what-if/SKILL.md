---
name: what-if
description: "Compare budget scenarios side-by-side. Use when: testing 2-4 allocation variants with projected outcomes."
---

# /digital-marketing-pro:what-if

## Purpose

Quick scenario comparison tool. Test 2-4 marketing scenarios against each other — different budget allocations, channel mixes, or strategic approaches — and see projected outcomes side-by-side. This is the lighter, faster alternative to full Monte Carlo simulation (`/digital-marketing-pro:simulate`). Where simulate runs thousands of iterations with full probability distributions, what-if uses point estimates with simple variance bands to give directional answers in minutes. Use it for rapid decision-making when you need a quick read on "should we do A or B?" without the statistical depth of a full simulation — team meetings, Slack discussions, quick planning calls, or narrowing down options before running a deeper analysis.

> **Simulated output — not a forecast.** what-if projections are directional point-estimates produced by `revenue-simulator.py` from your stated assumptions and historical benchmarks, not measured predictions. Treat every scenario number as a planning aid: validate the ROI assumptions against your own data before committing budget. All example dollar figures in this skill are SYNTHETIC (illustrative only — never reuse these numbers).

## Input Required

The user must provide (or will be prompted for):

- **Scenarios to compare**: 2-4 named scenarios, each with channel-level budget allocations and expected ROI per channel. Examples: "Scenario A: Heavy paid — $50K Google Ads, $30K Meta, $10K email" vs "Scenario B: Content-led — $20K Google Ads, $15K Meta, $40K content, $15K SEO." Each scenario needs a descriptive name and channel budget breakdown. If the user provides only high-level descriptions ("more on paid, less on organic"), ask for specific dollar allocations or percentage splits
- **Current baseline**: The existing budget allocation and recent performance as the reference point for comparison — what the brand is doing right now so each scenario shows a clear delta. If not provided, pull from brand context historical data
- **Evaluation criteria (optional)**: What matters most for this decision — total revenue, ROI efficiency, risk level, speed to impact, or a weighted combination. Defaults to expected revenue if not specified
- **Time horizon (optional)**: How far out to project — defaults to 3 months. Shorter horizons favor paid channels, longer horizons favor organic and content investments due to compounding effects

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Pull historical channel performance, recent ROI data, and known benchmarks to calibrate scenario projections. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with industry defaults.
2. **Define current baseline and alternative scenarios**: Structure the current state as Scenario 0 (baseline) with actual recent performance data. Then define each user scenario with channel budgets and ROI assumptions — using brand historical data where available, industry benchmarks where not. Flag any assumptions that differ significantly from historical performance so the user can validate them.
3. **Run quick simulation**: Execute `revenue-simulator.py` in what-if mode — a simplified projection that calculates expected revenue per scenario using point estimates with variance bands (not full Monte Carlo), applies basic diminishing returns for channels near saturation, and accounts for channel ramp time (SEO and content take months to deliver, paid is immediate). Faster execution, directional accuracy.
4. **Compare projected outcomes**: Build a side-by-side comparison table showing each scenario's projected revenue, total ROI, delta versus baseline (both absolute dollars and percentage), channel-level contribution, and a simple risk indicator (low/medium/high based on concentration and assumption sensitivity). Rank scenarios by the user's evaluation criteria.
5. **Identify best scenario and key trade-offs**: Select the scenario with the best expected return and the scenario with the best risk-adjusted return (if different). Articulate the key trade-offs between the top options — what you gain, what you give up, and what assumptions would need to hold true for each to deliver as projected.

## Output

A concise scenario comparison containing:

- **Side-by-side scenario comparison**: Each scenario showing projected revenue, total ROI, cost, and risk level — formatted as a clean comparison table with the baseline as the reference column and deltas highlighted for each alternative
- **Delta versus current baseline**: Per scenario, the absolute and percentage change in projected revenue, ROI, and cost compared to what the brand is doing today — making it immediately clear whether each scenario is an improvement and by how much
- **Recommendation with reasoning**: The recommended scenario with a clear explanation of why — balancing expected return, risk, feasibility, and alignment with brand goals. If two scenarios are close, explain what would tip the decision one way or the other
- **Key trade-offs between top scenarios**: The specific gains and sacrifices of choosing one top scenario over another — channel dependencies, ramp time differences, risk concentration, and reversibility if the bet doesn't pay off

## Agents Used

- **marketing-scientist** — Scenario modeling with point estimates and variance bands, channel ROI projection with ramp time and diminishing returns adjustments, side-by-side comparison analysis with delta calculations, risk assessment based on assumption sensitivity and channel concentration, and recommendation synthesis balancing expected return against risk profile and strategic fit
