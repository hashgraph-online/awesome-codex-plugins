---
name: varg-ad-variants
description: >-
  Turns one winning video ad into 20 ad variants that Meta's Andromeda and TikTok treat as
  different creatives: tag the winner with varg video_analyze, plan two layers (about 7 new
  concepts that each change message, visual execution or format, plus about 13 single-variable
  iterations, mostly new hooks), generate the new openers and concepts on varg (Seedance 2.5, Kling
  4, Nano Banana, ElevenLabs), swap hooks onto the winner with a tested FFmpeg script (word-boundary
  cut, normalised parts, 20 ms fade, manifest), re-caption every variant, and export names and a
  test plan. Use when a seller asks for ad variations, more creatives, hook variants, "scale my
  winning ad", "make 20 versions of this ad", creative testing volume for Meta or TikTok, or new
  hooks for an ad that is fatiguing. Not for the testing strategy alone (ad-creative-testing),
  finding winners from competitors (varg-ad-library-remix), or a brand-new single ad.
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  openclaw:
    requires:
      anyBins:
        - curl
        - ffmpeg
    homepage: https://varg.ai/how-to
compatibility: >-
  Needs a VARG_API_KEY with curl (see the varg-ai skill) or the varg MCP connection
  (https://mcp.varg.ai/mcp). The hook swap runs locally with ffmpeg and node 18+ or bun; captions
  use varg-dropship-reel's captions.mjs and an ffmpeg with libass.
allowed-tools: Bash(curl:*) Bash(jq:*) Bash(ffmpeg:*) Bash(ffprobe:*) Bash(node:*) Bash(bun:*) Read Write Edit
---

# One winning ad into 20 variants

Since Meta's Andromeda update, ads that look alike are grouped and compete as one ("Entity ID" in agency talk): a new caption, colour or music track is not a new creative. Sellers now test 20–40 creatives a week at about $20/day each and refresh every 2–3 weeks ([theoptimizer](https://theoptimizer.io/blog/how-to-test-ad-creatives-on-meta-after-the-andromeda-update-2026-playbook), [segwise](https://segwise.ai/blog/meta-andromeda-update-creative-strategy-2026)). The "suppressed above 60% similarity" thresholds are repeated by agencies but not published by Meta.

## 1. Tag the winner

`video_analyze` on the winner (about 5 credits; prompt in `varg-ad-library-remix`) → hook, angle, format, emotional driver, persona, proof, CTA. You scale the mechanism behind the ad, not the file.

## 2. Plan two layers (20 in total)

**Layer A, ~7 new concepts.** Each must pass the three-question check (two "no" answers = the same Entity): *Is the message different? Is the visual execution different, not just the text? Is the format different?* Moves: same script with a new persona (female → male → couple → parent), same structure with a new script, same concept in a new format (UGC → unboxing → demo → mascot song → problem/solution), same script with new b-roll.

**Layer B, ~13 iterations, one variable each.** Mostly new hooks (3–5 per concept, ≤3 s), then new CTAs or offers. If two fields change between variants, the plan is wrong ([Pixis](https://pixis.ai/blog/ad-creative-brief-template-how-to-turn-one-winning-ad-into-a-full-rotation/)).

Write the plan as JSON before generating; name every file `{angle}_{offer}_{product}_{format}_{hook}_v{n}`, e.g. `safety_fullprice_gloves_tutorial_povmandoline_v1`, with a closed list of 8–10 angles.

## 3. Make the new parts on varg

- New openers: a 3–6 s clip per hook (`varg-product-hook` archetypes, `varg-unboxing-video`) plus its spoken line on `eleven_v4` in the same voice as the winner (1 credit per line).
- New concepts: the skill that makes the format (`ai-ugc-ad-video`, `varg-mascot-jingle-ad`, `varg-dropship-reel` …).
- Price the batch first: `POST /v2/estimate` / `estimate_cost`.

## 4. Swap hooks onto the winner

Keep a **clean master** of the winner without burned captions. Find the cut: the first word of the body in its word timings (Whisper, or `hook` from `varg-dropship-reel`'s `guide-edl.mjs`). Then:

```bash
node scripts/hook-swap.mjs --body master_clean.mp4 --cut 7.34 --out variants/ \
  clips/mandoline.mp4+lines/pov-mandoline.mp3 \
  clips/knife.mp4+lines/knife-test.mp3
```

Each hook is a clip, or `clip+line.mp3` to lay a new spoken line over it (the hook lasts as long as the line + 0.3 s). Every part is normalised to 1080×1920 / 30 fps / 48 kHz before the join, with a 20 ms fade at the cut (no click), and `variants/manifest.json` records hook, line, cut and lengths. Then re-caption each variant: transcribe it, `captions.mjs`, burn with ffmpeg (libass).

## 5. Export the test plan

ABO, one creative per ad set, broad targeting, $20–50/day per ad set; kill under 1% CTR or at $10–30 spent without a result; judge after 7–14 days and 1,000+ impressions; move winners to CBO/Advantage+; refresh every 2 weeks. On TikTok, post hook variants as separate ads, not as duplicates of one post (duplicates get buried).

## Tested

2026-10-28 on the cut-resistant gloves reel (59 s). Two new spoken hooks on `eleven_v4` (1 credit each) over the reel's own clips, swapped in with `hook-swap.mjs` in seconds, then re-captioned:
- POV mandoline hook: https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_565f31d99f3a.mp4
- "I dragged a chef's knife across my hand. Look.": https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_7fe2d4c4fe3a.mp4

Both cut cleanly into "They can be purchased for…" with no click or jump. These are Layer B iterations; Layer A concepts need new footage.

## Related skills

`ad-creative-testing` (why an ad won, the test plan), `varg-ad-library-remix` (new angles from competitors), `varg-product-hook` and `varg-unboxing-video` (new openers), `varg-dropship-reel` (captions.mjs, guide-edl.mjs), `ai-ad-compliance-check`.
