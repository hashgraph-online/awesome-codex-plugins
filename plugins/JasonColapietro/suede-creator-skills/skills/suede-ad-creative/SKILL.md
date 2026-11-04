---
name: suede-ad-creative
description: "Suede AI Ad Creative Skills. Use when asked to \"write Google ad variants\" or iterate hooks, headlines, RSA/PMax assets, static or motion concepts from product and performance evidence. Returns grounded variants and a limit-checked review package. NOT FOR: budgets/targeting (suede-ads), experiment design (suede-ab-testing), organic posts (suede-social), general imagery (suede-image), or landing copy (suede-copy)."
metadata:
  display-name: "Suede AI Ad Creative Skills"
  version: 2.9.1
---

# Suede AI Ad Creative Skills

Read [the worked delivery contract](references/worked-contract.md) for a concrete
input, expected artifact, failure response and validation example.

## Compatibility

Works from supplied product/review/performance inputs; file access for creative packages and current platform documentation or preview for validation. Image/video generation needs an available approved production tool.

Use this performance-creative system to generate testable headlines, descriptions, primary text, and visual concepts, then iterate from real performance data.

## Before Starting

**Check for product marketing context first:**
If `.agents/product-marketing.md` exists (or `.claude/product-marketing.md`, or the legacy `product-marketing-context.md` filename, in older setups), read it before asking questions. Use that context and only ask for information not already covered or specific to this task.

Gather this context (ask if not provided):

### 1. Platform & Format
- What platform? (Google Ads, Meta, LinkedIn, TikTok, Twitter/X)
- What ad format? (Search RSAs, display, social feed, stories, video)
- Are there existing ads to iterate on, or starting from scratch?

### 2. Product & Offer
- What are you promoting? (Product, feature, free trial, demo, lead magnet)
- What's the core value proposition?
- What makes this different from competitors?

### 3. Audience & Intent
- Who is the target audience?
- What stage of awareness? (Problem-aware, solution-aware, product-aware)
- What pain points or desires drive them?

### 4. Performance Data (if iterating)
- What creative is currently running?
- Which headlines/descriptions are performing best? (CTR, conversion rate, ROAS)
- Which are underperforming?
- What angles or themes have been tested?

### 5. Constraints
- Brand voice guidelines or words to avoid?
- Compliance requirements? (Industry regulations, platform policies)
- Any mandatory elements? (Brand name, trademark symbols, disclaimers)

---

## How This Skill Works

This skill supports four modes:

### Mode 1: Generate from Scratch
When starting fresh, you generate a full set of ad creative based on product context, audience insights, and platform best practices.

### Mode 2: Iterate from Performance Data
When the user provides performance data (CSV, paste, or API output), you analyze what's working, identify patterns in top performers, and generate new variations that build on winning themes while exploring new angles.

The core loop:

```
Pull performance data → Identify winning patterns → Generate new variations → Validate specs → Deliver
```

### Mode 3: Scaled Static Batches (Grounded)
For recurring static ad production at volume (e.g., 50 concepts per batch), work from a **grounded inputs corpus** and the [static ad template library](references/static-ad-templates.md). Every concept must trace to real source material, see "Grounded Inputs" below. To run this on a daily or weekly cadence, route the production loop to `suede-marketing-loops`. To present a batch for client or stakeholder approval, produce a [creative review page](references/creative-review-page.md).

### Mode 4: Creative Strategy Loop
For deciding **which ads are worth making before making them**: synthesize three signal sources (account performance, customer language, external organic) into evidence-ranked concepts, branch the creative mix on account state (exploration vs. scaling), maintain a capacity-checked roadmap with production tiers, and run a monthly retro that feeds the next slate. The full system lives in [references/creative-roadmap.md](references/creative-roadmap.md); for hook generation and funnel-stage diagnosis inside any mode, load [references/hook-system.md](references/hook-system.md).

---

## Grounded Inputs

Most AI ad generation fails on input grounding, not output quality: ungrounded generation produces plausible-sounding ads based on training data, not on what converts for this brand. For scaled production (Mode 3), maintain a durable inputs corpus:

```
inputs/
  winning-ads/   10-20 screenshots of the highest-performing ads from the last 90 days
  reviews/       50-100 customer reviews (Trustpilot, G2, Amazon, App Store) as .md/.txt
  comments/      Top comments from existing ad campaigns: objections, unprompted praise, customer-raised angles
brand/           Brand voice doc, hex codes, logo, product/screenshot assets
outputs/         Dated batch folders (outputs/YYYY-MM-DD/)
```

