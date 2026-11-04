---
name: ecommerce-video-ads
description: >-
  Ecommerce video ad skills for Claude Code and AI agents: plans and makes short product videos that
  sell on TikTok, TikTok Shop, Instagram Reels and Meta ads, with AI or real footage. Asks the four
  questions that change the rules (where it runs, product facts, assets, budget), picks angle,
  hook, format and on-camera character, writes a second-by-second script, keeps the real product
  identical in AI shots, applies platform rules (AI labels, TikTok Shop bans on AI voices,
  slideshows and price mentions, the FTC fake-testimonial rule, music licensing), quotes cost
  before generating and plans different-concept variants. Use when someone wants a viral TikTok,
  Reels or TikTok Shop video for a product, ecommerce ad creatives or "10 ads for my product".
  Hands off to product-video-hooks, tiktok-shop-video, ai-ugc-ad-video, product-photo-to-video,
  ad-creative-testing and ecommerce-video-edit. NOT for app launch videos, music videos or brand
  films with nothing to sell.
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  varg.cost.typical: "~150–900 credits per finished 15–30 s ad (estimate)"
  varg.cost.estimate_tool: "varg:estimate_cost"
  varg.runtime.typical: "20–60 min"
  varg.models: "nano_banana_2_1, gpt_image_2_5, seedance_2_5, kling_v4, kling_v4_flash, veo_3_1, creatify_boreal, eleven_v4, sync_v3, ffmpeg"
  varg.outputs: "mp4 9:16 1080x1920, mp4 4:5"
  openclaw:
    requires:
      env:
        - VARG_API_KEY
    primaryEnv: VARG_API_KEY
    homepage: https://varg.ai
