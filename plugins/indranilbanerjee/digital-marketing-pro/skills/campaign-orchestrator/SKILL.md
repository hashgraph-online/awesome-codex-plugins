---
name: campaign-orchestrator
description: "Orchestrate full campaign lifecycle. Use when: planning, launching, managing, UTM setup, media plan, post-mortem."
---

# Campaign Orchestrator

## When to Use This Skill

Activate this module when the user's request involves any of the following:

- **Campaign Planning**: Designing a new marketing campaign from brief to launch plan
- **Budget Allocation**: Distributing marketing spend across channels, campaigns, or time periods
- **Channel Mix Optimization**: Selecting and balancing the right marketing channels for a goal
- **Media Planning**: Building a media plan with placements, timing, and spend
- **UTM Tracking**: Standardizing URL tracking parameters for campaign measurement
- **Cross-Channel Orchestration**: Coordinating messaging and timing across multiple channels
- **Campaign Post-Mortem**: Analyzing completed campaigns to extract learnings
- **ABM Campaign Planning**: Designing account-based marketing campaigns for targeted accounts
- **Campaign Calendar**: Building a time-sequenced plan of campaign activities

**Trigger phrases**: "campaign plan," "marketing budget," "budget allocation," "channel mix," "media plan," "UTM," "tracking parameters," "launch campaign," "campaign review," "post-mortem," "what worked," "ABM," "account-based," "media buy," "ad spend," "70/20/10"

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

Before executing campaign work, gather:

1. **Campaign Objective**: What is the primary goal? (Awareness, lead gen, revenue, retention, product launch, event, etc.)
2. **Budget**: Total available spend and any constraints on allocation
3. **Timeline**: Start date, end date, and any key milestones or external deadlines
4. **Target Audience**: Who is this campaign for? (Link to Audience Intelligence module if personas exist)
5. **Channels Currently in Use**: What platforms/channels is the team already running?
6. **Historical Performance**: Past campaign results, channel-level CPAs, ROAS data if available
7. **Creative Assets**: What exists? What needs to be created?
8. **Tech Stack**: Ad platforms, automation tools, CRM, analytics tools in use
9. **Team Capacity**: Who will execute? In-house team, agency, or hybrid?
10. **Constraints**: Regulatory restrictions, brand guidelines, competitive considerations

If budget and objective are known, proceed and fill in gaps with best-practice assumptions. Always document assumptions.

## Capabilities

- **Campaign Brief Generation**: Structured briefs covering objective, audience, messaging, channels, timeline, budget, KPIs, and creative requirements
- **Budget Allocation Models**: Three proven frameworks:
  - **70/20/10**: 70% proven channels, 20% promising channels, 10% experimental
  - **Efficiency-Ranked**: Allocate by channel CPA/ROAS performance data
  - **Funnel-Weighted**: Distribute budget based on where the funnel needs most investment
- **Channel Mix Optimization**: Data-informed channel selection based on audience, objective, budget, and industry benchmarks
- **UTM Standardization**: Complete UTM taxonomy with naming conventions, URL builder specs, and governance rules
- **Cross-Channel Orchestration**: Sequencing and coordinating touchpoints across channels for cohesive campaign experience
- **Campaign Post-Mortem**: Structured analysis framework covering performance vs. goals, channel contribution, creative performance, audience insights, and actionable learnings
- **ABM Campaign Planning**: Account selection, personalization tiers, multi-channel orchestration for target accounts, and sales-marketing alignment
- **Media Plan Templates**: Detailed plans with placements, formats, targeting, budgets, schedules, and expected performance
- **Campaign Risk Assessment**: Identifying potential failure points and mitigation strategies before launch

## Process

**Primary Workflow: Campaign Planning & Execution**

1. **Campaign Brief Development**
   - Define the SMART objective (Specific, Measurable, Achievable, Relevant, Time-bound)
   - Document the target audience (reference existing personas or build lightweight ones)
   - Craft the core campaign message and value proposition
   - Define the primary CTA and desired conversion action
   - Set primary and secondary KPIs with specific targets
   - Identify the campaign theme/concept if creative direction is needed

2. **Budget Allocation**
   - Select the allocation model based on available data:
     - **No historical data**: Use 70/20/10 with industry benchmarks
     - **Some performance data**: Use efficiency-ranked allocation
     - **Mature program with funnel data**: Use funnel-weighted allocation
   - Build the budget breakdown by channel, by week/month
   - Include production costs (creative, landing pages, tools) in the budget
   - Set aside 10-15% contingency for mid-campaign optimization
   - Define budget reallocation triggers (e.g., "shift budget from Channel A to B if CPA exceeds $X by week 3")

3. **Channel Strategy & Media Plan**
   - Select channels based on audience presence, objective fit, and budget constraints
   - For each channel, define:
     - Targeting parameters
     - Ad formats and placements
     - Messaging variation (adapt core message to channel context)
     - Budget and schedule
     - Expected performance (impressions, clicks, conversions, CPA)
   - Sequence touchpoints across channels (awareness channels fire first, retargeting follows)
   - Design the cross-channel frequency cap strategy

4. **UTM & Tracking Setup**
   - Build the UTM taxonomy for this campaign:
     - `utm_source`: Platform (google, facebook, linkedin, email, etc.)
     - `utm_medium`: Channel type (cpc, social, email, display, etc.)
     - `utm_campaign`: Campaign name (standardized naming convention)
     - `utm_term`: Keyword or targeting (for paid search, audience segment)
     - `utm_content`: Creative variant (ad-a, ad-b, hero-video, etc.)
   - Generate all campaign URLs with UTMs applied
   - Verify tracking pixels and conversion events are configured
   - Test the full tracking chain before launch

