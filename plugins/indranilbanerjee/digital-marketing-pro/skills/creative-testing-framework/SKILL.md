---
name: creative-testing-framework
description: "Design structured ad creative tests with A/B test plans, multivariate creative strategies, sample size calculations, and iteration cadences. Use when planning creative testing for ads, optimizing creative performance, or building a testing playbook across advertising platforms."
user-invocable: true
triggers:
  - design an A/B test for ads
  - creative testing strategy
  - multivariate ad test
  - test ad creative
  - ad creative testing framework
  - plan creative iterations
  - sample size for ad test
  - creative optimization testing
---

# /digital-marketing-pro:creative-testing-framework

## Purpose

Design a systematic creative testing framework that maximizes learning velocity while maintaining statistical rigor across advertising platforms. Produces a complete testing playbook with variable prioritization, sample size requirements, iteration cadence, and documentation standards for continuous creative optimization.

## Input Required

The user must provide (or will be prompted for):

- **Ad platform(s)**: Where ads are running — Google Ads, Meta Ads, LinkedIn Ads, TikTok Ads, programmatic DSPs, Pinterest, X/Twitter, or multi-platform
- **Creative types available**: What formats can be produced — static image, video (short-form/long-form), carousel, text-only, responsive display, HTML5, playable, or collection ads
- **Monthly ad budget allocated to testing**: How much budget is available specifically for creative experimentation vs. proven performers
- **Current top-performing creative**: Description or reference to the best-performing ads currently running, including their key metrics
- **Learning goals**: Which creative elements need optimization — headlines, imagery, CTA copy, video hooks, color palette, offer framing, social proof, format type, or ad copy length
- **Audience segments for testing**: The audience groups available for testing — prospecting, retargeting, lookalike, interest-based, demographic, or custom segments
- **Campaign objectives**: What the ads are optimized for — awareness (impressions/reach), consideration (clicks/video views), or conversion (leads/purchases/ROAS)
- **Historical creative performance data**: Optional — past test results, creative fatigue patterns, seasonal performance variations, and known winners/losers
- **Brand guidelines constraints**: Visual identity rules, messaging restrictions, mandatory disclaimers, or approval bottlenecks that affect creative production speed
- **Testing timeline**: How long the testing program should run — single sprint (2-4 weeks), quarterly roadmap, or ongoing evergreen program

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for custom templates at `~/.claude-marketing/brands/{slug}/templates/`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Define testing variables**: Catalog all testable creative elements — headline copy, body copy length, CTA text and color, hero image subject, image style (photo vs. illustration vs. UGC), video hook (first 3 seconds), video length, ad format (static vs. carousel vs. video), color palette, offer framing (discount vs. value vs. urgency), social proof type (testimonial vs. stat vs. badge), and layout composition.
3. **Prioritize variables by expected impact and ease**: Score each variable on a 2x2 matrix of expected performance impact (high/low) and production effort (high/low). Rank variables so the team tests high-impact, low-effort elements first. Use historical data and platform benchmarks to inform impact estimates where available.
4. **Design testing matrix**: Build the variable-by-variant grid — for each priority variable, define 2-4 variants to test against the current control. Ensure tests are isolated (one variable per test) unless running deliberate multivariate experiments. Map each test to the appropriate audience segment and platform.
5. **Calculate sample size per variant and minimum budget**: Compute the required conversions per variant with `python "${CLAUDE_PLUGIN_ROOT}/scripts/sample-size-calculator.py" --baseline-rate {rate} --mde {mde} --mde-type relative --significance 0.95 --power 0.80` (a "10-20% relative lift" is `--mde 0.10`-`0.20` with `--mde-type relative`; use `--mde-type absolute` if the target is stated in percentage points — the two differ by ~40× at a 5% baseline). Translate sample size into minimum budget per test based on current CPM/CPC rates.
6. **Define holdout control structure**: Design the control framework — allocate 10-20% of testing budget to an unchanging control creative that serves as a stable benchmark. Define when the control should be refreshed (quarterly or when performance degrades below threshold) and how new winners graduate to become the new control.
7. **Set statistical significance thresholds**: Define the confidence level required to declare a winner (90% for directional decisions, 95% for major creative shifts). Specify whether to use frequentist (p-value) or Bayesian (probability to be best) methodology. Document the minimum observation period (7+ days to account for day-of-week variation) and anti-peeking protocols.
8. **Create iteration cadence**: Design the testing rhythm — weekly creative refreshes for high-volume accounts, bi-weekly for mid-volume, monthly for lower-volume. Define the pipeline: brief (day 1), production (days 2-3), review and approval (day 4), launch (day 5), monitor (days 6-14), analyze and iterate (day 15). Align cadence with brand approval workflows.
9. **Build winner selection criteria**: Define how winners are determined — primary metric (CTR, conversion rate, ROAS, or CPA depending on objective), minimum confidence level, minimum sample size reached, and guardrail metrics that must not degrade (e.g., a headline that lifts CTR but tanks conversion rate is not a winner). Confirm a candidate winner is statistically real with `python "${CLAUDE_PLUGIN_ROOT}/scripts/significance-tester.py" --control-visitors {n} --control-conversions {n} --variant-visitors {n} --variant-conversions {n} --confidence 0.95` before declaring it. Include rules for ties and inconclusive results.
10. **Create documentation template for results and learnings**: Design a standardized test card template capturing: hypothesis, variable tested, variants, audience, platform, date range, sample size, primary metric results, secondary metrics, statistical significance, winner declaration, key learning, and next test recommendation. This builds the creative knowledge base over time.

