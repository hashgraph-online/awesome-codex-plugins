---
name: gen-message
version: "1.3.0"
description: Generate concise message digest with image for sharing on messaging platforms (WeChat, Telegram, Slack, etc.)
---

## Objective

Transform the daily AI news report data into a concise, copy-paste-friendly **message digest** optimized for sharing on messaging platforms. Produces two output files:

1. **Text digest** (`message_{DATE}.md`) — bold titles, one-line summaries, source links
2. **Digest image** (`message_{DATE}.png`) — 9:16 portrait infographic with compact card layout

The message digest shares the **same data pipeline** as the full report — all items go through the standard collect → score → deduplicate → cross-source link → verification pipeline. The only difference is the final output format: the full report produces a detailed multi-section Markdown document, while the message digest condenses the same verified data into a compact, share-friendly format.

**Factual integrity applies to all items:** Every item in the digest — regardless of score — must have a traceable, authoritative source (`source_url`). Items with score 7+ additionally require cross-source verification (`verified == true`, 2+ independent sources). Never include an item whose factual claims cannot be linked to a concrete primary source.

---

## Output Specs

### Text File: `message_{DATE}.md`

| Property | Value |
|----------|-------|
| Format | Markdown (renders as plain text in most messaging apps) |
| Encoding | UTF-8 |
| Sections | Header → Items (with source links) → Footer |

### Image File: `message_{DATE}.png`

| Property | Value |
|----------|-------|
| Format | PNG |
| Aspect Ratio | 9:16 portrait (optimized for mobile chat) |
| Layout | Single-column vertical card stack |
| Content | Same items as text digest, compact visual format |

---

## Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MESSAGE_ENABLED` | bool | `false` | Master switch for message digest generation |
| `MESSAGE_MIN_SCORE` | float | `5` | Minimum importance score to include an item |
| `MESSAGE_MAX_ITEMS` | int | `10` | Maximum number of items in the digest |
| `MESSAGE_LANG` | string | (from `--lang`) | Language override for the digest |
| `MESSAGE_IMAGE_STYLE` | string | (from `IMAGE_STYLE`) | Visual style override for the digest image |
| `MESSAGE_LINKS` | string | `inline` | Link placement: `inline` (after each item) or `bottom` (reference list at end) |
| `MESSAGE_CATEGORY_BALANCE` | bool | `true` | Distribute slots across content types to prevent single-type domination |

---

## Content Selection Rules

1. **Read data**: Load `data_{DATE}.json` from the working directory (this data has already been scored, deduplicated, and cross-source verified by the collection pipeline)
2. **Filter by score**: Only items with `importance >= MESSAGE_MIN_SCORE`
3. **Verify & ensure source link**: Every item included in the digest **MUST** have a valid `source_url`. This is a hard requirement — **no item may appear in the digest without an accompanying source link.**
   - If an item has a `source_url` in the data → use it directly
   - If an item has no `source_url` but has `verify_sources` or `cross_refs` → use the best available URL from those fields
   - If an item has no URL at all → **search for an authoritative source URL** (official blog, GitHub repo, announcement post, HuggingFace page) before including it. Construct the URL from known patterns when possible (e.g., `https://huggingface.co/{model_id}` for HF models, `https://github.com/{owner}/{repo}` for GitHub projects)
   - If no credible URL can be found after the above steps → **drop the item entirely** — do NOT include it without a link
   - For items with score 7+, additionally confirm `verified == true` (2+ independent sources)
   - **Zero-link items are a critical formatting error** — every item in the final output must end with a source link line
4. **Balance by category** (when `MESSAGE_CATEGORY_BALANCE` is `true`, default):
   a. Group qualifying items by `content_type`
   b. Apply per-type slot caps: `product` max **4**, `model` max **3**, `benchmark` max **2**, `financing` max **2**
   c. From each type, select the highest-scoring items up to the type's cap
   d. If a type has fewer qualifying items than its cap, its unused slots become available as overflow
   e. Fill remaining slots (up to `MESSAGE_MAX_ITEMS` total) with the next highest-scoring items from any type, regardless of whether that type has already hit its cap
   f. If `MESSAGE_CATEGORY_BALANCE` is `false`, skip this step and use pure top-N by score
5. **Sort**: Final selected items by importance score descending (highest first)
6. **Limit**: Ensure total does not exceed `MESSAGE_MAX_ITEMS`
7. **Translate**: If data language differs from `MESSAGE_LANG`, translate summaries. Entity names (proper nouns) stay unchanged.

---

## Text Generation Rules

### Language-Specific Headers

