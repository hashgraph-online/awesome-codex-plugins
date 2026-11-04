# Coding-agent terminal session

One turn of an AI coding agent (Claude Code-style) inside a terminal window: the user's prompt is typed into the input box, the agent answers with short text, tool-call lines (read file, edit, run tests), a diff, a spinner while it works, and a final summary. For AI dev-tool launches, "built with an agent" stories and tutorials. 16:9 native; 1:1 and 9:16 crop to the transcript column with huge type. Typical length 10–15 s.

Claude and Claude Code are Anthropic trademarks; build a look-alike transcript, no Anthropic logo or wordmark, invented repo and file names, and never show a fake result presented as a real benchmark.

## How the pros do it
- Pace it like a demo, not like reality: an agent turn can take minutes; compress waits into a 1.5–3 s spinner beat and speed long output instead of cutting it. Keep the turn under 30 s. [15][16]
- The prompt is typed by a person (12–20 cps, uneven gaps); the agent's text streams faster and in chunks (40–80 cps, word-sized bursts) so the two voices feel different. [10][14][62]
- While the agent works it shows a spinner with a one-line tip under it; a visible "working" line is what makes the wait legible. [19]
- The mode indicator cycles Manual → accept edits → plan with Shift+Tab, and a task list (Ctrl+T) shows up to five tasks with pending / in progress / done states: use these as on-screen story beats (plan → do → check). [18]
- Color with the brand accent sparingly: Anthropic's orange #d97757 on near-black #141413 / off-white #faf9f5; everything else stays terminal grey. [20]
- Window: Ghostty defaults are #282C34 background, white text, JetBrains Mono, block cursor, transparent titlebar; scale the font up for video. [17][16]
- Show the proof frame: the diff with green/red lines or "tests passed", held long enough to read, and zoomed if it is small. [16][1]
- Rebuild the transcript as HTML instead of recording: a real session is long, private and unpredictable; a rebuilt one is clear. [4]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `agent-terminal-session.prompt-tools` | Prompt typed, 3 tool-call lines tick to done, summary | prompt 16 cps, tool lines every 0.5 s with 0.6 s spinner each, summary streams 60 cps |
| `agent-terminal-session.code-edit` | Agent proposes an edit, diff block appears, accepted | diff block slides open height 0→auto 0.35 s power2.out, + lines #98C379 on rgba(152,195,121,.12), − lines #E06C75 |
| `agent-terminal-session.still-working` | Long task compressed: spinner, elapsed counter, tip line | spinner frame every 100 ms, elapsed counter counts real-looking seconds at 8× speed, tip line grey 70% |
| `agent-terminal-session.huge-type` | 9:16 transcript column, giant text | font 3.4% of frame height, 30 columns, one tool line on screen at a time |

## Timing and numbers
- Beats for a 12 s turn: 0–0.4 s window settles (scale 0.97→1, opacity, ease-out); 0.4–3.0 s prompt typed (40–45 chars at 16 cps); 3.0–3.4 s Enter beat; 3.4–8.5 s tool lines (each: appears, 0.6 s spinner, turns to a done mark); 8.5–10 s diff or result; 10–12 s summary + hold. [2][15]
- Prompt typing 12–20 cps with seeded 33–200 ms gaps; agent text 40–80 cps in word bursts (one burst per 50–80 ms). [10][62]
- Spinner: 8–10 glyph frames, 80–120 ms each (3 frames at 30 fps). Never a CSS animation; derive the frame from timeline time.
- Text size 28–34 px at 1080p (≈ 2.6–3.1% of frame height), line-height 1.4, max 96 columns; input box border 1 px rgba(255,255,255,.25) radius 8 px, padding 14×18 px. [16]
- Colors: bg #282C34 (Ghostty default) or #141413; text #E6E6E6; dim #8A8F98; accent #d97757; success #98C379; error #E06C75. [17][20]
- Font: JetBrains Mono (OFL-1.1). [17][49]

## Build it
1. Window: start from HyperFrames `code-terminal-run` (prompt typing behind a deterministic caret) and `terminal-simulator` (streamed logs); build the transcript rows as your own components. `npx hyperframes add code-terminal-run`.
2. Data: `[{role:"user", text}, {role:"tool", label:"Read src/app.ts"}, {role:"tool", label:"Edit src/app.ts", diff:[…]}, {role:"tool", label:"Run tests", result:"14 passed"}, {role:"agent", text}]`.
3. Precompute timings once from the beat table; on seek render each row's state (hidden / spinning / done) from `t`.
4. Camera: optional push-in to the diff (zoom 1.4–1.6, power3.inOut 0.8 s, starting 1 s before the diff lands). [1][63]
5. Remotion: `<Sequence from>` per row; spinner glyph = `frames[Math.floor(frame / 3) % frames.length]`.

## Mistakes that look amateur
- Real-time waits (10 s of spinner) → 0.6–1.5 s per tool step, a speed-up counter for long tasks. [15]
- Agent text typed at human speed with a caret → stream in word bursts, no caret. [62]
- Anthropic logo, a real repo, a real API key in an env dump → no logos, invented names, redact everything secret.
- Orange everywhere → accent only on the mode badge, spinner and highlights. [20]
- Tiny README-GIF text → 28–34 px at 1080p. [16]
- Diff flashing by → hold ≥ reading formula (0.6 s + chars/15) or zoom into it. [12][16]

## Sources
[1] Adam Pietrasiak (@pie6k) — camera leads the action — https://x.com/pie6k/status/1586636942879645696
[2] Emil Kowalski (@emilkowalski) — ease-out, scale from 0.93+ — https://x.com/emilkowalski/status/1954891053032755560
[4] Om Patel (@om_patel5) — https://x.com/om_patel5/status/2110398086438584391
[10] Dhakal et al. CHI 2018 — https://www.eurekalert.org/news-releases/569762
[12] Netflix English Timed Text Style Guide — https://partnerhelp.netflixstudios.com/hc/en-us/articles/217350977-English-USA-Timed-Text-Style-Guide
[14] Charm VHS — https://github.com/charmbracelet/vhs
[15] VHS best-practice skill — https://cdn.jsdelivr.net/npm/@marcfargas/skills@0.5.1/vhs/SKILL.md
[16] Thorsten Ball, How to Demo — https://thorstenball.com/how-to-demo
[17] Ghostty source — https://github.com/ghostty-org/ghostty
[18] Claude Code docs, Interactive mode — https://code.claude.com/docs/en/interactive-mode
[19] Claude Code docs, Settings (spinner + tip line) — https://code.claude.com/docs/en/settings
[20] Anthropic brand-guidelines skill — https://github.com/anthropics/skills/blob/main/skills/brand-guidelines/SKILL.md
[49] Google Fonts metadata — https://github.com/google/fonts
[62] HyperFrames notes-typing — https://github.com/heygen-com/hyperframes/tree/main/registry/components/notes-typing
[63] HyperFrames cursor-zoom-follow — https://github.com/heygen-com/hyperframes/tree/main/registry/components/cursor-zoom-follow
