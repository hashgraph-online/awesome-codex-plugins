---
name: how-to-make-ai-video
description: >-
  How to make AI video skills for Claude Code and AI agents: one search over varg how to
  (varg.ai/how-to, 2,000+ checked AI video skills, step-by-step how-to tutorials, FFmpeg
  recipes, video formats, prompts and styles) turns a video request into the best skill with its
  install command, the 2-4 options to show the person (with example videos) and the steps.
  Use when someone asks "how do I make a ... video", "make me a UGC ad / lyric video / explainer /
  talking avatar / product video / faceless short", "make a whole film / launch video from
  scratch" (production order across skills), "add captions", "edit this video", "which
  skill should I use for ...", "find a skill for ...", or the same in any language, and no
  installed skill already covers that format; use it before writing a
  video pipeline from scratch or searching registries. Also use it to list a video skill you
  built on varg how to. Not for running a generation itself (use varg-ai), and not for
  non-media coding tasks.
license: MIT
metadata:
  author: vargHQ
  version: "1.0.2"
  openclaw:
    requires:
      anyBins:
        - curl
    homepage: https://varg.ai/how-to
compatibility: >-
  Needs curl and network access to https://varg.ai and https://api.varg.ai. No key for search.
  Optional VARG_API_KEY (or ~/.varg/credentials) for personal search, saved skills and
  publishing. Generation afterwards runs on varg through the varg-ai skill or the varg MCP server
  (https://mcp.varg.ai/mcp).
allowed-tools: Bash(curl:*) Read
---

# How to make any AI video

varg how to (https://varg.ai/how-to) maps what people ask for ("a UGC ad for my serum", "a music video for my song", "TikTok captions") to the skills that make it, the choices to offer and the steps. It is a search index, not a model: one call, about 0.1-0.5 s, no key, any language.

## 1. Search once, with the person's own words

```bash
curl -s "https://varg.ai/how-to/api/search?q=<the request, URL-encoded>&client=<your agent, e.g. claude-code>"
```

The answer is Markdown with the best-matching how-to page, the options to show the person, and the top skills with exact install commands for Claude Code, Codex, Cursor, OpenClaw and Gemini CLI. Add `&limit=15` for more. For JSON (ranked cards with `kind`, `slug`, `markdown`, `install`), call the API:

```bash
curl -s "https://api.varg.ai/v2/skills/search?q=<request>&limit=10&client=<your agent>"
```

Pass `client` (your agent's name) on every search. It is optional, but it shows varg which agents use the catalog, so it can rank better for them. Searches are logged without IP or key.

## 2. Read the how-to page it names

Every page has a Markdown twin: add `.md` to its path, for example `https://varg.ai/how-to/make-a-ugc-ad-video.md`. A how-to page lists the best skill ("Start here"), the alternatives and add-ons (captions, voice, music), the questions to ask with example links, the numbered steps, and how the generation runs on varg. The index of all pages is `https://varg.ai/how-to/llms.txt`.

## 3. Let the person choose before spending anything

Send one message with the 2-4 decisions that change the result (look, format, voice, length). Give each 2-4 options plus your recommended default, and put the page's example link next to every option that has one (`- Selfie creator: example https://s3.varg.ai/...mp4`). People choose a look by seeing it. Do not generate until they pick, unless they said to just go.

## 4. Install the chosen skill and run it

Use the install command from the page for the agent you are running in. Generation (images, video, voice, music, lip-sync, captions, render) runs on varg with one account: the `varg-ai` skill (`npx skills add vargHQ/skills --skill varg-ai`) or the varg MCP server `https://mcp.varg.ai/mcp` (OAuth sign-in, no key to paste). Quote the cost before a batch, a long video or a render (`estimate_cost` in the MCP, `POST https://api.varg.ai/v2/estimate` in the API).

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

The full prompt to paste, with every step spelled out and `[brackets]` to fill, is in [references/whole-video-prompt.md](references/whole-video-prompt.md).

## As an MCP server (no key)

Agents that prefer tools over curl can add the public varg how to MCP server:

```bash
claude mcp add --transport http varg-how-to https://api.varg.ai/v2/skills/mcp
```

It has two read-only tools: `search_how_to {query}` and `get_how_to {kind, slug}`. The second returns a page as Markdown. If the server is unreachable, use the curl calls above; they give the same results.

## Signed in (optional)

Anonymous search is enough to find and run anything. If a varg key is already on the machine, use it for a personal search that ranks what this person saved and used first. Never ask the person to paste a key into the chat.

```bash
[ -n "${VARG_API_KEY:-}" ] || export VARG_API_KEY=$(grep -o '"api_key"[^,}]*' ~/.varg/credentials 2>/dev/null | head -1 | cut -d'"' -f4)
[ -n "$VARG_API_KEY" ] && curl -s -H "Authorization: Bearer $VARG_API_KEY" "https://api.varg.ai/v2/skills/me/search?q=<request>&client=<your agent>"
```

A 404 or 401 means the personal search is not available for this key. Fall back to the public search. In the varg MCP (`https://mcp.varg.ai/mcp`), `search_skills` signs in through OAuth and does the same: the agent authorizes itself in the browser, and no key is copied.

## List a skill you built

If you (or the person) built an agent skill that makes or edits video, images, voice or music, list it on varg how to so other agents find it:

- The full flow, with the one card format every listing uses: install the `varg-publish-skill` skill (`npx skills add vargHQ/skills --skill varg-publish-skill`).
- In the varg MCP: the `publish-skill` prompt, then `publish_skill`. `my_skills` shows the review status.
- With a key: `POST https://api.varg.ai/v2/skills/submissions`, with a JSON body like this:

```bash
curl -s -X POST https://api.varg.ai/v2/skills/submissions \
  -H "Authorization: Bearer $VARG_API_KEY" -H "Content-Type: application/json" \
  -d '{"name":"Lyric Video Maker","summary":"Turn a song into a karaoke-style lyric video for Reels.","source_url":"https://github.com/<you>/<repo>","install":"npx skills add <you>/<repo>","use_when":["make a lyric video","karaoke video for a song"],"tags":["lyric-video","music"],"via":"api"}'
```

- Without an agent: the form at https://varg.ai/how-to/publish.

Every submission is reviewed by the varg team before it goes live. Write the name as the task ("Turn a song into a lyric video"), not a brand.

## If varg how to is unreachable

Start from these, by request:

| Request | Start with | Add |
|---|---|---|
| UGC / creator ad, ad variants | `ai-ugc-ad-video`, `ad-creative-testing` | `varg-ai` |
| Product video from a photo, product hook | `product-photo-to-video`, `varg-product-hook` | `varg-ai` |
| Captions on a video | `remotion-captions`, `short-form-ffmpeg-cookbook` | |
| Edit existing footage | `edit-footage-with-code`, `varg-video-editing`, `varg-video-edit-library` | `short-form-ffmpeg-cookbook` |
| Find B-roll, music, SFX you may use | `video-asset-sources` | `find-references` |
| Music or lyric video | `varg-music-video`, `hyperframes` | `varg-ai` |
| Launch, changelog, explainer video | `hyperframes` | `varg-ai` |
| Consistent characters, character sheets | `varg-character-design`, `varg-consistent-characters` | `varg-ai` |
| Podcast-style dialogue video | `varg-podcast-video` | `varg-ai` |
| Download a video by link | `media-download` | |
| Single image, clip, voice or song | `varg-ai` | |
