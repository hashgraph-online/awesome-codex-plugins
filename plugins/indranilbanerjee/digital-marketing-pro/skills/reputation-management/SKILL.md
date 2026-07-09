---
name: reputation-management
description: "Manage brand reputation. Use when: handling reviews, crisis comms, negative press, sentiment, or recovery plans."
---

# Reputation Management

## When to Use This Skill

Activate this skill when the user's request involves any of the following:

- Generating more customer reviews or managing existing reviews across platforms
- Responding to negative reviews (Google, Yelp, G2, Capterra, Trustpilot, Amazon, BBB, industry-specific sites)
- Preparing for or responding to a brand crisis (product recall, executive scandal, data breach, viral complaint, lawsuit)
- Assessing and mitigating brand safety risks in advertising and partnerships
- Monitoring brand sentiment across social media, review platforms, and press
- Building a reputation recovery plan after a negative event
- Handling negative press, unfavorable search results, or misinformation
- Managing employee reviews on platforms like Glassdoor or Indeed
- Designing proactive reputation-building strategies
- Evaluating brand safety settings for ad placements and content adjacency
- Navigating legal constraints on reputation responses (defamation, HIPAA, regulated industries)
- Addressing fake review attacks or review manipulation by competitors

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

Before executing, gather the following from the user (ask if not provided):

- **Current situation**: Is this proactive reputation building, reactive crisis response, or ongoing reputation maintenance?
- **Severity level**: For crisis situations, what is the scope and intensity? (Single negative review, trending negative conversation, press coverage, legal action)
- **Industry**: Needed for compliance constraints (healthcare/HIPAA, finance/FINRA, legal/bar rules, government)
- **Platform landscape**: Which review platforms and social channels are most relevant to the business
- **Current review profile**: Average rating, review volume, review trend, and response rate
- **Brand voice**: Tone and communication style guidelines
- **Stakeholders**: Who needs to be involved in approvals (legal, PR, C-suite, customer service)
- **Existing monitoring**: What tools or processes are in place for sentiment tracking
- **History**: Any past crises or reputation issues and how they were handled
- **Resources**: Team capacity for review management, crisis response, and ongoing monitoring

## Capabilities

### Review Generation
- **FTC-compliant solicitation**: Ask for reviews without incentivizing positive reviews specifically. Incentives for leaving a review (not a positive review) require disclosure. Never gate reviews by satisfaction level (asking happy customers to review publicly while routing unhappy customers to private feedback is prohibited)
- **Platform-specific timing**: Google reviews (post-purchase/service completion), G2/Capterra (after meaningful product usage, typically 30-60 days), Amazon (post-delivery with review request button), Yelp (never directly solicit -- Yelp penalizes solicited reviews)
- **Review request sequences**: Email, SMS, in-app prompts, QR codes on receipts/packaging, post-interaction follow-ups
- **Review volume strategy**: Consistent review velocity matters more than spikes. Build automated review request flows triggered by key customer milestones
- **Review platform prioritization**: Focus efforts on platforms that influence purchase decisions for the specific industry (Google for local, G2 for SaaS, TripAdvisor for hospitality, Healthgrades for medical)

### Negative Review Response Framework
- **Response timing**: Respond within 24 hours for public reviews. Speed demonstrates attentiveness. Delayed responses appear dismissive
- **Response structure**: Acknowledge the concern, apologize for the experience (not admitting fault), explain what happened if appropriate, offer a resolution, and move the conversation offline
- **Tone calibration**: Professional and empathetic regardless of review tone. Never argue, get defensive, or blame the customer publicly. The response is for future readers, not just the reviewer
- **Legal review triggers**: Know when a response requires legal review (threatened litigation, allegations of illegal activity, regulated industry topics, potential defamation claims)
- **Follow-up protocol**: After resolving the issue offline, politely ask if the customer would consider updating their review. Never demand or pressure
- **Review disputes**: Platform-specific processes for flagging fake, defamatory, or policy-violating reviews for removal

### Crisis Communication (3-Tier Framework)

**Tier 1 -- Minor Crisis** (isolated complaint, single negative article, localized social media issue)
- **Severity indicators**: Limited reach, no media pickup, contained to one platform or conversation
- **Response timeline**: Respond within 2-4 hours with prepared acknowledgment
- **Actions**: Direct customer response, monitor for spread, prepare holding statement if needed
- **Stakeholders**: Customer service lead, social media manager

**Tier 2 -- Moderate Crisis** (trending complaint, multiple media outlets, influencer amplification, regional issue)
- **Severity indicators**: Growing reach, media inquiries, multiple customer complaints on the same issue, hashtag trending
- **Response timeline**: Public statement within 4-8 hours. Internal alignment within 2 hours
- **Actions**: Activate crisis team, issue holding statement, prepare full response, monitor real-time, brief executives
- **Stakeholders**: VP/Director of Marketing, PR team, legal counsel, customer service leadership
- **Stakeholder messaging matrix**: Different messages for customers (empathy + action), employees (facts + guidance), media (official statement), investors (impact assessment + response plan), partners (reassurance + timeline)
- **Brand voice shift protocol**: Move from standard marketing voice to crisis voice -- more human, more direct, less polished, zero humor, zero promotion

