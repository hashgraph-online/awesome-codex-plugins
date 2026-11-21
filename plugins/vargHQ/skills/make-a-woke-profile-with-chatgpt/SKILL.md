---
name: make-a-woke-profile-with-chatgpt
description: >-
  Turn one selfie into a satirical "I MADE ME WOKE" profile set with GPT Image 2.6, the image
  model in ChatGPT (aka Wokify): 11 woke versions of you (character sheet, woke friends photo,
  LinkedIn-style profile, DEI video call, protest TV interview, action figure, holographic trading
  card, woke cat, oat latte, "In this house" home, WOKEOPOLY), four as looping GIFs, in a 4:5
  collage sized for X plus an MP4, and an optional HyperFrames presenter-mode video. One command on
  varg, about $0.78; the prompts also work pasted into ChatGPT. Use when someone wants to make
  themselves woke, wokify a photo or profile picture, a woke AI filter, the "I made me woke" trend,
  a ChatGPT image prompt pack for a selfie, an AI action figure or trading card of themselves, or a
  collage of AI versions of one person. Not for photos of others without consent, public figures,
  or mocking LGBTQ+ people themselves (the joke is on performative habits and brands).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  openclaw:
    requires:
      anyBins:
        - python3
    homepage: https://varg.ai/how-to
compatibility: >-
  Needs a VARG_API_KEY (or ~/.varg/credentials from the varg CLI) and python3; collage.py needs
  Pillow, and --anim needs ffmpeg; presenter.py needs Pillow, Node 22+ for npx hyperframes, and
  ffmpeg for music. About 78 credits ($0.78) for the full set, 106 with --fresh (measured
  2026-11-05). The ChatGPT route needs only a ChatGPT account.
allowed-tools: Bash(python3:*) Bash(ffmpeg:*) Bash(npx:*) Bash(bunx:*) Read Write Edit
---

# Turn a selfie into a woke profile with GPT Image 2.6

One selfie goes in. Out come 11 woke versions of you and a 4:5 collage titled "I MADE ME WOKE"
for X, plus an MP4 where the card, the cat, the house lights and your protest interview move.
It runs on GPT Image 2.6, the image model behind ChatGPT, through varg. The full set costs about
**78 credits ($0.78)**: nine image edits at 7-8 credits, two GIFs at 7, and three shared tiles for
free. One command:

```bash
python3 scripts/wokify.py --selfie me.jpg --name "Alex" --pronouns "he/they" --out wokify-out
python3 scripts/collage.py wokify-out --anim        # collage.jpg 2400x3000, collage.mp4, collage.gif
```

Example, made from one selfie on 2026-11-05:
- [the collage (JPG, 4:5)](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_9c833861b4f7.jpg)
- [the animated collage (MP4)](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_a7221dc30e0a.mp4)
- [the presenter-mode video (MP4, 42 s)](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_e0bf94ebd85e.mp4)

No API key? Paste the prompts from [references/prompts.md](references/prompts.md) into ChatGPT
with your selfie attached, one tile per chat (section "ChatGPT route" below).

## Rules before you start

- **Use your own photo,** or one you have the person's clear permission to use. Never a public
  figure, a child, or someone who did not agree. The output is a recognizable fake of a real face.
- **Punch at habits and brands, not at people.** The jokes are tote bags, oat lattes, land
  acknowledgments on LinkedIn and rainbow logos that vanish in July. Pride and trans flags appear
  as the things the characters wear, never as the punchline.
- **No real brand logos.** GPT Image 2.6 adds them by itself: a Patagonia patch on a fleece vest,
  New Balance "N" on sneakers, GT's on kombucha, the LinkedIn "in". The prompts forbid them; still
  check every tile (step 4).

## Steps

1. **Pick the selfie.** It should be front-facing, sharp and evenly lit, about 1024 px or larger,
   with one face, nothing covering it, and a plain background. A smiling photo gives the best
   "smug" tiles. Ask for the person's name and pronouns: they go on the profile page and the call
   tile.
2. **Price it first.** `python3 scripts/wokify.py --dry-run` prints every tile and the total
   (~78 credits; `--fresh` remakes the shared cat, latte and house from their prompts: ~106).
