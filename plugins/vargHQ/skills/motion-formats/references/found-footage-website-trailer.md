# Found-footage website trailer

A 20–30 s horror-tinged teaser that "finds" a strange website: a screen recording, or a camcorder pointed at an old monitor, browses a page that slowly goes wrong, and ends on a title. It is analog-horror grammar applied to the web. Use it for a game, ARG, film, album or product teaser that wants intrigue, in 16:9 (native) or 9:16 (crop the monitor), at a typical length of 25 s.

## How the pros do it
- **Start mundane, end at the worst moment.** The genre escalates from tame to frightening ("progressive horror") and stops when things are at their worst, with no relief and no happy ending. [21]
- **Show less.** Leave the threat obscured so viewers imagine it. Analog horror avoids jump scares and gore, and glitches and noise make the viewer feel powerless. [20][21][22] A widely shared horror clip makes the same point: almost nothing is shown, and it terrifies. [25]
- **Treat the screen as the whole world** (the screenlife rules):
  - One screen and a fixed frame size.
  - Real-time action, with "transitions" hidden inside the frame.
  - Every sound comes from the computer.
  - The cursor shows the inner state: it freezes in hesitation and races in panic. [23]
- **Mimic official or period media.** Analog horror borrows broadcast slates, emergency-alert language and "Technical Difficulties" cards. It often contrasts cheerful easy-listening music with disturbing images. [21] The genre's look is low-fidelity 1960s–2000s TV and tape, often made in Blender or After Effects and then hidden behind degraded equipment. [20]
- **Make the tape damage real,** from a signal model (ntsc-rs: head-switching band, tracking noise, chroma noise) rather than overlays. Practitioners use it for released music videos and shorts. [1][6][7]
- **Trailer structure:**
  - Establish place and tone within about 10 s.
  - Build in "progressions" separated by accents: hits, quick shots, short sound cues.
  - Give each title card a "suck back" and a hit.
  - Telegraph a sound before you show its source, so it reads as sinister on the second hearing.
  - Build tension instead of jump scares. [24]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `found-footage-website-trailer.camcorder-crt` | A camcorder filming a late-90s CRT monitor in a dark room | 4:3 monitor inside 16:9; handheld micro-shake; REC and date HUD in VT323; ntsc-rs LP defaults; screen glow #CFE3FF on #050608 |
