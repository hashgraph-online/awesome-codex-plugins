---
name: video-skills
description: >-
  Finds the right agent skill for an AI video, image, voice or music job on varg how to
  (varg.ai/how-to, 2,000+ checked skills and how-to tutorials: UGC ads, ad variants, product videos, music and lyric videos,
  captions, talking avatars, podcast videos, faceless channels, explainers, launch and changelog
  videos, slideshows, chat-story and Notes ads, logo stings, dubbing, thumbnails, shorts from long
  videos) and shows the person the visual options before anything is generated.
  Use when someone asks to make, edit, caption, voice, dub or animate a video, asks "which skill
  should I use", "find a skill for", "how do I make a ... video", or wants images, voiceover or
  music for a video, and no installed skill already covers that format; use it before writing a
  pipeline from scratch or searching registries. Not for running a generation itself (use
  varg-ai), not for formats with their own varg skill (varg-music-video, varg-character-keynote,
  varg-consistent-characters, varg-character-design, varg-podcast-video, varg-product-hook,
  varg-dropship-reel, varg-previz), and not for
  non-media coding tasks.
license: MIT
metadata:
  author: vargHQ
  version: "1.1.0"
  openclaw:
    requires:
      anyBins:
        - curl
    homepage: https://varg.ai/how-to
compatibility: >-
  Needs curl and network access to https://varg.ai. Generation afterwards runs on varg
  through the varg-ai skill or the varg MCP server (https://mcp.varg.ai/mcp).
allowed-tools: Bash(curl:*) Read
---

# Video skills finder

varg how to (https://varg.ai/how-to) maps what people ask for ("a UGC ad", "клип на песню", "captions like TikTok") to the skills that make it, the choices to offer, and the steps. One search is usually enough.

## 1. Search once, with the person's own words

```bash
curl -s "https://varg.ai/how-to/api/search?q=<the request, any language, URL-encoded>&client=<your agent>"
```

It returns, as markdown: the best-matching how-to page, the options to offer, and the top skills with exact install commands for Claude Code, Codex, Cursor, OpenClaw and Gemini CLI. Add `&limit=15` for more. JSON: `/api/search.json?q=…`.

## 2. Read the how-to page it names

`https://varg.ai/how-to/<task-slug>.md` (for example `make-a-ugc-ad-video.md`) has the best skill ("Start here"), alternatives, add-ons (captions, voice, music), the questions to ask with example links, the steps, and how the generation runs on varg. Every catalog page has a `.md` twin; the full index is `https://varg.ai/how-to/llms.txt`. For the same search as a tool, add the public MCP server `https://api.varg.ai/v2/skills/mcp` (no key), or use the `how-to-make-ai-video` skill.

## 3. Let the person choose before spending anything

Send one message with the 2–4 decisions that change the result (look, format, voice, length), each with 2–4 options, plus your recommended default. Put the example link from the page next to every option that has one (`- Selfie creator — example: https://…/previews/….mp4`): people choose a look by seeing it, not by reading its name. Do not generate until they pick, unless they said to just go.

## 4. Install the chosen skill and run it

Use the install command from the page for the agent you are running in. Generation (images, video, voice, music, lip-sync, captions, render) runs on varg with one account: the `varg-ai` skill (`npx skills add vargHQ/skills --skill varg-ai`) or the varg MCP server `https://mcp.varg.ai/mcp` (OAuth sign-in, no key). Quote the cost in credits with varg's estimate (`estimate_cost` in the MCP, `POST /v2/estimate` in the API) before a batch, a long video or a render.

## If varg how to is unreachable

Start from these, by request:

| Request | Start with | Add |
|---|---|---|
| UGC / creator ad, ad variants | `fal-ugc`, `marketingskills-video` | `varg-ai` for generation, `iart-caption-animation` |
| Design a character, character sheet / turnaround, AI influencer or persona, mascot, the same character in new scenes | `varg-character-design` | `varg-ai` |
| A specific character type: granny or grandpa, big guy, cringe deadpan guy, very beautiful woman, fitness character, absurd creature or mascot, Simpsons/Pixar-style cartoon | `varg-character-grandma`, `varg-character-big-guy`, `varg-character-cringe`, `varg-character-beautiful-woman`, `varg-character-fitness`, `varg-character-absurd`, `varg-character-cartoon` | `varg-character-design` |
| Multi-scene ad with the same actors, a recurring character or mascot | `varg-consistent-characters`, `fal-character-design` | `varg-character-design`, `varg-ai` |
| Product video from a photo | `krea-motion`, `fal-commercial` | `varg-ai` |
| Viral product hook, "TikTok made me buy it" clip, product in use from photos | `varg-product-hook` | `media-download`, `varg-ai` |
| Dropshipping guide reel: product, price in China vs Shopify, laptop and pen, "Comment GUIDE" | `varg-dropship-reel` | `varg-product-hook`, `varg-ai` |
| Unboxing, ASMR or satisfying product video from photos | `varg-unboxing-video` | `varg-product-lock` |
| Product changes shape, logo or label between AI shots | `varg-product-lock` | `varg-ai` |
| Is this AI ad allowed on TikTok Shop / Meta, AI labels, FTC | `ai-ad-compliance-check` | |
| Clone winning competitor ads, Meta Ad Library, new angles | `varg-ad-library-remix` | `ai-ad-compliance-check` |
| 20 variants or new hooks for a winning ad | `varg-ad-variants` | `ad-creative-testing` |
| Singing mascot, jingle or cartoon product ad | `varg-mascot-jingle-ad` | `varg-character-absurd` |
| Translate or dub a video ad for other markets | `varg-ad-localize` | `varg-ad-variants` |
| Clothing try-on video from a flat-lay | `varg-tryon-video` | `varg-character-design` |
| Shorts from a long video / podcast recording | `clipify`, `herk-edit-kit` | `media-download` |
| Podcast-style or two-character dialogue video (generated) | `varg-podcast-video` | `varg-ai` |
| Captions on a video | `remotion-captions`, `iart-caption-animation` | |
| Talking avatar / presenter | `inference-sh-ai-avatar-video`, `varg-character-keynote` (speaker on stage) | `varg-ai` (voice, lip-sync) |
| Launch, changelog, explainer, data video | `hyperframes` (HeyGen) | `hyperframes-registry`, `varg-ai` |
| Music video / lyric video | `varg-music-video`, `hyperframes`, `motion-graphics-music-video` | `varg-ai` |
| Plan a multi-shot video, storyboard, camera blocking | `varg-previz` | `varg-ai` |
| Faceless channel video | `krea-faceless-video`, `hyperframes-vox-explainer` | `varg-ai` |
| Dubbing / translation | `elevenlabs-dubbing` | `media-download` |
| Thumbnails | `higgsfield-youtube-thumbnail` | |
| Animate a photo, single image/clip/voice/music | `varg-ai` | |
