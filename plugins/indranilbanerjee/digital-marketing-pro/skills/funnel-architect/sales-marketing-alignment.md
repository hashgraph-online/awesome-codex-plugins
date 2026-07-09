# Sales-Marketing Alignment — SMarketing Framework & Operations

A comprehensive reference for building operational alignment between sales and marketing. Covers shared funnel definitions, service level agreements, lead handoff processes, feedback loops, RevOps implementation, and ready-to-use templates.

---

## Shared Funnel Definitions

Every misalignment starts with marketing and sales defining the same terms differently. Lock these definitions before anything else.

### Funnel Stage Definitions

| Stage | Definition | Criteria | Owner |
|-------|-----------|----------|-------|
| **Visitor** | Anonymous individual who reaches any owned property | Page view or app session with no identifying info | Marketing |
| **Lead** | Known individual who has provided contact information | Form fill, signup, chat initiation, or data enrichment match | Marketing |
| **MQL (Marketing Qualified Lead)** | Lead demonstrating sufficient fit + engagement to warrant sales attention | Meets lead scoring threshold (demographic fit + behavioral signals) | Marketing |
| **SQL (Sales Qualified Lead)** | Lead accepted by sales as worth pursuing after initial qualification | Sales rep confirms budget, need, or active evaluation via first contact | Sales |
| **Opportunity** | Active deal in pipeline with defined timeline and stakeholders | Discovery call completed, requirements documented, decision-maker identified | Sales |
| **Customer** | Closed deal, signed contract, first payment received | Contract executed or first purchase completed | Sales (handoff to CS) |
| **Advocate** | Customer who actively refers, reviews, or promotes | NPS 9-10, referral given, case study participant, or public review | Customer Success + Marketing |

### Transition Triggers

| Transition | Trigger Event | SLA |
|-----------|---------------|-----|
| Visitor to Lead | Identifies themselves (form, signup, chat) | Instant (automated) |
| Lead to MQL | Reaches lead score threshold | Within 1 business hour of scoring |
| MQL to SQL | Sales rep accepts and makes first contact | Within 4 business hours of MQL notification |
| SQL to Opportunity | Discovery call completed, confirmed fit | Within 5 business days of SQL acceptance |
| Opportunity to Customer | Contract signed, payment processed | Per sales cycle benchmarks |
| Customer to Advocate | Achieves success metrics + engagement signals | Triggered at 90 days post-onboarding |

---

## Service Level Agreements (SLAs)

### Marketing SLA to Sales

Marketing commits to delivering a specified volume and quality of leads each period.

| Metric | Target | Measurement |
|--------|--------|-------------|
| **MQL volume** | [N] MQLs per month (calculated from revenue target backward) | CRM/MAP MQL count |
| **MQL quality score** | Average lead score of [X]+ for all MQLs passed | Lead scoring system average |
| **MQL-to-SQL acceptance rate** | > 60% of MQLs accepted by sales as SQLs | CRM stage conversion |
| **Lead data completeness** | 100% have email, name, company; 80% have phone, title, company size | CRM field audit |
| **Delivery timing** | MQLs routed within 1 hour of qualifying | Automation timestamp audit |
| **Content support** | Sales enablement content updated monthly; new assets for each campaign | Content calendar compliance |

### Sales SLA to Marketing

Sales commits to working every qualified lead with speed and consistency, and providing structured feedback.

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Speed-to-lead** | First outreach within 4 business hours of MQL notification | CRM activity timestamp |
| **Follow-up cadence** | Minimum 6 touches over 14 days before disqualifying | Sequence/cadence completion rate |
| **Disposition every MQL** | 100% of MQLs marked as accepted, disqualified, or recycled within 5 business days | CRM disposition audit |
| **Disqualification feedback** | Reason code required for every rejected MQL | CRM picklist completion |
| **CRM hygiene** | All opportunities have stage, amount, close date, and next step updated weekly | CRM data quality score |
| **Win/loss feedback** | Reason recorded for every closed-won and closed-lost within 48 hours | CRM close reason field |

### SLA Calculation: From Revenue Target to MQL Target

Work backward from the revenue goal to determine how many MQLs marketing must deliver.

```
REVENUE TARGET:           $1,000,000 / quarter
AVERAGE DEAL SIZE:        $25,000
DEALS NEEDED:             40
WIN RATE:                 25%
OPPORTUNITIES NEEDED:     160
SQL-TO-OPPORTUNITY RATE:  50%
SQLs NEEDED:              320
MQL-TO-SQL RATE:          60%
MQLs NEEDED:              534 per quarter (178/month)
```

---

## Lead Handoff Process

### MQL Scoring Criteria

