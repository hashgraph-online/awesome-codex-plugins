---
name: varg-ad-library-remix
description: >-
  Turns winning competitor ads from the Meta Ad Library, TikTok Creative Center, Kalodata or
  FastMoss into new ad angles for your own product, without copying them: rank ads by winner
  signals (running 30+ days, many variants, reach), break the top ones down with varg
  video_analyze (hook, angle, format, offer, proof, CTA, awareness level), map which angles and
  formats the market already runs, generate 10-20 new concepts (same angle in a new format, same
  format with a new angle, one awareness level up or down) using only claims you can prove, check
  originality, and hand each concept to a varg skill to produce. Use when a seller says "clone this
  winning ad", "what are my competitors running", "find winning ads for my product", "spy on
  TikTok Shop ads", "give me new angles", or pastes Ad Library or Creative Center links. Not for
  re-uploading or re-cutting someone else's footage (never), and not for one ad's 20 variants
  (use varg-ad-variants).
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
  (https://mcp.varg.ai/mcp) for video_analyze and generation. Downloading reference ads uses the
  media-download skill. Optional: an Ad Library MCP scraper.
allowed-tools: Bash(curl:*) Bash(jq:*) Bash(ffmpeg:*) Bash(ffprobe:*) Read Write Edit
---

# Remix winning ads into new angles

Sellers' top playbook in 2026: find ads that have run for 30+ days and remake what made them work. The idea, the format and the structure are free to reuse; the footage, the copy, the music, the voice, the logo and a beat-for-beat storyline are not ([idea vs expression](https://www.gfrlaw.com/what-we-do/insights/copyright-idea-can-be-copied-not-expression)). This skill keeps you on the right side of that line and turns winners into concepts for your product.

## 1. Collect candidates

| Source | How | What you get |
|---|---|---|
| Meta Ad Library | the person pastes URLs (search the competitor page or a keyword) | start date, variants, landing page; EU/UK ads also show reach |
| TikTok Creative Center → Top Ads | the person pastes URLs | likes, CTR tier, budget level, by industry and region |
| Kalodata / FastMoss | exports | TikTok Shop products and the videos that sold them (GMV) |
| Ad Library MCP scrapers | [facebook-ads-library-mcp](https://github.com/proxy-intell/facebook-ads-library-mcp), [tiktok-ads-library-mcp](https://github.com/proxy-intell/tiktok-ads-library-mcp) | `started_running`, `ads_using_creative` |

The official Meta `ads_archive` API returns non-EU ads only if they are political or issue ads, so it doesn't work for product ads ([Meta docs](https://developers.facebook.com/docs/marketing-api/reference/ads_archive/)). Prefer pasted URLs or a scraper; outside the EU/UK an ad's data vanishes when it pauses.

**Winner signals** (heuristics, not Meta facts): running 30+ days = proven, 14–30 = gaining; 5+ variants of one concept or the same video across pages = being scaled; EU reach = the only real volume number.

## 2. Break the top 5–10 down

Download with `media-download` (`vdl <url>`), upload (`POST /v2/files` or `create_upload`), then:

```bash
curl -s -X POST https://api.varg.ai/v2/tools/video_analyze/call -H "Authorization: Bearer $VARG_API_KEY" \
  -H "Content-Type: application/json" -d '{"model":"video-analyze","video_url":"AD_URL",
  "prompt":"Break this competitor product ad down for a remix: every shot with start-end seconds, camera and what happens; all on-screen text with timings; audio; the hook in the first 3 seconds; the angle (which pain or desire it sells), the format, the offer, the proof moment and the CTA; and the awareness level of the viewer it targets."}'
```

About 5 credits each. Tag each ad in one row of `winners.json`:

```json
{ "url": "…", "days_running": 41, "variants": 6, "hook": "spiking a drink at a club bar", "angle": "safety disguised as cute nail art",
  "format": "problem → Vs → solution, music, text overlays", "offer": "20 stickers", "proof": "sticker turns green in the drink",
  "cta": "link in bio", "awareness": "problem-aware" }
```

## 3. Map the gaps, then generate concepts

Put the winners in a grid of **angle** (pain, desire, fear, identity, price, gift, comparison) × **format** (problem → solution, unboxing, demo, testimonial, before/after, comparison, tutorial, POV skit, song/mascot) × **awareness** (unaware, problem-aware, solution-aware, product-aware, most-aware). Empty cells next to proven ones are the opportunities ([Motion frameworks](https://motionapp.com/library/frameworks/)).

Generate 10–20 concepts with three moves:

1. **Same angle, new format:** the proven pain in a format nobody in the niche runs (unboxing has the top Meta hit rate and the fewest ads).
2. **Same format, new angle:** the proven structure with a different pain or desire your product truly solves.
3. **One awareness level up or down:** problem-aware → solution-aware means less drama, more proof.

Each concept: title, angle and why it works, format, hook line (≤3 s), proof shot, claims allowed (from the seller's evidence only), the varg skill that makes it.

## 4. Originality check, then compliance

Reject a concept if it reuses footage, music, voice, copy lines, logos or characters, or repeats the source storyline beat for beat with only the product swapped. Then run every concept through `ai-ad-compliance-check` before anything is generated.

## 5. Produce

Hand each concept to the skill that makes it: `varg-product-hook` (hooks, problem → Vs → solution), `varg-unboxing-video`, `ai-ugc-ad-video`, `varg-mascot-jingle-ad`, `varg-dropship-reel`, then `varg-ad-variants` for hook variants of the winner.

## Tested

2026-10-28. Source: a German drink-test nail sticker reel (club bar → CCTV corridor → "Vs…" → product → sticker turns green → link in bio). `video_analyze` (5 credits) returned 7 timed shots, all text, angle "safety disguised as cute nail art", format problem/solution, proof "sticker turns green", awareness problem-aware. Remix: **same format, new angle** for a different product, car seat gap fillers: a dashcam "problem" (phone falls into the seat gap while driving), "Vs…", the reveal, the proof (coins and a phone stay on top), "Link in bio". Nothing reused but the structure. Result (21 s): https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_a2aa0853b683.mp4 · Steps: `references/example.md`.

## Related skills

`varg-product-hook` (breakdown steps in `references/breakdown.md`), `ai-ad-compliance-check`, `varg-ad-variants`, `ad-creative-testing` (test plan), `media-download`.
