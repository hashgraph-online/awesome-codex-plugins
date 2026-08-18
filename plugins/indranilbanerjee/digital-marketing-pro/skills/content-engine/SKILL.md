---
name: content-engine
description: "Draft marketing content in brand voice — blog posts, ad copy, email sequences, social posts, landing pages, and brand-voice guides — through a gated pipeline (research, outline, draft, fact-check, humanize, voice check, SEO checklist) with numbered working files and a five-gate quality scorecard before copy is publish-ready. Triggers on \"/digital-marketing-pro:content-engine\", \"write a blog post about X\", \"draft ad copy for this campaign\", \"create an email sequence\", \"landing page copy for our product\". Takes /digital-marketing-pro:content-brief as preferred upstream; hands off to /digital-marketing-pro:publish-blog, /digital-marketing-pro:content-repurpose, and /digital-marketing-pro:check. Reads the brand profile, guidelines, platform specs, and compliance rules."
argument-hint: "[content-type and topic]"
---

# Content Engine

## When to Use This Skill

Activate this module when the user's request involves any of the following:

- **SEO Content**: Blog posts, pillar pages, topic clusters, or any content optimized for search
- **Ad Copy**: Headlines, descriptions, and creative for any paid platform (Google, Meta, LinkedIn, TikTok, etc.)
- **Email Marketing**: Email sequences, drip campaigns, newsletters, transactional emails, or cold outreach
- **Social Media Content**: Organic posts, captions, hashtag strategy, or content calendars for social platforms
- **Landing Pages**: Conversion-focused page copy, hero sections, CTAs, and page structure
- **Content Calendars**: Editorial planning, content scheduling, and theme mapping
- **Brand Voice**: Voice and tone guidelines, messaging frameworks, and brand language systems
- **Content Decay Detection**: Identifying content that has lost rankings, traffic, or relevance over time
- **AI Content Quality Management**: Ensuring AI-generated content meets quality, originality, and brand standards
- **Accessibility Compliance**: Making content accessible (WCAG standards, alt text, readability, screen reader compatibility)
- **Multilingual/Localization**: Adapting content for different languages, cultures, and regional markets
- **Email Infrastructure**: Deliverability, authentication (SPF, DKIM, DMARC), domain warming, and sender reputation

**Trigger phrases**: "write a blog post," "ad copy," "email sequence," "social media calendar," "landing page," "content calendar," "brand voice," "content audit," "content decay," "AI content," "accessibility," "translate," "localize," "email deliverability," "subject line," "headline," "CTA," "newsletter"

## Brand Context (Auto-Applied)

Before producing any marketing output from this module:

1. **Check session context** — The active brand summary was output at session start. Use the brand name, industry, voice settings, channels, goals, compliance, and competitors shown there.
2. **If you need the full profile**, read: `~/.claude-marketing/brands/{slug}/profile.json`
3. **Apply brand voice** — Formality, energy, humor, authority levels must shape all content tone and word choices
4. **Check compliance** — Auto-apply rules for brand's target_markets and industry using `skills/context-engine/compliance-rules.md`
5. **Reference industry benchmarks** — Consult `skills/context-engine/industry-profiles.md` for the brand's industry
6. **Use platform specs** — Reference `skills/context-engine/platform-specs.md` for character limits and format requirements
7. **Check campaign history** — Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/campaign-tracker.py" --brand {slug} --action list-campaigns` before planning new work
8. **If no brand exists**, say: "No brand profile found. Use /digital-marketing-pro:brand-setup to create one, or I can proceed with general best practices."
9. **Check brand guidelines** — If `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` exists, load and enforce: `restrictions.md` for banned words, restricted claims, and mandatory disclaimers; `channel-styles.md` for channel-specific tone overrides (may differ from base voice); `messaging.md` for approved key messages, taglines, and positioning language; `voice-and-tone.md` for detailed voice rules beyond the 4 numeric scores. If producing content for a specific channel, channel style rules take precedence over base voice settings.

