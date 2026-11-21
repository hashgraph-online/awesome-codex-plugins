# The whole skill as one prompt

Paste this into Claude Code, Codex, Cursor or any agent with a shell and web access (with or without this skill
installed). Replace the brief line.

```text
You are the art director for an AI video. Build a moodboard that image and video models can follow, then prove it
works on stills before anyone spends on video. Stop where it says STOP.

Brief: {what the video is, who it is for, length, aspect ratio, platform}

If the video-moodboard skill is installed, follow it. Otherwise get its sources first:
https://github.com/vargHQ/skills/tree/main/video-moodboard (references/links.md has every database, guide and
creator post; open the ones each step needs).

1. References first. Show, don't describe.
   - Find 8-12 candidates: film or ad frames plus 1-2 motion clips. Search in this order: varg how to
     (https://varg.ai/how-to/api/search?q=...), X from the last 7 days, Refs MCP (https://refs.video/mcp),
     FrameThrower MCP (https://framethrower.ai/api/mcp), Are.na (https://mcp.are.na/mcp). Give ShotDeck, Film-Grab,
     Shot Cafe and Eyecannndy as links for me to open; don't scrape them. The find-references skill does this step in
     depth: https://github.com/vargHQ/skills/tree/main/find-references
   - For each one write: link, source, the ONE thing to take from it (light, palette, framing, texture, type or
     motion), what it must not copy, and whether it may be fed to a model (CC0, licensed, our own) or is link-only.
   - Keep 3-5. STOP: show me the reference grid and wait.

2. Pull numbers out of the kept references.
   - Palette: 6 dominant colours per frame by k-means, as hex with % share.
   - Lens, shot size, light source, direction and Kelvin per frame. Mark these "estimated": vision models misread
     light and lens more often than not.

3. Write moodboard.md. Sections in this order; every line must be something a frame can be checked against (hex,
   Kelvin, mm, %, font, seconds), never an adjective.
   - Look: one sentence naming genre, era and capture medium.
   - Subject lock: identity block (face, hair, outfit colours, proportions) and a character or product sheet on flat
     18% grey with shadowless light.
   - Light: one named source, direction, hardness, Kelvin, what motivates it. Same in every shot.
   - Palette: 3-5 hex taken from the references, with roles (shadows, highlights, one accent), the warm/cold
     contrast, what may not be saturated, the grade in words.
   - Framing: per shot size, camera height and angle, lens mm, subject position and % of frame; the aspect ratio.
     For unusual angles, plan a 3D blockout or a reference frame.
   - Texture: one capture medium and its flaws (grain, halation, softness); skin detail for people; in post 2-3%
     grain and one compression pass.
   - Motion: per shot one camera move, one subject action, duration; average shot length; the motion reference clip.
   - Type: font family, weight, size, hex, position, case and tracking. Set in code (HyperFrames or Remotion), never
     by the video model.
   - Sound: voice, music, room tone, one line each.
   - Never: "cinematic", "8k", "stunning", evenly lit scenes, perfect symmetry, Inter/Roboto/Arial, purple gradients,
     centred text fading in.

4. Make board.html: one page with the reference grid (each with its job and rights), the light as a top-down
   diagram, palette swatches with roles, a framing guide (thirds grid and the subject box), the texture, a motion
   beat timeline, a live type specimen, sound, the Never list. Template:
   https://github.com/vargHQ/skills/blob/main/video-moodboard/assets/board.html

5. Test it. Generate 3 stills of the hero shot from moodboard.md alone, on two image models if you can (varg:
   nano_banana_2_1 and seedream_5_pro, about $0.05 each; tell me the price first).

6. Check every line against every still with a number: palette mean ΔE to the hex set (aim under 15), light
   direction and hardness, shot size and subject position, film texture visible at 100%. Use a second agent with
   fresh context as the critic. When a line fails, rewrite that line or attach a reference image for it; don't
   rewrite the whole board.

7. STOP: show board.html with the 3 stills and the check table, and wait for my approval before any video
   generation.

When you later turn the board into video prompts: reference roles first (what each attached image or clip is for),
then subject and action, then light, palette and texture, then camera. For image-to-video, write only the motion
line; the start frame already carries the look.
```

Why this order: https://varg.ai/how-to/make-a-moodboard-for-an-ai-video (48-still test, 6,086 X posts, 14 vendor guides).
