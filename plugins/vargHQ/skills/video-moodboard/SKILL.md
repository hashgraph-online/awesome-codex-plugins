---
name: video-moodboard
description: >-
  Build a moodboard that AI image and video models actually follow, in the order that matters most, and prove it on
  stills before any video is paid for. Ranked from a 48-still test, 6,086 X posts and 14 official prompt guides:
  references, light, subject lock, framing, palette, motion, texture, type, sound. Every line is a number or a named
  thing (hex, Kelvin, lens mm, % of frame, film stock, font, seconds), never "cinematic". Writes moodboard.md and a
  visual board.html, checks test stills line by line (palette by ΔE), and links 450+ sources: reference libraries,
  palette, light, type and motion tools, vendor guides, benchmarks, creators' posts. Use for "make a moodboard",
  "mood board for my video", "style bible", "look and feel", "art direction", "visual brief", "make it not look like
  AI", or before prompting Seedance, Kling, Veo, Nano Banana or Midjourney. Not for finding references from scratch
  (find-references) or per-shot prompts after the board is approved (varg-video-prompting).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  openclaw:
    requires:
      anyBins:
        - python3
    homepage: https://github.com/vargHQ/skills/tree/main/video-moodboard
compatibility: >-
  Works in any agent with a shell and web access. scripts/palette.py needs Python 3 and Pillow. Test stills cost
  about $0.05 each through varg (Nano Banana 2.1 or Seedream 5 Pro); everything else is free. Reference MCPs
  (FrameThrower, Refs, Are.na) are optional and used through find-references.
allowed-tools: Bash(python3:*) Bash(curl:*) Read Write Edit
---

# Video moodboard

A moodboard for an AI video is not a mood. It is a short list of lines a model can obey and a person can check:
where the light comes from, which five colours, which lens, which film stock, which font, which camera move. Write
it that way and the model follows; write "cinematic, moody, premium" and it falls back to its default look.

