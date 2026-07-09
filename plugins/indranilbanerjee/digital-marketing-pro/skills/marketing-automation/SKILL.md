---
name: marketing-automation
description: "Design marketing automation workflows. Use when: building lead scoring, nurture sequences, drip campaigns, or behavioral triggers."
---

# Marketing Automation

## When to Use This Skill

Activate this module when the user's request involves any of the following:

- **Workflow Design**: Building, mapping, or optimizing automated marketing workflows and sequences
- **Lead Scoring**: Creating or refining lead scoring models, defining MQL/SQL thresholds, or troubleshooting scoring accuracy
- **Nurture Sequences**: Designing email nurture campaigns, drip sequences, or lifecycle-stage-based communication flows
- **Drip Campaigns**: Time-based or behavior-based automated email series for onboarding, education, or conversion
- **Behavioral Triggers**: Setting up event-based automation triggers (page visits, form fills, email engagement, product usage)
- **Lifecycle Marketing**: Mapping and automating communication across subscriber, lead, MQL, SQL, customer, and advocate stages
- **Marketing Operations**: Data hygiene, process optimization, tech stack management, deliverability, and compliance automation
- **Platform Strategy**: Selecting, configuring, or migrating between marketing automation platforms (HubSpot, ActiveCampaign, Klaviyo, Mailchimp, Marketo, Pardot)
- **Integration Patterns**: Connecting MAP to CRM, CDP, analytics, ad platforms, or custom data sources
- **Reporting & Attribution**: Measuring automation performance, sequence attribution, and lifecycle velocity
- **Cross-Channel Orchestration**: Coordinating automated touchpoints across email, SMS, push notifications, in-app messaging, and retargeting

**Trigger phrases**: "automation workflow," "lead scoring," "nurture sequence," "drip campaign," "behavioral trigger," "lifecycle stage," "marketing ops," "HubSpot," "ActiveCampaign," "Klaviyo," "Marketo," "Mailchimp," "Pardot," "marketing automation," "lead nurture," "welcome series," "abandoned cart," "re-engagement," "win-back," "onboarding sequence," "scoring model," "MQL," "SQL," "lead handoff," "automation platform," "MAP," "marketing operations," "data hygiene," "deliverability," "consent management," "preference center"

## Brand Context (Auto-Applied)

Before producing any marketing output from this module:

1. **Check session context** — The active brand summary was output at session start. Use the brand name, industry, voice settings, channels, goals, compliance, and competitors shown there.
2. **If you need the full profile**, read: `~/.claude-marketing/brands/{slug}/profile.json`
3. **Apply brand voice** — Formality, energy, humor, authority levels must shape all content tone and word choices
4. **Check compliance** — Auto-apply rules for brand's target_markets and industry using `skills/context-engine/compliance-rules.md`
5. **Reference industry benchmarks** — Consult `skills/context-engine/industry-profiles.md` for the brand's industry
6. **Use platform specs** — Reference `skills/context-engine/platform-specs.md` for character limits and format requirements
7. **Check campaign history** — Run `python campaign-tracker.py --brand {slug} --action list-campaigns` before planning new work
8. **If no brand exists**, say: "No brand profile found. Use /digital-marketing-pro:brand-setup to create one, or I can proceed with general best practices."
9. **Check brand guidelines** — If `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` exists, load and enforce: `restrictions.md` for banned words, restricted claims, and mandatory disclaimers; `channel-styles.md` for channel-specific tone overrides (may differ from base voice); `messaging.md` for approved key messages, taglines, and positioning language; `voice-and-tone.md` for detailed voice rules beyond the 4 numeric scores. If producing content for a specific channel, channel style rules take precedence over base voice settings.

Do not ask the user for information that already exists in their brand profile.

## Required Context

Before executing automation work, gather:

