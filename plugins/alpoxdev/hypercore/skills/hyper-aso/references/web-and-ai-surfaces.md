# Web And AI Surfaces

Use this reference when web-to-app links or AI assistant recommendations are in scope.

## 1. Web-To-App Links

| Item | What to check | Source |
|---|---|---|
| Apple Universal Links | `https://<domain>/.well-known/apple-app-site-association` is served without a file extension, declares `applinks` for the app, and exists on every subdomain used; the app's associated-domains entitlement lists the domains | AppleGrowth-24, AppleGrowth-25 |
| Smart App Banner | `<meta name="apple-itunes-app" content="app-id=...">` on the pages that should promote the app; `app-argument` optional | AppleGrowth-23 |
| Android App Links | `https://<domain>/.well-known/assetlinks.json` with relation `delegate_permission/common.handle_all_urls` and the signing-certificate fingerprints; with Play App Signing, use the fingerprint the Console shows | PlayQuality-13, PlayQuality-14 |
| Custom page and listing links | Apple custom product page URLs and deep links (iOS/iPadOS 18+); Play custom store listing URLs; campaign parameters on store badges | AppleGrowth-01, PlayListing-6 |
| Retired link services | Firebase Dynamic Links shut down on 2025-08-25 and its links return 404; Google Play Instant stopped accepting apps from December 2025; Firebase App Indexing documentation is no longer served | PlayQuality-15, PlayQuality-21, PlayQuality-24 |

Fetch each file and record the HTTP status, content type, and whether the app identifiers match. A link file that resolves is evidence of configuration, not of install or rank impact. A website's own search visibility is outside this skill's output.

## 2. AI Recommendation Surfaces

| Surface | State as of 2026-11-22 | Source |
|---|---|---|
| Apple App Store app tags | generated from metadata, AI, and curation; US storefront only; the owner can deselect tags | AppleMeta-30, KoreaAeo-19 |
| Apple review summaries | LLM-written, iOS 18.4+; English summaries in the US and eight further storefronts | AppleMeta-21, KoreaAeo-21 |
| Apple Intelligence actions | apps are reachable through declared App Intents schemas, a separate axis from listing metadata | KoreaAeo-23 |
| Google Play Ask Play and Gemini | conversational search and app discovery announced at I/O 2026; Gemini can draft custom store listings from keyword suggestions | KoreaAeo-24 |
| ChatGPT app directory | apps submitted with metadata and test guidance; OpenAI's metadata guide recommends a "Use this when..." description and golden-prompt evaluation | KoreaAeo-25..27 |

What follows from these:

- Listing metadata that names the real use cases in plain words serves store search, AI tags, and assistant answers at once; there is no separate magic field. Grade any AI-surface recommendation `heuristic` unless the store documents it.
- Review text feeds summaries; rating prompt and reply quality matter there too.

## 3. AI Assistant Probe

Run only when the user asks. Record it as `synthetic`:

- a fixed set of open prompts per locale ("best app for X"), engine, model or surface, country, date, and sample size;
- whether the app is named, its order, the alternatives named, and any cited source;
- one run is noise; report only a trend across repeated dated runs (KoreaAeo-29). A probe result is never a rank or install claim, and research finds LLM app recommendations can diverge from store metrics (KoreaAeo-30).

## Sources

> Checked 2026-11-22.

| Claim | Source |
|---|---|
| Link files, banner, custom links, retired services | AppleGrowth-01, AppleGrowth-23..25, PlayListing-6, PlayQuality-13..15, PlayQuality-21, PlayQuality-24 in [sources.md](sources.md) |
| AI surfaces | AppleMeta-21, AppleMeta-30, KoreaAeo-19, KoreaAeo-21, KoreaAeo-23..27 |
| Probe method and limits | KoreaAeo-29, KoreaAeo-30 |

### Evidence grade

`PRIMARY` for link specifications and surface availability; the probe method is `SECONDARY` practitioner and research guidance.
