# 3D code slab

A code snippet, syntax-highlighted, printed on a lit, bevelled 3D slab that turns through space and settles face-on so the code can be read. A hero shot for SDK and API launches, "one line to install" moments and conference title cards. 16:9 native; 1:1 and 9:16 use a taller slab with fewer, larger lines. Typical length 6–8 s.

Theme palettes below come from MIT-licensed themes (Dracula, GitHub's Primer themes, One Dark). No product logos on the slab.

## How the pros do it
- The slab is a "code image" in 3D, so start from the proven code-image layout: generous padding (56 px in one popular tool; 16/32/64/128 options with 64 default in another), a soft drop shadow (20 px down, 68 px blur), 14 px code at 133% line height scaled up for video, JetBrains Mono. [28][29]
- Motion must end in a readable rest: the turn is spectacle, the hold is the content. Use a motion that stabilizes quickly when text must be read. [45]
- Ease out into the rest, never linear; entrances feel snappy when they decelerate. [2][47]
- Keep the snippet short: 6–12 lines, ≤ 48 columns; if code changes, animate tokens rather than swapping images (≤ 0.9 s). [24]
- Pick the theme by exact palette, not by eye:
  - GitHub Dark: bg #0d1117, fg #f0f6fc, keyword #ff7b72, string #a5d6ff, function #d2a8ff, constant #79c0ff, variable #ffa657, tag #7ee787, comment #9198a1. [26]
  - GitHub Dark Dimmed: bg #212830, fg #d1d7e0, keyword #f47067, string #96d0ff, function #dcbdfb, constant #6cb6ff, variable #f69d50, tag #8ddb8c, comment #9198a1. [26]
  - One Dark: bg #282c34, fg #abb2bf, keyword #c678dd, string #98c379, function #61afef, cyan #56b6c2, red #e06c75, number #d19a66, class #e5c07b, comment #5c6370. [27]
  - Dracula: bg #282A36, fg #F8F8F2, keyword #FF79C6, string #F1FA8C, function #50FA7B, class/type #8BE9FD, constant #BD93F9, parameter #FFB86C, comment #6272A4, error #FF5555. [25]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `code-slab-3d.github-dark` | Near-black slab, GitHub Dark tokens | slab #0d1117, bevel 10 px, rim light cool #79c0ff at 20% |
| `code-slab-3d.dimmed` | Softer slate slab | slab #212830, rim light #6cb6ff at 15%, backdrop #15191f |
| `code-slab-3d.one-dark` | Classic editor grey-blue | slab #282c34, rim light #61afef at 18% |
| `code-slab-3d.dracula` | Purple-grey slab, saturated tokens | slab #282A36, rim light #BD93F9 at 22% |

## Timing and numbers
- 8 s clip (240 frames): 0–0.4 s fade/scale in (0.94→1); 0.2–3.2 s turn from rotateY −38°, rotateX 16°, rotateZ −4° to 0/0/0 with ease `power4.out` (use `expo.out` only for turns longer than 5 s; in short clips it snaps face-on in about 0.3 s); 3.2–7.4 s readable hold with a 1–2° idle drift (sine.inOut, 4 s period); 7.4–8.0 s exit or cut. [2][45][47]
- Camera: perspective 2000–2400 px at 1080p (focal ≈ 50 mm look); start dolly 115% scale → 100%.
- Slab: width 62% of frame (16:9), corner radius 18 px, thickness 24–32 px, bevel 8–12 px; padding 64 px; key light from top-left 35°, specular sweep across the face once during the turn (0.8 s). [29]
- Code: 30–36 px at 1080p (2.8–3.3% of frame height), line-height 1.45, JetBrains Mono 400/700 (OFL-1.1). [29][49]
- Shadow under the slab: offset 20 px, blur 68 px at 1×; scale both by slab size, opacity 0.45, shrink as it rises. [28]
- Backdrop: theme bg darkened 35%, or a soft radial gradient; never busy behind code.

## Build it
1. Start from HyperFrames `code-3d-extrude` (WebGL slab with real depth and lighting that rotates and settles to a readable rest, 8 s). `npx hyperframes add code-3d-extrude`. For a 2D-transform version use `code-slice-hero` or a CSS 3D card.
2. Highlight the code once at build time (Shiki + the theme JSON) and render it into a canvas texture at 2× the on-screen size for crisp text.
3. One paused GSAP timeline drives the mesh rotation/position (or CSS `rotateX/Y/Z` with `transform-style: preserve-3d`); lighting values are also tweened, all from timeline time.
4. Remotion: React Three Fiber with `useCurrentFrame()` → rotation via `interpolate(frame, [6, 96], [-38, 0], {easing: Easing.out(Easing.exp)})`.
5. Optional: Paper Shaders `liquid-metal-sting` or `grain-blob` behind the slab for a branded backdrop (keep its contrast under the code).

## Mistakes that look amateur
- Code still turning while the viewer tries to read it → settle face-on by 40% of the clip, then hold. [45]
- 30-line snippet with tiny text → 6–12 lines, ≥ 2.8% of frame height.
- Mixed theme colors (GitHub keyword on a Dracula slab) → one palette, exact hex. [25][26][27]
- Hard black shadow → large soft shadow, 20/68 px proportions. [28]
- Linear rotation or a bounce at rest → expo.out / power4.out into a dead-still rest. [2]
- Text rendered at 1× and scaled up in 3D → render at 2× texture size.

## Sources
[2] Emil Kowalski (@emilkowalski) — ease-out — https://x.com/emilkowalski/status/1970144111261868487
[24] Code Hike token transitions — https://codehike.org/docs/code/token-transitions
[25] Dracula spec + VS Code repo (MIT) — https://spec.draculatheme.com/ , https://github.com/dracula/visual-studio-code
[26] Primer primitives 10.3.4 dark / dark-dimmed; github-vscode-theme (MIT) — https://unpkg.com/@primer/primitives@10.3.4/dist/css/functional/themes/dark.css , https://unpkg.com/@primer/primitives@10.3.4/dist/css/functional/themes/dark-dimmed.css , https://github.com/primer/github-vscode-theme
[27] Atom one-dark-syntax (MIT) — https://github.com/atom/one-dark-syntax
[28] Carbon defaults (MIT) — https://github.com/carbon-app/carbon
[29] ray.so (MIT) — padding options, JetBrains Mono default — https://github.com/raycast/ray-so
[45] Screen Studio guide, Animations — https://screen.studio/guide/animations
[47] GSAP Eases — https://gsap.com/docs/v3/Eases/
[49] Google Fonts metadata — https://github.com/google/fonts
