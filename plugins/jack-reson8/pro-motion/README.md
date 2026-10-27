# Pro Motion · audio-first motion-graphics films with Claude Code

English | [简体中文](https://github.com/jack-reson8/pro-motion/blob/main/README.zh-CN.md) | [日本語](https://github.com/jack-reson8/pro-motion/blob/main/README.ja.md) | [한국어](https://github.com/jack-reson8/pro-motion/blob/main/README.ko.md) | [Tiếng Việt](https://github.com/jack-reson8/pro-motion/blob/main/README.vi.md) | [हिन्दी](https://github.com/jack-reson8/pro-motion/blob/main/README.hi.md)

**Give Claude a product (and a track, or let it plan one). Get a launch film, brand film or TVC that is designed, not templated — rendered in code, cut to the beat, in minutes.**

<table><tr>
<td align="center"><img src="https://raw.githubusercontent.com/jack-reson8/pro-motion/main/docs/showcase-launch.gif" width="260"><br><sub><b>Launch film</b> · product UI, effects that perform, 5 language cuts</sub></td>
<td align="center"><img src="https://raw.githubusercontent.com/jack-reson8/pro-motion/main/docs/showcase-brand.gif" width="260"><br><sub><b>Brand film</b> · stylized animation, objects as instruments</sub></td>
<td align="center"><img src="https://raw.githubusercontent.com/jack-reson8/pro-motion/main/docs/demo.gif" width="260"><br><sub><b>Starter template</b> · 8 s demo you get on install</sub></td>
</tr></table>

<sub>Films made with this skill for <b>Tutti</b>, a photo-play app. Full-length versions are attached to the <a href="https://github.com/jack-reson8/pro-motion/releases">latest release</a>.</sub>

Most "AI video" today is either a template (3D phone + App Store badge) or a generated clip you can't direct. Pro Motion takes a third path: **the music is planned as a marketing asset first, then Claude writes the film as code** — a deterministic `render(t)` on a canvas — so every hit lands on the music to the 16th note, every transition is designed, and any shot can be changed by timestamp and re-rendered in seconds.

It is the method distilled from a real project that went through ~10 rounds of "this looks like a PowerPoint", "the material is ugly", "the text floats on top", "I said stylized, not pop art" — until the cuts were accepted. **The method made the difference, so the method is what this skill encodes.**

## What it does

| Step | What Claude does |
|---|---|
| 1 · Brief | Fixes product, audience, markets, music, ratios, film type — decides defaults instead of interrogating |
| 1b · Campaign + audio | A `campaign.md` worksheet: six stunt ideas from 12 unconventional-marketing levers (the medium malfunctions, neighbour billboards, the restriction becomes the joke, absurd mascot, personal replies at scale, UGC army, FOOH…), scored and picked. Then the campaign brain (truth · tension · mechanic · channel), an audio plan with a sonic logo and hooks, one precise Suno/Udio prompt, then `audio_post.py` for exact-beat SFX, stutters, loops and loudness |
| 2 · Music | `analyze_music.py` → tempo, beat grid, onsets, low/high hits, a spectrogram with the grid drawn on. The spectrogram is the edit |
| 3 · Research | Finds official uploads, pulls 24-frame **contact sheets** with yt-dlp (no browser), writes a **technique sheet** per reference |
| 4 · Direction | **Three clearly different style frames** from named techniques — you pick before anything is animated |
| 5 · Story | One **protagonist** that transforms through every scene; every feature performs itself on a music event; every transition designed; text is animation; the ending grows into the logo |
| 6 · Build | `motion-lib.js`: easing & springs, squash & stretch, a beat camera driven by onsets, 12-fps doodle line boil, pen-written text, metaballs, halftone, stripes, 3D card ring, sticker outlines, subject cutouts (macOS Vision), multi-language switch — plus 40+ deterministic canvas equivalents of AE / Blender / anime devices: curl-noise particles, particles that assemble into a logo, Saber glow, shine, whip pan, iris, ink bleed, shatter, zoom-through, paper tear, morph, manga panels, infinite zoom, RGB split, glitch, dither, ASCII, riso, cut paper, toon shading, hatching, watercolour, slit-scan, echo, speed ramp. `fx-demo.html` shows each for one second |
| 7 · Render | `render-fast.js`: parallel headless tabs → JPEG frames → one ffmpeg mux. ~30 s for 20 s @ 60 fps. Contact-sheet check, audio-length check |
| 8 · Iterate | Feedback by timestamp; taste feedback goes back to research and direction, not to patching |

<p align="center"><img src="https://raw.githubusercontent.com/jack-reson8/pro-motion/main/docs/spectrogram-example.png" width="720" alt="Music analysis: spectrogram, envelope and beat grid"></p>

## Install

**As a Claude Code plugin (recommended)**

In a session: `/plugin install pro-motion --marketplace jack-reson8/pro-motion` — or from the shell:

```bash
claude plugin marketplace add jack-reson8/pro-motion
claude plugin install pro-motion@pro-motion
```

**As a plain skill**

```bash
git clone https://github.com/jack-reson8/pro-motion
cp -R pro-motion/plugins/pro-motion/skills/pro-motion ~/.claude/skills/
```

Requirements: Node 18+, Python 3 with `numpy scipy matplotlib`, Chrome/Chromium (auto-detected, or `CHROME=/path`). Subject cutouts need macOS 14+. Everything else is installed per project by `scripts/setup.sh`.

**Codex** (CLI or the ChatGPT desktop app):

```bash
codex plugin marketplace add jack-reson8/pro-motion
codex plugin add pro-motion@pro-motion
```

Or copy `plugins/pro-motion/skills/pro-motion` into `~/.codex/skills/`. The skill follows the open [Agent Skills](https://agentskills.io) standard, so it works in Claude Code, Codex and any agent that reads SKILL.md.

**Other agents** (Cursor, Gemini CLI, GitHub Copilot and other agents supported by the skills CLI):

```bash
npx skills add jack-reson8/pro-motion
```

## Use it

Just ask, with a track:

> Make a 20-second launch video for my photo app, cut to `~/Downloads/track.mp3`. Vertical, English master plus Japanese and Korean cuts.

> 用这首歌给我的品牌做一支强烈风格化的品牌片，先给我三个风格方向的风格帧。

> The 8–10 s section feels like a slideshow — redesign the transitions there.

Claude follows the skill: analyses the music, researches with contact sheets, shows style frames, writes `shotmap.md`, builds `film.js`, renders `out/*.mp4`, checks a frame sheet, and opens the result.

## What's inside

```
plugins/pro-motion/skills/pro-motion/
├── SKILL.md                    # the method (read by Claude)
├── scripts/
│   ├── setup.sh                # one-command project setup
│   ├── analyze_music.py        # tempo, grid, onsets, spectrogram
│   ├── audio_post.py           # exact-beat SFX, stutter, loop, loudness
│   ├── render-fast.js          # parallel render, stills mode, audio mux
│   ├── contact_sheet.sh        # frames at given seconds → one image
│   ├── ref_frames.sh           # reference video → 24-frame sheet (yt-dlp)
│   ├── cutout.swift            # subject mask (macOS Vision)
│   └── faces.swift             # face boxes (macOS Vision)
├── assets/template/            # campaign.md · audio-plan.md · film.html · film.js (runnable demo) · motion-lib.js · fx-demo.html · OFL fonts
└── references/
    ├── unconventional-marketing.md  # 12 stunt levers → steps → cases → how to apply
    ├── campaign-cases.md       # launch mechanics that travelled
    ├── audio-first.md          # campaign brain, audio plan, generator prompts
    ├── vfx-techniques.md       # transitions, rhythm, AE / Blender / stylised looks: source · params · lib call
    ├── sourcing.md             # how to find and read references
    ├── research-notes.md       # worked technique sheets
    ├── aesthetic-checklist.md  # story · motion · type · material · languages · delivery
    └── lessons.md              # bugs and taste mistakes already paid for
```

## Principles (the short version)

1. **The music is the edit.** Read the spectrogram; land every move on a mapped event.
2. **Look at real frames, never design from memory.**
3. **Pick a direction from style frames,** not the first association or the easiest thing to code.
4. **One protagonist, effects that perform, transitions that are designed** — or it reads as PowerPoint.
5. **Text is animation.** No lower-thirds, chips, or boxes.
6. **Ugly material makes an ugly film.** Real, current, licence-safe material — or blank space.
7. **Render in seconds, check one contact sheet, deliver.** Iterate by timestamp.

## Licence

Code and docs: MIT (see `LICENSE`). Bundled fonts: SIL Open Font License 1.1 (Patrick Hand, Yomogi, Gaegu, ZCOOL KuaiLe) — see `assets/template/assets/fonts/LICENSES.md`. References you download with `ref_frames.sh` are for private study only; don't redistribute them.

Contributions welcome — new motion primitives, transitions, technique sheets and lessons especially. See `CONTRIBUTING.md`.
