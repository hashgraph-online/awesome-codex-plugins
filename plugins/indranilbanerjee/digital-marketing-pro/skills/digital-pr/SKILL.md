---
name: digital-pr
description: "Plan digital PR campaigns. Use when: pitching journalists, HARO responses, thought leadership, or E-E-A-T building."
---

# Digital PR & Authority

## When to Use This Skill

Activate this module when the user's request involves any of the following:

- **Earned Media Strategy**: Planning how to get press coverage, media mentions, or editorial features
- **Press Releases**: Writing or optimizing press releases for distribution and pickup
- **Journalist Outreach**: Crafting pitch emails, building media lists, or developing journalist relationships
- **HARO/Connectively Pitching**: Responding to journalist queries on Help A Reporter Out (now Connectively) or similar platforms
- **Thought Leadership**: Positioning an executive or brand as an industry authority through content and speaking
- **Newsjacking**: Rapid-response commentary on breaking news to earn media coverage
- **Executive Personal Branding**: Building an executive's public profile and industry presence
- **E-E-A-T Authority Building**: Strengthening Experience, Expertise, Authoritativeness, and Trustworthiness signals for SEO and credibility
- **Press Kit Creation**: Assembling brand media kits with approved assets, boilerplate, and key facts

**Trigger phrases**: "press release," "media coverage," "journalist outreach," "HARO," "Connectively," "thought leadership," "newsjacking," "executive branding," "personal brand," "E-E-A-T," "authority building," "earned media," "PR strategy," "media pitch," "press kit," "media relations," "byline," "guest post," "speaking opportunity," "expert source"

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

Before executing Digital PR work, gather:

1. **Brand/Executive Profile**: Who or what are we building authority for? Company, product, executive, or expert?
2. **Industry/Niche**: What sector do they operate in? What topics are they credible on?
3. **Current Authority Level**: Do they have existing press coverage, bylines, speaking engagements, awards, or credentials?
4. **Target Publications**: Which media outlets, industry publications, or podcasts would be most valuable?
5. **Newsworthy Assets**: What data, research, products, milestones, or perspectives does the brand have that media would find interesting?
6. **Spokesperson**: Who is available and authorized to speak to media? What is their comfort level?
7. **Goals**: Brand awareness, SEO backlinks, thought leadership positioning, product launch coverage, or crisis management?
8. **Timeline**: Is there a news hook, product launch, or event driving urgency?
9. **Budget**: For press release distribution, media database tools, or PR agency support
10. **Sensitive Topics**: Any areas that are off-limits for media discussion?

For quick requests (e.g., "write a press release for our product launch"), proceed with available information. For strategic PR planning, gather the full context.

## Capabilities

- **Media Outreach Strategy**: Target publication mapping, journalist identification, relationship-building approach, pitch calendar, and outreach cadence planning
- **Press Release Optimization**: Newsworthy angle identification, inverted pyramid structure, quote crafting, multimedia integration, distribution channel selection, and SEO optimization for press releases
- **Pitch Template Creation**: Customizable pitch email templates for different scenarios (product launch, data/research, expert commentary, trend story, company milestone, partnership announcement)
- **HARO/Connectively Response Optimization**: Query monitoring strategy, response templates, credibility formatting, rapid-response workflow, and success rate optimization
- **Thought Leadership Content Strategy**: Byline article planning, speaking opportunity identification, podcast guesting strategy, original research planning, and industry report creation
- **Newsjacking Rapid-Response Framework**: News monitoring setup, relevance assessment criteria, speed-to-response protocols, pre-approved messaging templates, and brand safety guardrails
- **E-E-A-T Optimization**: Author bio optimization, credentials display, expert review processes, trust signal implementation, experience demonstration, and authority signal building
- **Executive Personal Branding**: LinkedIn optimization, speaking profile development, media training prep, signature content themes, and public positioning strategy
- **Press Kit Creation**: Brand boilerplate, executive bios, high-resolution assets, fact sheets, media contact information, and previous coverage highlights

## Process

**Primary Workflow: Digital PR Campaign**

1. **Authority Assessment & Goal Setting**
   - Audit current authority signals: existing press coverage, backlink profile, social proof, credentials, industry recognition
   - Identify the authority gap between current state and where the brand/executive needs to be
   - Set specific goals: number of placements, target publications, backlink targets, or awareness metrics
   - Determine the primary angle: Is this product-driven, data-driven, personality-driven, or trend-driven PR?

