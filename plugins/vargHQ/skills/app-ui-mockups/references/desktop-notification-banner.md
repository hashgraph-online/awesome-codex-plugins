# Desktop notification banner

A macOS-style notification banner (frosted card, app icon at the leading edge, bold title, one or two body lines, small time label) that slides in at the top-right of a desktop and later tucks back out. For "you just got paid / your render is done / new signup" moments, reviews told as notifications, and pacing beats in product films. 16:9 native (top-right corner); in 9:16 and 1:1 it sits top-centre like a phone banner. Typical length 3–5 s per banner.

macOS and its notification UI belong to Apple. Use your own invented app icon, never the Apple logo or another company's icon, and never a real person's message.

## How the pros do it
- Write it like the system does: a short title in title-style capitalization with no ending punctuation, and a body in complete, sentence-case sentences; let the system-style truncation handle overflow. [30]
- The system draws the app icon at the leading edge, so don't repeat the app name or icon in the text. [30]
- Feedback motion should be brief and precise, and leave the way it came: a banner that slid in from the right/top tucks back to the right/top. [32]
- Use a spring with a soft overshoot for arrival: first contact at ~0.31 s, ~3% overshoot, settled by ~0.7 s (ω 15, ζ 0.74). Exit faster than entry, 0.45 s ease-in. [60][2]
- Never scale in from 0; if you add scale, start ≥ 0.93 and pair with a 125 ms opacity fade. [2]
- macOS type scale for the card: Headline 13 pt bold for the title, Body 13 pt, Subheadline 11 pt for the time label; multiply by the same factor when you enlarge the card for video. [31]
- Hold long enough to read: 0.6 s + characters ÷ 15, never under 1.5 s for a banner with title + body. [11][12]
- Stack several banners newest-on-top with the older ones pushed down 8–12 px and dimmed, not overlapping chaos. [64]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `desktop-notification-banner.light` | Light frosted card over a wallpaper | card rgba(246,246,246,.72) + backdrop blur 30 px saturate 140%, radius 18 px (×1.5 = 27 px at 1080p), title #000 600, body #1d1d1f |
| `desktop-notification-banner.dark` | Dark frosted card | rgba(40,40,40,.72), border 1 px rgba(255,255,255,.1), title #FFF, body rgba(255,255,255,.85) |
| `desktop-notification-banner.stack` | 3 banners arrive 0.6 s apart and stack | newest on top, previous ones y +12 px, scale 0.97, opacity 0.75 |
| `desktop-notification-banner.huge` | Phone-style big banner for 9:16 | width 88% of frame, title 3.2% of frame height, body 2.8% |

## Timing and numbers
- In: x from +110% of card width → 0 (16:9) or y from −120% → 0 (9:16), spring ω 15 ζ 0.74 (≈ 0.7 s to settle, 21 frames); opacity 0→1 over the first 0.12 s. Out: 0.45 s power2.in, same direction it came. [60][2][32]
- Hold: `max(1.5, 0.6 + chars/15)` s; a 70-character body holds 5.3 s. [11][12]
- Desktop card at 1920×1080 (drawn at 1.5× of a 1280 pt-wide desktop for legibility): width 540 px, padding 18×21 px, icon 57 px (radius 22.5% superellipse), gap icon→text 15 px, margin from top-right 24 px. Title 20 px/24, body 20 px/24, time 16 px grey #8e8e93 right-aligned. [31]
- Material: backdrop-filter blur 30 px + saturate(140%); shadow 0 10px 30px rgba(0,0,0,.18). Blur needs a busy background to read.
- Fonts: Inter (OFL-1.1) 600/400 as the stand-in for SF Pro (Apple-licensed). [49]
- Sound: a short pop cue at first contact (0.31 s), not at the start of the move. [60]

## Build it
1. Start from HyperFrames `native-notification-pop` (system-faithful spring, iOS or macOS geometry, blur, exit none/fade/up) or the `macos-notification` block (5 s, banner with app icon and message); `notification-stack` for 1–5 stacked cards. `npx hyperframes add native-notification-pop`.
2. Variables: `app` (icon + name for accessibility only), `title`, `body`, `time` ("now"), `at`, `exit`.
3. Drive the spring as a closed form sampled by a linear GSAP driver (position = f(t)), so seeks are exact; no `gsap.timeScale()`.
4. Place in a desktop stage (wallpaper + optional menu bar) or over footage; for footage, add a 6–10% darkening of the area behind the card if contrast is low.
5. Remotion: `spring({frame, fps, config:{stiffness: 225, damping: 22.2, mass: 1}})` approximates ω 15, ζ 0.74 (stiffness = ω², damping = 2ζω).

## Mistakes that look amateur
- Title in sentence case with a full stop, or the app name repeated in the body → title-style title, no period, no app name. [30]
- Banner sliding out sideways after sliding in from the top → leave the way it came. [32]
- Linear slide or a big bounce → soft spring, ≤ 3% overshoot. [60]
- Text too small to read in a 1080p frame (true 13 pt at 1×) → draw the desktop at 1.5× scale. [31]
- Banner up for 1 s with two lines of text → reading formula, ≥ 1.5 s. [12]
- Real brand icons (bank, Stripe, Apple) on invented notifications → invented app icon.

## Sources
[2] Emil Kowalski (@emilkowalski) — https://x.com/emilkowalski/status/1954891053032755560 , https://x.com/emilkowalski/status/1954893389679206700
[11] Brysbaert 2019 via BPS — https://www.bps.org.uk/research-digest/most-comprehensive-review-date-finds-average-persons-reading-speed-slower
[12] Netflix English Timed Text Style Guide — https://partnerhelp.netflixstudios.com/hc/en-us/articles/217350977-English-USA-Timed-Text-Style-Guide
[30] Apple HIG Notifications — https://developer.apple.com/design/human-interface-guidelines/notifications
[31] Apple HIG Typography — https://developer.apple.com/design/human-interface-guidelines/typography
[32] Apple HIG Motion — https://developer.apple.com/design/human-interface-guidelines/motion
[49] Google Fonts metadata (Inter OFL) — https://github.com/google/fonts
[60] HyperFrames native-notification-pop — spring constants — https://github.com/heygen-com/hyperframes/tree/main/registry/components/native-notification-pop
