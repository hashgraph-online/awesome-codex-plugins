# VHS bouncing-logo screensaver

A logo drifts at constant speed and bounces off the frame edges, played back as if from a worn videotape at full field rate (50 or 60 fps), and lands in a corner on the final beat. Use it as a 5 s brand sting, an end card or a loop, in 16:9, 9:16 or 1:1. The format looks right only when the movement stays smooth and the tape damage stays authentic.

## How the pros do it
- **Pick the logo and frame sizes so the corner hit happens on cue.** The logo's centre reaches a corner after it has travelled `LCM(screen_w − logo_w, screen_h − logo_h)` px on each axis. A change of 1 px can turn a 2-minute cycle into a 46-minute one, so all sizes must be exact integers. [8]
- **Speed is constant, and the angle is exactly 45°.** Each wall flips one velocity component; a corner flips both. Never ease the motion: the hypnotic part is linear travel. [8]
- **Degrade with a real signal model, not an overlay.** Practitioners agree that ntsc-rs, a free open-source simulator, is the reference tool. It models the composite signal and the tape: head switching, tracking noise, chroma loss, ringing and edge wave. It ships as an After Effects/Premiere (OpenFX) plugin and a standalone app. [1][4][6][7]
- **Start from the ntsc-rs defaults, which are already period-correct.** Head-switching band 8 lines tall (offset 3, horizontal shift 72). Tracking noise band 12 lines (wave intensity 15, snow 0.025). Chroma noise 0.1, luma smear 0.5, ringing at frequency 0.45 with power 4, tape speed LP, edge wave intensity 0.5 at speed 4. [1]
- **Chroma is far blurrier than luma.** VHS resolves about 240 lines of luma, roughly a 3 MHz bandwidth. Chroma rides a carrier near 629 kHz with only about ±500 kHz of sidebands, and the tape's crosstalk cancellation halves vertical chroma resolution. Colour should therefore smear about 6× wider than brightness detail, and colour edges should look soft in both directions. [2]
- **Order matters: signal damage → downscale → CRT.** Apply the NTSC/VHS effect first, downscale, then (optionally) feed the low-res image to a CRT shader. A CRT shader run on a full-HD frame looks fake. [3]
- **Sell it on high-contrast edges.** Real tape smears and tapers each row where a bright edge meets dark, and the logo outline is where viewers look. Use a bold, flat logo on a dark field so the ringing and chroma bleed show. [5]
- **Keep the video frame rate at field rate.** Tape motion is 50 fields/s in PAL and 59.94 in NTSC. Rendering the bounce at 50/60 fps (not 24) gives the "live video" smoothness that the format is named for. ntsc-rs can also emulate the field order. [1][2]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `vhs-bouncing-logo.pal-50` | PAL tape, landscape, corner hit at 4.5 s | 1920×1080 @ 50 fps; logo 420×180; free area 1500×900; LCM 4500 px; 1000 px/s = 20 px/frame; y-bounce every 0.9 s, x-bounce every 1.5 s; corner 4.5 s, hold 0.5 s |
| `vhs-bouncing-logo.ntsc-60` | NTSC tape, landscape, same path | 1920×1080 @ 60 fps (59.94 also fine); same geometry; 16.67 px/frame |
| `vhs-bouncing-logo.vertical` | 9:16 phone screensaver | 1080×1920 @ 60 fps; logo 330×170; free 750×1750; LCM 5250; 1166.7 px/s; x-bounce every 0.643 s, y every 1.5 s; corner 4.5 s |
| `vhs-bouncing-logo.square` | 1:1 | 1080×1080 @ 50 fps; logo 330×180; free 750×900; LCM 4500; 1000 px/s; x every 0.75 s, y every 0.9 s; corner 4.5 s |
| `vhs-bouncing-logo.worn-ep` | Heavier "EP-speed rental tape" damage | same geometry; ntsc-rs tape speed EP, tracking height 24 lines, snow 0.08, chroma noise 0.25, chroma phase noise 0.01, head-switch height 12 |

## Timing and numbers
- **Beat structure (5.0 s):**
  - 0.00–0.50 s: tape lock-in. The tracking-noise band (12 lines ≈ 27 px at 1080p) rolls from the bottom to the top and fades out over 25 frames at 50 fps, and a "PLAY ▶" OSD shows top-left.
  - 0.00–4.50 s: the logo travels the whole time. Each wall hit changes the logo colour on that frame. Optionally add a 1-frame chroma kick: shift chroma 4–6 px.
  - 4.50 s: corner hit. Both velocity components flip, the logo colour flashes white for 2 frames, and a soft 2-frame tracking glitch fires.
  - 4.50–5.00 s: hold, or let it bounce out of the corner if you plan to loop.