Do not ask the user for information that already exists in their brand profile.

## Required Context

Before executing content work, gather:

1. **Content Type**: Which specific content format is needed?
2. **Audience**: Who is this content for? (Link to personas from Audience Intelligence if available)
3. **Objective**: What should this content achieve? (Traffic, conversions, engagement, education, retention)
4. **Brand Voice**: Does a brand voice guide exist? What is the tone? (Professional, casual, authoritative, playful, etc.)
5. **Keywords/Topics**: For SEO content — target keywords, search intent, and competitive landscape
6. **Platform**: Where will this content live? (Platform-specific requirements matter)
7. **Funnel Stage**: Where does this content fit in the customer journey?
8. **Existing Content**: What related content already exists? (Avoid cannibalization)
9. **Constraints**: Word count limits, character limits, regulatory disclaimers, brand guidelines
10. **Performance Benchmarks**: What does success look like for this content type?

For quick requests (e.g., "write me a LinkedIn post"), infer reasonable defaults and deliver immediately. For strategic content work, gather full context.

## Capabilities

- **SEO Content Creation**: Keyword-optimized blog posts, pillar pages, topic cluster design, meta titles/descriptions, internal linking strategy, and featured snippet optimization
- **Ad Copy (All Platforms)**: Google Ads (RSAs, headlines, descriptions), Meta Ads (primary text, headlines, descriptions), LinkedIn Ads, TikTok Ads, Twitter/X Ads — platform-specific formats and character limits
- **Email Sequences**: Welcome sequences, nurture drips, cart abandonment, re-engagement, onboarding, upsell/cross-sell, and win-back sequences with subject lines, preview text, body copy, and CTAs
- **Social Content**: Platform-native content for LinkedIn, Twitter/X, Instagram, TikTok, Facebook, YouTube, Pinterest — including captions, hashtags, hooks, and post structure
- **Landing Page Copy**: Hero headline/subhead, value proposition blocks, social proof, feature/benefit sections, FAQ, and CTA optimization
- **Content Calendars**: Editorial calendars with theme mapping, content pillars, publishing cadence, and channel distribution plans
- **Brand Voice System**: Voice attributes, tone spectrum (how voice adapts by context), vocabulary guidelines, do/don't examples, and brand-specific terminology
- **Content Decay Detection**: Methodology for identifying declining content by traffic, rankings, engagement, and freshness — with refresh prioritization
- **AI Content Quality Management**: Quality checklist for AI-generated content, originality verification approach, brand alignment review, fact-checking protocol, and human-in-the-loop guidelines
- **Accessibility Compliance**: WCAG 2.2 AA content guidelines, alt text writing, readability scoring, heading structure, link text, color contrast guidance, and screen reader optimization
- **Multilingual/Localization**: Translation-ready content structuring, cultural adaptation framework, locale-specific messaging guidelines, and RTL language considerations
- **Email Infrastructure**: SPF/DKIM/DMARC setup guidance, domain warming schedules, list hygiene practices, deliverability monitoring, and sender reputation management

## Process

**Primary Workflow: Content Creation**

1. **Content Strategy Alignment**
   - Confirm the content type, audience, objective, and funnel stage
   - Check for existing content that may overlap (prevent cannibalization)
   - Identify the core message and key takeaway
   - Select the appropriate content framework for the task

2. **Research & Preparation**
   - For SEO content: Analyze target keyword, search intent, SERP features, and top-ranking content
   - For ad copy: Review platform specs, competitor ads, and audience pain points
   - For email: Identify the sequence trigger, desired action, and subscriber segment
   - For social: Check platform trends, optimal formats, and audience behavior patterns
   - For landing pages: Identify the traffic source, visitor intent, and conversion goal