**Tier 3 -- Severe Crisis** (data breach, product safety issue, executive misconduct, viral outrage, regulatory action)
- **Severity indicators**: National/international media coverage, regulatory involvement, potential legal liability, significant customer impact
- **Response timeline**: Initial acknowledgment within 1-2 hours. Detailed response within 24 hours. Ongoing updates every 24-48 hours
- **Actions**: CEO-level response, legal coordination, regulatory notification (if required), customer notification, operational remediation, third-party investigation (if needed)
- **72-hour timeline**: Hour 0-2 (acknowledge, assemble team), Hour 2-8 (fact-finding, holding statement), Hour 8-24 (detailed response, customer outreach, media statement), Hour 24-48 (operational updates, stakeholder briefings), Hour 48-72 (recovery plan announcement, ongoing communication cadence)
- **Stakeholders**: CEO/C-suite, general counsel, board of directors (if public company), PR agency, regulatory contacts

### Brand Safety (4-Layer Framework)

**Layer 1 -- Ad Placement Safety**
- Ensuring ads do not appear alongside harmful, offensive, or brand-inappropriate content
- Platform-specific brand safety settings (Google content exclusions, Meta inventory filters, YouTube placement exclusions)
- Third-party verification tools (IAS, DoubleVerify, MOAT) for programmatic environments
- Keyword exclusion lists and site exclusion lists

**Layer 2 -- Association Safety**
- Vetting partners, influencers, and sponsors for brand alignment and risk
- Due diligence on co-marketing partners, event sponsors, and media placements
- Ongoing monitoring of brand-associated entities for emerging controversies

**Layer 3 -- Content Safety**
- Ensuring brand-produced content does not inadvertently create brand safety issues
- Content review process for cultural sensitivity, inclusivity, and potential misinterpretation
- Social media post approval workflows and crisis-proofing content calendars

**Layer 4 -- Data Safety**
- Protecting customer data in marketing operations
- Compliance with GDPR, CCPA, and other privacy regulations in marketing contexts
- Vendor data handling assessments for marketing technology partners

### Sentiment Monitoring Framework
- **Monitoring scope**: Social media mentions, review platforms, news/press, forums, employee review sites, search results
- **Sentiment scoring**: Positive, neutral, negative classification with intensity weighting
- **Alert thresholds**: Define spike thresholds that trigger escalation (e.g., 3x normal negative mention volume in 24 hours)
- **Competitive benchmarking**: Compare sentiment trends against key competitors
- **Topic clustering**: Group sentiment by theme (product quality, customer service, pricing, leadership) to identify systemic issues
- **Trend analysis**: Weekly/monthly sentiment trend reports to identify gradual shifts before they become crises

### Reputation Recovery Playbooks

**30-Day Plan (Immediate Stabilization)**
- Audit current reputation state across all platforms
- Respond to all outstanding negative reviews
- Launch review generation campaign to dilute negative content with fresh positive reviews
- Publish thought leadership or positive press content to improve search results
- Implement monitoring infrastructure if not already in place

**60-Day Plan (Rebuilding)**
- Execute content strategy targeting negative search results (SEO for reputation)
- Launch customer success stories and case study campaigns
- Engage in community outreach and corporate responsibility initiatives
- Build media relationships for positive press placements
- Implement systematic review management process

**90-Day Plan (Reinforcement)**
- Measure sentiment shift and review profile improvement
- Establish ongoing reputation monitoring and maintenance cadence
- Create crisis communication playbook to prevent future reputation damage
- Build brand advocacy program with satisfied customers and employees
- Conduct reputation audit to benchmark progress and set ongoing targets

## Process

### Negative Review Response (Most Common Use Case)

1. **Assess the review** -- Read carefully. Determine if the complaint is legitimate, exaggerated, or fabricated. Check if the reviewer is an actual customer. Assess the platform and visibility of the review.
2. **Check for legal triggers** -- Does the review mention legal action, allege illegal behavior, or involve a regulated topic? If yes, route through legal before responding.
3. **Draft the response** -- Follow the framework: acknowledge, empathize, explain (briefly and without excuses), offer resolution, and invite offline conversation. Keep it under 150 words for public responses.
4. **Tone check** -- Ensure the response is empathetic, professional, and non-defensive. Read it from the perspective of a potential customer seeing both the review and the response. The response should make the brand look better, not worse.
5. **Post and track** -- Publish the response, log it in the review management system, and set a follow-up reminder to check if the customer responded or updated their review.
6. **Resolve offline** -- If the customer engages, resolve the issue through direct communication. Document the resolution for internal process improvement.
7. **Pattern analysis** -- Regularly analyze negative reviews for recurring themes. Feed patterns back to product, operations, and customer service teams for systemic fixes.

### Crisis Response Activation

