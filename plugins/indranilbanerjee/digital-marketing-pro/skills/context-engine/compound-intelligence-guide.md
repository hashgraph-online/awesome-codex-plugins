# Compound Intelligence Guide

Reference knowledge for building marketing intelligence that improves over time. Every campaign, test, and observation should feed back into a system that makes the next decision better than the last.

---

## 1. Intelligence Graph Architecture

### Core Structure
The intelligence graph is a network of marketing insights connected by relationships:
- **Nodes**: Individual insights or learnings, each stored as a structured record with defined fields
- **Edges**: Relationships between insights — same audience, same channel, same objective, supporting evidence, contradicting evidence, causal relationship, temporal sequence
- **Metadata per node**: Confidence score (0.0-1.0), source agent (which specialist generated the insight), timestamp (when observed), revalidation date (when to recheck), context conditions (brand, industry, audience, channel, season, budget level)

### Why a Graph, Not a List
Lists of insights are flat and disconnected. A graph reveals patterns: "These 5 insights all relate to the developer audience on LinkedIn — together they form a playbook." It also surfaces contradictions: "These 2 insights about email timing disagree — they were observed in different seasons, which may explain the conflict."

### Node Types
- **Observation**: Raw data point. "Email campaign #47 had 23% open rate with emoji subject line"
- **Hypothesis**: Proposed explanation. "Emoji subject lines increase open rates for developer audience"
- **Validated Learning**: Confirmed pattern with sufficient evidence. "Emoji subject lines increase open rates by 8-12% for developer audience (confidence: 0.82, based on 7 campaigns)"
- **Playbook Rule**: Actionable instruction derived from validated learnings. "When writing email subject lines for developer audience, include 1 relevant emoji — expected open rate lift: 8-12%"
- **Anti-pattern**: Validated negative insight. "Avoid all-caps subject lines for enterprise audience — 15% lower open rate (confidence: 0.75, based on 5 campaigns)"

### Edge Types
- **Supports**: One insight provides evidence for another
- **Contradicts**: One insight conflicts with another (triggers investigation)
- **Extends**: One insight adds nuance or scope to another
- **Supersedes**: A newer insight replaces an older one (the older one is archived, not deleted)
- **Context-dependent**: Two insights that appear to contradict actually apply in different contexts

---

## 2. Learning Structure Lifecycle

### Stage 1: Observation
A single data point from a campaign, test, or analysis. Structured as:
- **What happened**: "Email open rates dropped 15% when we changed from question-format to statement-format subject lines"
- **Context**: Brand, audience segment, channel, time period, sample size
- **Source**: Which agent or analysis generated this observation
- **Initial confidence**: 0.5 (single observation, no corroboration)

### Stage 2: Hypothesis
When 2+ observations suggest a pattern, form a hypothesis:
- **Pattern statement**: "Question-format subject lines outperform statement-format for our B2B audience"
- **Supporting observations**: Links to the observations that suggest this pattern
- **Predicted outcome**: "If we switch back to question-format, open rates will recover by 10-15%"
- **Test design**: How to validate — "A/B test question vs statement format on next 3 email sends"
- **Confidence**: 0.6 (pattern emerging but unvalidated)

### Stage 3: Evidence Accumulation
Run the test or gather additional observations:
- Each confirming observation increases confidence (+0.1, capped at +0.3 per evidence)
- Each contradicting observation decreases confidence (-0.2)
- Track the evidence trail — every observation that supports or contradicts is linked as an edge

### Stage 4: Validated Learning
When confidence exceeds 0.8 threshold:
- **Formal statement**: "For B2B SaaS audience: question-format email subject lines achieve 12% higher open rates than statement-format, based on 7 campaigns across 3 months (confidence: 0.82)"
- **Conditions**: Specify when this applies (audience, channel, content type, season)
- **Boundaries**: Specify when this does NOT apply or is untested
- **Revalidation date**: Set 6-month check to confirm the learning still holds

### Stage 5: Playbook Rule
Validated learnings with confidence >0.85 are promoted to playbook rules:
- **Actionable instruction**: "When writing email subject lines for B2B SaaS audience, use question format. Expected lift: 10-14% open rate increase"
- **Exceptions**: Known conditions where the rule does not apply
- **Override conditions**: When to deviate (e.g., transactional emails, urgent announcements)

---

## 3. Confidence Scoring System

### Score Calculation
| Event | Score Change |
|-------|-------------|
| Initial observation | 0.50 (starting point) |
| Each supporting observation | +0.10 (max +0.30 from additional evidence) |
| Each contradicting observation | -0.20 |
| Time decay | -0.01 per month without revalidation |
| Context breadth bonus | +0.10 if validated across 3+ campaigns |
| Cross-agent confirmation | +0.15 if observed by a different agent type |
| Large sample size bonus | +0.05 if based on >10,000 data points |
| Causal validation (experiment) | +0.10 if confirmed via controlled experiment |

