---
slug: muapi-ugc-lifestyle-try-on
name: muapi-ugc-lifestyle-try-on
version: "1.0.0"
description: Generate UGC-style (User Generated Content) lifestyle photos of a person wearing or using your product — authentic, relatable, social-media-native imagery.
acceptLicenseTerms: true
---


# UGC Lifestyle Try-On

**Generate UGC-style (User Generated Content) lifestyle photos of a person wearing or using your product — authentic, relatable, social-media-native imagery.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `product_name` | text | yes | — | The product to feature (e.g. "white oversized hoodie", "blue light blocking glasses", "leather crossbody bag"). |
| `product_image` | image_url | yes | — | Product image or photo URL to use as reference for the try-on. |
| `model_description` | text | no | woman, 25-30 years old, natural look, diverse | Description of the model (e.g. "man, athletic build, 20s", "woman, curvy, 30s, warm skin tone"). |
| `setting` | text | no | casual lifestyle, natural lighting | Scene and mood (e.g. "urban street style", "cozy home morning routine", "gym workout", "coffee shop"). |
| `platform` | text | no | instagram | Target platform — "instagram", "tiktok", "pinterest", "amazon". |


## Steps

Submit the plan with TWO steps:

### Step 1 — Outfit/Product Try-On

1. **Try-on generation** — `muapi image edit` (model=`ai-dress-change`) if product is wearable clothing, otherwise `muapi image edit` (model=`flux-kontext-pro-i2i`):
   - For clothing/wearables with `ai-dress-change`:
     - Product: `{{product_image}}`
     - Prompt: `{{model_description}} wearing the product naturally in a {{setting}} environment. Authentic UGC-style photo, candid pose, natural expression.`
   - For accessories/non-clothing with `flux-kontext-pro-i2i`:
     - Prompt: `{{model_description}} using/wearing {{product_name}} in a {{setting}}. The product from the reference image is clearly visible and featured. Natural UGC-style lifestyle photography, authentic candid feel.`
   - Aspect ratio: 4:5 for Instagram, 9:16 for TikTok, 2:3 for Pinterest

### Step 2 — UGC Lifestyle Variant

2. **Lifestyle context shot** — `muapi image edit` (model=`gpt4o-edit`) using the output from Step 1:
   - Prompt: `Make this look like authentic UGC content — add realistic environment context for {{setting}}, adjust lighting to feel natural and unposed, subtle film grain, candid photography style. Keep product {{product_name}} clearly visible and well-lit.`

After generation:
- Present both the try-on and lifestyle variant
- Offer to generate a 3-image carousel set with different poses/settings
- Suggest adding a short UGC-style video with `kling-v3.0-pro-image-to-video`

## Notes
- UGC performs best when it looks "accidental" — avoid overly polished or symmetrical compositions.
- For TikTok/Reels, suggest animating the best static shot into a video.
- For Amazon, refer back to the `amazon-product-listing` skill for white-background variants.

## Trigger Keywords

`ugc`, `try on`, `lifestyle photo`, `model wearing`, `outfit photo`, `wear product`, `user generated`, `ugc content`, `lifestyle try on`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