1. **Severity assessment** -- Classify the crisis as Tier 1, 2, or 3 based on reach, media involvement, customer impact, and legal exposure.
2. **Assemble the team** -- Activate the appropriate stakeholders based on tier level. Establish a communication channel for real-time coordination.
3. **Fact-finding** -- Gather all available information. What happened, when, who is affected, what is the scope, and what do we know vs what is speculation.
4. **Holding statement** -- Issue a brief acknowledgment that the brand is aware of the situation and is investigating. This buys time without leaving a silence vacuum.
5. **Detailed response** -- Craft the full response addressing what happened, what the brand is doing about it, and what affected parties should do. Tailor messaging per stakeholder group.
6. **Distribution** -- Publish the response through appropriate channels (website statement, social media, email to affected customers, press release if media is involved).
7. **Monitor and update** -- Track conversation in real time. Update stakeholders and the public at regular intervals. Correct misinformation promptly.
8. **Post-crisis review** -- After the crisis subsides, conduct a retrospective. What caused it, how was the response, what should change in the crisis playbook, and what operational changes prevent recurrence.

## Reference Files

- `review-strategy.md` -- Review generation tactics, platform-specific solicitation rules, response templates, and review management workflows
- `crisis-communication.md` -- 3-tier crisis framework details, stakeholder messaging templates, 72-hour timeline playbook, and post-crisis retrospective guide
- `brand-safety.md` -- 4-layer brand safety framework, platform-specific settings, vendor evaluation criteria, and brand safety audit checklists
- `sentiment-monitoring.md` -- Monitoring tool recommendations, alert configuration guides, reporting templates, and competitive benchmarking methods
- `recovery-playbooks.md` -- 30/60/90-day recovery plans, SEO-for-reputation tactics, advocacy program designs, and reputation audit frameworks

## Output Formats

- **Review response**: Ready-to-publish response text tailored to the specific review, platform, and brand voice
- **Crisis communication plan**: Severity assessment, stakeholder matrix, messaging by audience, timeline, and channel distribution plan
- **Brand safety audit**: Layer-by-layer assessment, risk scores, gap analysis, and prioritized remediation actions
- **Sentiment report**: Current sentiment baseline, trend analysis, competitive comparison, and topic-level breakdown
- **Reputation recovery plan**: 30/60/90-day action plan with specific tactics, responsible parties, success metrics, and timeline
- **Review management playbook**: Standard operating procedures for review generation, monitoring, response, and escalation

## Edge Cases

### Crisis During Campaign Launch
If a crisis hits during a planned campaign launch, pause all scheduled marketing content immediately. Promotional content running alongside crisis response appears tone-deaf and amplifies backlash. Resume campaigns only after the crisis is resolved and public sentiment has stabilized. Factor in a buffer period -- restarting promotions too quickly can reignite criticism.

### Regional Crisis Containment
When a crisis is localized to one market or region, attempt containment before it spreads. Respond in the local language and on local platforms. Adjust global content calendars to avoid tone-deaf cross-posting. Brief regional teams immediately even if their markets are not yet affected, so they can prepare.

### Influencer-Caused vs Company-Caused Crisis
The response playbook differs based on crisis origin. For influencer-caused issues (influencer says something offensive while associated with the brand), distance the brand, invoke the morality clause, and focus messaging on brand values. For company-caused issues (product defect, employee misconduct, data breach), own the problem, take responsibility, and focus messaging on actions being taken.

### Regulated Industry Legal Gates
In healthcare, finance, and legal services, every public statement may have compliance implications. Build mandatory legal review into the crisis response timeline. For HIPAA-covered entities, never acknowledge a specific patient relationship in a review response. For financial services, never make statements that could be construed as investment advice or guarantees. These legal gates add response time, so prepare pre-approved response templates for common scenarios.

### Social Media Pile-On with Misinformation
When a brand faces viral criticism built on inaccurate information, resist the urge to respond emotionally or repeatedly. Issue one clear, factual correction through official channels. Do not engage in back-and-forth arguments with individual commenters. Arm supporters and employees with accurate talking points. Monitor for influencer or media amplification and respond directly to high-reach accounts spreading misinformation.

### Fake Review Attacks
If a business is targeted by coordinated fake negative reviews (competitor sabotage, disgruntled ex-employee, online mob), document the pattern (timing, reviewer profiles, language similarities), report to the platform with evidence, and respond to each review professionally (the response is for genuine readers, not the fake reviewers). Consider legal action for demonstrable defamation. Accelerate genuine review generation to dilute the impact.

### Employee Review Management (Glassdoor)
Employee review platforms influence recruiting and brand perception. Respond to negative Glassdoor reviews with the same professionalism as customer reviews. Never attempt to identify anonymous reviewers. Address systemic themes in employer branding content. Encourage satisfied employees to share their experiences authentically (never mandate or incentivize specific positive reviews).

## Related Skills

- **Influencer & Creator Marketing** -- Managing reputation risks from influencer partnerships and controversies
- **Paid Advertising** -- Brand safety settings in ad platforms and pausing campaigns during crises
- **Content Engine** -- Positive content creation for reputation recovery and thought leadership
- **Analytics & Insights** -- Sentiment data analysis and reputation metric tracking
- **SEO** -- Search result optimization for reputation management (suppressing negative results)
- **Emerging Channels** -- Monitoring and managing reputation on newer platforms and community channels
