# Code editor walkthrough

A guided tour through code in a VS Code-style editor: the camera scrolls to a line, the line is highlighted, and a comment thread (step N of M, short markdown note) opens beside it; repeat for 3–5 steps. For SDK launches, "how it works" explainers, docs videos and PR walkthroughs. 16:9 shows the full workbench; 1:1 and 9:16 crop to the editor pane with larger type. Typical length 10–15 s (2.5–3.5 s per step).

Visual Studio Code, VS Code and the VS Code icon are Microsoft trademarks. Use the open-source MIT theme colors, no VS Code icon or name in the video's branding, and say "a code editor" in titles.

## How the pros do it
- Structure it as a tour: each step anchored to a file and line, a short markdown note in a comment thread, Previous/Next navigation, a step counter. That is the established walkthrough pattern. [23]
- Animate code changes token by token, not by cross-fading whole blocks: matching tokens move to their new place, new tokens fade in; cap each transition at about 0.9 s. [24][50]
- Know where the viewer looks on every frame: dim the rest, highlight one line, point at it. [16]
- Camera: scroll so the target line lands at 40–45% of the editor height, then let the comment open; the scroll starts before the thread appears (lead by ~1 s for camera moves), and use a "focused" motion that stabilizes quickly when text must be read. [1][45]
- Hold each step for its reading time: 0.6 s + characters of the note ÷ 15, plus 0.8 s for the code line itself. [11][12]
- UI entrances are short and ease-out (comment thread ≤ 300 ms, scale from 0.97, not 0). [2][44]
- Use the exact theme tokens: Dark 2026 editor #121314, sidebar/activity/status #191A1B, text #BBBEBF, line numbers #858889, focus #3994BC; Light 2026 editor #FFFFFF, chrome #FAFAFD, text #202020, line numbers #606060, accent #0069CC. Syntax: keyword #ff7b72 / #cf222e, string #a5d6ff / #0a3069, function #d2a8ff / #8250df, constant #79c0ff / #0550ae, variable/entity #ffa657 / #953800, tag #7ee787 / #116329, comment #8b949e / #6e7781. [21]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `code-editor-walkthrough.dark-2026` | Full workbench, Dark 2026 theme, 4 steps | editor #121314, chrome #191A1B, line highlight #242526, accent #3994BC, step 3.0 s |
| `code-editor-walkthrough.light-2026` | Full workbench, Light 2026 theme | editor #FFFFFF, chrome #FAFAFD, line highlight #EAEAEA40, accent #0069CC, step 3.0 s |
| `code-editor-walkthrough.editor-only` | 9:16/1:1, editor pane only, huge type | font 2.9% of frame height, 34 columns, comment card below the line, full width |

## Timing and numbers
- Per step (3.0 s at 30 fps = 90 frames): 0–0.7 s scroll (power3.inOut) target line to 42% of pane height; 0.5–0.8 s line highlight sweeps left→right (power2.out); 0.7–0.95 s comment thread opens (height 0→auto + opacity, 0.25 s power2.out, scale 0.97→1); hold to 3.0 s or the reading formula, whichever is longer. [24][44][12]
- Code-change steps: token transition 0.6–0.9 s, ease power2.inOut, stagger 0; added tokens fade in during the last 40%. [24]
- Editor text 22–26 px at 1080p (2.0–2.4% of frame height) for 16:9 full workbench, line-height 1.5; editor-only crops 30–32 px. Gutter numbers at 85% size. [16]
- Comment thread card: width 46% of editor pane, radius 6 px, header "Step 2 of 4" 13–15 px at 70% opacity, body 18–20 px, 1 px border = focus color at 40%.
- Mockup proportions (our values, already enlarged for video) at 1920×1080: activity bar 60 px, sidebar 340 px, tab row 44 px, status bar 28 px; drop the sidebar entirely in 1:1 and 9:16.
- Font: JetBrains Mono or Geist Mono (OFL-1.1) for code; Inter (OFL-1.1) for UI chrome. [49]

## Build it
1. Start from HyperFrames `code-snippet-dark-2026` (full Dark 2026 workbench with per-character typing), then add `code-scroll` (camera scrolls a long file to a target line and spotlights it) and `code-highlight` (band sweeps a line, context dims). `npx hyperframes add code-snippet-dark-2026 code-scroll code-highlight`.
2. Data: `steps:[{file, line, title, note}]`; the comment thread is your own small component (header, markdown note, Prev/Next pills, counter).
3. For code edits, use Code Hike token transitions (React/Remotion) or, in HyperFrames, measure token positions before/after and tween `x/y` per token on one timeline. [24][50]
4. Syntax-highlight once at build time (Shiki with the theme JSON from the VS Code repo), not per frame.
5. Remotion: the Code Hike template (`npx create-video@latest --code-hike`) gives snippet-to-snippet transitions; wrap each step in a `<Sequence>`. [50]

## Mistakes that look amateur
- Cross-fading whole code blocks between steps → token transitions, ≤ 0.9 s. [24]
- Target line landing at the bottom edge after a scroll → 40–45% of pane height.
- Comment threads appearing before the scroll settles → scroll first, thread after.
- 14 px editor text in a 1080p video → ≥ 22 px; crop the workbench if needed. [16]
- VS Code logo in the corner or "VSCode" in the title → no icon, no name in branding. [22]
- Holding every step 2 s regardless of note length → reading formula. [12]

## Sources
[1] Adam Pietrasiak (@pie6k) — camera leads by ~1 s — https://x.com/pie6k/status/1586636942879645696
[2] Emil Kowalski (@emilkowalski) — https://x.com/emilkowalski/status/1954891053032755560
[11] Brysbaert 2019 via BPS — https://www.bps.org.uk/research-digest/most-comprehensive-review-date-finds-average-persons-reading-speed-slower
[12] Netflix English Timed Text Style Guide — https://partnerhelp.netflixstudios.com/hc/en-us/articles/217350977-English-USA-Timed-Text-Style-Guide
[16] Thorsten Ball, How to Demo — https://thorstenball.com/how-to-demo
[21] VS Code theme-defaults (2026-dark.json, 2026-light.json), MIT — https://github.com/microsoft/vscode/tree/main/extensions/theme-defaults/themes
[22] VS Code brand guidelines — https://code.visualstudio.com/brand
[23] Microsoft CodeTour — https://github.com/microsoft/codetour
[24] Code Hike token transitions — https://codehike.org/docs/code/token-transitions
[44] Emil Kowalski, Great animations — https://emilkowal.ski/ui/great-animations
[45] Screen Studio guide, Animations — https://screen.studio/guide/animations
[49] Google Fonts metadata — https://github.com/google/fonts
[50] Remotion Code Hike template — https://www.remotion.dev/templates/code-hike