3. **Content Creation**
   - Apply the brand voice guidelines (or establish them if none exist)
   - Write to the specific format requirements (character limits, structure, platform norms)
   - Build in persuasion architecture:
     - **Attention**: Hook/headline that stops the scroll or earns the click
     - **Interest**: Problem-aware framing that demonstrates understanding
     - **Desire**: Solution positioning with clear benefits and social proof
     - **Action**: Clear, specific CTA with reduced friction
   - Include SEO elements where applicable (keywords, headers, internal links, meta data)
   - Write multiple variations for testing when the format supports it (ad copy, subject lines, CTAs)

4. **Quality Assurance**
   - Brand voice alignment check
   - Readability score assessment (aim for grade 8 or below for general audiences). Run the analyzer on the draft:
     ```bash
     python "${CLAUDE_PLUGIN_ROOT}/scripts/readability-analyzer.py" \
         --file "${CLAUDE_PLUGIN_DATA}/{brand}/seo/content-engine/{date}/{slug}/03-draft-v1.md" \
         --target b2c_general
     ```
     (`--text` inline or `--file` path — mutually exclusive, one required; `--target` one of `b2c_general`, `b2b_professional`, `b2b_technical`, `children`, `academic`.)
   - Accessibility review (heading hierarchy, alt text guidance, link text clarity)
   - Fact-checking for any claims, statistics, or references
   - Platform compliance check (ad policies, character limits, format requirements)
   - SEO on-page audit (keyword placement, meta data, internal links) for search content
   - AI content quality check if AI-assisted (originality, brand alignment, factual accuracy)

5. **Optimization & Testing Plan**
   - Define what to A/B test (headlines, CTAs, email subject lines, ad creative)
   - Set performance benchmarks based on content type and channel
   - Schedule content review dates for decay monitoring
   - Plan content repurposing across formats and channels

**Secondary Workflow: Content Audit & Refresh**

1. Pull content inventory (URLs, publish dates, current traffic/rankings)
2. Score each piece on freshness, performance trend, and relevance
3. Categorize: Keep (performing well), Refresh (declining but fixable), Consolidate (thin/overlapping), Remove (irrelevant/harmful)
4. Prioritize refresh candidates by traffic recovery potential
5. Create refresh briefs with specific update instructions

## Reference Files

- `seo-content.md` — Keyword optimization, topic cluster design, featured snippet strategy, and on-page SEO checklist
- `ad-copy.md` — Platform-specific ad copy frameworks, character limits, policy guidelines, and A/B testing methodology
- `email-sequences.md` — Sequence templates (welcome, nurture, abandonment, etc.), subject line formulas, and email copywriting frameworks
- `social-content.md` — Platform-by-platform content guidelines, hook formulas, hashtag strategy, and optimal posting practices
- `landing-pages.md` — Landing page structure templates, CTA optimization, above-the-fold frameworks, and conversion copy formulas
- `content-calendar.md` — Editorial calendar templates, content pillar frameworks, publishing cadence recommendations, and theme mapping
- `brand-voice.md` — Voice development methodology, tone spectrum design, vocabulary guidelines, and brand voice audit process
- `content-decay.md` — Decay detection methodology, content scoring rubric, refresh prioritization framework, and update tracking
- `ai-content-quality.md` — AI content quality checklist, originality verification, brand alignment review, and human review workflow
- `accessibility.md` — WCAG 2.2 AA content checklist, alt text writing guide, readability standards, and inclusive language guidelines
- `multilingual.md` — Localization readiness checklist, cultural adaptation framework, translation management, and RTL considerations
- `email-infrastructure.md` — Authentication setup (SPF/DKIM/DMARC), domain warming plan, deliverability best practices, and list hygiene
- `email-automation.md` — Automation trigger design, workflow mapping, dynamic content rules, and behavioral email logic
- `case-studies.md` — Challenge-Solution-Results framework, customer-hero narrative structure, and case study creation best practices
- `personalization.md` — Personalization maturity model, segment/rule-based/behavioral strategies, and implementation guidance
- `video-scripting.md` — Platform-specific video formats and lengths, script structures, and hook and retention techniques

## Output Formats