### Confidence Thresholds
- **>0.85**: High confidence. Include in playbooks as default rules. Agents should follow these unless context explicitly contradicts
- **0.70-0.85**: Moderate-high confidence. Include in recommendations with supporting context. "Based on 5 prior campaigns, we recommend..."
- **0.50-0.70**: Moderate confidence. Suggest but flag as developing. "Early evidence suggests... recommend testing"
- **0.30-0.50**: Low confidence. Monitor for additional evidence. Do not include in recommendations
- **<0.30**: Auto-archive. Insufficient evidence or too much contradiction. Retain in graph for historical reference but exclude from active intelligence

### Confidence Decay and Revalidation
Every insight loses 0.01 confidence per month without revalidation. This ensures stale insights gradually lose influence. Revalidation methods:
- **Passive**: New campaign data confirms the insight (automatic, no effort required)
- **Active**: Deliberately test the insight in a new campaign (for high-value insights approaching threshold)
- **Review**: Analyst or agent reviews the insight against current market conditions (quarterly process)

---

## 4. Cross-Agent Distribution Rules

### When to Share Insights
When one specialist agent discovers an insight, determine relevance for other agents:
- **Content creator discovers audience preference** (e.g., "developer audience prefers code examples over abstract explanations") -> Distribute to email-specialist, social-media-manager, seo-specialist
- **Analytics analyst discovers channel pattern** (e.g., "LinkedIn drives 3x more qualified leads than Meta for enterprise audience") -> Distribute to marketing-strategist, media-buyer
- **SEO specialist finds ranking format** (e.g., "comparison posts rank 40% better than single-product reviews in SaaS category") -> Distribute to content-creator
- **Media buyer finds cost pattern** (e.g., "CPMs drop 30% on Tuesdays for B2B audiences on LinkedIn") -> Distribute to social-media-manager, marketing-strategist

### Distribution Filter
An insight must share at least one context dimension with the receiving agent's domain:
- **Audience overlap**: Both agents serve the same audience segment
- **Channel overlap**: Both agents operate on the same platform
- **Objective overlap**: Both agents work toward the same campaign objective
- **Industry overlap**: Both agents work in the same vertical

If zero dimensions overlap, do not distribute — the insight is likely irrelevant and adds noise.

### Distribution Format
When sharing cross-agent, include:
- The insight statement (one sentence)
- Confidence score
- Relevance explanation ("This is relevant to your work because...")
- Source evidence count
- Suggested action for the receiving agent

---

## 5. Compounding Advantage Quantification

### Brand Intelligence Score
`Score = total_validated_learnings * average_confidence * recency_factor`

Where recency_factor = average of (0.99^months_since_validation) across all learnings.

### Intelligence Maturity Stages
| Stage | Campaigns | Score Range | Characteristics |
|-------|-----------|-------------|----------------|
| Cold start | 0-5 | 0-10 | Pure industry benchmarks. No brand-specific intelligence. Every recommendation is generic |
| Early learning | 5-25 | 10-75 | Basic patterns emerging. First validated learnings about audience and channel performance. Starting to diverge from generic advice |
| Pattern recognition | 25-100 | 75-500 | Robust insights across primary channels. Playbook rules forming. Recommendations are measurably better than generic benchmarks |
| Intelligence moat | 100-500 | 500-2000 | Cross-channel insights, seasonal patterns, audience micro-segments understood. Competitive advantage in speed and precision of marketing decisions |
| Compound advantage | 500+ | 2000+ | Every new campaign benefits from all prior learnings. The intelligence system itself becomes a strategic asset. Competitors without compound intelligence cannot match decision quality regardless of budget |

### The Moat Argument
A brand that has run 500 campaigns with compound intelligence has a structural advantage that cannot be replicated by a brand starting from zero, even with a larger budget. The accumulated understanding of what works for this specific audience, in this specific market, with this specific product, compounds over time. This is the primary long-term value proposition of the intelligence system.

---

## 6. Anti-Patterns to Avoid

### Overfitting to Small Samples
Require minimum 3 observations before promoting from observation to hypothesis. A single campaign result — even a spectacular one — is not a pattern. It may be driven by timing, audience composition, competitive absence, or random variance.

### Survivorship Bias
Track what did NOT work, not just what worked. The database of anti-patterns is as valuable as the playbook of best practices. "We tested 8 hook formats; 2 worked and 6 did not" is more valuable than "We found 2 hook formats that work."

