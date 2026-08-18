# Lead Scoring Reference

Comprehensive reference for building, calibrating, and maintaining lead scoring models that accurately predict purchase intent and sales readiness.

---

## Scoring Fundamentals

Lead scoring assigns numeric values to contacts based on two dimensions:

1. **Explicit scoring (fit)** — How well does this person match your ideal customer profile? Based on demographic and firmographic data.
2. **Implicit scoring (engagement)** — How interested is this person in your product or service? Based on behavioral signals.

The combined score determines lifecycle stage (cold, warm, MQL, SQL) and triggers appropriate actions (continue nurture, alert sales, escalate priority).

**Scoring scale**: Use 0-100. Scores above 100 indicate exceptional fit + engagement and should still trigger the SQL handoff — they do not need a higher ceiling.

---

## Explicit Scoring (Demographic/Firmographic Fit)

Explicit scoring measures how closely a lead matches your ideal customer profile (ICP). These points are assigned based on who the person is, not what they do.

### B2B Explicit Scoring Criteria

| Criterion | Strong Fit | Moderate Fit | Weak Fit | Disqualifier |
|---|---|---|---|---|
| **Company size (employees)** | 50-500 (+15) | 501-2000 (+10) | 10-49 (+5) | <10 or >5000 (+0) |
| **Annual revenue** | $5M-$50M (+15) | $50M-$200M (+10) | $1M-$5M (+5) | <$1M (+0) |
| **Industry** | Target industry (+15) | Adjacent industry (+8) | Neutral industry (+3) | Excluded industry (-10) |
| **Job title/role** | Decision maker (VP+) (+20) | Influencer (Director/Manager) (+12) | End user (+5) | Intern/Student (-5) |
| **Department** | Primary buyer dept (+10) | Related dept (+5) | Unrelated dept (+0) | — |
| **Geography** | Target market (+10) | Serviceable market (+5) | Distant/unsupported (+0) | Restricted region (-15) |

**Notes:**
- Point values above are starting templates. Calibrate after 90 days of conversion data.
- "Strong fit" criteria should reflect your top 20% of closed-won deals.
- Adjust company size and revenue ranges to match YOUR ICP, not generic benchmarks.

### B2C Explicit Scoring Criteria

| Criterion | High Value | Medium Value | Low Value |
|---|---|---|---|
| **Location** | Primary market (+10) | Secondary market (+5) | Out of service area (+0) |
| **Age/demographic** | Core demographic (+10) | Adjacent demographic (+5) | Outside target (+0) |
| **Income bracket** | Target bracket (+10) | Adjacent bracket (+5) | Below threshold (+0) |
| **Customer type** | Past customer (+15) | Referral (+10) | Cold lead (+0) |
| **Product interest** | High-margin product (+10) | Standard product (+5) | Low-margin/free tier (+0) |

### eCommerce Explicit Scoring

| Criterion | Points |
|---|---|
| Created account | +10 |
| Added payment method | +15 |
| Past purchase history (1-2 orders) | +10 |
| Past purchase history (3+ orders) | +20 |
| High AOV (>2x average) | +15 |
| Opted into SMS | +5 |
| Loyalty program member | +10 |

---

## Implicit Scoring (Behavioral Engagement)

Implicit scoring measures intent through actions. What someone does reveals how interested they are.

### Email Engagement

| Action | Points | Decay |
|---|---|---|
| Opened email | +1 | Per email, cap at +5/week |
| Clicked email link | +3 | Per click, cap at +10/week |
| Clicked CTA (not just any link) | +5 | Per CTA click |
| Replied to email | +10 | Per reply |
| Forwarded email | +8 | Per forward |
| Opened 5+ emails in 30 days | +5 | Bonus for sustained engagement |

### Website Behavior

| Action | Points | Notes |
|---|---|---|
| General page visit | +1 | Per page, cap at +5/session |
| Blog post read (>60s on page) | +2 | Only count meaningful reads |
| Product/service page visit | +5 | High-intent pages |
| Pricing page visit | +15 | Strongest buying signal short of demo request |
| Comparison/alternative page visit | +10 | Evaluation stage signal |
| Case study/testimonial page | +8 | Social proof seeking = consideration stage |
| Careers page visit | +0 or -5 | Likely a job seeker, not a buyer |
| 3+ sessions in 7 days | +10 | Bonus for repeated engagement |
| 5+ pages per session | +5 | Deep site engagement |