compatibility: >-
  Planning, scripts and checks need nothing. Generation needs the varg MCP connection
  (https://mcp.varg.ai/mcp) or a VARG_API_KEY with curl (see the varg-ai skill). Editing uses
  ffmpeg locally or the varg ffmpeg tool.
allowed-tools: Bash(curl:*) Bash(ffmpeg:*) Bash(ffprobe:*) Read Write Edit
---

# Ecommerce video ads with AI agents

Make short product videos that stop the scroll and sell: TikTok, TikTok Shop, Instagram Reels and Meta ads. This skill is the plan and the rules. The sibling skills do each part.

**Cost gate.** Nothing is generated before the person has seen an estimate (`estimate_cost` on the varg MCP, or `POST /v2/estimate`) and said yes. Quote credits (1 credit = 1 cent). Draft cheap first: stills, `kling_v4_flash` or `seedance_2_fast_preview`, 480–720p. Spend on full models only for concepts the person approved.

## 1. Ask four questions, default the rest

Agents fail here in both directions: a wall of 15 questions, or invented product facts. Ask exactly these, in one message, then state what you assumed for everything else:

1. **Where does it run?** TikTok Shop video, TikTok ad (Spark or in-feed), organic TikTok/Reels, or a Meta ad. This one answer changes the rules on AI voices, prices on screen, music and labels (§4).
2. **What is true about the product?** Name, what it does, the one claim they can prove, the price and the live offer. Never invent specs, prices, reviews or results.
3. **What do you have?** Product photos (clean, front-on, label readable), any real footage (even 5 s), your face or voice, real reviews, a winning ad to build on.
4. **Budget?** Per video, or for the whole test batch.

Defaults when unanswered: 9:16 1080×1920, 15–25 s, hook in the first 2 s, burned-in captions, licensed music or none, AI people labelled, 3 different concepts.

## 2. Pick the angle before the hook

An angle = **buyer × problem × promise**. Mine it from the buyer's own words (reviews, comments, Reddit), not from adjectives. Write one line per angle: "Women 50+ whose knees crack on the stairs → a sleeve that lets them climb without thinking". Then:

- **Match the face to the claim:** "you cannot use a 22-year-old to sell joint support".
- **Match the room to the problem:** energy = kitchen at 6 am; sleep = dark bedroom; bloating = bathroom mirror; joints = halfway up the stairs; anything private = the car.
- **Run every awareness stage:** unaware (a big win or an unnamed fear), problem-aware (name it, then the fix), solution-aware (us vs them), product-aware (objections, reviews), most-aware (the offer).

Details and casting by category: [references/characters.md](references/characters.md).

## 3. Hook, format, structure

**Hook (0–3 s):** the product or the result on screen, the promise said out loud and written as text, all three agreeing. TikTok: value in 3 s, hook done by 6 s (90% of ad recall happens in the first 6 s). Meta: brand and message within 5 s gives 1.7× the purchase intent, and a hook in both picture and sound gives 1.5×. The hook must lead into the product. Bank of 60+ openers by type: `product-video-hooks`.

**Format:** choose from [references/formats.md](references/formats.md). Start with what wins most often: **unboxing** (9.8% hit rate on Meta, yet only 2% of what brands make), **hands-on demo** (8.1%), problem and fix in one clip (the top TikTok Shop structure), yapper (one person talking to camera, unpolished), street interview, podcast clip, us vs them on ONE attribute.

**Structure (15–30 s):**

| Time | Beat | On screen |
|---|---|---|
| 0–3 s | Hook | Product or result in frame from the first second, line spoken + written |
| 3–6 s | Bridge | The hook turns into the product: "this is why…" |
| 6–20 s | Demo | The product working in a real setting, shown more than once, 1–3 benefits, one specific number |
| 20–26 s | Proof | A real review, a real result, a count ("2,100 reviews") |
| last 3–4 s | CTA | One action, said and shown ("tap the orange cart") |

Meta's Reels study (Meta + Toluna) behind this order: listing benefits 5.3×, brand on screen under 25% of the runtime 4.8×, product shown more than once 2.7×, native elements such as emoji 2.5×, speech plus music 2.1×, a spoken or on-screen CTA 1.9×. Text on screen: at most 5–10 words per second. Long education ads (90 s to 2 min) can carry big budgets, but the product must appear before the halfway point. More: [references/structure.md](references/structure.md).

## 4. Platform rules (check before writing a word)

| Rule | TikTok Shop video | TikTok ad | Meta ad |
|---|---|---|---|
| AI voice as the presenter | **Banned** | Label required | OK (auto "AI info") |
| Realistic AI people | High risk; needs a visible real person | Label (AIGC toggle) or rejected | Auto-labelled |
| Still-image slideshow | **Banned** (≥3 s moving footage, a person visible) | Weak | Allowed |
| Price or deal said in video | Must match the product page exactly, or a violation | Must match the landing page | Must match |
| Before/after | Typical results only; none for weight | No false-impression before/after | Cosmetics 18+, no weight loss |
| Music | Commercial Music Library | Commercial Music Library | Original audio or Meta Sound Collection |
| Near-duplicate reposts | Suppressed; 5+ low-quality Shop videos in 7 days hide links | Grouped | Grouped as one ad (Andromeda) |

Everywhere: **never write a first-person testimonial for an AI person** ("I used this for two weeks…"). The FTC rule bans fake testimonials, AI ones included, at up to $53,088 per violation (the maximum since January 2025). New York has required a conspicuous synthetic-performer disclosure in ads since 9 June 2026. An AI presenter may demo and state facts; results and reviews must be real. Full table with sources: [references/platform-rules.md](references/platform-rules.md).

## 5. Make it

Route by what the person has:

| They have | Route | Skill |
|---|---|---|
| Real footage | Recut hook-first, captions, CTA, variants | `ecommerce-video-edit` |
| Product photos only, no person needed | Product shots: ASMR, unboxing hands, in use, macro | `product-photo-to-video` |
| Product photos, want a person | AI actor UGC (not for TikTok Shop) | `ai-ugc-ad-video` |
| A TikTok Shop listing | Shop-compliant script and shot list, real presenter | `tiktok-shop-video` |
| A winning ad | New hooks on the same body, new concepts | `ad-creative-testing` |
| A competitor's viral video | Copy the structure, never the footage or actor | `remake-reference` how-to on varg how to |
| A viral-style hook clip from photos | Backyard-camera fail, torture test, problem → solution as phone footage | `varg-product-hook` |
| A faceless dropshipping "guide" reel | Product, cost vs price on a laptop, steps, "Comment GUIDE" | `varg-dropship-reel` |

**Product fidelity (non-negotiable):** start every shot from the real product photo, never from text. Keep clips at 5 s or less with a slow or locked camera ("no fast spins, that's where products melt"). Spell the label text out in the prompt. Composite the real cutout or logo back onto hero shots. Reject any clip whose silhouette, label text, colour or part count differs from the photo.

**Character lock:** one identity sheet, the same reference on every shot, one video model per character (no model-hopping between shots), one voice, the exact transcript with the audio.

**No video tool?** Never ship a Ken Burns slideshow with a robot voice as the ad. Deliver the script, a shot list and a 5-shot phone filming checklist, and label any FFmpeg animatic as a placeholder.

Models on varg (prices only from `estimate_cost`): stills `nano_banana_2_1` / `gpt_image_2_5`; product in hand `bria_fibo_edit_1_5_product_holding`; clips `seedance_2_5` (most real, ~3 tries per keeper), `kling_v4` (cheaper, often right first time), `kling_v4_flash` for drafts, `veo_3_1`; presenter with speech in one call `creatify_boreal`; voice `eleven_v4`; lip-sync `sync_v3`. Pipelines and prompts: [references/models-and-prompts.md](references/models-and-prompts.md).

## 6. Variants and launch

- A variant is a **different concept** (buyer, angle, format, first frame), not a new caption. Meta groups look-alike ads as one ad; TikTok wants 3–5 very different creatives per ad group and at least 12 new videos a month on Smart+ and GMV Max.
- Only 5–8% of ads become winners (Motion, 578,750 creatives, 2026). Plan for it: 8–15 concepts drafted cheap, the full model only for the ones that pass review.
- Once a concept wins, cut 3–5 new openers on its body (`ecommerce-video-edit` §6).
- Name files `<product>_<angle>_<format>_<hook-id>_<creator>_<len>s_v<N>.mp4`.
- Kill and scale rules: `ad-creative-testing`.

## 7. Hand-off checklist

- [ ] Product or result on screen by second 2; hook said + written + shown
- [ ] Every product shot matches the photo (label, shape, colour, parts)
- [ ] Claims provable; price and offer match the product page; no fake urgency
- [ ] No AI first-person testimonial; AI people and voices labelled; TikTok AIGC toggle on (it resets when a campaign is duplicated)
- [ ] TikTok Shop: a real person on screen, a real voice, ≥3 s of moving footage, no slideshow, Video Pre-Check run
- [ ] Music licensed per platform (separate mixes)
- [ ] 1080×1920, safe zone clear (top 14%, bottom 35%, sides 6%), -14 LUFS; 4:5 cut for Meta feed
- [ ] Test plan: concepts, budget per concept, judge after 1–3× target CPA, not after 2 days

## References

| Read | When |
|---|---|
| [references/platform-rules.md](references/platform-rules.md) | Before any script: TikTok Shop, TikTok ads, Meta, FTC, NY, music, with sources |
| [references/formats.md](references/formats.md) | Choosing the format: 30 named formats, when each works |
| [references/characters.md](references/characters.md) | Casting the person on camera, by category and claim |
| [references/structure.md](references/structure.md) | Second-by-second templates: TikTok Shop 18 s, UGC 15 s, yapper, VSL |
| [references/models-and-prompts.md](references/models-and-prompts.md) | Pipelines, varg model ids, copyable prompts |
| [references/questions.md](references/questions.md) | The 25 questions sellers ask most, answered |
| [references/sources.md](references/sources.md) | Where every number comes from |
