---
name: gen-infographic
version: "1.3.0"
description: Generate cover and per-type infographics for MorningAI
---

## Objective

Generate multiple infographics for the daily report:

1. **Cover infographic** — top 4-5 updates across all types
2. **Per-type infographics** — one for each type that has important (7+) items

---

## Output Specs

| Image | Filename | When to generate | Aspect |
|-------|----------|-----------------|--------|
| Cover | `news_infographic_YYYY-MM-DD.png` | **Always** (if image gen is enabled) | 9:16 |
| Model | `news_infographic_YYYY-MM-DD_model.png` | Type has 7+ score items | 9:16 |
| Product | `news_infographic_YYYY-MM-DD_product.png` | Type has 7+ score items | 9:16 |
| Benchmark | `news_infographic_YYYY-MM-DD_benchmark.png` | Type has 7+ score items | 9:16 |
| Funding | `news_infographic_YYYY-MM-DD_funding.png` | Type has 7+ score items | 9:16 |
| KOL | `news_infographic_YYYY-MM-DD_kol.png` | ≥1 item with `is_kol_voice: true` (NO 7+ score gate — KOL voices are scored 4-7 by design) | 9:16 |
| Combined | `news_infographic_YYYY-MM-DD_combined.png` | Always (for report embed) | long |

- **Cover is always generated first as a standalone image** — even if no per-type sections qualify. Do NOT skip or merge the cover into a combined-only flow
- **Per-type sections use 9:16 portrait format**
- **Combined image**: Cover + sections stitched vertically — used for embedding in the Markdown report
- **Format**: PNG

### Social Posting (multi-image, no combined)

When posting to social platforms, use the **individual images** (not the combined long image):

| Platform | Max Images | Strategy |
|----------|-----------|----------|
| **X (Twitter)** | 4 per tweet | Cover + top 3 section images (by item count) |
| **Xiaohongshu** | 9 per post (carousel) | Cover + all section images |

> **`IMAGE_GEN_TYPES` config**: Controls which per-type images to generate. Default: `auto` (only types with 7+ items). Options: `all` (all types with any items), `none` (cover only), or comma-separated types like `model,product`.

---

## Title Format Specification

Each news title **must include three elements**:

| Element | Description | Example |
|---------|-------------|---------|
| **Entity name** | Company/product/organization name | NVIDIA, Cursor, Midjourney |
| **Event subject** | Specific model/product/event name | Alpamayo, Agent mode, V7 |
| **Core event** | Verb phrase describing the event | releases, open-sources, tops leaderboard, closes funding |

### Title Examples

✅ **Correct Examples**:
- NVIDIA Alpamayo Releases Open-Source Autonomous Driving VLA Model
- Cursor Closes $900M Series B Funding
- Midjourney V7 Officially Launches

❌ **Incorrect Examples**:
- Alpamayo 1 (missing entity name and event)
- NVIDIA Alpamayo (missing event description)
- Open-source autonomous driving model released (missing entity name)

---

## Content Detail Rules

Determine number of points based on score, **but do NOT use `[MAJOR]`/`[MINOR]` tags in Prompt or image**:

| Score | Number of Points | Card Size |
|-------|-----------------|-----------|
| **>= 7** | 3-5 detailed points | Large card (priority display) |
| **< 7** | 2-3 concise points | Small card |

> ⚠️ Score classification is only for guiding content detail level. **Do NOT** use `[MAJOR]`/`[MINOR]` or similar labels in Prompt!

---

## Style Presets

Select a visual style via `IMAGE_STYLE` config (default: `classic`). Insert the matching style block into `{STYLE_BLOCK}` in all prompt templates below.

### `classic` — Clean Editorial Magazine