| Deliverable | Format | Description |
|---|---|---|
| Blog Post / Article | Document | Complete SEO-optimized content with meta data, headers, and internal link suggestions |
| Ad Copy Set | Document / Spreadsheet | Multiple variations per platform with headlines, descriptions, and CTAs |
| Email Sequence | Document | Full sequence with subject lines, preview text, body copy, CTAs, and send timing |
| Social Media Content | Spreadsheet / Calendar | Posts organized by platform, date, copy, hashtags, and visual direction |
| Landing Page Copy | Document | Section-by-section copy with headline, subhead, body, bullets, CTAs, and form copy |
| Content Calendar | Spreadsheet | Monthly/quarterly editorial plan with themes, topics, formats, channels, and owners |
| Brand Voice Guide | Document | Complete voice system with attributes, tone spectrum, vocabulary, and examples |
| Content Audit Report | Spreadsheet + Document | Inventory with scores, categorization, and prioritized refresh recommendations |
| Accessibility Report | Checklist document | Content-level accessibility assessment with specific remediation steps |

## Edge Cases

### Regulated Industry Content (Disclaimers Required)
- **Situation**: Healthcare, financial services, legal, insurance, cannabis, gambling, or other industries requiring mandatory disclaimers, disclosures, or compliance language
- **Approach**: Flag the regulatory requirement at the start of content creation. Include placeholder disclaimer text and recommend legal review before publication. For ad platforms, note specific policy restrictions (e.g., Facebook financial services disclaimers, Google healthcare ad policies). Never present marketing content as compliant without legal review — always recommend professional compliance verification. Keep marketing copy and compliance language visually distinct.

