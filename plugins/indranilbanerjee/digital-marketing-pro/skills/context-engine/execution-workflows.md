# Execution Workflows — Standard Operating Procedures

All marketing execution follows standardized workflows to ensure consistency, quality, and compliance. Each workflow is a numbered step-by-step procedure that agents follow during execution. Skipping steps is not permitted — if a step does not apply, log it as "N/A" with a reason.

---

## 1. Blog Publishing Workflow

Use for: blog posts, articles, guides, listicles, how-to content, thought leadership.

### Content Preparation

1. **Format check** — Verify content is in the target CMS format (HTML for WordPress, rich text for Webflow). Strip unsupported elements.
2. **Word count validation** — Confirm word count meets the content brief. Minimum thresholds by type:
   - Standard blog post: 800-1,500 words
   - Pillar page: 2,000-4,000 words
   - News/update post: 400-800 words
3. **Readability score** — Run through readability analysis. Target Flesch-Kincaid grade level based on audience:
   - B2C general: Grade 6-8 (Flesch score 60-70)
   - B2B professional: Grade 10-12 (Flesch score 40-55)
   - Technical/developer: Grade 12-14 (Flesch score 30-45)
4. **Brand voice check** — Score content against brand voice profile. Minimum score: 70/100.

### SEO Optimization

5. **Primary keyword placement** — Verify primary keyword appears in:
   - Page title (within first 60 characters)
   - H1 heading (exactly once)
   - First 100 words of body text
   - At least one H2 subheading
   - URL slug
6. **Meta description** — Write or verify meta description: 150-160 characters, includes primary keyword, contains a clear value proposition or CTA.
7. **Alt text** — Every image has descriptive alt text. Include primary keyword in at least one image alt (naturally, not forced).
8. **Internal links** — Minimum 3 internal links to relevant existing content. At least 1 link in the first 300 words. Anchor text is descriptive (not "click here").
9. **External links** — Include 1-3 authoritative external sources where relevant. Set to `target="_blank" rel="noopener"`.
10. **Schema markup** — Apply appropriate JSON-LD schema (`BlogPosting`, `Article`, or `HowTo`).

### Publishing

11. **Category and tag assignment** — Assign to exactly 1 primary category and 2-5 relevant tags. Use existing taxonomy; create new terms only when no match exists.
12. **Featured image** — Upload featured image meeting platform specs (WordPress: 1200x628 px minimum). Verify it displays correctly in social share preview.
13. **Schedule or publish** — If scheduling, confirm publish date/time aligns with content calendar. If publishing immediately, confirm with user.
14. **Verify live URL** — After publishing, confirm the live URL responds with HTTP 200. Check that the page renders correctly (no broken images, no layout issues).
15. **Log execution** — Record in campaign tracker: URL, publish date, primary keyword, word count, readability score, SEO score.
16. **Monitor first 24h** — Check pageviews, bounce rate, and average time on page after 24 hours. Flag if pageviews are below 50% of the brand's blog average.

---

## 2. Email Campaign Workflow

Use for: marketing emails, newsletters, drip sequences, promotional blasts, event invitations.

### List Selection

1. **Segment identification** — Select the target segment based on campaign brief. Document segment name, size, and selection criteria.
2. **List size verification** — Confirm recipient count. Flag if count deviates more than 20% from expected size.
3. **Consent verification** — Verify all recipients have valid marketing consent per applicable regulation:
   - GDPR regions: Opt-in consent on file
   - CAN-SPAM regions: No opt-out on file
   - CASL regions: Express or valid implied consent (check expiry)
4. **Suppression check** — Cross-reference against suppression list (unsubscribes, bounces, complaints). Remove any matches.

### Template Build

5. **Subject line** — Write subject line: 30-50 characters for mobile safety. Score against email scoring rubric (minimum 70/100).
6. **Preview text** — Write preheader: 40-90 characters. Must complement (not repeat) the subject line.
7. **Body structure** — Build email body: clear hierarchy (headline, body, CTA), single-column for mobile-first, inline CSS for compatibility.
8. **CTA placement** — Primary CTA button above the fold. Repeat CTA at email bottom. Button minimum 44x44 px tap target.
9. **Personalization mapping** — Map merge tags to data fields. Test that all merge tags resolve correctly. Set fallback values for empty fields.
10. **Unsubscribe link** — Confirm functional unsubscribe mechanism is present and visible. One-click unsubscribe header included.

