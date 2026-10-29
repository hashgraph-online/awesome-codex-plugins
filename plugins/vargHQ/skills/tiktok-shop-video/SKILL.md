---
name: tiktok-shop-video
description: >-
  Turn a product link into a TikTok Shop video that sells and stays compliant. Writes the script
  and shot list for a shoppable or affiliate video in TikTok Shop's own styles (personal review,
  before & after, unboxing, tutorial, problem and fix in one clip), with the product visible from
  the first frame, one specific number in the demo and a cart CTA, and enforces the 2025–2026 Shop
  rules that kill reach and accounts: a real person on screen, no AI voice as the presenter, no
  still-image slideshows (at least 3 s of moving footage), no price or deal that differs from the
  product page, no exaggerated claims or weight before/after, commercial sounds only, no
  near-duplicate reposts. Uses AI only for b-roll and product shots. Use when someone makes TikTok
  Shop videos as a seller or affiliate, asks why Shop videos stall at 200 views or got a
  violation, or wants Shop content plans. NOT for paid TikTok or Meta ads with AI actors (use
  ai-ugc-ad-video) or for editing existing footage (use ecommerce-video-edit).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  varg.cost.typical: "free for scripts; ~40–300 credits per video for AI b-roll (estimate)"
  varg.cost.estimate_tool: "varg:estimate_cost"
  varg.runtime.typical: "15–40 min"
  varg.models: "nano_banana_2_1, bria_fibo_edit_1_5_product_holding, kling_v4, seedance_2_5, ffmpeg"
  varg.outputs: "script + shot list (markdown), mp4 9:16"
  openclaw:
    requires:
      anyBins:
        - curl
    homepage: https://varg.ai
compatibility: >-
  Scripts and shot lists need nothing. AI b-roll needs the varg MCP (https://mcp.varg.ai/mcp) or
  VARG_API_KEY. Editing uses ffmpeg (see ecommerce-video-edit).
allowed-tools: Bash(curl:*) Bash(ffmpeg:*) Read Write Edit
---

# Turn a product link into a TikTok Shop video

TikTok Shop pays for videos that make people buy, and since 2025 it penalizes the cheap ways to make them. Most rules below come from Seller University documents behind a login, reported by trade press (ppc.land, BigSeller). Check Seller Center for your market before relying on a specific number.

## 1. The rules (read first)

| Do | Don't |
|---|---|
| A real person on screen: the seller, the creator, a face or at least their own voice | An AI voice or pre-recorded narration standing in for the presenter (banned) |
| At least 3 s of real moving footage, a real setting, camera movement | Still images, slideshows, looping images, product-page screenshots |
| The hook (first 3–6 s) ties to the product | Unrelated stunt hooks |
| Prices and deals only if they match the product page exactly and are live | "Under $20", "flash deal", "before it sells out" unless exactly true (one affiliate deleted a 500K-view video and 30 more after a violation) |
| Typical results; "helps", "results vary" | Weight-loss claims or hashtags, body before/after, "cures", impossible claims |
| TikTok's commercial sounds | Trending sounds from organic posts |
| Each video a distinct angle, hook or presence | Near-duplicate reposts; 5+ low-quality Shop videos in 7 days hides product links for a week |
| Adults lead demos | Minors selling, narrating or recommending |
| Video Pre-Check before posting; the AIGC label on AI b-roll | Unlabelled AI people |

AI is fine for product b-roll (macro shots, in-use scenes, ingredient bursts) under a real presenter. Six violations in 90 days can remove selling permissions.

## 2. Pick a style

TikTok Shop Academy's official styles, plus the structure that converts best:

| Style | Shape | Fits |
|---|---|---|
| Problem and fix in one clip | The problem, then the same scene fixed by the product; maximise the visual gap | Cleaning, organizing, phone accessories, tools |
| Personal review | The creator's own story with the product | Any; needs real use |
| Unboxing | Suspense → setup → value | Gifts, gadgets, beauty |
| Tutorial / how-to | Exactly how to use it and what it gets you | Beauty, kitchen, tools |
| Before & after | Typical results only | Beauty, cleaning (never weight) |
| Reply to a comment | Video reply to a real comment's question | Follow-ups after a video pops |

## 3. Script (18–35 s)

```
0:00–0:03  HOOK   Product in frame from the first frame + callout or payoff
                  "If your [problem], watch this."  Text overlay = same promise, ≤8 words
0:03–0:13  DEMO   The product doing its job, real hands, real place, ONE specific number
                  ("dries in 4 minutes", "holds 12 kg")
0:13–0:25  PROOF  The result on camera; a real review read as a review; what's in the box
0:25–end   CTA    "Tap the orange cart" / "tap the basket below"; no price unless it matches the PDP
```

Write every spoken line out. The presenter may ad-lib delivery; claims stay as written. Text ≤5–10 words per second, captions inside the safe zone.

## 4. Shot list for a phone shoot (give this to the person)

1. Hook shot: the problem or the payoff, product in frame, phone at chest height
2. Close-up in hand, label readable, slow turn
3. The product doing its job, 2 angles
4. The result, held for 2 s
5. Face to camera: one line of honest opinion and the CTA

Film in 2–3 real locations (car, kitchen, porch). A seller whose videos all came from one corner of a room saw flat engagement until they changed locations.

## 5. AI b-roll (optional, credits)

Quote with `estimate_cost`, wait for a yes. Every shot starts from the real product photo:
- Product in a scene: `nano_banana_2_1` (edit, real photo as reference); in a hand: `bria_fibo_edit_1_5_product_holding`
- 3–5 s clips: `kling_v4` (cheap, often right first time) or `seedance_2_5` (most real), slow camera, label spelled out in the prompt
- Reject any shot where the label, shape, colour or parts differ from the photo. Label it as AI-generated.

Details: `product-photo-to-video`.

## 6. After posting

- Judge by **orders per 1,000 views**, not views. 5M-view videos often convert under 0.1%; 100K–800K views with high engagement is the reported sweet spot. Saves are the strongest sales signal.
- When a video pops: days 2–3 answer the top comment questions, days 4–5 handle objections, days 6–7 post proof.
- Stuck at ~200 views: change the first 3 seconds and the format, not the hashtags; re-cut the same footage shorter (one coach went from 800 to 3,000+ views by re-cutting a 1-minute voiceover into 7 s).
- Scale a converting video with GMV Max (auto-select videos, include affiliate videos).

## Related

`ecommerce-video-ads` · `product-video-hooks` · `ecommerce-video-edit` · `product-photo-to-video`

Sources: [ppc.land, Shop quality rules](https://ppc.land/tiktok-shops-quality-rules-ban-ai-voices-and-still-images-from-lives/), [ppc.land, Shop content styles](https://ppc.land/tiktok-shops-shoppable-video-content-guide-tells-creators-what-actually-works/), [ppc.land, posting limits](https://ppc.land/tiktok-shops-tightening-grip-new-rules-that-could-freeze-your-account/), [BigSeller, repetitive content](https://www.bigseller.pro/blog/articleDetails/3766/tiktok-shop-policy-update-sept-2025.htm), [TikTok GMV Max](https://ads.tiktok.com/help/article/best-practices-for-product-gmv-max?lang=en), [@ugctiamarie](https://x.com/ugctiamarie/status/2099871041661157549), [@KyndhalUGC](https://x.com/KyndhalUGC/status/1717309503396298811).