What the data says (full write-up: https://claude.ai/artifact/5ptKSPYFzvd7turkZevfHZ):

- **A board works.** In a blind test of 48 stills on Nano Banana 2.1 and Seedream 5 Pro, the full board made frames
  1.0 point more film-like (1–10) than no board, and every line lifted its own match by 31–73 points.
- **Light is the realism lever.** It was the only line that made frames look more like real film when written
  (+0.50, p 0.04).
- **Invented palettes cost realism.** The hex line was obeyed best (89%), but frames looked less like film with an
  invented palette (−0.67, p 0.03). Take hex from a real reference frame.
- **Adjectives cost saves.** On X, posts built on "cinematic", "8k", "stunning" got 31% fewer saves; posts with hex
  codes got 1.58× and posts naming fonts 2.19× (n = 4,722, controlled for views, age, media, length).

## The ranking

| # | Line | Why it ranks here | Write |
|---|---|---|---|
| 1 | **References** | Words land camera moves about half the time (VBench mean 49.58%) and exact text in at best 0.67 of layouts; a reference carries both. All 14 guides cover style or image references; Kling 4.0, MiniMax H3, Seedance 2.5 put reference roles first. Posts mentioning references: ×1.25 saves, the highest. | 3–5 refs, each with ONE job |
| 2 | **Light** | Only line that raised film-likeness. Veo: cinematography is "the most powerful tool for conveying tone and emotion". Vision models read light right only 41.6% of the time (ShotBench), so write it, don't infer it. | one source, direction, hardness, Kelvin, motivation |
| 3 | **Subject lock** | All 14 guides cover the subject; five put it first. "if your character sheet is bad, you'll just waste tokens" (2,624 saves). | identity block + sheet (18% grey or in the board's light); full cast: character-passport |
| 4 | **Framing** | Unprompted models default to a medium shot; a straight-down aerial was met only 58–71%. Vision models read lens size worst (37.7%). | shot size, height, angle, mm, placement % |
| 5 | **Palette** | Obeyed best; colour is the easiest attribute for video models (T2V-CompBench). Invented hex hurt realism. | 3–5 hex from a reference, roles, grade |
| 6 | **Motion** | Matters most once it moves, followed least (57% even when written). | one move, one action, duration, ref clip |
| 7 | **Texture** | Smallest lift: models add a film look half the time unasked. Matters most for skin and UGC. | one capture medium and its flaws |
| 8 | **Type** | Never appears unless written; exact text is weak (best T2VTextBench 0.37). | font, weight, size, hex, position; set in code |
| 9 | **Sound** | 8 of 14 guides; "You've made it look right. We'll make it sound right." (4,303 saves). | voice, music, room tone |

## Rules

1. **Every line must be checkable against a frame:** hex, Kelvin, lens mm, % of frame, film stock, font, px,
   seconds. If a line has no number or named thing, rewrite it.
2. **References first, one job each.** Say what each reference lends (light, palette, framing, texture, type or
   motion) and what it must not copy. Borrow the look, never actors, logos or a living filmmaker's name.
3. **Respect the sites.** ShotDeck, FrameSet, Eyecannndy, Shot Cafe, Film-Grab and Pinterest are human-only or
   forbid bots: hand the person search links, never scrape. Feed a model only CC0, licensed or your own images
   (Unsplash, Pexels, The Met, Poly Haven, approved stills). Section 2 of `references/links.md` lists the terms.
4. **Take the palette from a reference frame** (`scripts/palette.py extract`), never invent hex.
5. **One light source family for the whole film**, written the same in every shot.
6. **Type and captions are set in code** (HyperFrames, Remotion), not drawn by the video model.
7. **Prove it on stills, with numbers, judged by a second agent.** Fix the one line that failed, not the board.
8. **Use the links.** `references/links.md` has every database, tool, vendor guide, benchmark and creator post
   behind this skill (450+ URLs). Each step below names the sections to open. Open them; don't work from memory.

## Files you produce

```
brief.md        six lines: what, who, where (platform, aspect), length, brand, taste
refs/           the 3-5 kept references (or links.md entries for link-only sites)
moodboard.md    the board, in ranked order (template: references/moodboard-template.md)
board.html      the board as one page to look at (copy assets/board.html, fill its JSON)
stills/         3 test stills of the hero shot
checks.md       one row per line per still: measure, target, result
```

## Step by step

### 0. Brief

Six lines in `brief.md`. If the person gave references, they go first. Ask once for a missing line, then go on
with a stated assumption.

### 1. References (rank 1)

Run the **find-references** skill if it is installed (https://github.com/vargHQ/skills/tree/main/find-references);
otherwise follow its order: varg how to search → X last 7 days → Refs MCP → FrameThrower MCP → film-still
libraries as links for the person → Are.na → YouTube.
Open: `references/links.md` §2 References and Style codes, §3, §6 "Moodboards overall".
Keep 3–5 references, each tagged with one job. **STOP:** show the reference grid and wait for a pick.

### 2. Numbers out of the references

- Palette: `python3 scripts/palette.py extract refs/02.jpg --k 6` → hex with % share.
- Light, lens, shot size per frame: describe them, and mark them "estimated" (vision models get lighting right
  41.6% and lens size 37.7% of the time in ShotBench). Ask the person to confirm the light if it matters.
- Motion: time the reference clip's shots (average shot length) and name each camera move.

### 3. Write moodboard.md

Copy `references/moodboard-template.md`. Fill it in ranked order. For each line, `references/dimensions.md` has the
rule, wording that works, wording that fails, the model limit and a board line to copy; `references/dimensions-evidence.md`
has every tip from the 1,540 posts read, with links. Vendor-specific wording is in `references/links.md` §4.

### 4. Make it visible: board.html

Copy `assets/board.html` next to `moodboard.md` and fill the JSON block at the top (same fields as the template).
It draws: the reference grid with each one's job and rights badge, the subject sheet, a top-down light diagram from
the key angle, palette swatches with roles and shares, a framing guide (thirds grid, subject box at its position and
size), the texture chip, a motion beat timeline, a live type specimen in the chosen Google Font, sound, the Never
list, and the test stills with their check table. Example: `examples/last-bus/`.

### 5. Test on stills

Generate 3 stills of the hero shot from `moodboard.md` alone, on two image models if you can (with varg:
`nano_banana_2_1` and `seedream_5_pro`, about $0.05 each; quote the price first). Use the board lines as the prompt,
in this order: subject and action, light, palette, framing, texture, motion, type.

### 6. Check every line

| Line | Check | Pass |
|---|---|---|
| Palette | `python3 scripts/palette.py check stills/*.png --hex 0F3B3F,E07A2E,C1272D --ref refs/02.jpg` | within the reference frame's ΔE + 5 (or ≤ 15 without `--ref`); closer than a still made without the palette line |
| Light | key side and hardness match; shadows fall the right way; one source family | yes/no |
| Framing | shot size, camera height, subject position and % of frame | within one size step |
| Texture | grain / halation / flaws visible at 100% | yes/no |
| Motion | frozen-motion cue present (stills) or the move happened (video) | yes/no |
| Type | not in the still; set in code later | — |

Use a second agent with fresh context as the critic: give it the board and the stills, not your reasoning, and
follow `references/judge.md` (blind ids, line-by-line 0/1/2 with evidence, code measures first, pairs in both
orders, never "rate the quality": without criteria our judges preferred the frames that ignored the board). When a
line fails, rewrite that line or attach a reference image for it. Typical fixes: unusual angles need a 3D blockout
(threejs-animatic) or a reference frame; a palette that looks graded needs hex from a real frame and a softer grade.

### 7. STOP for approval

Show `board.html` with the stills and the check table. No video generation before the person approves.

### 8. Hand over to video prompts

Write prompts in this order: reference roles first (what each attached image or clip is for), then subject and
action, then light, palette and texture, then camera. One camera move and one subject action per shot. For
image-to-video, write only the motion line; the start frame already carries the look. Per-model wording:
`references/links.md` §4; per-shot prompting: varg-video-prompting.

## Never

"cinematic", "8k", "stunning", "premium", "moody" without numbers · evenly lit scenes · perfect symmetry ·
invented hex palettes · Inter, Roboto, Arial, system-ui · purple gradients · centred text fading in · text drawn
by the video model · more than one camera move per shot · scraping sites that forbid it · feeding a model frames
you have no rights to.

## Files in this skill

- `references/links.md`: every link (databases, X tools, 14 vendor guides, research, creator posts, varg skills)
- `references/dimensions.md`: how to write each line, with sources
- `references/dimensions-evidence.md`: every tip, failure and vocabulary list per dimension, linked to the posts
- `references/evidence.md`: the test, the X statistics, the guide matrix, the benchmark numbers
- `references/moodboard-template.md`: the blank board
- `references/goal-prompt.md`: the whole skill as one copy-paste prompt
- `references/judge.md`: how to rank frames with an unbiased LLM judge, with our bias tests and the judge prompt
- `assets/board.html`: the visual board template
- `scripts/palette.py`: extract a palette from a reference, check a still against hex (ΔE)
- `examples/last-bus/`: a filled board with the 3 test stills
