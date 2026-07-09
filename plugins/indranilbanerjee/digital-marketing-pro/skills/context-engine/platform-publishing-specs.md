# Platform Publishing Specs — API Requirements & Content Formats

This file defines the API-level requirements for publishing and managing content across marketing platforms. Use this reference when constructing payloads, mapping fields, and validating content before execution. For visual creative specs (image sizes, character limits for organic posts), see `platform-specs.md`.

---

## 1. WordPress

### REST API — Post Creation

| Field | Type | Details |
|---|---|---|
| `title` | string (rendered) | Post title. SEO best practice: keep under 60 characters for full SERP display. |
| `content` | string (HTML) | Full post body in HTML. Supports Gutenberg block markup. Classic editor uses standard HTML. |
| `excerpt` | string | Manual excerpt. If empty, WordPress auto-generates from first 55 words. Write a custom 150-160 character excerpt for SEO. |
| `status` | enum | `draft` | `publish` | `future` | `pending` | `private`. Use `future` with `date` field for scheduling. |
| `date` | string (ISO 8601) | Publish date. For scheduled posts, set `status: future` and `date` to future timestamp. Timezone from WordPress settings. |
| `categories` | array[int] | Category IDs (not names). Look up IDs via `GET /wp-json/wp/v2/categories?search={name}`. Assign exactly 1 primary category. |
| `tags` | array[int] | Tag IDs. Look up via `GET /wp-json/wp/v2/tags?search={name}`. Create new tags with `POST /wp-json/wp/v2/tags`. |
| `featured_media` | int | Attachment ID for featured image. Upload image first via `POST /wp-json/wp/v2/media` (multipart/form-data). |
| `slug` | string | URL slug. Auto-generated from title if omitted. For SEO: include primary keyword, use hyphens, keep under 60 characters. |
| `author` | int | Author user ID. Defaults to authenticated user. |
| `comment_status` | enum | `open` | `closed`. Default from WordPress settings. |
| `meta` | object | Custom fields. Yoast SEO fields below. |

### Yoast SEO Meta Fields

| Meta Key | Max Length | Purpose |
|---|---|---|
| `_yoast_wpseo_title` | 60 chars | SEO title (overrides post title in SERP). Use `%%title%% %%sep%% %%sitename%%` variables or write custom. |
| `_yoast_wpseo_metadesc` | 160 chars | Meta description for SERP snippet. Include primary keyword. End with CTA or value proposition. |
| `_yoast_wpseo_focuskw` | N/A | Focus keyphrase for Yoast analysis. Single keyword or phrase. |
| `_yoast_wpseo_canonical` | URL | Canonical URL if different from default permalink. |
| `_yoast_wpseo_opengraph-title` | 60 chars | Open Graph title for social sharing (falls back to SEO title). |
| `_yoast_wpseo_opengraph-description` | 200 chars | Open Graph description for social sharing. |

### Rate Limits and Authentication

| Parameter | Value |
|---|---|
| Authentication | Application Passwords (recommended), JWT, or OAuth 2.0 |
| Rate limit | No built-in limit; hosting provider may impose limits (typically 60-120 req/min) |
| Media upload max | Determined by server `upload_max_filesize` (typically 2-64 MB) |
| Batch operations | Not natively supported; use sequential requests with 100ms delay |

---

## 2. Webflow

### CMS API — Item Creation

| Field | Type | Details |
|---|---|---|
| `collection_id` | string | Target CMS collection ID. Retrieve via `GET /collections`. |
| `fields` | object | Key-value pairs matching collection field slugs. |
| `fields.name` | string | Item name (required). Used as the primary display name. |
| `fields.slug` | string | URL slug. Auto-generated if omitted. Must be unique within collection. |
| `fields._archived` | boolean | Set `true` to archive (hide from site). Default: `false`. |
| `fields._draft` | boolean | Set `true` to save as draft (not published). Default: `false`. |
| `fields.[rich-text]` | string (HTML subset) | Supports: `<h1>`-`<h6>`, `<p>`, `<a>`, `<strong>`, `<em>`, `<ul>`, `<ol>`, `<li>`, `<blockquote>`, `<img>`, `<figure>`. No `<script>`, `<style>`, or custom attributes. |
| `fields.[image]` | object | `{ "url": "https://...", "alt": "Description" }`. Image must be publicly accessible URL. |
| `fields.[reference]` | string | Referenced item ID for relational fields. |
| `fields.[multi-reference]` | array[string] | Array of referenced item IDs. |

