---
slug: muapi-product-campaign
name: muapi-product-campaign
version: "1.0.0"
description: Generate a full multi-channel product campaign — hero visuals, social media assets, short ad video, and platform-specific crops for an end-to-end launch campaign.
acceptLicenseTerms: true
---


# Product Campaign Pack

**Generate a full multi-channel product campaign — hero visuals, social media assets, short ad video, and platform-specific crops for an end-to-end launch campaign.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `product_name` | text | yes | — | The product being launched or promoted (e.g. "Nova Pro Wireless Earbuds"). |
| `campaign_message` | text | yes | — | Core campaign message or tagline (e.g. "Sound That Moves You", "Clean Beauty. Real Results."). |
| `target_audience` | text | yes | — | Who the campaign targets (e.g. "tech enthusiasts 18-35", "wellness-focused women 28-45"). |
| `visual_style` | text | no | modern, cinematic, premium | Campaign visual direction (e.g. "bold and vibrant", "soft pastel minimal", "dark luxury editorial"). |
| `product_image` | image_url | no | — | Optional product reference image. |


## Steps

This is a full-scale campaign. Submit a SINGLE the plan with all phases running in parallel.

### Phase A — Campaign Hero (2 assets)

1. **Hero still image** — If `{{product_image}}` provided, use `muapi image edit` (model=`nano-banana-pro-edit`); else `muapi image generate` (model=`nano-banana-pro`):
   - Prompt: `{{campaign_message}} — hero campaign image for {{product_name}}. {{visual_style}} style. Bold composition, product as centerpiece, dramatic lighting. {{target_audience}} aspirational lifestyle. Full-bleed editorial campaign photography. Clean, award-winning advertising quality.`
   - Aspect ratio: 16:9

2. **Square social hero** — `muapi image edit` (model=`bytedance-seedream-v4.5-edit`) using output of step 1:
   - Prompt: `Reframe and optimize for square social media feed format. Keep {{product_name}} centered and dominant. {{visual_style}}, maintain campaign energy. Crop tightly for maximum impact.`
   - Aspect ratio: 1:1

### Phase B — Campaign Video

3. **Short ad video** — If `{{product_image}}` provided, use `muapi video generate` (model=`kling-v3.0-pro-image-to-video`); else `muapi video generate` (model=`veo3.1-text-to-video`):
   - Prompt: `{{campaign_message}} — product campaign video for {{product_name}}. {{visual_style}} cinematic style. Dynamic reveal, product hero moment, {{target_audience}} lifestyle context. Professional commercial grade, 4K quality, smooth camera motion.`
   - Aspect ratio: 16:9, 8-10 seconds

### Phase C — Platform Crops (Parallel)

4. **Instagram Story / Reels format** — `muapi image edit` (model=`flux-kontext-pro-i2i`) from step 1 output:
   - Prompt: `Reframe campaign image for 9:16 vertical Story/Reels format. Top area clear for text overlay. Product and campaign energy preserved. {{visual_style}}.`
   - Aspect ratio: 9:16

5. **LinkedIn / Email banner** — `muapi image edit` (model=`flux-kontext-pro-i2i`) from step 1 output:
   - Prompt: `Reframe for wide email header or LinkedIn banner. 3:1 ultra-wide crop. Product left-aligned, right side clear for headline text. Professional campaign feel.`
   - Aspect ratio: 3:1

After generation:
- Present all assets as a cohesive campaign set
- Suggest adding a voiceover to the campaign video with `minimax-speech-2.6-hd`
- Offer a full `social-pack` skill run for additional platform variations

## Notes
- All phases reference the same product and visual DNA for campaign consistency.
- For beauty/fashion, use `ai-product-shot` for the hero instead of `nano-banana-pro`.
- The campaign video should feel like a 6-second premium ad, not a demo.

## Trigger Keywords

`product campaign`, `campaign`, `launch campaign`, `product launch`, `marketing campaign`, `brand campaign`, `full campaign`, `campaign assets`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