```
Style: Clean editorial magazine layout. Off-white (#F5F5F0) background with subtle warm gray grid lines. Bold sans-serif header "MorningAI" in black with a vivid accent color underline. Each card is a white rectangle with soft drop shadow (4px blur, 10% black), separated by generous whitespace. Use a refined accent palette: deep navy (#1A2744) for card titles, muted teal (#2A9D8F) for bullet icons, slate gray (#4A5568) for body text. NO gradients, NO textures, NO background patterns — pure flat white space.
Layout: Cards arranged in a balanced grid with equal gutters (24px). Maximize space for card content (titles and bullet points). Do NOT display score numbers or score badges — let card size and content density convey importance.
Card design: Card title in 18pt bold navy sans-serif, subtitle in 12pt gray italic. Bullet points with small teal dot markers, 14pt regular weight. Thin 1px light gray top-border on each card for subtle separation. NO icons, NO illustrations, NO decorative elements inside cards — text only with strong typographic hierarchy. Prioritize readable text and generous line spacing.
```

### `dark` — Dark Mode

```
Style: Dark mode editorial layout. Deep charcoal (#1A1A2E) background. Bold sans-serif header "MorningAI" in white (#FAFAFA) with electric blue (#00D4FF) accent underline. Each card is a dark slate (#16213E) rectangle with subtle 1px border in muted blue (#0F3460), separated by generous spacing. Accent palette: white (#FAFAFA) for card titles, soft violet (#7B68EE) for bullet icons, light gray (#B0BEC5) for body text. NO gradients, NO glow effects — clean flat dark surfaces.
Layout: Cards arranged in a balanced grid with equal gutters (24px). Maximize space for card content (titles and bullet points). Do NOT display score numbers or score badges — let card size and content density convey importance.
Card design: Card title in 18pt bold white sans-serif, subtitle in 12pt light gray italic. Bullet points with small violet dot markers, 14pt regular weight. Thin 1px muted blue top-border on each card. NO icons, NO illustrations — text only with strong typographic hierarchy on dark background. Prioritize readable text and generous line spacing.
```

### `glassmorphism` — Frosted Glass

```
Style: Glassmorphism editorial layout. Soft gradient background blending from lavender (#E8EAF6) top-left to pale rose (#FCE4EC) bottom-right. Bold sans-serif header "MorningAI" in dark charcoal (#212121) with warm coral (#FF6B6B) accent underline. Each card is a semi-transparent frosted white panel (rgba(255,255,255,0.65)) with backdrop blur effect, rounded corners (16px), and subtle white border (1px, 30% opacity). Accent palette: charcoal (#212121) for card titles, soft indigo (#5C6BC0) for bullet icons, medium gray (#546E7A) for body text. Soft diffused shadows (8px blur, 5% black) behind each card.
Layout: Cards arranged in a balanced grid with generous gutters (28px). Maximize space for card content (titles and bullet points). Do NOT display score numbers or score badges — let card size and content density convey importance.
Card design: Card title in 18pt bold charcoal sans-serif, subtitle in 12pt gray italic. Bullet points with small indigo dot markers, 14pt regular weight. NO hard borders — rely on frosted glass contrast for separation. Clean, airy, modern feel. Prioritize readable text and generous line spacing.
```

### `newspaper` — Classic Newsprint

```
Style: Classic newspaper editorial layout. Warm cream (#FFF8E7) background with very faint paper texture grain. Bold serif header "MorningAI" in deep black (#1A1A1A) with crimson red (#B71C1C) thin rule line below. Each card is separated by thin black hairline rules (1px) — NO card backgrounds, NO shadows, NO boxes. Content flows in a column-based newspaper grid. Accent palette: deep black (#1A1A1A) for card titles in bold serif, dark gray (#333333) for bullet text in serif, medium gray (#666666) for subtitles in italic serif.
Layout: Multi-column newspaper grid (2-3 columns). Large stories span full width at top, smaller stories in side-by-side columns below. Separated by horizontal and vertical hairline rules. NO cards, NO boxes — pure typographic layout. Do NOT display score numbers or score indicators — let column placement and headline size convey importance.
Card design: Card title in 18pt bold black serif, subtitle in 12pt gray italic serif. Bullet points with small em-dash markers, 14pt regular serif weight. Feels like the front page of a prestigious broadsheet. Prioritize readable text and generous line spacing.
```

