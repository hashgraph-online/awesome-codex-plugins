# EU Code of Practice on AI-Generated Content — context for marketing teams

**Status as of 29 July 2026:** the European AI Office published the **FINAL Code of Practice on Transparency of AI-Generated Content on 10 June 2026** — ahead of the **2 August 2026** applicability date for **AI Act Article 50 transparency obligations**. The Commission has confirmed the Code as an **"adequate voluntary tool"** for demonstrating Article 50 compliance, and has also adopted its **final Guidelines on Article 50**. The final Code is now the operative reference (superseding the 5 March 2026 second draft). The **initial-signatory window closed 22 July 2026**; late signing remains possible. (Re-verify this status line at each release.)

Sources: [Code of Practice on Transparency of AI-Generated Content — official page](https://digital-strategy.ec.europa.eu/en/policies/code-practice-ai-generated-content) · [final Code PDF](https://ec.europa.eu/newsroom/dae/redirection/document/129555) (10 June 2026).

This document is the canonical reference for any DMP skill that produces, validates, or distributes AI-generated marketing content into EU markets.

### July 2026 verification notes (re-check before each release)

- **Final EU Code of Practice** — ✅ PUBLISHED 10 June 2026. Citations in this doc now point at the final text. The **initial-signatory window closed 22 July 2026** (late signing remains possible); one time-sensitive obligation remains: Article 50 obligations **apply from 2 August 2026**.
- **Standardized EU disclosure icons** — ✅ published with the final Code. Use the official EU icons for visible AI-generation labels on EU-targeted assets; source them from the final Code annex rather than recreating them.
- **FTC endorsement guidance (May 2026)** — the US FTC's updated endorsement/testimonial guidance covers AI-generated testimonials and synthetic-creator content. Verify the current text against ftc.gov and fold specifics into `skills/influencer-creator/ftc-compliance.md` and `skills/c2pa-metadata/SKILL.md`.
- **New York synthetic-performer disclosure law (effective June 2026)** — applies to synthetic influencers and AI-generated endorsements ($1K–$5K per violation, $10K repeat). Verify scope/effective date against a primary source before relying on the figures.

## What Article 50 actually requires

Two distinct obligations:

1. **Providers** of generative AI systems (the model builders — OpenAI, Anthropic, Google, etc.) must ensure outputs are marked in a **machine-readable format** detectable as AI-generated. The mark must be implemented "in the design of the AI system" and be "effective, interoperable, robust and reliable as far as technically feasible."
2. **Deployers** (the marketing teams, agencies, and platforms using those systems to produce content) must **disclose** that the content is AI-generated when:
   - It is a **deep fake** (image, audio, or video that appreciably resembles real persons, objects, places, etc.) — disclosure is mandatory, with an exception for editorial/artistic expression where the disclosure must not hamper the work.
   - It is **AI-generated text published to inform the public on matters of public interest** — unless the content has undergone human editorial review with editorial responsibility for publication.

Penalty for non-compliance: up to **€15 million or 3% of total worldwide annual turnover**, whichever is higher.

## What the final Code requires

The final Code (10 June 2026) carries forward the second draft's structure with the requirements now settled:

### Section 1 — Providers
The final Code consolidates provider obligations around **two-layered marking**:

| Layer | Required? | Mechanism |
|---|---|---|
| **Secured metadata** | Required | C2PA-style content credentials embedded in the file (PNG, JPEG, MP4, WAV, OGG, PDF, DOCX, EXIF on raw images, etc.) |
| **Watermarking** | Required | Robust signal embedded in pixels / audio samples / token distributions that survives compression, screenshotting, format conversion |
| Fingerprinting | Optional | Perceptual hash registered in a detection database; useful when the marked file is re-encoded or transformed |
| Logging | Optional | Provider-side log of generated content for downstream takedown / verification requests |

The final Code also requires **detection and verification protocols** so a deployer or platform can programmatically verify a mark is present.

The Code explicitly supports **open standards** to keep compliance costs low — **C2PA satisfies the secured-metadata layer**.

### Section 2 — Deployers
Carried over from the second draft into the final text: **the prior taxonomy distinguishing AI-generated content from AI-assisted content is dropped**. The approach focuses on:

| What | Disclosure requirement |
|---|---|
| **Deepfakes** (images/audio/video resembling real persons, objects, places) | Visible icon / label / disclaimer required. Design and placement specifications in the Code annex. **The standardized EU icons are published with the final Code — use them.** |
| **Text publications on matters of public interest** | Disclosure required UNLESS human editorial review with editorial responsibility was applied |
| **Artistic, creative, satirical, fictional, or editorially-controlled content** | Simplified / reduced requirements — disclosure must not hamper the work |

The Section 2 changes mean DMP no longer needs to maintain a "AI-generated vs AI-assisted" classifier on every output. Every AI-touched asset that meets the deepfake or public-interest-text criteria carries the same disclosure obligation.

Source: [final Code of Practice (EU Commission, 10 June 2026)](https://ec.europa.eu/newsroom/dae/redirection/document/129555).

## Voluntary status

The Code is a **voluntary compliance tool** — it does not replace Article 50, it just provides a presumption-of-conformity path for signatories. If you don't sign, you still need to comply with Article 50 via your own mechanism. Marketing teams running multi-brand portfolios should consider signing on behalf of each brand whose target market includes any EU jurisdiction.

## What this means for DMP-generated content

DMP is a **deployer**, not a provider — and the same logic applies to any other AI content tooling in your stack. Article 50 deployer obligations apply when:

- The brand's target market includes any EU jurisdiction (check `brand.profile.json → target_markets` for any of: AT, BE, BG, HR, CY, CZ, DK, EE, FI, FR, DE, GR, HU, IE, IT, LV, LT, LU, MT, NL, PL, PT, RO, SK, SI, ES, SE)
- AND the content is AI-generated (image, video, audio, or text-published-to-inform-public)
- AND the disclosure exception does not apply (no human editorial review with editorial responsibility, or the asset is a deep fake)

### Mandatory disclosure paths used by the plugin

1. **Machine-readable mark** — embed a C2PA manifest with the `c2pa.ai-disclosure` assertion (spec 2.4, April 2026) via `/digital-marketing-pro:c2pa-metadata`. **This satisfies the Section 1 secured-metadata requirement automatically.** Note: the Code Section 1 also requires a watermarking layer — this is a *provider* obligation, but if you're stitching together outputs from multiple providers (e.g., AI-generated images composited in a separate design tool), verify the marks survive your post-processing pipeline.
2. **Visible deepfake disclosure** — for any AI-generated image/video/audio that resembles a real person, place, or object: visible icon/label/disclaimer on the asset OR in the adjacent caption / alt text / publication metadata. DMP's content pipeline auto-adds this when `c2pa_auto_sign: true` is on for the brand and the generator emitted `ai-claim: ai-generated-content`. **Anticipate the standardized EU icon** — the standardized EU disclosure icons shipped in the final Code annex (10 June 2026), DMP will adopt the standardized EU disclosure icon from the annex.
3. **Editorial-review proof for AI-generated text** — if you're publishing long-form AI-written articles to inform the public on matters of public interest, the editorial-review exception applies only if a human editor signed off with editorial responsibility. Your documented review records (the quality-assurance agent's logged evals, reviewer scorecards, sign-off notes) serve as evidence; **archive them for at least 3 years** (typical regulatory retention).

## The final Code is published — signatory decision and adoption

The final Code landed 10 June 2026. What that changes operationally:

- **Signatory decision is now live.** The Commission confirmed the Code as an adequate voluntary tool: signatories gain legal predictability across EU Member States, while non-signatories must demonstrate that their alternative measures meet the standard through individual market-surveillance assessment. The **initial-signatory window closed 22 July 2026** (late signing remains possible). Document the decision in `brand.profile.json → compliance.eu_code_of_practice_signatory: true|false`.
- **Cite the final Code URL** (done throughout this doc) and **use the standardized EU disclosure icons** from the final Code annex for visible labels.
- Adopt the final disclosure-language templates as the AI Office publishes annex updates, and fold vertical-specific samples into `industry-profiles.md` as they appear.

Under the final Code, the C2PA `c2pa.ai-disclosure` + IPTC digital-source-type pairing already shipped by DMP remains the canonical machine-readable mark for the Section 1 secured-metadata layer — C2PA is referenced as satisfying that layer.

## Operational checklist for marketing teams (Aug 2 readiness)

Run this checklist before 2 August 2026 for any brand with EU target markets:

- [ ] `brand.profile.json → target_markets` reviewed; EU jurisdictions identified
- [ ] `c2pa_auto_sign: true` enabled for any brand with EU markets
- [ ] All AI image/video generation paths route through `/digital-marketing-pro:c2pa-metadata` (verify with `/digital-marketing-pro:check`)
- [ ] Visible deepfake disclosure language drafted in EU languages relevant to target markets (DE / FR / IT / ES / NL / PL at minimum for major-EU brands)
- [ ] Editorial-review logs archived for any AI-generated long-form content in `archives/` directory (3+ year retention)
- [ ] Marketing platforms (CMS, social schedulers, email tools) confirmed to preserve C2PA metadata on re-upload (some platforms strip it — verify with `/digital-marketing-pro:c2pa-metadata --verify-roundtrip`)
- [ ] Decide whether brand/parent will sign the Code as a signatory and document in `brand.profile.json` — **initial-signatory window closed 22 July 2026; late signing remains possible**
- [ ] Replace any placeholder AI-disclosure labels with the standardized EU icons from the final Code annex

## Related skills

- `skills/c2pa-metadata/SKILL.md` — embed C2PA manifest including 2.4 `c2pa.ai-disclosure` assertion
- `skills/check/SKILL.md` — pre-publish gate, includes EU-market compliance check
- `skills/context-engine/compliance-rules.md` — jurisdiction-specific compliance rules (16+ privacy laws, AI labelling rules, advertising standards)
- `skills/context-engine/industry-profiles.md` — industry-specific transparency expectations

## Primary references

- [FINAL Code of Practice on Transparency of AI-Generated Content (10 June 2026) — PDF](https://ec.europa.eu/newsroom/dae/redirection/document/129555)
- [EU Digital Strategy — Code of Practice for AI-generated content (official overview page + signatory form)](https://digital-strategy.ec.europa.eu/en/policies/code-practice-ai-generated-content)
- [EU AI Act Article 50 (Regulation (EU) 2024/1689)](https://artificialintelligenceact.eu/article/50/)
- [C2PA Specification 2.4 (April 2026)](https://spec.c2pa.org/specifications/specifications/2.4/specs/C2PA_Specification.html) — `c2pa.ai-disclosure` assertion definition
- Historical: [second draft (5 March 2026)](https://digital-strategy.ec.europa.eu/en/library/commission-publishes-second-draft-code-practice-marking-and-labelling-ai-generated-content) — superseded by the final Code