### Content Downloads

| Action | Points | Notes |
|---|---|---|
| Top-funnel content (checklist, infographic) | +5 | Awareness stage |
| Mid-funnel content (whitepaper, guide, report) | +10 | Consideration stage |
| Bottom-funnel content (ROI calculator, buying guide) | +15 | Decision stage |
| Webinar registration | +10 | — |
| Webinar attended (live) | +15 | Higher intent than registration alone |
| Webinar watched on-demand | +8 | Intent but lower urgency |

### High-Intent Actions

| Action | Points | Notes |
|---|---|---|
| Demo request | +25 | Direct sales intent |
| Free trial signup | +20 | Product evaluation |
| Contact sales form | +25 | Explicit buying signal |
| Chat with sales | +15 | Real-time engagement with sales |
| RFP/quote request | +30 | Active buying process |
| Attended in-person event or meeting | +20 | High-commitment action |

### Product Usage (SaaS)

| Action | Points | Notes |
|---|---|---|
| Completed onboarding | +15 | Activated user |
| Used core feature | +10 | Found primary value |
| Invited team member | +20 | Expansion signal — strongest PQL indicator |
| Connected integration | +15 | Deepening commitment |
| Approaching usage limit | +10 | Natural upgrade trigger |
| Daily active usage (7+ days) | +15 | Habitual user |

---

## Negative Scoring

Negative scoring is as important as positive scoring. It prevents unqualified leads from reaching sales and protects scoring accuracy.

### Engagement-Based Negative Scoring

| Signal | Points | Notes |
|---|---|---|
| Email bounced (hard) | -15 | Invalid contact — also flag for data hygiene |
| Email bounced (soft, 3+ times) | -10 | Deliverability problem |
| Unsubscribed from emails | -25 | Clear disengagement signal |
| Marked email as spam | -50 | Remove from scoring entirely |
| No email engagement in 30 days | -5 | Apply as ongoing decay |
| No email engagement in 60 days | -10 | Additional decay |
| No email engagement in 90 days | -15 | Additional decay — trigger re-engagement workflow |
| No website visit in 60 days | -10 | — |

### Fit-Based Negative Scoring

| Signal | Points | Notes |
|---|---|---|
| Competitor domain email | -50 | Likely competitive intelligence, not a buyer |
| Free email domain (gmail, yahoo) for B2B | -10 | May be valid but lower confidence for enterprise |
| Student/academic email (.edu) | -15 | Research, not purchase intent (unless ed-tech) |
| Job title: intern, student, assistant | -10 | Low decision-making authority |
| Company size below minimum | -15 | Below serviceable threshold |
| Disqualified industry | -20 | Cannot serve this industry |
| Visited only careers page | -15 | Job seeker, not prospect |

### Behavioral Negative Scoring

| Signal | Points | Notes |
|---|---|---|
| Unsubscribed from product/trial | -20 | Active rejection |
| Requested data deletion (GDPR) | Remove from scoring | Compliance requirement — stop all scoring |
| Downloaded competitor comparison and never returned | -5 | Window shopper |
| Canceled meeting/demo no-show | -10 | Low commitment |
| Repeated form fills with fake data | -25 | Bot or low-quality lead |

---

## Score Thresholds & Lifecycle Stages

| Score Range | Stage | Definition | Action |
|---|---|---|---|
| 0-25 | **Cold** | Low fit or low engagement. May be early-stage or poor fit. | Continue top-funnel nurture. Do not pass to sales. |
| 26-50 | **Warm** | Moderate fit and/or engagement. Showing initial interest. | Mid-funnel nurture. Personalize based on behavior. |
| 51-75 | **MQL** (Marketing Qualified Lead) | Strong fit + meaningful engagement. Ready for sales evaluation. | Alert sales team. Begin MQL-to-SQL handoff process. |
| 76-100 | **SQL** (Sales Qualified Lead) | High fit + high engagement. Demonstrated buying signals. | Immediate sales follow-up. SLA: respond within 4 hours (B2B) or 1 hour (B2C). |

