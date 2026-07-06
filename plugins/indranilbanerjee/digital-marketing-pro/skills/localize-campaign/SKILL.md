---
name: localize-campaign
description: "Localize campaigns for multiple markets. Use when: translating assets, adapting references, adjusting compliance."
argument-hint: "[target-markets]"
---

# /digital-marketing-pro:localize-campaign

## Purpose

Full campaign localization across multiple target markets. This command takes all campaign assets — emails, ads, social posts, landing pages, video scripts, push notifications — and adapts them for each target market. It goes far beyond translation: cultural references are adjusted, compliance elements are modified per region, SEO is localized, creative recommendations are adapted, and assets are prepared for multilingual publishing.

This is the comprehensive localization workflow for market expansion. Where `/digital-marketing-pro:translate-content` handles a single piece of content, `/digital-marketing-pro:localize-campaign` orchestrates the localization of an entire campaign across multiple markets simultaneously. It coordinates translation service routing per language, transcreation for emotional content, market-specific compliance additions, cultural adaptation based on Hofstede cultural dimensions, localized SEO, RTL formatting for applicable languages, and produces a deployment-ready package per market with quality scores and publishing checklists.

## Input Required

The user must provide (or will be prompted for):

- **Campaign assets**: Content for localization, provided as:
  - File paths per asset type (e.g., "emails: /campaign/email-welcome.html, /campaign/email-follow-up.html; ads: /campaign/fb-ad.txt, /campaign/google-ad.txt; social: /campaign/ig-post.txt")
  - A campaign directory (e.g., "/campaign-q1/") — all files will be categorized by type based on naming conventions or metadata
  - Inline content blocks with asset type labels
- **Target markets**: One or more market codes in language-region format (e.g., hi-IN, de-DE, ja-JP, fr-FR, ar-SA, pt-BR, es-MX). Each code specifies both the language and the cultural/regulatory context
- **Campaign brief or strategy document**: Optional — provides campaign objectives, messaging hierarchy, key themes, and audience segments. Used to inform transcreation decisions and ensure localized versions maintain strategic alignment
- **Market-specific compliance requirements**: Optional — additional regulatory, legal, or industry requirements per market beyond what is already in the brand profile (e.g., "Germany requires Impressum link", "India requires MRP display", "Saudi Arabia prohibits alcohol imagery references")
- **Budget allocation per market**: Optional — if provided, influences prioritization (higher-budget markets get full transcreation and deeper cultural adaptation; lower-budget markets get quality translation with standard adaptation)
- **Priority markets**: Optional — markets to process first and with the most thorough adaptation. Other markets receive standard localization
- **Asset priority**: Optional — which asset types are most important (e.g., "landing pages are highest priority, social posts are secondary"). Affects depth of review and transcreation effort

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Extract full language configuration — `do_not_translate` terms, `translation_preferences`, `locale_formatting` rules per market, approved markets list. Load compliance rules for every target market from `skills/context-engine/compliance-rules.md`. Check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load voice-and-tone rules, messaging hierarchy, channel style guides, and any market-specific brand guidelines. Check for custom templates at `~/.claude-marketing/brands/{slug}/templates/` — localized templates may already exist for some markets. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Inventory all campaign assets**: Enumerate every asset from the provided sources. Categorize each by type (email, ad, social post, landing page, video script, push notification, SMS, blog post). For each asset, analyze the content to classify it as:
   - **Factual/informational**: Product descriptions, specifications, terms, pricing — suitable for direct translation
   - **Emotional/creative**: Headlines, CTAs, slogans, hero copy, storytelling — requires transcreation
   - **Compliance-sensitive**: Disclaimers, consent language, legal text, privacy notices — requires market-specific adaptation
   - **SEO-dependent**: Landing pages, blog posts, meta content — requires localized keyword research
   Report the full inventory to the user: total asset count, breakdown by type, breakdown by content classification, and estimated processing scope per market.
3. **For each target market**, execute the following localization pipeline:
   a. **Route translation service**: Run `python scripts/language-router.py --action route --source "{source_lang}" --target "{market_lang}"` to select the optimal translation service for this language pair. Log the selected service.
   b. **Translate factual content**: Process all factual/informational assets through the routed translation service via the appropriate MCP server (deepl, sarvam-ai, google-cloud-translation, or lara-translate). Pass do-not-translate terms, glossary entries, formality settings, and formatting preservation flags. Score each translation via `python scripts/language-router.py --action score`.
   c. **Transcreate emotional content**: For all emotional/creative assets, apply the transcreation methodology from `skills/context-engine/transcreation-framework.md`. Produce 2-3 creative adaptation options per piece, each with:
      - The adapted content in the target language
      - Back-translation for review
      - Intent-preservation score
      - Cultural fit assessment for this specific market
      - Tone alignment with the original
      Mark the recommended option but preserve all alternatives for client review.
   d. **Adapt cultural elements**: Reference the cultural dimension mapping in `skills/context-engine/multilingual-execution-guide.md` (Hofstede framework) to adapt:
      - **Social proof style**: Testimonials (individualist markets) vs. community endorsements (collectivist markets) vs. authority citations (high power-distance markets)
      - **Urgency tactics**: Direct scarcity (Western markets) vs. relationship-based urgency (Asian markets) vs. group-benefit urgency (collectivist markets)
      - **Trust signals**: Certifications and data (Germanic markets) vs. relationship and reputation (Asian markets) vs. authority endorsement (Middle Eastern markets)
      - **Visual/imagery recommendations**: Color associations, gesture meanings, modesty considerations, seasonal references per market
      - **Humor and tone**: Adjust or remove humor that does not translate culturally; adapt tone to match market expectations for formality
   e. **Localize compliance**: For each market, add or modify:
      - Market-specific disclaimers and legal notices
      - Data consent and privacy language per regional regulation (GDPR for EU, DPDPA for India, PIPA for Japan, LGPD for Brazil, etc.)
      - Industry-specific regulatory statements
      - Required disclosures (pricing, advertising standards, influencer disclosure)
      - User-provided market-specific compliance requirements
      Reference `skills/context-engine/compliance-rules.md` for the regulatory framework per market.
   f. **Localize SEO** (for landing pages, blog posts, and web content): Provide localized keyword suggestions based on the original keyword targets, generate hreflang tag specifications for multi-language site setup, create localized meta titles and meta descriptions, and adapt URL slug recommendations for the target language.
   g. **Adjust formatting**: Apply locale-specific formatting:
      - RTL text direction for Arabic (ar), Hebrew (he), Urdu (ur), Persian (fa) — flag any layout elements that need RTL adaptation
      - Date formats per locale (DD/MM/YYYY vs. MM/DD/YYYY vs. YYYY-MM-DD)
      - Number formatting (decimal separators, thousands separators)
      - Currency symbols and positioning
      - Measurement units (metric vs. imperial)
      - Phone number formats with country codes
      - Address format conventions
