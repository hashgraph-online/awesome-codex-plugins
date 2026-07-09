# Evaluation Framework Guide -- Content QA System

The Digital Marketing Pro eval system is an automated quality assurance pipeline that scores marketing content across six dimensions before it reaches publication. It catches hallucinations, unverified claims, structural problems, brand voice drift, readability issues, and general content quality gaps -- then persists results over time so you can detect regression and improve continuously.

This guide covers the full architecture, when to use each eval type, how to interpret results, and how to configure the system for different industries and content types.

---

## 1. Eval System Architecture

Eight scripts work together to form the evaluation pipeline. Each script is a standalone Python tool (stdlib only, zero external dependencies) that can run independently or be orchestrated by the master runner.

### Script Inventory

| Script | Role | Input | Output |
|--------|------|-------|--------|
| `eval-runner.py` | Master orchestrator | Content text/file + options | Composite report with weighted scores, grade, pass/fail |
| `hallucination-detector.py` | Fabrication detection | Content text/file | Hallucination risk score + flagged items |
| `claim-verifier.py` | Evidence cross-check | Content + evidence JSON | Claim verification score + per-claim status |
| `output-validator.py` | Structure validation | Content + schema name | Structure score + missing sections/format issues |
| `quality-tracker.py` | Persistence and trends | Eval results | Logged eval + trend data + regression alerts |
| `eval-config-manager.py` | Threshold management | Brand slug + config changes | Per-brand eval configuration |
| `prompt-ab-tester.py` | Variant comparison | Test name + variant scores | Statistical comparison + winner determination |
| `language-router.py` | Language detection/routing | Content text | Detected language + routing recommendation |

### How They Connect

```
Content (text or file)
        |
        v
  eval-runner.py (orchestrator)
        |
        +---> hallucination-detector.py ---> hallucination risk score
        |
        +---> claim-verifier.py -----------> claim verification score
        |         (requires --evidence)
        |
        +---> output-validator.py ---------> output structure score
        |         (requires --schema)
        |
        +---> content-scorer.py -----------> content quality score
        |
        +---> brand-voice-scorer.py -------> brand voice score
        |
        +---> readability-analyzer.py -----> readability score
        |
        v
  Weighted composite score + letter grade
        |
        v
  quality-tracker.py (persistence)
        |
        +---> Rolling baseline update
        +---> Regression detection
        +---> Trend analysis
```

The eval-runner calls each script via subprocess, collects JSON output from each, applies dimension weights, computes a composite score, assigns a letter grade, and optionally logs the result to quality-tracker.

### Key Design Decisions

- **Subprocess isolation**: Each evaluator runs in its own process. A failure in one dimension does not block the others. The eval-runner captures errors and reports partial results.
- **JSON-in, JSON-out**: Every script reads arguments from CLI flags and writes structured JSON to stdout. This makes them composable and testable.
- **Brand-aware**: All scripts resolve the active brand from `~/.claude-marketing/brands/_active-brand.json` when no `--brand` flag is provided. This means eval config, quality history, and A/B tests are all scoped per brand.

---

## 2. When to Use Each Eval Type

### run-full -- Before Publishing Any Content

Full 6-dimension evaluation. Use this for any content that will be seen by an external audience.

```
python eval-runner.py --action run-full --file draft.md --evidence claims.json --schema blog_post --log
```

**Use for**: Blog posts, emails, landing pages, press releases, ad copy, campaign plans, content briefs, whitepapers, case studies, web pages.

**Dimensions evaluated**: content_quality (0.25), brand_voice (0.20), hallucination (0.20), claim_verification (0.15), output_structure (0.10), readability (0.10).

**When to skip evidence/schema**: If no evidence file exists, claim_verification is omitted and its weight is redistributed. If no schema is specified, output_structure is omitted. The composite recalculates with remaining dimensions.

### run-quick -- During Drafting Iterations

Fast feedback loop with 3 dimensions. Use this while iterating on drafts to catch major issues early without the overhead of full evaluation.

```
python eval-runner.py --action run-quick --text "Your draft content here..."
```

**Use for**: First drafts, outline-to-draft transitions, rapid iteration cycles, internal review rounds.