2. **Media Landscape Mapping**
   - Identify tier 1, tier 2, and tier 3 target publications for this brand/industry
     - **Tier 1**: Major national/international outlets (NYT, Forbes, BBC, TechCrunch, etc.)
     - **Tier 2**: Respected industry publications and large digital outlets
     - **Tier 3**: Niche blogs, local media, podcasts, and newsletters
   - Research journalists who cover this beat at target publications
   - Map journalist interests, recent articles, and preferred pitch formats
   - Identify relevant podcasts, conferences, and speaking platforms
   - Note editorial calendars and upcoming themed issues at target publications

3. **Angle Development & Story Crafting**
   - Identify what makes this brand/person genuinely newsworthy (not just promotional)
   - Develop story angles that serve journalist needs:
     - **Data angle**: Original research, survey results, or industry data the brand can share
     - **Trend angle**: How the brand connects to a larger industry or cultural trend
     - **Counterintuitive angle**: A perspective that challenges conventional wisdom
     - **Human interest angle**: Founder story, customer transformation, or mission-driven narrative
     - **Timely angle**: Connection to current events, seasons, or upcoming dates
   - Create a story bank of 5-10 pitchable angles ranked by newsworthiness
   - Prepare supporting materials for each angle (data, quotes, visuals)

4. **Pitch Development**
   - Write customized pitch emails for each target journalist (NOT mass emails)
   - Pitch structure:
     - **Subject line**: Specific, newsy, concise (under 60 characters)
     - **Opening line**: Why this matters to their audience (not why it matters to you)
     - **The hook**: The newsworthy element in 2-3 sentences
     - **The offer**: What you can provide (data, interview, exclusive, visuals)
     - **Credibility**: Brief proof of why this source is credible
     - **CTA**: Clear, easy next step
   - Keep pitches under 200 words — journalists scan, they don't read
   - Prepare a follow-up sequence (one follow-up after 3-5 business days, maximum two total)

5. **HARO/Connectively Response Protocol**
   - Set up query monitoring for relevant categories and keywords
   - Response framework:
     - Answer the journalist's exact question first (in 2-3 sentences)
     - Add one unique insight or data point they won't get from other respondents
     - Include credentials and relevant experience in 1-2 sentences
     - Offer availability for follow-up questions
     - Keep total response under 300 words
   - Respond within 2-3 hours of query posting (speed is critical)
   - Track response rate and placement rate to optimize over time

6. **Thought Leadership Execution**
   - Define 3-5 signature topics the executive/brand owns
   - Create a content calendar mixing:
     - Byline articles for industry publications (1-2 per month)
     - LinkedIn long-form posts (2-4 per month)
     - Podcast guesting (1-2 per month)
     - Speaking engagements (quarterly minimum)
     - Original research or data projects (1-2 per year)
   - Build a "quotable insights" bank — pre-prepared expert commentary on likely trending topics
   - Develop a rapid-response protocol for newsjacking opportunities

7. **E-E-A-T Signal Building**
   - **Experience**: Document real-world experience through case studies, behind-the-scenes content, and practitioner insights
   - **Expertise**: Display credentials, certifications, and specialized knowledge prominently; create expert-level content
   - **Authoritativeness**: Earn mentions and links from authoritative sources, contribute to industry conversations, build a citation profile
   - **Trustworthiness**: Ensure accurate information, transparent sourcing, clear authorship, secure website, and consistent NAP (Name, Address, Phone) data
   - Implement author schema markup and detailed author bio pages
   - Build topical authority through depth and breadth of expert content

## Reference Files

- `media-outreach.md` — Journalist research methodology, media list building, pitch templates by scenario, outreach cadence rules, and relationship management
- `press-releases.md` — Press release structure, writing guidelines, distribution channel comparison, SEO optimization for releases, and multimedia best practices
- `thought-leadership.md` — Thought leadership content strategy, byline placement guide, speaking opportunity sourcing, podcast guesting playbook, and original research planning
- `newsjacking.md` — News monitoring setup, relevance scoring framework, rapid-response templates, brand safety assessment, and timing guidelines
- `eeat-authority.md` — E-E-A-T audit checklist, authority signal implementation guide, author optimization, trust signal taxonomy, and measurement framework

