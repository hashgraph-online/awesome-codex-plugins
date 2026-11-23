# Metric Dictionary

Use this reference before reading or comparing console metrics or vendor benchmarks.

## Apple App Store Connect (App Analytics)

| Metric | Definition | Source |
|---|---|---|
| Impressions | times the app was viewed for more than one second in search results, browse, or on the product page; product page views are included | AppleGrowth-12, AppleGrowth-13 |
| Product page views | times the product page was viewed | AppleGrowth-12 |
| Conversion rate | total downloads and pre-orders divided by unique device impressions | AppleGrowth-13 |
| First-time downloads / redownloads | first download on an Apple account / a later download by the same account | AppleGrowth-12 |
| Source type | App Store Search, App Store Browse, App Referrer, Web Referrer, and others | AppleGrowth-13 |
| Retention | share of downloading devices that used the app on later days | AppleGrowth-13 |
| Custom page, test, and event metrics | shown once a page, treatment, or event reaches five first-time downloads | AppleGrowth-03, AppleGrowth-05, AppleGrowth-14 |
| Product Page Optimization result | Bayesian estimate; "Performing Better" or "Worse" at 90% confidence, otherwise collecting data or likely inconclusive | AppleGrowth-05 |

App Analytics, Sales and Trends, and Payments reports count different things and are not interchangeable (AppleGrowth-11, AppleGrowth-15).

## Google Play Console

| Metric | Definition | Source |
|---|---|---|
| Store listing visitors | unique users who viewed the store listing | PlayQuality-6 |
| Unique clicks | unique users who tapped Install, Open, or Pre-register; the primary store listing metric since June 2026 | PlayQuality-6, PlayListing-30 |
| Click-through rate | share of store listing visitors who clicked; replaced the legacy conversion rate from July 2026 | PlayQuality-6 |
| Acquisitions | installs recorded by Play; moved to Statistics and exports in the 2026 change | PlayQuality-6 |
| Traffic source | Google Play search, Google Play explore, ads and referrals | PlayQuality-6 |
| Peer benchmarks | median and 25th/75th percentiles of a curated group (at least 100 apps) or a custom group (8-12 apps) | PlayQuality-8 |
| User-perceived crash and ANR rate | share of daily active users with a user-perceived crash or ANR, over 28 days | PlayQuality-1 |
| DAU/MAU and user loss rate | core-value metrics with listing-warning thresholds | PlayQuality-1 |
| Experiment metric | unique install, open, or pre-register clicks per variant, with the chosen confidence level and minimum detectable effect | PlayListing-7 |

Never compare a Play conversion or click-through number across the mid-2026 definition change.

## Vendor Benchmarks

- A benchmark is usable only with its vendor, store, country, category, metric definition, and date. Example: one vendor's 2025 US figures were 8.56% App Store page-view-to-install and 16.15% for Google Play, with a category spread from 5.2% to 52.8% (AsoIndustry-26); these predate Play's 2026 metric change.
- Another vendor argues no universal benchmark exists because only the stores hold full data and traffic mix dominates (AsoIndustry-27).
- Subscription apps need three rates: page to install, install to trial, trial to paid; optimizing only the last hides the first two (AsoIndustry-28, AsoIndustry-40).
- Ratings act on outcomes mainly through conversion; no store publishes a star weight in ranking (AsoIndustry-38, AppleMeta-16).

Grade every benchmark `tool` and every console reading `console`.

## Sources

> Checked 2026-11-22.

| Claim | Source |
|---|---|
| Apple metric definitions | AppleGrowth-03, AppleGrowth-05, AppleGrowth-11..15 in [sources.md](sources.md) |
| Play metric definitions and 2026 change | PlayQuality-1, PlayQuality-6, PlayQuality-8, PlayListing-7, PlayListing-30 |
| Benchmarks and their limits | AsoIndustry-26..28, AsoIndustry-38, AsoIndustry-40, AppleMeta-16 |

### Evidence grade

`PRIMARY` for console definitions; benchmarks are `SECONDARY` vendor data.