**Dimensions evaluated**: hallucination (0.40), content_quality (0.35), readability (0.25).

**Why these three**: Hallucination risk is weighted highest because catching fabricated claims early prevents downstream problems. Content quality and readability provide fast signal on whether the draft is heading in the right direction.

### run-compliance -- Before Regulated/Sensitive Content

Compliance-focused evaluation with 4 dimensions weighted toward truthfulness and verifiability.

```
python eval-runner.py --action run-compliance --file page.md --evidence facts.json --schema landing_page
```

**Use for**: Healthcare marketing, financial services content, legal marketing, pharmaceutical claims, insurance offers, educational institution marketing, real estate listings.

**Dimensions evaluated**: hallucination (0.35), claim_verification (0.30), brand_voice (0.20), output_structure (0.15).

**Why this combination**: Regulated industries face legal consequences for unverified claims. The heavy weighting on hallucination and claim verification ensures content is truthful before it goes through brand and structural checks.

### Individual Scripts -- Investigating Specific Issues

Run any evaluator standalone when you need to diagnose a specific problem.

```
python hallucination-detector.py --action detect --file draft.md
python claim-verifier.py --action extract-claims --text "We grew revenue 3x..."
python output-validator.py --action validate --file page.md --schema landing_page
```

**Use for**: Investigating why a composite score dropped, deep-diving into a specific dimension, validating a single aspect of content during revision.

---

## 3. Interpreting Composite Scores and Grades

| Grade | Score Range | Meaning | Action |
|-------|-------------|---------|--------|
| **A+** | 95--100 | Publication-ready, exemplary quality | Publish with confidence. Use as a reference example for future content. |
| **A** | 90--94 | Excellent, minimal revision needed | Publish. Optional minor polish for perfection. |
| **A-** | 85--89 | Very good, minor polish recommended | Publish after addressing any flagged items. Low-priority revisions. |
| **B+** | 80--84 | Good quality, some improvements worthwhile | Review flagged items. Publish if timeline is tight; revise if possible. |
| **B** | 75--79 | Acceptable, review flagged items | Revise flagged items before publishing. Most content lands here on first draft. |
| **B-** | 70--74 | Below average, revision recommended | Revise before publishing. Check which dimensions are pulling the score down. |
| **C+** | 65--69 | Mediocre, significant revision needed | Do not publish without revision. Identify the weakest 2-3 dimensions and address them. |
| **C** | 60--64 | Poor, major issues present | Substantial revision required. Consider re-approaching from a different angle. |
| **C-** | 55--59 | Very poor, substantial rewrite needed | Near-rewrite territory. Check if the content brief was clear enough. |
| **D** | 40--54 | Failing, do not publish without major revision | Rewrite from scratch using a clearer brief and stronger source material. |
| **F** | Below 40 | Auto-reject, fundamental quality issues | Blocked by auto-reject gate. Content is not salvageable through revision. Start over. |

**Practical guidance**: Most first drafts from agents score in the B to B+ range (75-84). Two rounds of targeted revision typically bring content into the A- to A range. If a first draft scores below C+ (65), the issue is usually an unclear brief or missing context, not just polish.

---

## 4. Hallucination Detection Methodology

The hallucination-detector uses heuristic pattern matching to identify content that may contain fabricated facts. It is deliberately conservative -- it flags potential issues for human review rather than silently passing questionable claims.

### What It Catches

- **Fabricated statistics without citations**: Percentages, dollar amounts, multipliers, and ratios that appear without attribution within 2 sentences
- **Placeholder URLs**: `example.com`, `your-site.com`, `brand.com`, and similar patterns
- **Unsubstantiated superlatives**: "best", "leading", "top", "#1" without qualifying evidence
- **Made-up entity citations**: "A Harvard study found...", "According to Forrester..." when no actual source is provided
- **Missing hedging on forward-looking claims**: Predictions and projections stated as facts without "expected", "projected", "estimated"

### What It Cannot Catch

This is critical to understand. The detector identifies *patterns* that correlate with hallucination. It cannot verify factual accuracy.

