---
name: audience-intelligence
description: "Research target audiences. Use when: buyer personas, segmentation, Jobs-to-Be-Done, psychographic profiling, audience deep-dive."
---

# Audience Intelligence

## When to Use This Skill

Activate this module when the user's request involves any of the following:

- **Buyer Persona Creation**: Building detailed profiles of ideal customers for marketing and product decisions
- **Audience Research**: Understanding who a brand's customers or prospects are at a demographic, psychographic, and behavioral level
- **Segmentation Strategy**: Dividing an audience into meaningful groups for targeted marketing
- **Jobs-to-Be-Done (JTBD) Analysis**: Identifying the functional, social, and emotional jobs customers hire a product to do
- **Psychographic Profiling**: Understanding audience values, attitudes, interests, lifestyles, and motivations
- **Anti-Persona Definition**: Defining who is NOT the target customer to prevent wasted spend
- **Audience Sizing & TAM Estimation**: Estimating the size of addressable audience segments

**Trigger phrases**: "buyer persona," "target audience," "who are our customers," "customer profile," "segmentation," "audience segments," "Jobs-to-Be-Done," "JTBD," "psychographic," "ideal customer profile," "ICP," "anti-persona," "lookalike audience," "audience research," "buying committee," "customer avatar"

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

Before executing audience intelligence work, gather:

1. **Business Description**: What does the company sell, to whom, and what problem does it solve?
2. **Existing Customer Data**: Any analytics, CRM data, survey results, or customer interviews available
3. **Product/Service Details**: Features, pricing, positioning, and key differentiators
4. **Current Audience Assumptions**: Who does the team think their customers are today?
5. **Market Context**: Industry, competitive landscape, market maturity
6. **Geographic Scope**: Local, regional, national, or global audience
7. **Business Model**: B2B, B2C, B2B2C, D2C — this fundamentally shapes persona structure
8. **Sales Process**: Self-serve, sales-assisted, enterprise sales — determines decision-maker mapping

If the user has minimal data, build hypothesis-driven personas based on business model, product, and market analysis. Label these clearly as hypotheses to be validated.

## Capabilities

- **Multi-Dimensional Persona Building**: Personas built across six dimensions:
  - **Demographic**: Age, gender, location, income, education, job title, company size
  - **Psychographic**: Values, attitudes, lifestyle, personality traits, motivations
  - **Behavioral**: Purchase patterns, channel preferences, content consumption, decision-making style
  - **Need-State**: Current pain points, unmet needs, desired outcomes, urgency level
  - **Information**: Where they research, who they trust, content format preferences, information journey
  - **Decision**: Decision criteria, objections, influencers, timeline, risk tolerance
- **JTBD Framework**: Mapping functional jobs (what they need done), social jobs (how they want to be perceived), and emotional jobs (how they want to feel) with outcome-driven innovation metrics
- **RFM Segmentation**: Recency, Frequency, Monetary value analysis for customer base segmentation
- **Behavioral Segmentation**: Grouping by usage patterns, engagement levels, and purchase behavior
- **Value-Based Segmentation**: Grouping by customer lifetime value and profitability potential
- **Lifecycle Segmentation**: Grouping by customer lifecycle stage (prospect, new, active, at-risk, churned, win-back)
- **Lookalike Audience Guidance**: Defining seed audience characteristics for platform-based lookalike targeting
- **Anti-Persona Definition**: Explicitly defining who should be excluded from targeting to prevent wasted spend and misaligned messaging
- **Buying Committee Mapping**: For B2B, mapping all roles involved in purchase decisions with their individual motivations and objections

## Process

**Primary Workflow: Persona Development & Segmentation**

1. **Discovery & Data Collection**
   - Gather all available customer data (analytics, CRM exports, survey results, interview transcripts)
   - Review existing marketing materials, landing pages, and ads for implicit audience assumptions
   - Analyze competitor targeting (who are they going after? what messaging do they use?)
   - If no data exists, conduct a market analysis to build hypothesis personas
   - Document the data quality level: data-rich, data-limited, or hypothesis-only

2. **JTBD Analysis**
   - Identify the core job the customer is hiring the product to do
   - Map functional jobs: What task needs to be accomplished?
   - Map social jobs: How does the customer want to be perceived by others?
   - Map emotional jobs: How does the customer want to feel?
   - Identify the "struggling moment" — what triggers the search for a solution?
   - Document competing solutions (including non-consumption and manual workarounds)
   - Define desired outcomes and how customers measure success

3. **Persona Construction**
   - Build 3-5 primary personas (avoid persona proliferation)
   - For each persona, complete all six dimensions:
     - **Demographic profile**: Concrete characteristics with ranges, not single points
     - **Psychographic profile**: Values, beliefs, lifestyle factors that influence purchase decisions
     - **Behavioral profile**: How they buy, where they spend time, what content they consume
     - **Need-state profile**: Specific pain points, urgency drivers, and desired outcomes
     - **Information profile**: Research behavior, trusted sources, content preferences
     - **Decision profile**: Criteria, objections, influencers, and timeline
   - Give each persona a memorable name and narrative (but avoid stereotyping)
   - Assign estimated segment size and revenue potential
   - Prioritize personas by business impact