3. **Run it.** `wokify.py` uploads the selfie (`POST /v2/files`) and runs the tiles four at a time
   on `gpt_image_2_6`. Each tile edits a hosted base image with the selfie as image 2, so the scene
   stays the same and only the face changes. The GIF steps then animate the tile's own still.
   About 2-3 minutes. Every job (id, credits, URL, prompt) goes to `wokify-out/run.json`.
4. **Look at every face and every logo.** Open each PNG at full size.
   - Face drifted? `--fix-face <tile>` runs a face-only pass on Flare with the selfie (8 credits)
     and keeps the old file as `<tile>.before-face-fix.png`.
   - A logo slipped in? `--fix-logo <tile> --where "the sneakers"` (7-8 credits).
   - Fixed a tile that has a GIF (`social`, `card`)? Re-animate it with
     `--gif-only --only <tile>`.
5. **Build the collage.** `python3 scripts/collage.py wokify-out --anim`. The rows are fixed (below);
   GIF tiles move in `collage.mp4` and `collage.gif`; the JPG uses their first frame.
6. **Optional: the presenter-mode video.** `python3 scripts/presenter.py wokify-out --music bed.mp3`
   writes a HyperFrames project. Render it with
   `cd wokify-out/presenter && npx hyperframes@0.9.15 render -o final.mp4 --crf 20`.
   - The video is 42 s at 1920x1080. The collage opens and scrolls for 9 s, then 11 slides of 3 s
     each show the current slide large, a NOW note, a NEXT preview, and every slide on a timeline
     with a rainbow highlight.
   - Music: any 42 s bed at 120 BPM keeps every cut on a beat. On varg:
     `{"model": "eleven_music_v2_5", "prompt": "...", "duration": 42, "provider_options": {"elevenlabs": {"force_instrumental": true}}}`.
     Pass the length as `duration`: a top-level `music_length_ms` is dropped silently and you get 30 s.
7. **Post it.** X shows a single 4:5 image uncropped in the feed. A GIF must be within 1280x1080,
   and phones only take 5 MB, which is why `collage.gif` is 720x900. The MP4 is the safer upload.
   A caption that fits: *"I made me woke 🏳️‍🌈 One selfie, 11 prompts: my LinkedIn, my cat, my
   trading card, my protest era."* Put links in the first reply: X shows posts with links less.

## The 12 tiles

| Tile | Label | What it is | Made from | Credits |
|---|---|---|---|---|
| `before` | BEFORE | your selfie | — | 0 |
| `me` | ME | "THE ALLY" character sheet: teal hair, pink glasses, septum ring, 8 views | base sheet + selfie | 8 |
| `friends` | MY FRIENDS | street-protest group photo with the 5 most-memed woke friends on X, you holding "WOKE 3.0" | selfie only, Flare, quality high, 2048x1152 | 7 |
| `linkedin` | MY LINKEDIN | "Chief Purpose Officer", land acknowledgment, cause icons, your name and pronouns | base page + selfie | 8 |
| `colleagues` | MY COLLEAGUES | "UNCONSCIOUS BIAS 101" video call; you are the one eating cereal | base call + selfie | 8 |
| `social` | MY SOCIAL LIFE | TV street interview: "Honestly? I'm here for the community. And the vibes." | base still + selfie, then GIF (10 frames, head moving) | 15 |
| `figure` | MY FIGURE | "URBAN PROGRESSIVE: NOW WITH EXTRA OPINIONS!" action figure | base box + selfie | 8 |
| `card` | MY CARD | holographic "THE ALLY" card: Moral superiority 99, Actual activism 4 | selfie, then GIF (8 frames, tilt + glare) | 15 |
| `pet` | MY PET | smug calico with a "they/them" tag, white wine, a tote bag | shared GIF (or `--fresh`) | 0 |
| `drink` | MY FAV DRINK | oat latte ad, the name misspelled on the cup | shared PNG (or `--fresh`) | 0 |
| `home` | MY HOME | "In this house we believe" diorama, lights blinking, "PRIVATE ROAD — NO TURNAROUNDS" | shared GIF (or `--fresh`) | 0 |
| `game` | MY FAVORITE GAME | WOKEOPOLY board; you are the figurine and the face on the 500 bill | base board + selfie | 8 |

