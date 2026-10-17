---
slug: muapi-chibi-collage-effect
name: muapi-chibi-collage-effect
version: "1.0.0"
description: Turn a real lifestyle photo into a polished "chibi clone sticker diary" image — the original person stays photorealistic, surrounded by 5–8 kawaii chibi mini-clones, scrapbook doodles, and handwritten-style captions that match the scene.
acceptLicenseTerms: true
---


# Chibi Collage Effect

**Turn a real lifestyle photo into a polished "chibi clone sticker diary" image — the original person stays photorealistic, surrounded by 5–8 kawaii chibi mini-clones, scrapbook doodles, and handwritten-style captions that match the scene.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `person_image` | image_url | yes | — | A clear lifestyle photo of the person. Setting, outfit, mood, and activity are read from this image and drive the chibi poses and captions. |


## Steps

### Phase A — Chibi Collage Generation

If `{{person_image}}` is not provided, ask the user to upload a lifestyle photo (café, outdoor, cozy at home, travel, etc.). The scene context is what makes the chibi clones feel native to the moment, so a generic studio headshot will give weaker results than a real lifestyle shot.

Once the photo is available, submit the plan with ONE step to generate the chibi collage:

1. **Chibi Collage Generation** — `muapi image edit` (model=`gpt-image-2-image-to-image`):
   - Reference Image: `{{person_image}}`
   - Image size: `2160x3840` (9:16 portrait) — high-resolution social-media-ready output
   - Background: `auto`
   - Output format: `png`
   - Quality: `auto`
   - Moderation: `low`
   - Prompt:
     ```
     Create a high-quality "chibi clone sticker diary photo" based on the uploaded real-life image. Preserve the original person's identity, face, hairstyle, hair color, outfit, body proportions, pose, lighting, and background. Do not alter facial features or turn the subject into a full illustration—maintain a realistic photo look.
     Analyze the uploaded image carefully: identify the setting, mood, activity, clothing style, and overall vibe of the scene. Use this analysis to determine the theme of the chibi stickers, poses, emotions, and text phrases — everything should feel native to the actual moment captured in the photo.
     Add 5–8 chibi mini clones of the same person around the subject, designed in a consistent kawaii sticker style (big head, small body, large expressive eyes, clean digital finish). Each clone must clearly resemble the real person (same hair, outfit, colors).
     Design each chibi with different actions and emotions that are directly relevant to what the person is doing or feeling in the photo — inferred naturally from the scene (e.g. if they're at a café: sipping coffee, reading, daydreaming, chatting; if outdoors: exploring, laughing, taking photos; if cozy at home: cuddling, reading, relaxing). Ensure all poses are unique and contextually matched to the image.
     Render each chibi as a sticker with white outlines, soft shadows, and a slightly floating effect. Arrange them around the subject and edges without covering the face or main body.
     Add light hand-drawn doodles (hearts, sparkles, arrows, motion lines, circles, stars) in white with subtle pink accents, keeping a clean scrapbook diary feel. Doodle style should complement the mood of the scene.
     Include 5–8 short handwritten-style phrases that match the mood and context of the uploaded photo — cute, expressive, and scene-appropriate. Use mostly white text with slight pink highlights and small decorative marks.
     Composition: keep the real person as the central focus, surrounded by chibi stickers and doodles. The result should feel like a polished, playful, high-resolution social media lifestyle diary image — clean, balanced, and visually rich without clutter.
     ```

Present the generated chibi collage to the user. Suggest variations they can try: different source photos (travel, café, cozy-at-home), or asking to bias the captions toward a specific tone (cute, sassy, journal-style).

## Trigger Keywords

`chibi collage`, `chibi sticker diary`, `mini me stickers`, `kawaii clone collage`, `sticker diary photo`, `scrapbook chibi`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
- Source schema reference: `gpt-image-v2-edit` maps to `gpt-image-2-image-to-image` in the muapi catalog.
- The output is intentionally 9:16 (2160×3840) so it's ready for IG Stories / Reels / TikTok / YT Shorts without re-cropping.
