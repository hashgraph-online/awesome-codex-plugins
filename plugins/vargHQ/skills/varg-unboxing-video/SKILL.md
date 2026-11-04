---
name: varg-unboxing-video
description: >-
  Turns product photos into an unboxing or ASMR video ad on varg: hands-only, top-down or POV,
  the box tapped, opened and the product lifted out and switched on, with native ASMR sound
  (taps, crinkle, lid pop) and no music, in timed VISUAL / ACTION / SOUND blocks on Seedance 2.5
  with the box and the product as references. Unboxing has the highest winner rate of any Meta ad
  format (9.8%, Motion 2026) while only 2.1% of ads use it. Use when a seller (TikTok Shop,
  Shopify, dropshipping, Amazon) asks for an unboxing video, an ASMR or satisfying product video,
  "open the box" content, a packaging reveal, or a hands-only product demo made from photos. Not
  for talking-head UGC (use ai-ugc-ad-video), the full 60 s guide reel (varg-dropship-reel) or a
  studio spin of the product alone (product-photo-to-video).
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
  (https://mcp.varg.ai/mcp). Optional: ffmpeg to layer extra sound effects.
allowed-tools: Bash(curl:*) Bash(jq:*) Bash(ffmpeg:*) Bash(ffprobe:*) Read Write Edit
---

# Unboxing and ASMR product video

Two photos in (the closed packaging and the product), a 10-second hands-only unboxing out: taps on the lid, the lid lifting off, the product in its tray, lifted out and switched on, with native ASMR sound and no music. In Motion's 2026 benchmark of 578,750 Meta ads, unboxing had the highest hit rate of any format (9.8%, spend-use ratio 1.3), yet only 2.1% of creatives use it ([runneth/Motion](https://runneth.com/library/research/creative-benchmarks-2026/top-visual-formats)).

Generation runs on varg: REST `https://api.varg.ai/v2` (the `varg-ai` skill) or the MCP server `https://mcp.varg.ai/mcp` (`call_tool`, `get_job`, `estimate_cost`). Price every clip first with `POST /v2/estimate` or `estimate_cost`.

## 1. Ask, then go

- **Photos:** the product (white background, ≥1000 px) and the closed packaging. No box? Make one: `nano_banana_2_1` with the product photo, "a closed premium retail box for this product, lift-off lid, the product photo printed on the front, on a light oak table". Tested: one call, 5 credits.
- **Opening:** lift-off lid (most reliable), magnetic flap, sleeve, tissue wrap. Avoid tape cutting: box physics and blades break most often.
- **Style:** hands-only ASMR top-down (default), cozy POV on a bed or sofa, or luxury macro on marble.
- **Length:** 5 s teaser (tap + reveal), 10 s standard, 15 s with first use.

## 2. The prompt: timed blocks, references by role

Name what each image is, never re-describe the product (the reference does that), and give every 2–4 s block a VISUAL, an ACTION and a SOUND. Add "slow, careful, pause" to every action: jerky hands are the most common failure ([Floyo's Seedance ASMR template](https://floyo.ai/workflows/seedance-2-0-asmr-unboxing-reference-4v78z8v47k8z)).

```
Vertical ASMR unboxing, hands only, no face, top-down camera on a light oak table, soft window light.
@image1 is the exact retail box, @image2 is the exact product inside; never change their shape,
colors or printing.
0-3s VISUAL: the closed box from @image1 already in frame, two hands rest on it. ACTION: fingertips
tap the lid three times, slow, careful. SOUND: hollow cardboard taps.
3-6s VISUAL: the lid lifts off slowly. ACTION: one hand holds the base, the other lifts the lid and
sets it aside, brief hold. SOUND: soft paper slide, lid suction pop.
6-10s VISUAL: the product from @image2 rests in a white tray; a hand lifts it out and turns it slowly
toward the camera, then presses the button and it switches on. SOUND: tissue crinkle, plastic click.
No music. Pure organic ASMR soundscape. No speech, no text, no subtitles.
```

```bash
curl -s -X POST https://api.varg.ai/v2/video -H "Authorization: Bearer $VARG_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"seedance_2_5","prompt":"<the prompt above>","files":[{"url":"BOX_URL"},{"url":"PRODUCT_URL"}],
       "aspect_ratio":"9:16","resolution":"720p","duration":10,"audio":true}'
```

Variants of the SOUND line that read well: "heavy glass-on-marble placement, fingernail taps, magnetic lid snap, foil seal peel-pop" (luxury); "fabric rustle, zipper, soft thud on a duvet" (cozy). Keep to about five named sounds per clip.

## 3. Shot order that sells

Start mid-open (hands already on the box), break the seal in one continuous shot, show the first look inside, lift the product out, show its size in the hand, end on first use (it lights up, clicks, pours). Or open on the payoff and cut back to the box ([influee](https://influee.co/ch/blog/unboxing-video-ad-angle)). Cut a 15 s ad and a 30–60 s long version from 2–3 clips.

## 4. Check before you use it

- The box and the product match the photos (printing, colors, shape). If the product drifts, use `varg-product-lock`.
- Five fingers per hand; the grip is on a plain face of the product, never across the logo.
- Native close-up foley (crinkle, click) is weaker than ambience. If it sounds thin, layer real effects in the edit: `ffmpeg -i video.mp4 -i crinkle.wav -filter_complex "[1:a]adelay=6200|6200,volume=0.8[s];[0:a][s]amix=inputs=2:normalize=0" -c:v copy out.mp4`.
- A label the viewer must read: use the real product photo with a slow push-in for that shot, not a generated close-up.

## Tested

2026-10-28, LED pet nail clipper: box made with `nano_banana_2_1` from the product photo (5 credits), then the prompt above on `seedance_2_5`, 10 s, 720p, audio on: 385 credits. The box stayed printed as the reference, the lid lifted cleanly, the clipper came out of its tray matching the photo, and the sound is taps and paper with no music. https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_942e9a6efa1c.mp4

## Rules

- Hands only, or label AI people as AI where the platform asks (TikTok, Meta).
- Show what the product really does and what is really in the box: TikTok Shop's AI rules forbid changing the quantity, adding accessories or showing effects the product can't deliver (check with `ai-ad-compliance-check`).

## Related skills

`varg-product-lock` (keep the product identical), `varg-product-hook` (other hook types), `varg-ad-variants` (put the unboxing in front of a winning ad), `product-photo-to-video` (studio product motion), `varg-ai` (models and prices).
