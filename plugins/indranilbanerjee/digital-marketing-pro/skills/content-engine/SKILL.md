---
name: content-engine
description: "Create or optimize marketing content. Use when: blog posts, ad copy, emails, social posts, landing pages, voice guidelines."
argument-hint: "[content-type and topic]"
---

# Content Engine

## When to Use This Skill

Activate this module when the user's request involves any of the following:

- **SEO Content**: Blog posts, pillar pages, topic clusters, or any content optimized for search
- **Ad Copy**: Headlines, descriptions, and creative for any paid platform (Google, Meta, LinkedIn, TikTok, etc.)
- **Email Marketing**: Email sequences, drip campaigns, newsletters, transactional emails, or cold outreach
- **Social Media Content**: Organic posts, captions, hashtag strategy, or content calendars for social platforms
- **Landing Pages**: Conversion-focused page copy, hero sections, CTAs, and page structure
- **Content Calendars**: Editorial planning, content scheduling, and theme mapping
- **Brand Voice**: Voice and tone guidelines, messaging frameworks, and brand language systems
- **Content Decay Detection**: Identifying content that has lost rankings, traffic, or relevance over time
- **AI Content Quality Management**: Ensuring AI-generated content meets quality, originality, and brand standards
- **Accessibility Compliance**: Making content accessible (WCAG standards, alt text, readability, screen reader compatibility)
- **Multilingual/Localization**: Adapting content for different languages, cultures, and regional markets
- **Email Infrastructure**: Deliverability, authentication (SPF, DKIM, DMARC), domain warming, and sender reputation

**Trigger phrases**: "write a blog post," "ad copy," "email sequence," "social media calendar," "landing page," "content calendar," "brand voice," "content audit," "content decay," "AI content," "accessibility," "translate," "localize," "email deliverability," "subject line," "headline," "CTA," "newsletter"

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

Before executing content work, gather:

1. **Content Type**: Which specific content format is needed?
2. **Audience**: Who is this content for? (Link to personas from Audience Intelligence if available)
3. **Objective**: What should this content achieve? (Traffic, conversions, engagement, education, retention)
4. **Brand Voice**: Does a brand voice guide exist? What is the tone? (Professional, casual, authoritative, playful, etc.)
5. **Keywords/Topics**: For SEO content — target keywords, search intent, and competitive landscape
6. **Platform**: Where will this content live? (Platform-specific requirements matter)
7. **Funnel Stage**: Where does this content fit in the customer journey?
8. **Existing Content**: What related content already exists? (Avoid cannibalization)
9. **Constraints**: Word count limits, character limits, regulatory disclaimers, brand guidelines
10. **Performance Benchmarks**: What does success look like for this content type?

For quick requests (e.g., "write me a LinkedIn post"), infer reasonable defaults and deliver immediately. For strategic content work, gather full context.

## Capabilities

- **SEO Content Creation**: Keyword-optimized blog posts, pillar pages, topic cluster design, meta titles/descriptions, internal linking strategy, and featured snippet optimization
- **Ad Copy (All Platforms)**: Google Ads (RSAs, headlines, descriptions), Meta Ads (primary text, headlines, descriptions), LinkedIn Ads, TikTok Ads, Twitter/X Ads — platform-specific formats and character limits
- **Email Sequences**: Welcome sequences, nurture drips, cart abandonment, re-engagement, onboarding, upsell/cross-sell, and win-back sequences with subject lines, preview text, body copy, and CTAs
- **Social Content**: Platform-native content for LinkedIn, Twitter/X, Instagram, TikTok, Facebook, YouTube, Pinterest — including captions, hashtags, hooks, and post structure
- **Landing Page Copy**: Hero headline/subhead, value proposition blocks, social proof, feature/benefit sections, FAQ, and CTA optimization
- **Content Calendars**: Editorial calendars with theme mapping, content pillars, publishing cadence, and channel distribution plans
- **Brand Voice System**: Voice attributes, tone spectrum (how voice adapts by context), vocabulary guidelines, do/don't examples, and brand-specific terminology
- **Content Decay Detection**: Methodology for identifying declining content by traffic, rankings, engagement, and freshness — with refresh prioritization
- **AI Content Quality Management**: Quality checklist for AI-generated content, originality verification approach, brand alignment review, fact-checking protocol, and human-in-the-loop guidelines
- **Accessibility Compliance**: WCAG 2.2 AA content guidelines, alt text writing, readability scoring, heading structure, link text, color contrast guidance, and screen reader optimization
- **Multilingual/Localization**: Translation-ready content structuring, cultural adaptation framework, locale-specific messaging guidelines, and RTL language considerations
- **Email Infrastructure**: SPF/DKIM/DMARC setup guidance, domain warming schedules, list hygiene practices, deliverability monitoring, and sender reputation management

