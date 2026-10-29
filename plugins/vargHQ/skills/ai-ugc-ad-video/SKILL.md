---
name: ai-ugc-ad-video
description: >-
  Open-source alternative to Arcads: AI UGC ads with an AI actor holding your real product. Casts a
  creator whose age matches the claim in the room where the problem happens, writes a phone-real
  script (a yapper, unboxing, street interview or in-car take) with every line in the prompt, locks
  the face, the voice and the product label across shots, prompts camera flaws and breaths so it
  doesn't look waxy, generates on Seedance 2.5, Kling 4 or Creatify through varg, and labels it.
  It never puts a first-person testimonial or result in an AI mouth (FTC rule) and never targets
  TikTok Shop presenters (AI voices banned there). Use when someone wants AI UGC ads, an AI
  creator or actor talking about their product, Arcads/Creatify/MakeUGC-style ads, or UGC without
  hiring creators. NOT for TikTok Shop affiliate videos (use tiktok-shop-video), product-only
  shots with no person (use product-photo-to-video), or the same characters across a multi-scene
  story (use varg-consistent-characters).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  varg.cost.typical: "~120–600 credits per finished 15 s ad including retakes (estimate)"
  varg.cost.estimate_tool: "varg:estimate_cost"
  varg.runtime.typical: "20–45 min"
  varg.models: "gpt_image_2_5, nano_banana_2_1, seedance_2_5, kling_v4, kling_v4_flash, creatify_boreal, eleven_v4, sync_v3, ffmpeg"
  varg.outputs: "mp4 9:16 1080x1920"
  openclaw:
    requires:
      env:
        - VARG_API_KEY
    primaryEnv: VARG_API_KEY
    homepage: https://varg.ai
compatibility: >-
  Needs the varg MCP connection (https://mcp.varg.ai/mcp) or a VARG_API_KEY with curl (see the
  varg-ai skill). Editing uses ffmpeg locally or the varg ffmpeg tool.
allowed-tools: Bash(curl:*) Bash(ffmpeg:*) Bash(ffprobe:*) Read Write Edit
---

# Open-source alternative to Arcads: AI UGC ads

An AI creator talks to camera about your product, holds it, uses it, and sounds like a person filming themselves. Generation runs on varg: the MCP (`call_tool`) or `POST https://api.varg.ai/v2/tools/{image|video|speech}/call`. Quote credits only, from `estimate_cost`, and wait for a yes before spending.

**What the data says:** in one operator's $100K test (220 videos), human UGC had the higher CTR and AI the higher ROAS, because AI made more variants cheaply. AI works for cold traffic, low-trust products and finding the winning angle; it is weak for high-ticket offers and warm audiences. The script matters more than whether the face is real. Use AI to find the angle, then consider remaking the winner with a real creator.

## 0. Gates

1. **Where does it run?** Meta ads and TikTok ads: OK, labelled. TikTok Shop video: stop and use `tiktok-shop-video` (AI voices as presenter and AI-made material are against Shop rules).
2. **Claims:** the AI creator may **demo and state facts**. Never write "I used it for two weeks and…", before/after results, or "my skin cleared". The FTC bans fake testimonials, AI ones included (~$51,744 per violation); New York requires a synthetic-performer disclosure in ads. Real reviews may be quoted as reviews ("2,100 reviews say…").
3. **Product photo:** clean, straight-on, label readable. "If the label isn't readable in the reference, the model invents its own text. That's where most people's ads die."
4. **Cost:** quote the full batch with `estimate_cost` (assume ~3 takes per usable Seedance clip, ~1–2 for Kling 4).

## 1. Cast the creator

- **Age matches the claim**, written as a number ("54-year-old woman"); **room matches the problem** (energy = kitchen at 6 am, sleep = bedroom lights off, bloating = bathroom mirror, joints = stairs, private = car).
- Real skin: "freckles, visible pores, a small blemish near the jaw, flyaway hairs, no retouching, no skin smoothing".
- One outfit with one specific detail ("collar slightly crooked, sleeves pushed up").
- Generate the creator still with `gpt_image_2_5` or `nano_banana_2_1`: "iPhone selfie photo, slightly below eye level, phone at arm's length…". Pick one, then make an identity sheet (front, ¾, side, expressions) and reuse the same image on every shot. Deeper casting: `varg-character-design`.

