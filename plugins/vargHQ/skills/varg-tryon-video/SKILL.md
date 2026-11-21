---
name: varg-tryon-video
description: >-
  Turns a flat-lay or product photo of clothing into a try-on video on varg: clean the garment
  photo, dress a model photo in it with Bria Virtual Try-On (or a Nano Banana / GPT Image edit for
  harder garments), keep the same model across shots, then animate fit-check motions that sell
  clothes (slow turn, tug and let fall, walk to camera, mirror selfie, fabric close-up) on Kling 4
  or Seedance 2.5 with the garment kept intact, and add size captions so the fit is honest. Use
  when a fashion or apparel seller (Shopify, TikTok Shop, Amazon, dropshipping) asks for a try-on
  video, "my clothes on a model", an AI model wearing their product, a fit-check or outfit video,
  a try-on haul, or virtual try-on from flat-lays. Not for accessories that need no body (use
  product-photo-to-video) or for consistent characters across a story (varg-character-design).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  openclaw:
    requires:
      anyBins:
        - curl
    homepage: https://varg.ai/how-to
compatibility: >-
  Needs a VARG_API_KEY with curl (see the varg-ai skill) or the varg MCP connection
  (https://mcp.varg.ai/mcp). ffmpeg to cut and caption the final ad.
allowed-tools: Bash(curl:*) Bash(jq:*) Bash(ffmpeg:*) Bash(ffprobe:*) Read Write Edit
---

# Flat-lay to try-on video

Open-source try-on models (OOTDiffusion, IDM-VTON, CatVTON) make stills and most carry research licences; nobody ships a clean video path. On varg it is two steps: a try-on still, then image-to-video with fit-check motion. Fit causes about half of apparel returns, so the video must show the real drape and say the size.

## 1. Clean the inputs

- **Garment:** flat-lay or ghost-mannequin photo, 1000 px or more (resolution is the biggest quality factor), tags and measurement labels removed (the model reads them as print). Write a **garment-truth caption** of only what is visible: fabric, colours, print or stripe pattern, buttons, pockets, logo text and position, hem length.
- **Model:** a full-body photo (head to shoes, arms relaxed, plain room), a generated one or a consenting real person. Keep one model per product line; for more shots, make a 4-view sheet (front, 45°, side, close-up) with `varg-character-design`.

## 2. Dress the model (still)

```bash
curl -s -X POST https://api.varg.ai/v2/image -H "Authorization: Bearer $VARG_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"bria_fibo_edit_1_5_virtual_try_on","files":[{"url":"MODEL_URL"},{"url":"GARMENT_URL"}],
       "prompt":"Dress the woman in the cardigan from the second image, worn open over her white t-shirt. Keep her face, hair, pose, jeans, sneakers and the room unchanged."}'
```

4 credits. For two garments or accessories, add up to three garment images. For prints, logos or embroidery Bria softens, try `nano_banana_2_1` or `gpt_image_2_5` with both images and: "preserve all visible text, graphics, prints and seams; do not add text, logos or accessories; full body, hem visible" ([test notes](https://suzuki-shoten.pages.dev/blog/metafit-genai-part2)). Compare against the garment-truth caption before animating.

## 3. Animate fit-check motions

One motion per 5 s clip, camera locked, full body and hem in frame, hands away from the print:

| Motion | Prompt core |
|---|---|
| Turn | "turns slowly 90 degrees to show the side, pauses, turns back" |
| Tug and fall | "lightly tugs both front edges and lets go so it falls open naturally" |
| Walk to camera | "walks three steps toward the camera, fabric moves with weight" |
| Mirror selfie | "phone mirror selfie, shifts weight, checks the back in the mirror" |
| Detail | "close-up: fingers pinch the knit at the cuff, slow pan across the texture" |

```
Fashion fit-check video, phone on a tripod, camera locked, full body and the hem always in frame.
<motion>. Hands stay away from the front panel. <fabric> moves with weight; <pattern, buttons, logo>
stay exactly the same. Natural window light, realistic iPhone footage, no text.
```

`kling_v4` (79 credits per 5 s, 720p) held the stripes and buttons in our test; `seedance_2_5` adds references (pass the garment as `@image2`) when Kling drifts. Cut 3–4 clips into a 15 s ad with a voiceover or music and captions.

## 4. Honest fit and labels

- Caption the size: "Model 170 cm, wears M". Offer 2–3 body types for bestsellers.
- Show realistic drape; don't let the model slim or reshape the body.
- AI model = AI label on TikTok and Meta; in ads reaching New York, a visible synthetic-performer disclosure (`ai-ad-compliance-check`). Never use a real person's likeness without consent.

## Failure modes

Logo or micro-print melts in motion → slower motion, add a static close-up, or drop that shot. Hands on the garment → the hidden part is redrawn. Hem or length drifts → "full body and hem in frame". Colour flicker → name the exact colours. Face drift → one model photo per product, 4-view sheet for series.

## Tested

2026-10-28: a cream cardigan with navy stripes and pearl buttons (flat-lay from `nano_banana_2_1`) on a full-body model photo. `bria_fibo_edit_1_5_virtual_try_on` dressed her in one call (4 credits), keeping face, room, jeans and the stripes; it dropped the two patch pockets. `kling_v4` fit check, 5 s (79 credits): she turns to the side, turns back, tugs the cardigan open; stripes and buttons held. https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_1213e32adbda.mp4

## Related skills

`varg-character-design` (a model who stays the same), `varg-product-lock` (garment details as references), `ai-ad-compliance-check`, `varg-ad-variants` (one per body type or colour), `varg-ai`.