**Why each input matters:**
- **Winning ads** carry the hooks, structures, and angles already proven for this brand
- **Reviews** carry the exact language buyers use for pain, transformation, and unexpected benefits, pull copy from them verbatim rather than paraphrasing
- **Ad comments** are the most-skipped and highest-value input: objections ("but does it work for X?") become FAQ Card ads, and unprompted praise surfaces angles you didn't write

**Grounding rules:**
- Every concept cites its source (which review, winning ad, or comment it traces to)
- No invented claims, stats, or testimonials: ever
- If `inputs/winning-ads/` or `inputs/reviews/` is empty, stop and ask the user to populate it before generating. Do not generate ungrounded concepts as a fallback.
- Inputs decay: refresh `inputs/winning-ads/` as new ads scale; refresh `inputs/reviews/` and `inputs/comments/` monthly

---

## Platform Specs

Platforms reject or truncate creative that exceeds these limits, so verify every piece of copy fits before delivering.

### Google Ads (Responsive Search Ads)

| Element | Limit | Quantity |
|---------|-------|----------|
| Headline | 30 characters | 3 to 15 |
| Description | 90 characters | 2 to 4 |
| Display URL path | 15 characters each | 2 paths |

Performance Max asset groups take 3 to 15 headlines (30 chars, at least one of
15 or fewer), 1 to 5 long headlines (90), 2 to 5 descriptions (90), and a
25-character business name. Image and video counts are in
[references/platform-specs.md](references/platform-specs.md).

**RSA rules:**
- Headlines must make sense independently and in any combination
- Pin headlines to positions only when necessary (reduces optimization)
- Include at least one keyword-focused headline
- Include at least one benefit-focused headline
- Include at least one CTA headline
- The quantities above are Google's ceiling. When the request came through `suede-ads`, its RSA output spec mandates the full 15 headlines and 4 descriptions, ship all of them.

### Meta Ads (Facebook/Instagram)

| Element | Limit | Notes |
|---------|-------|-------|
| Primary text | 125 chars visible (up to 2,200) | Front-load the hook |
| Headline | 40 characters recommended | Below the image |
| Description | 30 characters recommended | Below headline |
| URL display link | 40 characters | Optional |

### LinkedIn Ads

| Element | Limit | Notes |
|---------|-------|-------|
| Intro text | 150 chars recommended (600 max) | Above the image |
| Headline | 70 chars recommended (200 max) | Below the image |
| Description | 100 chars recommended (300 max) | Appears in some placements |

### TikTok Ads

| Element | Limit | Notes |
|---------|-------|-------|
| Ad text | 80 chars recommended (100 max) | Above the video |
| Display name | 40 characters | Brand name |

### Twitter/X Ads

| Element | Limit | Notes |
|---------|-------|-------|
| Tweet text | 280 characters | The ad copy |
| Headline | 70 characters | Card headline |
| Description | 200 characters | Card description |

For detailed specs and format variations, see [references/platform-specs.md](references/platform-specs.md).

---

## Generating Ad Visuals

**For static ad structure**, use the 15-template library in [references/static-ad-templates.md](references/static-ad-templates.md), layout frameworks (Us vs. Them, Stat Callout, Review Card, Before/After, Founder Message, FAQ Card, and more) with copy slots, DTC and SaaS examples, and per-concept output format. Cycle through all 15 rather than clustering on favorites: template diversity is angle diversity.

**When the concept is an iOS-native reveal video**, an iMessage thread, a ChatGPT answer, an Apple Notes confessional, or an AirDrop share, where the screen surface itself is the ad, read [references/imessage-video-ads.md](references/imessage-video-ads.md) before scripting. It carries surface selection, concept angles, pacing rules, production routes, and the compliance rules for dramatized conversations.

**When the concept is a faceless motion/explainer video** (15–45s, generated stills → image-to-video motion → TTS → captions), read [references/motion-video-ads.md](references/motion-video-ads.md) before writing prompts. It carries the pipeline, the visual-style library with fill-in prompt formulas, the brand-slots contract, and the QC gotchas.