### Rate Limits

| Parameter | Value |
|---|---|
| General API | 60 requests per minute per site |
| CMS API | 60 requests per minute |
| Publish API | 1 publish per minute per site |
| Authentication | API token (v2) or OAuth 2.0 |
| Max items per collection | 10,000 (CMS plan), 100,000 (Business plan) |

---

## 3. Email Platforms

### Payload Comparison

| Feature | SendGrid | Klaviyo | Customer.io | Brevo (Sendinblue) | Mailgun |
|---|---|---|---|---|---|
| **Endpoint** | `POST /v3/mail/send` | `POST /api/campaigns` | `POST /v1/send/email` | `POST /v3/smtp/email` | `POST /v3/{domain}/messages` |
| **Personalization syntax** | `{{variable}}` or `-variable-` (legacy) | `{{ variable }}` (Django/Jinja) | `{{customer.variable}}` (Liquid) | `{{ contact.variable }}` | `%recipient.variable%` |
| **Conditional logic** | Handlebars: `{{#if}}` | Jinja: `{% if %}` | Liquid: `{% if %}` | Jinja: `{% if %}` | Not supported in templates |
| **Scheduling** | `send_at` (Unix timestamp) | `send_time` (ISO 8601) | `send_at` (Unix timestamp) | `scheduledAt` (ISO 8601) | `o:deliverytime` (RFC 2822) |
| **Max schedule ahead** | 72 hours | Unlimited | Unlimited | Unlimited | 7 days |
| **List/segment ref** | List ID or segment ID in `to` | List ID or segment ID | Segment ID or filter | List ID or contact filter | Mailing list address |
| **Suppression handling** | Auto-suppresses bounces, unsubs, spam reports | Auto-suppresses; profiles marked suppressed | Auto-suppresses; explicit suppression API | Auto-suppresses; blocklist API | Auto-suppresses; built-in suppression list |
| **Rate limit** | 10,000 req/min (default) | 75 req/s (campaigns), 350 req/s (profiles) | 100 req/s | 50 req/s | 300 req/min (free), higher on paid |
| **Max recipients/send** | 1,000 per API call (batch) | Entire list (API manages batching) | 1,000 per batch trigger | 2,000 per API call | 1,000 per API call |
| **Webhook events** | delivered, opened, clicked, bounced, dropped, spam_report, unsubscribe | delivered, opened, clicked, bounced, dropped, marked_as_spam, unsubscribed | delivered, opened, clicked, bounced, failed, unsubscribed | delivered, opened, clicked, hard_bounce, soft_bounce, spam, unsubscribed | delivered, opened, clicked, bounced, dropped, complained, unsubscribed |

### Authentication Methods

| Platform | Auth Method |
|---|---|
| SendGrid | Bearer token (`Authorization: Bearer {API_KEY}`) |
| Klaviyo | API key header (`Authorization: Klaviyo-API-Key {KEY}`) |
| Customer.io | Basic auth (site_id:api_key) for track API; Bearer token for app API |
| Brevo | API key header (`api-key: {KEY}`) |
| Mailgun | Basic auth (`api:{API_KEY}`) |

---

## 4. Google Ads

### Campaign Hierarchy and Fields

| Level | Key Fields | Details |
|---|---|---|
| **Campaign** | `name`, `budget` (daily, in micros: amount x 1,000,000), `bidding_strategy`, `advertising_channel_type` (SEARCH, DISPLAY, SHOPPING, VIDEO, PERFORMANCE_MAX), `geo_target_type_setting`, `language_settings` | Budget in micros: $50/day = 50,000,000 micros. Geo targeting uses criterion IDs (US = 2840). |
| **Ad Group** | `name`, `campaign` (resource name), `type` (SEARCH_STANDARD, DISPLAY_STANDARD, VIDEO), `cpc_bid_micros` (default bid) | Default CPC bid in micros. Overridden by bid strategy at campaign level if automated. |
| **Ad** | `type` (RESPONSIVE_SEARCH_AD, RESPONSIVE_DISPLAY_AD, VIDEO_AD), `final_urls[]`, `path1`, `path2` | See creative specs below. |

### Responsive Search Ad (RSA) Fields