| Category | Signal | Points |
|----------|--------|--------|
| **Demographic Fit** | | |
| Title matches ICP | VP, Director, C-suite in target function | +20 |
| Company size matches ICP | 50-500 employees (adjust to your ICP) | +15 |
| Industry matches ICP | Target verticals | +10 |
| Geography | Target markets | +5 |
| **Behavioral Signals** | | |
| Pricing page visit | Viewed pricing page | +15 |
| Demo request | Submitted demo/trial form | +25 |
| Content engagement (high-intent) | Downloaded case study, ROI calculator, comparison guide | +10 each |
| Content engagement (low-intent) | Blog visit, social engagement | +2 each |
| Email engagement | Opened 3+ emails in 30 days | +5 |
| Repeat visits | 3+ sessions in 7 days | +10 |
| **Negative Signals** | | |
| Competitor employee | Works at a known competitor | -50 |
| Student / personal email | .edu or free email domain (if targeting enterprise) | -20 |
| Unsubscribed | Opted out of email | -30 |
| No engagement in 30 days | Score decay for inactivity | -5 per week |

**MQL threshold:** 50 points (adjust based on your MQL-to-SQL acceptance rate; target 60%+ acceptance)

### Routing Rules

| Condition | Assignment |
|-----------|-----------|
| Enterprise (500+ employees) | Enterprise AE by territory |
| Mid-market (50-499 employees) | Mid-market AE by round-robin |
| SMB (< 50 employees) | SDR team for qualification, then AE |
| Named account on target list | Assigned account owner (regardless of lead score) |
| Partner referral | Partner sales team |
| Existing customer (upsell signal) | Account manager / CSM |

### Speed-to-Lead Benchmarks

| Response Time | Qualification Rate Impact |
|---------------|--------------------------|
| < 5 minutes | Baseline (100% of expected conversion) |
| 5-30 minutes | 80% of expected conversion |
| 30-60 minutes | 60% of expected conversion |
| 1-24 hours | 35% of expected conversion |
| > 24 hours | 10% of expected conversion |

**The data is unambiguous:** leads contacted within 5 minutes are 9x more likely to convert than leads contacted after 30 minutes.

### Re-Queue Conditions

| Condition | Action |
|-----------|--------|
| Sales cannot reach after 6 attempts over 14 days | Return to marketing nurture; re-enter MQL queue if score rises again |
| Lead is interested but timing is wrong (6+ months out) | Place in long-term nurture; set CRM reminder for re-engagement |
| Lead is qualified but wrong persona | Route to correct sales team/segment |
| Lead needs more education | Return to marketing with specific content recommendations from sales |

---

## Feedback Loops

### Sales-to-Marketing Content Requests

| Request Type | Turnaround Target | Format |
|-------------|-------------------|--------|
| Objection-handling content | 1 week | One-pager, email snippet, or talk track |
| Competitive battlecard | 2 weeks | Structured comparison document |
| Case study for specific vertical/use case | 3-4 weeks | Full case study with customer approval |
| Product update positioning | 1 week from release | Messaging document + email template |
| Event/webinar support | 3 weeks before event | Landing page, email sequence, social posts |

### Closed-Loop Reporting

For every closed deal (won or lost), track which marketing touchpoints influenced the journey:

```
DEAL: [Company Name]
OUTCOME: Won / Lost
DEAL SIZE: $[X]
SALES CYCLE: [X days]
LEAD SOURCE: [First touch attribution]
MARKETING TOUCHPOINTS:
  - [Date] [Touchpoint 1: e.g., Downloaded whitepaper]
  - [Date] [Touchpoint 2: e.g., Attended webinar]
  - [Date] [Touchpoint 3: e.g., Clicked email CTA]
SALES TOUCHPOINTS:
  - [Date] [Activity 1: e.g., SDR cold call]
  - [Date] [Activity 2: e.g., AE demo]
DISQUALIFICATION REASON (if lost): [Reason code + notes]
COMPETITOR (if lost): [Who they chose]
WINNING FACTOR (if won): [What tipped the decision]
```

### Disqualification Reason Codes

