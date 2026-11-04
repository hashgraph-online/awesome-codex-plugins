---
name: varg-dropship-reel
description: >-
  Makes the 60-second faceless dropshipping "guide" reel end to end: a viral-looking product hook,
  a laptop on a zigzag tablecloth with a hand pointing a marker at the product cost, the store
  price and the demand chart, then each step (research tool → store → AI ad tool → Instagram →
  supplier ships), and a night-skyline ending shot on an iPhone with "Comment GUIDE". Script
  template, AI shots on varg (Seedance 2.5, GPT Image 2.5, Wan 3, ElevenLabs), word-by-word
  lime captions, the comment-to-DM funnel. Use when an e-commerce seller, dropshipper, affiliate of
  a product-research or AI-ad tool, or course creator asks for a product reel like @tradelle's,
  "a reel showing a product, its price in China and on Shopify", a "comment GUIDE" reel, a
  laptop-and-pen screen walkthrough, or one such reel per product every day. Not for the hook
  alone (use varg-product-hook), talking-head UGC ads, or screen recordings of software with a
  cursor (find those with video-skills).
license: MIT
metadata:
  author: vargHQ
  version: "1.1.0"
  openclaw:
    requires:
      anyBins:
        - curl
        - ffmpeg
    homepage: https://varg.ai
compatibility: >-
  Needs a VARG_API_KEY with curl (see the varg-ai skill) or the varg MCP connection
  (https://mcp.varg.ai/mcp). Assembly runs locally with ffmpeg built with libass (macOS:
  `brew install ffmpeg-full`) and node 18+ or bun for the scripts in scripts/ (screenshot.mjs
  also needs the playwright package).
allowed-tools: Bash(curl:*) Bash(jq:*) Bash(ffmpeg:*) Bash(ffprobe:*) Bash(node:*) Bash(bun:*) Read Write Edit
---

# Dropshipping guide reel

One template, a new product every day. Built from four @tradelle reels (Sept-Oct 2026, 56-64 s, 1080×1920) that share the same skeleton and almost the same voiceover; only the product, the prices and the hook change.

| Beat | Time | Picture | How we make it |
|---|---|---|---|
| Hook | 0-13 s | The product in action: real-looking phone or security-cam footage | `varg-product-hook` (Seedance 2.5 from product photos) |
| Price math | 13-27 s | Laptop, hand with a marker points at **cost**, **sell price**, **demand chart** | Real screenshots on a green-screen desk photo → Kling 4 adds the hand (or film it) |
| Steps | 27-53 s | The same desk and the same app UI in every shot, the pen walks through each screen | Same, one shot per screen |
| CTA | 53-60 s | Night skyline through an apartment window, iPhone look | Wan 3 or Seedance 2.5 once, reuse forever |

Captions: 1-2 words at a time, bold uppercase, white with a black outline, prices and keywords in lime, at 60 % of the height. Voice: one flat, confident male narrator, about 2.6 words per second, no music or a very quiet bed.

Generation runs on varg: the `varg-ai` skill (REST at `https://api.varg.ai/v2`) or the varg MCP server (`https://mcp.varg.ai/mcp`: `call_tool`, `get_job`, `estimate_cost`, `create_upload`). Every call returns a job; poll `GET /v2/jobs/{id}` until `completed`, the file is at `output.outputs[0].url`. Image-to-video jobs took 5-10 minutes in our test; one text-to-video job waited about an hour in the queue. Start them all at once and do the next step while they run.

## 1. Ask once, then go

