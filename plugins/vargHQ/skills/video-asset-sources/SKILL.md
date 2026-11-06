---
name: video-asset-sources
description: >-
  Find B-roll, stock footage, music, sound effects, motion blocks, lower thirds, transitions, fonts, icons, logos, LUTs
  and HDRIs that an AI agent can really fetch and legally put in a video. A decision procedure over 97 databases, each
  tested on 2026-11-03: which ones answer an agent at all, which query works, which license holds, and when to generate
  instead. Includes 37 tested no-key queries, the traps (easy APIs you cannot use commercially, popular lists that break
  a license), and a credits file for every asset. Use for "find b-roll", "stock footage for this", "royalty free music",
  "free sound effects", "whoosh sound", "free video assets", "pexels api", "freesound", "which database should I use",
  "can I use this clip commercially", or whenever an edit needs a file it does not have. Not for references to study
  rather than use (find-references) or for the edit itself (edit-footage-with-code).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  openclaw:
    requires:
      anyBins:
        - curl
        - python3
    homepage: https://github.com/vargHQ/skills/tree/main/video-asset-sources
compatibility: >-
  Needs curl. scripts/record_asset.py needs Python 3. Optional keys, all free to get: PEXELS_API_KEY, PIXABAY_API_KEY,
  FREESOUND_API_KEY. This is not legal advice: a person owns the final license call on paid work.
allowed-tools: Bash(curl:*) Bash(python3:*) Read Write
---

# Video asset sources

Of 97 databases we tested, 14 have no route an agent can use and 7 more need a login. Several of the most recommended ones fail in ways that are not visible: the download works and the license does not. So route before you search, and record the license of every file.

## Rules

1. **Route first.** If a page says "Just a moment", "Attention Required" or "Security Checkpoint", stop. Do not retry, change tactics or look for a scraper. Use the next source.
2. **A file that downloads is not a licensed file.** A premium clip's 1080p URL answered 200 with no login.
3. **License gate.** Accept: CC0, public domain, CC BY with a credit line, the Pexels, Pixabay, Mixkit Free and Coverr licenses, a paid plan the person holds. Reject: anything with NC, ND or SA, Sampling+, RemArc, Mixkit Restricted, and anything with no license signal. Never guess a license.
4. **Record every asset:** `python3 <skill>/scripts/record_asset.py --file assets/whoosh.mp3 --source-url <url> --license CC0 --license-url <url>`. Paste the credits into the video's description when the license wants one.
5. **Reference libraries are for study.** Their frames never go in the output.
6. **Stop after 2 failed queries per source.** Searching longer costs more than generating. Do not place a loosely related clip because it was available.
7. **You cannot hear.** Check placed audio with a tool or a person. Old library recordings can open with a spoken slate ("Line FX 5 take 1!", per @xiaohuaxi28). Trust no filename.
8. **Take only what the edit uses.** Pixabay's docs forbid "systematic mass downloads", and most sites expect the same.

Timeouts: 15 s for most APIs. 40 s for Openverse, then move on: 13 of 19 timed searches failed even at 40-60 s.

## What to use for what

| Need | First | Then | Generate when |
|---|---|---|---|
| Generic B-roll | Pexels API with a key. No key: Mixkit, then Coverr | Pixabay API | The shot names a product, person or place, or 2 queries found nothing matching the line |
| Real-world or archival | Wikimedia Commons. Space and Earth: NASA | Internet Archive, license filter on | **Never for a claim of fact.** Label a reconstruction, or use a graphic |
| Music bed | A subscription the person holds (Epidemic Sound MCP). No plan: Incompetech if a credit is fine, Mixkit if not | Generated bed: varg `mureka_9_5` | Exact length and structure, or no credit line possible |
| Sound effect | Freesound filtered to CC0 | Mixkit, Kenney for UI ticks, HyperFrames' bundled files | A signature sound (ElevenLabs), or a hit that must land on a frame across re-renders |
| Motion block, lower third, transition | HTML project: HyperFrames registry. Remotion: video-shotcraft, remotion-bits, `@remotion/transitions` | LottieFiles, Herk Edit Kit's draft cards, varg How-To | It must carry your data or brand. Write it, seek-safe. Before any transition: would a hard cut work? |
| Do not know the effect's name | motion-prompt, 192 names | | |
| Reference for pacing | Refs MCP (launch-heavy). Measure with PySceneDetect or `hyperframes measure` | For a talking head, measure 3 videos your audience watches | |
| Reference for look | FILMGRAB by film title, Motionographer | A person pulls frames from ShotDeck or Frameset | |
| Font | Fontsource | Google Fonts, Fontshare | Never |
| LUT or grade | `hyperframes media-treatment`, or ffmpeg curves | Lutify.me free, slaycamera/luts, G'MIC | You have a reference frame: a LUT from your own grade has clean rights |
| HDRI, texture, 3D | Poly Haven (CC0) | ambientCG, then 3D Asset Server across 26 sites | Rarely |
| Logo | The brand's press kit | Simple Icons, then SVGL | Never for a real brand. CC0 on a collection is not permission for the trademark |
| Icon | Lucide | Iconify, pinned to one set, license read | |

Exact queries: [references/tested-queries.md](references/tested-queries.md). Every source with its route, license and score: [references/all-sources.md](references/all-sources.md).

## Traps worth memorizing

| Looks fine | Why it is not |
|---|---|
| **BBC Sound Effects** | A keyless API over 33,066 clips, but RemArc bars commercial use, and an agent never sees that license |
| **Freesound, unfiltered** | Mixes CC0 with NC and Sampling+. Always filter |
| **Internet Archive** | About 81% of "ocean" results carry no license URL, and results include broadcast TV |
| **Coverr results** | `user-ai-*` and `*premium*` ids mixed in: 11 of 61 on one page |
| **Mixkit** | A second, Restricted license sits beside the free one, so check each item |
| **unDraw** | Its license bars automated search and download, and copied "17 assets" lists tell you to hand it to Claude |
| **MusicGen, local** | `facebook/musicgen-small` is CC-BY-NC-4.0, and HyperFrames' free music route can fall back to it |
| **video-talkcraft** | Listed as free on X, but PolyForm Noncommercial |
| **Openverse** | The most-saved source on X and HyperFrames' default for SFX, but unreliable when tested. Never a hard dependency |
| **Iconify** | One API, mixed licenses: 53 of 276 sets are CC BY, 6 GPL, 2 non-commercial |

Also check products, not only videos: Remotion needs a paid company license above 3 employees. GSAP's terms bar visual no-code builders that compete with Webflow, while using it in a video is fine. React Bits bars reselling components.

The full list of 36, with evidence: [references/traps.md](references/traps.md).

## When a need is not listed

1. Search varg How-To once: `curl -s 'https://api.varg.ai/v2/skills/search?q=QUERY&limit=5'`. (Disclosure: varg makes this skill and that catalog. Rank it by what it returns.)
2. For a 3D or game asset, search 3D Asset Server.
3. Try one open source with a license field. If nothing matches, generate.

## Adding a key

The free keys change the answer for B-roll. Ask the person only when the job needs it:

| Key | Unlocks | Where |
|---|---|---|
| `PEXELS_API_KEY` | B-roll search with orientation filters | https://www.pexels.com/api/ |
| `PIXABAY_API_KEY` | B-roll fallback | https://pixabay.com/api/docs/ |
| `FREESOUND_API_KEY` | License filter in an API, with durations | https://freesound.org/apiv2/apply |
