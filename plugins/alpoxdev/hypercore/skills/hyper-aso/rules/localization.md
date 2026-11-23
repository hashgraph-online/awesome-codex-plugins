# Localization Checks

**Purpose**: How to assess metadata locales, storefront indexing, Korean-language keywords, and ONE store when they are in scope.

## 1. Locale Inventory

- List every metadata locale per store, its storefront reach, and whether text and assets are localized or fall back to the default language.
- Apple: the App Store supports 50 metadata languages, and each storefront has a default language plus additional languages whose metadata is searchable there; localized keywords are searchable in every storefront that supports that language (AppleMeta-5, AppleMeta-10). Read the storefront table on the official localizations page for the storefronts in scope instead of copying a vendor table, because vendor tables go stale (AsoIndustry-8).
- As of the checked date, Apple lists English (U.K.) as the additional language for the Korea storefront, and Korean among the additional languages for the United States storefront (AppleMeta-5).
- Google Play: listings are localized by language; country targeting is done with custom store listings. Machine translation is free for 29 languages and human translation is paid (PlayListing-15, PlayListing-16).

## 2. Additional-Locale Keyword Capacity (Apple)

- An additional locale searchable in a storefront adds its own name, subtitle, and keyword field to that storefront's text inputs (AppleMeta-10). Vendors describe this as about 160 more indexable characters per locale and report that words do not combine across locales (AsoIndustry-10, AsoIndustry-48); record the no-combination behavior as `tool`.
- Recommend an additional locale only with text that is honest for speakers of that language. Filling a foreign locale with unrelated-language keywords is a known practice that Apple discourages (AsoIndustry-9); grade it a `warning`-level policy risk.

## 3. Korean-Language Keywords

- Byte budget: count Korean keyword-field proposals in UTF-8 bytes until the owner confirms the App Store Connect counter (`references/policy-limits.md`, Open Conflicts).
- Spacing, particles, and variants: Apple and Google do not document whether spaced and unspaced Korean forms (`가계부앱` and `가계부 앱`) or forms with particles match the same query. Track each variant separately and grade any equivalence claim `heuristic` until a rank tracker shows it (KoreaAeo-13).
- Mixed scripts: when users search an English brand or term in Latin script (`todo`, `AI`) or its Hangul spelling (`투두`), list both as candidates and measure each.
- Synonyms: put the highest-demand form in the name or subtitle and other forms in the keyword field (Apple) or the descriptions (Play), without repeating a form.
- AI review summaries and Apple app tags did not cover the Korea storefront as of the checked date (AppleMeta-21, AppleMeta-30); do not recommend optimizing for them there.

## 4. ONE Store (Korea, When Named)

- Use ONE store's own limits (`references/policy-limits.md`); its title allows 50 characters and it has a keyword list of up to ten entries (KoreaAeo-2).
- Enter the Google Play package name; ONE store says it improves search accuracy (KoreaAeo-3).
- Metadata edits apply in real time while binaries and ratings go through review (KoreaAeo-8).
- Market share context: as of October 2025 IGAWorks reported Google Play 70.58%, App Store 21.19%, and ONE store 8.24% of Korean app-market revenue; games skew higher on ONE store (KoreaAeo-9, KoreaAeo-10). Graded `tool`; use only to size the opportunity.

## Sources

> Checked 2026-11-22.

| Claim | Source |
|---|---|
| Apple locales, storefront languages, localized keyword search | AppleMeta-5, AppleMeta-10, AppleMeta-21, AppleMeta-30 in [../references/sources.md](../references/sources.md) |
| Play translation and localized listings | PlayListing-15, PlayListing-16 |
| Cross-localization behavior and its risk | AsoIndustry-8..10, AsoIndustry-48 |
| Korean storefront, ONE store limits, market share | KoreaAeo-2, KoreaAeo-3, KoreaAeo-8..10, KoreaAeo-13 |

### Evidence grade

`PRIMARY` for store rules; Korean variant matching and cross-locale combination are `tool` or `heuristic` as labelled.