## Process

**Primary Workflow: Content Creation**

1. **Content Strategy Alignment**
   - Confirm the content type, audience, objective, and funnel stage
   - Check for existing content that may overlap (prevent cannibalization)
   - Identify the core message and key takeaway
   - Select the appropriate content framework for the task

2. **Research & Preparation**
   - For SEO content: Analyze target keyword, search intent, SERP features, and top-ranking content
   - For ad copy: Review platform specs, competitor ads, and audience pain points
   - For email: Identify the sequence trigger, desired action, and subscriber segment
   - For social: Check platform trends, optimal formats, and audience behavior patterns
   - For landing pages: Identify the traffic source, visitor intent, and conversion goal

3. **Content Creation**
   - Apply the brand voice guidelines (or establish them if none exist)
   - Write to the specific format requirements (character limits, structure, platform norms)
   - Build in persuasion architecture:
     - **Attention**: Hook/headline that stops the scroll or earns the click
     - **Interest**: Problem-aware framing that demonstrates understanding
     - **Desire**: Solution positioning with clear benefits and social proof
     - **Action**: Clear, specific CTA with reduced friction
   - Include SEO elements where applicable (keywords, headers, internal links, meta data)
   - Write multiple variations for testing when the format supports it (ad copy, subject lines, CTAs)

4. **Quality Assurance**
   - Brand voice alignment check
   - Readability score assessment (aim for grade 8 or below for general audiences). Run the analyzer on the draft:
     ```bash
     python "${CLAUDE_PLUGIN_ROOT}/scripts/readability-analyzer.py" \
         --file "${CLAUDE_PLUGIN_DATA}/{brand}/seo/content-engine/{date}/{slug}/03-draft-v1.md" \
         --target b2c_general
     ```
     (`--text` inline or `--file` path — mutually exclusive, one required; `--target` one of `b2c_general`, `b2b_professional`, `b2b_technical`, `children`, `academic`.)
   - Accessibility review (heading hierarchy, alt text guidance, link text clarity)
   - Fact-checking for any claims, statistics, or references
   - Platform compliance check (ad policies, character limits, format requirements)
   - SEO on-page audit (keyword placement, meta data, internal links) for search content
   - AI content quality check if AI-assisted (originality, brand alignment, factual accuracy)

5. **Optimization & Testing Plan**
   - Define what to A/B test (headlines, CTAs, email subject lines, ad creative)
   - Set performance benchmarks based on content type and channel
   - Schedule content review dates for decay monitoring
   - Plan content repurposing across formats and channels

**Secondary Workflow: Content Audit & Refresh**

1. Pull content inventory (URLs, publish dates, current traffic/rankings)
2. Score each piece on freshness, performance trend, and relevance
3. Categorize: Keep (performing well), Refresh (declining but fixable), Consolidate (thin/overlapping), Remove (irrelevant/harmful)
4. Prioritize refresh candidates by traffic recovery potential
5. Create refresh briefs with specific update instructions

## Reference Files

- `seo-content.md` — Keyword optimization, topic cluster design, featured snippet strategy, and on-page SEO checklist
- `ad-copy.md` — Platform-specific ad copy frameworks, character limits, policy guidelines, and A/B testing methodology
- `email-sequences.md` — Sequence templates (welcome, nurture, abandonment, etc.), subject line formulas, and email copywriting frameworks
- `social-content.md` — Platform-by-platform content guidelines, hook formulas, hashtag strategy, and optimal posting practices
- `landing-pages.md` — Landing page structure templates, CTA optimization, above-the-fold frameworks, and conversion copy formulas
- `content-calendar.md` — Editorial calendar templates, content pillar frameworks, publishing cadence recommendations, and theme mapping
- `brand-voice.md` — Voice development methodology, tone spectrum design, vocabulary guidelines, and brand voice audit process
- `content-decay.md` — Decay detection methodology, content scoring rubric, refresh prioritization framework, and update tracking
- `ai-content-quality.md` — AI content quality checklist, originality verification, brand alignment review, and human review workflow
- `accessibility.md` — WCAG 2.2 AA content checklist, alt text writing guide, readability standards, and inclusive language guidelines
- `multilingual.md` — Localization readiness checklist, cultural adaptation framework, translation management, and RTL considerations
- `email-infrastructure.md` — Authentication setup (SPF/DKIM/DMARC), domain warming plan, deliverability best practices, and list hygiene
- `email-automation.md` — Automation trigger design, workflow mapping, dynamic content rules, and behavioral email logic

