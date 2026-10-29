# varg — AI Agent Skills for Video, Image, Speech & Music Generation

A collection of [Agent Skills](https://agentskills.io) for AI video, image, speech, and music generation using the varg platform. One skill to access Seedance 2.5, Kling 4, Wan 3, Veo 3.1, Nano Banana 2.1, GPT Image 2.5, ElevenLabs v4 and 200+ more models — zero code, just prompt.

<p align="center">
  <a href="https://github.com/vargHQ/skills/stargazers"><img src="https://img.shields.io/github/stars/vargHQ/skills" alt="GitHub stars"></a>
  <a href="https://github.com/vargHQ/skills/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="License"></a>
</p>

Works with **Claude Code**, **Cursor**, **Windsurf**, **OpenCode**, **ClawHub**, and any tool that supports the [Agent Skills](https://agentskills.io) standard.

## Installation

### ClawHub (recommended)

```bash
# Install a specific skill
npx clawhub@latest install vargai

# Or install all skills from this repo
npx clawhub@latest install vargai
```

### Claude Code plugin

Installs the `varg-ai` skill and the hosted varg MCP server (`https://mcp.varg.ai/mcp`, sign in with OAuth on first use):

```bash
claude plugin marketplace add vargHQ/skills
claude plugin install varg@varg
```

Or inside Claude Code: `/plugin marketplace add vargHQ/skills`, then `/plugin install varg@varg`.

### Kiro power

[`powers/varg-how-to`](powers/varg-how-to) connects the keyless varg how to MCP (`https://api.varg.ai/v2/skills/mcp`) in Kiro: Powers panel → **Add Custom Power** → **Import power from GitHub** → `https://github.com/vargHQ/skills/tree/main/powers/varg-how-to`.

### Claude Code (manual)

```bash
# Clone into personal skills directory (available in all projects)
git clone https://github.com/vargHQ/skills.git ~/.claude/skills/varg

# Or symlink individual skills
ln -s /path/to/skills/varg-ai ~/.claude/skills/varg-ai
```

### OpenCode

```bash
# Clone into any supported skills directory
git clone https://github.com/vargHQ/skills.git ~/.opencode/skills/varg

# Also works with:
#   ~/.agents/skills/
#   .opencode/skills/ (project-level)
```

### Agent Skills CLI

```bash
npx skills add vargHQ/skills --yes
```

## Available Skills

**How to make any AI video:** not sure which skill fits a video request? Start with [how-to-make-ai-video](./how-to-make-ai-video/). It searches varg how to ([varg.ai/how-to](https://varg.ai/how-to)), 2,000+ checked video skills and step-by-step tutorials, and lists the options to offer before anything is generated. No key needed. The same search is available as a public MCP server: `claude mcp add --transport http varg-how-to https://api.varg.ai/v2/skills/mcp`.

**Publish your own skill:** connect the varg MCP (`claude mcp add --transport http varg https://mcp.varg.ai/mcp`) and ask your agent to "publish this skill to varg how to" (install [varg-publish-skill](./varg-publish-skill/) so every listing gets the same card). It reads the skill, shows you the card and sends it with `publish_skill`; the varg team reviews it and it becomes searchable at [varg.ai/how-to](https://varg.ai/how-to). No agent: the form at [varg.ai/how-to/publish](https://varg.ai/how-to/publish). Skills that join this repo go through a pull request (see the README of each skill and [vargHQ/skills-marketplace](https://github.com/vargHQ/skills-marketplace) → *Adding a skill*).

| Skill | Description | ClawHub Slug |
|-------|-------------|--------------|
| [varg-ai](./varg-ai/) | AI video, image, speech, and music generation | `vargai` |
| [varg-previz](./varg-previz/) | Plan multi-shot AI videos: story, anchors, a three.js grey-box previz with auto cameras, Seedance video-to-video packs | — |
| [varg-video-editing](./varg-video-editing/) | Which service to edit existing footage with, job by job (cuts, talking-head cleanup, Shorts, captions, AI restyle and swaps, dubbing, upscaling, QA, handing off to Resolve/Premiere/Final Cut), plus the rules that keep cuts frame-accurate and in sync | — |
| [varg-video-edit-library](./varg-video-edit-library/) | 206 named edits for footage you already have, each with the look, when to use it, the common mistake, timings and a recipe for FFmpeg, HyperFrames, Remotion and CapCut: cuts and pacing (J/L cuts, match cuts, speed ramps), transitions (CapCut-style, every FFmpeg xfade, Remotion TransitionSeries, HyperFrames and GL shaders), headlines, quotes, end cards, UI walkthroughs, cursors, device mockups, code and terminal, AI agent flows, numbers and charts, logo walls, grids and backdrops | — |
| [media-download](./media-download/) | Save videos/audio by link from X, YouTube, Instagram, Facebook, TikTok and 1800+ sites (yt-dlp), and Pinterest images by pin, board or search (gallery-dl). Local, no API key | — |
| [short-form-ffmpeg-cookbook](./short-form-ffmpeg-cookbook/) | Short-form FFmpeg cookbook: copyable commands for Reels. Crop to 9:16, burn captions (SRT/ASS), trim and join, music with ducking; every command tested. Local, no API key | — |
| [paper-shaders](./paper-shaders/) | Frame-exact Paper Shaders backgrounds, textures and logo stings for HyperFrames and Remotion videos | `paper-shaders` |
| [how-to-make-ai-video](./how-to-make-ai-video/) | How to make AI video skills for Claude Code and AI agents: one search over varg how to gives the best skill with its install command, the options to show (with example videos) and the steps; also lists a skill you built on varg how to | — |
| [varg-publish-skill](./varg-publish-skill/) | Turn your agent skill into a varg how to listing: checks it against the standard, fills the one card format every listing uses, shows it to you and publishes it for review through the varg MCP | — |
| [video-skills](./video-skills/) | Finds the right skill for any AI video, image, voice or music job on varg how to and shows the options before anything is generated | — |
| [varg-music-video](./varg-music-video/) | Direct an AI music video for a song: beat grid, cast and references, storyboard on downbeats, stills first, Seedance shots, lip-sync pass, lyrics in code, platform masters | — |
| [varg-character-keynote](./varg-character-keynote/) | A 9:16 "character on stage" video in one render: a custom character delivers a punchy line at a keynote with native voice and applause | — |
| [varg-consistent-characters](./varg-consistent-characters/) | Multi-scene ads where the same actors, outfits and location stay consistent: profile cards, location card, stills for approval, native-audio clips, captions and QA | — |
| [varg-character-design](./varg-character-design/) | How to make characters people remember: definition, details, clothing, character card, a sheet that stays consistent, reuse in Nano Banana, Kling 4 and Seedance 2.5; moderation-safe wording and famous looks without IP names | — |
| [varg-character-grandma](./varg-character-grandma/) | Grandma and grandpa characters: age vs behaviour, real wrinkles, a loud signature outfit | — |
| [varg-character-big-guy](./varg-character-big-guy/) | Big guy characters: size shown with visible cues, a small delicate job, played straight | — |
| [varg-character-cringe](./varg-character-cringe/) | Cringe deadpan characters: bizarre but believable, one outfit, one repeated action (the Jean Phil format) | — |
| [varg-character-beautiful-woman](./varg-character-beautiful-woman/) | Very beautiful women who look like real models: casting details, real skin, fashion and swimwear styling, wording that passes filters | — |
| [varg-character-fitness](./varg-character-fitness/) | Fitness characters: real muscle, a signature colour, catalog wording that gets sports bras past false blocks | — |
| [varg-character-absurd](./varg-character-absurd/) | Absurd characters and mascots: food or object + animal + one human detail, in 3D, clay or photoreal looks | — |
| [varg-character-cartoon](./varg-character-cartoon/) | Original characters in famous cartoon looks (yellow sitcom, 3D family film, anime, paper cut-out, clay, puppet), described without IP names | — |
| [varg-podcast-video](./varg-podcast-video/) | Podcast and two-character dialogue videos: studio set, wide master shot, close-ups and cutaways from it, 5 s scenes with native dialogue audio, stitched episode | — |
| [varg-product-hook](./varg-product-hook/) | The first 5-15 s of a product video: find a hook that already sells this kind of product, then remake the idea as realistic phone or security-cam footage with Seedance 2.5 from your product photos (backyard camera, torture test, problem → solution, satisfying close-up, gift reaction) | — |
| [varg-dropship-reel](./varg-dropship-reel/) | The 60-second faceless dropshipping guide reel end to end: product hook, laptop on a zigzag tablecloth with a hand pointing a marker at cost, price and demand, the steps, a night-skyline iPhone ending with "Comment GUIDE", word-by-word lime captions and the comment-to-DM funnel; scripts cut and caption the reel | — |
| [Turn product photos into an AI ASMR unboxing video](./varg-unboxing-video/) · `varg-unboxing-video` | Turn product photos into an unboxing or ASMR video: hands-only, timed VISUAL/ACTION/SOUND blocks on Seedance 2.5 with the box and product as references, native ASMR sound, no music | — |
| [Turn product photos into AI video that keeps the logo and shape](./varg-product-lock/) · `varg-product-lock` | Keep the product identical in every AI shot: lock sheet, multi-angle reference pack, camera-risk ladder, drift check with video_analyze, real packshot composited back | — |
| [Turn an AI video ad into a TikTok Shop and Meta compliance report](./ai-ad-compliance-check/) · `ai-ad-compliance-check` | Check an AI video ad against TikTok Shop, Meta, YouTube, FTC, New York and EU AI Act rules: video_analyze pulls every claim, a versioned rules file scores pass / fix / block with sources | — |
| [Turn winning competitor ads into new AI video ad angles](./varg-ad-library-remix/) · `varg-ad-library-remix` | Turn winning competitor ads (Meta Ad Library, TikTok Creative Center, Kalodata) into new angles: winner signals, video_analyze breakdown, angle × format × awareness gaps, originality check | — |
| [Turn one winning video ad into 20 AI ad variations](./varg-ad-variants/) · `varg-ad-variants` | Turn one winning ad into 20 Andromeda-safe variants: concepts × single-variable iterations, new hooks on varg, a tested FFmpeg hook-swap script with a manifest, naming and test plan | — |
| [Turn a product into an AI singing mascot jingle ad](./varg-mascot-jingle-ad/) · `varg-mascot-jingle-ad` | Turn a product into a singing mascot ad: claymation character with a lip-sync face, Lyria jingle trimmed to 15-30 s, Seedance 2.5 singing to the song, master track laid back on top | — |
| [Turn one video ad into 8 languages with AI dubbing](./varg-ad-localize/) · `varg-ad-localize` | Turn one video ad into 8+ TikTok Shop markets: transcreation with an offer card per market, same-voice ElevenLabs, lip-sync only where faces talk, re-cut on the new words, native review | — |
| [Turn a flat-lay photo into an AI virtual try-on video](./varg-tryon-video/) · `varg-tryon-video` | Turn a flat-lay of clothing into a try-on video: Bria virtual try-on still, fit-check motions on Kling 4 (turn, tug, walk, mirror), honest size captions | — |
| [ecommerce-video-ads](./ecommerce-video-ads/) | Ecommerce video ad skills for Claude Code and AI agents: the plan and the rules for product videos that sell on TikTok, TikTok Shop, Reels and Meta: four questions, angle, hook, format, casting, second-by-second script, product fidelity, platform rules (AI labels, Shop bans, FTC), cost gate, variants | — |
| [product-video-hooks](./product-video-hooks/) | Turn a product into scroll-stopping video hooks: three agreeing layers (frame, line, text), 70-line hook bank, claim checks, one MP4 per hook | — |
| [tiktok-shop-video](./tiktok-shop-video/) | Turn a product link into a TikTok Shop video: Shop styles, 18–35 s script, phone shot list, and the 2025–2026 rules (real presenter, no AI voice, no slideshow, no mismatched prices) | — |
| [ai-ugc-ad-video](./ai-ugc-ad-video/) | Open-source alternative to Arcads: AI UGC ads with an AI actor holding your real product, face, voice and label locked, phone-real prompts, no AI testimonials | — |
| [product-photo-to-video](./product-photo-to-video/) | Turn a product photo into a product video ad: truth sheet, cut-out, storyboard sheet, Seedance PRODUCT LOCK, repair pass, real packshot on the last second; ASMR unboxing, macro, 360° loop, try-on | — |
| [ad-creative-testing](./ad-creative-testing/) | Turn one winning ad into a creative testing plan: decode the winner, concepts Meta and TikTok treat as different, how many and when to judge, funnel diagnosis, kill/scale rules, naming | — |
| [ecommerce-video-edit](./ecommerce-video-edit/) | Turn raw product footage into a TikTok ad with FFmpeg: hook moved to second 0, dead air cut, text hook and CTA in the safe zone, -14 LUFS, one MP4 per hook, 4:5 cut; tested commands, local, no API key | — |

## Requirements

- `VARG_API_KEY` (get at [varg.ai](https://varg.ai)) or the hosted varg MCP (`https://mcp.varg.ai/mcp`) -- required for varg-ai, varg-previz and the format skills (varg-music-video, varg-character-keynote, varg-consistent-characters, varg-character-design and its category recipes, varg-podcast-video, varg-product-hook, varg-dropship-reel, ecommerce-video-ads, ai-ugc-ad-video, product-photo-to-video); media-download, short-form-ffmpeg-cookbook, paper-shaders, how-to-make-ai-video, varg-publish-skill (publishes with a varg login or key, no credits), video-skills, varg-video-edit-library, varg-video-editing, ecommerce-video-edit, ad-creative-testing, product-video-hooks (written hooks) and tiktok-shop-video (scripts) need no key (varg-video-editing uses varg only for the paid edits it recommends)
- **Cloud mode**: curl only (zero dependencies)
- **Local mode**: bun runtime + ffmpeg
- **paper-shaders**: Node 22 and ffmpeg for HyperFrames (`npx hyperframes`), or a Remotion 4 project

## What this plugin connects to

Everything the plugin runs, sends or fetches:

- **varg how to MCP** (`https://api.varg.ai/v2/skills/mcp`): no key. Sends the search text you or the agent type (`search_how_to`) and returns how-to cards. Searches are logged without IP or key (query, MCP client name, top results).
- **varg MCP** (`https://mcp.varg.ai/mcp`): OAuth sign-in to your varg account. Sends generation requests (prompts, uploaded or linked media) and spends your varg credits; results are stored in your varg account and served from `s3.varg.ai`.
- **varg API** (`https://api.varg.ai`): the skills' `curl` examples send `VARG_API_KEY` from your environment as a Bearer token to api.varg.ai only, never to any other host. Skills that need no key are listed under Requirements.
- **media-download**: runs `yt-dlp` on your machine against the video link you give it (X, YouTube, Instagram, TikTok, Pinterest and other sites yt-dlp supports) and saves the file locally.
- **paper-shaders** and **varg-previz**: render locally; varg-previz bundles three.js (MIT) in `varg-previz/templates/previz/vendor/` so the previz page works offline.
- The plugin has no hooks and changes no Claude settings or permissions.

Privacy: https://varg.ai/privacy · Terms: https://varg.ai/terms · Security: [SECURITY.md](./SECURITY.md)

## Skill Structure

Each skill follows the [Agent Skills specification](https://agentskills.io/specification):

```
skill-name/
├── SKILL.md            # Core instructions (required)
├── references/         # On-demand reference docs
│   ├── models.md       # Model catalog, pricing
│   ├── components.md   # Component reference
│   └── ...
├── scripts/            # Executable setup/helper scripts
│   └── setup.sh
└── assets/             # Static resources (optional)
```

## Adding a New Skill

1. Create a directory at the repo root with your skill name (lowercase, hyphens only):

```bash
mkdir my-new-skill
```

2. Create `my-new-skill/SKILL.md` with cross-compatible frontmatter:

```yaml
---
name: my-new-skill
description: >-
  What this skill does and when to use it.
  Include trigger keywords for auto-discovery.
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  openclaw:
    requires:
      env:
        - VARG_API_KEY
      anyBins:
        - curl
        - bun
    primaryEnv: VARG_API_KEY
    homepage: https://varg.ai
compatibility: >-
  Describe environment requirements here.
allowed-tools: Bash(bun:*) Bash(curl:*) Read Write Edit
---

Your skill instructions here...
```

3. Add reference docs in `my-new-skill/references/` (keep `SKILL.md` under 500 lines).

4. Push to `main` -- the GitHub Actions workflow auto-publishes all changed skills to ClawHub via `clawhub sync`.

### Frontmatter Field Reference

| Field | Standard | Purpose |
|-------|----------|---------|
| `name` | Agent Skills | Skill identifier (must match directory name) |
| `description` | Agent Skills | What + when (used for discovery in all tools) |
| `license` | Agent Skills | License (MIT for ClawHub) |
| `metadata.author` | Agent Skills | Author identifier |
| `metadata.version` | Agent Skills | Semver version string |
| `metadata.openclaw` | ClawHub | Runtime requirements, env vars, binaries |
| `compatibility` | Agent Skills | Human-readable requirements description |
| `allowed-tools` | Claude Code / OpenCode | Pre-approved tools (experimental in OpenCode) |

All fields are cross-compatible -- tools ignore fields they don't recognize.

## Quick Start

```bash
# 1. Install the skill
npx clawhub@latest install vargai

# 2. Set your API key
export VARG_API_KEY=varg_xxx

# 3. Run setup to verify environment
bash varg-ai/scripts/setup.sh

# 4. Render your first video
bunx vargai@alpha render hello.tsx --preview    # Free preview
bunx vargai@alpha render hello.tsx --verbose    # Full render
```

## Documentation

- [vargHQ/sdk](https://github.com/vargHQ/sdk) -- Full SDK documentation
- [vargHQ/templates](https://github.com/vargHQ/templates) -- Video template examples
- [Agent Skills Spec](https://agentskills.io/specification) -- Agent Skills format
- [ClawHub](https://clawhub.ai) -- Skill registry

## License

MIT