### Threshold Calibration Process

1. **Start with the defaults above** for the first 90 days.
2. **After 90 days**, pull conversion data: What score did closed-won deals reach before converting?
3. **Find the natural break point**: The score range where conversion rate jumps significantly. That is your MQL threshold.
4. **Validate with sales**: Ask sales which MQLs were actually qualified. If >60% of MQLs convert to SQL, your threshold is right. If <40%, your MQL threshold is too low (you are sending unready leads).
5. **Recalibrate quarterly**: Buying behavior changes, product changes, and market shifts all affect scoring accuracy.

---

## Progressive Profiling

Progressive profiling collects lead information incrementally across multiple interactions rather than asking for everything upfront.

### Data Collection by Engagement Level

| Engagement Level | Data to Collect | Method |
|---|---|---|
| **First touch** | Email address only | Single-field form, inline subscription |
| **Second engagement** (content download) | First name, company name | 2-3 field form |
| **Third engagement** (deeper content) | Job title, company size | 3-4 field form (pre-fill known fields) |
| **Fourth engagement** (high-intent) | Phone, industry, pain points | Longer form acceptable at this intent level |
| **MQL threshold** | Budget, timeline, decision process | Sales discovery call (not forms) |

**Rules:**
- Never ask for information you already have. Pre-fill known fields.
- Never gate top-funnel content behind forms with 5+ fields. The conversion rate drop is not worth the data.
- Every additional form field reduces completion rate by approximately 10%.
- Use enrichment tools (Clearbit, ZoomInfo, Apollo) to fill firmographic data without asking the prospect.

---

## Lead Scoring Models by Business Type

### B2B SaaS

- **Emphasis**: Product usage signals > email engagement > content consumption
- **Key PQL indicators**: Invited team member, connected integration, daily active usage
- **MQL criteria**: Score 55+ with at least one high-intent action (demo request, pricing page visit + trial signup)
- **SQL criteria**: Score 80+ OR PQL threshold met (specific product usage milestones)
- **Unique consideration**: Free tier usage must be scored carefully — high product engagement does not always mean purchase intent if the free tier is sufficient

### B2B Professional Services

- **Emphasis**: Content consumption (case studies, methodology content) > direct inquiry > event attendance
- **Key signals**: Downloaded multiple case studies in same industry, attended webinar, returned to site 3+ times
- **MQL criteria**: Score 50+ with industry fit confirmed and engagement with solution-level content
- **SQL criteria**: Score 75+ OR direct consultation request
- **Unique consideration**: Long sales cycles (3-12 months). Score decay must be slower (monthly, not weekly). Weight industry fit heavily — misaligned industry almost never converts.

### B2C eCommerce

- **Emphasis**: Browse behavior > cart activity > purchase history > email engagement
- **Key signals**: Repeat site visits, cart creation, wishlist additions, product page views (especially 3+ products in same category)
- **Scoring application**: Trigger abandoned cart, browse abandonment, and replenishment workflows rather than traditional MQL handoff
- **Unique consideration**: No "sales team" handoff. Score drives automated workflow enrollment and promotional targeting.

### Local Business

- **Emphasis**: Location proximity > direct inquiry > review engagement
- **Key signals**: Visited directions/location page, called the business, submitted contact form, clicked "book appointment"
- **Scoring application**: Simple 3-tier model (cold/warm/hot) triggering automated follow-up
- **Unique consideration**: Volume is typically low enough that complex scoring is unnecessary. Focus on response speed over scoring sophistication.

---

## Score Decay

Scores must decay over time to reflect that engagement fades. A lead who was highly engaged 6 months ago but silent since then is not the same as one who is active today.

### Decay Models

**Time-based decay (recommended for most businesses):**

| Inactivity Period | Decay Action |
|---|---|
| 14 days no activity | -2 points (gentle nudge) |
| 30 days no activity | -5 points |
| 60 days no activity | -10 points + trigger re-engagement workflow |
| 90 days no activity | -15 points |
| 180 days no activity | Reset to baseline (keep explicit fit score, zero out behavioral score) |