## Output Formats

| Deliverable | Format | Description |
|---|---|---|
| PR Strategy Document | Document | Comprehensive plan with goals, target media, angles, timeline, and KPIs |
| Media List | Spreadsheet | Tiered list of publications and journalists with contact info and beat details |
| Press Release | Document | Publication-ready release with headline, subhead, body, quotes, boilerplate, and contact |
| Pitch Email Templates | Document | Customized pitch templates for each angle and journalist tier |
| HARO Response Templates | Document | Pre-structured response frameworks for common query types |
| Thought Leadership Calendar | Spreadsheet/Calendar | 90-day plan with content types, topics, platforms, and deadlines |
| E-E-A-T Audit Report | Document | Current authority assessment with specific improvement actions |
| Press Kit | Document + asset folder | Brand boilerplate, bios, fact sheet, approved images, and media contact info |
| Executive Brand Strategy | Document | Personal branding plan with positioning, content themes, and platform strategy |

## Edge Cases

### Newsjacking Controversial Topics (Brand Safety Risk)
- **Situation**: A trending news story is relevant to the brand's expertise, but the topic is politically charged, divisive, or sensitive
- **Approach**: Apply a strict brand safety assessment before any newsjacking response. Score the opportunity on three dimensions: Relevance (is the brand genuinely expert here?), Risk (could the response backfire?), and Reward (is the potential coverage worth the risk?). If the topic is politically divisive, recommend staying silent unless the brand has a clear, mission-aligned reason to speak. For sensitive topics (tragedy, crisis, discrimination), only respond if the brand can add genuine value, not promotional commentary. When in doubt, do not newsjack. Prepare a "kill switch" protocol for pulling published responses if sentiment shifts.

### Regulated Industries (Legal Review Required)
- **Situation**: Healthcare, financial services, legal, or other regulated industries need legal review before any public statement
- **Approach**: Build legal review into the workflow timeline — add 3-5 business days minimum for legal approval. Pre-approve a library of statements and claims that can be used without per-instance legal review to enable faster response. For HARO responses (where speed matters), create pre-cleared credential statements and limit expert commentary to well-established facts rather than claims that could be construed as advice. Always include appropriate disclaimers. Flag that press releases in regulated industries require compliance review before distribution.

### Small Brand with No Media Relationships
- **Situation**: Brand or executive has no existing press coverage, no media contacts, and no public profile
- **Approach**: Start with foundation-building, not pitching tier 1 outlets. Phase the approach: (1) Build a credible online presence first (LinkedIn, website bio, author pages). (2) Start with HARO/Connectively responses to build a portfolio of quotes and mentions. (3) Target tier 3 outlets (niche blogs, local media, industry newsletters) for initial coverage. (4) Create original data or research that gives media a reason to cite the brand. (5) After building a portfolio of 5-10 placements, begin pitching tier 2 publications. Set realistic expectations: building media authority from zero takes 6-12 months of consistent effort.

### Crisis-Related PR
- **Situation**: The brand is facing negative press, a product recall, customer complaint viral moment, or other reputation threat
- **Approach**: This module handles proactive PR, not crisis communications. For active crisis situations, recommend the user consult a crisis communications specialist or agency. However, provide immediate guidance: (1) Acknowledge the situation promptly and transparently. (2) Do not hide, deflect, or attack. (3) Communicate what happened, what you are doing about it, and what changes will prevent recurrence. (4) Centralize communications through a single spokesperson. (5) Monitor media and social sentiment in real time. After the crisis stabilizes, use the standard PR workflow to rebuild trust through positive coverage, thought leadership, and earned media.

## Related Skills

- **Content Engine** — For creating thought leadership content, byline articles, blog posts, and social content that builds authority
- **AEO/GEO Intelligence** — For ensuring AI platforms accurately represent the brand, which is heavily influenced by media citations and authority signals
- **Analytics & Insights** — For measuring PR impact through backlink tracking, brand mention monitoring, referral traffic, and share of voice analysis
- **Campaign Orchestrator** — For integrating earned media into broader campaign plans and amplifying PR wins through paid and owned channels
- **Audience Intelligence** — For understanding which journalists and publications the target audience reads and trusts
