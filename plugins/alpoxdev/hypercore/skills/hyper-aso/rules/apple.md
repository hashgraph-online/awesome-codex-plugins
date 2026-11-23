# Apple App Store Checks

**Purpose**: The checks to run when the Apple App Store is in scope. Limits and their sources are in `references/policy-limits.md`; this file states what to check and how to grade it.

## 1. Search Inputs

- Apple names text relevance (app name, subtitle, keyword field, primary category) and user behavior (downloads, ratings and reviews) as search factors (AppleMeta-16). The developer name is searchable too (AppleMeta-2).
- Score only those fields as text-relevance inputs. The description, promotional text, What's New, and screenshot captions are conversion copy; a claim that one of them affects App Store ranking is `heuristic` at best (AppleMeta-9, AppleMeta-16, AsoIndustry-15..18).
- Custom product pages with assigned keywords are an additional search surface for those keywords (AppleGrowth-31, AppleMeta-29).

## 2. Field Checks

| Check | Finding when it fails | Grade |
|---|---|---|
| Name carries the brand plus at least one descriptive term the target user searches | `warning` when the name is brand-only and the brand has no search demand | `heuristic`, with demand evidence named |
| Name, subtitle, and keyword field do not repeat the same word; Apple combines words across these fields | `warning` for each repeated word, with the bytes or characters it wastes | `official` (AppleMeta-16) |
| Keyword field: comma-separated, no space after commas, no plural or singular duplicates, no app or category name already present, no words shorter than three characters | `warning` per defect | `official` for the field rules, `heuristic` for plural handling (AsoIndustry-11, AppleMeta-33) |
| Keyword field length counted in UTF-8 bytes | `critical` when proposed copy exceeds 100 bytes | `official` (AppleMeta-2); see the open conflict in `references/policy-limits.md` |
| Subtitle states the core benefit or use case rather than repeating the name | `info` or `warning` | `heuristic` |
| Description first lines and promotional text state the value and current offer; promotional text can change without a version | `info` | `heuristic`; editability is `official` (AppleMeta-15) |
| Primary category matches the main function | `warning`; an irrelevant category is a guideline risk | `official` (AppleMeta-17) |

## 3. Conversion Tools

- Custom product pages: count live pages against the limit, check that each has a distinct audience or keyword theme, that assigned keywords are approved, and that ads or links point to them (AppleGrowth-01, AppleGrowth-03).
- Product Page Optimization: check whether a test ran in the last 90 days, what it tested, its result state, and whether test icons are in the binary. A result is a winner only when App Store Connect marks it "Performing Better" (AppleGrowth-02, AppleGrowth-05).
- In-App Events: check event cadence, badge type, card copy limits, and whether events cover the app's real content moments (AppleGrowth-06, AppleGrowth-07, AppleGrowth-09).
- Promoted in-app purchases and subscription offers: check whether purchases are promoted and named for search users (AppleGrowth-10, AppleGrowth-29, AppleGrowth-30).

## 4. Ratings And Reviews

- Read the summary rating and count per storefront in scope; ratings are per territory (AppleMeta-21).
- Rating prompt: check that it uses the system API, fires after a completed positive task, never at launch or onboarding, and never behind a "Do you like the app?" filter; the system caps it at three displays a year (AppleMeta-20, AppleMeta-25).
- Rating reset: recommend it only for a release that fixes the cause of low ratings, and state that it is irreversible and global (AppleMeta-23).
- Responses: check coverage of recent low-star reviews and that responses fit Apple's one-response rule (AppleMeta-24).
- AI review summaries and app tags: note whether they apply to the storefronts in scope; as of the checked date they do not apply to Korea (AppleMeta-21, AppleMeta-30).

## 5. Metadata Policy Risk

Flag, with the guideline number, every element that conflicts with App Review Guidelines 2.3 (accurate metadata), including (AppleMeta-18):

- keyword stuffing in the name or subtitle, or trademarked, competitor, or celebrity terms in any field (2.3.7);
- screenshots that do not show the app in use (2.3.3) or previews with content not captured from the app;
- prices, discounts, URLs, or unverifiable claims in creative assets (AppleMeta-40);
- references to other mobile platforms or to Apple products in a way the guidelines forbid.

This is a discoverability and rejection risk flag. A pass or fail verdict on submission readiness is outside this skill's output.

## 6. Measurement

- App Analytics: impressions, product page views, conversion rate, first-time downloads, redownloads, and source type (App Store Search, App Store Browse, App Referrer, Web Referrer). Read definitions in `references/metrics.md`.
- Custom page, test, and event metrics appear only after five first-time downloads (AppleGrowth-03, AppleGrowth-05).
- Apple Ads search-term reports are first-party demand evidence for keyword choice; they measure paid traffic and are graded `console` only when the owner exports them.

## Sources

> Checked 2026-11-22.

| Claim | Source |
|---|---|
| Search factors, field rules, category, ratings, review prompt, policy sections | AppleMeta-2, AppleMeta-9, AppleMeta-15..18, AppleMeta-20..25, AppleMeta-29, AppleMeta-30, AppleMeta-33, AppleMeta-40 in [../references/sources.md](../references/sources.md) |
| Custom pages, tests, events, promoted purchases, offers | AppleGrowth-01..10, AppleGrowth-29..31 |
| Caption indexing dispute, keyword-field tactics | AsoIndustry-11, AsoIndustry-15..18 |

### Evidence grade

`PRIMARY` for rules taken from Apple pages; vendor-derived checks are labelled `heuristic` in the table.