| Language | Header Text | Item Count Format |
|----------|-------------|-------------------|
| `zh` | `MorningAI {DATE}` | `共 {N} 条重要更新` |
| `en` | `MorningAI {DATE}` | `{N} notable updates today` |
| `ja` | `MorningAI {DATE}` | `本日の注目 {N} 件` |

### Emoji Markers by Score

| Score Range | Emoji | Meaning |
|-------------|-------|---------|
| 9-10 | 🔥 | Major / breakthrough |
| 7-8 | ⭐ | Important |
| 5-6 | 🔷 | Notable |

### Item Format

Each item follows this structure:

```
{emoji} **{Entity} {Event description}**
{One to two sentence summary: what it IS/DOES + why it matters.}
🔗 {source_url}
```

**Rules:**
- Title is bold, includes entity name + concise event description
- Summary is 1-2 sentences max — must answer TWO questions:
  1. **What is it / what does it do?** — the core capability, function, or purpose (e.g., "Code generation model specialized for multi-file edits", "Open-source text-to-video model supporting 10-second 1080p clips")
  2. **Why is it interesting / what's notable?** — the differentiator, breakthrough, or key advancement (e.g., "first open-weight model to beat GPT-4o on SWE-bench", "runs locally on consumer GPUs with 8GB VRAM")
- **Prioritize technical substance** over popularity metrics: benchmark scores, parameter counts, context window, architecture innovations, licensing, pricing, speed improvements
- **Do NOT lead with vanity metrics** like download counts, likes, stars, or follower counts — these say nothing about what the thing does. Only mention them if the surge itself IS the news (e.g., "hit 100K stars in 48 hours")
- No score numbers displayed — the emoji conveys importance level
- **Each item MUST end with a `🔗 {source_url}` line** — this is non-negotiable. An item without a source link is a formatting error. If the data lacks a `source_url`, construct one from known URL patterns (HuggingFace model page, GitHub repo, official blog) or search for an authoritative link. If no URL can be found, **drop the item** rather than publishing it without a link.
- Items separated by a blank line

### Special Formatting

For GitHub Trending items or items with notable engagement metrics:

```
🔥 **GitHub Trending: {repo-name}**
{What it does + why it's trending.} ⭐ {star_count}(+{delta})
🔗 {source_url}
```

Note: even for trending items, lead with what the project does, then append the star count as supporting context — not the other way around.

### Link Placement

**`MESSAGE_LINKS=inline`** (default):

Each item ends with a source link line:

```
🔥 **Anthropic Releases Claude 4.5 Sonnet**
New mid-tier model with +18% SWE-Bench, 200K context, 40% faster output.
🔗 https://anthropic.com/news/claude-4-5-sonnet
```

**`MESSAGE_LINKS=bottom`** (alternative — groups links at the end):

Links grouped as a numbered reference list at the bottom, items do NOT include inline links:

```
---
[1] {Entity Event} - {URL}
[2] {Entity Event} - {URL}
```

### Footer

```
---
Powered by MorningAI | Full report: report_{DATE}.md
```

---

## Image Generation

### When to Generate

Generate `message_{DATE}.png` only if image generation is available (i.e., `IMAGE_GEN_PROVIDER` is configured and not `none`). If unavailable, skip image generation and produce text only.

### Image Specifications

| Property | Value |
|----------|-------|
| Aspect Ratio | 9:16 portrait |
| Layout | Single-column vertical card stack |
| Cards | One card per item, compact format |
| Card Content | Emoji marker + bold title + one-line summary |
| Style | From `MESSAGE_IMAGE_STYLE` or `IMAGE_STYLE` config |

### Image Prompt Template

```
9:16 portrait infographic, {HEADER_TEXT} {YYYY-MM-DD}, ALL text content in {LANG}.
Purpose: Compact message digest for mobile sharing on messaging apps.

Total news items: {N}

News cards (display EXACTLY {N} cards, compact vertical layout):

Card 1: {emoji} {Entity name} {Event description}
- {One-line summary with key metrics}

Card 2: {emoji} {Entity name} {Event description}
- {One-line summary with key metrics}

(... list all {N} items ...)

CRITICAL RULES:
- ALL text on this image MUST be in {LANG}
- Entity names are proper nouns (OpenAI, DeepSeek, Cursor) — keep as-is, do NOT translate
- Each card has: emoji marker + bold title + one-line summary (NOT multi-line bullets)
- Use 🔥 for top items, ⭐ for important items, 🔷 for regular items
- Compact single-column vertical stack — one card below another
- Title font: 18pt bold, summary font: 13pt regular
- Cards separated by thin divider or subtle spacing (12px)
- Card width fills 90% of image width
- Do NOT display score numbers, badges, or importance markers
- Do NOT invent items not listed
- Maximize content area — minimize decorative elements
- Header: "{HEADER_TEXT} {YYYY-MM-DD}" at top
- Footer: small gray text "Powered by MorningAI" at bottom
- Optimized for screenshot sharing in messaging apps

{STYLE_BLOCK}

Message digest layout adaptation:
- Single-column vertical stack (NOT grid layout)
- Each card: title line + summary line only (compact, no multi-line bullets)
- Tight vertical spacing between cards
- Clean, uncluttered, high information density
- Mobile-optimized: large enough text to read on phone screens
```

