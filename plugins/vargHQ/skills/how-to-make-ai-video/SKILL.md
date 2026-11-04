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
  version: "1.0.0"
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

One search finds one format skill. That is right for a clip, an ad in a known format, captions or an edit. When the person wants a whole piece made from scratch, properly (several shots, a story, a launch film, an explainer, a music video built from nothing), no single skill covers it: follow this production order instead, and search (step 1 above) only for the format skill a step needs.

Before step 1, set up the project with `video-project-github` (it creates the folders and the private repo, and the person only clicks once), then agree a spend cap and the paid models allowed. Estimate before every paid call and say the running total. Use video models only for what code cannot draw (real people, crowds, weather, physical motion). Each step writes one file; at every **STOP**, show it and wait.

| # | Step | Writes | Goes deeper |
|---|---|---|---|
| 1 | References: real film stills and frames, what to take from each | `refs.md` | `find-references`, `varg-mockups` |
| 2 | Moodboard, in ranked order: references, light, subject lock, framing, palette (hex from a reference), motion, texture, type, sound, "Never"; proved on 3 test stills | `moodboard.md`, `board.html` **STOP** | `video-moodboard`, `varg-mockups`, `varg-video-prompting` |
| 3 | Script, then storyboard: one promise, beats joined by but/therefore, every line sized to its seconds and checked (`check_script.py`), then the camera per shot | `script.md`, `STORYBOARD.md` **STOP** | `video-script`, `varg-previz` |
| 4 | Sound first: sound plan, voices cast from candidates, lines with pauses and breaths, music mapped to bars, key SFX, a checked mix | `sound/plan.md`, `cues.json`, `mix.wav`, `beats.json` **STOP** | `video-sound`, `varg-ai`, `varg-music-video`, [earshot](https://github.com/Leonxlnx/earshot) |
| 5 | Characters and props: one passport paragraph (pasted word for word), a turnaround sheet in the moodboard look, six expressions as cause + tells, a measured voice line; props with materials, wear and motion | `cast/*.md`, sheets **STOP** | `character-passport`, `varg-character-design`, `varg-consistent-characters`, `varg-product-lock` |
| 6 | Blockout in code: three.js geometry, still vs reference, 3 rounds | blockout stills **STOP** | `threejs-animatic`, `varg-previz` |
| 7 | Takes in code, timed to `beats.json`; video model only where needed | shots, **STOP** before the first paid video call | `video-animate`, [hyperframes](https://github.com/heygen-com/hyperframes), [remotion-dev/skills](https://github.com/remotion-dev/skills), `varg-video-prompting`, `varg-ai` |
| 8 | Edit: timestamped notes, approved looks saved as /commands | `cut.mp4`, `notes.md` | `edit-footage-with-code`, `varg-video-editing`, `short-form-ffmpeg-cookbook` |
| 9 | Review: measure, don't self-grade (ffprobe, broken frames, sync, spelling) | `review.md` **STOP** | QA checklist in `varg-video-prompting` |
| 10 | Keep it: private GitHub repo from the start, a saved version at every **STOP**, media by hash, undo for anything | `AGENTS.md`, `media.lock.jsonl` | `video-project-github` |

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