| Field | Count | Max Length | Notes |
|---|---|---|---|
| `headlines` | 3-15 | 30 chars each | At least 3 required. Provide 15 for maximum combinations. Can pin to positions 1, 2, 3. |
| `descriptions` | 2-4 | 90 chars each | At least 2 required. Can pin to positions 1, 2. |
| `final_urls` | 1+ | N/A | Landing page URL(s). First URL is primary. |
| `path1` | 0-1 | 15 chars | Display URL path segment 1 (e.g., "shoes"). |
| `path2` | 0-1 | 15 chars | Display URL path segment 2 (e.g., "running"). |

### Bid Strategies

| Strategy | Use When | Key Parameter |
|---|---|---|
| `MANUAL_CPC` | Full control over bids, limited data | `cpc_bid_micros` per ad group/keyword |
| `TARGET_CPA` | Conversion-focused, 30+ conversions/month | `target_cpa_micros` |
| `TARGET_ROAS` | Revenue-focused, 50+ conversions/month | `target_roas` (percentage, e.g., 300% = 3.0) |
| `MAXIMIZE_CONVERSIONS` | Conversion-focused, spend full budget | Optional `target_cpa_micros` |
| `MAXIMIZE_CONVERSION_VALUE` | Revenue-focused, spend full budget | Optional `target_roas` |
| `MAXIMIZE_CLICKS` | Traffic-focused | Optional `cpc_bid_ceiling_micros` |

---

## 5. Meta Ads (Facebook & Instagram)

### Campaign Structure

| Level | Key Fields | Details |
|---|---|---|
| **Campaign** | `name`, `objective` (OUTCOME_AWARENESS, OUTCOME_TRAFFIC, OUTCOME_ENGAGEMENT, OUTCOME_LEADS, OUTCOME_APP_PROMOTION, OUTCOME_SALES), `special_ad_categories[]` (HOUSING, EMPLOYMENT, CREDIT, NONE), `status` | Objective determines available optimization goals and ad formats. Special Ad Categories restrict targeting options. |
| **Ad Set** | `name`, `campaign_id`, `targeting`, `budget` (`daily_budget` or `lifetime_budget` in cents), `bid_strategy`, `billing_event`, `optimization_goal`, `start_time`, `end_time`, `status` | Budget in cents: $50/day = 5000. Minimum daily budget varies by country ($1-$5 USD). |
| **Ad** | `name`, `adset_id`, `creative` (object), `status` | Creative contains all visual and copy elements. |

### Targeting Object

| Field | Type | Details |
|---|---|---|
| `age_min` | int | 18-65 (minimum 18). Not available in Special Ad Categories. |
| `age_max` | int | 18-65+. Not available in Special Ad Categories. |
| `genders` | array[int] | `[0]` = all, `[1]` = male, `[2]` = female. Not available in Special Ad Categories. |
| `geo_locations` | object | `countries[]`, `regions[]`, `cities[]`, `zips[]`. Radius targeting available. |
| `interests` | array[object] | `[{ "id": "123", "name": "Digital Marketing" }]`. Browse via Interest Search API. |
| `behaviors` | array[object] | Behavioral targeting (purchase behavior, device usage, travel). |
| `custom_audiences` | array[object] | `[{ "id": "audience_id" }]`. CRM lists, website visitors, app users. |
| `excluded_custom_audiences` | array[object] | Audiences to exclude from targeting. |
| `locales` | array[int] | Language targeting by locale ID. |

### Creative Object

| Field | Max Length | Details |
|---|---|---|
| `object_story_spec.link_data.message` | 2,200 chars (125 recommended) | Primary text above the creative. |
| `object_story_spec.link_data.name` | 255 chars (27 recommended) | Headline below the creative. |
| `object_story_spec.link_data.description` | 2,200 chars (27 recommended) | Description below headline (not shown on all placements). |
| `object_story_spec.link_data.link` | URL | Destination URL. |
| `object_story_spec.link_data.call_to_action.type` | enum | SHOP_NOW, LEARN_MORE, SIGN_UP, DOWNLOAD, GET_OFFER, BOOK_TRAVEL, CONTACT_US, APPLY_NOW, SUBSCRIBE, WATCH_MORE, GET_QUOTE, SEND_MESSAGE |
| `object_story_spec.link_data.image_hash` | string | Upload image via Marketing API, use returned hash. |
| `object_story_spec.video_data.video_id` | string | Upload video via Marketing API, use returned ID. |

