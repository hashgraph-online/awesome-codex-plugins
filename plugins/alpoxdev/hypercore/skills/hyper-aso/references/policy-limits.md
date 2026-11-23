# Store Policy Limits

Use this reference before stating any character, byte, size, count, duration, or threshold limit. Every row was read on the official page on the checked date; the source ids resolve to rows in [sources.md](sources.md). Limits change: when a run depends on one for a critical finding, re-open the source and record the new checked date in the run's `sources.md`.

## Contents

- Apple App Store text fields
- Apple App Store assets
- Apple conversion tools
- Apple ratings
- Google Play text fields
- Google Play assets
- Google Play conversion tools
- Google Play ratings and quality
- ONE store (Korea)
- Open conflicts

## Apple App Store Text Fields

Checked 2026-11-22.

| Field | Limit | Search input per Apple | Changes without a new version | Source |
|---|---|---|---|---|
| App name | 2-30 characters | yes | no | AppleMeta-1, AppleMeta-16 |
| Subtitle | 30 characters | yes | no | AppleMeta-1, AppleMeta-16 |
| Keywords | "up to 100 bytes of content", each keyword more than two characters, comma-separated | yes | no | AppleMeta-2 |
| Description | 4,000 characters | not named as an App Store search input; Apple says it is used for web engine search results | no | AppleMeta-2, AppleMeta-9 |
| Promotional text | 170 characters | no; Apple states it does not affect ranking | yes | AppleMeta-2, AppleMeta-15, AppleMeta-16 |
| What's New | 4,000 characters | no | rides the version | AppleMeta-2 |
| Categories | one primary (required) and one optional secondary; primary affects browse placement and is part of text relevance | primary yes | no | AppleMeta-16, AppleMeta-17 |
| Metadata locales | 50 languages | — | — | AppleMeta-5 |
| Propagation | metadata edits can take up to 24 hours to appear | — | — | AppleMeta-9 |

Apple names text relevance (name, subtitle, keywords, primary category) and user behavior (downloads, ratings and reviews) as search factors (AppleMeta-16). The developer name is also searchable (AppleMeta-2).

## Apple App Store Assets

Checked 2026-11-22.

| Asset | Limit | Source |
|---|---|---|
| Screenshots | 1-10 per device size; JPEG or PNG, no alpha; iPhone and (for iPad apps) 13-inch iPad sets required; the first one to three can show in search results | AppleMeta-3, AppleMeta-15 |
| App previews | up to 3 per localization per device size; 15-30 seconds; up to 500 MB; previews play before screenshots | AppleMeta-2, AppleMeta-4 |
| App icon | ships in the app binary, not uploaded as metadata; a change needs a new version | AppleMeta-11 |
| Creative assets (product page header, search, universal) | header 21:9 3840x1646 PNG; search 3:2; universal 16:9 5244x2950 PNG; header video 5-30 seconds | AppleMeta-12 |
| Asset content | relate to the core experience; no prices, discounts, URLs, or unverifiable claims in creative assets | AppleMeta-40 |

## Apple Conversion Tools

Checked 2026-11-22.

| Tool | Limit | Source |
|---|---|---|
| Custom product pages | up to 70 per app (raised from 35 on 2025-10-29); each can carry its own screenshots, previews, promotional text, and assigned keywords; a page appears in search only for assigned keywords once approved and visible; metrics show after five first-time downloads; deep links need iOS/iPadOS 18+ | AppleGrowth-01, AppleGrowth-03, AppleGrowth-31, AppleMeta-29 |
| Product Page Optimization | up to 3 treatments against the original; one test at a time; up to 90 days; icon, screenshots, and previews only; test icons must already be in the live binary at 1024x1024; results at 90% confidence | AppleGrowth-02, AppleGrowth-04, AppleMeta-27, AppleMeta-28 |
| In-App Events | name 30, short description 50, long description 120 characters; up to 10 published at once and 15 approved; publish up to 14 days before start; event length 15 minutes to 31 days | AppleGrowth-06, AppleGrowth-08 |
| Promoted in-app purchases | up to 20 on the product page | AppleGrowth-10, AppleMeta-15 |
| Win-back offers and offer codes | see AppleGrowth-29 and AppleGrowth-30 for the per-subscription and per-quarter caps | AppleGrowth-29, AppleGrowth-30 |
| Featuring nomination | submitted in App Store Connect; Apple asks for at least three weeks' lead time | AppleGrowth-32 |

## Apple Ratings

Checked 2026-11-22.

| Rule | Limit | Source |
|---|---|---|
| In-app rating prompt | the system shows it at most three times in a 365-day period per user; after a rating it can show again only for a new version and after more than 365 days; never shown in TestFlight | AppleMeta-25, AppleMeta-26 |
| Rating reset | only when releasing a new version; irreversible; applies to every storefront at once; written reviews stay | AppleMeta-23 |
| Developer response | one public response per review, editable; can take up to 24 hours to appear | AppleMeta-24 |
| AI review summaries | iOS 18.4+; English summaries in the US and eight further English storefronts, not Korea as of the checked date | AppleMeta-21, KoreaAeo-20 |
| App tags | generated from metadata, AI, and curation; US storefront only as of the checked date | AppleMeta-30, KoreaAeo-19 |

## Google Play Text Fields

Checked 2026-11-22.

| Field | Limit | Source |
|---|---|---|
| App name (title) | 30 characters; no emoji, repeated special characters, ALL CAPS outside a brand, or words such as "free", "#1", "best" | PlayListing-1, PlayListing-2 |
| Short description | 80 characters | PlayListing-1, PlayListing-3 |
| Full description | 4,000 characters | PlayListing-1 |
| Character counting | limits apply to full-width and half-width characters alike | Play Console Help answer 9859152 (leader check, 2026-11-22) |
| Tags | up to 5 per app; changes can take up to 24 hours | PlayListing-5 |
| Search use | title, description, and category are used to match search intent; icon, title, screenshots, video, description, and links are pre-install quality signals | PlayListing-23, PlayQuality-9 |

