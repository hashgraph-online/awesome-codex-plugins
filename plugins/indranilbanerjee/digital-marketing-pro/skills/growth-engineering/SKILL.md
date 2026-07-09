---
name: growth-engineering
description: "Engineer growth loops. Use when: building referral programs, viral loops, or product-led growth strategy."
---

# Growth Engineering

## When to Use This Skill

Activate this skill when the user's request involves any of the following:

- Designing or improving a product-led growth (PLG) motion
- Building or optimizing referral programs (customer referral, partner referral, ambassador programs)
- Creating viral loops or increasing organic sharing mechanics
- Planning a product or company launch (Product Hunt, beta launches, waitlists)
- Improving user retention, reducing churn, or designing re-engagement campaigns
- Running growth experiments and building an experimentation culture
- Setting up or optimizing affiliate marketing programs
- Designing activation flows and reducing time-to-value for new users
- Building growth models or forecasting viral growth coefficients
- Solving cold-start problems for marketplaces or platforms
- Identifying and scoring product-qualified leads (PQLs)
- Any question about growth levers, growth loops, or sustainable acquisition strategies

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

Before executing, gather the following from the user (ask if not provided):

- **Product type**: SaaS, marketplace, ecommerce, mobile app, content platform, service business
- **Business model**: Subscription, transactional, freemium, free-trial, advertising-supported
- **Current stage**: Pre-launch, early traction (under 1,000 users), growth stage, scale stage
- **Key metrics**: Current MRR/ARR, user count, activation rate, retention rate, churn rate, NPS
- **Existing growth channels**: Which acquisition channels are active and their relative performance
- **Viral potential**: Whether the product has inherent sharing mechanics or requires artificial virality
- **Team and resources**: Engineering capacity for growth features, marketing budget, partnership resources
- **Target user**: Who the ideal user is and what their primary motivation for using the product is
- **Competitive landscape**: Key competitors and their growth strategies

## Capabilities

### Product-Led Growth (PLG) Strategy
- **Free-to-paid conversion**: Freemium model design, free trial optimization, feature gating strategy, usage-based pricing triggers
- **Activation metrics**: Define the "aha moment," map the steps to reach it, measure and optimize activation rate
- **Time-to-value optimization**: Reduce friction between signup and first value experience through onboarding design, templates, sample data, and guided tours
- **PQL scoring**: Define product-qualified lead criteria based on usage patterns, feature adoption, team size, and engagement frequency
- **Self-serve expansion**: In-product upgrade prompts, usage limit notifications, team invite flows, seat expansion triggers
- **Reverse trial**: Give full access first, then downgrade to free -- when this works better than traditional freemium

