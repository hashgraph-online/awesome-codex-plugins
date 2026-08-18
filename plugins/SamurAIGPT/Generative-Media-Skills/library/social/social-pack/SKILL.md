---
slug: muapi-social-pack
name: muapi-social-pack
version: "1.0.0"
description: Re-render a hero image into Instagram, TikTok, YouTube-shorts and Twitter/X aspect ratios.
acceptLicenseTerms: true
---


# Social Media Pack

**Re-render a hero image into Instagram, TikTok, YouTube-shorts and Twitter/X aspect ratios.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `source_image` | image_url | yes | — | URL of the hero image (or asset_id from this session). |
| `caption_idea` | text | no | — | Optional caption / overlay direction (kept short). |
| `formats` | list | no | 1:1, 9:16, 4:5, 16:9 | Aspect ratios to produce. |


## Steps

Use the plan to fan out one node per format.

1. For each requested aspect ratio in `{{formats}}`:
   - Call `muapi image edit` (model=nano-banana-2-edit) with the source image.
   - Prompt: "Reframe the composition to {{aspect_ratio}} for social media.
     Keep the subject centred and uncropped. Match the original lighting
     and palette. {{caption_idea_hint}}".
   - Where `{{caption_idea_hint}}` = "Leave headroom at the top for a
     caption: '<caption_idea>'." (only if caption_idea is non-empty).
2. All formats run in parallel (no inter-node dependencies).
3. Return one asset id per format, labelled with the platform it suits:
   - 1:1   → Instagram feed
   - 9:16  → TikTok / IG Reels / YT Shorts
   - 4:5   → Instagram portrait
   - 16:9  → Twitter / X / YouTube
   - 21:9  → cinematic banner

## Notes
- Don't generate fresh images — only reframe / re-edit the source.
- If the source already matches a format, skip that node and surface the
  original asset id for it.

## Trigger Keywords

`social pack`, `resize for social`, `cross-post`, `multi-platform`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
