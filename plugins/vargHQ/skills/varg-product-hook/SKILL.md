---
name: varg-product-hook
description: >-
  Makes the first 5-15 seconds of a product video, the part that stops the scroll: either finds
  a hook that already went viral for this kind of product (TikTok Creative Center, ad spy tools,
  Reels search) and remakes the idea, or generates a realistic UGC-style clip of the product in
  use with Seedance 2.5 on varg from the product's own photos (a backyard-camera fail, a torture
  test, problem then solution, a satisfying close-up, a gift reaction), or the whole "The problem → Vs → The solution" music ad. Use when someone selling
  a product (dropshipping, Shopify, TikTok Shop, Amazon) asks for a viral hook, a scroll-stopper,
  a "TikTok made me buy it" clip, product b-roll that looks like real footage, or "a video of my
  product in use" made from product photos. Not for the full guide reel with the laptop and pen
  (use varg-dropship-reel, which calls this skill for its hook), talking-head UGC ads with an
  actor reading a script (find one with video-skills), or studio packshot spins (use varg-ai).
license: MIT
metadata:
  author: vargHQ
  version: "1.2.0"
  openclaw:
    requires:
      anyBins:
        - curl
    homepage: https://varg.ai
compatibility: >-
  Needs a VARG_API_KEY with curl (see the varg-ai skill) or the varg MCP connection
  (https://mcp.varg.ai/mcp). Downloading reference clips uses the media-download skill (yt-dlp).
allowed-tools: Bash(curl:*) Bash(jq:*) Bash(ffmpeg:*) Bash(ffprobe:*) Read Write Edit
---

# Product hook

The hook is the first 5-15 seconds of a product reel: real-looking footage of the product doing the one thing that makes people stop. In the dropshipping reels this skill was built from (@tradelle, Sept-Oct 2026), the hook carried the video: a snake biting a leg gaiter, a worker getting sand and grinder sparks thrown at his face mask, a cat's claw lit up by an LED clipper. The voiceover over the hook is a plain product line ("These are the leg guards I wear when I'm outdoors"). Two more reels (a cat runner, drink-test nail stickers) show the other use: the hook stretched into the whole 15-22 s ad, "The problem → Vs → The solution", set to music with no voice (section 3).

Generation runs on varg: the `varg-ai` skill (REST at `https://api.varg.ai/v2`) or the varg MCP server (`https://mcp.varg.ai/mcp`, tools `call_tool` + `get_job`). Every call returns a job; poll `GET /v2/jobs/{id}` until `completed`, the file is at `output.outputs[0].url`.

## 1. Ask two things first

1. **Where the hook comes from**
   - **Remake a proven idea with AI (recommended):** find a hook that already worked for this kind of product, then generate your own version with your product. No rights problems, any angle you want.
   - **Your own footage:** the supplier's video or your own phone clips. Only use supplier or other people's clips with written permission. Sellers get takedowns for reposted AliExpress videos.
2. **Which archetype** (pick from the table in step 3, or let the product decide: protective gear → torture test or backyard camera; pet and home gadgets → problem/solution or satisfying close-up; gifts → reaction).

Also collect: 1-3 product photos (a clean packshot plus one in-use photo if there is one), the product name, and the one benefit to show.

## 2. Find what already works (10 minutes)

| Where | What to look at |
|---|---|
| TikTok Creative Center → Top Ads / Top Products | Filter by your country and category; sort by CTR. Note the first 3 seconds of the top 5 ads. |
| Kalodata, FastMoss | TikTok Shop products with rising sales and the creator videos that sold them. |
| Minea, PiPiADS | Ad spy tools: the ad, how long it has been running, engagement. An ad running 30+ days is profitable. |
| Instagram / TikTok search | `tiktok made me buy it`, `amazon finds`, `backyard camera caught this`, `<product> test`, "where can I buy this" in comments. |
| Product research tools (Tradelle, Sell The Trend, AutoDS) | The product page often embeds the video ads that sell it. |

Save the 2-3 best references with the `media-download` skill (`vdl <url>`) and break each one down: every shot with its time, the text on screen, the voiceover word for word, the structure. The fastest way is one `video_analyze` call on varg (~5 credits, MCP `analyze_video`); for exact frames, a 1-frame-per-second contact sheet with FFmpeg plus Whisper word timings. Commands, the table to fill and what to look for: [references/breakdown.md](references/breakdown.md). End with the idea in one line ("snake strikes the gaiter in a swamp, the gaiter holds"); you remake the idea, not the clip.

## 3. Pick the archetype and fill the prompt

Every prompt has five blocks (the order matters for Seedance 2.5):

1. **Identity:** "the <product> from @image1 (exact same product: same shape, colors, material, logo)".
2. **Shot:** "vertical UGC clip shot handheld on an iPhone in <place>, natural light, slight hand shake".
3. **Action:** one clear physical action and its result, in order.
4. **Camera:** close-up or medium, one move at most.
5. **Exclusions:** "Real footage look, no music, no text, no subtitles." Captions and offers go in the edit, never in the prompt.

| Archetype | What happens | Prompt core (blocks 2-4) |
|---|---|---|
| **Backyard camera caught this** | Security-cam angle: something goes wrong, the product saves the day | "Fixed security-camera view from a house corner, slightly wide lens, timestamp-free. A man in overalls clears tall grass with a leaf blower; a large snake lunges at his leg and bites the <product from @image1> on his shin; he jumps back unhurt." |
| **Torture test** | The product takes abuse and holds | "Front-facing phone selfie video by a worker in a garage. He wears the <product from @image1>. A friend throws a handful of sand at his face, then holds an angle grinder near him so sparks spray across the visor; he doesn't flinch." |
| **Problem → solution** | 2-3 s of the annoying problem, then the product fixing it | "Shot 1 (0-3s): backyard camera view, an orange cat climbs the fence and escapes while its owner chases it. Shot 2 (3-8s): handheld, the same cat happily rolls around the lawn inside the <product from @image1>." |
| **Satisfying close-up** | Macro of the product doing its job | "Extreme close-up, hands hold a fluffy cat's paw; the <product from @image1> switches on its LED, lights up the claw so the pink quick shows, snips just the tip; the clipping drops into the guard." |
| **Gift reaction** | Someone unwraps it, puts it on, reacts | "Living room, Father's Day: a dad opens a gift box, pulls out the <product from @image1>, puts it on and laughs; his son films on a phone." |
| **Before / after** | Same spot, two states | "Shot 1: a grimy oven door, a hand sprays the <product from @image1>. Shot 2: same framing, the hand wipes once and the glass is spotless." |

For a hook with a person who must stay the same across several clips, make a character sheet first (`varg-character-design`).

### The whole ad as one hook: "The problem → Vs → The solution" (14-22 s, music, no voice)

Two of the reels this skill was built from aren't hooks for a longer video. They are the entire ad: a cat-runner reel (@rollymewofficial, 14 s, 160k likes) and a German drink-test nail-sticker reel (NailSense, 22 s). Both use the same skeleton:

| Time | Text on screen | Picture |
|---|---|---|
| 0-5 s | `The problem 🥺` / `Das Problem 🥺` | The pain, shot as real life: a cat escaping over the fence on a backyard camera; a man leaning over a woman's drink at a club bar |
| 5-9 s | (same text) | The stakes, on a **security-cam** angle with an on-screen timestamp and camera name ("CAM 04 · HINTERER FLUR · 17.10.2026 02:47"): the cat gone, the man walking her down a back corridor |
| 9-10 s | `Vs...` | A hard cut, sometimes with the product already coming into frame |
| 10-12 s | `The solution 😍` / `Die Lösung 😍` | The product revealed in a clean, warm setting (a vanity with a candle; an autumn lawn) |
| 12-16 s | One feature line (`Drink-Test als Sticker 💖`) | Hands use it, step by step |
| 16-20 s | One benefit line (`Süß & kinderleicht 🥰`) | The proof moment: the star sticker turns from pink to green in the drink; the cat rolls safely through a store |
| 20-22 s | `Link in der Bio für deine 🛡` | The product held up in the problem setting |

- No voiceover. A trending song carries it, and the song is added in the app, not baked into the file.
- Text: one short line in sentence case with one emoji, white with a soft shadow, in the top third. Each line stays on until the next beat. This is the platform's native text style, not the big word-by-word captions of the guide reel.
- Make it as 4-5 clips: 2 problem clips (the second is the security-cam angle), the reveal, the use, the proof. Then cut on the text changes. In the security-cam clips, ask for "CCTV night-vision black-and-white, fisheye, high corner angle". Add the timestamp overlay in the edit, because model-drawn text comes out garbled. Render the text lines and the timestamp as transparent PNGs (any headless browser; libass can't draw colour emoji) and lay them on with `varg-dropship-reel`'s `assemble.mjs` (`overlays`), with the music as the only soundtrack.
- **Same person in both problem clips:** make the second clip image-to-video from the **last frame of the first** ("same fixed camera, same woman, same car, continuous footage"). Two separate text-to-video clips gave two different women.
- **Fear themes get restricted.** The drink-spiking reel is behind Instagram's "can't be seen by certain audiences" gate: logged-out and younger viewers can't open it, so its reach is capped. Danger, assault, injury and medical scares sell protective products but can trigger age gates or ad rejection. Show the threat without anything happening to the person on screen.

## 4. Generate

Upload the product photos (`POST /v2/files`, MCP `create_upload` → PUT to `proxy_url`), then:

```bash
curl -s -X POST https://api.varg.ai/v2/video \
  -H "Authorization: Bearer $VARG_API_KEY" -H "Content-Type: application/json" \
  -d '{
    "model": "seedance_2_5",
    "prompt": "Vertical UGC product clip shot handheld on an iPhone in a cozy living room, natural window light, slight hand shake. Extreme close-up: a person'\''s hands hold a fluffy orange cat'\''s front paw on a grey blanket. They bring in the pet nail clipper from @image1 (exact same product, same white and pastel-blue colors, same LED light at the blade). The LED switches on and lights up the claw so the pink quick is visible through it; the clipper snips the very tip of the claw cleanly, the clipping drops into the transparent guard. The cat stays calm. Real footage look, no music, no text, no subtitles.",
    "files": [{ "url": "PRODUCT_PACKSHOT_URL" }],
    "aspect_ratio": "9:16",
    "resolution": "720p",
    "duration": 6
  }'
```

- One image in `files` is the first frame on most models, but `seedance_2_5` (≤9 images), `kling_v4` (≤7) and `wan_3` (≤10) take it as a **reference** and build the scene around it. Name each one in the prompt (`@image1`, `@image2`).
- Hooks are 4-8 s per clip; plan 2-3 clips (13 s in total covered the hook in every reel studied). Seedance 2.5 can do 2-3 shots in one 8-12 s clip with "Shot 1 (0-3s): … Shot 2 (3-8s): …".
- Price it first: `POST /v2/estimate` (same body) or MCP `estimate_cost`. A 6 s 720p `seedance_2_5` clip cost 231 credits in our test (Oct 2026). Drafts: `wan_3` at about a quarter of that, then the keeper on `seedance_2_5`.
- Keep `audio` off when a voiceover goes on top. Turn it on (`"audio": true`) for a hook that plays with its own sound (a scream, a snap, a crash), as in "Backyard camera caught this".

## 5. Check before you use it

- **Is it the same product?** Compare shape, color and logo against the packshot frame by frame. If it drifts, add a second photo from another angle as `@image2`, and add "do not change the product's shape, color or size".
- **Does the action read in 1 second with the sound off?** If not, shorten to the moment of impact.
- **Hands and animals:** count fingers, check paws. Regenerate the clip instead of fixing it in the edit.
- **Product scale:** Seedance sometimes makes the product too big or small; say its real size ("palm-sized").
- Re-running with a byte-identical body is a free cache hit; change one word to get a new take.

Tested 2026-10-28, four more hooks from one packshot each, all on `seedance_2_5`: a backyard security camera with a solar flood light (night IR, the light flares on), a torture test with cut-resistant gloves (knife across the glove, grabbing the blade, a mandoline), a dog version of the nail clipper, and a Father's Day gift reaction with a neck massager. All read as phone or CCTV footage on the first take; the full reels are in `varg-dropship-reel`. A 21 s "The problem → Vs → The solution" ad for car seat gap fillers (2 `kling_v4` dashcam clips + 2 `seedance_2_5` product clips, PNG text overlays, a `mureka_9_5` music bed): https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_a2aa0853b683.mp4. Its reveal clip drifted from long foam wedges to boxier blocks; pass a second product angle as `@image2` for products with an unusual shape.

Tested 2026-10-27: an LED pet nail clipper packshot (`gpt_image_2_5`) + the prompt above on `seedance_2_5` at 6 s 720p gave a usable handheld close-up on the first try: the product stayed recognizable, the LED lit up, and it looked like phone footage.

## Rules

- Don't claim the AI clip is a real customer or a real event. Label AI content where the platform asks for it (TikTok and Instagram AI labels).
- Don't use real brand logos you don't own, real people's faces or celebrity lookalikes.
- Don't repost someone else's video as your hook. Remake the idea with your own product.

## Related skills

`varg-dropship-reel` (the full 60-second guide reel this hook opens), `varg-ai` (models, uploads, prices), `media-download` (save reference clips), `varg-character-design` (a person who stays the same across clips), `video-skills` (other ad formats).
