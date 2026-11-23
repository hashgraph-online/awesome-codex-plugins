# Keyword Research

Use this reference before proposing keywords or reading a popularity, volume, or difficulty number.

## Contents

- Process
- Metrics and their limits
- Placement
- Rank tracking
- Change cadence

## Process

1. **Seed**: list the app's core jobs in the user's words, the category vocabulary, the brand, and the terms in the owner's own search data (Apple Ads search-term report, Play Console search terms) when available.
2. **Expand**: add synonyms, singular and plural forms, long-tail phrases of two to four words, competitor-listing vocabulary (never competitor brand names in metadata), and locale-specific spellings (AsoIndustry-1, AsoIndustry-3, AsoIndustry-13).
3. **Filter by relevance first**: keep a term only when a user searching it would want this app. A popular term that does not match the app wastes field space and harms conversion (AsoIndustry-33).
4. **Rank candidates**: order by relevance, then demand, then attainability. Use demand and difficulty only to rank candidates against each other, not as counts (AsoIndustry-29).
5. **Place**: assign each term to one field per store and locale (see Placement), and record the counted length.
6. **Measure**: track ranks per store, country, and device after release, and compare with the owner's impressions and source data (AsoIndustry-14).

A practical candidate pool is thirty to fifty terms before filtering (AsoIndustry-12); this is vendor guidance, not a rule.

## Metrics And Their Limits

| Metric | Origin | How to use it |
|---|---|---|
| Apple Ads search popularity | Apple, shown as a 1-5 relative bar in Apple Ads (AppleGrowth-21); reported on a 5-100 scale through the API and vendor tools (AsoIndustry-4, AsoIndustry-6) | First-party relative demand for the App Store; record the scale and date; Apple changed thresholds and grouped close variants in October 2025 and October 2026, so values across those dates are not comparable (AsoIndustry-5, AsoIndustry-42) |
| Vendor volume or traffic score | Each vendor's own model | Ordinal ranking within one vendor; never cardinal search counts; no vendor receives Apple's real query volume (AsoIndustry-29, AsoIndustry-44) |
| Difficulty or competitiveness | Each vendor's own formula (for example from the strength of the top-ranked apps) | Compare only within one vendor; difficulty is relative to the app's own strength (AsoIndustry-6, AsoIndustry-7, AsoIndustry-30) |
| Google Play popularity | Vendor estimate; Google does not publish keyword volume | Lower confidence than Apple-derived values; one vendor publishes its own error (AsoIndustry-30) |
| Rank | Observed position for a query in one store, country, and device | Personalization and time move it; a single snapshot is weak evidence, and "not ranked" is missing data, not rank zero (AsoIndustry-14, KoreaAeo-35) |

Every keyword row in `results.json.keyword_set` that carries a popularity or difficulty value names its `source`; the gate in `assets/runtime/check-results.jq` rejects a popularity value without one.

## Placement

### Apple App Store

- Strongest terms in the name and subtitle; supporting terms in the keyword field; no word repeated across these three fields (AppleMeta-16, AsoIndustry-11).
- Apple combines words across the name, subtitle, and keyword field into phrases, so single words often cover phrases (AppleMeta-33); this is vendor-described and graded `tool`.
- Keyword field: commas without spaces, no duplicates, no words shorter than three characters, counted in bytes (AppleMeta-2).
- Additional searchable locales add capacity (see `rules/localization.md`).
- Custom product pages can carry assigned keywords for a theme (AppleGrowth-31).

### Google Play

- Strongest terms in the title and short description, then natural use in the full description early and in context (PlayListing-23).
- Repetition is checked as an observation; vendor density targets are `heuristic`, and keyword lists are a policy violation (AsoIndustry-31, PlayListing-1).
- Custom store listings can target search keywords (PlayListing-6).

## Rank Tracking

- Track per store, country, device, and locale, with history (AsoIndustry-14).
- Weight ranks by demand when summarizing visibility, and say which vendor's formula is used (AsoIndustry-47).
- "Not ranked" is missing, not rank zero (KoreaAeo-35).

## Change Cadence

- After a metadata change, wait before judging and before the next change; vendors suggest two to three weeks on the App Store and three to four on Google Play (AsoIndustry-12). Record the wait as `heuristic`.
- Seasonal vocabulary follows the owner's own console history first, then third-party trend data (AsoIndustry-19).

## Sources

> Checked 2026-11-22.

| Claim | Source |
|---|---|
| Process, expansion, candidate pool, cadence | AsoIndustry-1, AsoIndustry-3, AsoIndustry-12, AsoIndustry-13, AsoIndustry-19 in [sources.md](sources.md) |
| Metric origins, scale changes, and limits | AppleGrowth-21, AsoIndustry-4..7, AsoIndustry-29, AsoIndustry-30, AsoIndustry-42, AsoIndustry-44 |
| Placement | AppleMeta-2, AppleMeta-16, AppleMeta-33, AppleGrowth-31, AsoIndustry-11, AsoIndustry-31, PlayListing-1, PlayListing-6, PlayListing-23 |
| Rank tracking | AsoIndustry-14, AsoIndustry-47, KoreaAeo-35 |

### Evidence grade

`SECONDARY` - the process is practitioner method; store rules inside it are `PRIMARY` and cited to Apple or Google.
