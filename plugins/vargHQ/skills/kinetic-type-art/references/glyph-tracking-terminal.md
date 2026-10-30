# Glyph-tracking terminal camera

An AI-agent terminal session where a virtual camera tracks the newest glyphs as they print, cutting between about a dozen beat-timed close-ups (prompt, tool call, diff, result) before pulling out to the full window. For agent, CLI and developer-tool launches. 16:9 and 9:16 (also 1:1); 6-8 s.

## How the pros do it
- Compute glyph positions without DOM reflow so the camera knows where every character is on every frame; userland text measurement makes this cheap [9].
- Use a monospace face so each glyph's x is column x advance; JetBrains Mono (wght 100-800) or IBM Plex Mono, both OFL [27].
- Text that moves in depth stays sharp as SVG or real text, never a bitmap [4].
- Make terminal output land like an answer streams: uneven bursts on a token rhythm, words landing grey then inking to full colour, not a typewriter tick [41].
- Prompt typing: chunked human cadence behind a deterministic caret, with an optional backspace-retype [41].
- Cut the shots to the beat; each shot's start is computed from absolute time [38].
- The message is the priority: every close-up must contain one readable fact (a command, a number, a filename) [55].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `glyph-tracking-terminal.dark` | Dark terminal, green prompt, white output | bg #0B0B0D, text #E6E6E6, prompt #33FF8A, accent #FF8A1F, JetBrains Mono 500 |
| `glyph-tracking-terminal.light` | Light terminal for keynote looks | bg #F7F7F5, text #1A1A1A, accent #3255A4 |
| `glyph-tracking-terminal.tilt` | Close-ups in 3D: camera rotates 8-14deg around the line | perspective 1400 px, rotateY ±10deg, rotateX 6deg |

## Timing and numbers (7 s = 210 f, 12 shots)
- 12 shots in 7 s = 17.5 f each; at 103 BPM (60/103 x 30 = 17.48 f) one shot per beat. Or alternate 17/18 f shots on any edit grid; compute each start as round(i x 17.5).
- Shot = camera move to target glyph + hold: move 6-8 f `power3.inOut` (or a hard cut every 3rd shot), hold the rest.
- Zoom levels: wide 1x (full window), medium 2.2-3x (one line), close 4-6x (a token). Pattern: wide → medium → close → close → medium → ... → wide (last 30 f).
- Camera leads text: target = the glyph that will print 2-4 f after the shot starts, so the eye lands as it appears.
- Terminal font size 22-28 px at 1x on a 1920x1080 frame; line height 1.4; window inset 120 px.
- 9:16: window fills width minus 48 px; close-ups at 3-4x so lines stay inside the frame.
- Motion blur on camera moves: 2-4 subframes at 180-degree shutter, if the renderer supports it.

## Build it
1. HyperFrames: `code-terminal-run` (prompt types deterministically, executes, prints lines on cues), `typed-prompt`, `streaming-text`; `yt-camera-move` or `scroll-camera-story` for camera rigs [41].
2. Pre-layout: build the whole transcript as data (lines, tokens, print times); compute each glyph's (x, y) as col x advance, row x lineHeight (monospace) or with a measurer [9].
3. Camera: a wrapper div with `transform: translate(-cx*s + W/2, -cy*s + H/2) scale(s)`; keyframe (cx, cy, s) per shot from the target glyph's position.
4. Printing: each glyph visible when `t >= printTime[i]`; stream colour from #777 to final over 4-6 f.
5. Remotion: same; camera values interpolated with `interpolate(frame, [start, start+7], [a, b], {easing: Easing.inOut(Easing.cubic)})`.
6. Keep all text as live DOM text or SVG so zooms stay crisp [4].

## Mistakes that look amateur
- Camera follows the caret frame by frame → seasick; move in shots, hold between.
- Zooming a rasterized screenshot → blurry at 4x; use real text [4].
- Proportional font with per-frame DOM measurement → jitter and slow renders; monospace + precomputed layout [9].
- Even-tick typing → robotic; chunk the cadence [41].
- Close-ups that land on whitespace → target a token that prints in the next 2-4 f.
- Fake brand names of real AI products in the transcript → use generic or your own product.

## Sources
[4] @jh3yy, blow-out text — https://x.com/jh3yy/status/1702790661911494765 — crisp text in z
[9] @_chenglou, text measurement — https://x.com/_chenglou/status/2037713766205608234
[27] google/fonts METADATA — https://github.com/google/fonts — JetBrains Mono, IBM Plex Mono
[38] Silverman Sound BPM calculator — https://www.silvermansound.com/bpm-to-fps-calculator
[41] HyperFrames registry — https://github.com/heygen-com/hyperframes/tree/main/registry — code-terminal-run, typed-prompt, streaming-text, yt-camera-move
[55] John LePore interview — https://pushing-pixels.org/?p=12751 — message first
Gap: no practitioner write-up on per-glyph camera tracking was found; the shot grammar and zoom levels are our starting values.