- **Factually incorrect but plausible statistics**: "23% of marketers use AI" is plausible but might be 27% or 19%. The detector sees a cited percentage and passes it.
- **Outdated data presented as current**: A 2021 stat with a 2021 citation looks valid to the detector even if the data is stale.
- **Subtle misrepresentations**: Cherry-picked data, misleading comparisons, or out-of-context quotes.
- **Domain-specific inaccuracies**: Industry jargon used incorrectly, technical claims that sound right but are wrong.

### False Positive Scenarios

- **Legitimate statistics with citation in a different paragraph**: The detector checks within a 2-sentence window. If the citation is 3+ sentences away, it may flag the stat.
- **Intentional superlatives in opinion/editorial content**: "Our best quarter ever" in a CEO letter is legitimate but may trigger the superlative detector.
- **Brand names that look like placeholders**: A brand literally named "YourBrand" or "CompanySite" will trigger placeholder patterns.

### Reducing False Positives

1. Always cite sources within 2 sentences of any statistic
2. Use explicit attribution phrases: "according to", "per", "based on", "as reported by"
3. Add dates to time-sensitive claims: "In Q4 2025, conversions increased by 47%"
4. Use hedging language for projections: "projected to reach", "expected to grow", "estimated at"
5. Qualify superlatives: "the leading platform in our category" rather than just "the leading platform"

---

## 5. Claim Verification

The claim-verifier extracts verifiable claims from content and fuzzy-matches them against a user-provided evidence file. This is the only eval dimension that requires external input (the evidence JSON).

### Preparing Evidence Files

Evidence files are JSON with this structure:

```json
{
    "evidence": [
        {
            "claim": "50% increase in conversions",
            "source": "GA4 Q4 2025 report",
            "date": "2025-12-31",
            "verified": true
        },
        {
            "claim": "Trusted by 500+ companies",
            "source": "CRM customer count",
            "date": "2025-11-15",
            "verified": true
        }
    ]
}
```

Each item needs: `claim` (the text of the claim as you would write it), `source` (where the data comes from), `date` (when it was verified), and `verified` (boolean -- is this confirmed?).

### Building an Evidence Library

Build your evidence file incrementally from real data sources:

- **Analytics**: Export key metrics from GA4, Search Console, ad platforms. Record exact numbers with dates.
- **Awards/Certifications**: Document award name, granting body, date received, and any expiration.
- **Customer counts**: Pull from CRM. Update quarterly.
- **Financial claims**: Use official financial reports. Mark clearly if estimates vs. actuals.
- **Testimonials**: Record customer name, quote, date, and consent status.
- **Performance claims**: Screenshot or export the specific report that backs each claim.

### Match Confidence Levels

| Level | Fuzzy Match Score | Evidence Status | Meaning |
|-------|-------------------|-----------------|---------|
| **Verified** | 0.80 or higher | `verified: true` | Claim matches evidence and evidence is confirmed |
| **Partially verified** | 0.60--0.79 | Any | Claim is similar to evidence but not an exact match. Numbers may differ slightly. |
| **Unverified** | Below 0.60 or no match | N/A | No evidence found for this claim. It might be true but is not documented. |
| **Contradicted** | 0.60 or higher | Numbers conflict | Claim matches evidence text but the numbers are different (e.g., "50% increase" vs. evidence showing "32% increase"). |

### Best Practices

- Update evidence files quarterly -- stale evidence leads to false "unverified" results
- Include the date for every evidence item so time-sensitive claims can be flagged when they expire
- Mark expired claims explicitly (set `verified: false` with a note) rather than deleting them
- Store evidence files at `~/.claude-marketing/brands/{slug}/evidence/` for persistence across sessions
- Separate evidence by domain: `evidence-metrics.json`, `evidence-awards.json`, `evidence-customers.json`

---

## 6. Output Validation

The output-validator checks content against structural schemas. It verifies that required sections are present, word counts are within bounds, formatting rules are followed, and no placeholder text remains.

### Built-in Schemas