### Multilingual Campaigns
- **Situation**: Content needs to work across multiple languages and cultural contexts
- **Approach**: Write source content with localization in mind (avoid idioms, cultural references, humor that won't translate). Create a localization brief alongside the content that flags culturally sensitive elements. Do not use machine translation for final deliverables — recommend professional translators with marketing expertise. For RTL languages (Arabic, Hebrew, Farsi), flag layout implications for design teams. Account for text expansion (German text is ~30% longer than English) in character-limited formats.

### Content Cannibalization
- **Situation**: Multiple pages competing for the same keyword or covering the same topic
- **Approach**: Audit existing content before creating anything new. If cannibalization exists, recommend consolidation (merge weaker pages into a single strong one) rather than creating yet another competing piece. Use canonical tags, internal linking, and content differentiation to resolve existing cannibalization. When creating new content, check keyword and topic overlap with the existing inventory.

### AI-Generated Content Disclosure
- **Situation**: User wants to publish AI-generated content and needs guidance on disclosure
- **Approach**: Recommend transparency. Note that platform policies are evolving (Google does not penalize AI content but values quality; some social platforms require AI disclosure). Always recommend human review and editing of AI-generated drafts. Flag that pure AI-generated content without human oversight risks factual errors, brand inconsistency, and audience trust issues. Provide the quality assurance checklist for AI-assisted content.

### Accessibility for Video/Audio Content
- **Situation**: Content includes video, audio, or interactive elements needing accessibility treatment
- **Approach**: Recommend captions (not auto-generated — accuracy matters) for all video content. Provide audio descriptions for visual-only information in videos. Create transcripts for podcasts and audio content. Ensure interactive elements are keyboard-navigable. Test with screen readers. Follow WCAG 2.2 AA at minimum, with AAA as a stretch goal for public-facing content.

### RTL Languages
- **Situation**: Content in Arabic, Hebrew, Farsi, Urdu, or other right-to-left languages
- **Approach**: Flag RTL implications early in the process. Content structure, CTA placement, and visual hierarchy all reverse. Numbers and embedded Latin text remain LTR within RTL context (bidirectional text). Recommend native-speaker review for all RTL content. Design templates must support RTL layouts. Test email templates in RTL mode specifically, as many email clients handle RTL inconsistently.

## Numbered output convention

All content-engine outputs go to `${CLAUDE_PLUGIN_DATA}/{brand}/seo/content-engine/{YYYY-MM-DD}/{slug}/`:

```
00-input.md                topic, target keyword, intent, format, source brief (from keyword-cluster?)
01-research.md             source list, key data points, expert quotes, competitor references
02-outline.md              H1, H2/H3 structure with target word counts per section
03-draft-v1.md             first complete draft
04-fact-check.md           per-claim verification + citations
00-source-draft.md         the author's own words, verbatim (ONLY when --source-draft was given)
05-humanize.md             AI-pattern detection + rewrite log (flags from scripts/ai-tell-scan.py)
05-scans.json              Surface + structural scan output, keyed {"surface":…, "structure":…}
05-authorship.json         author-sentence provenance (ONLY when 00-source-draft.md exists)
06-brand-voice-check.md    voice score (formality/energy/humor/authority) vs brand profile
07-seo-checklist.md        title, meta, schema, internal links, image alt text
08-quality-scorecard.md    the gates below
09-publish-ready.md        final clean copy + handoff metadata
PLAN.md                    summary + publish instructions
```

## Quality scorecard

| Gate | What it checks |
|---|---|
| **brand_voice_match** | `06-brand-voice-check.md` shows **`distance` ≤ 0.15 on each axis** (formality/energy/humor/authority). **The unit is the scorer's 0–1 scale, not the profile's 1–10 scale.** This gate previously read "≤ 1.5 point deviation" while `brand-voice-scorer.py` emits `distance` bounded at 1.0 — so read literally it could never fail, which is the same hollow-gate defect as a gate with no measurement behind it. 0.15 is the threshold the scorer already uses internally to flag a deviation. Note what this does and does not measure: the target axis values come from `brand-setup`'s mapping of voice descriptors to numbers, and there is no rubric for descriptors it has not seen — so a FAIL here is a prompt to check the profile's targets as much as the copy |
| **fact_check_clean** | `04-fact-check.md` shows 0 unverified claims and ≥ 1 citation per factual statement |
| **humanize_passed** | `python "${CLAUDE_PLUGIN_ROOT}/scripts/ai-tell-scan.py" --file 05-humanize.md` reports `humanize_passed: true` — i.e. `flagged_paragraph_pct` ≤ the brand threshold (default 10%). **Run the script; do not judge this by eye.** See "Humanize step" below for what counts as a flag |
| **seo_complete** | `07-seo-checklist.md` shows title ≤ 60 chars, meta 150-160 chars, ≥ 1 schema type, ≥ 3 internal links, all images have alt text. **Two criteria take an explicit `N/A` rather than a pass:** internal links when the brand has no published site (a pre-launch brand's first article cannot link internally to anything — record `N/A (no site)` and the gate ignores it, but never record it as met), and alt text when the piece has no images (0 of 0 is a pass that verifies nothing — record `N/A (no images)`). An `N/A` must name its reason; a bare `N/A` is a FAIL |
| **eu_disclosure_if_ai** | If the brand has `target_markets` including EU AND the content is AI-generated, `09-publish-ready.md` carries the required Article 50 disclosure (machine-readable + visible) |

`status: ready` requires all five gates pass — **and the run audit re-deriving them:**

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/run-audit.py" --run-dir "${CLAUDE_PLUGIN_DATA}/{brand}/seo/content-engine/{date}/{slug}"
```

Run it after writing `08-quality-scorecard.md` and before declaring `status: ready`. It re-derives what the scorecard claims from the artifacts themselves: every numbered artifact present, the humanize verdict re-measured with a fresh `ai-tell-scan.py` run (never read off the scorecard), no scan JSON embedded in the file `authorship.py` measures, the authorship record matching a fresh measurement when a source draft exists, recorded voice distances actually inside the 0.15 gate, and the publish-ready copy free of production placeholders. **Exit 1 means the scorecard is claiming something the artifacts do not support — fix the finding, never the wording.** The verdict lands in `run-audit.json` beside the artifacts, so the next reader can see the run was verified rather than trusted.

## AI-assistance disclosure (all runs, not just EU)

Beyond the EU gate above, every publish-ready draft applies the brand's `ai_disclosure` block from profile.json — `{"mode": "claude-surfaces"|"always"|"off", "text": null|custom, "author": null|name}` (missing block = the default: claude-surfaces, no custom text, no author).

1. Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/detect_surface.py" --mode {mode}` — its `disclosure_applies` field IS the decision. The fail-safe is deliberate: an `uncertain` surface applies the disclosure in claude-surfaces mode (skipping requires an AFFIRMATIVE non-Claude fingerprint). Never override the script's answer by guessing.
2. When it applies, append the block as the final content paragraph of `09-publish-ready.md` — inside the body, so it survives `/digital-marketing-pro:publish-blog` — using: no custom text and no author → `*Created with AI assistance and reviewed by our editorial team.*`; author set → `*Created with AI assistance; researched, fact-checked, and edited by {author}.*`; custom text → verbatim. The default wording is vendor-neutral (no model or vendor names) and claims only the review this pipeline performs. The author field is OPTIONAL — never invent a name, never block on it being blank.
3. Record the decision in the handoff metadata either way: `disclosure: {applied, mode, surface}` — an unapplied disclosure is a recorded choice, not an omission.

## Humanize step (`05-humanize.md`) — what a flag actually is

The `humanize_passed` gate is measured by `scripts/ai-tell-scan.py`, not by impression. Run it and work the flags it returns.

**`05-scans.json` holds BOTH scans under named keys — never two JSON documents in one file.** Write it as `{"surface": {...ai-tell-scan output...}, "structure": {...structural-tell-scan output...}}`. Two `>` redirects into the same path produce a file that `json.load` rejects; a run doing exactly that is how this was found. On Windows, redirect with `PYTHONIOENCODING=utf-8` set — the default cp1252 encodes the em-dash in the advisory note as byte `0x97` and the file then fails to parse.

**Keep `05-humanize.md` to the article body.** `scripts/authorship.py --draft 05-humanize.md` classifies every sentence in that file, so scan JSON or report prose living there is counted as machine-added text against the author's share. Measured on a real run: appending the scan JSON and a short report moved `author_word_share` from 0.253 to 0.206 and flipped `may_claim_authored` from true to false — denying the author credit for work they actually did, on nothing but file layout. Reports go in `05-scans.json`; the draft file stays the draft.

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/ai-tell-scan.py" --file 05-humanize.md [--max-flagged-pct N]
```

**Two tells count toward the gate**, because they are precise enough to gate on:

- **`significance_marker`** — a sentence whose only job is to tell the reader what a neighbouring sentence means: "here's the thing", "that's the part that got me", "which is exactly the problem", "let that sink in". → **DELETE the sentence. Do not reword it.** The specific it points at already does the work; softening a marker into a gentler marker is not a fix. If the moment matters, return to the specific instead of announcing it.
- **`soft_adverb_cluster`** — two or more of honestly / genuinely / truly / literally / actually / basically / quietly in one sentence → delete them. A sentence that needs force needs a specific, not an adverb.

**Everything else the scan reports is advisory context, not gate material** — `llm_favored_word`, connective openers ("So,", "However,"), participial openers, em-dash density, and short ungrounded one-liners. Those appear in ordinary human writing too, and gating on them would fail good copy and spin the pipeline into pointless rewrites. Fix them where the scan is right; do not chase the number.

- **`llm_favored_word`** (advisory since 2026-08-15) — delve, leverage, seamless, tapestry, testament, pivotal, myriad… → still worth fixing: use the plain word you would say out loud, or better, a concrete noun from the piece's own subject. It stopped counting toward the gate after measurement: across 272 chunks of prose published before ChatGPT existed, 23 of these words fired and **every one fired only on the human writing, none on the model writing**. Technical and journalistic English uses "robust", "facilitate" and "leverage" normally, while current models have largely been trained off them — so as a gating signal it could only ever produce false positives.

### What passing this gate does and does not mean

Passing means **no dense cluster of the two precise tells**. It is a floor, not a verdict. Measured on 39 documents published before ChatGPT existed, the gate failed none of them; measured on 18 documents of unedited model prose, it caught none of them. So a pass is not evidence the piece reads as a person wrote it, and it would not catch a humanize step that did nothing at all. Treat `advisory_rating` and the structural scan as the editor-facing signal — they do separate the two classes (unedited model prose landed HIGH 83% of the time versus 9% for published human prose) — and treat both as a to-do list for a person, never as proof of authorship.

**The fix for any flag is a verified specific from `04-fact-check.md`, never a synonym swap and never an invented fact.** If no grounding exists for a sentence, cut the sentence or add a defensible caveat — do not invent a number, date, source, or example to make prose sound human.

## Bring your own words (`--source-draft`)

When the user supplies their own rough draft — a voice-note transcript, bullets, a stream-of-consciousness dump — save it verbatim as `00-source-draft.md` and build the piece **around their sentences instead of over them**. Do not clean it up on the way in; the mess is the signal.

- Carry their sentences into `03-draft-v1.md` **verbatim** — typos, run-ons, lowercase and all. Never paraphrase, condense, merge, or grammar-fix them; "improving" their voice is what deletes their authorship.
- **The humanize step's tells do not apply to their sentences.** If the author wrote "here's the thing", it stays. A pattern describes what a model writes unprompted, not what a person chose to say.
- Add your material *between* their sentences: the research, the sourced specifics, the structure, the sections they only gestured at.
- **Their claims are their voice, not verified facts.** Anything factual you ADD still comes from `04-fact-check.md`. If one of their claims contradicts the research, flag it for the human editor and leave the sentence alone — they decide, not you.
- After humanizing, verify the promise was kept:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/authorship.py" \
  --source 00-source-draft.md --draft 05-humanize.md --out 05-authorship.json
```

Exit 3 means author sentences were rewritten or dropped. **Restore them verbatim and re-run until it exits 0.** This one is not advisory: every AI-tell scan here stays advisory because a detector signal is a probabilistic opinion, but "the author wrote this sentence and it is no longer here" is a checkable fact about a promise this pipeline made.

- **Provenance-accurate disclosure.** When `05-authorship.json` reports `may_claim_authored: true` — which requires both that ≥25% of the finished words are the author's verbatim AND that none of their sentences were rewritten or dropped — the disclosure in `09-publish-ready.md` becomes `*Written by {author} with AI assistance for research, structure, and fact-checking.*` (or, with no author named, `*Written from the author's own draft, developed with AI assistance and reviewed before publication.*`). Otherwise use the standard wording above. **Never infer authorship from anything but this record.** The direction is one-way by design: an authorship record may only ever make a disclosure MORE specific about human involvement that demonstrably happened. Overclaiming human authorship is the one form of this statement a reader cannot check.
- There is no target ratio. `author_word_share` exists so the disclosure can be accurate; no number makes text "human enough", and nothing here is aimed at a detector.

## Structural-tell pass (advisory, never a gate)

After `05-humanize.md`, run `python "${CLAUDE_PLUGIN_ROOT}/scripts/structural-tell-scan.py" --file {draft}` — the Tier-2 STRUCTURAL layer (StoryScope-derived: AI text stays detectable on structure even after a perfect surface pass). Where it reports NOTE/ATTENTION (moralizing closers, template symmetry, low specificity, stance absence, uniform rhythm, entity development), apply structural edits grounded in the fact-check file: cut the spelled-out takeaway, break symmetry the content doesn't earn, add specific verified facts (never invented), take a defensible stance.

**`entity_development`** deserves its own note because it is easy to fix the wrong way. A NOTE/ATTENTION band means the piece introduces name after name and number after number, each mentioned once and abandoned — a machine establishing a setting rather than an expert making a case. **Fix by developing, never by deleting:** give a specific the argument already rests on a second substantive mention from `04-fact-check.md` — what it implies, who disputes it, what it cost. Cutting specifics to move this number would lower the `specificity` finding in the same scan, which matters more, and inventing a mention is forbidden outright. The proxy stays silent below 600 words or 12 distinct entities, because a short piece names things once for lack of room. Add the scan JSON to **`05-scans.json`** under the `"structure"` key, alongside the surface scan's `"surface"` key (never to `05-humanize.md` — see the humanize step: that file is measured sentence-by-sentence by `authorship.py`) and note the overall band in `08-quality-scorecard.md` as ADVISORY — it never gates `status: ready`, and it measures visible structure only (it cannot see and has no relationship to any statistical watermark).

## Chain handoffs

- **Upstream:** `/digital-marketing-pro:content-brief` (preferred — pre-researched) or `/digital-marketing-pro:keyword-cluster` (`06-pillar-pages.md` becomes content briefs)
- **Downstream:**
  - `/digital-marketing-pro:publish-blog` — pushes the publish-ready draft to the CMS
  - `/digital-marketing-pro:content-repurpose` + `/digital-marketing-pro:social-strategy` — repurposes the article across platforms
  - `/digital-marketing-pro:check` — final pre-publish gate
  - `/digital-marketing-pro:c2pa-metadata` — if AI-generated images accompany the article and EU markets are targeted

## Tips & caveats

- **Brand voice deviation tolerance is per-axis, not aggregate.** A piece that's 1 point off on every axis is not the same as 4 points off on humor alone — the latter is a fail even if the average looks OK.
- **Humanize step is not a guarantee** against AI-detection tools — it's a probabilistic improvement, and no scan here detects or removes any statistical watermark. `ai-tell-scan.py` measures visible text only. For pieces that must minimize AI-sounding patterns, run additional humanize passes and re-score with `/digital-marketing-pro:eval-content`, iterating until the flagged patterns clear; a final human edit pass remains the strongest signal — and the strongest signal of all is the author's own sentences, which is what `--source-draft` preserves.
- **Fact-check is content's most-skipped gate.** Don't ship a piece with "0 unverified" only because no one looked. Run `/digital-marketing-pro:verify-claims` against the draft if you didn't have a fact-checker in the loop.
- **For pillar content,** target the upper bound of word count (3000+ for SaaS, 5000+ for B2B research) — pillar pages need depth for topical authority. For spoke content, the lower bound is fine.
- **Don't write the meta description last.** Write it FIRST, before the article — it's the answer to "what's this page's promise?" Writing it last produces post-hoc summaries that don't drive click intent.

## Related Skills

- **Audience Intelligence** — For persona-specific content targeting and messaging that resonates with defined segments
- **AEO/GEO Intelligence** — For optimizing content to be cited by AI answer engines and maintaining entity consistency
- **Campaign Orchestrator** — For mapping content to campaign channels and ensuring message consistency across touchpoints
- **Funnel Architect** — For aligning content to funnel stages and ensuring every stage has appropriate content support
- **Digital PR & Authority** — For thought leadership content, press releases, and E-E-A-T authority building through content
- **Analytics & Insights** — For measuring content performance, identifying decay, and optimizing based on data

## Context efficiency

This skill's reference docs (`skills/<this-skill>/*.md`) sum to ~30-50KB. Don't load them eagerly — pick targeted sections:

- **Grep before Read.** Find the keyword or section heading first, then Read with `offset` + `limit` to pull just that range.
- **Walk `${CLAUDE_SKILL_DIR}` once.** Use a single directory listing to see what's there, then Read only the files that match your current step.
- **One source at a time.** If the workflow says "consult three reference files," read them sequentially after deciding what you need from each. Bulk-loading all three blows the per-skill 5K-token budget that auto-compaction reserves.
- **Strip noise from CSV inputs.** If the input is a large CSV, grep the header line first to pick columns, then process row-by-row — do not Read the whole file into context.
