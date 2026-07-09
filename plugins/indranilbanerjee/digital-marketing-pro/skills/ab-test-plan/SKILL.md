---
name: ab-test-plan
description: "Design A/B and multivariate tests. Use when: sample size calculation, testing hypothesis, CRO experimentation."
argument-hint: "[element-to-test]"
---

# /digital-marketing-pro:ab-test-plan

## Purpose

Dedicated A/B test planning with a structured hypothesis framework, statistical sample size calculation, variant design, and monitoring plan. Produces a complete experiment specification with statistical rigor and clear decision criteria.

## Input Required

The user must provide (or will be prompted for):

- **Element to test**: The specific page, component, or experience being tested (landing page headline, CTA button, pricing page layout, email subject line, checkout flow, form design, etc.)
- **Current conversion rate**: Baseline conversion rate for the metric being tested (or best estimate)
- **Desired minimum detectable effect (MDE)**: The smallest improvement worth detecting. **MDE is ABSOLUTE by default** — expressed in the same units as the baseline (baseline 5.0% and you want to catch a +1.0 percentage-point lift, i.e. 5.0% → 6.0% ⇒ `--mde 0.01 --mde-type absolute`). To express it as a **relative** lift instead (a 10% relative improvement on a 5% baseline = 5.5% ⇒ `--mde 0.10 --mde-type relative`), pass `--mde-type relative`. This distinction is the single most common sample-size error: the same "10%" read as absolute vs. relative changes the required sample size by roughly 40× at a 5% baseline. Always confirm which the user means.
- **Daily traffic or impressions**: Average daily visitors or impressions to the test page or element
- **Significance level**: Desired confidence level, default 95% (alpha = 0.05)
- **Statistical power**: Desired power, default 80% (beta = 0.20)
- **Number of variants**: How many variants to test (default 1 treatment + 1 control; more for multivariate)
- **Business context**: What prompted the test idea (analytics data, user feedback, competitive analysis, heuristic audit, stakeholder request)

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply voice, compliance, industry context. Check `guidelines/_manifest.json` for restrictions, messaging, channel styles, voice-and-tone rules, and templates. If a template matching this command exists in `~/.claude-marketing/brands/{slug}/templates/`, apply its format. If no brand exists, prompt for `/digital-marketing-pro:brand-setup` or proceed with defaults.
2. **Check campaign history**: Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/campaign-tracker.py" --brand {slug} --action list-campaigns` to review past test results and avoid re-testing already-validated hypotheses.
3. **Run sample size calculator**: Execute the calculator with the baseline rate, MDE, MDE type, significance, and power. The `--mde-type` flag defaults to `absolute` — always confirm with the user which interpretation they mean before computing (the two differ by ~40× at a 5% baseline):
   ```bash
   # Absolute MDE — detect a 1.0 percentage-point lift on a 5% baseline (5.0% → 6.0%)
   python "${CLAUDE_PLUGIN_ROOT}/scripts/sample-size-calculator.py" --baseline-rate 0.05 --mde 0.01 --mde-type absolute --significance 0.95 --power 0.80

   # Relative MDE — detect a 10% relative lift on a 5% baseline (5.0% → 5.5%)
   python "${CLAUDE_PLUGIN_ROOT}/scripts/sample-size-calculator.py" --baseline-rate 0.05 --mde 0.10 --mde-type relative --significance 0.95 --power 0.80
   ```
   This determines the required sample size per variant. Later, when the test has run, evaluate the result with `python "${CLAUDE_PLUGIN_ROOT}/scripts/significance-tester.py" --control-visitors {n} --control-conversions {n} --variant-visitors {n} --variant-conversions {n} --confidence 0.95`.
4. **Build hypothesis statement**: Structure the hypothesis in the format: "If [specific change], then [primary metric] will [direction and magnitude] because [rationale grounded in data, user research, or established UX principle]."
5. **Design test variants**: Define the control (current experience) and one or more treatment variants. Specify exactly what changes in each variant -- copy, layout, color, imagery, flow, or functionality. For multivariate tests, define the variable matrix and interaction effects to watch.
6. **Define primary and secondary metrics**: Identify the primary success metric (the one that determines the winner) and secondary metrics to monitor for unintended effects (e.g., testing CTA click rate as primary, but watching bounce rate, time on page, and downstream conversion as secondary guardrails).
7. **Calculate test duration**: Based on sample size requirements and daily traffic, estimate the number of days needed. Ensure the duration spans at least one full business cycle (7 days minimum) to account for day-of-week variation. Flag if duration exceeds 8 weeks (validity risk).
8. **Create monitoring plan**: Define interim checkpoints for technical QA (not statistical peeking), sample ratio mismatch (SRM) detection, and guardrail metric alerts that would trigger early test stoppage for data quality or user experience reasons.
9. **Define stopping rules and decision criteria**: Specify when to call the test (sample size reached + significance threshold met), when to stop early (guardrail violations, SRM detected, implementation bugs), and the protocol for inconclusive results (extend, redesign, or implement based on directional signal).
10. **Assess traffic feasibility**: Verify that the daily traffic can reach the required sample size within a reasonable timeframe (under 8 weeks). If traffic is insufficient, recommend reducing the number of variants, increasing the MDE, or using qualitative methods instead.
11. **Document pre-registration**: Record the test plan before launch -- hypothesis, metrics, sample size, duration, and decision criteria -- to prevent post-hoc rationalization and ensure scientific rigor.

## Output

A structured A/B test plan containing:

- Hypothesis statement in If/Then/Because format with supporting evidence or rationale
- Control and variant descriptions with specific, implementable change details
- Required sample size per variant and total sample size
- Estimated test duration in days based on traffic volume and required sample size
- Primary metric and secondary metric definitions with measurement methods
- Guardrail metrics that trigger early stoppage if degraded
- Monitoring dashboard specification with interim checkpoint schedule
- Statistical analysis plan (frequentist or Bayesian, one-tailed or two-tailed, correction for multiple comparisons)
- Stopping rules for early termination (guardrail violations, SRM detection, critical bugs)
- Go/no-go decision criteria with clear thresholds for winner declaration
- Post-test action plan for winning, losing, and inconclusive scenarios
- Traffic feasibility assessment with low-traffic alternative recommendations if applicable
- Test documentation template for recording results and learnings in the campaign tracker

## Agents Used

- **cro-specialist** -- Hypothesis design, variant specification, sample size calculation, statistical analysis planning, monitoring framework, stopping rules, traffic feasibility assessment, and experiment documentation
