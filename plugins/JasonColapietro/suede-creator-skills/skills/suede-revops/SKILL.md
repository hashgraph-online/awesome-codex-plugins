---
name: suede-revops
description: "Define lifecycle stages, fit and engagement scores, MQL/SQL handoffs, routing SLAs, pipeline hygiene, CRM automation, deal-desk tiers, and dashboard metrics. Use when asked to \"fix our lead routing\" or specify revenue operations. Returns implementation-ready rules with owners and measurement. NOT FOR: prospect lists (use suede-prospecting), outbound copy (use suede-cold-email), lifecycle campaigns (use suede-emails), pricing strategy (use suede-pricing), or unapproved production CRM changes."
metadata:
  display-name: "Suede AI Revenue Operations Skills"
  version: 2.0.1
---

# Suede AI Revenue Operations Skills

## Compatibility

Works from supplied CRM schemas, exports, and process evidence. Live CRM inspection needs authorized access; implementation documents do not require HubSpot, Salesforce, or Zapier connectors.

For a concrete input, expected handoff, and failure check, read
[the worked handoff](references/worked-handoff.md).

Suede AI RevOps maps the lifecycle rules, data contracts, scoring, routing, and
handoffs that connect acquisition, sales, and customer success. It produces
implementation-ready operating logic while keeping production CRM mutation
behind live-schema review and approval.

## Before Starting

**Check for product marketing context first:**
If `.agents/product-marketing.md` exists (or `.claude/product-marketing.md`, or the legacy `product-marketing-context.md` filename, in older setups), read it before asking questions. Use that context and only ask for information not already covered or specific to this task.

Gather this context (ask if not provided):

1. **GTM motion**: Product-led (PLG), sales-led, or hybrid?
2. **ACV range**: What's the average contract value?
3. **Sales cycle length**: Days from first touch to closed-won?
4. **Current stack**: CRM, marketing automation, scheduling, enrichment tools?
5. **Current state**: How are leads managed today? What's working and what's not?
6. **Goals**: Increase conversion? Reduce speed-to-lead? Fix handoff leaks? Build from scratch?

Work with whatever the user gives you. If they have a clear problem area, start there. Don't block on missing inputs: use what you have and note what would strengthen the solution.

---

## Core Principles

### Single Source of Truth
One system of record for every lead and account. If data lives in multiple places, it will conflict. Pick a CRM as the canonical source and sync everything to it.

### Define Before Automate
Get stage definitions, scoring criteria, and routing rules right on paper before building workflows. Automating a broken process just creates broken results faster.

### Measure Every Handoff
Every handoff between teams is a potential leak. Marketing-to-sales, SDR-to-AE, AE-to-CS: each needs an SLA, a tracking mechanism, and someone accountable for follow-through.

### Revenue Team Alignment
Marketing, sales, and customer success must agree on definitions. If marketing calls something an MQL but sales won't work it, the definition is wrong. Alignment meetings aren't optional.

---

## Lead Lifecycle Framework

### Stage Definitions

| Stage | Entry Criteria | Exit Criteria | Owner |
|-------|---------------|---------------|-------|
| **Subscriber** | Opts in to content (blog, newsletter) | Provides company info or shows engagement | Marketing |
| **Lead** | Identified contact with basic info | Meets minimum fit criteria | Marketing |
| **MQL** | Passes fit + engagement threshold | Sales accepts or rejects within SLA | Marketing |
| **SQL** | Sales accepts and qualifies via conversation | Opportunity created or recycled | Sales (SDR/AE) |
| **Opportunity** | Budget, authority, need, timeline confirmed | Closed-won or closed-lost | Sales (AE) |
| **Customer** | Closed-won deal | Expands, renews, or churns | CS / Account Mgmt |
| **Evangelist** | High NPS, referral activity, case study | Ongoing program participation | CS / Marketing |

### MQL Definition

An MQL requires both **fit** and **engagement**:

- **Fit score**: Does this person match your ICP? (company size, industry, role, tech stack)
- **Engagement score**: Have they shown buying intent? (pricing page, demo request, multiple visits)