## Output Formats

| Deliverable | Format | Description |
|---|---|---|
| Blog Post / Article | Document | Complete SEO-optimized content with meta data, headers, and internal link suggestions |
| Ad Copy Set | Document / Spreadsheet | Multiple variations per platform with headlines, descriptions, and CTAs |
| Email Sequence | Document | Full sequence with subject lines, preview text, body copy, CTAs, and send timing |
| Social Media Content | Spreadsheet / Calendar | Posts organized by platform, date, copy, hashtags, and visual direction |
| Landing Page Copy | Document | Section-by-section copy with headline, subhead, body, bullets, CTAs, and form copy |
| Content Calendar | Spreadsheet | Monthly/quarterly editorial plan with themes, topics, formats, channels, and owners |
| Brand Voice Guide | Document | Complete voice system with attributes, tone spectrum, vocabulary, and examples |
| Content Audit Report | Spreadsheet + Document | Inventory with scores, categorization, and prioritized refresh recommendations |
| Accessibility Report | Checklist document | Content-level accessibility assessment with specific remediation steps |

## Edge Cases

### Regulated Industry Content (Disclaimers Required)
- **Situation**: Healthcare, financial services, legal, insurance, cannabis, gambling, or other industries requiring mandatory disclaimers, disclosures, or compliance language
- **Approach**: Flag the regulatory requirement at the start of content creation. Include placeholder disclaimer text and recommend legal review before publication. For ad platforms, note specific policy restrictions (e.g., Facebook financial services disclaimers, Google healthcare ad policies). Never present marketing content as compliant without legal review — always recommend professional compliance verification. Keep marketing copy and compliance language visually distinct.

