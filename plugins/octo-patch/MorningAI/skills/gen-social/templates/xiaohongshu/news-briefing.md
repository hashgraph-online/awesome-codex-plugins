---
platform: xiaohongshu
style: news-briefing
default_lang: zh
default_items: 5
min_score: 5
image_style: classic
image_lang: zh
---

## Constraints

- **Title**: ≤ 20 characters, compact and news-like
- **Body**: ≤ 1000 characters
- **Tags**: 5-10 hashtags at end of body, format: `#标签`
- **Images**: 3:4 portrait, carousel supported (3-6 images)
- **Emoji**: Minimal — only as section markers, keep professional tone

## Tone & Voice

- Concise, neutral, high information density — like a news briefing
- Objective and professional, NOT enthusiastic or personal
- Use framing like "今日速报" "快讯" "要点速览"
- Focus on facts and key numbers, not personal opinions
- Compact sentence structure, avoid filler words

## Content Structure

### Title
- Format: `{emoji} {compact phrase}` (≤ 20 chars)
- Emphasis on speed and authority
- Examples: "📰AI快讯｜5条要闻速览", "⚡今日AI要点速报", "🗞️AI日报｜重要更新"

### Body
1. **Date line** (1 short sentence) — "4月8日 AI 行业要闻速览👇"
2. **Bullet items** — compact, information-dense:
   - `{number}. {Entity}：{Event core}` (1 line)
   - `▸ {Key detail or number}` (1-2 sub-points max)
3. **Tags** — 5-10 relevant hashtags

### Body Format Rules
- Simple numbered list (1. 2. 3.)，NOT emoji numbers
- Each item ONE LINE for the headline, 1-2 lines for sub-points
- Use ▸ for sub-points
- NO excessive formatting, NO bold brackets【】
- Compact line spacing — density over readability
- Professional, factual — avoid "意味着" "值得关注" etc.

## Character Limit Rules

| Component | Budget |
|-----------|--------|
| Title | ≤ 20 chars |
| Date line | ~20-30 chars |
| Per item block | ~80-120 chars |
| Tags | ~100-150 chars |
| **Total body** | **≤ 1000 chars** |

## Image Style Rules

**Default: `classic` image style (can be overridden by channel config `image_style` field).**

Image prompt MUST include these classic-specific directives:
- Off-white background (#F5F5F0), clean editorial magazine layout
- Sans-serif typography, white card panels with subtle drop shadows
- Card-based layout with rounded corners (8px)
- Color palette: navy (#1B2A4A) titles, teal (#2A9D8F) bullet icons, slate gray (#4A5568) body text
- Structured, authoritative visual hierarchy
- Maximize content area with generous line spacing for mobile readability
- DO NOT include style labels or content-type annotations on the image

## Output Format

```
---xiaohongshu---

---title---
{emoji} {title text}

---body---
{compact news body}

#tag1 #tag2 #tag3 #tag4 #tag5

---images---
1: {image_filename}
2: {image_filename}
3: {image_filename}
4: {image_filename}
```

## Example Output

```
---xiaohongshu---

---title---
📰AI快讯｜5条要闻速览

---body---
4月8日 AI 行业要闻速览👇

1. Anthropic：Claude 4.5 Sonnet 发布
▸ 编程能力+18%，上下文200K，速度+40%

2. Google：Gemini 2.5 Flash 公测
▸ 100万上下文，AI Studio免费开放

3. DeepSeek：V3-0407 开源发布
▸ 671B MoE，MIT协议，性能接近GPT-4o

4. Cursor：后台Agent正式上线
▸ 无需盯屏，后台自动重构+提PR，Pro版10并发

5. Windsurf：C轮2亿美元
▸ 估值30亿，Insight Partners领投

#AI快讯 #人工智能 #Claude #Gemini #DeepSeek #Cursor #科技新闻 #AI日报 #大模型

---images---
1: social_2026-04-14_xhs_zixun_zh_1.png
2: social_2026-04-14_xhs_zixun_zh_2.png
3: social_2026-04-14_xhs_zixun_zh_3.png
4: social_2026-04-14_xhs_zixun_zh_4.png
```