Neither alone is sufficient. A perfect-fit company that never engages isn't an MQL. A student downloading every ebook isn't an MQL.

### MQL-to-SQL Handoff SLA

Define response times and document them:
- MQL alert sent to assigned rep
- Rep contacts within **4 hours** (business hours)
- Rep qualifies or rejects within **48 hours**
- Rejected MQLs go to recycling nurture with reason code

**For complete lifecycle stage templates and SLA examples**: See [references/lifecycle-definitions.md](references/lifecycle-definitions.md)

---

## Lead Scoring

### Scoring Dimensions

**Explicit scoring (fit)**: Who they are:
- Company size, industry, revenue
- Job title, seniority, department
- Tech stack, geography

**Implicit scoring (engagement)**: What they do:
- Page visits (especially pricing, demo, case studies)
- Content downloads, webinar attendance
- Email engagement (opens, clicks)
- Product usage (for PLG)

**Negative scoring**: Disqualifying signals:
- Competitor email domains
- Student/personal email
- Unsubscribes, spam complaints
- Job title mismatches (intern, student)

### Building a Scoring Model

1. Define your ICP attributes and weight them
2. Identify high-intent behavioral signals from closed-won data
3. Set point values for each attribute and behavior
4. Set MQL threshold (typically 50-80 points on a 100-point scale)
5. Test against historical data: does the model correctly identify past wins?
6. Launch, measure, and recalibrate quarterly

### Common Scoring Mistakes

- Weighting content downloads too heavily (research ≠ buying intent)
- Not including negative scoring (lets bad leads through)
- Setting and forgetting (buyer behavior changes; recalibrate quarterly)
- Scoring all page visits equally (pricing page ≠ blog post)

**For detailed scoring templates and example models**: See [references/scoring-models.md](references/scoring-models.md)

---

## Lead Routing

### Routing Methods

| Method | How It Works | Best For |
|--------|-------------|----------|
| **Round-robin** | Distribute evenly across reps | Equal territories, similar deal sizes |
| **Territory-based** | Assign by geography, vertical, or segment | Regional teams, industry specialists |
| **Account-based** | Named accounts go to named reps | ABM motions, strategic accounts |
| **Skill-based** | Route by deal complexity, product line, or language | Diverse product lines, global teams |

### Routing Rules Essentials

- Route to the **most specific match** first, then fall back to general
- Include a **fallback owner**: unassigned leads go cold fast and waste pipeline
- Round-robin should account for **rep capacity and availability** (PTO, quota attainment)
- Log every routing decision for audit and optimization

### Speed-to-Lead

Response time is one of the largest controllable factors in inbound conversion.
Older vendor studies report order-of-magnitude differences with undisclosed
methods; trust the direction, not the multipliers, and measure your own curve
(method in `references/routing-rules.md`):
- Default target: first touch within **5 minutes** during business hours
- Expect a steep drop within the first hour
- Treat leads untouched for **24 hours** as cooling and route them to nurture with a reason code

Build routing rules that prioritize speed. Alert reps immediately. Escalate if SLA is missed.

**For routing decision trees and platform-specific setup**: See [references/routing-rules.md](references/routing-rules.md)

---

## Pipeline Stage Management

### Pipeline Stages

| Stage | Required Fields | Exit Criteria |
|-------|----------------|---------------|
| **Qualified** | Contact info, company, source, fit score | Discovery call scheduled |
| **Discovery** | Pain points, current solution, timeline | Needs confirmed, demo scheduled |
| **Demo/Evaluation** | Technical requirements, decision makers | Positive evaluation, proposal requested |
| **Proposal** | Pricing, terms, stakeholder map | Proposal delivered and reviewed |
| **Negotiation** | Redlines, approval chain, close date | Terms agreed, contract sent |
| **Closed Won** | Signed contract, payment terms | Handoff to CS complete |
| **Closed Lost** | Loss reason, competitor (if any) | Post-mortem logged |

### Stage Hygiene