5. **Launch Checklist**
   - Creative assets approved and uploaded
   - Landing pages live and tested (load speed, mobile, forms, tracking)
   - UTM links verified and click-tested
   - Conversion tracking confirmed with test conversions
   - Budget and schedules set correctly in all platforms
   - Team roles and escalation paths defined
   - Monitoring dashboard set up with real-time KPIs

6. **In-Flight Optimization**
   - Define the check-in cadence (daily for first week, then weekly)
   - Set optimization triggers and rules (when to pause, scale, or shift)
   - A/B test creative and messaging variations
   - Monitor for ad fatigue, audience saturation, and competitive interference
   - Execute budget reallocation based on pre-defined triggers

7. **Post-Mortem & Learning Extraction**
   - Performance vs. target for every KPI
   - Channel-by-channel contribution analysis
   - Creative performance ranking
   - Audience segment performance
   - What worked, what didn't, and why
   - Specific recommendations for the next campaign
   - Updated benchmarks for future budget allocation

## Reference Files

- `campaign-planning.md` — Campaign brief template, SMART objective framework, and campaign concept development process
- `budget-allocation.md` — Detailed allocation models (70/20/10, efficiency-ranked, funnel-weighted), reallocation triggers, and budget template
- `channel-strategy.md` — Channel selection matrix, channel-by-channel specs (formats, targeting, benchmarks), and cross-channel orchestration playbook
- `utm-tracking.md` — UTM naming conventions, URL builder specification, governance rules, and common UTM mistakes to avoid
- `post-mortem.md` — Post-mortem framework, analysis template, learning extraction methodology, and benchmark updating process
- `abm-strategy.md` — Account selection criteria, personalization tier framework, ABM channel playbook, and sales-marketing alignment protocol

## Output Formats

| Deliverable | Format | Description |
|---|---|---|
| Campaign Brief | Document | Complete brief with objective, audience, messaging, channels, timeline, KPIs |
| Budget Allocation Plan | Spreadsheet | Channel-by-channel budget with weekly/monthly breakdown and contingency |
| Media Plan | Spreadsheet | Detailed placements, formats, targeting, budgets, schedules, and forecasts |
| UTM Tracking Sheet | Spreadsheet | All campaign URLs with standardized UTM parameters |
| Launch Checklist | Checklist document | Pre-launch verification items with status tracking |
| Post-Mortem Report | Document | Performance analysis, learnings, and recommendations |
| ABM Campaign Plan | Document + spreadsheet | Account list, personalization plan, channel sequencing, and timeline |
| Campaign Calendar | Calendar/timeline | Visual timeline of all campaign activities and milestones |

## Edge Cases

### Minimal Budget (<$1K/month)
- **Situation**: Very limited paid media budget, often a startup or small business
- **Approach**: Do NOT spread thin across many channels. Recommend concentrating 100% of paid budget on a single highest-potential channel. Supplement with zero-cost tactics (organic social, community, content, email to existing list). Design the campaign to maximize learning per dollar. Set expectations clearly: at this budget level, the goal is validated learning, not scale. Recommend the campaign as a test to identify the channel worth investing more in.

### Enterprise Multi-Market Campaigns
- **Situation**: Global campaign spanning multiple countries, languages, and regulatory environments
- **Approach**: Build a modular campaign framework with a global core (brand message, visual identity, KPIs) and local adaptation layers (language, cultural nuance, channel mix, regulatory compliance). Create a market prioritization matrix. Stagger launches to allow learning transfer between markets. Account for timezone and cultural calendar differences in scheduling. Flag markets with specific regulatory constraints (GDPR, platform bans, industry regulations).

### Campaign During Crisis
- **Situation**: Launching or running a campaign during a brand crisis, industry crisis, or societal crisis
- **Approach**: Recommend pausing non-essential campaigns immediately. For essential campaigns, audit all creative and messaging for tone-appropriateness. Remove anything that could appear insensitive. Shift to helpful, empathetic messaging. Pause aggressive direct-response tactics. Re-evaluate the campaign objective — brand trust preservation may override lead gen goals. Provide a decision framework for when to resume normal operations.

### Seasonal Campaign Timing
- **Situation**: Campaign tied to a seasonal event (Black Friday, back-to-school, Q4 planning season, etc.)
- **Approach**: Build backward from the event date to set preparation milestones. Account for ad platform review times (24-72 hours for new ads). Factor in audience behavior shifts (CPMs spike 2-4 weeks before major shopping events). Recommend early-bird warm-up campaigns to build retargeting pools. Design post-event follow-up sequences. Include competitive intelligence on expected competitor activity during peak periods.

### Regulated Industry Ad Restrictions
- **Situation**: Industries like healthcare, finance, alcohol, cannabis, legal services, or gambling face advertising restrictions
- **Approach**: Before any channel recommendation, flag known restrictions (e.g., Facebook limits on housing/employment/credit targeting, Google restrictions on healthcare claims, platform bans on cannabis advertising). Recommend channels with more flexible policies where appropriate. Build compliance review into the approval process. Include required disclaimers and disclosures in creative specs. Suggest legal review for all ad copy before launch.

## Related Skills

- **Funnel Architect** — For designing the funnel that campaigns drive traffic into and mapping campaign touchpoints to funnel stages
- **Audience Intelligence** — For the persona and segmentation data that informs campaign targeting
- **Content Engine** — For creating all campaign creative assets (ad copy, emails, landing pages, social content)
- **Analytics & Insights** — For campaign performance measurement, attribution, and post-mortem analysis
- **Digital PR & Authority** — For earned media campaigns and PR-driven campaign amplification