---

## 6. LinkedIn Ads

### Campaign Structure

| Level | Key Fields | Details |
|---|---|---|
| **Campaign Group** | `name`, `status`, `total_budget` (optional cap), `start_date`, `end_date` | Container for related campaigns. |
| **Campaign** | `name`, `campaign_group`, `type` (SPONSORED_CONTENT, MESSAGE_ADS, TEXT_ADS, DYNAMIC_ADS), `objective` (BRAND_AWARENESS, WEBSITE_VISITS, ENGAGEMENT, VIDEO_VIEWS, LEAD_GENERATION, WEBSITE_CONVERSIONS, JOB_APPLICANTS), `daily_budget` (in cents), `bid_strategy`, `audience` | Budget in cents. Minimum daily budget: $10 USD. |
| **Creative** | `campaign`, `type`, `content` (varies by type) | Linked to a campaign. Content structure depends on ad type. |

### Targeting Facets

| Facet | Details |
|---|---|
| `job_titles` | URN list. Specific job titles from LinkedIn taxonomy. |
| `job_functions` | Broad function categories (Marketing, Engineering, Finance, etc.). |
| `seniorities` | Entry, Senior, Manager, Director, VP, CXO, Owner/Partner. |
| `industries` | LinkedIn industry taxonomy (150+ industries). |
| `company_names` | Specific companies by URN. Minimum audience: 300 members. |
| `company_size` | Ranges: 1, 2-10, 11-50, 51-200, 201-500, 501-1000, 1001-5000, 5001-10000, 10001+. |
| `skills` | Member-listed skills. Broad matching. |
| `degrees` | Degree type (Bachelor's, Master's, PhD, etc.). |
| `fields_of_study` | Academic field of study. |
| `member_groups` | LinkedIn Group membership. |
| `locations` | Geographic targeting by country, state, metro area. |

### Sponsored Content — Creative Fields

| Field | Max Length |
|---|---|
| Introductory text | 600 chars (150 recommended for no truncation) |
| Headline | 200 chars (70 recommended) |
| Description | 300 chars (100 recommended) |
| Image | 1200 x 627 px (1.91:1). Also supports 1080x1080 and 1080x1350. Max 5 MB. |
| Video | 3s-30min. 360p-1080p. MP4. Max 200 MB. |

---

## 7. TikTok Ads

### Campaign Structure

| Level | Key Fields | Details |
|---|---|---|
| **Campaign** | `campaign_name`, `objective_type` (REACH, TRAFFIC, VIDEO_VIEWS, LEAD_GENERATION, APP_PROMOTION, WEB_CONVERSIONS, PRODUCT_SALES), `budget_mode` (BUDGET_MODE_DAY, BUDGET_MODE_TOTAL), `budget` | Minimum daily budget: $50 USD (campaign level), $20 USD (ad group level). |
| **Ad Group** | `adgroup_name`, `placement_type` (PLACEMENT_TYPE_AUTOMATIC, PLACEMENT_TYPE_NORMAL), `targeting`, `budget`, `schedule_type`, `bid_type`, `bid_price` | Automatic placement recommended. Manual placement options: TikTok, Pangle, Global App Bundle. |
| **Ad** | `ad_name`, `ad_format` (SINGLE_VIDEO, SINGLE_IMAGE, CAROUSEL, SPARK_ADS), `video_id` or `image_ids[]`, `ad_text`, `call_to_action`, `landing_page_url` | Spark Ads: use `tiktok_item_id` from authorized organic post. |

### Targeting Options

| Field | Details |
|---|---|
| `age_groups` | AGE_13_17, AGE_18_24, AGE_25_34, AGE_35_44, AGE_45_54, AGE_55_100. |
| `genders` | GENDER_MALE, GENDER_FEMALE, GENDER_UNLIMITED. |
| `languages` | ISO 639-1 language codes. |
| `locations` | Country, state/province, city, DMA. |
| `interests` | TikTok interest categories (hierarchical). |
| `behaviors` | Video interaction behaviors, creator interaction, hashtag interaction. |
| `custom_audiences` | Custom audience IDs (CRM upload, website pixel, app events). |
| `lookalike_audiences` | Lookalike audience ID with similarity type (narrow, balanced, broad). |

### Creative Specs

