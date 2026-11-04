# app-ui-mockups demo

The preview video for the `app-ui-mockups` card on varg.ai/how-to: four UI scenes from this skill, one after the
other, all with invented apps, people and code.

| Time | Template · preset | What it shows |
|---|---|---|
| 0.0–5.7 s | `agent-terminal-session · prompt-tools` | A coding-agent turn in a terminal (no product logo): the window settles (scale 0.97 → 1), the prompt types on the preset's seeded gap table (+120 ms at spaces), Enter beat, three tool lines every 0.5 s each with a 0.6 s spinner (one 45° step every 100 ms = 3 f) that turns into a done mark, then the summary streams at 60 cps in word bursts, no caret. Colours #282C34 / #E6E6E6 / #8A8F98, accent #d97757 only on the prompt mark, mode badge and spinner; JetBrains Mono 30 px, line-height 1.4 |
| 5.7–9.0 s | `team-chat-channel · conversation` + `reactions` | Invented workspace "Lumen Labs", #launch, initials avatars. New rows land with a 0.3 s power2.out column push and a 12 px rise; reaction pills pop 0.5 s after their message (0.18 s `back.out(2)`), counts tick every 0.12 s. Sidebar #4A154B, text #1D1C1D, timestamps #616061, Lato 400/700/900, Noto Color Emoji |
| 9.0–12.0 s | `code-slab-3d · github-dark` | An invented 8-line TypeScript function on a bevelled slab (#0d1117, 10 px bevel, 28 px thickness from stacked layers, rim #79c0ff @20%), perspective 2200 px, turning from rotateY −38°, rotateX 16°, rotateZ −4° to face-on with `power4.out` while the camera dollies 115% → 100%; one specular sweep (0.8 s); soft shadow at 0.45; GitHub Dark tokens; JetBrains Mono 34 px, line-height 1.45 |
| 12.0–16.0 s | `exploded-ui-panels · orbit-collapse` | An invented "Northwind" analytics dashboard in 5 layers: flat (0–0.4 s), tilt to rotateX 55° / rotateZ −35° and explode (power3.out, stagger 0.07 s bottom → top), 25° orbit (sine.inOut), collapse (1.1 s power3.inOut, stagger 0.06 s top → bottom), dead-still final screen 3.7–4.0 s. z gaps 90 px, hero card +220 px, per-layer shadow offset 0.12·z, blur 0.35·z |

1920×1080, 30 fps, 16 s, silent. Values come from `assets/presets/*.json` and each reference's "Timing and numbers".

## Render

```bash
cd app-ui-mockups/examples/demo
PATH=$HOME/.nvm/versions/node/v22.19.0/bin:$PATH npx --yes hyperframes@0.8.206 check
PATH=$HOME/.nvm/versions/node/v22.19.0/bin:$PATH npx --yes hyperframes@0.8.206 render -o app-ui-mockups.mp4 --fps 30 --crf 20
```

## Content and credits

- All names (Lumen Labs, Ana Ruiz, Marco Bianchi, Priya Nair, Tomas Keller, Northwind), messages, code, repo and
  numbers are invented. No product or platform logos; the chat and terminal are generic look-alikes.
- Fonts: JetBrains Mono and Inter (OFL, bundled with HyperFrames); Lato 400/700/900 Latin (OFL) and a 3-glyph
  subset of Noto Color Emoji (OFL) from Google Fonts in `assets/fonts/`.
- No footage, images or audio.

## Deviations

- Every template is compressed to fit four in 16 s: the 12 s agent turn runs in 5.7 s (same per-step values: typing
  table, 0.5 s tool cadence, 0.6 s spinner, 60 cps summary, but a 1.1 s summary hold instead of 2 s); the 10 s chat
  shows two arrivals and one reaction burst in 3.3 s (Priya's 34-character message is pushed after 1.65 s, under its
  `0.6 + chars/15` = 2.9 s hold, though it stays on screen to the end); the 8 s slab runs 3 s with no idle drift.
- `code-slab-3d`: `power4.out` over 2.6 s instead of `expo.out` over 3 s, which in a 3 s slot snaps face-on in
  about 0.3 s and hides the turn. Thickness is 14 stacked CSS layers (no WebGL).
- `team-chat-channel`: drawn at app scale 1.6 instead of 1.25 (see preset problems).
- `exploded-ui-panels`: layers are nested so each z is relative to the layer below; with flat siblings the
  top → bottom stagger lets the card layer pass the content layer during the collapse and hide the content for a
  few frames. The stage also pulls back to 0.76 while exploded so the 490 px stack stays in frame.
- The agent window starts at 40% opacity instead of 0 so the first frame (the social thumbnail) is not empty.

## Preset problems found

- `team-chat-channel.conversation`: `text 15px` with `app_scale_for_video 1.25` gives 18.75 px at 1080p, under the
  reference's own floor ("never below 2.2% of frame height" = 23.8 px). Fix: app scale 1.6 (text 24 px, name 24 px,
  timestamp 21 px, avatar 58 px), or state the floor as the rule and derive the scale from it.
- `code-slab-3d.github-dark`: `expo.out` over the 3 s turn window looks like a snap in any clip shorter than the
  8 s template. Suggest naming `power4.out` the default for clips under 5 s.
- `exploded-ui-panels.orbit-collapse`: the top → bottom collapse stagger makes layers cross if they are flat
  siblings (an upper layer lands before the one under it). Suggest a build note: nest layers or give each a z
  relative to its parent.
