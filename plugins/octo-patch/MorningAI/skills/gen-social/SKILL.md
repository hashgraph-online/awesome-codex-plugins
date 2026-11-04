---
name: gen-social
version: "1.3.0"
description: Generate platform-specific social media copy and images for content distribution
---

## Objective

Transform the daily AI news report into platform-optimized social media content. Generates ready-to-post copy and adapted images for multiple platforms, with support for multiple accounts and styles per platform.

**Phase 1 scope**: Generate copy files + images. No auto-publish (future phase).

---

## Supported Platforms

### X / Twitter

| Constraint | Value |
|------------|-------|
| Single tweet | 280 characters max |
| Thread | Unlimited tweets (recommended 5-15) |
| Images per tweet | Up to 4, 16:9 or 1:1 |
| Hashtags | 2-3 per tweet |
| Mentions | @handle format |

### Xiaohongshu (Little Red Book)

| Constraint | Value |
|------------|-------|
| Title | 20 characters max |
| Body | 1000 characters max |
| Images | Up to 9 per post, 3:4 or 1:1 (carousel) |
| Tags | 5-10 # tags at end of body |
| Emoji | Heavy use expected (platform culture) |

---

## Style Definitions

### Custom Personas & Styles

Templates define the voice, tone, and format for each channel. This repo ships with **one example template per platform** as a starting point:

- **X**: `templates/x/insider.md` (Tech Insider persona)
- **Xiaohongshu**: `templates/xiaohongshu/educational.md`

To create your own persona or style:

```bash
# X persona
cp skills/gen-social/templates/x/insider.md skills/gen-social/templates/x/my-persona.md

# Xiaohongshu style
cp skills/gen-social/templates/xiaohongshu/educational.md skills/gen-social/templates/xiaohongshu/my-style.md
```

Edit the copy, then set your channel config `style` field to match the filename (e.g. `"style": "my-persona"`). Custom templates in these directories are gitignored — your personas stay local.

### X Styles

Each X style has a distinct **persona** — a consistent voice and perspective that makes the account feel like a real person, not a news feed.

**Available styles:**

| Style | Persona | Template | Tone | Default Items | Min Score |
|-------|---------|----------|------|---------------|-----------|
| `briefing` | Daily Briefing | `templates/x/briefing.md` | Clean scannable index + infographic image, neutral | 5 | 6 |
| `insider` | Razor | `templates/x/insider.md` | Devastating one-liners, deadpan, says the quiet part loud | 3 | 7 |
| `commentary` | Builder | `templates/x/commentary.md` | First-person practical, opinionated hot takes, @levelsio meets @karpathy | 3 | 8 |
| `thread` | Hype-Free Analyst | `templates/x/thread.md` | Data-driven thread, contrarian, pattern recognition, @Benedict Evans | 5 | 6 |

### Xiaohongshu Styles

**Available styles:**

| Style | Template | Tone | Default Items | Min Score |
|-------|----------|------|---------------|-----------|
| `news-briefing` | `templates/xiaohongshu/news-briefing.md` | Telegraph speed-scan, priority indicators | 5-8 | 5 |
| `educational` | `templates/xiaohongshu/educational.md` | Structured explainer, numbered, "one article to understand it all" | 3-5 | 6 |
| `recommendation` | `templates/xiaohongshu/recommendation.md` | Enthusiastic discovery, heavy emoji, "must see!" | 3 | 7 |

---

## Channel Configuration

A **channel** is the core abstraction: one channel = one platform + one style + one language + content selection rules. Each channel produces an independent set of output files.

### Channel Config File

Located at `~/.config/morning-ai/social_channels.json` (or path set via `SOCIAL_CHANNELS_FILE`).