| Schema | Required Sections | Min Words | Max Words | Format Rules |
|--------|-------------------|-----------|-----------|--------------|
| `blog_post` | title, introduction, body, conclusion | 300 | -- | has_headings, has_paragraphs |
| `email` | subject_line, body, cta | 50 | -- | has_cta, has_subject |
| `ad_copy` | headline, body, cta | 10 | 150 | has_cta |
| `social_post` | body | 5 | 500 | -- |
| `landing_page` | headline, value_proposition, body, cta | 100 | -- | has_headings, has_cta |
| `press_release` | headline, dateline, body, boilerplate, contact | 200 | -- | has_headings, has_paragraphs |
| `content_brief` | objective, target_audience, key_messages, outline | 100 | -- | has_headings |
| `campaign_plan` | objective, strategy, channels, timeline, budget, kpis | 300 | -- | has_headings, has_paragraphs |

### Creating Custom Schemas

Save a JSON file with your custom schema and pass it via `--custom-schema`:

```json
{
    "required_sections": ["headline", "hero_copy", "features", "testimonials", "pricing", "cta"],
    "min_words": 200,
    "max_words": 1500,
    "format_rules": ["has_headings", "has_cta", "has_paragraphs"],
    "description": "SaaS product page with pricing table"
}
```

### Section Detection

The validator uses fuzzy matching on markdown headings (`##`, `###`) and bold labels (`**Section Name**`) to identify sections. The `SECTION_ALIASES` mapping handles common variations (e.g., "intro" matches "introduction", "next steps" matches "cta").

### Common Validation Failures

- **Missing CTAs**: The most frequent failure. Always include an explicit call-to-action section even in informational content.
- **Placeholder text left in**: `[Insert company name]`, `{brand}`, `Lorem ipsum`, `TBD` all trigger deductions.
- **Word count violations**: Ad copy exceeding 150 words, blog posts under 300 words. Check the schema limits before writing.
- **Missing required sections**: Press releases commonly miss the boilerplate or contact section. Campaign plans often skip the KPIs section.

---

## 7. Quality Tracking and Regression

The quality-tracker persists every eval result and computes rolling statistics. This is how you detect quality drift over time.

### How Baselines Work

- Baselines are computed as the **30-day rolling average** per content type per scoring dimension
- A minimum of 5 evals is required before a baseline is established
- Baselines update automatically every time a new eval is logged
- Storage: `~/.claude-marketing/brands/{slug}/quality/evals/eval-{timestamp}.json`

### Regression Alerts

Regression is flagged when either condition is met:

1. **Rolling average drop**: The last-5-eval average for any dimension drops more than **10 points** below the 30-day baseline
2. **Single dimension spike**: Any single eval scores more than **15 points** below the baseline for a dimension

### Interpreting Trends

Use `quality-tracker.py --action get-trends --days 30` to see weekly buckets:

- **Improving**: Weekly average rising by 3+ points per week for 2+ consecutive weeks
- **Stable**: Weekly average within +/- 3 points of the baseline
- **Declining**: Weekly average dropping by 3+ points per week for 2+ consecutive weeks

### Acting on Regression

When a regression alert fires, investigate in this order:

1. **Recent prompt changes**: Did an agent's instructions change? Did a workflow update alter how content is generated?
2. **Brand profile updates**: Was the brand voice profile modified? Did industry or audience targeting change?
3. **Agent instruction changes**: Were any agent markdown files edited recently?
4. **Evidence file staleness**: Are claim verification scores dropping because evidence is outdated?
5. **Content type shift**: Are you generating more of a content type that naturally scores lower (e.g., short social posts vs. long blog posts)?

---

## 8. Integration with the Approval Workflow

The eval system is wired into the approval framework documented in `approval-framework.md`.

### Automatic Eval During Execution

- The `execution-coordinator` agent calls `eval-runner.py --action run-quick` before creating an approval record for any content
- The eval grade is included in the approval record so human reviewers have quality context
- If the composite score falls below the **auto-reject threshold** (default 40, configurable via eval-config-manager), execution is blocked automatically

### Content Scoring Hooks

The `hooks.json` PreToolUse hook for Write and Edit operations runs a lightweight hallucination check in real-time. This catches obvious fabrication indicators during content generation, not just at eval time.

### Approval Record Integration

Every approval record includes:
- `eval_grade`: The letter grade from the most recent eval
- `eval_composite`: The numeric composite score
- `eval_flags`: Array of specific issues flagged by any evaluator
- `eval_timestamp`: When the eval was run

