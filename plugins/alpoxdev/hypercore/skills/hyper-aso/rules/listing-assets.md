# Listing Asset Checks

**Purpose**: How to assess icons, screenshots, previews, promo videos, and feature graphics on both stores. Exact specifications are in `references/policy-limits.md`.

## 1. What To Collect

- The current asset set per store, device class, and locale, read from the live page (`live`) or the owner's export. Record the storefront and device used.
- Which screenshots appear in search results: on the App Store the first one to three (AppleMeta-15); on Google Play the gallery visible without scrolling on the device class viewed.
- Whether localized assets exist or the default-language set is shown in other locales (AppleMeta-10, PlayListing-15).

## 2. Specification Checks

| Check | Severity when it fails | Grade |
|---|---|---|
| Counts, pixel sizes, formats, and durations inside the store limits for every required device class | `critical` when a required set is missing; `warning` otherwise | `official` |
| Apple: previews are captured from the app; screenshots show the app in use | `warning`; guideline risk 2.3.3 | `official` (AppleMeta-18) |
| No prices, discounts, rank claims ("#1", "best"), URLs, or unverifiable claims in graphics | `critical` | `official` (AppleMeta-40, PlayListing-1) |
| Google Play icon: square, full-bleed, no rank or Play marks; Play applies the mask and shadow | `warning` | `official` (PlayListing-4) |
| Apple icon ships in the binary; a change needs a version, and test icons must be in the binary for Product Page Optimization | `info` in planning | `official` (AppleMeta-11, AppleMeta-28) |
| Google Play large-screen and foldable sets present when the app supports those devices | `warning`, rising with the April 2027 requirement | `official` (PlayQuality-5) |

## 3. Conversion Judgment

These are `heuristic` judgments; state them as such and prefer a store experiment to settle them.

- The first frames carry the core value in one short caption each, readable at search-result size.
- The sequence follows the main user job, one feature per frame, rather than a feature list on one frame.
- Captions are written in the locale's own language and fit the locale's reading length.
- The icon stays recognizable at small size and differs from the top competitors in the same results.
- Vendor test cases report that changing screenshots moves conversion more than other assets (AppleMeta-37, AppleMeta-38, AsoIndustry-35); treat them as `tool` or `heuristic` case evidence, not a rule.
- Screenshot caption text is conversion copy. Its effect on App Store ranking is disputed; do not score it as a ranking input (AsoIndustry-15..18).

## 4. Experiment Plan

When an asset change is proposed, write it as a test plan:

- Store tool: Product Page Optimization (up to three treatments, up to 90 days) or Store Listing Experiments (up to two variants, default or localized).
- One variable per test; name the hypothesis, the audience or locale, the metric the store reports, and the stop rule.
- Traffic sizing: small apps can detect only large effects within the test window (AsoIndustry-23); say so when the app's traffic is small and propose a bolder variant instead of a micro-change.
- Seasonality and paid campaigns running during the test are recorded as confounders.

## Sources

> Checked 2026-11-22.

| Claim | Source |
|---|---|
| Asset specs, search-result screenshots, guideline and policy rules | AppleMeta-3, AppleMeta-4, AppleMeta-10, AppleMeta-11, AppleMeta-15, AppleMeta-18, AppleMeta-28, AppleMeta-40, PlayListing-1, PlayListing-3, PlayListing-4, PlayListing-15, PlayQuality-5 in [../references/sources.md](../references/sources.md) |
| Vendor conversion cases, caption dispute, power analysis | AppleMeta-37, AppleMeta-38, AsoIndustry-15..18, AsoIndustry-23, AsoIndustry-35 |

### Evidence grade

`PRIMARY` for specification checks; §3 is `heuristic` by design.
