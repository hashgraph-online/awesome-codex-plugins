# Desktop terminal window

An editable, classic desktop terminal window (macOS Terminal-style: title bar with three window dots and a centred "user — zsh — 80×24" title, light or dark profile) that types and runs a short shell session. A neutral, reusable frame for any command, install line or log. 16:9 native; 1:1 and 9:16 use a narrower window and larger type. Typical length 5–8 s.

macOS and Terminal belong to Apple. Build a look-alike window; SF Mono is Apple-licensed, so use an OFL monospace. No Apple logo, no real usernames or hostnames.

## How the pros do it
- The window is a frame, not the subject: record or build only the window, 1080p, big type; no menu bar, no dock, no notifications. [16]
- Window chrome numbers that demo tools use: a 30 px title bar, 10 px dots spaced 15 px centre-to-centre, 60 px padding around the terminal, 1200×600 default canvas, 80 columns. Scale them all by the same factor for video. [14]
- Type at 12–20 cps with uneven, seeded gaps (humans average 52 WPM ≈ 4.3 cps, which is too slow on screen). [10][14][62]
- Hold 3 s after quick output, 5 s after long output; compress long output with speed, keep the clip under 30 s. [15]
- Size chrome text from the macOS type scale: Body and Headline are 13 pt (16 pt line), Callout 12 pt; a window drawn at 1.5× for video puts the title at ~20 px. [31]
- Entrance: the window scales 0.94 → 1 with an opacity fade, ease-out, about 0.35 s; never from scale 0. [2][44]
- A retro amber or green profile is a valid variant: phosphor amber is #ffb700-ish; keep glow subtle on a clean window. [40][41]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `desktop-terminal-window.basic-light` | White profile, black text | bg #FFFFFF, text #1E1E1E, title bar #ECECEC, dots #FF4F4D #FEBB00 #00CC1D, radius 12 px |
| `desktop-terminal-window.pro-dark` | Black profile, light-grey text, lime caret | bg #000000, text #C7C7C7, caret #A6E22E block, title bar #2B2B2B |
| `desktop-terminal-window.homebrew-green` | Green-on-black retro profile | text #28FE14, bg #000000, glow text-shadow 0 0 6px rgba(40,254,20,.45) |
| `desktop-terminal-window.amber` | Amber phosphor profile | text #FFB000, bg #0B0700, glow 0 0 8px rgba(255,176,0,.5), no scanlines |

## Timing and numbers
- 6 s clip: 0–0.35 s window in (scale 0.94→1, opacity 0→1, power2.out); 0.5–2.6 s command typed (≈ 30 chars at 14 cps); 2.6–3.0 s Enter beat; 3.0–3.6 s output in bursts every 50 ms; 3.6–6.0 s hold. [2][15]
- Typing gaps from a seeded 33–200 ms table; +120 ms at spaces. Caret: block, blinks on a 1.0 s cycle (30 frames) when idle, solid while typing. [46][62]
- Window at 1080p (16:9): 1500×860 px, radius 12 px, title bar 42 px (30 px × 1.4), dots 14 px with 21 px centre spacing, inner padding 28 px; shadow 0 30px 80px rgba(0,0,0,.35). [14]
- Text 26–32 px (2.4–3.0% of frame height), line-height 1.3, ≤ 90 columns. Title 20 px, grey #6E6E6E (light) / #9A9A9A (dark), centred, format "user — zsh — 80×24". [31]
- Fonts: JetBrains Mono or IBM Plex Mono (OFL-1.1) for the terminal; Inter (OFL-1.1) 500 for the title. [49]

## Build it
1. Start from HyperFrames `code-snippet-apple-terminal-pro` (black profile, grey text, lime cursor, per-character typing) or `code-terminal-run`. `npx hyperframes add code-snippet-apple-terminal-pro`.
2. Expose variables: `title`, `profile` (basic-light | pro-dark | homebrew-green | amber), `lines` (array of `$ cmd` / output strings), `speed`.
3. Precompute per-character times from the gap table × `1/speed`; render by slicing on seek.
4. For the amber/green profiles add a single `text-shadow` glow; save scanlines and curvature for the amber booth console template.
5. Remotion: same data in props; `<AbsoluteFill>` window, characters from `Math.floor(charsAt(frame / fps))`.

## Mistakes that look amateur
- Window dots in the wrong order or sizes off → red, amber, green from the left, equal size, centres 1.5 dot-diameters apart. [14]
- Live clock or real username in the title → fixed invented user, fixed size "80×24". [14]
- Typing perfectly evenly → seeded uneven gaps. [62]
- Terminal font under 2.2% of frame height → 26–32 px at 1080p. [16]
- Heavy CRT effects on a modern window → glow only; CRT belongs to the retro console template. [41]

## Sources
[2] Emil Kowalski (@emilkowalski) — https://x.com/emilkowalski/status/1954891053032755560
[10] Dhakal et al. CHI 2018 — https://www.eurekalert.org/news-releases/569762
[14] Charm VHS source (style.go, draw.go) — https://github.com/charmbracelet/vhs
[15] VHS best-practice skill — https://cdn.jsdelivr.net/npm/@marcfargas/skills@0.5.1/vhs/SKILL.md
[16] Thorsten Ball, How to Demo — https://thorstenball.com/how-to-demo
[31] Apple HIG Typography (macOS text styles) — https://developer.apple.com/design/human-interface-guidelines/typography
[40] Phosphor color notes (P3 602 nm) — https://publish.obsidian.md/xybre/permalink/e397c38e-aa6f-45eb-831f-f02a3836abc4
[41] cool-retro-term Default Amber profile — https://github.com/Swordfish90/cool-retro-term
[44] Emil Kowalski, Great animations — https://emilkowal.ski/ui/great-animations
[46] remotion-bits TypeWriter — https://remotion-bits.pages.dev/docs/reference/typewriter
[49] Google Fonts metadata — https://github.com/google/fonts
[62] HyperFrames notes-typing — https://github.com/heygen-com/hyperframes/tree/main/registry/components/notes-typing