Human reviewers should pay special attention to items where `eval_flags` is non-empty, even if the composite score is acceptable.

---

## 9. Eval Configuration Recommendations

Use `eval-config-manager.py` to tune weights and thresholds per brand.

### By Industry

| Industry | Hallucination | Claim Verification | Content Quality | Brand Voice | Structure | Readability |
|----------|--------------|-------------------|----------------|-------------|-----------|-------------|
| Healthcare | 0.30 | 0.25 | 0.15 | 0.15 | 0.10 | 0.05 |
| Financial Services | 0.25 | 0.25 | 0.15 | 0.15 | 0.10 | 0.10 |
| Legal Services | 0.25 | 0.25 | 0.15 | 0.15 | 0.15 | 0.05 |
| B2B Technology | 0.15 | 0.15 | 0.30 | 0.15 | 0.10 | 0.15 |
| Consumer/Lifestyle | 0.15 | 0.10 | 0.20 | 0.25 | 0.10 | 0.20 |
| E-commerce | 0.20 | 0.15 | 0.20 | 0.20 | 0.15 | 0.10 |
| Education | 0.25 | 0.20 | 0.20 | 0.10 | 0.15 | 0.10 |

### By Content Type

| Content Type | Hallucination | Claim Verification | Content Quality | Brand Voice | Structure | Readability |
|-------------|--------------|-------------------|----------------|-------------|-----------|-------------|
| Ad copy | 0.30 | 0.15 | 0.20 | 0.20 | 0.05 | 0.10 |
| Blog posts | 0.20 | 0.15 | 0.25 | 0.20 | 0.10 | 0.10 |
| Press releases | 0.20 | 0.25 | 0.15 | 0.15 | 0.15 | 0.10 |
| Social posts | 0.25 | 0.10 | 0.20 | 0.25 | 0.05 | 0.15 |
| Landing pages | 0.20 | 0.20 | 0.20 | 0.15 | 0.15 | 0.10 |
| Emails | 0.20 | 0.15 | 0.20 | 0.20 | 0.15 | 0.10 |
| Campaign plans | 0.10 | 0.10 | 0.30 | 0.10 | 0.25 | 0.15 |

### By Brand Maturity

- **New brands** (first 30 days): Use lower minimum thresholds (50-60) while building baselines. Focus on establishing consistent content production before tightening quality gates. Set auto-reject at 35.
- **Growing brands** (30-90 days): Gradually increase minimum thresholds (60-70) as baselines stabilize. Start enforcing brand voice scores. Set auto-reject at 40.
- **Established brands** (90+ days): Use higher thresholds (70-80) with strict enforcement. Regression alerts should trigger immediate investigation. Set auto-reject at 45-50.

---

## 10. LLM-as-Judge Limitations

The eval system uses deterministic heuristics (pattern matching, fuzzy matching, word counting) rather than LLM-based judgment for scoring. This is intentional -- deterministic checks are consistent, fast, and free. However, it means the eval system has inherent blind spots.

### What Still Requires Human Judgment

- **Domain-specific factual accuracy**: Is that medical claim actually correct? Is that legal interpretation sound? The eval system checks if claims are *cited*, not if they are *true*.
- **Cultural appropriateness**: Tone, humor, and references that may be inappropriate for specific cultural contexts. No heuristic can reliably detect this.
- **Strategic alignment**: Does this content support the campaign goal? Is it positioned correctly against competitors? These are strategic questions beyond pattern matching.
- **Creative quality and originality**: Is this content genuinely insightful, or is it a competent rehash of existing ideas? Creativity is not scorable by heuristic.
- **Emotional resonance**: Does this content connect with the reader emotionally? Engagement is felt, not measured by word patterns.

### The Quality-Assurance Agent

The `quality-assurance` agent adds LLM-based reasoning on top of script scores. It reads the eval results, examines the flagged items, and provides qualitative commentary. This adds nuance that scripts cannot provide -- but the agent's judgments should be verified for high-stakes content because LLM reasoning can itself be inconsistent.

### Recommended Workflow