| Code | Reason | Marketing Action |
|------|--------|-----------------|
| DQ-01 | No budget | Nurture with ROI content; re-engage next fiscal year |
| DQ-02 | No authority (wrong persona) | Refine targeting criteria and lead scoring |
| DQ-03 | No need (problem doesn't exist) | Review content targeting; tighten ICP definition |
| DQ-04 | Bad timing (> 6 months) | Long-term nurture sequence |
| DQ-05 | Competitor chosen | Feed to competitive intelligence; review positioning |
| DQ-06 | Bad data (wrong contact info, spam) | Audit lead sources; tighten form validation |
| DQ-07 | Too small / not ICP | Adjust scoring; consider self-serve path |

---

## Shared Metrics Dashboard

### Primary Alignment Metrics

| Metric | Formula | Target | Owner |
|--------|---------|--------|-------|
| **Marketing-sourced pipeline** | Total pipeline value from marketing-generated leads | 40-60% of total pipeline | Joint |
| **Marketing-influenced revenue** | Closed revenue where marketing touched the journey | 60-80% of total revenue | Joint |
| **Lead-to-customer rate** | Customers / Total leads | Industry-dependent (SaaS: 2-5%) | Joint |
| **MQL-to-SQL acceptance rate** | SQLs / MQLs | > 60% | Marketing quality indicator |
| **SQL-to-opportunity rate** | Opportunities / SQLs | > 50% | Sales quality indicator |
| **Speed-to-lead** | Median time from MQL to first sales touch | < 1 hour | Sales |
| **Sales cycle length** | Median days from SQL to close | Benchmark against prior quarters | Joint |
| **Average deal size** | Revenue / Deals | Benchmark against prior quarters | Joint |
| **CAC by channel** | Total acquisition cost / Customers by channel | Decreasing quarter-over-quarter | Joint |

---

## Meeting Cadence

### Daily: Pipeline Standup (15 minutes)

- **Who:** SDR team lead + marketing campaign manager
- **Agenda:** Yesterday's MQLs delivered, today's follow-up priorities, any lead quality flags
- **Output:** Real-time routing adjustments, immediate feedback on campaign quality

### Weekly: Campaign Performance Review (30 minutes)

- **Who:** Marketing ops + sales ops + 1 AE representative
- **Agenda:** MQL volume and quality this week, campaign performance by source, lead disposition rates, content requests
- **Output:** Weekly scorecard, content request queue updates

### Monthly: Funnel Health Review (60 minutes)

- **Who:** VP Marketing + VP Sales + RevOps
- **Agenda:** Full-funnel conversion rates, SLA compliance, pipeline coverage ratio, attribution analysis, competitive intelligence debrief
- **Output:** Monthly alignment report, SLA adjustments, resource allocation decisions

### Quarterly: Strategic Planning (Half-day)

- **Who:** CMO + CRO + RevOps + team leads
- **Agenda:** Revenue target review, ICP refinement, scoring model recalibration, campaign planning, technology stack evaluation, SLA renegotiation
- **Output:** Updated SLAs, next-quarter campaign calendar, ICP documentation, scoring model changes

---

## Common Misalignment Patterns

### Diagnostic Framework

| Symptom | Marketing Says | Sales Says | Root Cause | Fix |
|---------|---------------|------------|-----------|-----|
| Low conversion | "We generate enough leads" | "Leads are garbage" | MQL criteria too loose; lead scoring not calibrated | Joint scoring workshop; recalibrate with closed-deal data |
| Pipeline shortfall | "We hit MQL targets" | "Not enough pipeline" | MQLs don't convert to opportunities | Tighten demographic scoring; add intent signals |
| Long sales cycles | "Leads are well-nurtured" | "Leads aren't ready to buy" | Content nurture doesn't address buying objections | Map content to buyer journey stages; include sales input on topics |
| High CAC | "We need more budget" | "We need better leads, not more" | Channel mix includes low-quality sources | Analyze CAC by channel; cut underperformers; reinvest in proven channels |
| Revenue miss despite volume | "We delivered 120% of MQL target" | "Win rate dropped 15%" | Quantity over quality trade-off | Shift MQL target to quality-weighted metric; implement MQL-to-revenue tracking |

---

## Revenue Operations (RevOps)

### What RevOps Is

RevOps is a centralized function that owns the processes, technology, data, and reporting across marketing, sales, and customer success. It eliminates the operational silos that cause misalignment.

### Key RevOps Responsibilities

| Domain | Responsibilities |
|--------|-----------------|
| **Process** | Funnel stage definitions, lead routing rules, handoff processes, SLA management |
| **Technology** | CRM, MAP, sales engagement, attribution, BI tools — unified stack governance |
| **Data** | Single source of truth for pipeline, conversion, and revenue metrics; data hygiene |
| **Reporting** | Shared dashboards, funnel analytics, attribution, forecasting |
| **Enablement** | Cross-functional process training, playbook documentation, new hire onboarding |

### RevOps Implementation Phases

| Phase | Timeline | Focus |
|-------|----------|-------|
| **Foundation** | Months 1-2 | Audit current state; document existing processes; identify gaps; define funnel stages |
| **Unification** | Months 3-4 | Integrate CRM + MAP; build shared dashboards; implement lead scoring; define SLAs |
| **Optimization** | Months 5-6 | Launch SLA tracking; implement closed-loop reporting; establish meeting cadence |
| **Maturity** | Ongoing | Predictive scoring; attribution modeling; revenue forecasting; continuous process improvement |

---

## Templates

### SLA Document Structure

```
SALES-MARKETING SERVICE LEVEL AGREEMENT
Effective Date: [Date]
Review Cadence: Quarterly

REVENUE TARGETS:
- Quarterly revenue goal: $[X]
- Required pipeline coverage: [X]x (e.g., 3x)

MARKETING COMMITMENTS:
- MQL volume: [N] per month
- MQL quality: [X]% acceptance rate target
- Data completeness: [Standards]
- Routing speed: [Timeframe]
- Content delivery: [Cadence and response times]

SALES COMMITMENTS:
- Speed-to-lead: [Timeframe]
- Follow-up cadence: [Minimum touches]
- Disposition deadline: [Timeframe]
- CRM hygiene: [Standards]
- Feedback delivery: [Cadence]

ESCALATION PROCESS:
- SLA breach identified by: [RevOps / automated alert]
- First escalation: [Team lead, within 24 hours]
- Second escalation: [VP level, within 48 hours]

REVIEW AND AMENDMENT:
- Monthly SLA compliance review in funnel health meeting
- Quarterly renegotiation in strategic planning session
- Either party can request emergency review with 48-hour notice

SIGNATURES:
VP Marketing: _____________ Date: _______
VP Sales: _____________ Date: _______
```

### Pipeline Review Agenda

```
WEEKLY PIPELINE REVIEW — [Date]

1. FUNNEL METRICS (5 min)
   - MQLs delivered this week: [N] (target: [N])
   - MQL acceptance rate: [X%] (target: 60%+)
   - Speed-to-lead median: [X hours] (target: < 4 hours)

2. DEAL INSPECTION (15 min)
   - Deals closing this month: [Review top 10 by value]
   - Stalled deals (no activity in 14+ days): [Review and assign actions]
   - Deals at risk: [Identify and discuss]

3. CAMPAIGN IMPACT (5 min)
   - Top performing campaign this week: [Campaign] — [N] MQLs at [X%] acceptance
   - Underperforming campaign: [Campaign] — [Issue and recommended action]

4. FEEDBACK LOOP (5 min)
   - Content requests from sales: [List]
   - Lead quality flags: [Specific issues]
   - Competitive intelligence: [What sales is hearing]

ACTION ITEMS:
- [Owner] [Action] [Due date]
```

### Monthly Marketing-Sales Report

```
MONTHLY ALIGNMENT REPORT — [Month Year]

EXECUTIVE SUMMARY:
[2-3 sentences on overall alignment health]

MARKETING SLA COMPLIANCE:
| Metric              | Target  | Actual  | Status |
|---------------------|---------|---------|--------|
| MQL volume          | [N]     | [N]     | [Met/Missed] |
| MQL acceptance rate | 60%     | [X%]    | [Met/Missed] |
| Data completeness   | 80%     | [X%]    | [Met/Missed] |
| Content delivery    | On-time | [X/Y]   | [Met/Missed] |

SALES SLA COMPLIANCE:
| Metric              | Target     | Actual     | Status |
|---------------------|------------|------------|--------|
| Speed-to-lead       | < 4 hours  | [X hours]  | [Met/Missed] |
| Follow-up cadence   | 6 touches  | [X avg]    | [Met/Missed] |
| Disposition rate     | 100% in 5d | [X%]       | [Met/Missed] |
| CRM hygiene         | Weekly     | [X% compliant] | [Met/Missed] |

FUNNEL PERFORMANCE:
| Stage               | Volume | Conversion Rate | vs. Prior Month |
|---------------------|--------|-----------------|-----------------|
| Leads               | [N]    | —               | [+/- X%]        |
| MQLs                | [N]    | [X%]            | [+/- X%]        |
| SQLs                | [N]    | [X%]            | [+/- X%]        |
| Opportunities       | [N]    | [X%]            | [+/- X%]        |
| Closed-Won          | [N]    | [X%]            | [+/- X%]        |

REVENUE ATTRIBUTION:
- Marketing-sourced: $[X] ([X%] of total)
- Marketing-influenced: $[X] ([X%] of total)
- Sales-sourced: $[X] ([X%] of total)

KEY INSIGHTS:
1. [Insight with supporting data]
2. [Insight with supporting data]
3. [Insight with supporting data]

NEXT MONTH PRIORITIES:
1. [Priority + owner]
2. [Priority + owner]
3. [Priority + owner]
```