### Quality Assurance

11. **Spam score check** — Run content through spam analysis. Target SpamAssassin score below 5.0. Flag trigger words (free, guarantee, act now, limited time).
12. **Test send** — Send to internal seed list (minimum 3 addresses across Gmail, Outlook, Apple Mail).
13. **Rendering review** — Verify rendering on desktop and mobile. Check dark mode compatibility. Confirm images load and alt text displays when images are blocked.

### Send

14. **Approval gate** — Obtain explicit approval from authorized user before sending.
15. **Schedule or send** — Set send time based on posting-time-analyzer.py output or brand's established best send time. Respect quiet hours (no sends 9 PM-8 AM recipient local time).
16. **Monitor delivery** — Track within first 2 hours:
    - Deliverability: Target >95%
    - Bounce rate: Flag if >3%
    - Unsubscribe rate: Flag if >0.5%
    - Spam complaints: Flag if >0.1%
17. **Performance log** — Record: send date, list size, subject line, open rate, click rate, conversion rate, revenue attributed.

---

## 3. Ad Campaign Workflow

Use for: Google Ads, Meta Ads, LinkedIn Ads, TikTok Ads, Pinterest Ads, Amazon Ads.

### May 2026 platform updates (read before configuring)

- **Google Performance Max (PMax) 2026 updates** — brand exclusion lists are now first-class (use them to keep PMax from spending on competitor brand terms or off-strategy categories); per-network placement reporting now exposed (use this to verify YouTube vs Display vs Search distribution matches the campaign objective); first-party audience exclusions supported; **15 videos per asset group** (was 5); **PMax experiments** for testing creative or audience changes against a control. Combined effect: PMax is now reasonable to run if you instrument it; the old "black box" criticism is mostly addressed by the exclusion + reporting features.
- **Meta Advantage+ shopping campaigns 2026** — in-app checkout, AI product overlays (price/reviews on product hover), retailer integrations standard. Creative should be designed at the product-tile scale, not full-frame. Catalog quality dominates performance — invest in clean product feed (high-res images, accurate stock status, full attributes) before tuning bids.
- **Meta Advantage+ Leads — globally available (May 2026)** — Meta's automated lead-generation campaign type rolled out globally in May 2026 (was country-limited in 2025). Single campaign type that auto-tests creative, audience expansion, and placement. **Use when:** lead-gen is the objective AND the brand has installed lead-quality feedback (Conversions API tied to CRM) — without quality feedback Advantage+ Leads optimises for cheap leads, not qualified leads. **Don't use when:** the brand is in a regulated Special Ad Category (housing, credit, employment) — automated audience expansion fights against the manual targeting constraints those categories require.
- **Threads ads (global, March 2026 rollout completing May 2026)** — Meta opened Threads to ads globally with image-only formats in standard placements. Inventory is cheap-to-moderate (still ramping). Best for: brand awareness with a younger / news-adjacent audience, journalism / B2B thought-leadership amplification, and creator collaborations. Image-only constraint means treat Threads as a static placement — no video, no carousels yet (May 2026). Pair with Instagram in the same campaign for cross-app delivery; do not allocate >10% of Meta budget to Threads alone until your account-level data shows comparable CPA.
- **Meta brand-safety controls (May 2026)** — Advertiser-level inventory filters tightened in Q2 2026 after Reels-adjacency incidents. Three tiers: Expanded (most reach, lowest brand-safety filter), Moderate (default), and Limited (highest filter, ~30% less reach). Default to Moderate; move to Limited only for regulated industries (finance, healthcare, B2G) or after a documented brand-safety incident — the reach cost is real. The Brand Suitability dashboard now exposes which Reels topics your ads served adjacent to in the last 30 days.
- **LinkedIn Ads** — March 2026 algorithm shift on the organic side also affects ad relevance scoring; ads carrying external links get lower distribution than ads with in-platform content (lead gen forms, document ads, conversation ads). Lead gen forms remain the highest-converting LinkedIn ad format.
- **TikTok Ads (post-USDS Jan 2026)** — US-served ads now run through USDS LLC infrastructure; ad-account migration was automatic for existing US advertisers. AI-generated creative requires AI disclosure label.
- **Retail media (Amazon, Walmart, Instacart)** — combined retail-media ad spend now ~$60B+/year (US 2026). Worth a campaign track for any DTC or CPG brand selling on these platforms.

