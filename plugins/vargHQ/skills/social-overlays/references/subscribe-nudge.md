# Subscribe-and-bell nudge

A cursor (or tap) clicks a red Subscribe button, it flips to "Subscribed", then the bell gets clicked and wiggles. The classic YouTube-creator reminder, as a lower-third or corner overlay. 16:9 first (long-form), also 9:16 and 1:1; about 5 s.

## How the pros do it
- Don't open with it. Paddy Galloway (consultant to MrBeast and Jesser; 10B+ views generated) jokes that the intro "subscribe, smash that like button" shows up as a falling retention curve [32]. Place the nudge after the first payoff, not in the first 30 s.
- YouTube's own creator account advises asking viewers to subscribe at the end of the video, e.g. after a collab [33]. Two good slots: right after the strongest value moment, and in the final 20 s.
- Keep the ask simple and in a spot that does not interrupt the viewing [34]; an overlay in a lower corner while the creator keeps talking beats a full-screen stop.
- There is no formula: a creator with a large channel reported gaining more subs on videos where he didn't ask [35]. Make the nudge optional per video and short (≤ 5 s).
- Don't collide with end screens: end-screen elements (including a Subscribe element) live in the last 5–20 s of videos ≥ 25 s long, can be up to 4 elements in 16:9, and suppress other interactive elements [8]. If the nudge runs at the end, finish it before the end-screen window or leave the end-screen grid areas empty.
- YouTube tested an automatic glow on the real Subscribe button when a creator says "subscribe" (red/orange/yellow, about 1–2 s, desktop) [11]: say "subscribe" on the frame the overlay button is clicked so the real button may light up too.
- Colours from YouTube's brand page: YouTube Red #FF0033, Almost Black #212121, White [14]. "Subscribed" state is neutral grey/dark; the bell is outlined → filled on click.
- Text contrast: white on #FF0033 is 3.96:1, so the label must be large text (≥24 px or ≥18.5 px bold) [42].
- YouTube's logo, button design and bell are YouTube's trademarks; don't add the logo and don't imply YouTube sponsorship.
- In 9:16, the overlay must stay inside the Shorts safe box (top 288, bottom 672, left 48, right 192 px) [5], or the universal box if cross-posted [1][4].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `subscribe-nudge.subscribe` | Red pill "SUBSCRIBE", cursor clicks, flips to grey "SUBSCRIBED" | pill #FF0033, label #FFFFFF Roboto 700, flipped house dark #272727, or house light #E5E5E5 on light theme |
| `subscribe-nudge.subscribe-bell` | Same, then bell click + 3-swing wiggle | bell 64 px, rotate ±15°→±8°→±4°, 0.5 s, `sine.inOut` |
| `subscribe-nudge.highlight` | Channel avatar + name card, button glow ring (no cursor) | glow ring #FF0033→#FFB400, 1.2 s, opacity 0.6→0 |
| `subscribe-nudge.vertical` | 9:16 version, stacked avatar + button, finger tap | inside Shorts box, centre y = 1060 |

## Timing and numbers (5 s = 150 f)
- 0.00–0.40 s: card (avatar 96 px + channel name + button) slides in from left 64 px, `cubic-bezier(0.05,0.7,0.1,1)` (12 f) [26].
- 0.40–1.10 s: cursor travels to the button (arc, `power2.inOut`).
- 1.20 s: press (scale 0.94, 3 f) → 1.30 s flip to "Subscribed" with 0.2 s colour cross-fade; say "subscribe" on this frame [11].
- 1.60–2.20 s: cursor to bell; 2.30 s click; bell outline→filled 0.1 s; wiggle 0.5 s: rotate 0→15→−12→8→−4→0°, `transform-origin: 50% 8%`.
- 2.8–4.5 s: hold. 4.5–4.75 s: exit left 48 px + fade, `cubic-bezier(0.3,0,0.8,0.15)` (8 f).
- Sizes at 1920×1080: card 620×132 px, bottom-left at x 96, y 820 (above the bottom 15%); button 236×72 px, radius 36 px, label 30 px/700. At 1080×1920: card 760×150 px, button 280×84 px, label 34 px/700.
- Cursor: macOS-style arrow at ~3.5× (≈ 72 px tall at 1080p) with dark outline [40].
- SFX: click on each press frame; optional soft "ding" on the bell, −8 dB under VO (house).

## Build it
1. HyperFrames: `oversized-cursor` for the pointer, `badge-pop` for the bell count dot, `vpn-youtube-spot` block as a YouTube-styled reference scene [40]; card built in HTML.
2. One paused GSAP timeline with labels `press1`, `flip`, `press2`, `wiggle` so editors can retime by moving labels.
3. Flip as two stacked layers (red and grey) cross-faded, not a text swap mid-tween; seek-safe.
4. Remotion: `const flipped = frame >= 39`; bell rotation = keyframed `interpolate(frame, [69,72,75,78,81,84], [0,15,-12,8,-4,0])`.
5. Params: `channelName`, `avatarUrl`, `showBell`, `inputDevice`, `theme: dark|light`, `startAt` (default: after the first payoff marker).

## Mistakes that look amateur
- Nudge in the first 10 s → after the first payoff or at the end [32][33].
- Overlay sitting under end-screen elements → finish before the last 20 s or leave the grid free [8].
- YouTube logo pasted next to the button → not needed and a trademark use; leave it out.
- Bell wiggle as an endless loop → 3 decaying swings, then rest.
- Tiny system cursor on a phone-sized video → 3.5× cursor [40].
- Red label text at 16 px → ≥ 30 px bold at 1080p [42].

## Sources
[1] TikTok safe-zone template · [4] Meta Reels specs · [5] Google vertical safe zone · [8] YouTube Help: end screens · [11] Tubefilter: subscribe glow test · [14] YouTube brand colours · [26] Material 3 motion · [32] Paddy Galloway · [33] YouTube Creators · [34] Nick Nimmin · [35] Cody Wanner · [40] HyperFrames registry · [42] WCAG 2.1 contrast.