- **Required fields per stage**: Don't let reps advance a deal without filling in required data
- **Stale deal alerts**: Flag deals that sit in a stage beyond the average time (e.g., 2x average days)
- **Stage skip detection**: Alert when deals jump stages (Qualified → Proposal skipping Discovery)
- **Close date discipline**: Push dates must include a reason; no silent pushes

### Pipeline Metrics

| Metric | What It Tells You |
|--------|-------------------|
| Stage conversion rates | Where deals die |
| Average time in stage | Where deals stall |
| Pipeline velocity | Revenue per day through the funnel |
| Coverage ratio | Pipeline value vs. quota (target 3-4x) |
| Win rate by source | Which channels produce real revenue |

---

## CRM Automation Workflows

Platform-agnostic build list: the set to design before the stack is decided,
in build order:

1. **MQL alert + assignment**: instant rep notification with lead context
2. **SLA escalation**: notify the manager when response time is missed
3. **Score-driven stage promotion**: advance lifecycle stage when criteria are met
4. **Meeting booked / no-show**: notify the AE; auto-follow-up on a miss
5. **Closed-won handoff**: create the CS task and update the forecast
6. **Stale deal alert**: flag a deal past 2x average days in stage
7. **Recycled-lead nurture**: return disqualified leads to marketing with a reason code
8. **Activity digest + re-engagement**: daily high-intent summary; alert on a dormant lead's return

**For the trigger and action definitions per platform**: HubSpot workflows,
Salesforce Flow equivalents, Calendly/SavvyCal, and Zapier patterns, including
round-robin, routing by criteria, and pre-meeting enrichment: See
[references/automation-playbooks.md](references/automation-playbooks.md). Read
it once the CRM is known; build from the list above when it is not.

---

## Deal Desk Processes

### When You Need a Deal Desk

- ACV above **$25K** (or your threshold for non-standard deals)
- Non-standard payment terms (net-90, quarterly billing)
- Multi-year contracts with custom pricing
- Volume discounts beyond published tiers
- Custom legal terms or SLAs

### Approval Workflow Tiers

| Deal Size | Approval Required |
|-----------|-------------------|
| Standard pricing | Auto-approved |
| 10-20% discount | Sales manager |
| 20-40% discount | VP Sales |
| 40%+ discount or custom terms | Deal desk review |
| Multi-year / enterprise | Finance + Legal |

### Non-Standard Terms Handling

Document every exception. Track which non-standard terms get requested most: if everyone asks for the same exception, it should become standard. Review quarterly.

---

## Data Hygiene & Enrichment

### Dedup Strategy

- **Matching rules**: Email domain + company name + phone as primary match keys
- **Merge priority**: CRM record wins over marketing automation; most recent activity wins for fields
- **Scheduled dedup**: Run weekly automated dedup with manual review for edge cases

### Required Fields Enforcement

- Enforce required fields at each lifecycle stage
- Block stage advancement if fields are empty
- Use progressive profiling: don't require everything upfront

Enrichment vendors are listed under Tool Integrations below, with the
provenance, freshness, lawful-basis, and credit-cost checks that apply before
proposing any of them.

### Quarterly Audit Checklist

- Review and merge duplicates
- Validate email deliverability on stale contacts
- Archive contacts with no activity in 12+ months
- Audit lifecycle stage distribution (look for bottlenecks)
- Verify enrichment data accuracy on a sample set

---

## RevOps Metrics Dashboard

### Key Metrics

Benchmark columns are illustrative starting ranges, not sourced industry figures. Replace each with the user's own trailing-quarter value before setting targets.

