---
name: funnel-architect
description: "Design marketing funnels. Use when: mapping customer journeys, attribution modeling, or conversion paths."
---

# Funnel Architect

## When to Use This Skill

Activate this module when the user's request involves any of the following:

- **Funnel Design**: Building or restructuring a marketing/sales funnel for a specific business model
- **Customer Journey Mapping**: Visualizing the end-to-end path from first awareness to post-purchase advocacy
- **Attribution Modeling**: Determining how credit for conversions should be assigned across touchpoints
- **Funnel Analysis**: Diagnosing where prospects drop off and why
- **Conversion Path Optimization**: Improving the sequence of interactions that lead to conversion
- **Gap Analysis**: Identifying missing stages, touchpoints, or content in an existing funnel
- **Micro-Conversion Strategy**: Defining and optimizing the small commitments that lead to macro conversions

**Trigger phrases**: "funnel," "customer journey," "attribution," "conversion path," "where are we losing customers," "buyer journey," "TOFU/MOFU/BOFU," "lead nurture flow," "drop-off analysis," "touchpoint mapping," "pipeline," "conversion rate by stage"

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

Before executing funnel work, gather:

1. **Business Model**: SaaS, e-commerce, lead gen, marketplace, subscription, service-based, hybrid, etc.
2. **Current Funnel State**: Does a documented funnel exist? What stages are defined? What tools track it?
3. **Revenue Model**: How the business makes money (subscription, one-time purchase, freemium, etc.)
4. **Average Deal Size & Sales Cycle Length**: Critical for determining funnel complexity
5. **Key Conversion Actions**: What counts as a lead, MQL, SQL, opportunity, customer?
6. **Current Metrics**: Conversion rates between stages if available
7. **Tech Stack**: CRM, marketing automation, analytics platforms in use
8. **Team Structure**: Is there a separate sales team? Is it product-led growth? Who owns each funnel stage?

If the user cannot provide all context, use the business model to apply sensible defaults and note assumptions.

**Minimum viable context**: Business model and what the company sells. Everything else can be inferred from these two inputs and refined as more information surfaces.

## Capabilities

- **Business-Model-Adaptive Funnel Design**: Custom funnel architectures for 9 distinct business models (SaaS, e-commerce, lead gen, marketplace, subscription box, professional services, media/publishing, mobile app, B2B enterprise)
- **Journey Mapping with Emotion & Friction Points**: Visual journey maps that capture not just touchpoints but emotional states, friction moments, and decision triggers at each stage
- **Attribution Model Selection & Design**: Guidance on choosing the right attribution model (last-click, first-click, linear, time-decay, position-based, data-driven, custom) based on business context
- **Funnel Templates**: Pre-built, customizable funnel frameworks for 9 business models with default stages, KPIs, and conversion benchmarks
- **Gap Analysis**: Systematic identification of missing stages, content, touchpoints, or automation in an existing funnel
- **Micro-Conversion Definition**: Identifying and sequencing the small commitment actions that build toward macro conversion
- **Stage-by-Stage KPI Framework**: Defining the right metrics for every funnel stage so performance is measurable
- **Funnel Velocity Analysis**: Measuring how quickly prospects move through stages and identifying bottlenecks
- **Multi-Touch Journey Orchestration**: Designing coordinated touchpoint sequences across channels
- **Post-Purchase Funnel Extension**: Retention, expansion, and advocacy stage design

## Process

**Primary Workflow: Funnel Design & Optimization**

1. **Business Model Classification**
   - Identify the business model (or hybrid combination)
   - Determine the revenue model and typical sales cycle
   - Classify as product-led, sales-led, or hybrid growth motion
   - Select the appropriate funnel template as a starting framework

2. **Current State Assessment**
   - If an existing funnel is documented, map it stage by stage
   - Identify what metrics are currently tracked at each stage
   - Note where tracking breaks down or data goes dark
   - Document all current touchpoints (ads, content, emails, sales calls, product interactions)