| `found-footage-website-trailer.screen-capture` | Clean, early-2000s screen capture that slowly corrupts | 1920×1080 @ 30 fps; real-time cursor; page loads in bands; compression blocks only on the "wrong" beats |
| `found-footage-website-trailer.broadcast-slate` | Emergency-broadcast style interruptions between browsing shots | hard cuts to full-screen slates (white text on #000000 or #0000AA), Courier Prime caps, an easy-listening bed under the slates |
| `found-footage-website-trailer.vertical` | 9:16 crop for Shorts and Reels | the monitor fills 90% of the width; captions in the top 20% safe band; same beats |

## Timing and numbers
- **Beat structure (25.0 s, 30 fps = 750 frames):**
  - 0.0–2.0 s, **cold open:** black, then tape lock-in (a tracking band rolls up for 15 frames). The only sound is a hum (fan, CRT whine, HDD click).
  - 2.0–7.0 s, **mundane:**
    - A URL types in at 12–18 characters/s with irregular gaps of 60–180 ms, on a fictional domain such as `.example`.
    - The page loads top to bottom in 3–5 bands, about 0.4 s each.
    - A slow scroll at 120–180 px/s.
    - A dial-up/handshake or click sound. Place and tone are clear by 7 s, inside the 10 s rule. [24]
  - 7.0–14.0 s, **escalation:** three "wrong" details, with shots shortening from 2.5 s to 1.6 s to 1.0 s:
    - a hit counter jumping to an impossible number;
    - a guestbook entry dated in the future;
    - a photo that loads line by line and shows a figure that wasn't there before.
    - Each reveal gets a 2–4 frame tracking glitch and a low hit. Telegraph one sound (a knock or a breath) here without its source. [24]
  - 14.0–20.0 s, **loss of control:**
    - The cursor moves on its own: smooth, unnaturally linear, no hesitation. That contrasts with the hesitant human cursor before it, which froze for 0.5–1.0 s. [23]
    - A slow push-in on the photo (scale 1.0 → 1.6 over 3 s, ease `power1.in`).
    - 1–2 single-frame flash cuts.
    - A text line such as "DO NOT REFRESH" typed by the page itself.
  - 20.0–21.0 s, **silence:** total silence for 18–30 frames over a frozen frame.
  - 21.0–23.5 s, **title:** hard cut to the title on black with a hit. Hold it at least 2.0 s so it can be read. [24]
  - 23.5–25.0 s, **button:** an 8–12 frame sting. The page reloads and one detail has changed, or the telegraphed sound returns with its source. Cut to black on the sound.
- **Shot list (9 shots):**
  1. Black and lock-in.
  2. Address bar typing.
  3. Page load wide.
  4. Scroll detail (counter).
  5. Guestbook close-up.
  6. Photo loading.
  7. Cursor moves itself.
  8. Push-in on the photo.
  9. Title, then the button.
- **Cursor:**
  - Human: speed 400–900 px/s, with 1–3 px hand jitter at 8–12 Hz while moving and hover pauses of 0.3–1.0 s.
  - "Possessed": a constant 600 px/s on perfectly straight lines with no jitter.
- **Camcorder HUD:**
  - "REC ●" with the dot at #FF2A2A, blinking at 1 Hz (0.5 s on, 0.5 s off).
  - Date and time in the lower right. Use VT323 (OFL-1.1) at 5.5% of frame height, #FFFFFF with a 2 px #000 shadow, inset 6%.
  - Handheld drift: about 0.3% of frame width at 0.5–1 Hz, plus 1 px of high-frequency jitter. Use the registry `camera-shake` handheld profile.
- **Web-page typography (period feel, all free):**
  - Gelasio (OFL-1.1, metric-compatible with Georgia) for body text.
  - Arimo (OFL-1.1, Arial metrics) for UI.
  - Courier Prime (OFL-1.1) for slates and "typed" lines.
  - Links in #0000EE, visited links in #551A8B, page background #FFFFFF or a tiled texture.
  - Set the page at 100% zoom on an 800×600 virtual viewport, then film or scale it.
- **Tape damage on the final picture:** ntsc-rs defaults [1], with the LP tape speed; the head-switching band is always present. Spikes on reveals only: tracking height 24 lines, snow 0.08, for 2–4 frames.

## Build it
1. **The website.** Build the fake site as HTML inside the composition, with only fictional names and domains. Put it in `browser-device-stage` (browser chrome) for the screen-capture preset, or inside `filmed-screen` for the camcorder-CRT preset (perspective, depth of field that follows a named element, LED sub-pixels, focus racks).
2. **Browsing.**
   - `typewriter` or `typed-prompt` for the URL.
   - `scroll-camera-story` or a GSAP `y` tween on the page for scrolling.
   - `cursor-zoom-follow`, `cursor-text-select` and `agent-cursor` for the cursor beats. Use `agent-cursor`'s self-driving feel for the "possessed" cursor and remove its name label.
3. **Camera and HUD.** Wrap in `camera-shake` (handheld profile) and overlay `camcorder-hud` (REC, battery, date, timeline-driven counter). Everything is driven by the timeline clock, so it is seek-safe.
4. **Glitch beats.** Use `scan-band` or `glitch` for the 2–4 frame tracking hits, `rgb-glitch-text` for the slate words, `flash-through-white` or 1-frame black for flash cuts, and `grain-overlay` throughout.
5. **Tape pass.** Render clean, then run ntsc-rs (standalone or OpenFX plugin) with the preset values; optionally downscale and add a CRT after it. [1][3]
6. **Sound.** Use only diegetic computer sounds (fan, clicks, modem, speaker hiss) plus one telegraphed sound. Music, if any, must play from the page itself: a MIDI autoplay or an easy-listening embed. [23][21]

## Mistakes that look amateur
- Showing the monster or face clearly → keep it partial, low-res, out of focus or one frame long. [20][22][25]
- Glitches everywhere → keep the picture clean and degrade only on the reveal beats, so the damage means something. [21]
- An unmotivated orchestral score → only sounds the computer could make. [23]
- Modern UI fonts and flat 2020s web design → period fonts, default link colours, tables and tiled backgrounds.
- Ending on a resolution or a logo with a happy jingle → end at the worst moment, then a short, unsettling button. [21][24]
- A real website, brand or person → always fictional; platform UIs are recognisable mockups only, and their marks belong to their owners.
- A title card that flashes for under 1 s → hold it at least 2 s with a hit sound. [24]

## Sources
[1] ntsc-rs parameter reference (MLT Framework plugin docs) — https://mltframework.org/plugins/FilterOpenfx-wtf-vala^ntscrs/ — tape-damage values
[3] Finn McKenty (@thefinnmckenty) — https://x.com/thefinnmckenty/status/2078469612786847903 — NTSC → downscale → CRT order
[6] Kazuya Kanehisa (@kane_hisa) — https://x.com/kane_hisa/status/2089547611653181655 — ntsc-rs for tracking noise and ghosting
[7] Aoi Aiue (@aiue_aoi_) — https://x.com/aiue_aoi_/status/2066505023367028766 — ntsc-rs used in a released music video
[20] Wikipedia — "Analog horror" — https://en.wikipedia.org/wiki/Analog_horror — conventions; key creators: Kris Straub (Local 58, 2015), Remy Abode (Gemini Home Entertainment, 2019), Alex Kister (The Mandela Catalogue, 2021), Kane Parsons (The Backrooms, 2022; Blender + After Effects behind degraded looks)
[21] Jordan Maison (film journalist) — "Everything there is to know about the analog horror genre" (Videomaker) — https://www.videomaker.com/how-to/directing/film-history/everything-there-is-to-know-about-the-analog-horror-genre/ — progressive horror, slates, music contrast, end at the worst
[22] Jason Hellerman — "What is analog horror" (No Film School) — https://nofilmschool.com/what-is-analog-horror — distortion and powerlessness, limits of old tech as realism
[23] Timur Bekmambetov (producer of Unfriended and Searching) — "Rules of the Screenmovie" (MovieMaker) — https://moviemaker.com/unfriended-rules-of-the-screenmovie-a-manifesto-for-the-digital-age/ — unity of place, time and sound; the cursor as character
[24] Jonny Elwyn (editor and blogger) — "Inside Professional Trailer Editing" — https://jonnyelwyn.co.uk/film-and-video-editing/inside-professional-trailer-editing/ — 10 s open, progressions, title-card hits, telegraphing (quotes Derek Lieu, Tommy Malatesta, James Rowney)
[25] cinesthetic. (@TheCinesthetic; film account, 14k likes) — https://x.com/TheCinesthetic/status/2113398995305504810 — a found-footage scene as proof that horror needs to show very little
