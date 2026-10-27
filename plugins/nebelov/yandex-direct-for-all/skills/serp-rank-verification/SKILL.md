---
name: serp-rank-verification
description: Use when checking whether a site, page, product, publication, or competitor appears in search results, or when reporting organic search positions, indexing, snippets, SERP blocks, captcha blockers, regions, locales, or rank-readback evidence.
---

# SERP Rank Verification

Use this skill for search-result presence, indexing, and organic position checks.

## Required Readback

A rank claim must record:

1. search engine and host;
2. query exactly as searched;
3. region, locale, language, device or viewport when relevant;
4. date and time;
5. result type counted;
6. target URL or domain matched;
7. whether ads, shopping, maps, snippets, AI blocks, or promo modules were excluded.

Organic position means an organic result only. Ads, shopping blocks, maps, promo widgets, sitelinks, and other modules are not organic rank positions unless the user asked for that module separately.

## Blocker States

Captcha, robot checks, tunnel failures, partial browser navigation, blocked screenshots, missing region control, and failed search access are blocker or partial states. They do not prove absence from search results.

If only indexing is proven, say indexing is proven. Do not turn indexing into ranking, traffic, lead, or revenue proof.

## Evidence Table

Use a compact table for repeat checks:

```tsv
query	engine	region	locale	checked_at	result_type	position	target_url	match_type	excluded_modules	blocker	proof_artifact
```

When access is blocked, keep `position` empty and fill `blocker` with the concrete failure.
