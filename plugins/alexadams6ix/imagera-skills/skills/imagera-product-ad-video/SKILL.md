---
name: imagera-product-ad-video
description: "Someone needs a short video ad for a product and has only a photo: an eight-second clip with their line read aloud and captioned. Use when: \"Make a video ad for my skincare serum from this photo\", \"I need a 9:16 product ad for TikTok\", \"Can you make a promo video for my headphones?\", \"product ad\", \"video ad\", \"commercial\", \"promo video\". Runs the Imagera \"Product ad video\" template (one still, one eight-second clip, a voiceover, a dub and captions — a few minutes)."
---

# Product ad video

Turns a product photo into an eight-second ad: a hero still that keeps the product exactly as photographed, a clip with a slow camera move built from it, your line read aloud over the clip, and word-by-word captions. Enough for a paid social placement without a shoot.

## When to use

Someone needs a short video ad for a product and has only a photo: an eight-second clip with their line read aloud and captioned.

## How to run it

- Ask for a product photo, the one line the ad says, and where it runs: 9:16 for Reels and TikTok, 1:1 for feed or 16:9 for YouTube.
- The voice reads the line exactly as typed and nothing else, so keep it to about 20 words for the 8-second clip; offer a trimmed version rather than rewriting it silently.
- Never invent prices, discounts, claims or a call to action the user did not give. The hero still keeps the product exactly as photographed.
- If the product must match across several ads or shots, offer the Object ID skill (/object-id) first. For a creator holding it and talking, offer the Talking product review skill (/ugc-talking-review); to test several looks, offer Ad variations (/ad-variations).
- Before handing it over, check the product stays sharp and unchanged in the clip and the captions match the spoken line.

## Inputs

- `photo` (image) — a photo of your product
- `pitch` (text) — the one thing you want the ad to say
- `ratio` (one of: 9:16 for Reels and TikTok, 1:1 for feed, 16:9 for YouTube) — where it will run

## Steps

1. Hero frame
2. Clip with a camera move
3. Voice
4. Dub
5. Captions

## Run it through Imagera

Connect the Imagera MCP server (https://mcp.imagera.ai/mcp, sign in with your Imagera account), then:

1. `run_skill` with `skill_id: "product-ad-video"` and the inputs above, `confirm: false` — this returns the price in credits and starts nothing.
2. Show the price. Only after the person agrees, call `run_skill` again with `confirm: true`.
3. Poll `check_skill_run` with the returned `run_id` until it finishes; hand over the result URLs.
4. Pictures of a saved Character, Object, Location or Outfit ID: `list_identities` returns each ID's sheet URL to pass as a reference image.

In Imagera itself, type `/product-ad-video` in Superagent, or open it from https://imagera.ai/skills.