- **Position is a triangle wave, so the motion is seek-safe.** `x(t) = L − |((v·t + x0) mod 2L) − L|` with `L = free_w`, and the same for y with `free_h`. There is no physics state, so any frame can render alone. The `pal-50` preset starts at a corner when x0 = y0 = 0. Set `x0 = 0.25·L` so the opening frame doesn't already show a corner; this shifts the corner hit, so recompute it with the LCM.
- **Logo colour cycle:** hard-switch on each wall hit through 6 saturated colours, e.g. #FF3B30, #FFCC00, #34C759, #00C7FF, #5856D6, #FF2D92. Never repeat the same colour twice in a row.
- **Converting tape artefacts to 1080p (our calculation from the line counts in [2]):**
  - 1 tape line ≈ 1080/480 = 2.25 px.
  - Head-switching band: 8 lines ≈ 18 px at the very bottom.
  - Luma detail: 240 TVL gives a blur of about 4.5 px per cycle. Use a horizontal Gaussian with sigma 1.5–2 px.
  - Chroma at about 40 TVL gives about 27 px per cycle. Use a horizontal chroma blur with sigma 8–10 px and a 3–6 px chroma delay.
- **OSD:** VT323 (OFL-1.1) at 6% of frame height, #FFFFFF with a 2 px #000 drop shadow. Inset 7% from the top-left; that is 76 px at 1080p.
- **Background:** #000000 or VCR blue #0000AA. Keep the logo at least 3:1 against it so the ringing and bleed read.

## Build it
1. **Clean pass in HyperFrames at the target fps** (50 or 60). Build one paused GSAP timeline whose `onUpdate` sets the logo `x`/`y` from the triangle-wave formula on `tl.time()`. Precompute the wall-hit times, `k·free/v`, for the colour switches. Use the registry `logo-sting` or `extruded-logo` if the logo needs depth, and `camcorder-hud` or `typewriter` for the OSD text.
2. **Tape pass.** Export the clean render and run it through ntsc-rs, either the standalone app or the OpenFX/After Effects plugin, with the preset values above. [1][6]
3. **Lighter in-browser fallback:** layer `grain-overlay` with `scan-band` for one tracking glitch at 4.5 s, and `chromatic-aberration-wipe` or `rgb-glitch-text` for the 1-frame wall kicks.
4. **ffmpeg approximation for footage, or if ntsc-rs is unavailable** (filters from [9]):

   ```
   scale=-2:480:flags=bicubic,format=yuv420p,
   gblur=sigma=1.0:sigmaV=0.01:planes=1,
   gblur=sigma=4:sigmaV=0.5:planes=6,
   chromashift=cbh=2:crh=-2:edge=smear,
   noise=c0s=6:c0f=t+u:c1s=3:c1f=t:c2s=3:c2f=t,
   eq=saturation=0.85:contrast=0.95,
   scale=-2:1080:flags=bicubic
   ```

   The head-switch and tracking bands aren't covered by stock filters, so use ntsc-rs for those.
5. **Optional CRT,** applied last and on the downscaled image [3]. The `yt-screen-warp` overlay is enough. For a full shader, see the pixel-art runner card.

## Mistakes that look amateur
- Easing the bounce or changing the angle → keep the speed constant at 45°; ease only the OSD. [8]
- A corner hit that misses by a few pixels → pick integer sizes from the LCM table, and don't let auto-layout pick the logo size. [8]
- A "VHS" look made of RGB-split plus scanline PNG overlays → use a signal model (ntsc-rs). Real VHS barely splits R/G/B; it smears chroma sideways and drops chroma detail. [1][2]
- The CRT shader on a full-res frame, or applied before the tape damage → follow the order tape → downscale → CRT. [3]
- Rendering at 24/30 fps → the format's appeal is the 50/60 fps field-rate smoothness. [2]
- Constant heavy tracking noise → keep tracking clean except at the lock-in (0–0.5 s) and the corner beat. Constant damage hides the logo.

## Sources
[1] ntsc-rs parameter reference (MLT Framework plugin docs for the open-source ntsc-rs OpenFX filter by valadaptive) — https://mltframework.org/plugins/FilterOpenfx-wtf-vala^ntscrs/ — every default value above
[2] Mika Iisakkila — "VHS / S-VHS" technical comparison (VideoUniversity) — https://www.videouniversity.com/?p=909 — 240 lines, about 3 MHz luma, halved vertical chroma
[3] Finn McKenty (@thefinnmckenty; designer, built a desktop app joining ntsc-rs and RetroArch CRT shaders) — https://x.com/thefinnmckenty/status/2078469612786847903 — order: NTSC distortion → downscale → CRT
[4] Finn McKenty — https://x.com/thefinnmckenty/status/2079554243380572162 — ntsc-rs and RetroArch CRT shaders are best in class (965 likes)
[5] Finn McKenty — https://x.com/thefinnmckenty/status/2099292476687491095 — rows taper on high-contrast edges
[6] Kazuya Kanehisa (@kane_hisa; Japanese video creator, 984 likes) — https://x.com/kane_hisa/status/2089547611653181655 — free ntsc-rs AE plugin simulates tracking noise, ghosting and cross-colour
[7] Aoi Aiue (@aiue_aoi_; music-video creator, 842 likes) — https://x.com/aiue_aoi_/status/2066505023367028766 — the VHS/NTSC noise in a released music video is ntsc-rs
[8] David Vreken — "Bouncing DVD Logo" (The Lost Math Lessons) — http://lostmathlessons.blogspot.com/2016/03/bouncing-dvd-logo.html — LCM corner formula and sensitivity table
[9] FFmpeg filters documentation — https://ffmpeg.org/ffmpeg-filters.html — gblur (sigma, sigmaV, planes), chromashift, noise, boxblur options
