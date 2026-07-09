---
name: emerging-channels
description: "Explore emerging marketing channels. Use when: evaluating voice search, social commerce, or new platforms."
---

# Emerging Channels

## When to Use This Skill

Activate this skill when the user's request involves any of the following:

- Optimizing content for voice search (Alexa, Google Assistant, Siri, smart speakers)
- Preparing for or leveraging visual search (Google Lens, Pinterest Lens, Amazon visual search)
- Building conversational commerce flows (WhatsApp Business, Facebook Messenger, chatbot funnels, SMS marketing)
- Setting up or optimizing social commerce (Instagram Shopping, TikTok Shop, Pinterest Shopping, YouTube Shopping)
- Building, growing, or managing online communities (Discord, Slack, Circle, Facebook Groups, Reddit, forums)
- Planning podcast marketing strategy (branded podcasts, podcast advertising, guest appearances, podcast SEO)
- Developing video marketing strategy across formats and platforms (short-form, mid-form, long-form, live)
- Marketing on newer or underutilized platforms and channels
- Evaluating whether an emerging channel is worth investing in for a specific business
- Understanding platform-specific commerce features and shoppable content
- Designing chatbot conversations and automated messaging funnels
- Building voice applications (Alexa Skills, Google Actions) for brand engagement
- Exploring international messaging platforms (WeChat, LINE, KakaoTalk, Telegram) for commerce

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

- **Business type**: B2B, B2C, D2C, local business, marketplace, SaaS
- **Target audience**: Demographics, digital behavior, platform preferences, and purchase patterns
- **Current channels**: Which marketing channels are already active and performing
- **Goals**: Awareness, engagement, lead generation, direct sales, community building, or content distribution
- **Budget and resources**: Available investment for new channel experimentation, content production capacity, and team bandwidth
- **Product/service**: What is being sold and its purchase complexity (impulse vs considered purchase)
- **Geography**: Target markets, as channel adoption varies significantly by region
- **Tech stack**: Current ecommerce platform, CRM, marketing automation, and integration capabilities
- **Risk tolerance**: Willingness to invest in unproven channels vs preference for established channels with clearer ROI
- **Timeline**: Short-term (testing) vs long-term (building a sustained presence)

## Capabilities