### Campaign Structure

1. **Campaign hierarchy** — Set up: Campaign (objective, budget, schedule) → Ad Group/Ad Set (targeting, bid) → Ad (creative, copy, CTA, destination URL).
2. **Naming convention** — Apply standard naming: `{Brand}_{Objective}_{Audience}_{Platform}_{Date}`. Example: `Acme_Leads_Retargeting_Meta_2026-02`.

### Audience Setup

3. **Targeting definition** — Configure audience: demographics, interests, behaviors, geo-locations. Document all targeting parameters.
4. **Exclusions** — Set exclusion audiences: existing customers (if prospecting), recent converters, internal traffic, competitors' employees (if possible).
5. **Lookalike/similar audiences** — If using, specify source audience (minimum 1,000 contacts for Meta, 300 for LinkedIn) and similarity percentage (1-3% for precision, 5-10% for reach).

### Creative

6. **Creative upload** — Prepare assets per platform specs (see `platform-specs.md` and `platform-publishing-specs.md`). Minimum 3 creative variations for A/B testing.
7. **Ad copy** — Write copy per platform character limits. Score against ad creative rubric (minimum 70/100 to launch).
8. **Landing page** — Verify destination URL loads in under 3 seconds, matches ad messaging (message match), and has working conversion tracking.

### Budget and Bidding

9. **Bid strategy selection** — Choose strategy aligned with campaign objective:
   - Awareness: Maximize reach / Target CPM
   - Traffic: Maximize clicks / Target CPC
   - Conversions: Maximize conversions / Target CPA / Target ROAS
10. **Daily budget** — Set daily budget within brand's `budget_range`. Never exceed the brand's maximum daily budget without explicit re-confirmation from user.
11. **Budget pacing** — Configure even daily distribution unless campaign brief specifies otherwise (e.g., dayparting, accelerated delivery).

### Compliance and Launch

12. **Compliance review** — Check against platform ad policies (see `compliance-rules.md` Section 4). Verify required disclaimers for regulated industries. Confirm Special Ad Category designation if applicable (housing, credit, employment).
13. **Conversion tracking** — Verify pixel/tag fires correctly on conversion page. Test with a click-through before launch.
14. **Launch** — Activate campaign. Confirm status shows "Active" or "Running" (not "Limited" or "Error").

### Optimization

15. **48-hour check** — Review: impressions, CTR, CPC. Pause underperforming creatives (CTR below 50% of ad group average). Confirm budget is pacing correctly.
16. **7-day optimization** — Review: CPA, ROAS, conversion rate. Adjust bids, reallocate budget from underperforming ad groups. Add negative keywords (search campaigns).
17. **14-day review** — Full performance review: creative fatigue check (frequency >3.0), audience saturation, budget efficiency. Refresh creatives if CTR has declined >20% from launch.
18. **Performance log** — Record: impressions, clicks, CTR, CPC, conversions, CPA, ROAS, spend. Compare against industry benchmarks from `industry-profiles.md`.

---

## 4. Social Scheduling Workflow

Use for: organic social media posts across all platforms.

1. **Content format** — Prepare content per platform specifications (see `platform-specs.md`). Respect character limits, image sizes, and video duration limits per platform.
2. **Platform-specific formatting** — Adapt content for each platform's culture:
   - LinkedIn: Professional tone, industry insights, paragraph breaks
   - Instagram: Visual-first, caption with line breaks, emojis appropriate to brand voice
   - Twitter/X: Concise, conversational, thread format for long content
   - TikTok: Native video, trending audio consideration, casual tone
