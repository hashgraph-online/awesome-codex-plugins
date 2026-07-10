---
name: cro
description: "Optimize conversion rates. Use when: auditing landing pages, testing forms, or improving checkout flow."
---

# CRO (Conversion Rate Optimization)

## When to Use This Skill

Activate this skill when the user's request involves any of the following:

- Auditing a landing page for conversion performance
- Designing or improving a landing page layout, copy, or user flow
- Setting up, analyzing, or interpreting A/B tests or multivariate tests
- Optimizing web forms (lead gen, signup, contact, application)
- Designing or auditing pricing pages and pricing presentation
- Reducing cart abandonment or improving checkout completion rates
- Improving any website conversion metric (lead form submissions, signups, purchases, trial starts)
- Calculating sample sizes, test duration, or statistical significance for experiments
- Prioritizing which conversion improvements to tackle first
- Diagnosing why a page or funnel has a low conversion rate
- Asking about trust signals, social proof, urgency elements, or CTA optimization

## Brand Context (Auto-Applied)

Before producing any marketing output from this module:

1. **Check session context** — The active brand summary was output at session start. Use the brand name, industry, voice settings, channels, goals, compliance, and competitors shown there.
2. **If you need the full profile**, read: `~/.claude-marketing/brands/{slug}/profile.json`
3. **Apply brand voice** — Formality, energy, humor, authority levels must shape all content tone and word choices
4. **Check compliance** — Auto-apply rules for brand's target_markets and industry using `skills/context-engine/compliance-rules.md`
5. **Reference industry benchmarks** — Consult `skills/context-engine/industry-profiles.md` for the brand's industry
6. **Use platform specs** — Reference `skills/context-engine/platform-specs.md` for character limits and format requirements
7. **Check campaign history** — Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/campaign-tracker.py" --brand {slug} --action list-campaigns` before planning new work
8. **If no brand exists**, say: "No brand profile found. Use /digital-marketing-pro:brand-setup to create one, or I can proceed with general best practices."
9. **Check brand guidelines** — If `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` exists, load and enforce: `restrictions.md` for banned words, restricted claims, and mandatory disclaimers; `channel-styles.md` for channel-specific tone overrides (may differ from base voice); `messaging.md` for approved key messages, taglines, and positioning language; `voice-and-tone.md` for detailed voice rules beyond the 4 numeric scores. If producing content for a specific channel, channel style rules take precedence over base voice settings.

Do not ask the user for information that already exists in their brand profile.

## Required Context

Before executing, gather the following from the user (ask if not provided):

- **Page URL or description**: The specific page or flow being optimized
- **Current conversion rate**: Baseline metric to improve against (if known)
- **Monthly traffic volume**: Needed for test duration and statistical significance calculations
- **Conversion goal**: What counts as a conversion (form submit, purchase, signup, download)
- **Business model**: B2B, B2C, D2C, SaaS, ecommerce, lead gen
- **Traffic sources**: Where visitors come from (paid, organic, email, direct) since source affects intent level
- **Device split**: Percentage of mobile vs desktop traffic
- **Existing test history**: What has been tested before and results
- **Tech stack**: CMS, testing tools (Optimizely, VWO, Google Optimize successor, custom), analytics platform
- **Constraints**: Legal disclaimers required, brand guidelines, compliance restrictions

## Capabilities

### Landing Page Audits
- **5-second test**: Does the page communicate its value proposition within 5 seconds of loading?
- **Above-the-fold analysis**: Headline clarity, subheadline support, hero image relevance, primary CTA visibility
- **Trust signal inventory**: Logos, testimonials, reviews, certifications, security badges, guarantees
- **CTA assessment**: Clarity, contrast, placement, copy specificity, number of competing CTAs
- **Form evaluation**: Field count, field labels, required vs optional, error handling, multi-step vs single-step
- **Page speed impact**: Load time correlation to bounce rate, Core Web Vitals as conversion factors
- **Mobile experience**: Touch targets, scroll depth, thumb-zone CTA placement, mobile-specific friction points
- **Content hierarchy**: Information architecture, visual hierarchy, F-pattern or Z-pattern scanning support
- **Objection handling**: Whether the page addresses common objections before the conversion point