### Voice Search Optimization
- **Query pattern analysis**: Voice queries are longer, more conversational, and more question-based than typed queries. Optimize for natural language patterns ("What's the best Italian restaurant near me" vs "Italian restaurant NYC")
- **Content structure for voice**: Featured snippet optimization, FAQ schema markup, concise answer paragraphs (40-60 words for Google's spoken responses), and position zero targeting
- **Speakable schema markup**: Implementing structured data that identifies sections of content suitable for text-to-speech playback by voice assistants
- **Local voice search**: "Near me" query optimization, Google Business Profile completeness, local schema markup, and review volume/recency
- **Voice commerce**: Voice-initiated purchasing flows, reorder by voice, voice-exclusive promotions, and integration with Amazon Alexa shopping
- **Voice app development**: When to build Alexa Skills or Google Actions, use cases (brand utilities, content delivery, customer service), and discovery optimization

### Visual Search
- **Image optimization for search**: Descriptive file names, comprehensive alt text, high-quality images from multiple angles, and consistent image sizing
- **Google Lens optimization**: Product images that are easily identifiable by visual recognition, unique product design elements, and schema markup for products
- **Pinterest Lens strategy**: Lifestyle imagery, shoppable pins, visual similarity to trending Pinterest content, and Pinterest SEO
- **Structured data for visual search**: Product schema, image schema, and video schema that help search engines understand visual content
- **Visual search commerce**: Enabling "search by photo" on ecommerce sites, visual similarity recommendations, and AR try-on features
- **Platform-specific visual search**: Amazon visual search, ASOS Style Match, and retailer-specific visual search capabilities

### Conversational Commerce
- **WhatsApp Business**: Catalog setup, automated greetings, quick replies, broadcast lists, WhatsApp Business API for scale, and click-to-WhatsApp ads
- **Chatbot funnels**: Lead qualification bots, product recommendation bots, customer support bots, appointment booking bots, and cart recovery bots
- **Conversation design**: Writing chatbot scripts that feel natural, handling edge cases gracefully, knowing when to escalate to human agents, and maintaining brand voice in automated interactions
- **SMS marketing**: Opt-in compliance (TCPA), message frequency optimization, promotional vs transactional messages, segmentation, and two-way SMS conversations
- **Messenger marketing**: Facebook Messenger bots, sponsored messages, recurring notifications, and integration with Meta ad campaigns
- **International messaging platforms**: WeChat Official Accounts and Mini Programs (China), LINE Official Accounts (Japan/SE Asia), KakaoTalk Channels (Korea), Telegram Bots (Eastern Europe/Middle East)
- **Conversational AI**: Using LLMs for more natural chat interactions, hybrid AI-human support models, and training conversational AI on brand knowledge bases

### Social Commerce
- **Instagram Shopping**: Shop setup, product tagging in posts/Stories/Reels, live shopping, Shopping from Creators, and checkout optimization
- **TikTok Shop**: Product listing, affiliate marketplace, live shopping events, shoppable videos, and TikTok Shop Ads integration
- **Pinterest Shopping**: Product pins, catalog integration, shopping Ads, and Pinterest's visual discovery to purchase pipeline
- **YouTube Shopping**: Product shelves, shopping tags in videos, live shopping, and Shorts shopping integration
- **Social storefront optimization**: Product descriptions for social context (different from website), social-first imagery, pricing strategy for social buyers
- **Live shopping**: Platform selection, host preparation, production requirements, engagement tactics, and conversion optimization for real-time selling
- **Shoppable content strategy**: Integrating commerce into organic content without making every post a sales pitch; editorial-to-commerce ratio guidance

### Community Building
- **Platform selection**: Discord (real-time, younger demographics, gaming/tech), Slack (professional, B2B), Circle (course/membership), Facebook Groups (broad demographics, easy onboarding), Reddit (niche interests, authenticity-focused), brand-owned forums (full control, SEO benefits)
- **Community health metrics**: Daily/weekly/monthly active members, post frequency, response rate, member-to-member interactions (not just brand-to-member), retention rate, and NPS
- **Growth flywheel**: Content attracts members, members create content, content attracts more members. Design the initial content and engagement loops that start this flywheel
- **Moderation strategy**: Community guidelines, moderation team structure (paid moderators, volunteer mods, AI moderation), escalation procedures, and transparency in enforcement
- **Community-led growth**: Using community as a top-of-funnel acquisition channel, community members as beta testers and product advisors, and community content as marketing content
- **Monetization**: When and how to monetize (premium tiers, events, courses, marketplace), without destroying community culture
- **Community manager role**: Skills needed, time commitment, empowerment level, and integration with marketing and product teams

### Podcast Marketing
- **Branded podcast strategy**: When to create a branded podcast (thought leadership, audience building, customer education), format selection (interview, narrative, solo commentary, panel), and production quality tiers
- **Podcast advertising**: Host-read vs programmatic ads, CPM benchmarks ($18-50 for host-read mid-roll), frequency and reach planning, and attribution methods (vanity URLs, promo codes, pixel-based)
- **Guest appearance strategy**: Identifying target podcasts, crafting pitches, preparing talking points, and maximizing each appearance with social promotion and backlinks
- **Podcast SEO**: Show titles, episode titles, show notes optimization, transcript publishing, and distribution across platforms (Apple, Spotify, YouTube, Google)
- **Podcast-to-content pipeline**: Repurposing podcast episodes into blog posts, social clips, email content, and video snippets to maximize ROI from each recording
- **Measurement and attribution**: Downloads, listens, completion rates, subscriber growth, and tying podcast exposure to website traffic and conversions

### Video Marketing
- **Short-form strategy (under 60 seconds)**: TikTok, Instagram Reels, YouTube Shorts. Hook in first 1-3 seconds, native platform aesthetics, trending audio/formats, high-volume posting cadence (3-7x per week)
- **Mid-form strategy (1-10 minutes)**: Instagram, Facebook, LinkedIn, TikTok. Educational content, product demos, behind-the-scenes, and story-driven content
- **Long-form strategy (10+ minutes)**: YouTube, webinars, course content. Deep-dive tutorials, interviews, documentaries, and thought leadership. YouTube algorithm favors watch time, making longer content advantageous when retention is maintained
- **Production tiers**: Lo-fi (smartphone, natural lighting, minimal editing -- authentic feel), mid-fi (basic lighting, external mic, simple graphics), and hi-fi (professional production, scripted, studio)
- **Video SEO**: YouTube title and description optimization, tags, thumbnails (CTR optimization), chapters, cards, end screens, and embedding strategy for website SEO
- **Live video**: Platform selection (YouTube Live, Instagram Live, TikTok Live, LinkedIn Live, Twitch), preparation checklist, engagement tactics, and repurposing live content
- **Video distribution**: Platform-native uploads vs cross-posting, platform-specific optimization (aspect ratios, captions, lengths), and distribution scheduling

## Process

### New Channel Evaluation (Most Common Use Case)

1. **Audience validation** -- Confirm the target audience is active on the channel in question. Check platform demographics, usage data, and competitor presence. Do not invest in a channel because it is trendy; invest because the audience is there.
2. **Competitive landscape** -- Analyze what competitors and adjacent brands are doing on the channel. Identify gaps and opportunities. Determine if there is a first-mover advantage or if the channel is already saturated.
3. **Resource assessment** -- Determine the minimum viable investment (time, budget, content production) required to test the channel meaningfully. Most emerging channels require consistent effort over 3-6 months before yielding reliable data.
4. **Pilot design** -- Create a 90-day pilot plan with specific content cadence, engagement strategy, and success metrics. Define what "success" looks like at the end of the pilot to make a continue/stop/scale decision.
5. **Content strategy** -- Develop channel-specific content that respects platform norms and user expectations. Repurpose existing content where possible, but always adapt to the platform format rather than cross-posting identical content.
6. **Measurement framework** -- Set up tracking for both leading indicators (followers, engagement, reach) and lagging indicators (website traffic, leads, sales) attributed to the channel.
7. **Execute and learn** -- Run the pilot, document what works and what doesn't, adjust the strategy based on data, and make the continue/stop/scale decision at the end of the pilot period.
8. **Scale or sunset** -- If the pilot succeeds, build a sustained strategy with increased resources. If it fails, document the learnings, sunset the effort, and redirect resources.

### Social Commerce Setup

1. **Platform selection** -- Choose the social commerce platform(s) based on audience presence, product type, and technical requirements. Visual products thrive on Instagram and Pinterest. Trend-driven products thrive on TikTok. Considered purchases benefit from YouTube.
2. **Storefront setup** -- Configure the platform's shopping features: product catalog upload, collection organization, shipping and return policies, and payment integration.
3. **Product content optimization** -- Create product listings optimized for social context. Social product descriptions should be shorter, more conversational, and benefit-focused compared to website listings. Product images should match the platform's visual style.
4. **Shoppable content strategy** -- Plan the content calendar with a mix of shoppable and non-shoppable content. Aim for a ratio where no more than 30-40% of content is directly shoppable to avoid audience fatigue.
5. **Live shopping integration** -- If applicable, plan live shopping events with hosts, products, and promotional cadence. Schedule during peak audience activity hours.
6. **Measurement setup** -- Configure platform analytics, UTM tracking for external attribution, and revenue tracking per platform and content type.

## Reference Files

- `voice-search.md` -- Voice query patterns, content optimization tactics, speakable schema implementation, and voice commerce integration guides
- `visual-search.md` -- Image optimization checklists, visual search platform guides, structured data templates, and visual commerce implementation
- `conversational-commerce.md` -- WhatsApp Business setup, chatbot design frameworks, SMS compliance guides, and conversation flow templates
- `social-commerce.md` -- Platform-by-platform setup guides, product listing optimization, live shopping playbooks, and social storefront best practices
- `community-building.md` -- Platform selection matrices, community launch playbooks, moderation frameworks, health metric dashboards, and growth strategies
- `podcast-marketing.md` -- Branded podcast launch guide, advertising rate benchmarks, guest pitching templates, and podcast SEO checklists
- `video-marketing.md` -- Format-by-platform guides, production tier specifications, video SEO checklists, and distribution strategy frameworks
- `web3-decentralized.md` -- Blockchain-based marketing, tokenized loyalty programs, NFT utility campaigns, decentralized social platforms, DAO marketing, and Web3 measurement frameworks

## Output Formats

- **Channel evaluation report**: Audience fit assessment, competitive analysis, resource requirements, 90-day pilot plan, success metrics, and go/no-go recommendation
- **Social commerce plan**: Platform selection rationale, storefront setup checklist, content strategy, live shopping calendar, and revenue projections
- **Conversational commerce flow**: Chatbot conversation map, message templates, escalation rules, and integration specifications
- **Community launch plan**: Platform selection, launch timeline, initial content plan, moderation guidelines, growth milestones, and health metrics dashboard
- **Podcast strategy**: Format recommendation, content calendar, production specifications, distribution plan, and measurement framework
- **Video content plan**: Platform-specific content calendar, production specifications per format, SEO optimization checklist, and distribution schedule
- **Voice/visual search audit**: Current optimization status, gap analysis, implementation roadmap, and expected impact

## Edge Cases

### Platform-Restricted Industries
Cannabis, CBD, firearms, adult products, and certain pharmaceutical products cannot advertise on most platforms and face restrictions on social commerce features. For these industries, focus on owned channels (website, email, SMS with compliance), community building on platforms that permit the category, SEO and content marketing, and compliant influencer partnerships. Always verify current platform policies as they change frequently.

### B2B Community Building
B2B communities operate differently from B2C. Members join for professional development, networking, and problem-solving rather than brand fandom. Slack and LinkedIn Groups tend to outperform Discord for B2B. Content should be practitioner-focused, not promotional. The community must deliver professional value independent of the product. Moderation is typically lighter but quality standards are higher.

### Podcast Measurement Limitations
Podcast attribution remains challenging. Downloads do not equal listens. Listener demographics are estimated, not measured. Cross-device tracking is unreliable. Mitigate by using unique promo codes, vanity URLs, and post-purchase surveys ("How did you hear about us?"). Accept that podcast marketing is often a brand/awareness investment with indirect attribution. Do not hold podcasts to the same direct-response metrics as paid search.

### Voice Search for Non-English Languages
Voice search optimization for non-English languages requires language-specific considerations. Natural language patterns, question structures, and colloquial expressions vary by language and dialect. Schema markup should use hreflang tags and language-specific structured data. Voice assistant capabilities and market penetration vary by language and region (Google Assistant vs Alexa vs Siri market share differs significantly by country).

### Social Commerce in Non-US Markets
In China, WeChat Mini Programs and Douyin (Chinese TikTok) dominate social commerce with capabilities far beyond Western platforms. In Southeast Asia, LINE and Shopee Live are major channels. In Korea, KakaoTalk commerce is significant. Do not assume Instagram and TikTok Shop are the default everywhere. Research market-specific platforms and behaviors before building a social commerce strategy for international markets.

### Community Toxicity Management
Even well-managed communities face toxicity challenges. Build clear community guidelines before launching, not after problems arise. Implement graduated enforcement (warning, temporary mute, temporary ban, permanent ban). Use AI moderation for first-pass filtering combined with human review for context-dependent decisions. Establish an appeals process. Document and respond to patterns (coordinated harassment, hate speech, misinformation) with transparent policy enforcement. Burnout among community managers is a real risk; plan for adequate staffing and rotation.

## Related Skills

- **SEO** -- Voice search and visual search overlap with organic search optimization strategies
- **Paid Advertising** -- Social commerce ad integrations, TikTok Shop Ads, and click-to-message ad formats
- **Content Engine** -- Content creation for video, podcast, and community channels
- **Influencer & Creator Marketing** -- Creator partnerships for social commerce, podcast guesting, and community seeding
- **Growth Engineering** -- Community-led growth, viral loops through social features, and referral amplification
- **CRO** -- Conversion optimization for social storefronts, chatbot funnels, and voice commerce flows
- **Analytics & Insights** -- Measurement and attribution for emerging channels with limited native analytics

## Agents Used

- **social-media-manager** — Platform-native social commerce strategy, community management, content calendar planning, social listening, UGC curation, and cross-platform engagement optimization
