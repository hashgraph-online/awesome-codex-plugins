---
name: influencer-creator
description: "Plan influencer and creator partnerships. Use when: discovering creators, UGC campaigns, or FTC compliance."
---

# Influencer & Creator Marketing

## When to Use This Skill

Activate this skill when the user's request involves any of the following:

- Finding or vetting influencers and creators for brand partnerships
- Building creator briefs or campaign briefs for influencer collaborations
- Understanding FTC disclosure requirements for sponsored content
- Structuring influencer contracts including usage rights, exclusivity, and payment terms
- Measuring influencer campaign performance (EMV, ROAS, brand lift, engagement)
- Planning UGC (user-generated content) campaigns or strategies
- Licensing or repurposing influencer/UGC content in paid ads
- Managing influencer relationships at scale (ambassador programs, always-on partnerships)
- Navigating international influencer compliance (UK ASA, French ARPP, etc.)
- Handling influencer controversies or compliance violations mid-campaign
- Evaluating influencer authenticity (fake followers, engagement pods, audience quality)
- Planning B2B influencer or thought leader partnerships
- Designing employee advocacy programs that intersect with influencer strategy
- Building affiliate-influencer hybrid compensation models

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

- **Campaign objective**: Awareness, consideration, conversions, content creation, or community building
- **Product/service**: What is being promoted, including price point and purchase complexity
- **Target audience**: Demographics, interests, platforms they use, and purchase behavior
- **Budget**: Total influencer budget and how it should split between fees and product seeding
- **Platforms**: Which social platforms are priorities (Instagram, TikTok, YouTube, LinkedIn, X, Pinterest, Twitch)
- **Content type needed**: Posts, Stories, Reels, TikToks, YouTube videos, livestreams, blog posts, podcasts
- **Usage rights**: Whether content will be repurposed for paid ads, website, or other channels
- **Timeline**: Campaign dates, content delivery deadlines, and review periods
- **Industry**: Needed to flag specific compliance requirements (FTC, FDA, FINRA, FCC)
- **Geography**: Markets being targeted to determine applicable disclosure laws
- **Past influencer work**: What has been tried before and what worked or didn't

## Capabilities

### Influencer Discovery
- **Platform-specific search**: Identification criteria for Instagram, TikTok, YouTube, LinkedIn, X, Pinterest, and Twitch creators
- **Audience authenticity analysis**: Detecting fake followers, engagement pods, and purchased engagement. Red flags include sudden follower spikes, low comment quality, engagement rate anomalies, and follower-to-following ratio issues
- **Engagement quality assessment**: Moving beyond vanity metrics to evaluate comment sentiment, save rates, share rates, and genuine audience interaction
- **Niche matching**: Aligning creator content themes, audience demographics, and brand values with campaign objectives
- **Tier classification**: Nano (1K-10K), micro (10K-100K), mid-tier (100K-500K), macro (500K-1M), and mega (1M+) with strategic use cases for each tier
- **Competitive analysis**: Identifying creators who work with competitors and evaluating partnership opportunities or exclusion needs

### Creator Brief Templates
- **Campaign brief structure**: Background, objectives, key messages, creative direction, mandatory elements, do's and don'ts, timeline, and deliverables
- **Creative freedom framework**: Balancing brand requirements with authentic creator expression. Over-scripted content underperforms.
- **Platform-specific formats**: Adapting brief requirements for Reels vs TikTok vs YouTube vs Stories vs static posts
- **Messaging hierarchy**: Must-say messages, should-say messages, and may-say messages to give creators structured flexibility
- **Reference content**: Including examples of content style the brand likes (mood boards, reference posts) without asking creators to copy