**Activity-based decay (for high-engagement models):**
- Decay only behavioral scores, not fit scores (someone's company size does not change because they stopped emailing you)
- Apply decay proportionally: high-engagement contacts decay faster because their inflated scores are more misleading if stale
- Reset behavioral score to zero after 6 months of no activity, then re-score only on new actions

**Seasonal adjustment:**
- Pause decay during known low-activity periods (holidays, summer) for B2B
- For B2C, reverse: increase scoring during seasonal peaks (Black Friday, back-to-school) to capture urgency

---

## Sales Handoff Rules

### MQL-to-SQL Handoff Process

1. **Lead reaches MQL threshold** (score 51-75)
2. **Automated notification** sent to assigned sales rep (or round-robin to SDR team)
3. **Handoff SLA**: Sales must contact MQL within defined window
   - B2B SaaS: 4 business hours
   - B2B enterprise: 24 business hours (research needed before outreach)
   - B2C/eCommerce: 1 hour (or automated — no human needed)
4. **Sales qualification**: SDR/AE determines if MQL is truly sales-ready
   - **Accepted** → SQL (score adjusted to 76+, enters sales pipeline)
   - **Rejected** → Recycled back to marketing nurture with feedback reason
   - **Disqualified** → Removed from scoring (bad fit, wrong person, competitor)
5. **Feedback loop**: Sales rejection reasons feed back into scoring model calibration
   - If 50%+ of MQLs are rejected, MQL threshold is too low
   - If <5% of MQLs are rejected, threshold might be too high (missing opportunities)

### Handoff Data Package

When handing an MQL to sales, include:
- Lead score breakdown (explicit vs. implicit)
- Full activity timeline (pages visited, content downloaded, emails engaged)
- Company/contact enrichment data
- Source of first touch and most recent engagement
- Active nurture sequence (so sales does not repeat what marketing already said)
- Any known pain points or use case signals from content engagement patterns

---

## Re-Scoring Triggers

Certain events should trigger a complete re-evaluation of a contact's score rather than incremental changes.

| Trigger | Action |
|---|---|
| Job title change (promotion) | Re-score explicit fit. VP promotion = significant score increase. |
| Company change | Re-score all explicit criteria. New company may not be ICP. |
| Re-engagement after dormancy | Reset behavioral score to zero, then re-score from new activity only |
| Closed-lost deal | Reset to warm (30-40 points), enter long-term nurture. Do not zero out. |
| Customer churned | Move to win-back track. Score separately from new lead scoring. |
| Requested to be removed from sales pipeline | Remove from SQL, return to MQL nurture. Reduce score by 20. |
| Merged duplicate records | Combine scores: take higher explicit score + sum of behavioral (capped at 100) |

---

## Measuring Scoring Model Accuracy

### Key Metrics

| Metric | Target | What It Tells You |
|---|---|---|
| **MQL-to-SQL conversion rate** | 40-60% | Are MQLs actually qualified? |
| **SQL-to-Opportunity conversion rate** | 50-70% | Are SQLs truly sales-ready? |
| **MQL-to-Closed-Won rate** | 5-15% (B2B) | End-to-end scoring effectiveness |
| **Average score at conversion** | Cluster analysis | Where conversions actually happen on the scale |
| **False positive rate** | <40% | High-score leads that never convert |
| **False negative rate** | <10% | Low-score leads that convert anyway (missed opportunities) |
| **Score-to-revenue correlation** | R > 0.5 | Does score actually predict revenue? |
| **Time from MQL to SQL** | Decreasing QoQ | Is scoring identifying readiness earlier? |

### Quarterly Scoring Audit Checklist

1. Pull all leads that converted to customer in the last quarter
2. Analyze their score at time of MQL handoff — what was the distribution?
3. Pull all MQLs that were rejected by sales — what was their score at handoff?
4. Identify any customers who were never scored as MQL (false negatives) — what signals were missed?
5. Compare average score at conversion vs. MQL threshold — adjust threshold if they diverge
6. Review top 5 highest-scored leads that did NOT convert — why? Are certain scoring criteria overweighted?
7. Check decay effectiveness — are stale leads being properly deprioritized?
8. Validate with sales team — qualitative feedback on MQL quality trend