3. **Journey Mapping**
   - Map the full customer journey from unaware to advocate
   - For each stage, document:
     - **Touchpoints**: What the prospect interacts with
     - **Actions**: What they do (micro-conversions)
     - **Emotions**: What they feel (excitement, confusion, hesitation, trust)
     - **Friction Points**: What slows them down or causes drop-off
     - **Decision Triggers**: What moves them to the next stage
     - **Content Needs**: What information they need at this moment
   - Include parallel paths (not all journeys are linear)

4. **Gap Analysis**
   - Compare current state against the ideal funnel for this business model
   - Identify missing stages or undefined transitions
   - Flag content gaps (stages with no supporting content)
   - Highlight automation gaps (manual handoffs that should be automated)
   - Detect measurement gaps (stages with no KPIs)
   - Spot channel gaps (stages served by only one channel)

5. **Funnel Architecture Design**
   - Define each stage with clear entry/exit criteria
   - Assign KPIs and conversion benchmarks to every stage
   - Design the micro-conversion sequence
   - Map content to each stage (existing and needed)
   - Specify automation triggers and rules
   - Define handoff protocols between marketing and sales (if applicable)

6. **Attribution Model Recommendation**
   - Based on funnel complexity, sales cycle length, and available data, recommend an attribution model
   - Explain trade-offs of the recommendation vs. alternatives
   - Provide implementation guidance for their tech stack

7. **Optimization Roadmap**
   - Prioritize improvements by impact and effort
   - Define A/B testing plan for high-impact stage transitions
   - Set up monitoring cadence for funnel health metrics
   - Create a 30/60/90-day optimization plan

**Secondary Workflow: Funnel Diagnosis (When a Funnel Exists but Underperforms)**

1. **Data Collection**
   - Gather conversion rates between every stage for the last 3-6 months
   - Pull time-to-conversion data (how long prospects spend at each stage)
   - Identify volume at each stage to build the full funnel waterfall

