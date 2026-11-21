# Apple App Store: Official Specs & Guidelines

Compiled from developer.apple.com in March 2026 and re-checked against current
secondary coverage on 2026-10-23 (Apple pages could not be fetched directly in
that check). Confirm any limit in App Store Connect before shipping metadata.

## Character Limits

| Field                   | Limit            | Indexed for Search?      | Notes                                                    |
| ----------------------- | ---------------- | ------------------------ | -------------------------------------------------------- |
| App Name                | 30 chars (min 2) | Yes                      | Must be unique; no trademarks, competitor names, pricing |
| Subtitle                | 30 chars         | Yes                      | No unverifiable claims                                   |
| Keywords                | 100 bytes        | Yes (hidden)             | Commas, no spaces between terms                          |
| Description             | 4,000 chars      | **No**                   | Plain text only, no HTML                                 |
| Promotional Text        | 170 chars        | **No** (Apple confirmed) | Updatable without new version                            |
| What's New              | 4,000 chars      | No                       | Required for all versions after first                    |
| IAP Name                | 35 chars         | Yes                      | Appears in search                                        |
| IAP Description         | 55 chars         | No                       |                                                          |
| In-App Event Name       | 30 chars         | Yes                      | Title case required                                      |
| In-App Event Short Desc | 50 chars         | Yes                      | Sentence case                                            |
| In-App Event Long Desc  | 120 chars        | No                       | Sentence case                                            |

**Keywords field is 100 bytes, not 100 characters.** Non-Latin scripts (Arabic,
Chinese, Japanese, Korean) use 2-3 bytes per character, reducing effective
keyword count significantly.

## Screenshot Specs

| Device           | Required?     | Count | Dimensions (portrait)      |
| ---------------- | ------------- | ----- | -------------------------- |
| 6.9" iPhone      | **Required**  | 1-10  | 1260 x 2736                |
| 13" iPad         | **Required**  | 1-10  | 2064 x 2752                |
| Mac              | If applicable | 1-10  | Up to 2880 x 1800 (16:10)  |
| Apple Watch      | If applicable | 1-10  | Varies by model            |
| Apple TV         | If applicable | 1-10  | 1920 x 1080 or 3840 x 2160 |
| Apple Vision Pro | If applicable | 1-10  | 3840 x 2160                |

- Formats: JPEG, PNG
- Apple auto-scales from required base sizes to smaller devices
- **First 3 screenshots** are the ones visible in search results
- **Screenshot caption indexing is not confirmed by Apple.** Some ASO vendors
  reported it in 2025 and at least one has since withdrawn the claim. Write
  captions for conversion in the searcher's words, and treat any ranking effect
  as a hypothesis to test, not a field to optimize.

## App Preview Video Specs

- **Count:** Up to 3 per app
- **Duration:** 15-30 seconds
- **Max file size:** 500 MB
- **Codecs:** H.264 (10-12 Mbps, up to 30fps) or ProRes 422 HQ
- **Audio:** Stereo, 256 kbps AAC or PCM, 44.1/48 kHz
- **Formats:** .mov, .m4v, .mp4
- **Behavior:** Autoplays muted on product page (iOS 11+)

## Custom Product Pages (CPPs)

- **Max:** 70 additional pages (plus 1 default)
- **Customizable:** Screenshots, promotional text, app previews, deep links (iOS 18+)
- **Keywords:** Each keyword combo must be unique to a single CPP
- **Review:** Submitted to App Review independently of app updates
- **Organic search:** CPPs can be assigned keywords and shown in organic search
  results (announced WWDC25, rolled out July 2025; limit raised from 35 to 70 in
  October 2025, per secondary coverage)

## Product Page Optimization (A/B Testing)

- **Treatments:** Up to 3 vs original
- **Testable:** App icons, screenshots, app preview videos
- **NOT testable:** Title, subtitle, description, keywords
- **Concurrent tests:** 1 per app
- **Max duration:** 90 days
- **Icon constraint:** All icon variants must be in the published app binary
- **Confidence:** Apple recommends 90% threshold (Bayesian method)
- **Cannot modify** a test once started

## In-App Events

- **Max approved:** 15 in App Store Connect at once
- **Max published:** 10 on App Store simultaneously
- **Max duration:** 31 days per event
- **Pre-event promotion:** Up to 14 days before start
- **Badge types:** Challenge, Competition, Live Event, Major Update, New Season, Premiere, Special Event

**Event card image:** 16:9, min 1920x1080, max 3840x2160
**Event details image:** 9:16, min 1080x1920, max 2160x3840

**Not suitable:** Repetitive daily tasks, price promotions without new content, general awareness campaigns.

## Ratings & Reviews

- **SKStoreReviewController:** Max 3 prompts per 365-day period
- System controls display frequency (may show fewer than 3)
- Do not use custom buttons to request reviews
- Developers can respond to all reviews in App Store Connect
- Summary rating is territory-specific

## App Store Tags

Announced at WWDC25: Apple generates feature tags for apps with large language
models from app metadata, a human reviews them, and developers can manage or
deselect tags in App Store Connect. Tags surface features buried in the
description, category, and metadata, so clear, specific metadata gives the
model better material. Check App Store Connect for the tags currently attached
and remove any that misdescribe the app.

Source (secondary): https://techcrunch.com/2025/06/11/at-wwdc-apple-says-it-will-use-ai-to-tag-apps-to-improve-discoverability-on-the-app-store

## Editorial Curation

Apple runs human editorial curation (Today tab, category features, collections)
alongside algorithmic ranking. Design quality, screenshot craft, and a coherent
product story therefore carry weight beyond keyword indexing; Google Play has
no equivalent human-curated surface at the same scale.

## Metadata Rejection Triggers (App Review Guidelines)

| Guideline | Rejection Trigger                                                         |
| --------- | ------------------------------------------------------------------------- |
| 2.3.1     | Hidden features, misleading marketing, false pricing                      |
| 2.3.2     | Not disclosing IAPs in description/screenshots                            |
| 2.3.3     | Screenshots that don't show app in use (only splash/login)                |
| 2.3.4     | Preview videos using non-app content                                      |
| 2.3.5     | Wrong category selected                                                   |
| 2.3.7     | Keyword stuffing: trademarks, competitor names, pricing, irrelevant terms |
| 2.3.8     | Metadata not appropriate for all audiences (must be 4+ rated)             |
| 2.3.10    | Other platform names/imagery (Android, etc.) in metadata                  |
| 2.3.12    | Generic What's New for significant changes                                |
| 2.3.13    | Inaccurate in-app event metadata                                          |

Sources: developer.apple.com/app-store/product-page/,
developer.apple.com/app-store/search/,
developer.apple.com/app-store/review/guidelines/