1. **Automated eval first**: Run `eval-runner.py` to get quantitative scores and flagged items
2. **Agent review for flagged items**: Let the quality-assurance agent analyze any flags or low-scoring dimensions
3. **Human review for high-stakes content**: Any content that is regulated, high-spend, or high-visibility should get human eyes regardless of score
4. **Final approval**: Use the approval workflow to confirm publication readiness

---

## 11. Prompt A/B Testing

The prompt-ab-tester tracks variant performance over time. Use it when you want to compare different approaches to the same content task.

### When to Test

- **Subject lines**: "Direct benefit" vs. "Curiosity gap" vs. "Question-based"
- **Headlines**: Different angles on the same topic
- **CTAs**: "Start free trial" vs. "See pricing" vs. "Book a demo"
- **Email body approaches**: Long-form storytelling vs. short-form bullet points
- **Ad copy styles**: Feature-led vs. benefit-led vs. social-proof-led

### Setting Up a Test

```
python prompt-ab-tester.py --action create-test --test-name email-subject-q1 \
    --data '{"description":"Testing email subject line styles for Q1 campaign"}'
```

### Logging Variants

Run each variant through `eval-runner.py`, then log the scores:

```
python prompt-ab-tester.py --action log-variant --test-name email-subject-q1 \
    --variant A --data '{"description":"Direct benefit","scores":{"content_quality":85,"brand_voice":78,"composite":82}}'

python prompt-ab-tester.py --action log-variant --test-name email-subject-q1 \
    --variant B --data '{"description":"Question-based","scores":{"content_quality":78,"brand_voice":82,"composite":80}}'
```

### Minimum Sample Sizes

| Sample Size | Reliability |
|-------------|-------------|
| 1--4 evals per variant | Insufficient. Results are anecdotal. |
| 5--9 evals per variant | Directional signal. Useful for eliminating clearly worse variants. |
| 10+ evals per variant | Reliable comparison. Differences of 5+ points are meaningful. |

### Interpreting Results

- **Greater than 10-point difference**: Significant. The higher-scoring variant is meaningfully better.
- **5--10 point difference**: Likely significant. Use the higher-scoring variant but consider retesting with more samples.
- **Less than 5-point difference**: Inconclusive. The variants are effectively equivalent. Choose based on strategic preference.

### Best Practices

1. **Test one variable at a time**: If you change both the headline and the CTA, you cannot attribute score differences to either change.
2. **Use consistent evaluation criteria**: All variants in a test should use the same eval type (run-full, run-quick) with the same weights.
3. **Log all variants**: Even the losing variants have value. They show what does not work and inform future content strategy.
4. **Name tests descriptively**: `email-subject-q1-curiosity-vs-benefit` is better than `test-1`.
5. **Archive completed tests**: Use the results to update content guidelines and inform future A/B tests.

---

## Quick Reference: Script Commands

```bash
# Full eval with all options
python eval-runner.py --action run-full --file draft.md --evidence claims.json --schema blog_post --brand acme --log

# Quick eval during drafting
python eval-runner.py --action run-quick --text "Your draft content..."

# Compliance eval for regulated content
python eval-runner.py --action run-compliance --file page.md --evidence facts.json --schema landing_page

# Standalone hallucination check
python hallucination-detector.py --action detect --file draft.md

# Extract claims without verifying
python claim-verifier.py --action extract-claims --text "We grew revenue by 3x..."

# Verify claims against evidence
python claim-verifier.py --action verify --file draft.md --evidence evidence.json

# Validate structure against schema
python output-validator.py --action validate --file page.md --schema landing_page

# List available schemas
python output-validator.py --action list-schemas

# Get quality trends for last 30 days
python quality-tracker.py --action get-trends --days 30

# Check for quality regression
python quality-tracker.py --action check-regression

# Get current eval config
python eval-config-manager.py --action get-config

# Set hallucination threshold for ad copy
python eval-config-manager.py --action set-threshold --dimension hallucination --threshold 80 --content-type ad_copy

# Create an A/B test
python prompt-ab-tester.py --action create-test --test-name headline-test --data '{"description":"Testing headline styles"}'

# Get A/B test results
python prompt-ab-tester.py --action get-results --test-name headline-test
```