3. **Hashtag research** — Select 3-5 hashtags per post. Mix: 1-2 high-reach (100K+ posts), 2-3 niche/industry-specific (1K-100K posts). Platform exceptions: Twitter/X (1-2 max), LinkedIn (3-5), Instagram (5-10).
4. **Optimal posting time** — Use `posting-time-analyzer.py` output or brand's established best posting times. Cross-reference with `platform-specs.md` general recommendations.
5. **Visual assets** — Verify all images/videos meet platform dimension and file size requirements. Check text-safe zones for Stories/Reels content.
6. **Schedule** — Queue post in scheduling tool or platform native scheduler. Confirm scheduled time is correct (timezone awareness).
7. **Engagement monitoring** — Check engagement at 2 hours and 24 hours after posting. Respond to comments within brand guidelines.
8. **Performance report** — At 24 hours and 7 days, log: impressions, reach, engagement rate, saves, shares, link clicks (if applicable). Compare to brand's rolling 30-day average.

---

## 5. CRM Operations Workflow

Use for: contact imports, lead creation, data updates, list management, pipeline operations.

1. **Data validation** — Check all records for required fields. Validate formats:
   - Email: RFC 5322 compliant, domain has MX record
   - Phone: E.164 format (international), strip non-numeric characters
   - URL: Must include protocol (https://)
   - Country/State: ISO 3166 codes
2. **Deduplication check** — Run dedup using matching hierarchy:
   - Primary: Email address (exact match)
   - Secondary: Phone number (normalized)
   - Tertiary: Company name + contact name (fuzzy match, >85% similarity)
3. **Field mapping** — Map source fields to CRM native fields. Document any unmapped fields. Create custom fields only with explicit approval.
4. **Pre-import snapshot** — Take a backup snapshot of affected records before any bulk operation. Store snapshot path in execution log.
5. **Import/create** — Execute import. For bulk operations (>100 records): use batch API endpoints, implement rate limiting per CRM vendor specs.
6. **Verification** — Confirm: record count matches expected count, no data truncation, all required fields populated. Spot-check 5 random records for accuracy.
7. **Campaign linking** — Associate imported contacts with the relevant campaign/list in CRM.
8. **Sync log entry** — Record: operation type, record count, source, date, operator, any errors or warnings.

---

## 6. Report Delivery Workflow

Use for: weekly pulse reports, monthly reviews, QBRs, ad-hoc performance reports.

1. **Data pull** — Query all connected analytics sources (Google Analytics, Search Console, ad platforms, email platforms, CRM) via MCP servers. Normalize date ranges to the reporting period.
2. **Aggregation** — Combine data from multiple sources. Normalize: currency (convert to brand's primary currency), date formats (ISO 8601), metric definitions (e.g., "conversions" definition consistent across platforms).
3. **KPI calculation** — For each KPI, calculate:
   - Current period value
   - vs. target (% attainment)
   - vs. previous period (% change, direction arrow)
   - vs. industry benchmark (above/below, percentile if available)
4. **Anomaly detection** — Flag any metric that changed >25% period-over-period. Flag any KPI below 80% of target. Flag any metric that deviates >2 standard deviations from the 90-day mean.
5. **Format selection** — Choose delivery format per report type:
   - Weekly pulse: Slack blocks or short email
   - Monthly review: Google Slides or HTML email with charts
   - QBR: Google Slides presentation deck
   - Ad-hoc: Google Sheets or direct message
6. **Brand/agency voice** — Apply appropriate voice:
   - Internal reports: Can use shorthand, reference multiple clients (agency mode)
   - Client-facing reports: Professional, third-person, brand-appropriate language
7. **Send** — Deliver report via configured channel. Include a 2-3 sentence executive summary at the top.
8. **Confirm receipt** — Log delivery timestamp. For email delivery, verify no bounce. For Slack, verify message posted successfully.

---

## 7. SMS/WhatsApp Workflow

Use for: promotional SMS, transactional SMS with marketing elements, WhatsApp marketing messages.

### Compliance (Mandatory First Step)

1. **Consent verification** — Verify opt-in consent for every recipient:
   - US (TCPA): Express written consent for marketing SMS. Prior express consent for informational.
   - EU (GDPR): Explicit opt-in consent.
   - Canada (CASL): Express consent with documented proof.
   - All: Consent must be specific to SMS/WhatsApp channel (email consent does not transfer).
2. **Quiet hours** — Enforce sending windows: no messages between 9:00 PM and 8:00 AM in recipient's local timezone. South Korea: no messages 9 PM-8 AM (law). US: varies by state, 8 AM-9 PM is safest.
3. **Opt-out mechanism** — Every message must include opt-out instructions:
   - SMS: "Reply STOP to unsubscribe" (exact or equivalent)
   - WhatsApp: Unsubscribe link or reply keyword

### Message Preparation

4. **Message formatting** — Respect character limits:
   - SMS (GSM-7 encoding): 160 characters per segment. Unicode: 70 characters per segment.
   - WhatsApp: 1,024 characters. Supports rich media (images up to 5 MB, video up to 16 MB, documents up to 100 MB).
5. **Sender ID verification** — Confirm sending number/ID is registered and verified:
   - SMS: Toll-free number, short code, or 10DLC (US). Alphanumeric sender ID (international, where supported).
   - WhatsApp: Verified WhatsApp Business API number with approved display name.
6. **Template approval (WhatsApp)** — WhatsApp marketing messages require pre-approved templates. Submit template for Meta approval (24-48h turnaround). Session messages (within 24h of user message) do not require templates.

### Send and Monitor

7. **Test send** — Send to internal test numbers first. Verify delivery and rendering.
8. **Send** — Execute send. Monitor delivery rate in real-time.
9. **Delivery tracking** — Track: delivery rate (target >95%), response rate, opt-out rate (flag if >1% per send). Log undeliverable numbers for list cleanup.
10. **Cost tracking** — Record per-message cost. SMS costs vary by country and carrier. **WhatsApp Business Platform switched to per-message pricing on 1 July 2025** (was per-conversation). India marketing-template messages are roughly USD 0.0118 each (cheapest globally; Germany ~11×). Click-to-WhatsApp ads and Facebook Page CTAs open a 72-hour free service window; service messages inside the 24-hour customer-care window remain free. Alert if campaign cost exceeds budget by >10%.

---

## 8. Memory Operations Workflow

Use for: storing marketing insights, campaign learnings, content to brand memory, knowledge base updates.

1. **Content extraction** — Strip formatting artifacts. Extract key points, metrics, and actionable insights. Preserve source attribution (campaign name, date, channel).
2. **Metadata tagging** — Apply structured metadata:
   - `content_type`: insight | campaign_data | performance_snapshot | content_piece | voice_sample
   - `tags`: Array of relevant topic tags (e.g., ["email", "subject-lines", "open-rate"])
   - `source`: Origin campaign or analysis
   - `date`: ISO 8601 timestamp
   - `confidence`: high | medium | low (for insights)
3. **Deduplication** — Generate content hash. Check against existing entries. If duplicate detected, update the existing entry's metadata (timestamp, confidence) rather than creating a new entry.
4. **Storage** — Write to appropriate location under `~/.claude-marketing/brands/{slug}/`:
   - Insights: `insights.json` (rolling buffer, max 200 entries, oldest evicted)
   - Campaigns: `campaigns/{id}.json`
   - Performance: `performance/{campaign}-{date}.json`
   - Content: `content-library/`
5. **Index update** — Update relevant index files (`_index.json` for campaigns). Ensure the new entry is searchable by tags and date.
6. **Verification** — Read back the stored entry. Confirm content matches what was written. Confirm search/lookup returns the entry.
7. **Sync state** — Update `_active-brand.json` last-modified timestamp. Log the memory operation in the execution log.

---

## Pre-Flight Checklist

A quick-reference table of mandatory checks per execution type. All checks must pass before execution proceeds.

| Check | Blog | Email | Ads | Social | CRM | Report | SMS/WA | Memory |
|---|---|---|---|---|---|---|---|---|
| Brand context loaded | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Compliance rules applied | Yes | Yes | Yes | Yes | Yes | No | Yes | No |
| Content scored (rubric) | Yes | Yes | Yes | Yes | No | No | No | No |
| Platform specs verified | Yes | Yes | Yes | Yes | No | No | Yes | No |
| Consent/opt-in verified | No | Yes | No | No | No | No | Yes | No |
| Budget within range | No | No | Yes | No | No | No | Yes | No |
| Test send/preview | No | Yes | No | No | No | No | Yes | No |
| Approval gate | Medium | Medium | High | Medium | High | Low | High | Low |
| Backup/snapshot taken | No | No | No | No | Yes | No | No | No |
| Tracking verified | Yes | Yes | Yes | No | No | No | Yes | No |
| Performance log entry | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