**Variable substitution:**
- `{HEADER_TEXT}`: See Language-Specific Headers table above
- `{LANG}`: "Chinese" for zh, "English" for en, "Japanese" for ja
- `{STYLE_BLOCK}`: Injected from existing style presets (see `skills/gen-infographic/scripts/styles.py`)

### Image Generation Method

Use the same methods as Step 4 (gen-infographic):

**Option A** — Native tool (if supported):
Generate using built-in image generation capability with the prompt above.

**Option B** — Python script:
```bash
cd {SKILL_DIR} && python3 skills/gen-infographic/scripts/gen_infographic.py --prompt "{prompt}" -o {CWD}/message_{YYYY-MM-DD}.png
```

---

## Workflow Summary

1. Check `MESSAGE_ENABLED=true` — skip if not enabled
2. Read `data_{DATE}.json` from the working directory
3. Read this specification and the digest template (`templates/digest.md`)
4. Select items: filter by score >= `MESSAGE_MIN_SCORE`, apply category balance (if enabled), sort desc, limit to `MESSAGE_MAX_ITEMS`
5. Generate text digest → write to `{CWD}/message_{DATE}.md`
6. If image generation available → build prompt from template, generate → `{CWD}/message_{DATE}.png`

---

## Example Output

```
MorningAI 2026-04-14

8 notable updates today

🔥 **Anthropic Releases Claude 4.5 Sonnet**
New mid-tier model with +18% SWE-Bench, 200K context, 40% faster output. Available via API and claude.ai.
🔗 https://x.com/AnthropicAI/status/example

⭐ **Google Gemini 2.5 Flash Enters Public Preview**
Flash-tier model with native multimodal reasoning, 1M context. Free tier on AI Studio.
🔗 https://x.com/GoogleDeepMind/status/example

⭐ **Cursor Background Agents Now Generally Available**
Autonomous background agents for multi-file refactoring, test generation, and PR creation. Max 10 concurrent on Pro.
🔗 https://cursor.com/changelog/background-agents-ga

⭐ **DeepSeek Open-Sources V3-0407 Model**
Updated V3 with 671B MoE architecture, MIT license. Weights available on HuggingFace.
🔗 https://github.com/deepseek-ai/DeepSeek-V3

⭐ **OpenAI Open-Sources Codex CLI**
Terminal-based coding agent with suggest, auto-edit, and full-auto modes. MIT license.
🔗 https://github.com/openai/codex

⭐ **LMSYS Chatbot Arena April Rankings Update**
Claude 4.5 Sonnet enters #2 overall (ELO 1287). Gemini 2.5 Pro holds #1 in coding.
🔗 https://lmarena.ai

⭐ **GitHub Copilot Coding Agent Public Preview**
Autonomous agent handles issues and creates PRs in secure cloud sandbox. Free for Pro+ and Enterprise.
🔗 https://github.blog/changelog/copilot-coding-agent

⭐ **Windsurf Raises $200M Series C at $3B Valuation**
Largest round in AI coding tools space. Plans to hire 200 engineers and expand enterprise features.
🔗 https://techcrunch.com/2026/04/07/windsurf-raises-200m

---
Powered by MorningAI | Full report: report_2026-04-14.md
```

---

## Notes

- The text digest reads from `data_{DATE}.json` directly — it does NOT depend on the report being generated first
- All summaries must be condensed to 1-2 sentences — prioritize explaining what the thing IS and why it matters, not popularity metrics (downloads, likes, stars)
- Entity names are always preserved as proper nouns regardless of language setting
- The image is optional — if no image generation provider is configured, only the text file is produced
- When `MESSAGE_LINKS=bottom`, the reference numbers are implicit (ordered by item appearance) — do NOT add `[1]` markers in the item body, and do NOT include `🔗` lines after each item
