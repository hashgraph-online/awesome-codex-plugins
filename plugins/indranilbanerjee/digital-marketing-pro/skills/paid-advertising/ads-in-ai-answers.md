# Ads Inside AI Answers — ChatGPT Ads and Google AI Mode

Everything below was checked on **2026-10-04** against the source linked next to it. **Primary** means the platform's own developer docs, help center, or official blog. **Secondary** means trade press or third-party write-ups. Plan only on primary claims and treat secondary ones as unconfirmed until you see them in the ad account.

Never quote CPMs, CPCs, auction mechanics, or audience sizes for these surfaces from memory. Neither platform publishes them in the sources below, so any number would be invented.

---

## 1. ChatGPT Ads as a paid channel

### 1.1 What the developer surface documents (primary)

Source: [developers.openai.com/ads](https://developers.openai.com/ads), checked 2026-10-04.

| Surface | What it does (per OpenAI's docs) | Notes for a plan |
|---|---|---|
| **Advertiser API** | Create and manage campaigns, ad groups, and ads | Same three-level hierarchy as other platforms |
| **Bulk API** | Create and update campaigns, ad groups, and ads in bulk | Use for large catalogs or many ad groups |
| **Measurement Pixel** | Send conversion events from web pages | Browser-side; pair it with the Conversions API |
| **Image Tag** | Send conversion events from HTML without JavaScript | Fallback for pages where scripts can't run |
| **Conversions API** | Server-to-server conversion events | OpenAI calls it "a more reliable tracking source than the pixel alone" ([docs](https://developers.openai.com/ads/conversions-api.md)) |
| **Custom Audiences** | Create, update, and combine customer audiences for targeting and bid adjustments | Customer lists only, with no pixel-built audiences. **Not available in the EEA or Switzerland** ([docs](https://developers.openai.com/ads/custom-audiences.md)) |
| **Product Feeds** | Set up, update, and advertise a product catalog | CSV uploaded over SFTP ([docs](https://developers.openai.com/ads/product-feeds.md)) |
| **Delta Feeds API** | Update availability, titles, and prices for existing variants without re-uploading the catalog | Enabled per ad account ([docs](https://developers.openai.com/ads/delta-feeds.md)) |
| **Hotel Feeds** | Hotel property feeds | **Limited beta** |
| **Reporting API** | Delivery, cost, product, and attributed-conversion metrics | See 1.4 |
| **Insights API** | Aggregated insights across accounts, campaigns, ad groups, ads | Use for roll-ups |

### 1.2 What is secondary-sourced only (label it in every deliverable)

The following come from trade-press reports, not from OpenAI pages we could open:

- launch dates
- the audience (reported as ChatGPT Free and Go users)
- country rollout (reported as 31 European markets on 18 Aug 2026, then Southeast Asia and Taiwan on 23 Sep 2026)
- "Sponsored Agents"

Write them into a plan as *"reported, unverified"*. Before you allocate budget, confirm in the brand's own Ads Manager account that the target countries are available.

### 1.3 Planning

1. **Treat it as a test line, not a core channel.** Fund it from the media plan's contingency reserve. Set a pre-registered success criterion, such as a CPA or ROAS band against the brand's own baseline, before launch.
2. **Tracking comes before spend.** Do not launch until the Pixel and the Conversions API are both live and deduplicating (see 1.4). If you cannot measure the test, don't run it.
3. **Audience reality check.**
   - Custom Audiences only work from first-party customer lists you have the right to use. OpenAI's docs say: "Don't upload broker-sourced data."
   - The docs give **25,000 matched users** as the public planning threshold for inclusion and bid-adjustment audiences. Exclusion-only audiences have no minimum.
   - Custom Audiences are unavailable in the EEA and Switzerland. For EU/CH plans, drop audience-based tactics entirely instead of planning around them.
4. **Product ads.**
   - Campaigns that run off a catalog use `"mode": "product_feed"` and reference the feed ID.
   - Ad groups inherit the feed and can filter it by brand, price range, category, or custom labels.
   - The `product_ad_template` ad type fills in product details with macros such as `{{product.title}}` and `{{product.price}}`.
5. **Compliance.** Before you upload any audience, OpenAI requires you to confirm rights, notices, consents, and legal bases. Run this through `skills/context-engine/compliance-rules.md` for every target market, and get privacy/legal sign-off for the use case as the docs instruct.

### 1.4 Tracking: Pixel in the browser + Conversions API on the server

Source: [Conversions API docs](https://developers.openai.com/ads/conversions-api.md), checked 2026-10-04.

**Send both and deduplicate.**
- Reuse the same value as the API `id` and the pixel `event_id`, with the same Pixel ID and the same `event_name`.
- OpenAI identifies duplicates by Pixel ID + `event_name` + `id`. It keeps the first event received and discards later matches.
- If the `id` values differ, every conversion counts twice.

**Event names the API accepts:**
`appointment_scheduled`, `checkout_started`, `contents_viewed`, `custom`, `items_added`, `lead_created`, `order_created`, `page_viewed`, `registration_completed`, `subscription_created`, `trial_started`, `app_installed`, `app_opened`.

**Hashing.** All PII is SHA-256 hashed after normalization:
- emails: trimmed and lowercased
- phone numbers: 8–15 digits, with formatting and leading zeros removed
- external IDs: trimmed, case preserved
- names: lowercased, with whitespace and ASCII punctuation removed

Geographic values are sent as raw strings. **Never send unhashed PII.**

**Auth.** The Conversions API uses a bearer key that you provision in Ads Manager. Store it in a secret manager, never in a brand file or a skill output.

**View-through attribution** uses a fixed one-day window after an eligible impression. When click-through and view-through both apply, the click wins.

### 1.5 Reporting

Source: [Reporting API docs](https://developers.openai.com/ads/reporting.md), checked 2026-10-04.

- **Metrics:**
  - impressions, clicks, spend, CTR, CPC, CPM
  - goal conversions from clicks plus views within the selected windows
  - cost per action, post-click conversion rate
  - attributed purchases (`order_created`), ROAS
- **Levels and segments:**
  - reports run at account, campaign, ad group, and ad level
  - segment by country, device, and platform
  - compare products by feed ID and item ID
- **Attribution windows:**
  - default is 30 days after a click and 1 day after an impression
  - selectable click windows are 7, 14, or 30 days
  - view attribution can be toggled separately
- **Freshness:**
  - impressions, clicks, and CTR can arrive within minutes
  - spend finalizes later
  - conversions update in daily processing, so recent days will move
- **Limits:**
  - the conversion endpoint returns HTTP 413 above 2,000 summary or event rows
  - hourly delivery data covers about 30 days
  - non-hourly reporting covers the most recent 365 days

**Honest cross-channel comparison:**
- Do not put ChatGPT Ads ROAS next to Google or Meta ROAS until the attribution windows match.
- Report the window next to every conversion number.
- Do not judge the latest 2–3 days of conversions until daily processing has settled.

### 1.6 Feeds

- **Initial catalog.** Upload a UTF-8 CSV over SFTP.
  - Required fields: `item_id`, `title`, `description`, `url`, `brand`, `image_url`, `price`, `availability`, `seller_name`, `seller_url`, `return_policy`, `target_countries`, `store_country`, `is_eligible_search`, `is_eligible_checkout`, `is_ads_eligible`.
  - In the CSV, price is in major units plus a currency code, for example `"79.99 USD"`.
  - Only rows with `is_ads_eligible` = `true` are processed for ads.
- **Changes between uploads.** The Delta Feeds API (`PATCH /feeds/{feed_id}/products`) updates title, price, and availability for **existing** variants.
  - In this API, price is in **minor** units, for example `{"amount": 7999, "currency": "USD"}`.
  - Delta updates cannot add products or create feeds.
  - The docs state no rate limit, so don't invent one.
  - If Delta access is disabled on the account, the docs say to contact the OpenAI account team.
- **Relation to the agentic-commerce product feed.** The ads docs reference the "OpenAI product file schema". They do not say the ads catalog and the agentic-commerce (ACP) feed are one file. Keep `item_id` values stable across both if the brand runs both. `/digital-marketing-pro:agent-readiness-audit` checks the commerce-feed side.

---

## 2. Google AI Mode ads

Source: [blog.google — "A new generation of ads for the AI era of Search"](https://blog.google/products/ads-commerce/google-marketing-live-search-ads/) (20 May 2026), checked 2026-10-04. Primary.

- **There is no separate AI Mode campaign type in the post.** Google recommends building "a strong foundation with AI Max for Search, AI Max for Shopping campaigns and Performance Max" to reach the new ad experiences. In a plan, AI Mode is **inventory reached through those campaign types**, not its own line item.
- **Formats in testing:** "Conversational Discovery ads" and "Highlighted Answers". They appear while people research products in AI Mode.
- **Direct Offers:**
  - The pilot launched in January 2026.
  - It is expanding to promotion bundling, native checkout for Universal Commerce Protocol (UCP) merchants, and travel deals.
  - Google describes these upgrades as "coming soon".
- **Business Agent for leads:** people "Chat" inside the ad instead of filling in a static form. The post dates this to the "coming months". Do not plan it as available until the account shows it.
- **Measurement:** the post gives **no advertiser-specific measurement guidance** for these formats. Do not promise AI-Mode-only reporting in a plan. Report through the parent AI Max / Performance Max campaign, and say that the AI Mode share is not separately documented.
- **Geography:** the post does not specify countries for the new features.

**What this means for setup:**
1. Audit the account's AI Max state first. Search campaigns are auto-upgrading from September 2026; see the "Since August 2026" section of `SKILL.md`.
2. Apply brand guardrails before you open more inventory to AI-generated assets. Use `text_guidelines.term_exclusions` and `messaging_restrictions` (see `google-ads.md`).
3. For Shopping, the feed is the creative.
   - Conversational attributes such as `question_and_answer` help AI matching (per Google, see `/digital-marketing-pro:agent-readiness-audit`).
   - Checkout eligibility needs `native_commerce(checkout_eligibility)` on each product listing.

---

## 3. Pre-spend checklist (both surfaces)

- [ ] Every factual claim in the plan carries its source and its "checked" date. Secondary claims are labeled "reported, unverified".
- [ ] Target countries are confirmed inside the brand's own ad account, not taken from press reports.
- [ ] ChatGPT Ads: Pixel + Conversions API are live, `event_id` = `id` dedup has been tested with one test conversion, and hashing has been verified.
- [ ] Attribution windows are written next to every conversion metric, and cross-channel ROAS is compared only on matched windows.
- [ ] AI Mode: no AI-Mode-only KPI is promised; results are reported at the AI Max / PMax campaign level.
- [ ] Brand compliance rules have been applied to audiences, feeds, and AI-generated asset guardrails.
- [ ] Launching goes through `/digital-marketing-pro:launch-ad-campaign` and its typed approval gate. This file plans; it never spends.