```json
[
  {
    "id": "x_insider_en",
    "platform": "x",
    "style": "insider",
    "lang": "en",
    "items": 3,
    "min_score": 7,
    "image": true,
    "image_aspect": "16:9"
  },
  {
    "id": "x_thread_en",
    "platform": "x",
    "style": "thread",
    "lang": "en",
    "items": 5,
    "min_score": 6,
    "image": true,
    "image_aspect": "16:9"
  },
  {
    "id": "xhs_kepu_zh",
    "platform": "xiaohongshu",
    "style": "educational",
    "lang": "zh",
    "items": 5,
    "min_score": 6,
    "image": true,
    "image_aspect": "3:4",
    "image_count": 4
  },
  {
    "id": "xhs_zhongcao_zh",
    "platform": "xiaohongshu",
    "style": "recommendation",
    "lang": "zh",
    "items": 3,
    "min_score": 7,
    "image": true,
    "image_aspect": "3:4",
    "image_count": 3
  }
]
```

### Channel Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique channel identifier, used in output filenames |
| `platform` | string | Yes | `x` or `xiaohongshu` |
| `style` | string | Yes | Style name (see Style Definitions above) |
| `lang` | string | Yes | Language code: `en`, `zh`, `ja`, etc. |
| `items` | number | No | Max items to include (default: from template) |
| `min_score` | number | No | Minimum score threshold (default: from template) |
| `image` | boolean | No | Generate images for this channel (default: `false`) |
| `image_aspect` | string | No | Image aspect ratio: `16:9`, `1:1`, `3:4` (default: platform default) |
| `image_count` | number | No | Number of carousel images for xiaohongshu (default: 1) |
| `image_style` | string | No | Override image style: `classic`, `dark`, `glassmorphism`, `newspaper`, `tech`, `cover-hook` (default: persona's recommended style). Note: `cover-hook` is special — it is intended only for the FIRST image of a Xiaohongshu carousel (the thumbnail in the discovery feed). Subsequent images should use the channel's regular style. |
| `include_types` | array | No | Filter by content types, e.g. `["model", "product"]` (default: all) |
| `kol_voice_only` | boolean | No | If `true`, only items with `is_kol_voice: true` are eligible for selection. Used by the dedicated KOL channel so that KOL original commentary becomes the post's main topic, not embedded inside an unrelated post. (default: `false`) |
| `conditional` | string | No | Conditional run gate. Currently supported: `viral_only` (max score ≥ `min_score`) and `kol_voice_available` (at least one item with `is_kol_voice: true` and `score ≥ min_score`). If the gate fails, the channel produces an empty manifest entry (no copy file, no images) and downstream consumers (e.g. foreman publish adapter) should skip the run gracefully. |

### Quick Setup (Single Channel via Env Vars)

When only one channel is needed, use env vars instead of a JSON file:

```bash
SOCIAL_PLATFORM=x
SOCIAL_STYLE=insider
SOCIAL_LANG=en
```

This creates a single channel with id `{platform}_{style}_{lang}`.

---

## Content Selection Rules

For each channel, select items from the daily report data:

1. **Filter by score**: only items with `importance >= min_score`
2. **Filter by type**: if `include_types` is set, only those content types
3. **Filter by KOL voice flag**: if `kol_voice_only: true` is set, only items where `is_kol_voice: true`
4. **Sort by score**: highest first
5. **Limit**: take top N items (from channel `items` setting or template default)
6. **Translate**: if source data language differs from channel `lang`, translate content. Entity names (proper nouns) stay unchanged.

### Conditional Channels (Pre-Selection Gate)

**This check runs BEFORE the 5 steps above.** Some channels only make sense on certain days (e.g. a viral-only channel that should only post when there's a genuinely big story). These channels declare a `conditional` field — the value tells the pipeline what gate to apply:

| `conditional` value | Gate logic |
|---|---|
| (omitted) | Always run (default) |
| `viral_only` | Channel runs ONLY if `max(item.importance for item in today's data) >= channel.min_score`. If no item clears the threshold, the channel is skipped. |
| `kol_voice_available` | Channel runs ONLY if at least one item has `is_kol_voice: true` AND `score >= channel.min_score`. If no qualifying KOL voice exists today, the channel is skipped. Used by the dedicated KOL channel so that on quiet KOL days the post is not forced. |

**When a conditional channel is gated off:**

1. Do NOT generate a copy file or images for this channel
2. Still emit a manifest entry, but with a `skipped: true` field and a `skip_reason` explaining why (e.g. `"max score 7.8 < required 8.5"`)
3. Required manifest entry shape for skipped conditional channels:
   ```json
   {
     "id": "xhs_zhongcao_viral_zh",
     "platform": "xiaohongshu",
     "style": "single-topic",
     "skipped": true,
     "skip_reason": "max score 7.8 < required 8.5"
   }
   ```
4. Downstream publish adapters (e.g. foreman `daily-publish-xhs-2-viral`) detect `skipped: true` and mark their run as SKIPPED rather than FAILED.

**Why this matters**: it lets us schedule a 12:00 viral-only post on the cron without generating empty/low-quality posts on slow news days. The viral channel only fires content when there's something worth firing about.

---

## Copy Generation

For each channel:

1. Read the template: `{SKILL_DIR}/skills/gen-social/templates/{platform}/{style}.md`
2. Select items using Content Selection Rules above
3. Generate copy following the template's format rules, character limits, and tone
4. Validate character counts against platform limits

### Post-Generation Checklist

- [ ] Character count within platform limits (280/tweet for X, 20 title + 1000 body for Xiaohongshu)
- [ ] Language matches channel `lang` setting
- [ ] Entity names preserved as proper nouns (not translated)
- [ ] Source links included where template requires them
- [ ] Hashtags/tags present and relevant
- [ ] No score numbers displayed in copy (scores are internal only)

---

## Image Generation

Social images reuse the existing image generation infrastructure (`lib/image_gen.py`) and the same providers (Gemini/GPT/MiniMax).

### Image Language Rules

Image text language **must match the target platform**, not the report source language:

| Platform | Image Language | Header Text |
|----------|---------------|-------------|
| **X** | **English only** | "MorningAI" |
| **Xiaohongshu** | **Chinese only** | "MorningAI" |

All card titles, bullet points, section headers, and any text rendered on the image must be in the platform's language. Entity names (proper nouns like OpenAI, DeepSeek) remain unchanged.

### Persona–Image Style Mapping

Each persona/style has a **recommended image style** that matches its voice. This overrides the global `IMAGE_STYLE` setting for social images.

#### X Styles

| Persona | Recommended Image Style | Images | Why |
|---------|------------------------|--------|-----|
| **briefing** (Daily Briefing) | `classic` | 1 cover + per-category (model/product/benchmark/funding) | Clean editorial, professional — cover indexes the day, per-category images go deeper |
| **insider** (Tech Insider) | `tech` | 0 | Razor is pure text — images dilute the punchline |
| **commentary** (Builder) | `dark` | 0 | Builder takes stand alone — bold text, no visual crutch |
| **thread** (Hype-Free Analyst) | `classic` | 1 cover | Clean editorial magazine — serious, data-focused, no visual noise |

#### Xiaohongshu Styles

| Style | Default Image Style | Images | Why |
|-------|---------------------|--------|-----|
| **recommendation** | `glassmorphism` | 3 carousel | Frosted glass, warm tones — lifestyle/discovery aesthetic |
| **educational** | `classic` | 4 carousel | Clean editorial — structured, authoritative content |
| **news-briefing** | `newspaper` | 1 | Classic newsprint — information-dense, professional |

> **IMPORTANT**: If the channel config has an explicit `image_style` field, that takes absolute priority over the defaults above. Do NOT include style labels or content-type annotations in image prompts.

#### Briefing Per-Category Images

The **briefing** channel generates additional per-category images beyond the cover, mirroring how `gen-infographic` handles per-type infographics:

| Image | Filename | Generated When |
|-------|----------|----------------|
| Cover | `social_{DATE}_x_briefing_en_cover.png` | Always |
| Model | `social_{DATE}_x_briefing_en_model.png` | ≥1 Model item with score ≥ min_score |
| Product | `social_{DATE}_x_briefing_en_product.png` | ≥1 Product item with score ≥ min_score |
| Benchmark | `social_{DATE}_x_briefing_en_benchmark.png` | ≥1 Benchmark item with score ≥ min_score |
| Funding | `social_{DATE}_x_briefing_en_funding.png` | ≥1 Funding item with score ≥ min_score |

Per-category images:
- Same classic style as cover, 16:9 landscape
- Header: "MorningAI — {Type} Updates" (no date — consistent with infographic per-type images)
- Include ALL qualifying items of that type (not limited to the channel `items` cap)
- Each card: entity + event + 2-3 bullet points

The recommended style is a default — channels can override via `image_style` field in the channel config. If not set, the persona's recommended style is used. If no persona mapping exists, falls back to the global `IMAGE_STYLE` setting.

### Platform-Specific Image Adaptation

**X images**:
- Aspect ratio: 16:9 (landscape) or 1:1 (square)
- **All text in English** — titles, bullets, headers, everything
- Header: "MorningAI"
- Apply the persona's recommended image style (see mapping above)
- Single image per tweet (or up to 4 for threads)

**Xiaohongshu images**:
- Aspect ratio: 3:4 (portrait) or 1:1 (square)
- **All text in Chinese** — titles, bullets, headers, everything
- Header: "MorningAI"
- Apply the style's recommended image style (see mapping above), plus Xiaohongshu-specific adaptations:
  - Larger font sizes for mobile readability
  - Rounded card corners (16px)
  - Emoji-style bullet markers
- Carousel strategy (when `image_count > 1`):
  - Image 1: Cover overview — top headlines, eye-catching title
  - Image 2-N: Detail pages — 1-2 items per image with expanded bullet points
  - Last image: Follow/subscribe CTA (optional)

### Image Prompt Template

```
{ASPECT} infographic, {HEADER_TEXT} {YYYY-MM-DD}, ALL text content in {LANG}.

Total news items: {N}

News cards (display EXACTLY {N} cards):

Card 1: {Entity name} {Event subject} {Core event verb phrase}
- {Point 1}
- {Point 2}
- {Point 3}

(... list according to actual item count ...)

CRITICAL RULES:
- ALL text on this image MUST be in {LANG} — titles, bullet points, headers, labels, everything
- Entity names are proper nouns (OpenAI, DeepSeek, Cursor) — keep as-is, do NOT translate
- Do NOT display ANY platform names on the image (no "小红书", "Xiaohongshu", "特刊", "Twitter", "X" etc.) — the image is content, not an ad for the platform
- Header text: "{HEADER_TEXT}"
- Each card title MUST include: Entity name + Event subject + Event description
- Display complete titles, do NOT truncate
- Do NOT display score numbers, score badges, or importance markers
- Do NOT invent items not listed
- Display ALL bullet points for each card
- Maximize content area — card titles and bullet points are the primary focus

ANTI-AI-SLOP RULES (mandatory — ref: huashu-design):
- NO purple/lavender/violet gradients — this is the #1 "AI-generated" tell
- NO emoji as bullet markers or icons — use typographic bullets (·, —, or numbered)
- NO rounded-corner cards with colored left border accent — the 2020-2024 AI slop archetype
- NO Inter/Roboto/Arial/system fonts as display — use serif display fonts (Noto Serif, Source Serif, Georgia)
- NO neon glow, glassmorphism, or frosted glass effects
- NO decorative icons per heading — if an icon doesn't carry information, remove it
- NO flat digital color blocks — use paper/material texture feel
- Color restraint: black + cream/white + ONE accent color max. Do NOT invent extra colors
- Typography IS the visual language — let font weight, size, and spacing create hierarchy, not color/shape decoration
- One detail at 120%, everything else at 80% — not uniformly polished, but sharp where it counts
- Describe mood, not pixel coordinates — "feels like a morning broadsheet" beats "title at top, 36pt, centered"

{STYLE_BLOCK}
{PLATFORM_STYLE_ADDON}
```

**Variable substitution:**
- `{HEADER_TEXT}` → "MorningAI" for X, "MorningAI" for Xiaohongshu
- `{LANG}` → "English" for X, "Chinese" for Xiaohongshu
- `{STYLE_BLOCK}` → from the persona's recommended image style (see `skills/gen-infographic/SKILL.md` Style Presets)

**`{PLATFORM_STYLE_ADDON}`** for Xiaohongshu — **use the matching style variant based on the channel's `image_style` field**:

**When `image_style` = `glassmorphism`:**
```
Additional Xiaohongshu adaptation (glassmorphism):
- ALL text must be in Chinese (except entity proper nouns)
- Soft gradient background (lavender to pale rose)
- Semi-transparent frosted white cards with backdrop blur
- Use rounded corners (16px) on all cards
- Larger title font (22pt bold) for mobile readability
- Warm accent colors: coral (#FF6B6B), soft pink (#FFB4B4), lavender (#E8EAF6)
- Emoji bullet markers (colored dots or sparkle symbols)
- Clean, fresh, lifestyle-magazine aesthetic
- Generous padding and line spacing for mobile screens
```

**When `image_style` = `newspaper`:**
```
Additional Xiaohongshu adaptation (newspaper):
- ALL text must be in Chinese (except entity proper nouns)
- Mood: feels like unfolding a quality morning broadsheet — authoritative, calm, information-dense, zero decoration
- Warm cream background (#FFF8E7) with subtle paper grain texture — NOT flat digital white
- Typography IS the design: bold serif headers (Noto Serif CJK / Source Han Serif / Georgia feel), clean sans-serif body
- Typographic hierarchy through font weight (700 headers, 400 body) and size contrast — NOT through color or shape
- Thin black hairline rules (1px) between sections, like column dividers in a broadsheet
- NO card backgrounds, NO rounded corners, NO shadows, NO colored borders — pure typographic layout
- Color: cream + deep black + crimson (#DC143C) accent ONLY — crimson used sparingly (dateline, one key number, or a thin rule)
- Bullet markers: typographic only (· or —), NEVER emoji
- One signature detail at 120%: the headline typography should feel crafted, like a newspaper masthead
- Generous line spacing (1.6+) for mobile readability, but information-dense — fill the space with content, not decoration
- DO NOT use gradients, frosted glass, glow effects, or any "digital" aesthetic
- The image should look like it was typeset, not generated
```

**When `image_style` = `cover-hook`:** (FIRST image of XHS carousel ONLY — this is the discovery-feed thumbnail)
```
Additional Xiaohongshu adaptation (cover-hook):
- ALL text must be in Chinese (except entity proper nouns)
- Mood: a newspaper EXTRA edition headline — urgent, bold, one statement that demands attention, but with editorial class, not digital loudness
- 3:4 single card, super-large title text occupying ≥ 50% of canvas
- Title text = the post title or its strongest 1-line variant (e.g., "Cursor 估值飙到 500 亿")
- ONE single subtitle line below with the most striking concrete data point (e.g., "3 年达 20 亿 ARR · 史上最快 B2B")
- Newspaper headline poster aesthetic:
  - Warm cream (#FFF8E7) with bold black serif title, OR deep charcoal (#1A1A1A) with cream/off-white serif title
  - Bold serif typography (Noto Serif CJK / Source Han Serif / Georgia feel), weight ≥ 700
  - Paper grain texture — NOT flat digital color blocks
- Thin crimson (#DC143C) hairline rule above or below the headline — the ONE signature detail at 120%
- Optional: small "MorningAI" masthead at very top in small caps, like a newspaper nameplate — restrained, not decorative
- NO bullet points, NO emoji, NO icons, NO small annotations — single statement only
- NO body text, NO list of items, NO date stamps — only the headline + one subtitle line
- NO gradients, NO glow, NO frosted glass, NO rounded corners — this is typeset, not generated
- The cover should look like a broadsheet front page that was photographed, not a Canva template
```

**When `image_style` = `classic`:**
```
Additional Xiaohongshu adaptation (classic):
- ALL text must be in Chinese (except entity proper nouns)
- Off-white background (#F5F5F0), clean editorial magazine layout
- Card-based layout with subtle shadows
- Navy (#1B2A4A), coral (#E8634A), teal (#2A9D8F) accent palette
- Use rounded corners (8px) on cards
- Larger title font for mobile readability
- Structured, authoritative visual hierarchy
- Generous padding and line spacing for mobile screens
```

**`{PLATFORM_STYLE_ADDON}`** for X (append to any base style):
```
Additional X/Twitter adaptation:
- ALL text must be in English (except entity proper nouns)
- Optimized for timeline scroll — key info visible at small preview size
- High contrast text for readability on mobile
```

### Generating Images

Use the same methods as Step 4 (gen-infographic):

**Option A** — Native tool (if supported):
Generate each image using built-in image generation capability.

**Option B** — Python script batch mode:
Build a manifest JSON and run:
```bash
cd {SKILL_DIR} && python3 skills/gen-infographic/scripts/gen_infographic.py --batch {CWD}/social/manifest_images.json
```

Manifest entries support `"aspect_ratio": "3:4"` for Xiaohongshu images.

#### Cover-Hook for Xiaohongshu Carousels

For Xiaohongshu channels with `image_count >= 2` AND style `recommendation` or `single-topic`, the **first image** of the carousel is the discovery-feed thumbnail and MUST use the `cover-hook` style addon (regardless of the channel's regular `image_style`):

- Image 1 → use `{PLATFORM_STYLE_ADDON}` for `cover-hook`. Content = post title + ONE strongest data point. No bullet points, no list of items.
- Image 2..N → use the channel's regular `image_style` (e.g., `newspaper`). Content = the per-item news cards as before.

This applies because the first image is what stops the scroll in the discovery feed; an information-dense newspaper card is unreadable as a thumbnail. Channels that already declare `image_style: cover-hook` explicitly should apply it to ALL images (rare — typically reserved for single-image posts).

---

## Output Files

All output goes to `{CWD}/social/` directory.

### Naming Convention

```
social/
├── social_{DATE}_{channel_id}.md              # Copy file
├── social_{DATE}_{channel_id}_cover.png       # Single/cover image
├── social_{DATE}_{channel_id}_{N}.png         # Carousel image N
└── social_{DATE}_manifest.json                # Output index
```

### Manifest Format

> **MANDATORY SCHEMA — DO NOT IMPROVISE FIELD NAMES OR PATHS**
>
> The manifest is consumed by downstream tools that match on exact field
> names and assume flat filenames. Past LLM-generated output has drifted
> in ways that silently break consumers (`channel_id` instead of `id`,
> `copy` instead of `copy_file`, paths prefixed with `social/`). This
> section is the contract — produce it byte-for-byte as specified.

**Required top-level shape:**
- `channels` MUST be a JSON **array** (list). Never a dict keyed by id.

**Required per-channel fields** — use these exact names, no aliases:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | string | Yes | Channel identifier. **Field name is `id`, NOT `channel_id`.** |
| `platform` | string | Yes | `x` or `xiaohongshu` |
| `style` | string | Yes | Style name |
| `lang` | string | Yes | `en`, `zh`, `ja`, etc. |
| `copy_file` | string | Conditional | **Filename only** (no directory prefix). Field name is `copy_file`, NOT `copy`. **Omit this field if `skipped: true`.** |
| `images` | array<string> | Conditional | **Filenames only** (no directory prefix). Empty list `[]` if no images. **Omit this field if `skipped: true`.** |
| `items_used` | number | No | Count of source items included |
| `skipped` | boolean | No | Set to `true` for conditional channels that did not meet their gate (e.g. viral_only with no item ≥ min_score). When `true`, omit `copy_file` and `images`. |
| `skip_reason` | string | Conditional | Required when `skipped: true`. Short explanation, e.g. `"max score 7.8 < required 8.5"`. |

**Path rules — applies to `copy_file` and every entry in `images`:**
- Write the **bare filename** as it appears under `social/` (e.g. `social_2026-04-18_xhs_zixun_zh.md`).
- Do **NOT** include any directory component — no `social/`, no `./`, no absolute path.
- Wrong: `"copy_file": "social/social_2026-04-18_xhs_zixun_zh.md"` ❌
- Right: `"copy_file": "social_2026-04-18_xhs_zixun_zh.md"` ✅

**Canonical example** (copy this shape exactly):

```json
{
  "date": "2026-04-14",
  "channels": [
    {
      "id": "x_insider_en",
      "platform": "x",
      "style": "insider",
      "lang": "en",
      "copy_file": "social_2026-04-14_x_insider_en.md",
      "images": ["social_2026-04-14_x_insider_en_cover.png"],
      "items_used": 3
    },
    {
      "id": "xhs_kepu_zh",
      "platform": "xiaohongshu",
      "style": "educational",
      "lang": "zh",
      "copy_file": "social_2026-04-14_xhs_kepu_zh.md",
      "images": [
        "social_2026-04-14_xhs_kepu_zh_1.png",
        "social_2026-04-14_xhs_kepu_zh_2.png",
        "social_2026-04-14_xhs_kepu_zh_3.png",
        "social_2026-04-14_xhs_kepu_zh_4.png"
      ],
      "items_used": 5
    },
    {
      "id": "xhs_zhongcao_viral_zh",
      "platform": "xiaohongshu",
      "style": "single-topic",
      "lang": "zh",
      "skipped": true,
      "skip_reason": "max score 7.8 < required 8.5"
    }
  ]
}
```

**Forbidden variants** (all of these have been observed in real output and
break downstream consumers — do not produce them):

```json
// ❌ WRONG — "channel_id" is not a recognized field
{ "channel_id": "xhs_zixun_zh", ... }

// ❌ WRONG — "copy" is not a recognized field
{ "id": "xhs_zixun_zh", "copy": "...", ... }

// ❌ WRONG — paths must be bare filenames
{ "copy_file": "social/social_2026-04-18_xhs_zixun_zh.md",
  "images": ["social/social_2026-04-18_xhs_zixun_zh_1.png"] }

// ❌ WRONG — channels must be a list, not a dict keyed by id
{ "channels": { "xhs_zixun_zh": { ... } } }
```

Before writing the manifest file, mentally diff your output against the
canonical example above. If any field name, structure, or path shape
differs, fix it before writing.

---

## Workflow Summary

1. Check if social content is enabled (`SOCIAL_ENABLED=true`)
2. Load channel configuration (JSON file or env vars)
3. For each channel:
   a. **Conditional gate**: if the channel has a `conditional` field, evaluate the gate. If it fails, write a manifest entry with `skipped: true` + `skip_reason` and continue to the next channel — do NOT generate copy or images.
   b. Read the channel's template file
   c. Select top items from report data (score filter + item limit)
   d. Generate copy following template rules and character limits
   e. Write copy to `social/{DATE}_{channel_id}.md`
   f. If `image: true` — build image prompts and generate platform-adapted images. For XHS carousels with style `recommendation` or `single-topic`, the FIRST image uses the `cover-hook` style addon; subsequent images use the channel's regular `image_style`.
   g. Write images to `social/{DATE}_{channel_id}_{N}.png`
4. Write manifest to `social/{DATE}_manifest.json`

---

## Notes

- Channels are fully independent — each reads from the same daily data but produces separate output
- Multiple channels can target the same platform with different styles, languages, or content focus
- **Image language follows the platform**: X images are always English, Xiaohongshu images are always Chinese — regardless of the channel `lang` setting for copy
- **Image style follows the persona**: each persona/style has a recommended image style that matches its voice (see Persona–Image Style Mapping). Channels can override via `image_style` field
- All content must respect platform character limits — validation is mandatory
- Entity names are proper nouns and must NOT be translated regardless of `lang` setting
- When the same item appears in multiple channels, each channel generates its own adapted version independently
