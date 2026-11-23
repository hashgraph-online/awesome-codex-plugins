# Google Play Checks

**Purpose**: The checks to run when Google Play is in scope. Limits and their sources are in `references/policy-limits.md`; this file states what to check and how to grade it.

## 1. Search Inputs And Ranking Signals

- Google names user relevance, quality of the app experience, editorial value, ads, and the Play user experience as ranking factors, and says title, description, and category are used to match search intent (PlayListing-23, PlayQuality-9).
- Play has no hidden keyword field. The title, short description, and full description are the text inputs; the icon, title, screenshots, video, description, and links are pre-install quality signals (PlayListing-23).
- Technical quality is a visibility input: an app over an Android vitals bad-behavior threshold can be less discoverable and show a listing warning (PlayQuality-1, PlayQuality-12).

## 2. Field Checks

| Check | Finding when it fails | Grade |
|---|---|---|
| Title carries the brand plus a descriptive term, within 30 characters, without emoji, repeated symbols, ALL CAPS, or rank and price words | `critical` for a policy word, `warning` for a brand-only title without demand | `official` (PlayListing-2) |
| Short description states the core benefit in plain language within 80 characters | `warning` | `heuristic`; limit `official` |
| Full description covers the main use cases in natural sentences, with the important terms early; no keyword blocks, anonymous testimonials, or rank and price claims | `critical` for a keyword block or rank claim | `official` (PlayListing-1) |
| Term repetition | report a repetition count only as an observation; Google publishes no ideal density | `heuristic` (AsoIndustry-31) |
| Category and up to five tags match the app | `warning` | `official` (PlayListing-5) |

## 3. Conversion Tools

- Custom store listings: count them against the limit and check their targeting (country, search keywords, pre-registration, ads traffic, churned users) and that each has its own message (PlayListing-6).
- Store Listing Experiments: check recent experiments, what they tested, audience share, minimum detectable effect, confidence level, and result state; a variant wins only when the Console reports it; run at least a week to cover weekday patterns (PlayListing-7, PlayListing-8).
- Promotional content (LiveOps): check cadence, type, tagline rules, and the 28-day scorecards when the owner provides them (PlayListing-18..20, PlayListing-28, PlayListing-29).
- Pre-registration for pre-launch apps: per-country setup, optional reward, and a pre-launch custom listing (PlayListing-21, PlayListing-22).

## 4. Ratings And Reviews

- The public rating is weighted toward recent ratings and split by country and device type; it does not reset per version (PlayListing-10, PlayListing-36). Read it per country in scope.
- In-App Review API: check that the flow fires after a completed task, without a pre-question, altered card, or CTA, and expect the hidden quota to suppress repeated calls (PlayListing-13).
- Incentivized ratings, forced pop-ups, and paid or automated reviews violate policy (PlayListing-12, PlayQuality-17).
- Replies: check coverage of recent low-star reviews; Google reports that replying to negative reviews tends to raise that reviewer's rating, graded `official` as Google's own claim, not as a guaranteed effect (PlayListing-37).

## 5. Quality Signals

- With the owner's Android vitals export, compare the user-perceived crash and ANR rates with the bad-behavior thresholds overall and on the worst device model (PlayQuality-1). Without the export, the category is `unknown`.
- Core value: DAU/MAU and user loss rate below their thresholds can trigger a listing warning (PlayQuality-1).
- Large-screen quality: from April 2027 Google requires adaptive quality Tier 3 for publishing and updates and foldable screenshots; flag apps that target phones only (PlayQuality-4, PlayQuality-5).
- Size: record the download size; growth lowers install success, and large downloads show a mobile-data warning (PlayQuality-10, PlayQuality-11).

## 6. Metadata Policy Risk

Flag, with the policy name, every element that conflicts with the Metadata, Deceptive Behavior, or Ratings and Reviews policies (PlayListing-1, PlayListing-2, PlayListing-12, PlayQuality-16): misleading feature claims, imitation of the OS or other apps, rank or price claims in text or graphics, keyword lists, testimonials, and incentivized reviews. This is a risk flag, not a compliance verdict.

## 7. Measurement

- Since June and July 2026 the store listing reports count unique Install, Open, and Pre-register clicks and report click-through rate instead of the legacy conversion rate; never compare a post-change rate with an older conversion rate (PlayQuality-6, PlayListing-30).
- Traffic sources: Google Play search, Google Play explore, and ads and referrals (PlayQuality-6).
- Peer benchmarks are medians and percentiles of a curated or custom peer group; record which (PlayQuality-8).
- Google Ads App campaigns serve on Play search and browse surfaces, so paid traffic mixes into explore; record whether campaigns ran in the window (PlayQuality-19).

## Sources

> Checked 2026-11-22.

| Claim | Source |
|---|---|
| Ranking factors, field rules, tags, custom listings, experiments, promotional content, pre-registration, ratings | PlayListing-1..2, PlayListing-5..8, PlayListing-10, PlayListing-12, PlayListing-13, PlayListing-18..23, PlayListing-28..30, PlayListing-36, PlayListing-37 in [../references/sources.md](../references/sources.md) |
| Vitals, core value, adaptive quality, size, metric change, benchmarks, App campaigns, deceptive behavior | PlayQuality-1, PlayQuality-4..6, PlayQuality-8..12, PlayQuality-16, PlayQuality-17, PlayQuality-19 |
| Density as a vendor heuristic | AsoIndustry-31 |

### Evidence grade

`PRIMARY` for rules taken from Google pages; vendor-derived checks are labelled `heuristic` in the table.