1. **Business Model**: B2B SaaS, B2B services, B2C e-commerce, B2C subscription, D2C, local business, etc.
2. **Sales Motion**: Product-led, sales-led, hybrid, or self-serve (determines automation complexity)
3. **Current Platform**: Which MAP is in use? CRM? CDP? (or is this a greenfield selection)
4. **Lifecycle Stages**: Are stages defined? What criteria determine each stage transition?
5. **Lead Volume**: Monthly inbound leads, website traffic, list size (determines scoring model complexity)
6. **Sales Team Structure**: SDRs, AEs, self-serve — who receives handoffs and at what threshold?
7. **Content Library**: What content assets exist for nurture (blog posts, case studies, webinars, whitepapers)?
8. **Current Automations**: What workflows already exist? Are they performing?
9. **Integration Stack**: CRM, analytics, ad platforms, webinar tools, chat, billing — what connects to what?
10. **Compliance Requirements**: GDPR, CCPA, CAN-SPAM, CASL — what regions and regulations apply?

For quick requests (e.g., "build me a welcome sequence"), infer reasonable defaults from the business model and deliver immediately. For strategic automation architecture, gather full context.

## Capabilities

- **Workflow Design & Architecture**: End-to-end automation workflow mapping, trigger design, branching logic, wait steps, goal conditions, and exit criteria for any marketing scenario
- **Lead Scoring Models**: Explicit scoring (demographic/firmographic fit), implicit scoring (behavioral engagement), negative scoring (disqualifiers), score decay, and threshold calibration for MQL/SQL handoff
- **Nurture Sequence Design**: Stage-specific nurture campaigns with content mapping, cadence optimization, personalization layers, and progressive profiling strategies
- **Drip Campaign Engineering**: Time-based and behavior-based drip architectures for welcome series, abandoned cart recovery, post-purchase follow-up, onboarding, re-engagement, and win-back
- **Behavioral Trigger Systems**: Event-based automation using page views, email engagement, form submissions, product usage events, purchase history, and custom events
- **Lifecycle Stage Management**: Stage definitions, transition criteria, automated stage progression, stage-based content strategy, and lifecycle velocity tracking
- **Cross-Channel Orchestration**: Coordinating email, SMS, push notifications, in-app messaging, direct mail triggers, and retargeting audiences within unified workflows
- **Marketing Operations**: Data hygiene automation (deduplication, normalization, enrichment), process optimization, campaign request workflows, QA checklists, and approval gates
- **Deliverability Management**: Sender reputation monitoring, authentication setup (SPF, DKIM, DMARC), IP warm-up planning, list hygiene automation, and inbox placement optimization
- **Compliance Automation**: Consent management workflows, preference center design, suppression list management, GDPR/CCPA automated data handling, and unsubscribe processing
- **Platform Strategy**: MAP selection criteria, feature comparison across HubSpot, ActiveCampaign, Klaviyo, Mailchimp, Marketo, and Pardot — migration planning and implementation roadmaps
- **Integration Architecture**: CRM sync patterns, bi-directional data flows, webhook design, API integration strategy, and data transformation logic between systems
- **Reporting & Attribution**: Automation performance dashboards, sequence-level attribution, lifecycle velocity metrics, engagement scoring analysis, and ROI measurement for automation programs

## Process

**Primary Workflow: Automation Strategy & Build**

1. **Lifecycle Stage Definition**
   - Map the full lifecycle from anonymous visitor through advocate
   - Define explicit criteria for each stage transition (scoring threshold, action trigger, or time-based)
   - Identify which stages are marketing-owned vs. sales-owned
   - Establish SLAs for stage transitions (e.g., MQL-to-SQL response time)

2. **Lead Scoring Model Design**
   - Build explicit scoring based on demographic/firmographic fit
   - Layer implicit scoring from behavioral engagement signals
   - Add negative scoring for disqualifiers and inactivity decay
   - Set MQL and SQL thresholds with the sales team
   - Define the handoff process and feedback loop for scoring accuracy

3. **Workflow Architecture**
   - Map all required automation workflows (welcome, nurture, scoring, handoff, re-engagement, etc.)
   - For each workflow, define: trigger, entry criteria, steps, branching logic, wait times, exit conditions, and success metric
   - Design cross-channel coordination rules (when to email vs. SMS vs. push)
   - Build suppression and frequency capping logic to prevent over-communication

