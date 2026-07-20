# EU Code of Practice on AI-Generated Content — context for marketing teams

**Status as of July 2026:** the European Commission's AI Office published the **second draft** of the voluntary **Code of Practice on Marking and Labelling of AI-generated content** on **5 March 2026**; stakeholder feedback closed **30 March 2026**. The final Code had been signalled for June 2026, but **June passed without the final text being confirmed published** — as of early July 2026, treat the **second draft (5 March 2026) as the operative reference** and re-check the AI Office library for the final Code, which is still expected ahead of the **2 August 2026** applicability date for **AI Act Article 50 transparency obligations**. (Re-verify this status line at each release — the timeline is moving.)

Source: [EU Digital Strategy — second draft of the Code of Practice on Marking and Labelling of AI-generated content](https://digital-strategy.ec.europa.eu/en/library/commission-publishes-second-draft-code-practice-marking-and-labelling-ai-generated-content) (5 March 2026).

This document is the canonical reference for any DMP skill that produces, validates, or distributes AI-generated marketing content into EU markets.

### July 2026 verification notes (re-check before each release)

- **Final EU Code of Practice** — not confirmed published as of early July 2026. When it lands, update the citations, adopt the **standardized EU disclosure icon** from the annex, and refresh the disclosure-language templates (see the checklist at the end of this doc).
- **Standardized EU disclosure icon** — the second-draft annex illustrates a proposed icon but it is not yet final. Monitor the annex; do not hard-code an icon asset until the final Code confirms it.
- **FTC endorsement guidance (May 2026)** — the US FTC's updated endorsement/testimonial guidance covers AI-generated testimonials and synthetic-creator content. Verify the current text against ftc.gov and fold specifics into `skills/influencer-creator/ftc-compliance.md` and `skills/c2pa-metadata/SKILL.md`.
- **New York synthetic-performer disclosure law (effective June 2026)** — applies to synthetic influencers and AI-generated endorsements ($1K–$5K per violation, $10K repeat). Verify scope/effective date against a primary source before relying on the figures.

## What Article 50 actually requires

Two distinct obligations:

1. **Providers** of generative AI systems (the model builders — OpenAI, Anthropic, Google, etc.) must ensure outputs are marked in a **machine-readable format** detectable as AI-generated. The mark must be implemented "in the design of the AI system" and be "effective, interoperable, robust and reliable as far as technically feasible."
2. **Deployers** (the marketing teams, agencies, and platforms using those systems to produce content) must **disclose** that the content is AI-generated when:
   - It is a **deep fake** (image, audio, or video that appreciably resembles real persons, objects, places, etc.) — disclosure is mandatory, with an exception for editorial/artistic expression where the disclosure must not hamper the work.
   - It is **AI-generated text published to inform the public on matters of public interest** — unless the content has undergone human editorial review with editorial responsibility for publication.

Penalty for non-compliance: up to **€15 million or 3% of total worldwide annual turnover**, whichever is higher.

## What the second draft adds vs the first

The second draft (5 March 2026) made these material changes from the first draft (released late 2025):

### Section 1 — Providers
The second draft consolidates provider obligations around **two-layered marking**:

| Layer | Required? | Mechanism |
|---|---|---|
| **Secured metadata** | Required | C2PA-style content credentials embedded in the file (PNG, JPEG, MP4, WAV, OGG, PDF, DOCX, EXIF on raw images, etc.) |
| **Watermarking** | Required | Robust signal embedded in pixels / audio samples / token distributions that survives compression, screenshotting, format conversion |
| Fingerprinting | Optional | Perceptual hash registered in a detection database; useful when the marked file is re-encoded or transformed |
| Logging | Optional | Provider-side log of generated content for downstream takedown / verification requests |

The second draft also requires **detection and verification protocols** so a deployer or platform can programmatically verify a mark is present.

The draft explicitly supports **open standards** to keep compliance costs low — **C2PA satisfies the secured-metadata layer**.

### Section 2 — Deployers
The biggest change in the second draft: **the prior taxonomy distinguishing AI-generated content from AI-assisted content has been dropped**. The new approach focuses on:

| What | Disclosure requirement |
|---|---|
| **Deepfakes** (images/audio/video resembling real persons, objects, places) | Visible icon / label / disclaimer required. Design and placement specifications in the Code annex. A proposed standardized EU icon is illustrated in the annex. |
| **Text publications on matters of public interest** | Disclosure required UNLESS human editorial review with editorial responsibility was applied |
| **Artistic, creative, satirical, fictional, or editorially-controlled content** | Simplified / reduced requirements — disclosure must not hamper the work |

The Section 2 changes mean DMP no longer needs to maintain a "AI-generated vs AI-assisted" classifier on every output. Every AI-touched asset that meets the deepfake or public-interest-text criteria carries the same disclosure obligation.

Source: [Section-by-section summary of the second draft (EU Commission)](https://digital-strategy.ec.europa.eu/en/library/commission-publishes-second-draft-code-practice-marking-and-labelling-ai-generated-content).

## Voluntary status

The Code is a **voluntary compliance tool** — it does not replace Article 50, it just provides a presumption-of-conformity path for signatories. If you don't sign, you still need to comply with Article 50 via your own mechanism. Marketing teams running multi-brand portfolios should consider signing on behalf of each brand whose target market includes any EU jurisdiction.

## What this means for DMP-generated content

DMP is a **deployer**, not a provider — and the same logic applies to any other AI content tooling in your stack. Article 50 deployer obligations apply when:

- The brand's target market includes any EU jurisdiction (check `brand.profile.json → target_markets` for any of: AT, BE, BG, HR, CY, CZ, DK, EE, FI, FR, DE, GR, HU, IE, IT, LV, LT, LU, MT, NL, PL, PT, RO, SK, SI, ES, SE)
- AND the content is AI-generated (image, video, audio, or text-published-to-inform-public)
- AND the disclosure exception does not apply (no human editorial review with editorial responsibility, or the asset is a deep fake)

### Mandatory disclosure paths used by the plugin

1. **Machine-readable mark** — embed a C2PA manifest with the `c2pa.ai-disclosure` assertion (spec 2.4, April 2026) via `/digital-marketing-pro:c2pa-metadata`. **This satisfies the Section 1 secured-metadata requirement automatically.** Note: the Code Section 1 also requires a watermarking layer — this is a *provider* obligation, but if you're stitching together outputs from multiple providers (e.g., AI-generated images composited in a separate design tool), verify the marks survive your post-processing pipeline.
2. **Visible deepfake disclosure** — for any AI-generated image/video/audio that resembles a real person, place, or object: visible icon/label/disclaimer on the asset OR in the adjacent caption / alt text / publication metadata. DMP's content pipeline auto-adds this when `c2pa_auto_sign: true` is on for the brand and the generator emitted `ai-claim: ai-generated-content`. **Anticipate the standardized EU icon** — when the final Code publishes (expected mid-2026; as of July 2026 not yet confirmed), DMP will adopt the standardized EU disclosure icon from the annex.
3. **Editorial-review proof for AI-generated text** — if you're publishing long-form AI-written articles to inform the public on matters of public interest, the editorial-review exception applies only if a human editor signed off with editorial responsibility. Your documented review records (the quality-assurance agent's logged evals, reviewer scorecards, sign-off notes) serve as evidence; **archive them for at least 3 years** (typical regulatory retention).

## When the Code is published in final form (expected 2026 — not yet published as of July 2026)

The skills `c2pa-metadata`, `check` (the pre-publish gate), and any future regulatory-compliance skill should be updated to:

- Cite the final Code URL
- Adopt the final standardized EU disclosure icon
- Adopt any final disclosure-language templates the AI Office publishes
- Note the brand's signatory status (if the brand or its parent company signs the Code, document it in `brand.profile.json → compliance.eu_code_of_practice_signatory: true`)
- Update `industry-profiles.md` with vertical-specific disclosure-language samples once the AI Office annex publishes them

Until final publication, the C2PA `c2pa.ai-disclosure` + IPTC digital-source-type pairing already shipped by DMP is the most defensible deployer-side compliance mechanism — both are referenced positively in the Section 1 draft guidance.

## Operational checklist for marketing teams (Aug 2 readiness)

Run this checklist before 2 August 2026 for any brand with EU target markets:

- [ ] `brand.profile.json → target_markets` reviewed; EU jurisdictions identified
- [ ] `c2pa_auto_sign: true` enabled for any brand with EU markets
- [ ] All AI image/video generation paths route through `/digital-marketing-pro:c2pa-metadata` (verify with `/digital-marketing-pro:check`)
- [ ] Visible deepfake disclosure language drafted in EU languages relevant to target markets (DE / FR / IT / ES / NL / PL at minimum for major-EU brands)
- [ ] Editorial-review logs archived for any AI-generated long-form content in `archives/` directory (3+ year retention)
- [ ] Marketing platforms (CMS, social schedulers, email tools) confirmed to preserve C2PA metadata on re-upload (some platforms strip it — verify with `/digital-marketing-pro:c2pa-metadata --verify-roundtrip`)
- [ ] Decide whether brand/parent will sign the Code as a signatory and document in `brand.profile.json`

## Related skills

- `skills/c2pa-metadata/SKILL.md` — embed C2PA manifest including 2.4 `c2pa.ai-disclosure` assertion
- `skills/check/SKILL.md` — pre-publish gate, includes EU-market compliance check
- `skills/context-engine/compliance-rules.md` — jurisdiction-specific compliance rules (16+ privacy laws, AI labelling rules, advertising standards)
- `skills/context-engine/industry-profiles.md` — industry-specific transparency expectations

## Primary references

- [EU Digital Strategy — Commission publishes second draft of Code of Practice on Marking and Labelling of AI-generated content (5 March 2026)](https://digital-strategy.ec.europa.eu/en/library/commission-publishes-second-draft-code-practice-marking-and-labelling-ai-generated-content)
- [EU Digital Strategy — Code of Practice for AI-generated content (overview page)](https://digital-strategy.ec.europa.eu/en/policies/code-practice-ai-generated-content)
- [EU AI Act Article 50 (Regulation (EU) 2024/1689)](https://artificialintelligenceact.eu/article/50/)
- [C2PA Specification 2.4 (April 2026)](https://spec.c2pa.org/specifications/specifications/2.4/specs/C2PA_Specification.html) — `c2pa.ai-disclosure` assertion definition
