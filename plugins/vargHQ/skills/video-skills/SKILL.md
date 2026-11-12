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
  version: "1.1.2"
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

One search finds one format skill. That is right for a clip, an ad in a known format, captions or an edit. When the person wants a whole piece made from scratch, properly (several shots, a story, a launch film, an explainer, a music video built from nothing), no single skill covers it: follow the ten steps below, and search (step 1 above) only for the format skill a step needs.

The route lives at https://varg.ai/how-to/make-a-video-in-ten-steps.md and is kept current there; read it first when you can reach it. The line a person pastes to start it:

```text
Make my video in ten steps. Read https://varg.ai/how-to/make-a-video-in-ten-steps.md and follow it: one step at a time, stop for my yes at every STOP, and tell me the cost before anything paid.

The video: [what it is, who it is for, how long, where it will be shown]
```

Rules:

- Before step 1, ask once for what is missing: what the video is, who it is for, the length, the platform and aspect ratio, the brand (name, colours, type, logo), what the person loves and hates in videos like it, a spend cap and the paid models allowed. Then set up the project with step 10's skill, so every STOP is a saved version.
- One step at a time, in order. Before a step, read its guide and install its skill. Skip a step only when the person already has its output. When a skill names a different next step, this order wins; a video drawn entirely in code still takes every step, and step 7 sends its shots to code.
- Each step writes its files. At every STOP, show them and wait for the person's yes.
- Estimate the cost before every paid call and say the running total. Never go over the cap. Nothing before step 7 needs a video model: steps 2 and 5 make a few paid stills and step 4 paid voice and music, each after its estimate and a yes.
- Use video models only for what code cannot draw: real people, crowds, weather, physical motion. Text, numbers, UI, charts and logos are built in code.
- Sound is locked before picture (step 4), and the picture is cut to it.
- Measure, do not grade yourself (step 9). Between close takes a person picks.
- Generation runs on varg with one account: the varg-ai skill (npx skills add vargHQ/skills --skill varg-ai) or the varg MCP server https://mcp.varg.ai/mcp.

| # | Step | Writes | Skill | Guide |
|---|---|---|---|---|
| 1 | **References** **STOP**: Write the brief, then one query pack per job the piece needs: light gets the most, then framing, people, location, texture, palette, type, motion, music. Search each source in its own words, open everything you keep, prove who made it, and show three candidates per job. Turn what the obvious search repeats into never.md. Sites that forbid bots go into links.md for the person to open. The person picks the references. | refs/refs.md, refs/never.md, refs/links.md, refs/board.html | `find-references`, `varg-mockups` | https://varg.ai/how-to/find-references-for-an-ai-video.md |
| 2 | **Moodboard** **STOP**: Write the board in ranked order: references, light, subject lock, framing, palette as hex taken from a reference, motion, texture, type, sound, and a Never list. Every line is a number or a named thing, and every hex comes from a picked reference, never from memory. Prove the board on three test stills before anything else is generated. | look/moodboard.md, look/board.html | `video-moodboard`, `varg-mockups`, `varg-video-prompting` | https://varg.ai/how-to/make-a-moodboard-for-an-ai-video.md |
| 3 | **Script** **STOP**: One promise, ten hooks to choose from, beats joined by BUT or THEREFORE, one spoken line per visual, every line sized to its seconds (about 2.5 words a second) and checked with the skill's check_script.py. Then the storyboard: timing and camera for every shot. | script.md, STORYBOARD.md | `video-script`, `varg-previz` | https://varg.ai/how-to/write-a-video-script-with-an-agent.md |
| 4 | **Sound and voice** **STOP**: Lock the sound before any picture: a sound plan, two or three voice candidates to pick from, lines written with pauses and breaths, music mapped to bars, the few effects that matter, and a mix measured by script. beats.json holds the time of every cut, hit and word; the picture is cut to it. | sound/plan.md, cues.json, mix.wav, beats.json | `video-sound`, `varg-ai`, `varg-music-video`, [earshot](https://github.com/Leonxlnx/earshot) | https://varg.ai/how-to/design-sound-and-voice-for-ai-video.md |
| 5 | **Characters and props** **STOP**: For every person, creature, product and prop: one passport paragraph that is pasted word for word into every later prompt, a turnaround sheet in the moodboard's look, six expressions written as a cause plus physical tells, and a measured voice line. Props get materials, wear and how they move. | cast/*.md, character and prop sheets | `character-passport`, `varg-character-design`, `varg-consistent-characters`, `varg-product-lock` | https://varg.ai/how-to/design-characters-and-props-for-ai-video.md |
| 6 | **Previz in code** **STOP**: Block every shot in code (Three.js by default, Blender when the guide says so): geometry, camera and timing from the storyboard and beats.json. Render one still next to its reference and close the gaps, three rounds, before any motion. The previz owns camera, blocking and timing from here on. | staging.json, blockout stills, previz.mp4 | `code-to-video-previz`, `threejs-animatic`, `varg-previz` | https://varg.ai/how-to/previz-a-video-in-threejs-or-blender.md |
| 7 | **Animate** **STOP**: Route each element, not each shot: code draws what must be exact (text, numbers, UI, logos), the video model does what code cannot (faces, cloth, weather, crowds). A cheap 480p pass first; try timing and camera variants in the previz, then roll takes that vary only the performance. STOP before the first paid video call, with the estimate. | takes/*.mp4 with one sidecar per take | `video-animate`, [hyperframes](https://github.com/heygen-com/hyperframes), [remotion-dev/skills](https://github.com/remotion-dev/skills), `varg-video-prompting`, `varg-ai` | https://varg.ai/how-to/animate-a-previz-with-ai-video-models.md |
| 8 | **Edit**: Cut the speech first, lock the sound, then add picture, graphics last. Assemble on beats.json. The person gives notes with timestamps and you fix exactly those; an approved look or fix is saved as a reusable command so it stays the same. | cut.mp4, notes.md | `edit-footage-with-code`, `video-asset-sources`, `varg-video-editing`, `short-form-ffmpeg-cookbook` | https://varg.ai/how-to/edit-a-video-with-hyperframes-and-agents.md |
| 9 | **Judge** **STOP**: Measure, do not grade yourself. Code reads every frame and writes a time, a number and a picture for each flag (duration, black or frozen frames, seams, sync, loudness, spelling on screen). A fresh agent reads only the flags. Takes rank on counted defects, and a person picks between close ones. | review.md | `media-judge`, QA checklist in `varg-video-prompting` | https://varg.ai/how-to/judge-an-ai-video-without-bias.md |
| 10 | **Keep it in GitHub**: Set this up before step 1 and use it at every STOP: a private GitHub repo, text in git, media listed by hash with its bytes in Releases, keys in .env behind a commit hook. Save a version at every STOP so anything can be undone, and prove the backup restores byte for byte. | AGENTS.md, media.lock.jsonl | `video-project-github` | https://varg.ai/how-to/keep-a-video-project-in-github.md |

Before each step, read its guide (the `.md` link) and install its skill (`npx skills add vargHQ/skills --skill <skill>`). Every claim in the guides is traced to its source in the evidence bank: https://varg.ai/how-to/guide-pages/evidence-bank/data/PLAYBOOK.md.

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
