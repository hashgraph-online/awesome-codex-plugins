# Delivering a video, and the traps on the way

## Check the file, not the command

```sh
node <skill folder>/scripts/qa.mjs videos/<slug>/<slug>.mp4 [--kind trailer|clip|music-video]
```

It decodes every frame and reports: decode errors, H.264 and yuv420p (what every phone plays), even
frame sizes, BT.709 colour tags, faststart (the index at the front, so a phone starts playing before
it has downloaded everything), black stretches, frozen stretches (held frames from a capture that
could not keep up), silent stretches, loudness (about -14 LUFS for the web) and true peak (under -1
dBTP), and the 25 MiB a studio site serves itself. Then open the contact sheet and watch it once,
start to end: QA is not a review.

## Shapes

- One 1920x1080 master and its contact sheet is the default delivery.
- A 9:16 cut (1080x1920) when a vertical feed is named: the whole game frame over a blurred fill, or
  a crop that follows the action; never a fixed centre crop that hides it.
- Social feeds autoplay muted: burn the key words into the picture (the film draw-over's kinetic type
  does it) or ship `captions.vtt`, which the studio's video page loads.

- A captured frame is a JPEG: full range, BT.601. `format=yuv420p` and `-colorspace bt709` change
  neither (the file reads back `yuvj420p`, primaries and transfer unset, and phones show it washed
  out or crushed). The skill's encodes end in `scale=out_range=tv:out_color_matrix=bt709,
  format=yuv420p,setparams=…` with `-color_range tv`: converted, then tagged. A file made another
  way: check it with `qa.mjs`.

## Capture

- A game too heavy to paint 30 frames a second is filmed frame by frame instead (`trailer`, or
  `record-fixed.mjs` directly): the page's clock is stepped 1/30 s a frame, so nothing is held.
  Its sound is rebuilt from the game's sound log, not recorded (`references/TRAILER.md`, section 0).

- Wait about three seconds after the page loads before the first frame: fonts, shaders and the first
  round settle.
- A 3D game in headless Chrome paints 12 to 30 fps depending on the machine; the capture records the
  real presentation time of every frame and holds a frame the page did not paint. Many held frames
  (`heldFrames` in `capture.json`) look like stutter: capture again with fewer programs running, or at
  a smaller size.
- Headless Chrome needs the GPU flags; a software renderer makes a game look frozen.
- If the browser path in the environment points at another Chromium-based app (an Electron shell, a
  full-screen app browser), capture fails with "Target.createTarget: Not supported" or opens no page: point it at
  Chrome or Chrome for Testing.
- Keep the raw frames until the edit is locked, then delete them (a minute of 1080p frames is gigabytes;
  check free disk space before a capture and keep at least 10 GB free).

## Honesty

- **Interpolated frames are fabrication.** Frame interpolation (`minterpolate`, "AI smoothing") invents
  gameplay that never happened. Recapture instead.
- Rebuild a constant frame rate from the saved frames and their real timestamps, never from a rounded
  frame clock.
- Mask anything private in a capture before it is public: addresses, ports, a local development URL,
  location text, and QR codes. Decode every QR code in a public video (a QR that points at a local
  address or a private room is a leak and a dead end); re-cutting stills from the footage brings back
  anything masked only in the edit.
- Show real elapsed times and real results; no claim the game does not back up.
- Bots are bots: never imply a crowd that was not there.

## Generated footage

- Model strengths, measured: Veo for acting and hands, Kling for locked-off shots and a face that
  stays the same person; Seedance refuses stills that look like real people; some models smear faces.
- **Continuity is the first thing a viewer notices.** Write the cast and where everyone is into every
  prompt, and check every face on every re-roll: takes silently recast people.
- A punch-in over about 1.3x on a 1080p base goes soft; generate at the framing you need.
- Real UI inside generated footage (a phone screen, a monitor): have an image-edit model paint the
  screen pure green, key it, find the screen's four corners, and warp a frame-exact render of the real
  UI onto it; matte to the tracked corners because some lights key as green too.
- A generated room tone can carry a steady hum: check the spectrum (the `sound` skill's `analyze`
  lists narrow tones).