### `tech` — Terminal / Hacker

```
Style: Tech terminal aesthetic layout. Near-black background (#0D1117) with very faint dot grid pattern (8px spacing, 5% white). Bold monospace header "MorningAI" in bright cyan (#00FFCC) with a blinking cursor underscore effect. Each card is a dark panel (#161B22) with 1px border in dim cyan (#1A3A3A), rounded corners (4px). Accent palette: bright green (#39FF14) for card titles in monospace bold, amber (#FFB000) for bullet markers as `>` symbols, light gray (#C9D1D9) for body text in monospace. Each card has a subtle top-left label like `// MODEL` or `// PRODUCT` in dim green (#1A4A1A).
Layout: Cards arranged in a balanced grid with equal gutters (16px). Compact spacing, information-dense. Maximize space for card content (titles and bullet points). Do NOT display score numbers or score badges — let card size and content density convey importance.
Card design: Card title in 16pt bold green monospace, subtitle in 11pt gray monospace. Bullet points with amber `>` markers, 13pt regular monospace. Thin 1px dim cyan border. Feels like a developer dashboard or terminal readout. Prioritize readable text and generous line spacing.
```

---

## Prompt Template

```
9:16 portrait infographic, MorningAI {YYYY-MM-DD}, {LANG} text content.

Total news items for today: {N}

News cards (display EXACTLY {N} cards):

Card 1: {Entity name} {Event subject} {Core event verb phrase}
- {Point 1}
- {Point 2}
- {Point 3}
- {Point 4}
- {Point 5}

Card 2: {Entity name} {Event subject} {Core event verb phrase}
- {Point 1}
- {Point 2}
- {Point 3}

(... list according to actual item count ...)

CRITICAL RULES:
- Each card title MUST include: Entity name + Event subject + Event description
- Display complete titles, do NOT truncate
- Do NOT display any labels like [MAJOR], [MINOR], or importance markers
- Do NOT display score numbers, score badges, or any numerical ratings on the image
- Do NOT invent items not listed
- Display ALL bullet points for each card
- Cards arranged in a grid layout (landscape orientation)
- Maximize content area — card titles and bullet points are the primary focus
- If fewer than 4 items, use more whitespace and decorative elements
- Cover header MUST include the date: "MorningAI {YYYY-MM-DD}"

{STYLE_BLOCK}
```

**`{STYLE_BLOCK}`** — insert the matching style block from the Style Presets section above, based on `IMAGE_STYLE` config (default: `classic`).

---

## Usage Instructions

### 1. Determine Images to Generate

From the report, identify:
- **Cover**: Top 4-5 items across all types by score
- **Per-type**: For each type (Model/Product/Benchmark/Funding), check if it has 7+ score items. If yes, generate a per-type image.
- **KOL**: If ≥1 item has `is_kol_voice: true`, generate a KOL section image (`_kol.png`). NO 7+ score gate — KOL voices are scored conservatively (4-7) by design, so applying the standard gate would suppress the section image even when the report's `## KOL Voices` block is populated.

### 2. Build Prompts

**Cover prompt**: Use the Cover Prompt Template above.

**Per-type prompt**: Use the Per-Type Prompt Template below.

### Per-Type Prompt Template

```
9:16 portrait infographic, MorningAI — {Type} Updates, {LANG} text content.

Total news items: {N}

News cards (display EXACTLY {N} cards):

Card 1: {Entity name} {Event subject} {Core event verb phrase}
- {Point 1}
- {Point 2}
- {Point 3}

Card 2: {Entity name} {Event subject} {Core event verb phrase}
- {Point 1}
- {Point 2}

(... list according to actual item count ...)

CRITICAL RULES:
- Each card title MUST include: Entity name + Event subject + Event description
- Display complete titles, do NOT truncate
- Do NOT display any labels like [MAJOR], [MINOR], or importance markers
- Do NOT display score numbers, score badges, or any numerical ratings on the image
- Do NOT invent items not listed
- Display ALL bullet points for each card
- Cards arranged vertically (portrait layout), one below another
- Maximize content area — card titles and bullet points are the primary focus
- If fewer than 3 items, use more whitespace and decorative elements
- Do NOT display dates in the header or title — per-type images use "MorningAI — {Type} Updates" only, without any date

{STYLE_BLOCK}
```