Collage rows (4:5, 2400x3000): BEFORE · MY FRIENDS / ME · MY CARD · MY LINKEDIN / MY FIGURE · MY PET ·
MY FAV DRINK · MY HOME / MY SOCIAL LIFE · MY FAVORITE GAME · MY COLLEAGUES.

The research behind two of the tiles was done on X on 2026-11-05:
- **The #1 woke animal is the cat.** JD Vance's "childless cat ladies" clip has 30.1M views and
  29.6k likes, and a "WOKE CAT" meme has 110k likes. The runner-up, the pit bull, peaks around 2.5k.
- **The woke friend group** has five most-memed archetypes:
  - the they/them art student (teal hair, septum ring, pronoun pin);
  - the "performative male" feminist (mustache, cardigan, iced matcha, tote; 21k likes);
  - the wine-mom ally;
  - the masked DSA organizer;
  - the tie-dye boomer.

  The setting is a street protest, and the sign is the 11-04 "WOKE 3.0" meme (45-50k likes).

Sources are linked in [references/prompts.md](references/prompts.md).

## What we learned making it (measured on varg, 2026-11-05)

- **Edit a base image, don't generate the scene.** Sending [scene, selfie] with "replace the
  person with the person from image 2" keeps every label, layout and joke exact. Generating the
  whole scene from text with the selfie also works, but the text and layout come out different
  every time.
- **Small faces come out mushy.** In a 1088x608 image, faces in a group or storefront are about
  25 px wide and lose your likeness. Fixes:
  - frame closer and raise `image_size` (for example 1536x1712 per panel);
  - for the sharpest faces, pin `fal:openai/gpt-image-2.6/sunburst/edit` at `quality: "high"`;
  - Sunburst sharpens but drifts identity, so follow it with the Flare face-only pass (`--fix-face`).
- **GIF edits of an existing image keep text readable.** The card's stat grid, the TV chyron and
  the lawn sign stayed exact in every frame. Text the model has to *invent* inside a GIF still
  garbles past one word (see the gpt-image-gif skill).
- **The model re-adds real logos from memory.** It drew the LinkedIn "in" back onto a page that had
  a plain briefcase, until the prompt said "keep the briefcase logo, do not draw a letter logo".
- **Frame sizes for GIFs.** The frames share one sprite sheet capped at 3840 px on its long edge
  and 8.3 MP in total. 8 frames of 768x768, 10 of 1024x576 and 12 of 768x768 all pass.
- **The files API refuses GIF uploads** (they come back as `.bin`). Host GIFs elsewhere, or feed
  the still and let the model make the GIF.

## ChatGPT route (no code)

1. Open ChatGPT, attach your selfie and, for a tile with a base, the base image. The links are in
   `scripts/tiles.json` → `base`.
2. Paste the tile's prompt from [references/prompts.md](references/prompts.md). Replace `{NAME}`
   and `{PRONOUNS}`, and call the selfie "image 2".
3. For the GIF tiles, attach the result and paste the GIF prompt, asking for "a looping animated
   GIF" ([@op7418](https://x.com/op7418/status/2118184315507118272) showed ChatGPT doing this on
   launch day). If your ChatGPT returns a still, use the varg route for the GIF tiles.
4. Save each result as `<tile>.png` or `.gif` in one folder and run `collage.py` on it.
   Without Python, any 4:5 grid tool works.

## Files

- `scripts/wokify.py`: the runner. It uploads the selfie, runs the tiles and their GIFs in
  parallel, and handles the face and logo fixes, `--dry-run`, `--only`, `--fresh` and `run.json`.
  Standard library only.
- `scripts/tiles.json`: every tile with its base image URL, prompt, size and GIF settings, plus the
  fix prompts. Edit prompts here.
- `scripts/collage.py`: the 4:5 X collage as JPG, plus MP4 and GIF with `--anim`.
- `scripts/presenter.py`: the presenter-mode slideshow video as a HyperFrames project.
- `references/prompts.md`: every prompt verbatim, for ChatGPT, with the research links and the
  prompts that made the base images.

Related skills: [gpt-image-2-6](../gpt-image-2-6/) (model guide, Flare vs Sunburst, prices),
[gpt-image-gif](../gpt-image-gif/) (GIF frame budget), [varg-ai](../varg-ai/) (API key, MCP).