### Referral Systems
- **Give-and-get programs**: Both referrer and referee receive incentives (e.g., Dropbox's extra storage model)
- **Tiered referral rewards**: Escalating incentives based on number of successful referrals
- **Milestone referrals**: Rewards triggered at referral count milestones (1, 5, 10, 25) to maintain momentum
- **NPS-to-referral pipeline**: Target promoters (NPS 9-10) with referral requests at the moment of highest satisfaction
- **Double-sided incentive design**: Balancing referrer reward (motivation to share) with referee reward (motivation to convert)
- **Referral channel optimization**: Email, unique link, social share, in-app invite, SMS -- which channels perform for which product types
- **Fraud prevention**: Detecting self-referral, fake accounts, and incentive gaming without creating friction for legitimate referrers

### Viral Loop Design
- **Inherent virality**: The product naturally requires others to use it (Slack, Zoom, Google Docs)
- **Artificial virality**: Manufactured sharing through incentives, social features, or content creation (shareable reports, badges, results)
- **Content virality**: User-generated content that surfaces on external platforms and drives new users back
- **Social proof virality**: Visible usage signals (badges, signatures, "powered by" links, public profiles)
- **Viral coefficient calculation**: K-factor = invites per user x conversion rate of invites. K > 1 means exponential growth; K between 0.5-1.0 augments paid acquisition significantly
- **Viral cycle time**: Reducing the time between a user joining and their invitees joining. Shorter cycles compound faster even with lower K-factors

### Launch Playbooks
- **Tier 1 launch** (major product): Full press campaign, influencer seeding, Product Hunt, beta community, launch event, paid amplification
- **Tier 2 launch** (feature/update): Existing user announcement, targeted outreach, community posts, changelog, email campaign
- **Tier 3 launch** (minor update): In-app notification, changelog update, social media post
- **Pre-launch waitlist**: Viral waitlist mechanics (share to move up), early access incentives, drip content to maintain interest
- **Product Hunt launch**: Preparation timeline (2-4 weeks), hunter selection, launch day playbook, post-launch engagement
- **Beta program design**: Closed beta recruitment, feedback loops, beta-to-launch transition, early adopter community building

### Retention Loops
- **Engagement design**: Habit loops (trigger, action, variable reward, investment), notification strategy, content cadence
- **Re-engagement campaigns**: Email sequences, push notifications, in-app messages, retargeting ads triggered by inactivity signals
- **Churn prediction**: Behavioral signals that indicate churn risk (login frequency drop, feature usage decline, support ticket patterns)
- **Winback sequences**: Timed outreach to churned users with personalized value reminders, product updates, and incentive offers
- **Cohort analysis**: Track retention by signup cohort, acquisition channel, activation status, and feature adoption to identify what drives long-term retention
- **Expansion revenue**: Upsell and cross-sell triggers based on usage patterns, team growth, and feature engagement

### Affiliate Marketing
- **Program design**: Commission structure (percentage, flat fee, tiered, recurring), cookie duration, attribution rules
- **Network selection**: When to use affiliate networks (ShareASale, CJ, Impact) vs building a custom program
- **Affiliate recruitment**: Finding high-quality affiliates through competitor analysis, content partnerships, and niche community outreach
- **Commission optimization**: Balancing commission rates to attract affiliates while maintaining profitability; performance tiers to reward top performers
- **Fraud detection**: Click fraud, cookie stuffing, brand bidding violations, trademark misuse, coupon abuse
- **Content affiliate strategy**: Working with bloggers, review sites, comparison sites, and niche publishers
- **Affiliate-influencer hybrids**: Creator partnerships with performance-based compensation models

## Process

### PLG Implementation (Most Common Use Case)

1. **Map the user journey** -- Document every step from first awareness to paid conversion. Identify where users currently drop off and where they experience value.
2. **Define the activation metric** -- Determine the specific action or combination of actions that correlates with long-term retention. This is the "aha moment" the entire PLG motion revolves around.
3. **Design the free offering** -- Structure the free tier or trial to give users enough value to experience the activation moment while creating natural upgrade triggers. Reference common models: feature-limited freemium, usage-limited freemium, time-limited trial, reverse trial.
4. **Optimize time-to-value** -- Redesign onboarding to get users to the activation metric as fast as possible. Remove unnecessary steps, add templates/sample data, implement guided tours, and offer quick-start paths.
5. **Build PQL scoring** -- Define the behavioral signals that indicate a free user is ready for a sales touch or upgrade prompt. Combine usage frequency, feature breadth, team size, and engagement depth into a composite score.
6. **Implement expansion loops** -- Design in-product mechanisms for organic growth: team invites, shared workspaces, public outputs, integrations that touch other teams, and usage-based upgrade paths.
7. **Measure and iterate** -- Track activation rate, free-to-paid conversion rate, time-to-activation, expansion revenue, and viral coefficient. Run experiments on each stage of the funnel.

### Referral Program Build

1. **Assess viral potential** -- Determine whether the product has inherent sharing mechanics or requires incentive-driven referrals. Analyze NPS data to identify promoter concentration.
2. **Design incentive structure** -- Choose the referral model (give-and-get, tiered, milestone) based on product type, customer LTV, and competitive benchmarks. Set incentive values at 10-25% of customer acquisition cost.
3. **Build referral mechanics** -- Create unique referral links, sharing interfaces, tracking infrastructure, and reward fulfillment flows. Make sharing frictionless (one-click, pre-written messages).
4. **Integrate referral touchpoints** -- Embed referral prompts at high-satisfaction moments: post-purchase, after achieving a milestone, after a positive support interaction, at NPS survey completion.
5. **Launch and promote** -- Announce the program to existing users, feature it in onboarding, add it to account dashboards, and include it in email communications.
6. **Monitor and optimize** -- Track share rate, invite conversion rate, referral revenue, and fraud signals. A/B test incentive types, sharing copy, and prompt placement.

## Reference Files

- `product-led-growth.md` -- PLG frameworks, freemium vs trial decision trees, activation metric identification, PQL scoring models
- `referral-systems.md` -- Referral program templates, incentive design principles, fraud prevention tactics, and case studies
- `viral-loops.md` -- Viral coefficient calculations, loop design patterns, virality assessment frameworks
- `launch-strategy.md` -- Tier 1/2/3 launch playbooks, Product Hunt guide, waitlist mechanics, beta program design
- `retention-loops.md` -- Engagement frameworks, churn prediction models, winback sequences, cohort analysis methods
- `affiliate-marketing.md` -- Program setup guides, network comparisons, commission optimization, fraud detection systems

## Output Formats

- **PLG strategy document**: User journey map, activation metric definition, free tier design, PQL criteria, expansion loop mechanics, and success metrics
- **Referral program spec**: Incentive structure, mechanics description, integration points, launch plan, and monitoring dashboard requirements
- **Launch playbook**: Pre-launch timeline, launch day checklist, channel-by-channel activation plan, post-launch follow-up sequence
- **Retention analysis**: Cohort retention curves, churn risk indicators, re-engagement campaign designs, and winback sequence templates
- **Growth model**: Spreadsheet-ready model with viral coefficient, cycle time, channel-level CAC, retention curves, and projected growth trajectories
- **Affiliate program blueprint**: Commission structure, network/platform recommendation, recruitment strategy, compliance guidelines, and fraud monitoring plan

## Edge Cases

### Non-Viral Products
Some products have no inherent sharing mechanic (e.g., personal finance tools, solo productivity apps). For these, create artificial virality through shareable outputs (reports, achievements, results), social proof features (public profiles, leaderboards), content creation tools that naturally surface the brand, or incentive-driven referrals. Not every product needs a viral coefficient above 1 -- even K=0.3 meaningfully reduces CAC.

### Marketplace Cold-Start Problem
Two-sided marketplaces face the chicken-and-egg problem: no supply without demand, no demand without supply. Solve by starting with one side (usually supply) through manual recruitment, seeding content, or offering the supply side a standalone value proposition. Concentrate on a narrow geography or vertical first. Reference strategies: Uber started with black cars, Airbnb started with events, and Yelp started with reviews before transactions.

### B2B vs B2C Retention Dynamics
B2B retention depends on product becoming embedded in workflows, multi-user adoption within an organization, and integration with other tools. B2C retention depends on habit formation, content freshness, and emotional engagement. Do not apply B2C engagement tactics (daily push notifications, gamification) to B2B products. B2B retention is measured monthly or quarterly, not daily.

### Referral Fraud Prevention
Common referral fraud patterns include self-referral with multiple accounts, referral rings between friends who churn after receiving rewards, and bot-generated fake referrals. Mitigate by requiring the referred user to complete a meaningful action (purchase, usage threshold) before rewards are distributed, implementing device fingerprinting, setting reasonable reward caps, and monitoring for anomalous patterns.

### International Launch Sequencing
When launching internationally, do not launch everywhere simultaneously. Sequence by market attractiveness (TAM, competitive density, regulatory complexity), language/localization readiness, and existing demand signals. Start with one new market, prove the playbook, then expand. Payment methods, compliance requirements, and cultural norms vary significantly and can break launch plans built for the home market.

## Related Skills

- **Paid Advertising** -- Paid acquisition that PLG and viral loops can amplify or replace over time
- **CRO** -- Activation and onboarding optimization overlaps heavily with CRO principles
- **Content Engine** -- Content marketing that feeds growth loops and launch amplification
- **Analytics & Insights** -- Cohort analysis, experiment measurement, and growth modeling
- **Influencer & Creator Marketing** -- Creator partnerships for launch amplification and affiliate-influencer hybrids
- **Funnel Architect** -- Growth engineering strategies plug into the broader acquisition and retention funnel