4. **Nurture Sequence Design**
   - Map content to each lifecycle stage and persona
   - Design cadence and timing based on business model (B2B vs. B2C) and industry benchmarks
   - Layer personalization: name, company, industry, behavior-based content blocks, stage-appropriate messaging
   - Define exit triggers (converted, unsubscribed, disqualified, moved to different sequence)
   - Plan A/B tests within sequences (subject lines, send times, content variants)

5. **Implementation & Testing**
   - Build workflows in the MAP with proper naming conventions
   - Test every branch path with sample contacts before activation
   - Verify integrations fire correctly (CRM sync, scoring updates, handoff notifications)
   - Confirm suppression rules prevent conflicts between active workflows
   - Set up monitoring alerts for error rates and unexpected drops in flow completion

6. **Optimization & Reporting**
   - Define KPIs per workflow (completion rate, conversion rate, time-to-convert, engagement rate)
   - Build reporting dashboard for automation program performance
   - Establish review cadence (weekly for active campaigns, monthly for scoring model accuracy)
   - Document learnings and feed back into workflow refinement

**Secondary Workflow: Automation Audit & Optimization**

1. Pull inventory of all active workflows, their trigger conditions, and current performance
2. Identify zombie workflows (active but no contacts entering), underperformers (low completion or conversion), and conflicts (overlapping triggers or suppression gaps)
3. Audit lead scoring accuracy by comparing score-to-conversion correlation
4. Review data hygiene (duplicate rates, field completeness, decay)
5. Assess deliverability health (bounce rates, spam complaints, authentication status)
6. Prioritize fixes by revenue impact and implementation effort

## Reference Files

- `automation-workflows.md` — Workflow design patterns, trigger types, branching logic, cross-channel orchestration, testing methodology, and common anti-patterns
- `lead-scoring.md` — Explicit and implicit scoring models, point value frameworks, threshold calibration, decay rates, and scoring models by business type
- `nurture-sequences.md` — Lifecycle-stage nurture design, sequence templates, cadence optimization, personalization layers, and content mapping frameworks
- `marketing-ops.md` — Data hygiene automation, tech stack management, deliverability, compliance automation, team workflows, and platform comparison matrix

## Agents Used

- **email-specialist** — Automation sequence content, subject line optimization, deliverability management, and email-specific workflow design
- **analytics-analyst** — Automation performance tracking, scoring model accuracy analysis, lifecycle velocity reporting, and attribution for automated touchpoints
- **marketing-strategist** — Lifecycle strategy alignment, cross-channel orchestration planning, automation program ROI, and business-model-specific automation architecture

## Output Formats

| Deliverable | Format | Description |
|---|---|---|
| Automation Workflow Map | Document + diagram | Visual workflow with triggers, steps, branches, wait times, exit conditions, and KPIs |
| Lead Scoring Model | Document + spreadsheet | Complete scoring rubric with explicit/implicit criteria, point values, thresholds, and decay rules |
| Nurture Sequence Plan | Document | Full sequence with email content briefs, timing, personalization rules, and A/B test plan |
| Lifecycle Stage Framework | Document + diagram | Stage definitions, transition criteria, ownership, SLAs, and content mapped to each stage |
| Marketing Ops Audit | Document + checklist | Data hygiene assessment, deliverability health check, process review, and prioritized fixes |
| Platform Recommendation | Document + comparison matrix | Scored evaluation of MAP options with migration plan and implementation timeline |
| Automation Performance Report | Dashboard spec + document | KPIs per workflow, scoring accuracy, lifecycle velocity, and optimization recommendations |

## Edge Cases

### No Existing Automation (Greenfield)
- **Situation**: Business has no marketing automation platform or workflows in place
- **Approach**: Start with the minimum viable automation stack: (1) Select a MAP appropriate for the business size and model. (2) Build the three highest-impact workflows first — welcome series, lead scoring with basic handoff, and one re-engagement sequence. (3) Establish baseline metrics before optimizing. (4) Add complexity incrementally after the foundation is stable. Do not attempt to build a 50-workflow automation program from scratch — it will be unmaintainable. Crawl, walk, run.