### Correlation vs Causation
Tag every insight as "correlation" unless causally validated via controlled experiment (A/B test, holdout, geo-lift). Correlational insights are still useful for hypothesis generation but should not be treated as reliable playbook rules. Example: "Campaigns launched on Tuesdays perform better" may be correlation (you launch your best work on Tuesdays) rather than causation (Tuesdays are inherently better).

### Recency Bias
Weight insights by confidence score, not just by how recent they are. A validated learning from 6 months ago (confidence 0.85) is more reliable than a single observation from last week (confidence 0.50). Time decay handles the gradual loss of relevance without allowing recency to override evidence quality.

### Echo Chamber Effect
Actively seek disconfirming evidence. When a hypothesis has 4 supporting observations, deliberately look for conditions under which it fails. Test the hypothesis in a different audience segment, different channel, or different season. Insights that survive active attempts at disconfirmation are significantly more robust.

### Anecdote Elevation
A single impressive result does not constitute a reliable insight. "That one LinkedIn post went viral" does not mean the format, topic, or timing is a repeatable strategy. Require pattern-level evidence before changing standard operating procedures.

---

## 7. Agency Mode Intelligence

### Cross-Client Pattern Detection
When operating in agency mode (multiple brands), the intelligence system can detect patterns that no single-client system could see:
- **Industry benchmarks from real data**: "Across 12 SaaS clients, average email open rate is 22.4% — Client X at 18% is underperforming"
- **Channel effectiveness by vertical**: "LinkedIn outperforms Meta for B2B lead gen across 8 of 9 clients"
- **Seasonal patterns**: "Q4 CPMs increase 40-60% across all e-commerce clients — pre-plan budgets accordingly"

### Anonymization Requirements
Strip all client-identifying information before aggregating cross-client intelligence:
- Replace client names with anonymous identifiers
- Remove brand-specific creative details
- Aggregate metrics at the industry/audience level, not the campaign level
- Never share one client's specific performance data with another client

### Opt-In Shared Intelligence Pool
Clients can opt in to contribute anonymized insights and receive cross-client intelligence in return:
- **Contributors**: Their data (anonymized) improves the pool, and they receive the full benefit of cross-client patterns
- **Non-contributors**: Receive only industry benchmarks, not detailed cross-client insights
- **Firewall**: Client-specific intelligence is NEVER accessible to other clients, regardless of opt-in status. Only aggregated, anonymized patterns are shared

### Higher Confidence Thresholds
Cross-client insights require stronger evidence because they generalize across different brands, audiences, and contexts:
- Require 5+ observations across 3+ clients (vs 3 observations for single-client insights)
- Minimum confidence 0.75 before surfacing cross-client recommendations (vs 0.50 for single-client)
- Always tag cross-client insights with the industry and audience conditions under which they were observed

---

## 8. Intelligence Maintenance

### Monthly Review
Review the top 20 insights by confidence score:
- Are they still valid based on recent campaign data?
- Has the market, platform, or audience changed in ways that might invalidate them?
- Are any approaching revalidation deadlines?
- Promote strong hypotheses that have accumulated new evidence
- Archive insights that have decayed below 0.30 confidence

### Quarterly Audit
Full intelligence graph review:
- **Archive stale insights**: Anything below 0.30 confidence or older than 12 months without revalidation
- **Promote strong hypotheses**: Hypotheses that accumulated sufficient evidence since last audit
- **Resolve contradictions**: When two insights conflict, investigate context differences. Run a targeted test if the stakes are high. Archive the lower-confidence insight if no resolution is found
- **Graph health metrics**: Total active insights, average confidence, percentage revalidated in last 90 days, insight-to-playbook-rule conversion rate

### Annual Playbook Refresh
Rebuild playbooks from current high-confidence validated learnings:
- Remove playbook rules based on insights that have decayed or been superseded
- Add new rules from insights that have reached playbook threshold since last refresh
- Review rule applicability — do the context conditions still match current brand strategy?
- Benchmark playbook recommendations against current industry benchmarks to ensure they have not become outdated

### Conflict Resolution Protocol
When two insights directly contradict:
1. **Check context differences**: Do they apply to different audiences, channels, or time periods? If so, both may be valid under different conditions. Tag as context-dependent
2. **Compare confidence scores**: If one has significantly higher confidence (>0.15 difference), defer to the higher-confidence insight
3. **Check recency**: If confidence is similar, the more recent insight may reflect a genuine market shift
4. **Run targeted test**: If the stakes are high and neither insight clearly dominates, design a test to resolve the conflict
5. **Archive if unresolvable**: If testing is not feasible, archive the lower-confidence insight and flag the surviving insight for revalidation in 3 months
