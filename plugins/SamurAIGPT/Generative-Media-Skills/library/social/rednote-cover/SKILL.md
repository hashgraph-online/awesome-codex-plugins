---
slug: muapi-rednote-cover
name: muapi-rednote-cover
version: "1.0.0"
description: Create a Xiaohongshu (RedNote/小红书) style cover image — vibrant, lifestyle-focused, with aesthetic typography overlay suitable for the Chinese social platform.
acceptLicenseTerms: true
---


# RedNote Cover

**Create a Xiaohongshu (RedNote/小红书) style cover image — vibrant, lifestyle-focused, with aesthetic typography overlay suitable for the Chinese social platform.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `topic` | text | yes | — | The post topic (e.g. "morning skincare routine", "cozy café study vlog", "ootd autumn fashion"). |
| `style` | text | no | aesthetic, warm tones, lifestyle photography | Visual style (e.g. "minimalist Korean aesthetic", "cottagecore", "dark moody luxe", "bright Taiwanese street style"). |
| `text_overlay` | text | no | — | Optional Chinese or English text to appear in the cover design (e.g. "今日穿搭✨" or "Morning Glow"). |
| `orientation` | text | no | portrait | Image orientation — "portrait" (3:4) for feed, "square" (1:1) for grid. |
| `reference_image` | image_url | no | — | Optional reference photo of the subject or product. |


## Steps

### Phase A — Cover Image

Submit the plan with ONE or TWO steps:

1. **Cover image** — If `{{reference_image}}` is provided, use `muapi image edit` (model=`bytedance-seedream-v4.5-edit`); otherwise use `muapi image generate` (model=`bytedance-seedream-v4.5`).
   - Prompt: `Xiaohongshu (RedNote/小红书) style cover photo for {{topic}} post. {{style}}. Aesthetic lifestyle photography, soft natural lighting, visually appealing composition, clean and airy feel. High engagement social media cover, editorial quality. Platform optimized for Chinese lifestyle app.`
   - If `{{text_overlay}}` is provided, append: `Include elegant text overlay saying "{{text_overlay}}" in a stylish font, placed at top or bottom third of image.`
   - Aspect ratio: `3:4` if orientation is portrait, `1:1` if square

After generation, present the cover and offer:
- A set of 3 variations with different color moods (warm / cool / neutral)
- A carousel set (3 images for a RedNote carousel post)
- Upscaling for print/export quality

## Notes
- RedNote covers perform best with: soft bokeh backgrounds, centered subjects, warm or pastel tones, and clear visual hierarchy.
- If topic is fashion/outfit, suggest `ugc-lifestyle-try-on` skill for wearable product shots.
- Korean/Japanese aesthetic filters (soft, matte, film grain) trend highly on the platform.

## Trigger Keywords

`rednote`, `xiaohongshu`, `小红书`, `red note`, `rednote cover`, `xhs cover`, `chinese social`, `lifestyle cover`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