| Metric | Formula / Definition | Illustrative range |
|--------|---------------------|-----------|
| Lead-to-MQL rate | MQLs / Total leads | 5-15% |
| MQL-to-SQL rate | SQLs / MQLs | 30-50% |
| SQL-to-Opportunity | Opportunities / SQLs | 50-70% |
| Pipeline velocity | (# deals x avg deal size x win rate) / avg sales cycle | Varies by ACV |
| CAC | Total sales + marketing spend / new customers | LTV:CAC > 3:1 |
| LTV:CAC ratio | Customer lifetime value / CAC | 3:1 to 5:1 healthy |
| Speed-to-lead | Time from form fill to first rep contact | < 5 minutes ideal |
| Win rate | Closed-won / total opportunities | 20-30% (varies) |

### Dashboard Structure

Build three views:
1. **Marketing view**: Lead volume, MQL rate, source attribution, cost per MQL
2. **Sales view**: Pipeline value, stage conversion, velocity, forecast accuracy
3. **Executive view**: CAC, LTV:CAC, revenue vs. target, pipeline coverage

---

## Output Format

When delivering RevOps recommendations, provide:

1. **Lifecycle stage document**: Use the stage template shape in
   [references/lifecycle-definitions.md](references/lifecycle-definitions.md)
   for each stage: Entry criteria / Exit criteria / Owner / Actions on entry /
   SLA / Required fields / Recycle path. Do not invent a different shape.
2. **Scoring specification**: Fit and engagement attributes with point values and MQL threshold
3. **Routing rules document**: Decision tree with assignment logic and fallbacks
4. **Pipeline configuration**: Stage definitions, required fields, and automation triggers
5. **Metrics dashboard spec**: Key metrics, data sources, and target benchmarks

Format each as a standalone document the user can implement directly. Include platform-specific guidance when the CRM is known.

---

## Tool Integrations

These are evaluation examples, not guaranteed integrations. Verify the live
schema, authenticated account, permissions, API limits, pricing, and vendor
documentation before proposing implementation.

| Tool Category | Examples | Verify Before Use |
|---------------|----------|-------------------|
| CRM | HubSpot, Salesforce | Objects, fields, ownership, automation, permissions |
| Scheduling | Calendly, SavvyCal, Chili Piper | Routing logic, availability, privacy |
| Enrichment | HubSpot Breeze Intelligence (formerly Clearbit, whose standalone product was retired), Apollo, Clay, ZoomInfo | Provenance, freshness, lawful basis, credit cost |
| Automation | Zapier, Make, n8n, native CRM workflows | Trigger scope, retries, rollback, secrets |
| AI agents | CRM-native agents (HubSpot Breeze agents, Salesforce Agentforce), custom multi-agent workflows | Which steps run unattended, what they can write, audit log, human checkpoint |
| Partner operations | Crossbeam, partner-relationship tools | Account matching, deal rules, commissions |

### Where AI agents fit

Agents are good at the repetitive middle of revops: enriching a new lead, checking it against routing rules, drafting the first-touch email for rep approval, summarizing a call into CRM fields, and flagging stale deals. Keep three rules:
1. Agents read and draft freely; they write to the CRM only within fields and objects the owner approved, with every write logged.
2. Anything that contacts a prospect, changes ownership, or alters a deal amount stays behind a human checkpoint unless the user explicitly authorizes otherwise with caps.
3. Measure the agent like a rep: speed-to-lead, routing accuracy, and error rate per week.

Suede AI's Agent Studio (https://suedeai.app) builds and runs multi-agent workflows like these for teams that want them operated end to end; `suede-marketing-loops` designs the recurring checks and checkpoints either way.

---

## Boundaries

- Do not change production CRM fields, routing, automations, permissions, SLAs,
  ownership, or records without reading the live schema, previewing the exact
  effect, and receiving explicit approval.
- Do not delete, merge, deduplicate, enrich, or reassign records as a planning
  step, and do not expose personal data in reports.
- Do not redefine lifecycle stages or claim pipeline impact from modeled data;
  document assumptions and the stakeholders who must approve the operating
  rule.

## Routing

- Use `suede-prospecting` to build and qualify the source list.
- Use `suede-cold-email` for approved outbound sequence copy.
- Use `suede-sales-enablement` for collateral and rep-facing materials.
- Use `suede-analytics` for pipeline measurement and attribution.
- Use `suede-pricing` when deal-desk work turns into a pricing decision:
  discount tiers that keep getting overridden, a non-standard term everyone
  requests, or list-price and packaging changes.
