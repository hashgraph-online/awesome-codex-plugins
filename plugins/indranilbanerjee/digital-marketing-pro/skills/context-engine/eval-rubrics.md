# Evaluation Rubrics -- Scoring Criteria for All Dimensions

Detailed scoring rubrics for the six eval dimensions used by `eval-runner.py`. Each rubric defines what constitutes a given score range, with concrete examples. Use these rubrics to understand why content received a particular score and what to fix.

---

## 1. Hallucination Risk Score (0--100)

Measures the likelihood that content contains fabricated statistics, fake citations, placeholder URLs, or unsubstantiated claims. Higher scores mean lower risk.

| Score Range | Risk Level | Description | Example |
|-------------|------------|-------------|---------|
| **90--100** | Minimal risk | All statistics are cited within 2 sentences. No placeholder URLs. No unsubstantiated superlatives. Forward-looking claims use proper hedging. Attribution phrases present throughout. | "According to our Q4 2025 GA4 report, conversions increased by 47% quarter-over-quarter, driven primarily by organic search improvements." |
| **75--89** | Low risk | Minor citation gaps or occasional missing attribution, but no fabricated data. Some statistics may lack immediate sourcing but are plausible and verifiable. | "Conversions increased significantly last quarter." (Missing the specific number is actually safer than fabricating one -- vague but honest.) |
| **60--74** | Moderate risk | Some unverified statistics present. A few superlative claims without backing. Mild hedging issues on forward-looking statements. Human review recommended before publication. | "Our platform has helped thousands of businesses grow their revenue." (Vague but not fabricated. The "thousands" claim should be verified.) |
| **40--59** | High risk | Multiple unverified statistics. Placeholder URLs detected. Several unsubstantiated claims. Specific numbers appear without any source attribution. Revision required. | "73% of marketers agree our tool is the best, leading to 5x ROI improvements within the first month." (No source for 73%, "the best" is unsubstantiated, 5x ROI is unverified.) |
| **0--39** | Critical risk | Fabricated statistics with fake citations. Multiple superlative claims without any evidence. Placeholder URLs throughout. Made-up entity references. Do not publish. Auto-reject triggered. | "A Harvard Business School study confirmed our product increases conversions by 500%, making us the #1 platform trusted by 10,000+ companies worldwide." (No such study exists, 500% is fabricated, #1 is unsubstantiated, 10,000 is unverified.) |

**Key patterns that reduce scores**: Uncited percentages (-5 to -10 each), placeholder URLs (-10 each), unqualified superlatives (-5 each), fake entity citations (-15 each), missing hedging on projections (-5 each).

---

## 2. Claim Verification Score (0--100)

Measures how well the verifiable claims in content match against the provided evidence file. Only scored when an evidence file is supplied.

| Score Range | Level | Description |
|-------------|-------|-------------|
| **90--100** | Fully verified | All extracted claims match evidence items with high confidence (fuzzy match >= 0.80). Evidence items are marked as verified. Source dates are current. |
| **70--89** | Mostly verified | Most claims verified. Some minor claims (e.g., "growing team", "global presence") are unverified but low-risk. Core quantitative claims all have evidence. |
| **50--69** | Mixed | Roughly half of claims are verified. Some important quantitative claims lack evidence. Human review needed to determine which unverified claims to keep, revise, or remove. |
| **30--49** | Mostly unverified | Most claims lack matching evidence. Multiple quantitative claims cannot be confirmed. Significant evidence gaps that must be filled before publication. |
| **0--29** | Unverified or contradicted | Claims either have no evidence at all, or evidence contradicts the claims (e.g., content says "50% increase" but evidence shows 32%). Block publication until evidence is provided or claims are corrected. |

**Scoring formula**: `(verified_count * 100 + partially_verified_count * 60) / total_claims`. If no verifiable claims are found in the content, score defaults to 100 with a note explaining that no claims required verification.

**What counts as a verifiable claim**: Percentages, dollar amounts, multipliers, customer/user counts, trust claims ("trusted by X"), certifications, rankings, compliance claims, and financial figures. General qualitative statements ("we care about quality") are not extracted as verifiable claims.

---

## 3. Output Structure Score (0--100)

Measures whether content matches the expected structural schema. Only scored when a schema is specified.

| Score Range | Level | Description |
|-------------|-------|-------------|
| **90--100** | Complete | All required sections present and detected. Word count within bounds. All format rules satisfied (headings, paragraphs, CTAs as required). No placeholder text detected. |
| **70--89** | Minor gaps | Minor section name variations that are still detected via fuzzy matching. Formatting is mostly correct. Word count is within 10% of bounds. No placeholder text. |
| **50--69** | Partial | Missing 1--2 required sections, or word count is 10--25% outside bounds, or minor formatting issues (e.g., no headings when `has_headings` is required). |
| **30--49** | Significant gaps | Missing multiple required sections. Significant word count violation (more than 25% outside bounds). Placeholder text detected (e.g., `[Insert here]`, `{company_name}`, `Lorem ipsum`). |
| **0--29** | Fundamentally wrong | Content does not match the schema at all. Most required sections are missing. Structure bears no resemblance to the expected content type. |

**Common deductions**: Missing required section (-15 per section), placeholder text found (-10 per instance), word count under minimum (-10), word count over maximum (-5), missing required heading format (-5), missing CTA when `has_cta` is required (-15).

---

## 4. Content Quality Score (0--100)

Measures overall writing quality: clarity, coherence, depth, actionability, and engagement. Scored by `content-scorer.py` using the weighted rubric defined in `scoring-rubrics.md`.

| Dimension | Weight | 0 (Fail) | 5 (Weak) | 10 (Good) | 15--20 (Excellent) |
|-----------|--------|----------|----------|-----------|-------------------|
| **Audience Relevance** | 20% | Wrong audience entirely | Generic, could be for anyone | Addresses target persona | Deeply resonates with specific persona's pain points and jobs-to-be-done |
| **Readability** | 15% | Grade level wildly inappropriate | 3+ grades off target | Within 1 grade of target | Perfect grade level for audience (B2C: 6th--8th, B2B: 10th--12th) |
| **SEO Optimization** | 15% | No keyword targeting | Keyword present but poorly placed | Primary keyword in title, H1, first 100 words, meta | Full optimization: keyword clusters, internal links, schema, intent match |
| **Originality** | 15% | Rehashed generic content | Some unique angles | Original insights or data points | First-hand experience, proprietary data, unique frameworks |
| **Brand Voice Match** | 15% | Completely off-brand | Partially aligned | Consistent with brand voice profile | Unmistakably on-brand across all 4 voice dimensions |
| **CTA Effectiveness** | 10% | No CTA or irrelevant CTA | CTA present but weak/generic | Clear CTA aligned with funnel stage | Compelling, specific, urgency-appropriate CTA with value proposition |
| **Compliance** | 10% | Violations present (legal risk) | Missing optional best practices | All required disclaimers present | Full compliance + proactive best practices (accessibility, disclosure) |

**Score interpretation**: 85--100 = Publish-ready. 70--84 = Minor revisions. 50--69 = Major revisions. Below 50 = Rewrite.

---

## 5. Brand Voice Score (0--100)

Measures alignment with the active brand's voice profile (formality, energy, humor, authority). Scored by `brand-voice-scorer.py` using the 9-point brand context system.

| Score Range | Level | Description |
|-------------|-------|-------------|
| **90--100** | Unmistakably on-brand | Tone, vocabulary, sentence structure, and personality markers all match the brand profile. Content could only have come from this brand. |
| **75--89** | Consistently on-brand | Overall tone is correct. Minor vocabulary variations that do not break brand consistency. Personality markers are present. |
| **60--74** | Partially on-brand | Tone is generally appropriate but inconsistent. Some sections match the brand voice while others drift. Vocabulary gaps. |
| **40--59** | Mostly off-brand | Tone does not match the brand profile. Wrong formality level, mismatched energy, or inappropriate humor. Content reads as generic. |
| **0--39** | Completely off-brand | Content contradicts the brand voice profile. Wrong audience register, clashing personality, or tone-deaf messaging. |

**What the scorer checks**: Formality level (casual to formal on 1--10 scale), energy level (subdued to energetic), humor level (serious to playful), authority level (peer to expert). Each dimension is compared against the brand profile values with tolerance thresholds.

---

## 6. Readability Score (0--100)

Measures how accessible the content is to the target audience. Scored by `readability-analyzer.py` using multiple readability metrics.

| Score Range | Level | Description |
|-------------|-------|-------------|
| **90--100** | Optimal | Flesch-Kincaid grade matches target audience perfectly. Average sentence length is 15--20 words. Paragraphs are 3--5 sentences. Jargon is either absent or explained on first use. |
| **75--89** | Good | Grade level is within 1--2 grades of target. Sentence length mostly appropriate. Occasional long paragraphs or unexplained jargon. |
| **60--74** | Acceptable | Grade level is 2--3 grades off target. Some sentences are too complex. Jargon density is noticeable. Paragraphs are inconsistently sized. |
| **40--59** | Difficult | Grade level is significantly off target. Long, complex sentences dominate. Dense jargon without explanation. Wall-of-text paragraphs. |
| **0--39** | Inaccessible | Content is unreadable for the target audience. Academic-level complexity for a consumer audience, or oversimplified for a technical audience. |

**Target readability by audience**: B2C general (6th--8th grade Flesch-Kincaid), B2C premium (8th--10th grade), B2B general (10th--12th grade), B2B technical (12th--14th grade), Academic/research (14th+ grade).

---

## 7. Composite Score Interpretation and Decision Matrix

The composite score is a weighted sum of all evaluated dimensions. It determines the letter grade and the recommended action.

| Grade | Score | Publish? | Revise? | Rewrite? | Human Review Required? |
|-------|-------|----------|---------|----------|----------------------|
| A+ | 95--100 | Yes | No | No | Optional |
| A | 90--94 | Yes | Optional | No | Optional |
| A- | 85--89 | Yes | Recommended | No | No, unless regulated |
| B+ | 80--84 | Conditional | Yes | No | Recommended for external content |
| B | 75--79 | Conditional | Yes | No | Yes, for flagged items |
| B- | 70--74 | No | Yes | No | Yes |
| C+ | 65--69 | No | Yes, significant | No | Yes |
| C | 60--64 | No | Consider rewrite | Maybe | Yes |
| C- | 55--59 | No | No | Yes | Yes |
| D | 40--54 | No | No | Yes | Yes |
| F | <40 | Blocked | No | Yes, from scratch | Mandatory |

**"Conditional" publishing**: Content in the B to B+ range can be published if the specific flagged items have been reviewed and accepted. Check which dimensions are pulling the score down -- a B+ with a low hallucination score is more concerning than a B+ with a low readability score.

---

## 8. Content Type-Specific Weight Recommendations

Default weights (from `eval-runner.py` FULL_EVAL_WEIGHTS) are balanced for general use. Override per content type for more targeted evaluation.

| Content Type | Content Quality | Brand Voice | Hallucination | Claim Verification | Structure | Readability |
|-------------|----------------|-------------|--------------|-------------------|-----------|-------------|
| **blog_post** | 0.25 | 0.20 | 0.20 | 0.15 | 0.10 | 0.10 |
| **email** | 0.20 | 0.20 | 0.20 | 0.15 | 0.15 | 0.10 |
| **ad_copy** | 0.20 | 0.20 | 0.30 | 0.15 | 0.05 | 0.10 |
| **social_post** | 0.20 | 0.25 | 0.25 | 0.10 | 0.05 | 0.15 |
| **landing_page** | 0.20 | 0.15 | 0.20 | 0.20 | 0.15 | 0.10 |
| **press_release** | 0.15 | 0.15 | 0.20 | 0.25 | 0.15 | 0.10 |
| **content_brief** | 0.30 | 0.10 | 0.10 | 0.10 | 0.25 | 0.15 |
| **campaign_plan** | 0.30 | 0.10 | 0.10 | 0.10 | 0.25 | 0.15 |

**Rationale for notable overrides**:
- **Ad copy gets 0.30 hallucination weight**: Short content with high external visibility. A single fabricated claim in a 50-word ad is far more damaging than in a 1,500-word blog post.
- **Social posts get 0.25 brand voice weight**: Social media is where brand personality is most visible. Off-brand social posts erode brand consistency quickly.
- **Press releases get 0.25 claim verification weight**: Press releases are cited by journalists and become the public record. Every claim must be verifiable.
- **Content briefs and campaign plans get 0.25 structure weight**: These are planning documents. Their value comes from completeness and organization, not polish.

---

## 9. Industry-Specific Eval Considerations

Beyond weight adjustments, certain industries require additional eval vigilance in specific areas.

### Healthcare and Pharmaceuticals
- **Critical dimensions**: Hallucination (0.30), claim verification (0.25)
- **Additional checks**: No disease treatment claims without FDA disclaimers. No "cures" or "prevents" language for supplements. HIPAA-compliant patient references (no PII). Adverse effect disclosures where required.
- **Auto-reject triggers**: Any unverified efficacy claim. Missing required disclaimers. Unauthorized health advice.

### Financial Services and Insurance
- **Critical dimensions**: Hallucination (0.25), claim verification (0.25)
- **Additional checks**: No guaranteed returns language ("will earn", "guaranteed profit"). SEC/FCA disclaimer presence. Past performance disclaimers on investment content. APR/fee disclosure accuracy. No misleading comparison claims.
- **Auto-reject triggers**: Guaranteed return claims. Missing regulatory disclaimers. Fabricated performance figures.

### Legal Services
- **Critical dimensions**: Hallucination (0.25), claim verification (0.25), structure (0.15)
- **Additional checks**: No unauthorized practice of law. Jurisdictional disclaimers. Attorney advertising notices where required. No outcome guarantees ("we will win your case"). Precise language -- legal marketing tolerates no ambiguity.
- **Auto-reject triggers**: Guaranteed case outcomes. Missing attorney advertising disclosures.

### Education and EdTech
- **Critical dimensions**: Claim verification (0.20), content quality (0.20)
- **Additional checks**: Accreditation claims must be verified against the accrediting body. Student outcome claims need substantiation (graduation rates, employment rates, salary data). No misleading enrollment promises.
- **Auto-reject triggers**: Fabricated accreditation claims. Unsubstantiated outcome statistics.

### Real Estate
- **Critical dimensions**: Hallucination (0.20), claim verification (0.20)
- **Additional checks**: Fair Housing Act compliance -- no discriminatory language targeting or excluding protected classes. Accurate property descriptions (square footage, bedroom count). No misleading neighborhood characterizations. Price accuracy.
- **Auto-reject triggers**: Fair housing violations. Fabricated property details.

### Food, Beverage, and Supplements
- **Critical dimensions**: Hallucination (0.25), claim verification (0.25)
- **Additional checks**: FDA labeling requirements for health claims. No "clinically proven" without actual clinical trials. Allergen disclosure. "Structure/function" claim boundaries (can say "supports immune health", cannot say "prevents colds"). Organic/non-GMO certification verification.
- **Auto-reject triggers**: Unauthorized health claims. Missing FDA disclaimers on supplements. Fabricated clinical trial references.

---

## Quick Reference: When to Override Defaults

Use `eval-config-manager.py --action set-weights` when:
- Your industry has specific compliance risks (see industry sections above)
- Your content type mix is dominated by one format (weight that format's priorities)
- You see recurring false flags in a dimension that matters less for your use case
- Your brand has matured past the baseline-building phase and you want stricter gates

Use `eval-config-manager.py --action set-threshold` when:
- A specific dimension consistently underperforms and you want a minimum floor
- Regulatory requirements demand a hard minimum on hallucination or claim verification
- You want content-type-specific minimums (e.g., hallucination >= 80 for ad_copy only)

Use `eval-config-manager.py --action set-auto-reject` when:
- You want to change the composite score below which content is automatically blocked
- Default is 40 (grade F). Regulated industries should consider 45--50.