Collect: the product (store or supplier link, 1-3 photos), **cost price** and **sell price**, which tools the steps name (the research tool, store builder, AI ad tool, supplier: the ones you're an affiliate of, or your own store), the CTA keyword (default `GUIDE`), and the language.

Then offer these choices in one message, each with a default:

1. **Hook:** AI remake from product photos (default) / your own footage. Archetype: backyard camera, torture test, problem → solution, satisfying close-up, gift reaction.
2. **Laptop shots:** full AI from screenshots (default) / film them yourself (free, looks 100 % real, guide in `references/screen-demo.md`).
3. **Ending:** AI night skyline (default, make once and reuse) / your own phone clip / stock.
4. **Voice:** ElevenLabs `eleven_v4`, voice "Brian" (default) / another voice / your own recording.

Quote the price before generating (`POST /v2/estimate` or MCP `estimate_cost` per clip). What our tests paid (Oct 2026): 6 s `seedance_2_5` hook clip 231 credits, 5 s laptop shot 79 on `kling_v4`, the desk photo 22 once, the skyline 60 once, voice 8. The first reel is about 1,250 credits (2 hook clips + 9 laptop shots + skyline); every next product about 860 (2 hook clips + 5 product-specific laptop shots + voice), because the desk, the skyline and 4 of the laptop shots are shared. With real laptop footage, about 470 per reel.

## 2. Write the script

Fill the template in `references/script.md` (140-160 words for 55-60 s). Put the exact prices you'll show on screen into the script. No income promises (see the claims section there).

## 3. Make the pieces (start all video jobs in parallel)

**Hook (0-13 s):** follow `varg-product-hook`: 2-3 clips of 4-6 s on `seedance_2_5`, 9:16, 720p, the product photo as `@image1`.

**Laptop shots (13-53 s):** `references/screen-demo.md`. In short (the UI must be identical in every shot, so no model ever draws the screen):
1. Once: a desk photo with a MacBook whose screen is flat chroma green (`gpt_image_2_5`, prompt in the reference).
2. Screenshots of every screen the script names, same size: your real store and tool, or `assets/demo-app.html` (`scripts/screenshot.mjs`).
3. `node scripts/screen-on-laptop.mjs plate.png frames/ screens/*.png`: each screenshot warped onto the green screen, pixel-exact.
4. Animate each frame for 5 s on `kling_v4` (79 credits): locked camera, static screen, the hand with a marker enters and points along a path in script order. 9 clips per reel; landing, settings, ad tool and flow are shared across products.

**Skyline ending (53-60 s):** `references/cta-and-funnel.md` has the iPhone-look prompt. Text-to-video on `wan_3` (60 credits for 6 s) did it well in our test. Make 2 variants once and reuse the better one in every reel.

**Voiceover:**

```bash
curl -s -X POST https://api.varg.ai/v2/speech -H "Authorization: Bearer $VARG_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "eleven_v4", "voice": "Brian", "text": "<the script>"}'
```

**Word timings for the captions:** transcribe the voiceover with `groq_whisper_large_v3_turbo`. It returns `data.words` with a start and end per word; `whisper_large_v3` returns only sentence chunks.

```bash
curl -s -X POST https://api.varg.ai/v2/tools/transcription/call -H "Authorization: Bearer $VARG_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "groq_whisper_large_v3_turbo", "audio_url": "VOICEOVER_URL", "language": "en"}'
# poll the job, then save its result (the object with "words") as words.json
```

## 4. Cut it

Download every clip into `clips/` under the names `guide-edl.mjs` lists (hook1, hook2, productA, productB, store, home, settings, adpaste, ads, flow, orders, skyline), then:

```bash
mkdir -p fonts && curl -sL -o fonts/Bangers-Regular.ttf \
  https://github.com/google/fonts/raw/main/ofl/bangers/Bangers-Regular.ttf   # free, close to the originals' comic bold
node scripts/captions.mjs words.json captions.ass --keywords "shopify,profit,demand,free,guide,china"
node scripts/guide-edl.mjs words.json clips > edit.json   # cuts every screen in on the word that names it
node scripts/assemble.mjs edit.json
```

For a voiceover in another language add `--lang es` (built in: en, es) or `--anchors anchors.json` with the same 11 keys; see `varg-ad-localize`. `guide-edl.mjs` finds the script's anchor words ("purchased", "sold", "Even after", "Here is how", "First", "Offer", "Then go", "It will", "Start posting", "when a customer", "Comment") and writes one cut per phrase. To cut by hand, `edit.json` is one entry per cut:

```json
{
  "out": "reel.mp4", "voiceover": "vo.mp3", "captions": "captions.ass", "fontsdir": "fonts",
  "shots": [
    { "file": "hook1.mp4",   "in": 0,   "dur": 3.0 },
    { "file": "hook2.mp4",   "in": 0.5, "dur": 2.6 },
    { "file": "research.mp4","in": 0,   "dur": 3.0 },
    { "file": "store.mp4",   "in": 0,   "dur": 4.1 },
    { "file": "research.mp4","in": 2.6, "dur": 2.4, "zoom": 1.08 },
    { "file": "skyline.mp4", "in": 0,   "dur": 4.6 }
  ]
}
```

`zoom` punches in (use it when you reuse a clip), `speed` below 1 slows a shot, a shot longer than its source holds the last frame, and `overlays` (`[{ "file": "banner.png", "start": 0, "end": 7 }]`, full-frame PNGs with alpha) put on-screen text with emoji or a CCTV timestamp over the hook. libass can't draw colour emoji, so render those lines as PNGs. Shots should add up to the voiceover length. The script picks up Homebrew's `ffmpeg-full` by itself when the default `ffmpeg` can't burn subtitles.

**ffmpeg without captions support.** Homebrew's `ffmpeg` has no libass since 2025 (`ffmpeg -filters | grep subtitles` prints nothing). Install the keg-only `ffmpeg-full` next to it (`brew install ffmpeg-full`); it doesn't replace `ffmpeg`. Seen on macOS 15.1 (2026-10-27): the install upgraded shared libraries, after which the old `ffmpeg` failed to start (`Library not loaded: libx265…`) and `ffmpeg-full` failed on `freetype` (`Library not loaded: /usr/lib/libhvf.dylib`). Fix: `brew upgrade ffmpeg` and `brew reinstall --build-from-source freetype`. Don't run this on someone's machine without asking: it changes their system Homebrew.

Check the result: watch it once with sound and once muted; every price on screen must match the voice and the caption at that moment.

## 5. Post and catch the comments

Caption `Best time to start is here 🤝 #entrepreneur #onlinebusiness #ecommerce` (the originals' exact line), a ManyChat comment trigger on the keyword that DMs the guide, and the AI label where the platform asks for it. Setup and what to put in the guide: `references/cta-and-funnel.md`.

## Tested

2026-10-28, four products end to end on varg with this exact pipeline: one green-screen desk photo (`gpt_image_2_5`), the demo app's screens via `screenshot.mjs` + `screen-on-laptop.mjs`, 24 laptop shots on `kling_v4`, hooks on `seedance_2_5`, `eleven_v4` "Brian" voices, word timings from local Whisper, `guide-edl.mjs` + `captions.mjs` + `assemble.mjs`. The app looks the same in every shot and the desk never changes; the hand is the only thing that moves.

| Reel | Hook | Link |
|---|---|---|
| LED pet nail clipper | satisfying close-up (cat, then dog) | https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_782920d92e94.mp4 |
| Solar security light | backyard security camera + "Backyard camera caught this ❌" overlay; the AI video step on varg.ai | https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_d45406f8d0db.mp4 |
| Cut-resistant gloves | torture test (knife, mandoline) | https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_631fb721a315.mp4 |
| Heated neck massager | gift reaction (Father's Day) | https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_3c77d15fbf7e.mp4 |

The first version (2026-10-27) drew each laptop frame with `gpt_image_2_5`; the UI changed between shots, which is why the steps above keep the model off the screen.

## Rules

- Real prices, real store, real screenshots. No fake reviews, sales counts or income claims.
- Don't repost other people's videos as the hook. Remake the idea with your product (`varg-product-hook`).
- Say it's an ad when you're paid or an affiliate; label AI footage where the platform asks.
- Keep Burj Khalifa out of focus in paid ads (Emaar wants approval for ad use).
- Re-running a byte-identical request is a free cache hit; change a word to get a new take.

## Files

```
reel/
  script.md          # filled template
  product.png        # packshot (and any extra product photos)
  plate.png          # the green-screen desk photo, made once
  screens/*.png      # screenshots, one per screen named in the script
  frames/*.jpg       # screen-on-laptop.mjs output, one per screenshot
  clips/*.mp4        # hook1-2, laptop shots (productA/B, store, home, settings, adpaste, ads, flow, orders), skyline
  vo.mp3  words.json  captions.ass  fonts/
  edit.json  reel.mp4
```

Tutorial with all five example videos and the tools compared: https://github.com/vargHQ/how-to-make-ai-videos-for-dropshipping

## Related skills

`varg-product-hook` (the hook), `varg-ai` (models, uploads, prices, cloud render), `media-download` (save reference reels), `short-form-ffmpeg-cookbook` (more edits: zoom punches, speed ramps, loudness), `video-skills` (other ad formats).