### A/B Testing Framework
- **ICE prioritization**: Score potential tests by Impact (1-10), Confidence (1-10), and Ease (1-10) to determine test order
- **Hypothesis format**: Structured as "If we [change], then [metric] will [improve/decrease] because [rationale]"
- **Sample size calculation**: Based on baseline conversion rate, minimum detectable effect, statistical power (80%), and significance level (95%)
- **Test duration estimation**: Accounting for traffic volume, conversion rate, and full business cycles (minimum 1-2 weeks to capture weekly patterns)
- **Result interpretation**: Statistical significance, practical significance, segment analysis, and revenue impact projection
- **Sequential testing**: When to use fixed-horizon vs sequential/Bayesian methods for faster decisions

### Form Optimization
- **Field reduction**: Remove or defer non-essential fields. Each additional field reduces conversion by approximately 4-7%
- **Progressive profiling**: Collect information across multiple interactions rather than all at once
- **Inline validation**: Real-time feedback as users complete fields reduces form abandonment
- **Smart defaults**: Pre-fill known data, use sensible defaults, and provide auto-complete
- **Multi-step forms**: Break long forms into logical steps with progress indicators
- **Field type optimization**: Dropdowns vs radio buttons vs text inputs based on option count and context
- **Error messaging**: Specific, helpful error messages positioned near the relevant field

### Pricing Psychology
- **Anchoring**: Present a higher-priced option first to make target option seem reasonable
- **Decoy effect**: Introduce a strategically inferior option to push users toward the target plan
- **Charm pricing**: $99 vs $100 -- when it works (B2C, impulse purchases) and when it backfires (premium B2B)
- **Price framing**: Annual vs monthly display, per-user vs flat rate, daily equivalency ("less than a cup of coffee")
- **Plan naming**: Naming conventions that guide self-selection (Starter/Growth/Enterprise vs Basic/Pro/Premium)
- **Feature differentiation**: Which features to gate at each tier to create natural upgrade pressure
- **Social proof on pricing**: Showing "Most Popular" badges, customer counts per tier, or logos

### Checkout Optimization
- **Cart abandonment reduction**: Exit-intent offers, cart recovery emails, progress indicators, persistent cart
- **Guest checkout**: Always offer guest checkout; forced account creation causes 24% abandonment
- **Payment method coverage**: Credit cards, PayPal, Apple Pay, Google Pay, Buy Now Pay Later, regional methods
- **Shipping transparency**: Show costs early, offer free shipping thresholds, provide delivery estimates
- **Order summary persistence**: Keep order details visible throughout checkout
- **Security reinforcement**: SSL badges, payment logos, money-back guarantees at the point of payment
- **One-page vs multi-step checkout**: Decision framework based on product complexity and information requirements
- **Post-purchase optimization**: Confirmation page upsells, order confirmation email, account creation after purchase

## Process

### Standard Landing Page Audit (Most Common Use Case)

1. **5-second scan** -- Review the page as a first-time visitor. Can you identify what the company does, who it is for, and what action to take within 5 seconds?
2. **Above-the-fold audit** -- Evaluate headline specificity, subheadline support, hero relevance, and CTA prominence. The fold is the most valuable real estate.
3. **Trust and credibility** -- Inventory all trust signals (testimonials, logos, reviews, certifications, guarantees). Identify gaps where social proof is missing at critical decision points.
4. **CTA analysis** -- Count all CTAs on the page. Check for competing actions, button copy specificity ("Get My Free Trial" beats "Submit"), contrast ratio, and placement frequency.
5. **Content flow** -- Walk through the page section by section. Does it follow a logical persuasion sequence? Problem, solution, proof, action?
6. **Form/conversion point** -- Evaluate the form or conversion mechanism. Count fields, assess labels, check error handling, and evaluate the micro-copy around the submit button.
7. **Mobile audit** -- Review the same page on mobile. Check touch targets (minimum 44x44px), scroll depth to CTA, horizontal scrolling issues, and load time.
8. **Speed check** -- Note any visible performance issues. Recommend Core Web Vitals audit if speed appears to be a factor.
9. **Prioritized recommendations** -- Deliver findings as a prioritized list using the ICE framework. Quick wins first, structural changes second, redesign-level changes last.

### A/B Test Design Process

