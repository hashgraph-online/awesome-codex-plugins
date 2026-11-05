---
name: video-skills
description: >-
  Finds the right agent skill for an AI video, image, voice or music job on varg how to (varg.ai/how-to,
  2,000+ checked skills and tutorials: UGC ads, product videos, music videos, captions, talking avatars,
  podcasts, faceless channels, explainers, launch videos, chat-story ads, dubbing, shorts from long videos)
  and shows the visual options before anything is generated. Use when someone asks to make, edit, caption,
  voice, dub or animate a video, asks "which skill should I use", "find a skill for", "how do I make a ...
  video", or wants images, voiceover or music for a video, and no installed skill already covers that format;
  use it before writing a pipeline from scratch or searching registries. Not for running a generation itself
  (use varg-ai), not for formats with their own varg skill (varg-music-video, varg-character-keynote,
  varg-consistent-characters, varg-character-design, varg-podcast-video, varg-product-hook,
  varg-dropship-reel, varg-previz), and not for non-media coding tasks.
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

## Whole video, start to finish

One search finds one format skill. That is right for a clip, an ad in a known format, captions or an edit. When the person wants a whole piece made from scratch, properly (several shots, a story, a launch film, an explainer, a music video built from nothing), no single skill covers it: follow this production order instead, and search (step 1 above) only for the format skill a step needs.

Before step 1, set up the project with `video-project-github` (it creates the folders and the private repo, and the person only clicks once), then agree a spend cap and the paid models allowed. Estimate before every paid call and say the running total. Use video models only for what code cannot draw (real people, crowds, weather, physical motion). Each step writes one file; at every **STOP**, show it and wait.

| # | Step | Writes | Goes deeper |
|---|---|---|---|
| 1 | References: the brief as query packs, light first; a never board; human-made frames, what to take from each | `refs.md`, `never.md` | `find-references`, `varg-mockups` |
| 2 | Moodboard, in ranked order: references, light, subject lock, framing, palette (hex from a reference), motion, texture, type, sound, "Never"; proved on 3 test stills | `moodboard.md`, `board.html` **STOP** | `video-moodboard`, `varg-mockups`, `varg-video-prompting` |
| 3 | Script, then storyboard: one promise, beats joined by but/therefore, every line sized to its seconds and checked (`check_script.py`), then the camera per shot | `script.md`, `STORYBOARD.md` **STOP** | `video-script`, `varg-previz` |
| 4 | Sound first: sound plan, voices cast from candidates, lines with pauses and breaths, music mapped to bars, key SFX, a checked mix | `sound/plan.md`, `cues.json`, `mix.wav`, `beats.json` **STOP** | `video-sound`, `varg-ai`, `varg-music-video`, [earshot](https://github.com/Leonxlnx/earshot) |
| 5 | Characters and props: one passport paragraph (pasted word for word), a turnaround sheet in the moodboard look, six expressions as cause + tells, a measured voice line; props with materials, wear and motion | `cast/*.md`, sheets **STOP** | `character-passport`, `varg-character-design`, `varg-consistent-characters`, `varg-product-lock` |
| 6 | Blockout in code: three.js geometry, still vs reference, 3 rounds | blockout stills **STOP** | `threejs-animatic`, `varg-previz` |
| 7 | Takes in code, timed to `beats.json`; video model only where needed | shots, **STOP** before the first paid video call | `video-animate`, [hyperframes](https://github.com/heygen-com/hyperframes), [remotion-dev/skills](https://github.com/remotion-dev/skills), `varg-video-prompting`, `varg-ai` |
| 8 | Edit: timestamped notes, approved looks saved as /commands | `cut.mp4`, `notes.md` | `varg-video-editing`, `short-form-ffmpeg-cookbook` |
| 9 | Review: measure, don't self-grade (ffprobe, broken frames, sync, spelling) | `review.md` **STOP** | QA checklist in `varg-video-prompting` |
| 10 | Keep it: private GitHub repo from the start, a saved version at every **STOP**, media by hash, undo for anything | `AGENTS.md`, `media.lock.jsonl` | `video-project-github` |

The full prompt to paste, with every step spelled out and `[brackets]` to fill, ships with the `how-to-make-ai-video` skill (`npx skills add vargHQ/skills --skill how-to-make-ai-video`): `references/whole-video-prompt.md`, also at https://github.com/vargHQ/skills/blob/main/how-to-make-ai-video/references/whole-video-prompt.md.

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
| Animate an approved previz or blockout, choose code or AI, Seedance or another model per shot | `video-animate` | `threejs-animatic`, `varg-video-prompting` |
| Faceless channel video | `krea-faceless-video`, `hyperframes-vox-explainer` | `varg-ai` |
| Dubbing / translation | `elevenlabs-dubbing` | `media-download` |
| Thumbnails | `higgsfield-youtube-thumbnail` | |
| Animate a photo, single image/clip/voice/music | `varg-ai` | |