### Platform Migration
- **Situation**: Migrating from one MAP to another (e.g., Mailchimp to HubSpot, or HubSpot to Marketo)
- **Approach**: Migration is a project, not a task. (1) Audit all existing workflows, lists, scoring rules, and integrations in the current platform. (2) Map feature parity — identify what translates directly vs. what needs redesign. (3) Clean data before migrating (do not migrate dirty data into a clean system). (4) Run platforms in parallel during transition with clear cutover criteria. (5) Re-test every workflow post-migration. (6) Plan for a 2-4 week stabilization period where performance may dip. Never do a "big bang" migration on a Friday.

### Over-Automation (Too Many Active Workflows)
- **Situation**: Contacts are enrolled in multiple competing workflows, receiving excessive communications, or experiencing contradictory messaging
- **Approach**: This is the most common automation failure mode. (1) Audit all active workflows and map potential overlaps. (2) Implement strict suppression rules — a contact should be in ONE primary nurture at a time. (3) Build a priority hierarchy (transactional > behavioral trigger > active campaign > evergreen nurture). (4) Add global frequency caps (e.g., max 3 marketing emails per week). (5) Create a workflow governance document that requires approval before launching new automations. Automation without governance leads to subscriber fatigue and unsubscribes.

### Low Lead Volume (<100 Leads/Month)
- **Situation**: Business does not generate enough leads to justify complex scoring models or multi-branch workflows
- **Approach**: Simplify everything. (1) Skip lead scoring entirely — at low volumes, a human can review every lead. (2) Build simple linear sequences instead of complex branching workflows. (3) Focus on 2-3 high-quality nurture emails rather than a 12-email sequence. (4) Use behavioral triggers sparingly (pricing page visit and demo request are enough). (5) Invest in lead generation before investing in lead automation. Automation scales efficiency — but there must be something to scale first.

### Regulated Industries (Healthcare, Finance, Legal)
- **Situation**: Automation must comply with industry-specific regulations beyond standard CAN-SPAM/GDPR
- **Approach**: Layer industry compliance on top of standard email compliance. (1) For healthcare: HIPAA-compliant platforms only, no PHI in email, explicit consent for health-related communications. (2) For financial services: required disclosures in every communication, fair lending language, FINRA review for investment content. (3) For legal: bar association advertising rules vary by jurisdiction, avoid guarantees of outcomes. (4) Build compliance checks into workflow approval gates — no automation goes live without compliance review. (5) Log all consent and communication history for audit trails. (6) Recommend platforms with built-in compliance features for regulated industries.

### B2C High-Volume Transactional + Marketing Coexistence
- **Situation**: E-commerce or subscription business sends both transactional emails (order confirmation, shipping, receipts) and marketing emails from the same platform
- **Approach**: Separate transactional and marketing sending infrastructure. (1) Use dedicated IPs or subdomains for transactional vs. marketing email. (2) Never suppress transactional emails based on marketing preferences — they are legally distinct. (3) Do not insert marketing content into transactional emails (this reclassifies them as marketing under CAN-SPAM). (4) Monitor deliverability separately for each stream. (5) Ensure unsubscribe from marketing does not affect transactional delivery. Most MAPs handle this natively, but verify the configuration.

## Related Skills

- **Content Engine** — For creating the email copy, subject lines, and content assets that populate automation workflows
- **Funnel Architect** — For aligning automation workflows to funnel stages and ensuring every stage transition is supported by the right sequence
- **Analytics & Insights** — For measuring automation performance, lifecycle velocity, and building attribution models for automated touchpoints
- **Audience Intelligence** — For persona-based nurture design, behavioral segmentation, and enriching lead scoring with audience insights
- **CRO** — For optimizing the landing pages and forms that feed leads into automation workflows
- **Campaign Orchestrator** — For coordinating automation-driven campaigns with broader campaign strategy and cross-channel planning