**When you need to pick an image, video, voice, or code-based generation tool**, or price a batch, read [references/generative-tools.md](references/generative-tools.md). It owns the tool-class roster (described by capability, not brand), per-placement image specs, and cost comparisons; those age, so use its numbers rather than any you remember.

**Workflow for scaled production:** generate hero concepts with an
authorized image or video model, turn the winners into a code-rendered
template (Remotion or Hyperframes), batch variations from a data feed, and return to generation only for
new angles.

---

## Generating Ad Copy

### Step 1: Define Your Angles

Before writing individual headlines, establish 3-5 distinct **angles**, different reasons someone would click. Each angle should tap into a different motivation.

**Common angle categories:**

| Category | Example Angle |
|----------|---------------|
| Pain point | "Stop wasting time on X" |
| Outcome | "Achieve Y in Z days" |
| Social proof | "Join [verified count] teams who..." |
| Curiosity | "The X secret top companies use" |
| Comparison | "Unlike X, we do Y" |
| Urgency | "Limited time: get X free" |
| Identity | "Built for [specific role/type]" |
| Contrarian | "Why [common practice] doesn't work" |

### Step 2: Generate Variations per Angle

For each angle, generate multiple variations. Vary:
- **Word choice**: synonyms, active vs. passive
- **Specificity**: numbers vs. general claims
- **Tone**: direct vs. question vs. command
- **Structure**: short punch vs. full benefit statement

At volume (10+ variations), close with a wild-card pass: 3-5 concepts on angles nobody asked for: contrarian, emotional, uncomfortably specific. These are where the outliers come from, and they cost one extra pass.

### Step 3: Validate Against Specs

Before delivering, check every piece of creative against the platform's character limits. Flag anything that's over and provide a trimmed alternative.

### Step 4: Organize for Upload

Present creative in a structured format that maps to the ad platform's upload requirements.

---

## Iterating from Performance Data

When the user provides performance data, follow this process:

### Step 1: Analyze Winners

Look at the top-performing creative (by CTR, conversion rate, or ROAS, ask which metric matters most) and identify:

- **Winning themes**: What topics or pain points appear in top performers?
- **Winning structures**: Questions? Statements? Commands? Numbers?
- **Winning word patterns**: Specific words or phrases that recur?
- **Character utilization**: Are top performers shorter or longer?

### Step 2: Analyze Losers

Look at the worst performers and identify:

- **Themes that fall flat**: What angles aren't resonating?
- **Common patterns in low performers**: Too generic? Too long? Wrong tone?

Name the underperformers explicitly and say why the angle failed. Do not open by praising the existing set, and do not soften a losing angle into "needs more testing" when the declared metric has already resolved it at sufficient volume, say it lost, and retire it.

### Step 3: Generate New Variations

Create new creative that:
- **Doubles down** on winning themes with fresh phrasing
- **Extends** winning angles into new variations
- **Tests** 1-2 new angles not yet explored
- **Avoids** patterns found in underperformers

### Step 4: Document the Iteration

Track what was learned and what's being tested:

```
## Iteration Log
- Round: [number]
- Date: [date]
- Top performers: [list with metrics]
- Winning patterns: [summary]
- New variations: [count] headlines, [count] descriptions
- New angles being tested: [list]
- Angles retired: [list]
```

---

## Writing Quality Standards

Read [the writing quality standards](references/writing-quality.md) before drafting. They specify source-backed headlines, banned generic strings, complementary descriptions and truthful urgency.

## Output Formats

### Standard Output

Organize by angle, with character counts:

```
## Angle: [Pain Point: Manual Reporting]

### Headlines (30 char max)
1. "Stop Building Reports by Hand" (29)
2. "Automate Your Weekly Reports" (28)
3. "Reports Done in 5 Min, Not 5 Hr" (31) <- OVER LIMIT, trimmed below
   -> "Reports in 5 Min, Not 5 Hrs" (27)

### Descriptions (90 char max)
1. "Marketing teams save 10+ hours/week with automated reporting. Start free." (73)
2. "Connect your data sources once. Get automated reports forever. No code required." (80)
```

### Bulk CSV Output

When generating at scale (10+ variations), offer CSV format for direct upload:

```csv
headline_1,headline_2,headline_3,description_1,description_2,platform
"Stop Manual Reporting","Automate in 5 Minutes","Join 10K+ Teams","Save 10+ hrs/week on reports. Start free.","Connect data sources once. Reports forever.","google_ads"
```