### FTC Compliance Engine
- **Disclosure requirements**: Clear and conspicuous disclosure rules. "#ad" or "Sponsored" must be unambiguous and unavoidable
- **Platform-specific disclosure placement**: Instagram (above the fold in captions, not buried in hashtags), TikTok (text overlay and caption), YouTube (verbal and written disclosure in first 30 seconds plus platform's paid promotion checkbox), podcasts (verbal disclosure before and during sponsored segments)
- **Material connection definition**: Any relationship that might affect credibility must be disclosed -- free products, payment, affiliate links, family relationships, employment
- **AI and virtual influencer rules**: Virtual influencers and AI-generated content must disclose their non-human nature. FTC has signaled enforcement focus here
- **Consumer Review Rule**: Reviews must reflect genuine experience. Incentivized reviews require disclosure. Fake reviews and suppression of negative reviews are prohibited
- **Contract compliance clauses**: Specific contractual language requiring FTC compliance, indemnification for non-compliance, and right to request content edits for disclosure issues
- **International compliance**: UK ASA (clear labeling as "Ad"), French ARPP (mandatory disclosure with specific language), EU regulations, Canadian Ad Standards, Australian AANA requirements
- **Endorsement guides updates**: FTC 2023 updated Endorsement Guides expanded disclosure requirements, increased brand liability, and addressed social media specifics

### Performance Tracking
- **Earned Media Value (EMV)**: Calculating the equivalent advertising value of organic influencer reach and engagement
- **Direct ROAS**: Tracking revenue from influencer-specific discount codes, UTM links, and affiliate links
- **Brand lift measurement**: Pre/post campaign surveys, branded search volume changes, social mention increases, and sentiment shifts
- **Engagement metrics**: Rate, quality, saves, shares, comments, and audience growth during campaign periods
- **Content performance**: Comparing influencer content performance against brand-created content benchmarks
- **Attribution modeling**: Multi-touch attribution for influencer as an awareness/consideration channel that assists conversions elsewhere

### Contract Frameworks
- **Usage rights**: Organic only, paid amplification rights, perpetual vs time-limited, platform restrictions, territory restrictions
- **Exclusivity terms**: Category exclusivity (competitor brands), platform exclusivity, duration, and compensation premium for exclusivity (typically 25-100% fee increase)
- **Morality clause**: Behavior standards, grounds for termination, notification requirements, and content removal rights
- **Payment terms**: Flat fee, performance bonus, affiliate/commission hybrid, product-only, retainer. Payment schedules (50% upfront / 50% on delivery is standard)
- **Content approval process**: Number of revision rounds (2 is standard), approval timeline (48-72 hours), and what constitutes approval vs revision
- **Deliverables specification**: Exact number, format, platform, posting schedule, and caption/disclosure requirements
- **Cancellation terms**: Notice period, kill fee (typically 25-50% for cancelled campaigns), and force majeure provisions
- **IP ownership**: Who owns the content (usually the creator), license terms granted to the brand, and derivative work rights

### UGC Strategy
- **UGC solicitation**: Branded hashtag campaigns, contests, review campaigns, unboxing encouragement, and community challenges
- **Rights management**: Obtaining permission to use customer content, terms of service for submissions, and proper attribution
- **UGC in paid ads**: Licensing customer content for ad creative, UGC-style ads produced by creators, and whitelisting/Spark Ads for running ads from creator handles
- **UGC curation**: Selecting, moderating, and showcasing user content on brand channels, website, and marketing materials
- **Quality control**: Maintaining brand safety when amplifying user content, moderation policies, and content guidelines

## Process

### Influencer Campaign Build (Most Common Use Case)

1. **Define campaign parameters** -- Establish objectives, budget, timeline, target audience, and platform priorities. Determine whether the campaign is awareness-focused, conversion-focused, or content-creation-focused.
2. **Influencer identification** -- Build a candidate list using niche relevance, audience demographics, engagement quality, content style, and brand alignment. Reference `influencer-discovery.md` for platform-specific search strategies.
3. **Audience vetting** -- Analyze each candidate's audience for authenticity and demographic match. Check for fake followers, engagement pods, and audience-brand alignment. Eliminate creators whose audience does not match the target.
4. **Outreach and negotiation** -- Craft personalized outreach. Present the partnership opportunity with clear expectations and compensation. Negotiate deliverables, timeline, usage rights, and payment terms.
5. **Contracting** -- Execute contracts covering deliverables, timeline, compensation, usage rights, exclusivity, FTC compliance requirements, morality clause, approval process, and cancellation terms. Reference `contract-frameworks.md`.
6. **Brief delivery** -- Send detailed creative briefs that communicate brand requirements while preserving creative freedom. Include mandatory elements, key messages, do's and don'ts, and reference content. Reference `creator-briefs.md`.
7. **Content review** -- Review submitted content for brand alignment, FTC compliance (disclosure placement and clarity), factual accuracy, and quality standards. Provide feedback within the agreed timeline. Limit revision requests to contracted rounds.
8. **Publish and amplify** -- Coordinate posting schedule across creators. Boost top-performing content with paid amplification where usage rights allow. Run Spark Ads or whitelisted ads from creator handles.
9. **Performance measurement** -- Track EMV, engagement, reach, conversions (via codes/UTMs), and brand lift. Compare against benchmarks and campaign KPIs. Reference `performance-tracking.md`.
10. **Post-campaign analysis** -- Document what worked, what didn't, which creators overperformed, and lessons learned. Use findings to inform future campaign planning and creator relationship development.

### FTC Compliance Audit

1. **Review all sponsored content** -- Check every piece of influencer content for clear and conspicuous disclosure.
2. **Verify disclosure placement** -- Confirm disclosures are visible without clicking "more," are not buried in hashtag strings, are in the first line of captions, and appear as text overlays in video content.
3. **Check disclosure language** -- Ensure disclosure is unambiguous. "#ad" and "Sponsored by [Brand]" are clear. "#ambassador," "#collab," and "#partner" are not sufficient on their own.
4. **Audit video content** -- Verify verbal disclosure within the first 30 seconds and written disclosure in the video itself (not just the description).
5. **Document compliance status** -- Create a compliance log for each piece of content with status, issues found, and corrective actions taken.
6. **Remediate violations** -- Contact creators to update non-compliant content. Document the request and resolution for legal protection.

## Reference Files

- `influencer-discovery.md` -- Platform-specific search strategies, vetting checklists, audience analysis frameworks, and tier-level strategy guides
- `creator-briefs.md` -- Brief templates for each content format, creative freedom guidelines, and messaging hierarchy frameworks
- `ftc-compliance.md` -- Complete FTC Endorsement Guide requirements, platform-specific disclosure rules, international compliance matrix, and contract language templates
- `performance-tracking.md` -- EMV calculation methods, attribution models, reporting templates, and benchmark data by industry and platform
- `contract-frameworks.md` -- Full contract templates, clause-by-clause explanations, negotiation guides, and rate benchmarking by tier and platform
- `ugc-strategy.md` -- UGC solicitation playbooks, rights management frameworks, UGC-to-ad pipelines, and curation best practices

## Output Formats

- **Influencer campaign plan**: Campaign overview, creator shortlist with rationale, brief outline, timeline, budget breakdown, and KPI targets
- **Creator brief**: Complete brief document ready to send to influencers with all brand requirements, creative direction, and compliance instructions
- **FTC compliance audit**: Content-by-content compliance status, violations found, remediation actions, and updated compliance guidelines
- **Influencer contract template**: Customized contract with all relevant clauses based on campaign specifics
- **Campaign performance report**: Creator-level and aggregate performance metrics, ROI analysis, content performance rankings, and strategic recommendations
- **UGC program design**: Solicitation strategy, rights management process, curation guidelines, and repurposing workflow

## Edge Cases

### Influencer Posts Without Disclosure
If a live influencer post is missing required FTC disclosure, respond within hours. Contact the creator immediately to add disclosure. Document the outreach and resolution. If the creator is unresponsive within 24 hours, escalate to their management. Maintain a compliance log that demonstrates good-faith efforts. The brand bears liability for influencer non-compliance under FTC guidelines.

### Influencer Controversy Mid-Campaign
When a partnered influencer becomes involved in controversy, assess severity immediately. For minor issues (off-brand opinion), monitor but continue. For moderate issues (offensive content unrelated to the brand), pause scheduled content and evaluate. For severe issues (illegal activity, hate speech, scandal), pause immediately, activate the morality clause, issue a brand statement distancing from the individual, and remove or de-amplify existing content. Decision speed matters -- a delayed response is perceived as endorsement.

### Cross-Border Campaigns with Different Disclosure Rules
When running campaigns across multiple countries, apply the strictest applicable standard as the baseline. UK ASA requires "Ad" labels. France requires specific French-language disclosure. The EU has evolving platform-specific rules. Build a compliance matrix by market and embed market-specific instructions in creator briefs. When in doubt, over-disclose.

### B2B Influencer Marketing
B2B influencer partnerships involve thought leaders, industry analysts, and professional creators rather than lifestyle influencers. KPIs shift from engagement and reach to lead quality, content authority, and pipeline influence. Payment models often involve speaking fees, co-created content, advisory roles, or event sponsorships rather than per-post fees. LinkedIn and YouTube are primary platforms. Long-form content (whitepapers, webinars, podcast interviews) outperforms short-form.

### Employee Advocacy vs Influencer Marketing
Employee sharing of company content is governed by different rules than influencer marketing, but disclosure is still required. Employees must disclose their employment relationship when endorsing their employer's products. Design employee advocacy programs with built-in disclosure, approved messaging, and clear guidelines separating personal opinions from company endorsements.

### Affiliate-Influencer Hybrid Arrangements
When influencers receive both a flat fee and affiliate commission, both the sponsorship and the affiliate relationship must be disclosed. "#ad" covers the sponsorship; affiliate links require separate disclosure (e.g., "I earn a commission if you purchase through my link"). Structure contracts to clearly delineate the fee component from the performance component for accounting and compliance purposes.

## Related Skills

- **Paid Advertising** -- Amplifying influencer content through paid channels (whitelisting, Spark Ads, boosted content)
- **Content Engine** -- Content strategy that incorporates influencer and UGC content into the broader content calendar
- **Reputation Management** -- Managing brand reputation when influencer controversies arise
- **Growth Engineering** -- Affiliate-influencer hybrid programs and referral amplification through creators
- **Analytics & Insights** -- Attribution and measurement for influencer campaign performance
- **Emerging Channels** -- Social commerce integration with influencer content (TikTok Shop, Instagram Shopping)