## Output

A structured creative testing framework containing:

- **Testing variable priority ranking** — impact-by-effort matrix with all testable elements scored, ranked, and sequenced into a testing roadmap
- **Testing matrix** — variable-by-variant grid showing each test, its control, variants, target audience, and platform with clear isolation of variables
- **Sample size requirements per variant** — calculated minimums based on current performance data, desired MDE, and confidence level
- **Minimum budget per test** — translated from sample size requirements using current platform CPM/CPC rates with total testing budget allocation
- **Holdout control design** — 10-20% budget allocation, control refresh criteria, and winner graduation process from test to evergreen
- **Statistical significance thresholds and methodology** — confidence levels, frequentist vs. Bayesian approach, minimum observation periods, and anti-peeking rules
- **Iteration cadence calendar** — week-by-week or sprint-by-sprint testing schedule with brief, production, launch, and analysis dates mapped out
- **Winner selection criteria** — primary metric, confidence level, minimum lift threshold, guardrail metrics, tie-breaking rules, and inconclusive result protocols
- **Creative brief template per variant** — standardized brief format ensuring each variant is produced with clear differentiation from control and other variants
- **Naming convention for creative tracking** — systematic naming structure (platform_audience_variable_variant_date) enabling clean performance analysis across platforms
- **Documentation template for results and learnings** — test card format for recording hypothesis, results, significance, learnings, and next steps in a searchable knowledge base
- **Creative fatigue indicators and refresh triggers** — metrics that signal when a winning creative is losing effectiveness (CTR decline, frequency threshold, engagement drop) with recommended refresh actions
- **Platform-specific testing best practices** — Meta Advantage+ creative considerations (including Advantage+ Leads, globally available May 2026), Google responsive ad testing nuances, LinkedIn creative specs, TikTok native content requirements, Threads image-only placement (global rollout completing May 2026), and platform-specific budget minimums
- **AI creative variant production** — When testing variants at scale, use `Nano Banana Pro` for high-fidelity static variants with brand-character consistency (best-in-class on-image text rendering), `Gemini Veo 3.1` or `Gemini Omni` for short-form video variants, and `Veo 3.1` specifically when synchronized native audio matters. All AI-generated test variants destined for EU placements must be C2PA-signed via `/digital-marketing-pro:c2pa-metadata` before launch — the pre-publish gate (`/digital-marketing-pro:check`) blocks unsigned AI assets on EU-targeted ad sets. Treat AI-generation cost-per-variant as the new floor for "creative production cost" in your minimum-budget math
- **Quarterly testing roadmap** — 12-week plan showing which variables to test in which order, with budget phasing, milestone reviews, and strategic learning goals per quarter

## Agents Used

- **cro-specialist** — Testing methodology design, statistical rigor framework, sample size calculation, significance thresholds, winner selection criteria, holdout control structure, and documentation standards
- **media-buyer** — Platform-specific testing configuration, budget allocation per test, creative format recommendations, audience segment mapping, naming conventions, fatigue monitoring, and quarterly roadmap planning