### Multilingual Campaigns
- **Situation**: Content needs to work across multiple languages and cultural contexts
- **Approach**: Write source content with localization in mind (avoid idioms, cultural references, humor that won't translate). Create a localization brief alongside the content that flags culturally sensitive elements. Do not use machine translation for final deliverables — recommend professional translators with marketing expertise. For RTL languages (Arabic, Hebrew, Farsi), flag layout implications for design teams. Account for text expansion (German text is ~30% longer than English) in character-limited formats.

### Content Cannibalization
- **Situation**: Multiple pages competing for the same keyword or covering the same topic
- **Approach**: Audit existing content before creating anything new. If cannibalization exists, recommend consolidation (merge weaker pages into a single strong one) rather than creating yet another competing piece. Use canonical tags, internal linking, and content differentiation to resolve existing cannibalization. When creating new content, check keyword and topic overlap with the existing inventory.

### AI-Generated Content Disclosure
- **Situation**: User wants to publish AI-generated content and needs guidance on disclosure
- **Approach**: Recommend transparency. Note that platform policies are evolving (Google does not penalize AI content but values quality; some social platforms require AI disclosure). Always recommend human review and editing of AI-generated drafts. Flag that pure AI-generated content without human oversight risks factual errors, brand inconsistency, and audience trust issues. Provide the quality assurance checklist for AI-assisted content.

### Accessibility for Video/Audio Content
- **Situation**: Content includes video, audio, or interactive elements needing accessibility treatment
- **Approach**: Recommend captions (not auto-generated — accuracy matters) for all video content. Provide audio descriptions for visual-only information in videos. Create transcripts for podcasts and audio content. Ensure interactive elements are keyboard-navigable. Test with screen readers. Follow WCAG 2.2 AA at minimum, with AAA as a stretch goal for public-facing content.

### RTL Languages
- **Situation**: Content in Arabic, Hebrew, Farsi, Urdu, or other right-to-left languages
- **Approach**: Flag RTL implications early in the process. Content structure, CTA placement, and visual hierarchy all reverse. Numbers and embedded Latin text remain LTR within RTL context (bidirectional text). Recommend native-speaker review for all RTL content. Design templates must support RTL layouts. Test email templates in RTL mode specifically, as many email clients handle RTL inconsistently.

## Numbered output convention

All content-engine outputs go to `${CLAUDE_PLUGIN_DATA}/{brand}/seo/content-engine/{YYYY-MM-DD}/{slug}/`:

```
00-input.md                topic, target keyword, intent, format, source brief (from keyword-cluster?)
01-research.md             source list, key data points, expert quotes, competitor references
02-outline.md              H1, H2/H3 structure with target word counts per section
03-draft-v1.md             first complete draft
04-fact-check.md           per-claim verification + citations
05-humanize.md             AI-pattern detection + rewrite log
06-brand-voice-check.md    voice score (formality/energy/humor/authority) vs brand profile
07-seo-checklist.md        title, meta, schema, internal links, image alt text
08-quality-scorecard.md    the gates below
09-publish-ready.md        final clean copy + handoff metadata
PLAN.md                    summary + publish instructions
```

## Quality scorecard

| Gate | What it checks |
|---|---|
| **brand_voice_match** | `06-brand-voice-check.md` shows ≤ 1.5 point deviation from brand profile on each axis (formality/energy/humor/authority) |
| **fact_check_clean** | `04-fact-check.md` shows 0 unverified claims and ≥ 1 citation per factual statement |
| **humanize_passed** | `05-humanize.md` shows AI-pattern density below the brand-specific threshold (default: under 10% of paragraphs flagged) |
| **seo_complete** | `07-seo-checklist.md` shows title ≤ 60 chars, meta 150-160 chars, ≥ 1 schema type, ≥ 3 internal links, all images have alt text |
| **eu_disclosure_if_ai** | If the brand has `target_markets` including EU AND the content is AI-generated, `09-publish-ready.md` carries the required Article 50 disclosure (machine-readable + visible) |

`status: ready` requires all five gates pass.

## Chain handoffs

- **Upstream:** `/digital-marketing-pro:content-brief` (preferred — pre-researched) or `/digital-marketing-pro:keyword-cluster` (`06-pillar-pages.md` becomes content briefs)
- **Downstream:**
  - `/digital-marketing-pro:publish-blog` — pushes the publish-ready draft to the CMS
  - `/digital-marketing-pro:social-strategy` — repurposes the article across platforms (or hand to `contentforge:social-adapt` if ContentForge is installed)
  - `/digital-marketing-pro:check` — final pre-publish gate
  - `/digital-marketing-pro:c2pa-metadata` — if AI-generated images accompany the article and EU markets are targeted

## Tips & caveats

- **Brand voice deviation tolerance is per-axis, not aggregate.** A piece that's 1 point off on every axis is not the same as 4 points off on humor alone — the latter is a fail even if the average looks OK.
- **Humanize step is not a guarantee** against AI-detection tools — it's a probabilistic improvement. For pieces that MUST pass an explicit AI-detection gate, use the ContentForge pipeline (`contentforge:create-content`) which has the 29-pattern catalog + self-critique meta-pass.
- **Fact-check is content's most-skipped gate.** Don't ship a piece with "0 unverified" only because no one looked. Run `/digital-marketing-pro:verify-claims` against the draft if you didn't have a fact-checker in the loop.
- **For pillar content,** target the upper bound of word count (3000+ for SaaS, 5000+ for B2B research) — pillar pages need depth for topical authority. For spoke content, the lower bound is fine.
- **Don't write the meta description last.** Write it FIRST, before the article — it's the answer to "what's this page's promise?" Writing it last produces post-hoc summaries that don't drive click intent.

## Related Skills

- **Audience Intelligence** — For persona-specific content targeting and messaging that resonates with defined segments
- **AEO/GEO Intelligence** — For optimizing content to be cited by AI answer engines and maintaining entity consistency
- **Campaign Orchestrator** — For mapping content to campaign channels and ensuring message consistency across touchpoints
- **Funnel Architect** — For aligning content to funnel stages and ensuring every stage has appropriate content support
- **Digital PR & Authority** — For thought leadership content, press releases, and E-E-A-T authority building through content
- **Analytics & Insights** — For measuring content performance, identifying decay, and optimizing based on data

## Context efficiency

This skill's reference docs (`skills/<this-skill>/*.md`) sum to ~30-50KB. Don't load them eagerly — pick targeted sections:

- **Grep before Read.** Find the keyword or section heading first, then Read with `offset` + `limit` to pull just that range.
- **Walk `${CLAUDE_SKILL_DIR}` once.** Use a single directory listing to see what's there, then Read only the files that match your current step.
- **One source at a time.** If the workflow says "consult three reference files," read them sequentially after deciding what you need from each. Bulk-loading all three blows the per-skill 5K-token budget that auto-compaction reserves.
- **Strip noise from CSV inputs.** If the input is a large CSV, grep the header line first to pick columns, then process row-by-row — do not Read the whole file into context.