4. **Anti-Persona Development**
   - Define 1-3 anti-personas: people who may seem like targets but are poor fits
   - Common anti-persona types: price-sensitive bargain hunters (for premium brands), feature-seekers who will never buy (tire kickers), wrong company size or industry
   - Document specific signals that identify anti-personas in your data
   - Create exclusion criteria for ad targeting and lead qualification

5. **Segmentation Strategy**
   - Select the segmentation approach based on available data and business needs:
     - **RFM**: When transaction data is available — score by recency, frequency, monetary value
     - **Behavioral**: When usage/engagement data exists — group by behavior patterns
     - **Value-based**: When LTV data is available — prioritize high-value segments
     - **Lifecycle**: When customer journey stage data exists — customize by stage
     - **Needs-based**: When qualitative research is available — group by pain point
   - Define segment boundaries and naming conventions
   - Map segments to personas (segments are data-driven groups; personas are the human stories within them)
   - Assign channel and messaging strategies per segment

6. **Activation Planning**
   - For each persona/segment, define:
     - Priority channels for reaching them
     - Messaging themes and value propositions that resonate
     - Content types and formats they prefer
     - Lookalike audience seed criteria for paid platforms
     - Lead scoring rules based on persona fit
   - Create a persona-to-campaign mapping guide
   - Build a validation plan to test persona hypotheses with real campaign data

## Reference Files

- `persona-builder.md` — Six-dimension persona template, persona interview guide, data-to-persona methodology, and persona validation framework
- `jtbd-framework.md` — Jobs-to-Be-Done analysis methodology, job mapping canvas, outcome-driven innovation scoring, and competing solutions analysis
- `segmentation.md` — RFM scoring model, behavioral segmentation framework, lifecycle segmentation definitions, and segment-to-action mapping
- `psychographic-profiling.md` — Values and attitudes framework, lifestyle analysis, motivation mapping, and psychographic data collection methods

## Output Formats

| Deliverable | Format | Description |
|---|---|---|
| Buyer Persona Document | Document (per persona) | Complete six-dimension persona with narrative, data points, and activation guidance |
| Persona Summary Card | One-page visual | Quick-reference persona card for team alignment |
| JTBD Analysis | Document | Job map, struggling moments, desired outcomes, and competing solutions |
| Segmentation Model | Spreadsheet + document | Segment definitions, criteria, sizes, and strategy per segment |
| Anti-Persona Profiles | Document | Who to exclude, why, and identification signals |
| Buying Committee Map | Visual diagram + document | B2B decision-maker map with roles, motivations, and influence paths |
| Audience Activation Guide | Document | Channel, messaging, and content recommendations per persona/segment |
| Lookalike Audience Spec | Document | Seed audience criteria and platform-specific setup instructions |

## Edge Cases

### B2B Buying Committees (Multiple Personas per Deal)
- **Situation**: Enterprise B2B purchases involve 6-10 decision-makers with different roles, motivations, and objections
- **Approach**: Build individual personas for each buying committee role: Champion (internal advocate), Economic Buyer (controls budget), Technical Evaluator (assesses capabilities), End User (daily user), Legal/Procurement (risk and compliance), Executive Sponsor (strategic alignment). Map influence relationships between roles. Design content and messaging specific to each role's concerns. Create a "buying committee journey" that shows how roles engage at different stages. Note that the Champion persona is usually the most critical — they sell internally on your behalf.

### Two-Sided Marketplace Audiences
- **Situation**: Platform serves both supply side (sellers, creators, providers) and demand side (buyers, consumers)
- **Approach**: Build completely separate persona sets for each side. Map the interdependencies — how does the supply-side experience affect demand-side personas, and vice versa? Identify the "chicken and egg" constraint: which side must be built first? Create cross-side personas that exist on both sides (e.g., a seller who also buys). Design distinct messaging, channels, and value propositions for each side.

### Limited Data Environments
- **Situation**: Startup or new market entry with no customer data, no CRM, no analytics history
- **Approach**: Build hypothesis personas using market research, competitor analysis, industry reports, and founder/team domain knowledge. Label all personas explicitly as "Hypothesis — Version 1" to set expectations. Design a rapid validation plan: run small targeted campaigns to test persona assumptions. Define specific signals that would confirm or invalidate each persona. Plan to iterate personas after 30-60 days of market data. Use JTBD analysis (which can be done through market observation) as the primary framework when demographic data is unavailable.

### Global Audiences with Cultural Differences
- **Situation**: Audience spans multiple countries, cultures, and languages with fundamentally different values and behaviors
- **Approach**: Do NOT create a single global persona. Build regional persona variants that share a core structure but diverge on cultural dimensions: communication style, decision-making process, trust signals, channel preferences, and value hierarchy. Research cultural dimensions (Hofstede framework as a starting point) for key markets. Flag markets where the product positioning may need fundamental reframing, not just translation. Recommend local market validation before scaling campaigns internationally. Be explicit about the limits of cultural generalization — personas are starting points, not stereotypes.

## Related Skills

- **Funnel Architect** — For mapping personas to funnel stages and designing stage-appropriate touchpoints for each audience segment
- **Content Engine** — For creating persona-specific content, messaging, and creative assets
- **Campaign Orchestrator** — For targeting personas through campaigns and allocating budget by segment priority
- **Analytics & Insights** — For validating persona hypotheses with behavioral data and refining segments over time
- **AEO/GEO Intelligence** — For understanding what AI platforms tell your audience about your brand and optimizing for their AI-powered research behavior