### Static Batch Output (Mode 3)

For scaled static batches, save to a dated folder with an index:

```
outputs/YYYY-MM-DD/
  INDEX.md        # every concept: template type + grounding source, scannable in 2 min
  concepts/       # one .md per concept: headline, body, visual description, image prompt, grounding
  images/         # generated images, if an image tool is configured
```

Per-concept format is defined in [references/static-ad-templates.md](references/static-ad-templates.md). The human workflow this supports: open the folder, scan INDEX.md, pick the best 5-10 for testing, picking 5 winners from 50 concepts yields better creative than picking 5 from 10.

### Creative Review Page (client / stakeholder approval)

When a person who isn't you needs to review and pick, a client, a partner, a stakeholder, produce a **creative review page**: a self-contained HTML artifact that presents each concept as an in-feed platform mockup (Instagram/Facebook, with a whitelist-handle toggle), breaks carousels into a labeled frame-by-frame storyboard, lets them toggle headline/copy variations, and discloses what's grounded in real assets. It's the visual upgrade to INDEX.md, a decision made off one link instead of by reading markdown. The template ships at [assets/creative-review-template.html](assets/creative-review-template.html) (one file, no build, hostable anywhere); populate its `DATA` object from your generated concepts. Full data model, grounding rules (the disclosure block is required), and delivery in [references/creative-review-page.md](references/creative-review-page.md).

### Iteration Report

When iterating, include a summary:

```
## Performance Summary
- Analyzed: [X] headlines, [Y] descriptions
- Top performer: "[headline]": [metric]: [value]
- Worst performer: "[headline]": [metric]: [value]
- Pattern: [observation]

## New Creative
[organized variations]

## Recommendations
- [What to pause, what to scale, what to test next]
```

---

## Pre-delivery self-check

Every mode clears this gate before anything is handed over. It is not mode-specific and it is not optional.

- [ ] Every headline and description renders its character count inline
- [ ] No variant exceeds its platform's limit: anything over is trimmed, with the trimmed version shown
- [ ] At least 2-3 CTA headlines are present in every RSA
- [ ] No two variants share an angle; near-duplicates are removed
- [ ] Every Mode 3 concept cites its grounding source (which review, winning ad, or comment)
- [ ] No string from the Never-ship list above appears in any variant
- [ ] Nothing plausibly violates platform policy for the target placement

Any failure means fix it before delivering. Do not ship a batch with the failure noted as a caveat.

---

## Common Mistakes

- **Writing headlines that only work together**: RSA headlines get combined randomly
- **All variations sound the same**: Vary angles, not just word choice
- **No CTA headlines**: RSAs need action-oriented headlines to drive clicks; include at least 2-3
- **Generic descriptions**: "Learn more about our solution" wastes the slot
- **Testing too many things at once**: Change one variable per test cycle
- **Retiring creative too early**: give each variant enough spend to judge on the declared metric; for Meta lead gen use the TCPL gates in `suede-ads`

---

## Tool Integrations

This pack does not ship ad-platform connectors or CLI wrappers. Use only the
user's authorized platform UI, export, API, or installed connector, and verify
the current official platform documentation before constructing a call.

For a performance-led batch:

1. Read or export current ad-level performance at a declared date range and
   account scope.
2. Record the platform, account, currency, attribution window, and metric
   definitions with the data.
3. Analyze patterns, then generate traceable variants in this skill.
4. Route campaign, budget, audience, or upload decisions to `suede-ads`.
5. Treat activation as a separate authorized action after rendered review.

---

## Boundaries

- Do not invent product capabilities, testimonials, performance numbers, urgency, or platform-native proof.
- Do not upload, publish, activate, or spend against creative without explicit authorization and a final rendered review.
- Do not generate a replacement Suede S; use only the approved canonical mark when a Suede brand mark is required.
- Do not decide a creative winner from taste alone; use the declared metric, audience, spend, and test window.

## Routing

- Need campaign structure, targeting, budgets, or optimization -> use `suede-ads`.
- Need a statistically valid creative test -> use `suede-ab-testing`.
- Need source language from customers -> use `suede-customer-research`.
- Need landing-page copy or recurring production -> use `suede-copy` or `suede-marketing-loops`.
- Before any variant goes live in front of real people -> use `suede-deslop`.
- From those skills, route paid-media creative production back to `suede-ad-creative`.
