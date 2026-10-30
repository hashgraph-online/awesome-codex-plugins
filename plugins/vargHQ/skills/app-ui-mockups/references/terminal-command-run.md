# Terminal command run

One command typed into a modern GPU terminal window (Ghostty-style: dark, borderless, transparent titlebar), executed, and its output streamed: plain output, a render with a progress bar, a coloured git log, or a huge-type version for vertical video. For CLI launches, install one-liners, "it just works" beats inside dev-tool launch films. 16:9 native; 1:1 and 9:16 crop to a narrower window with larger type. Typical length 6–12 s.

Ghostty is an MIT open-source terminal; there is no logo in this template. Never show real tokens, real hostnames or real usernames.

## How the pros do it
- Record or build at 1080p, show only the terminal (no menu bar, no battery), and bump the font size, then bump it again. [16]
- Human typing averages 52 WPM ≈ 4.3 characters/s (≈ 230 ms per key); that is too slow for video. Demo tools default to 50 ms per character (20 cps) and practitioners go faster, 25–40 ms, calling 50 ms slow. Use 12–20 cps for a "human" feel and 30 cps for long commands. [10][14][15]
- Make the rhythm uneven: real typists roll over 40–70% of keys, so gaps cluster short with occasional long ones; a cycled gap table of 33–200 ms (mean ≈ 85 ms) reads as a person. Pause longer at spaces and before flags. [10][62]
- After Enter, hold so the output can render and be read: about 3 s after a quick command, 5 s after a long one; keep the whole demo under 30 s and speed long output up instead of cutting mid-line. [15]
- Know where the viewer looks on every frame: the caret, then the first output line, then the result line. Highlight or zoom the one line that proves the point. [16]
- Use a seeded typo rate if you want "human" (≤ 2% of characters, corrected after 5 frames); never random per render. [46]
- Rebuilding the terminal as HTML beats a screen recording for control: deterministic timing, no stray notifications, crisp type at any scale. [4][48]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `terminal-command-run.command-output` | Prompt, typed command, 4–8 output lines, new prompt | 16 cps with 33–200 ms gaps, Enter beat 0.35 s, lines every 60 ms, hold 3 s |
| `terminal-command-run.render-progress` | Command → progress bar 0→100% → "Done in 4.2s" | bar 40 cells, update every 100 ms (3 frames), eases power1.inOut overall, final line green |
| `terminal-command-run.git-log` | `git log --oneline --graph` style coloured history | 8–12 commits, lines every 40 ms, hash yellow #E5C07B, branch label green #98C379, HEAD cyan #56B6C2 |
| `terminal-command-run.huge-type` | 9:16 / 1:1, 32–40 columns, giant mono | font 3.6% of frame height, 34 columns, command ≤ 30 chars, no wrapping |

## Timing and numbers
- Typing: `natural` 12 cps (gaps from a 33–200 ms table, +120 ms at spaces, +250 ms before `--flags`); `snappy` 20 cps (50 ms, the VHS default); `fast` 30 cps (33 ms). At 30 fps: 20 cps = 1 char per 1.5 frames, so drive by time, not by whole frames. [10][14][15][62]
- Beat between last character and Enter: 0.3–0.45 s. Command "thinking" before output: 0.2–0.8 s (spinner frames every 80 ms if the tool shows one).
- Output: bursts of 3–6 lines every 40–80 ms; final result line gets its own 0.25 s beat before it prints. Hold after the last line ≥ 3 s, or reading formula (0.6 s + chars/15). [12][15]
- Cursor: block cursor (Ghostty default), blink cycle 1.0 s (30 frames) while idle, solid while typing. [17][46]
- Window: Ghostty defaults are bg #282C34, fg #FFFFFF, 13 pt, 2 px padding; for video use 28–34 px font at 1080p (≈ 2.6–3.1% of frame height), padding 32–48 px, line-height 1.35, 80–100 columns max in 16:9. [17][16]
- Chrome: 12 px traffic-light dots (red / amber / green; VHS draws #FF4F4D / #FEBB00 / #00CC1D, 10 px dots with centres 15 px apart in a 30 px bar; scale up for video), window radius 12–14 px, shadow 0 30 80 rgba(0,0,0,.45). [14]
- Font: JetBrains Mono (OFL-1.1, Ghostty's embedded default) 400/700. Alternatives: IBM Plex Mono, Geist Mono, Fira Code (all OFL). [17][49]

## Build it
1. Start from HyperFrames `code-terminal-run` (one command: deterministic typing behind an integer-cycle caret, output per cue, fresh prompt) or `terminal-simulator` (multi-command with streamed logs). `npx hyperframes add code-terminal-run`.
2. Script as data: `[{type:"cmd", text:"npx create-thing my-app"}, {type:"out", lines:[…], gap:0.06}, {type:"progress", from:0, to:100, dur:2.4}]`.
3. Precompute every character's time from a seeded gap table (the 33–200 ms cycle) times `1/speed`; render `text.slice(0, n(t))` on seek. No `setInterval`.
4. Progress bar: one tween of a number 0→100 with `ease:"power1.inOut"`; render `█` cells = round(n/100×40) and the percent text from the same value.
5. Remotion: same arrays; `const n = charsAt(frame/fps)`; output lines via `Sequence` per line.
6. For real footage of a terminal, upscale with `scale=iw*2:ih*2:flags=lanczos` and sharpen lightly `unsharp=5:5:0.6`, but prefer rebuilding.

## Mistakes that look amateur
- Perfectly even typing at 10–20 ms per key → seeded uneven gaps, 12–20 cps. [10][62]
- Output dumped in one frame → bursts every 40–80 ms, result line on its own beat.
- Cutting away the instant output ends → hold ≥ 3 s. [15]
- 14 px font in a 1080p video (README-GIF sizes) → 28–34 px. [16]
- Full desktop visible around the terminal → terminal only, or a clean backdrop. [16]
- Wrapping lines in vertical video → cap columns, shorten the command.

## Sources
[4] Om Patel (@om_patel5) — https://x.com/om_patel5/status/2110398086438584391
[10] Dhakal et al., CHI 2018 (EurekAlert) — 52 WPM, 40–70% rollover — https://www.eurekalert.org/news-releases/569762
[12] Netflix English Timed Text Style Guide — https://partnerhelp.netflixstudios.com/hc/en-us/articles/217350977-English-USA-Timed-Text-Style-Guide
[14] Charm VHS source — 50 ms/char default, window bar dots — https://github.com/charmbracelet/vhs
[15] VHS best-practice skill — 25–40 ms, Sleep 3–5 s, < 30 s — https://cdn.jsdelivr.net/npm/@marcfargas/skills@0.5.1/vhs/SKILL.md
[16] Thorsten Ball, How to Demo — https://thorstenball.com/how-to-demo
[17] Ghostty Config.zig / embedded.zig — https://github.com/ghostty-org/ghostty
[46] remotion-bits TypeWriter — seeded errors, blink 30 frames — https://remotion-bits.pages.dev/docs/reference/typewriter
[48] Steve Lemuel — rebuilt UI for a dev-tool teaser — https://contra.com/p/llNMeeMX-raycast-kinetic-product-motion
[49] Google Fonts metadata — https://github.com/google/fonts
[62] HyperFrames notes-typing — key-gap table — https://github.com/heygen-com/hyperframes/tree/main/registry/components/notes-typing
