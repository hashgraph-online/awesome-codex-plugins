---
name: ai-media-quality-review
description: Inspect generated images, video and audio before delivery using deterministic metadata, contact-sheet, black-frame and silence checks plus visual and listening review. Use to accept, reject or repair Magic Hour media outputs; it does not generate media or predict audience performance.
license: MIT
metadata:
  author: magichourhq
  version: "1.0.1"
---

# AI media quality review

Review the actual downloaded file against its brief and source media. Run the bundled inspection script when FFmpeg and FFprobe are available:

```sh
python3 scripts/inspect_media.py /absolute/path/to/output.mp4 --output-dir /absolute/path/to/review
```

The script creates `probe.json`, `review.json` and a contact sheet or waveform. It reports technical signals; it does not decide whether the creative result is good. A diagnostic failure stops the script and removes an earlier `review.json` in that output directory. Treat a nonzero exit or missing report as unverified, never as a clean result.

## Apply the acceptance criteria

Read the original request and list the few required outcomes and protected details. Inspect the generated artifacts at full size and the intended delivery size.

- **Image:** composition, crop, identity, anatomy, hands, geometry, product/character details, required text and logos, unwanted text and visible artifacts.
- **Video:** first and last frames, intended action and camera, identity/object continuity, flicker, warping, abrupt cuts, actual dimensions, frame rate, duration and audio streams.
- **Speech/music:** listen through the full export; check intelligibility, pronunciation, last word or phrase, clipping, silence, mouth timing, cut points and synchronization.

Inspect the actual last frame as well as the contact sheet. A gradual fade can darken a face without crossing the black-frame threshold; an empty `black_segments` list does not rule it out. Review contact-sheet flags in context. Intentional black or silent sections are not defects. A clean diagnostic report cannot prove smooth motion, accurate lip sync, good music or a compelling result. Full-speed viewing and listening remain required for those claims.

Return a compact verdict for each requirement: pass, fail or unverified, with the observed evidence. A successful request, valid file or plausible thumbnail is not a quality pass.

When repair is authorized, identify the smallest failed requirement and return to the last accepted source. Change the relevant reference, prompt, route, interval or deterministic finishing step. Do not regenerate an accepted shot to fix captions, crop or assembly, and do not continue spending beyond the existing limit.

Deliver the accepted file and retain the review folder with it. State any unavailable playback, listening, source comparison or broad-subject validation.