> Adjust the style header text to "MorningAI — {Type} Updates" when using the preset.

### Combined Prompt Template — not used

> **Removed.** All reports now use Cover (9:16) + Per-Type Sections (9:16) + stitch for the combined report image. Social platforms use the individual images directly.

---

## Image Strategy

Image generation produces **individual images + a combined long image**:

1. **Cover** (9:16 portrait): Top 4-5 items across all types — **always generated first as a standalone file**
2. **Per-type sections** (9:16 portrait): One for each type with 7+ score items
3. **Combined** (long vertical): Cover + sections stitched vertically — for Markdown report embedding

> **Important**: The cover image must always exist as a separate file (`news_infographic_YYYY-MM-DD.png`). Do NOT skip cover generation even when producing a combined image.

**Social posting** uses the individual images directly (cover + sections), NOT the combined long image. See Output Specs > Social Posting for platform limits.

> If only 1-2 qualifying items exist, the cover still generates with extra whitespace. Per-type sections are skipped for types with no 7+ items.

Manifest example:
```json
[
  {"prompt": "<cover prompt>", "output": "news_infographic_YYYY-MM-DD.png"},
  {"prompt": "<model section>", "output": "news_infographic_YYYY-MM-DD_model.png"},
  {"prompt": "<product section>", "output": "news_infographic_YYYY-MM-DD_product.png"}
]
```

---

### 3. Generate Images

Follow the **Image Strategy** section above — generate cover + per-type sections + stitch combined.

**Option A** — Native tool (if supported):
Generate each image using your tool's built-in capability, then stitch.

**Option B** — Python script (default, recommended):
Build a manifest JSON and run with `--stitch`:

```bash
cd {SKILL_DIR} && python3 skills/gen-infographic/scripts/gen_infographic.py --batch {CWD}/manifest.json --stitch
```
> All images are 9:16 portrait. Requires `pip install Pillow`. Produces individual images + `news_infographic_YYYY-MM-DD_combined.png`.

### 4. Post-generation Verification (required)

For each generated image:
- Check card count equals N
- Verify each card title includes complete three elements
- Check if titles are truncated
- Confirm no unprovided content
- Confirm no `[MAJOR]`, `[MINOR]` or similar labels displayed
- Confirm no score numbers or score badges are displayed
- If issues found, regenerate or manually correct

### 5. Insert into Report

- Cover image: at report beginning
- Per-type images: at the top of each type section

---

## Handling Few Updates

When valid news items < 4, **do NOT pad with fake content**:

| Item Count | Layout Strategy |
|------------|----------------|
| **1 item** | Centered large card + "Today's Highlight" label + whitespace and decorative elements |
| **2 items** | Left-right symmetric or top-bottom stacked |
| **3 items** | Three-column even or pyramid layout |
| **4-5 items** | Standard grid layout |

> **Core principle**: prefer whitespace over fabrication.

---

## Notes

- Title uses "MorningAI", news content in the target language (default: English, follows `--lang` parameter)
- **Date display rule**: Only the **cover image** header includes the date (`MorningAI YYYY-MM-DD`). Per-type section images must **NOT** include any date — use `MorningAI — {Type} Updates` only.
- **`{LANG}`** — substitute with the full language name: "English" (default), "Chinese", "Japanese", etc., based on the `--lang` parameter
- **Strictly generate based on actual item count**, do not force 4-5 items
- **Do NOT use `[MAJOR]`/`[MINOR]` labels in Prompt**
- Use card size and point count to reflect importance differences
- Insert image into report Markdown beginning after generation
- **Popular Model Blocklist**: unless explicitly in report, do not include models/products not in the report
