# varg — AI Agent Skills for Video, Image, Speech & Music Generation

A collection of [Agent Skills](https://agentskills.io) for AI video, image, speech, and music generation using the varg platform. One skill to access Seedance 2.5, Kling 4, Wan 3, Veo 3.1, Nano Banana 2.1, GPT Image 2.6, ElevenLabs v4 and 200+ more models — zero code, just prompt.

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
| [code-to-video-previz](./code-to-video-previz/) | Prototype a video in code with an agent: which tool (Three.js, Blender or none), one scene file both render, number audits, a 3D camera solve of a reference shot in headless Blender, staging from a painting, handoff prompts, and quotes from people who've done it. Standard library for checks; Bun and Chrome or `bpy` for renders | — |
| [threejs-animatic](./threejs-animatic/) | A three.js animatic ("animatronic") of every shot: jointed mannequins, sets in real metres, a START/END camera per shot timed to the music, a top-down frustum map, frame-exact MP4 render (headless Chrome or HyperFrames), then a greyscale Seedance video-to-video pack. Working starter project, no npm | — |
| [find-references](./find-references/) | Find real, human-made references before anything is made, for AI image, video and music and for video made with code: one query pack per job (light first, then framing, people, location, texture, palette, type, motion, music, and a never board), each source searched in its own words, a helper that reaches 22 open sources with no key, links for the sites only a person may open, measuring scripts, and an LLM judge benched for bias. Includes the whole skill as one `/goal` prompt | — |
| [video-moodboard](./video-moodboard/) | A moodboard that image and video models follow, ranked by what matters most (references, light, subject lock, framing, palette, motion, texture, type, sound) from a 48-still test, 6,086 X posts and 14 vendor guides. Every line is a number or a named thing; writes `moodboard.md` and a visual `board.html`, checks 3 test stills line by line (palette by ΔE), and links 450+ databases, tools, guides, benchmarks and creator posts. |
| [video-script](./video-script/) | Write the script before anything is made: one promise, ten hooks, beats joined by but/therefore, one spoken line per visual, every line sized to its seconds and checked by `check_script.py` (pace, hook timing, shot length, unsourced numbers, AI-sounding phrases). Six structures with one example script each, and variations for demo and launch videos, product reviews, ads and UGC, social shorts and short-form drama, plus a loop for testing and improving the skill | — |
| [video-sound](./video-sound/) | The sound of any video, from 480 sourced findings (Murch, Thom, Burtt, trailer editors, NPR, voice directors, model docs) and paid tests: AI voices cast from candidates a person picks and directed with each model's tags, dialogue and narration with pauses, breaths and small actions, effects only where something happens, music planned bar by bar with the stop made in the edit, and a mix graded by script (LUFS, true peak, voice over music, effects within a frame, cuts on the beat, dead air). `sound.py` + `audition.py` + `judge_takes.py` (an audio LLM judge that shortlists takes: yes/no checks, both orders, code decides); whole skill as one prompt | — |
| [media-judge](./media-judge/) | Judge finished AI-made video, images and music by measuring them, not grading them. One command reads every frame and writes a time, a number and a picture for broken frames, banding after a simulated X or YouTube upload, jiggling numbers, spelling, too much on screen, pinned graphics, sliding labels, face, outfit and light changes, sound after the cut and distance to references against the template. Includes the LLM-as-a-judge protocol with bias measured on real clips, a ranker, a seeded test bench, and a guide to building your own | — |
| [video-animate](./video-animate/) | Animate once the previz, characters, moodboard, script and sound exist: code or AI per element, Seedance 2.5 or another model per shot, a cheap 480p pass first, long or short runs, takes that vary only the performance, picture cut to the locked track, and plates ready for motion design. Frame counts from the animation canon, cinema and music video tricks, 12 prompt templates, a take checker and a database directory. | — |
| [video-project-github](./video-project-github/) | Keep an AI video project, or any agent-built project, in a private GitHub repo without learning git: the agent creates it, keeps keys out, saves a version at every approved step and gives an undo for anything. Media goes by hash into Releases of the same repo, so no 100 MB wall and one login; a one-command proof restores the project byte for byte. Folder layout, take and render naming, editing as text. In our tests a smaller model pushed keys to GitHub in 3 of 3 unaided runs and 0 of 3 with the skill | — |
| [character-passport](./character-passport/) | Cast an AI video before anything moves: for every character and hero prop a passport (one paragraph, every visible detail, pasted word for word into every prompt by `scripts/prompt.py`, which fails any paraphrase), a turnaround sheet in the moodboard's look, six expressions written as a cause + physical tells, a voice line (pace in wpm, accent, one verbal habit) measured by `scripts/voice_check.py`, and props with materials, wear and how they move and sound. Built on a blind-judged test (stills on Nano Banana 2.1, acting on Kling 4 and Seedance 2.5); includes code routes (three.js, VRM, SVG face rig), tested reference sites, who to learn from, and a bias-aware protocol to judge and rank takes with AI judges (binary rubric, pairwise in both orders, three model families, calibration against people; `face_check.py`, `judge_agreement.py`). |
| [varg-mockups](./varg-mockups/) | Mock up a video before paying for it: one HTML review board of numbered stills with shot specs, prompts, approve / needs-fix and notes, feedback copied as Markdown; stills that do not look like AI slop and stay consistent; device and UI mockups | — |
| [varg-video-prompting](./varg-video-prompting/) | Prompt varg's video, image, voice and music models: which model for which shot, prompt anatomy for video, stills and edits, what @image1, @video1 and @audio1 copy, dialogue and lip-sync, a frame and audio QA checklist, gotchas from paid runs | — |
| [edit-footage-with-code](./edit-footage-with-code/) | Edit real footage with an agent: read the take as text and audio, cut dead air and retakes without clipping words, keep graphics on spoken words in HyperFrames or Remotion, check with numbers and frames. Scripts for analysis, cuts, QA and a blind judge pack. Built from 2,318 X posts and cold-agent tests | — |
| [video-asset-sources](./video-asset-sources/) | Find B-roll, music, sound effects, motion blocks, fonts and logos an agent can really fetch and legally use: 97 databases tested, 37 working no-key queries, license traps, a credits file | — |
| [varg-video-editing](./varg-video-editing/) | Which service to edit existing footage with, job by job (cuts, talking-head cleanup, Shorts, captions, AI restyle and swaps, dubbing, upscaling, QA, handing off to Resolve/Premiere/Final Cut), plus the rules that keep cuts frame-accurate and in sync | — |
| [varg-video-edit-library](./varg-video-edit-library/) | 206 named edits for footage you already have, each with the look, when to use it, the common mistake, timings and a recipe for FFmpeg, HyperFrames, Remotion and CapCut: cuts and pacing (J/L cuts, match cuts, speed ramps), transitions (CapCut-style, every FFmpeg xfade, Remotion TransitionSeries, HyperFrames and GL shaders), headlines, quotes, end cards, UI walkthroughs, cursors, device mockups, code and terminal, AI agent flows, numbers and charts, logo walls, grids and backdrops | — |
| [media-download](./media-download/) | Save videos/audio by link from X, YouTube, Instagram, Facebook, TikTok and 1800+ sites (yt-dlp), and Pinterest images by pin, board or search (gallery-dl). Local, no API key | — |
| [short-form-ffmpeg-cookbook](./short-form-ffmpeg-cookbook/) | Short-form FFmpeg cookbook: copyable commands for Reels. Crop to 9:16, burn captions (SRT/ASS), trim and join, music with ducking; every command tested. Local, no API key | — |
| [paper-shaders](./paper-shaders/) | Frame-exact Paper Shaders backgrounds, textures and logo stings for HyperFrames and Remotion videos, plus 11 researched looks (liquid metal, god rays, marbled ink, contour lines, datamosh rain…) | `paper-shaders` |
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
| [How to prompt Kling 4 for cinematic AI video](./kling-4-prompting/) · `kling-4-prompting` | Prompt Kling 4 so it doesn't look like AI slop: key frames from GPT Image 2.5 plus a short director's prompt, reference-to-video inputs (@Image, @Element, @Video, @Voice), multi-shot with seconds, "no slow motion", dialogue in quotes, the failure fixes and the varg call with the reference route pinned | — |
| [Make a short film or music video with Kling 4](./kling-4-keyframe-film/) · `kling-4-keyframe-film` | Beat sheet, cast and look references, every key shot as a still on GPT Image 2.5, one 30-second Kling 4 take per beat, then cut the usable seconds like live-action takes; dialogue scenes and the fix pass | — |
| [Turn key frames into a 30-second action montage with Kling 4](./kling-4-action-montage/) · `kling-4-action-montage` | Breakdance, BMX, skate or chase montages from 3-4 stills and a one-line prompt: the moves, "no slow motion", the end state as the last still, picking the seconds that land | — |
| [GPT Image 2.6 guide and text-heavy layout recipes](./gpt-image-2-6/) · `gpt-image-2-6` | GPT Image 2.6 on varg: Flare vs Sunburst, quality vs reasoning_effort, sizes, what fal rejects, measured prices, the MCP and REST calls, and credited prompt recipes for infographics, launch posters, editorial travel prints, Baroque gallery posters, landmark postcards, character turnarounds, storyboards and clean upscales | — |
| [Turn a still or mascot into a looping GIF with GPT Image 2.6](./gpt-image-gif/) · `gpt-image-gif` | Prompt or still → looping GIF: the sprite-sheet pixel budget with a measured frame-size table for 2-16 frames, approve a still first, loop-lock wording, frame timing, transparent backgrounds, failure modes, and `gif2web.sh` for WebP and MP4 | — |
| [Turn a photo or character into an animated sticker pack](./gpt-image-sticker-pack/) · `gpt-image-sticker-pack` | 6-8 emotions with one word each from one approved still, then `export.sh` fits and checks every sticker against the Telegram, WhatsApp, LINE, WeChat, Discord and Slack specs (checked on the official docs, linked) | — |
| [Make game sprite sheets with GPT Image 2.6](./gpt-image-sprite-sheet/) · `gpt-image-sprite-sheet` | A strict 4×4 sheet spec (translated from @SSSS_CRYPTOMAN), then `slice.sh` cuts the frames, keys out the background, aligns the ground line and writes a GIF, an atlas PNG and a JSON atlas for Phaser, with the Godot steps | — |
| [Edit only the parts you circle with GPT Image 2.6](./gpt-image-markup-edit/) · `gpt-image-markup-edit` | Circles, arrows and notes on a transparent layer (`markup.py` from JSON), sent as `markup_image_url` with one prompt line per colour, a diff check, and when to use `mask_url` instead | — |
| [Turn a selfie into a woke profile with GPT Image 2.6 (Wokify)](./make-a-woke-profile-with-chatgpt/) · `make-a-woke-profile-with-chatgpt` | One selfie → 11 satirical woke versions of you (character sheet, woke friends, LinkedIn, DEI call, protest interview GIF, action figure, trading card GIF, cat GIF, oat latte, blinking "In this house" home, WOKEOPOLY), a 4:5 "I MADE ME WOKE" collage for X and a HyperFrames presenter video; `wokify.py` runs it on varg for ~$0.78, and every prompt also works pasted into ChatGPT | — |
| [Turn photos and a name into a personalized AI birthday video](./varg-birthday-video/) · `varg-birthday-video` | Turn a name, an age and a few photos into a birthday video that is theirs: a song that sings the name (ElevenLabs Music), their photo blowing out the candles (GPT Image 2.5 still, Seedance 2.5 or Wan 3), a retro camcorder tape, then-and-now, a pet's birthday, a milestone poster; the formats that spread on X, 27 looks, and a script that exports for WhatsApp | — |
| [Turn photos into an AI invitation, holiday greeting or tribute video](./varg-occasion-video/) · `varg-occasion-video` | Invitations and save-the-dates that unfold with the names and date printed right (Seedance 2.5 first and last frames), Christmas, New Year, Diwali and Eid greetings, old photos brought to life, a love story across the eras, calm memorial and retirement tributes | — |
| [ecommerce-video-ads](./ecommerce-video-ads/) | Ecommerce video ad skills for Claude Code and AI agents: the plan and the rules for product videos that sell on TikTok, TikTok Shop, Reels and Meta: four questions, angle, hook, format, casting, second-by-second script, product fidelity, platform rules (AI labels, Shop bans, FTC), cost gate, variants | — |
| [product-video-hooks](./product-video-hooks/) | Turn a product into scroll-stopping video hooks: three agreeing layers (frame, line, text), 70-line hook bank, claim checks, one MP4 per hook | — |
| [tiktok-shop-video](./tiktok-shop-video/) | Turn a product link into a TikTok Shop video: Shop styles, 18–35 s script, phone shot list, and the 2025–2026 rules (real presenter, no AI voice, no slideshow, no mismatched prices) | — |
| [ai-ugc-ad-video](./ai-ugc-ad-video/) | Open-source alternative to Arcads: AI UGC ads with an AI actor holding your real product, face, voice and label locked, phone-real prompts, no AI testimonials | — |
| [product-photo-to-video](./product-photo-to-video/) | Turn a product photo into a product video ad: truth sheet, cut-out, storyboard sheet, Seedance PRODUCT LOCK, repair pass, real packshot on the last second; ASMR unboxing, macro, 360° loop, try-on | — |
| [ad-creative-testing](./ad-creative-testing/) | Turn one winning ad into a creative testing plan: decode the winner, concepts Meta and TikTok treat as different, how many and when to judge, funnel diagnosis, kill/scale rules, naming | — |
| [ecommerce-video-edit](./ecommerce-video-edit/) | Turn raw product footage into a TikTok ad with FFmpeg: hook moved to second 0, dead air cut, text hook and CTA in the safe zone, -14 LUFS, one MP4 per hook, 4:5 cut; tested commands, local, no API key | — |
| [caption-styles](./caption-styles/) | 17 animated caption looks (karaoke, word pop, sliding pill, word tiles, glass, neon, serif italic…) as exact presets: font, size per format, sync 1-2 frames before the voice, 9:16 safe box, contrast; from the Netflix and BBC subtitle guides and short-form editors. Local, no API key | — |
| [title-design](./title-design/) | Lower thirds, speaker plates, show opens and headline, CRT, chrome and glitch title reveals with broadcast rules: hold time from word count, safe areas, type scale, plate opacity, easing. Local, no API key | — |
| [kinetic-type-art](./kinetic-type-art/) | 17 kinetic typography pieces on the beat (typeface strobe, word slams, word tunnel, manifesto, riso and photocopy posters, decrypt and glitch wordmarks) with beat maths, spacing, free font pairings and palettes. Local, no API key | — |
| [social-overlays](./social-overlays/) | CTA pills, follow and subscribe prompts, review cards, LIVE badges, comment callouts and counters in one 9:16 safe box from TikTok, Reels and Shorts specs, timed after the payoff, real data only (FTC). Local, no API key | — |
| [app-ui-mockups](./app-ui-mockups/) | Message threads, team chat, coding-agent terminals, code walkthroughs, 3D code slabs and exploded UIs rebuilt as HTML at measured typing and reading speeds, with theme colors from MIT sources. Local, no API key | — |
| [transition-craft](./transition-craft/) | Shake-distort cuts, Droste infinite zooms, tile-flip mosaics, bokeh, collage and 3D gallery transitions: frame counts, beat placement, log-space zooms, decaying shakes. Local, no API key | — |
| [motion-formats](./motion-formats/) | Seven formats with beat structures and presets: analog-horror website trailer, VHS bouncing logo, pixel-art runner on a CRT, wave wordmark, DAW one-shot music video, launch trailer, kinetic lyric video. Local, no API key | — |
| [maps-and-data-motion](./maps-and-data-motion/) | Globe-to-country dives, satellite flyovers, route and watercolor maps, self-drawing charts, count-ups, versus timelines and audio visualizers, with map credits and tile licences built in. Local, no API key | — |
| [footage-effects](./footage-effects/) | Glow and halation, glitch, CRT, chromatic aberration, halftone, acid photocopy, zoom blur and heat haze on real footage: 34 tested ffmpeg chains plus HyperFrames and Remotion versions. Local, no API key | — |

## Requirements

- `VARG_API_KEY` (get at [varg.ai](https://varg.ai)) or the hosted varg MCP (`https://mcp.varg.ai/mcp`) -- required for varg-ai, varg-previz, varg-video-prompting, varg-mockups (for generated stills; the board itself needs no key) and the format skills (varg-music-video, varg-character-keynote, varg-consistent-characters, varg-character-design and its category recipes, varg-podcast-video, varg-product-hook, varg-dropship-reel, the Kling 4 skills (kling-4-prompting, kling-4-keyframe-film, kling-4-action-montage), the GPT Image 2.6 skills (gpt-image-2-6, gpt-image-gif, gpt-image-sticker-pack, gpt-image-sprite-sheet, gpt-image-markup-edit, make-a-woke-profile-with-chatgpt; their local scripts need no key), the occasion skills (varg-birthday-video, varg-occasion-video), ecommerce-video-ads, ai-ugc-ad-video, product-photo-to-video); media-download, short-form-ffmpeg-cookbook, paper-shaders, the motion craft skills (caption-styles, title-design, kinetic-type-art, social-overlays, app-ui-mockups, transition-craft, motion-formats, maps-and-data-motion, footage-effects), threejs-animatic (varg only for its Seedance step), how-to-make-ai-video, varg-publish-skill (publishes with a varg login or key, no credits), video-skills, varg-video-edit-library, varg-video-editing, ecommerce-video-edit, ad-creative-testing, product-video-hooks (written hooks) and tiktok-shop-video (scripts) need no key (varg-video-editing uses varg only for the paid edits it recommends)
- **Cloud mode**: curl only (zero dependencies)
- **Local mode**: bun runtime + ffmpeg
- **paper-shaders** and the motion craft skills: Node 22 and ffmpeg for HyperFrames (`npx hyperframes`), or a Remotion 4 project; footage-effects needs only ffmpeg

## What this plugin connects to

Everything the plugin runs, sends or fetches:

- **varg how to MCP** (`https://api.varg.ai/v2/skills/mcp`): no key. Sends the search text you or the agent type (`search_how_to`) and returns how-to cards. Searches are logged without IP or key (query, MCP client name, top results).
- **varg MCP** (`https://mcp.varg.ai/mcp`): OAuth sign-in to your varg account. Sends generation requests (prompts, uploaded or linked media) and spends your varg credits; results are stored in your varg account and served from `s3.varg.ai`.
- **varg API** (`https://api.varg.ai`): the skills' `curl` examples send `VARG_API_KEY` from your environment as a Bearer token to api.varg.ai only, never to any other host. Skills that need no key are listed under Requirements.
- **media-download**: runs `yt-dlp` on your machine against the video link you give it (X, YouTube, Instagram, TikTok, Pinterest and other sites yt-dlp supports) and saves the file locally.
- **paper-shaders** and **varg-previz**: render locally; varg-previz bundles three.js (MIT) in `varg-previz/templates/previz/vendor/` so the previz page works offline.
- **code-to-video-previz**: its Three.js page loads three.js (MIT, pinned version) from jsDelivr and renders with your local Chrome and ffmpeg. Blender and camera solving use the `bpy` package through `uv`. Nothing is uploaded and no account is needed.
- **video-project-github**: runs `git` and `gh` on your computer, creates a private repo on your GitHub account and uploads your project and media there (only with your go-ahead, after you sign in yourself). It never reads or uploads `.env`, adds git hooks to the project, and refuses a public repo. No other network calls.
- **threejs-animatic**: its starter loads three.js (MIT, pinned version) from jsDelivr, runs a Bun server on localhost that saves camera edits into the project folder, and renders with your local Chrome and ffmpeg. **varg-mockups** boards are single HTML files; notes stay in the viewer's browser storage.
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

# 4. Make your first clip (TSX/JSX videos are deprecated; edit clips with the ffmpeg tool)
curl -fsSL https://varg.ai/install | sh && vargai login
vargai generate_video --prompt "waves at dusk" --duration 5
```

## Documentation

- [vargHQ/sdk](https://github.com/vargHQ/sdk) -- Full SDK documentation
- [vargHQ/templates](https://github.com/vargHQ/templates) -- Video template examples
- [Agent Skills Spec](https://agentskills.io/specification) -- Agent Skills format
- [ClawHub](https://clawhub.ai) -- Skill registry

## License

MIT