## Google Play Assets

Checked 2026-11-22.

| Asset | Limit | Source |
|---|---|---|
| App icon | 512x512 32-bit PNG, sRGB, up to 1,024 KB; Play applies the corner mask and shadow; no rank or Play-program marks | PlayListing-3, PlayListing-4 |
| Feature graphic | 1024x500 JPEG or 24-bit PNG, no alpha | PlayListing-3 |
| Phone screenshots | 2-8; 320-3,840 px per side; up to 8 MB; long side at most 2.3 times the short side | PlayListing-3 |
| Foldable / large screen screenshots | foldable 3-8 at 960-3,840 px; large screen sets as the Console lists them | PlayListing-3, PlayQuality-5 |
| Preview video | one YouTube URL, no playlist or timecode | PlayListing-3 |

## Google Play Conversion Tools

Checked 2026-11-22.

| Tool | Limit | Source |
|---|---|---|
| Custom store listings | up to 50; targets include country, ads traffic, pre-registration, search keywords, and user state | PlayListing-6 |
| Store Listing Experiments | one default graphics experiment or up to five localized experiments at once; up to two variants against the current listing; name 50 characters; stops after six months; the app name is not testable; Google advises at least one week | PlayListing-7, PlayListing-8, PlayListing-35 |
| Promotional content | submit at most 60 days before start; review up to 4 days; time-limited events end within 30 days; tagline 80 characters with the value in the first 40 | PlayListing-19, PlayListing-20 |
| Pre-registration | per country; Google suggests opening it three to six weeks before launch | PlayListing-21, PlayListing-22 |
| Translation | free machine translation into 29 languages; paid human translation in up to 48 | PlayListing-16 |

## Google Play Ratings And Quality

Checked 2026-11-22.

| Rule | Limit | Source |
|---|---|---|
| Public rating | weighted toward recent ratings; total hidden below five ratings; split by country and device type; does not reset per version | PlayListing-10, PlayListing-36 |
| Developer reply | one public reply per review, editable; Reply to Reviews API covers production reviews with comments from the last week, 200 GET per hour and 2,000 POST per day | PlayListing-10, PlayListing-14 |
| In-App Review API | time-bound quota that Google does not publish; calling more than once in less than a month may show nothing; no pre-question, altered card, or CTA | PlayListing-13 |
| Android vitals bad behavior | user-perceived crash rate 1.09% overall or 8% on one device model; user-perceived ANR rate 0.47% overall or 8% on one device model; over the threshold an app can be less discoverable and show a listing warning; 28-day window | PlayQuality-1 (leader check, 2026-11-22) |
| Core value | DAU/MAU below 8% or user loss rate above 5% can trigger a listing warning | PlayQuality-1 |
| Size | warning above 200 MB on mobile data; size growth lowers install success | PlayQuality-10, PlayQuality-11 |
| Reporting change | from June 2026 the primary store listing metric is unique Install/Open/Pre-register clicks; from July 2026 click-through rate replaces the legacy conversion rate | PlayQuality-6, PlayListing-30 (leader check, 2026-11-22) |

## ONE Store (Korea)

Checked 2026-11-22. Applies only when the user names ONE store.

| Field | Limit | Source |
|---|---|---|
| Title | 50 characters | KoreaAeo-1, KoreaAeo-2 |
| One-line description | 100 characters | KoreaAeo-2 |
| Description | 1,300 characters | KoreaAeo-2 |
| Keywords | 1-10 | KoreaAeo-2 |
| Screenshots | 2-8, up to 1 MB, up to 1,300x1,300 px | KoreaAeo-2 |
| Graphic image / icon | 1024x578 / 512x512 | KoreaAeo-2 |
| Package name | entering the Google Play package name improves search accuracy per ONE store | KoreaAeo-3 |

## Open Conflicts

| Topic | Conflict | Handling |
|---|---|---|
| Apple keyword field unit | The App Store Connect reference says "100 bytes"; Apple marketing pages and most vendors say 100 characters; one Korean vendor says Hangul counts one per character | Count UTF-8 bytes as the safe upper bound (Hangul is 3 bytes, so about 33 syllables) and tell the owner to confirm with the App Store Connect counter. Record `미확인/충돌`. (AppleMeta-2, AppleMeta-15, KoreaAeo-13) |
| Screenshot caption indexing on iOS | Vendors claim caption text has been OCR-indexed since 2025; Apple's search page says screenshots do not affect ranking; one vendor test did not reproduce it | Treat captions as conversion copy; any rank effect is `heuristic`. (AppleMeta-32, KoreaAeo-17, KoreaAeo-18, AsoIndustry-15..18) |
| Apple Ads popularity scale | Apple Ads shows popularity as a 1-5 bar; the API and vendors report 5-100; Apple regrouped close variants in October 2025 and October 2026 | Name the scale and date with every popularity value; never compare across a change. (AppleGrowth-21, AsoIndustry-4, AsoIndustry-5, AsoIndustry-42) |
| Google Play release notes length | 500 characters appears only in vendor material | Do not state it as official. (PlayListing-34) |

## Sources

> Checked 2026-11-22.

| Claim | Source |
|---|---|
| Every row above | The ledger rows named in each table, in [sources.md](sources.md); leader re-checks are marked in the row |

### Evidence grade

`PRIMARY` - every limit was read on an Apple, Google, or ONE store page. Vendor rows appear only in Open Conflicts.