## 2. Pick the format

| Format | Shape | Notes |
|---|---|---|
| Yapper | 30–60 s to camera, a story; product named as the fix after ~35 s | The 2026 workhorse; do the jump cuts by hand (cut on a blink) |
| End-of-day vlog | 15 s, low energy, product beside the face | Template in [references/prompts.md](references/prompts.md) P1 |
| Unboxing / in-hand demo | Product by second 2 | Highest hit-rate format on Meta |
| Street interview | The question hooks; no product for ~15 s | Feed each finished clip back as the reference for the next |
| In-car | Private, unscripted | "The cheapest to render well" |
| Podcast clip | Host + guest | Use `varg-podcast-video` |

## 3. Write the script into the prompt

Every spoken line goes in the video prompt, with timings. Under ~85 words for 30 s. Open on the most embarrassing version of the problem, or mid-motion with a throwaway line ("Okay. Last thing, then bed."). Add written-in stumbles. End on one CTA.

## 4. Generate shot by shot

For each beat (≤5 s, or one 15 s Seedance take):

```
Seedance 2.5 / Kling 4 inputs:
  image 1 = the creator still (identity)
  image 2 = the product photo (label readable)
  prompt  = TALENT / PRODUCT (label text spelled out in order) / LOCATION / LIGHTING (one condition)
            / FRAMING / beats with dialogue / PERFORMANCE / CAMERA CHARACTER / POSITIVE LOCKS
```

- `seedance_2_5`: the most real; reported ~3 attempts per keeper. `kling_v4`: cheaper, often right first time. Draft on `kling_v4_flash`.
- `creatify_boreal`: a product presenter with synced speech in one call, when speed matters more than control.
- Voice: native audio from the video model, or `eleven_v4` + `sync_v3` lip-sync. Give the model the voice file **and the exact transcript**, or it stretches the speech to fit the motion.
- **Locks:** same face, wardrobe, product, room and light on every beat; "exactly two arms and two hands, one hand always holding the phone"; no model-hopping between shots of one creator.
- **Realism:** handheld tremor, autofocus hunts, rolling shutter, sensor noise, mild wide-angle distortion at arm's length; a breath or a swallow between lines; phone-mic audio; no music, no captions in generation.

Full prompts (realistic skincare UGC, camcorder vlog, street interview chain, Creatify JSON): [references/prompts.md](references/prompts.md).

## 5. Reject pass

Before anything reaches the edit, compare each clip with the references: face (jaw, freckles, hair), label text letter by letter, product shape and colour, hand count, lip-sync drift. Regenerate failures; don't fix them with captions.

## 6. Edit and label

- Assemble with `ecommerce-video-edit`: hook first, cut dead air (human jump cuts), captions in the safe zone, one CTA, -14 LUFS, one MP4 per hook.
- Label: TikTok's AIGC toggle (it resets on duplicated campaigns) or an on-screen "AI-generated"; Meta adds "AI info" itself; keep generation logs.
- Variants: a different buyer, angle or format, not 10 avatars reading one script (`ad-creative-testing`).

## Related

`ecommerce-video-ads` · `product-video-hooks` · `varg-character-design` · `varg-consistent-characters` · `varg-podcast-video` · `ecommerce-video-edit`

Sources: [r/FacebookAds $100K test](https://reddit.sentinel-team.org/posts/1rlvjrg/snapshots/2026-03-05T23%3A31%3A13.407127Z), [FTC rule](https://www.ftc.gov/news-events/news/press-releases/2024/08/federal-trade-commission-announces-final-rule-banning-fake-reviews-testimonials), [TikTok AI policy](https://ads.tiktok.com/help/article/tiktok-ads-policy-misleading-and-false-content), [@abxxai realistic UGC thread](https://x.com/abxxai/status/2095179656802844727), [@CEO_Vlad](https://x.com/CEO_Vlad/status/2113238974957486375), [@YourAlphaMom Seedance vs Kling test](https://x.com/YourAlphaMom/status/2115191029641175400), [@mikefutia street interview](https://x.com/mikefutia/status/2081842993557127634).