1. **Identify the problem** -- Use data (analytics, heatmaps, session recordings, user feedback) to pinpoint the conversion bottleneck.
2. **Form hypothesis** -- Write a structured hypothesis: "If we [change X], then [metric Y] will [increase/decrease] by [estimated amount] because [rationale based on evidence]."
3. **Score with ICE** -- Rate Impact, Confidence, and Ease on a 1-10 scale. Prioritize tests with highest composite scores.
4. **Calculate requirements** -- Determine sample size with `python "${CLAUDE_PLUGIN_ROOT}/scripts/sample-size-calculator.py" --baseline-rate {rate} --mde {mde} --mde-type absolute --significance 0.95 --power 0.80` (pass `--mde-type relative` if the MDE is a relative lift — the two differ by ~40× at a 5% baseline). Estimate test duration based on daily traffic.
5. **Design variation** -- Create the test variation. Change only one variable per test (unless running a multivariate test with sufficient traffic).
6. **QA the test** -- Verify tracking, check both variations across devices and browsers, confirm that the test does not break downstream flows.
7. **Run and monitor** -- Launch the test. Do not peek at results before reaching calculated sample size. Monitor for technical issues only.
8. **Analyze and document** -- At the end of the test, evaluate statistical significance with `python "${CLAUDE_PLUGIN_ROOT}/scripts/significance-tester.py" --control-visitors {n} --control-conversions {n} --variant-visitors {n} --variant-conversions {n} --confidence 0.95`, check segment-level results, calculate revenue impact, and document learnings regardless of outcome.

## Reference Files

- `landing-page-audit.md` -- Detailed audit checklist, scoring rubric, and benchmark conversion rates by industry
- `ab-testing.md` -- Test design templates, sample size calculators, statistical methods, and common testing pitfalls
- `form-optimization.md` -- Field-by-field optimization guide, progressive profiling implementation, and form UX patterns
- `pricing-psychology.md` -- Pricing page templates, psychological principles with examples, and tier structure frameworks
- `checkout-optimization.md` -- Cart abandonment diagnosis, checkout flow templates, and payment optimization strategies

## Output Formats

- **Landing page audit report**: Section-by-section findings with severity ratings (critical/high/medium/low), screenshots or references to specific elements, and prioritized action items with ICE scores
- **A/B test plan**: Hypothesis, variation description, sample size requirements, estimated duration, success criteria, and segmentation plan
- **Form optimization spec**: Current vs recommended field list, layout wireframe description, validation rules, and error message copy
- **Pricing page recommendation**: Tier structure, pricing presentation, feature matrix, and psychological triggers with rationale
- **Checkout optimization plan**: Funnel stage analysis, drop-off diagnosis, and ordered list of improvements with expected impact

## Edge Cases

### Low Traffic Sites
Sites with fewer than 1,000 monthly conversions often cannot reach statistical significance within a reasonable timeframe. For these sites, skip A/B testing and instead implement best practices directly based on audit findings. Use before/after measurement with awareness of confounding variables. Consider qualitative methods (user testing with 5 users catches 85% of usability issues) over quantitative testing.

### B2B Long-Form Pages vs B2C Short-Form
B2B landing pages often need to be longer because purchase decisions involve multiple stakeholders, higher price points, and longer evaluation cycles. Do not default to "shorter is better." Instead, ensure the above-the-fold section qualifies intent quickly, and let the rest of the page handle objections comprehensively. B2C impulse purchases benefit from short, fast, single-CTA pages.

### Mobile-First vs Desktop-First Optimization
Check the device split before making recommendations. If 70%+ of traffic is mobile, optimize for mobile first and ensure desktop does not break. If traffic is desktop-dominant (common in B2B), optimize for desktop but never neglect mobile. The "responsive" middle ground often serves neither well.

### Regulated Industries with Required Disclaimers
Healthcare, finance, legal, and insurance pages often require lengthy disclaimers, disclosures, or compliance text. Do not recommend removing these. Instead, work on formatting (collapsible sections, footnotes, smaller but readable type) and ensure the required content does not visually compete with the primary CTA. Position disclaimers after the conversion point where legally permissible.

### Testing During Seasonal Peaks
Avoid launching A/B tests during Black Friday, holiday seasons, or major promotional periods. User behavior during peaks is not representative of normal behavior. Tests run during these periods will produce unreliable results. If a test must run during a peak, note the caveat and plan a validation retest during a normal period.

## Related Skills

- **Paid Advertising** -- CRO directly impacts ad campaign ROAS; landing page quality affects Quality Score and ad relevance
- **Analytics & Insights** -- Data analysis for identifying conversion bottlenecks and measuring test results
- **Content Engine** -- Copywriting for headlines, CTAs, and persuasive page content
- **Funnel Architect** -- CRO fits within the broader funnel optimization strategy
- **Growth Engineering** -- Activation and onboarding optimization overlaps with CRO for SaaS products
- **SEO** -- Page speed and Core Web Vitals affect both rankings and conversion rates

## Agents Used

- **cro-specialist** — Primary agent for all CRO tasks: landing page audits, A/B test design, form optimization, pricing psychology, checkout optimization, statistical significance calculations, and experiment documentation