| Field | Spec |
|---|---|
| Video aspect ratio | 9:16 (recommended), 1:1, 16:9 |
| Video duration | 5-60 seconds (9-15 seconds recommended for In-Feed) |
| Video resolution | 720x1280 minimum (1080x1920 recommended) |
| Video format | MP4, MOV, MPEG, AVI |
| Video file size | Max 500 MB |
| Ad text | 1-100 characters (emoji supported) |
| Display name | Max 40 characters |
| Profile image | 50x50 px minimum |

---

## 8. Social Post Specs — Quick Reference

| Platform | Max Chars | Image Size | Video Max Duration | Video Max Size | Hashtags | Link Behavior |
|---|---|---|---|---|---|---|
| **Twitter/X** | 280 (free), 25K (Premium) | 1600x900 or 1080x1080 | 2:20 (free), 4h (Premium) | 512 MB | 1-2 recommended | Auto-shortened (t.co) |
| **Instagram Feed** | 2,200 | 1080x1080 or 1080x1350 | 60s (feed), 90s (Reels) | 4 GB | 5-10 recommended (30 max) | Link in bio only (no clickable links in captions) |
| **LinkedIn** | 3,000 (posts), 125K (articles) | 1200x627 or 1080x1080 | 10 min | 5 GB | 3-5 recommended | Clickable in post (may reduce reach) |
| **TikTok** | 4,000 | N/A (video-first) | 60 min | 10 GB (desktop) | 3-5 recommended | Link in bio; link sticker for 1K+ followers |
| **Facebook** | 63,206 | 1200x630 or 1080x1080 | 240 min | 10 GB | 1-3 recommended | Clickable link preview |
| **YouTube** | Title: 100, Desc: 5,000 | Thumbnail: 1280x720 | 12 hours | 256 GB | N/A (tags: 500 chars total) | Clickable in description |
| **Pinterest** | Desc: 500 | 1000x1500 | 15 min | 2 GB | Not used (keyword-based) | Clickable destination URL per pin |

---

## 9. Twilio SMS/WhatsApp

### SMS Specifications

| Parameter | Value |
|---|---|
| GSM-7 encoding | 160 characters per segment. Characters: A-Z, a-z, 0-9, standard punctuation. |
| Unicode encoding | 70 characters per segment. Triggered by: emojis, non-Latin scripts, special characters. |
| Concatenated SMS | Up to 10 segments (1,600 GSM-7 chars or 700 Unicode chars). Each segment billed separately. |
| MMS media | Max 5 MB per message. Supported: JPEG, PNG, GIF, MP4, MP3. |
| Sender types (US) | Toll-free (verified), short code (high throughput, $500-$1,000/month), 10DLC (registered, $2-$15/month A2P fee). |
| Sender types (International) | Alphanumeric sender ID (11 chars, e.g., "ACME" — not available in US/Canada). |
| Throughput | Toll-free: 40 MPS. Short code: 100+ MPS. 10DLC: 1-75 MPS (based on trust score). |
| Required content | Opt-out instructions in every marketing message: "Reply STOP to unsubscribe" or equivalent. |
| Quiet hours | No sends 9 PM-8 AM recipient local time (industry best practice; some states legally mandate). |

### WhatsApp Business API

| Parameter | Value |
|---|---|
| Message types | Template messages (pre-approved, for initiating conversations) and session messages (within 24h window after user message). |
| Template approval | Submit via Meta Business Manager. Review: 24-48 hours. Categories: MARKETING, UTILITY, AUTHENTICATION. |
| Template variables | `{{1}}`, `{{2}}`, etc. Positional placeholders. Up to 10 per template. |
| Text message limit | 1,024 characters. |
| Media types | Image (5 MB), Video (16 MB), Document (100 MB), Audio (16 MB), Sticker (100 KB static, 500 KB animated). |
| Interactive messages | Buttons (up to 3 quick-reply buttons, 20 chars each) or lists (up to 10 items in up to 10 sections). |
| Conversation pricing | Meta charges per 24-hour conversation window. Rates vary by country and conversation category. Marketing conversations: ~$0.02-$0.08 USD (varies by country). |
| Quality rating | Green (high), Yellow (medium), Red (low). Low quality = reduced throughput or template rejection. Maintain by keeping opt-out and block rates low. |
| Opt-out requirement | Must provide opt-out mechanism. High block rates trigger quality rating drops. Honor opt-outs within 24 hours. |