2. **Drop-Off Analysis**
   - Calculate the absolute and relative drop-off at each stage transition
   - Identify the single largest drop-off point (the "leaky bucket")
   - Segment drop-off by traffic source, device, geography, and audience segment
   - Determine if drop-off is a volume problem (not enough enter the stage) or a conversion problem (they enter but don't advance)

3. **Root Cause Identification**
   - For each high-drop-off transition, investigate:
     - Is the content at this stage compelling enough?
     - Is the CTA clear and the next step obvious?
     - Is there a friction point (long forms, confusing UX, required info the prospect does not have)?
     - Is the timing wrong (asking for too much too early)?
     - Is there a trust gap (insufficient social proof or credibility at this stage)?
   - Cross-reference with qualitative data (customer feedback, sales team input, session recordings) if available

4. **Fix Prioritization**
   - Score each identified issue on impact (how much conversion improvement is possible) and effort (how hard is the fix)
   - Focus on the highest-impact, lowest-effort fixes first
   - Design specific experiments to test each fix before full rollout

## Reference Files

- `journey-mapping.md` — Customer journey mapping methodology, emotion mapping framework, touchpoint cataloging, and journey visualization templates
- `attribution-models.md` — Detailed comparison of attribution models, selection criteria decision tree, implementation guides per platform, and custom model design
- `funnel-templates.md` — Pre-built funnel architectures for 9 business models with default stages, benchmarks, and customization guides
- `gap-analysis.md` — Gap analysis framework, diagnostic questions, common gap patterns by business model, and prioritization scoring

## Output Formats

| Deliverable | Format | Description |
|---|---|---|
| Funnel Architecture | Visual diagram + document | Stage-by-stage funnel with entry/exit criteria, KPIs, and content mapping |
| Customer Journey Map | Visual map + narrative | Full journey from awareness to advocacy with emotions, friction, and triggers |
| Gap Analysis Report | Document with priorities | All identified gaps with severity, impact score, and fix recommendations |
| Attribution Model Spec | Document | Recommended model with rationale, alternatives, and implementation steps |
| Stage KPI Dashboard | Table/spreadsheet spec | Metrics, benchmarks, and tracking methodology for every funnel stage |
| Micro-Conversion Map | Diagram + document | Sequenced small-commitment actions that build toward macro conversions |
| Funnel Optimization Roadmap | Prioritized plan | 30/60/90-day plan with specific actions, owners, and expected impact |

## Edge Cases

### Hybrid Business Models
- **Situation**: Business combines multiple models (e.g., SaaS with a marketplace component, or e-commerce with subscription)
- **Approach**: Build a primary funnel based on the dominant revenue model, then layer in secondary paths. Identify where the funnels diverge and converge. Create distinct stage definitions for each path but unified attribution. Do not force-fit a single template — hybrid models need hybrid funnels.

### Two-Sided Marketplaces
- **Situation**: Business serves both supply side (sellers, providers) and demand side (buyers, consumers)
- **Approach**: Design parallel funnels for each side. Map interdependencies (where one side's funnel stage depends on the other side's activity). Identify the "chicken and egg" dynamics and design the funnel to solve for the constrained side first. Track marketplace liquidity metrics alongside conversion metrics.

### Offline-to-Online Journeys
- **Situation**: Significant portion of the journey happens offline (events, retail, phone calls, field sales)
- **Approach**: Create explicit "dark funnel" stages where tracking is limited. Design bridge mechanisms (QR codes, unique URLs, call tracking numbers, CRM manual entry) to connect offline interactions to the digital funnel. Acknowledge measurement limitations honestly and recommend proxy metrics where direct tracking is impossible.

### Very Long B2B Cycles (12+ Months)
- **Situation**: Enterprise sales with buying committees, RFPs, legal review, and 12-24 month cycles
- **Approach**: Build a milestone-based funnel rather than a time-based one. Design for buying committee dynamics (champion, economic buyer, technical evaluator, legal). Include "re-engagement" loops for stalled deals. Use account-level scoring rather than individual lead scoring. Attribution must be multi-touch with heavy time-decay weighting. Content needs are deep and stage-specific — exec summaries for C-suite, technical docs for evaluators, ROI models for finance.

### Product-Led Growth (PLG) Funnels
- **Situation**: Product usage IS the primary funnel mechanism — users self-serve through a free tier or trial before converting
- **Approach**: The funnel is driven by product engagement, not traditional marketing touches. Design around activation milestones (the "aha moments" in the product). Map the progression from signup to activation to engagement to conversion to expansion. Define product-qualified leads (PQLs) based on usage thresholds rather than marketing-qualified leads. Integrate product analytics (Amplitude, Mixpanel, Pendo) as the primary funnel tracking tool. Marketing's role shifts toward driving signups and supporting activation through in-app messaging, onboarding emails, and educational content.

### Funnel with No Existing Data
- **Situation**: New business or new market with no historical funnel data to analyze
- **Approach**: Build a hypothesis funnel using industry benchmarks and business model templates. Define stage conversion rate assumptions clearly and label them as hypotheses. Design the funnel with measurement baked in from day one so data accumulates quickly. Recommend a 90-day "instrument and learn" phase where the goal is data collection and assumption validation, not optimization. Set minimum traffic/volume thresholds for each stage before drawing conclusions from conversion rates.

## Related Skills

- **Campaign Orchestrator** — For executing the campaigns that drive traffic into the funnel and move prospects through stages
- **Audience Intelligence** — For understanding who enters the funnel, building personas for each stage, and segmenting by funnel behavior
- **Analytics & Insights** — For measuring funnel performance, attribution analysis, and anomaly detection in conversion rates
- **Content Engine** — For creating the stage-specific content mapped to each funnel touchpoint
- **AEO/GEO Intelligence** — For optimizing the top-of-funnel awareness stage where AI-generated answers drive discovery