4. **Score each localized asset**: Run `python scripts/language-router.py --action score` on every translated/transcreated asset to assess translation quality (length ratio, formatting preservation, key term consistency, placeholder integrity, completeness).
5. **Evaluate localized content quality**: Run `python scripts/eval-runner.py --brand {slug} --action run-quick --text "{localized_content}" --content-type "{type}"` on each localized asset to assess overall content quality in the target language. This catches issues beyond translation accuracy — readability, persuasion, brand alignment in the target language.
6. **Run brand voice check**: Execute `python scripts/brand-voice-scorer.py --brand {slug} --text "{localized_content}"` on key assets (headlines, hero copy, email subject lines) to verify brand voice preservation across languages.
7. **Create per-market delivery package**: For each target market, assemble:
   - All localized assets organized by type
   - Translation quality scores per asset
   - Content quality scores per asset
   - Transcreation options for emotional content (with recommended option marked)
   - Cultural adaptation notes explaining what was changed and why
   - Compliance additions with regulatory references
   - SEO recommendations (keywords, hreflang, meta content)
   - Formatting notes (RTL flags, date/number/currency formats applied)
   - Deployment checklist specific to this market
8. **Generate cross-market consistency report**: Verify that core brand messaging, campaign themes, and value propositions remain consistent across all localized versions. Flag any market where the localized messaging diverges significantly from the campaign strategy. Check that do-not-translate terms are consistently preserved across all markets. Verify that visual/imagery recommendations are consistent where appropriate and diverge where culturally necessary.
9. **Produce localization summary**: Compile the full overview — all markets, all assets, all scores, all flags — into a single summary document with a quality scoreboard (markets as rows, assets as columns, scores in cells) and an overall campaign localization health score.

## Output

A comprehensive campaign localization package containing:

- **Per-market asset package**: For each target market:
  - All localized content organized by asset type (email, ad, social, landing page, etc.)
  - Translation quality score per asset with dimension breakdown
  - Content quality score per asset (eval-runner assessment)
  - Brand voice score for key assets
- **Transcreation options**: For all emotional/creative content across all markets — 2-3 options per piece with back-translations, intent-preservation scores, cultural fit notes, and recommended option marked
- **Cultural adaptation notes**: Per-market summary of what was adapted and why — social proof style, urgency tactics, trust signals, humor adjustments, imagery recommendations, with Hofstede dimension references
- **Compliance additions per market**: Every disclaimer, consent statement, regulatory notice, and required disclosure added for each market, with regulatory references (GDPR Article X, DPDPA Section Y, etc.)
- **Localized SEO recommendations**: Per-market keyword suggestions, hreflang tag specifications, localized meta titles and descriptions, URL slug recommendations
- **RTL and formatting notes**: For applicable markets — RTL layout flags, date/number/currency format specifications, measurement unit conversions, address and phone format conventions
- **Cross-market consistency report**: Verification that brand messaging, campaign themes, and value propositions are coherent across all markets, with flags for significant divergences
- **Quality scoreboard**: Matrix of all markets (rows) by all assets (columns) with translation quality scores, content quality scores, and overall grades — provides an at-a-glance view of campaign localization health
- **Deployment checklist per market**: Market-specific steps for publishing — platform settings, language targeting, geo-targeting, compliance approvals needed, QA review points, go-live sequence
- **Campaign localization health score**: Single aggregate score reflecting overall localization quality, consistency, and completeness across all markets
- **Recommendations**: Priority items for human review (low-scoring assets, culturally sensitive transcreation decisions, compliance items requiring legal sign-off), process improvements for future localization runs, and terms to add to the brand glossary

## Agents Used

- **localization-specialist** -- Manages the end-to-end localization pipeline including translation service routing, transcreation execution, cultural adaptation using Hofstede dimensions, compliance localization, quality scoring, cross-market consistency verification, and per-market package assembly
- **content-creator** -- Generates transcreation options for emotional and creative content, produces culturally adapted headlines and CTAs, creates localized meta descriptions and SEO copy, and ensures marketing effectiveness is preserved across languages
- **execution-coordinator** -- Coordinates the multi-market publishing workflow, manages deployment checklists, sequences go-live across markets and channels, tracks approval status per market, and ensures all compliance sign-offs are obtained before publishing
