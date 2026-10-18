# Video creative assets

This skill is image-first; video is here so a mixed brief doesn't have to
leave. For generating the footage itself, the `veo-video` skill covers prompt
craft and model constraints — this file covers what Amazon Ads will accept.

## Sponsored Brands video

| Specification | Requirement |
|---|---|
| Duration | 6–45 seconds; 20 seconds or less strongly recommended, 15–30 cited as optimal for impression |
| Dimensions | 1280 × 720, 1920 × 1080, or 3840 × 2160 |
| Aspect ratio | 16:9, square pixel only |
| File format | MP4 or MOV |
| File size | 500 MB or less |
| Video codec | H.264 or H.265 |
| Frame rate | 23.976, 23.98, 24, 25, 29.97, 29.98, or 30 fps |
| Video bitrate | 1 Mbps minimum; 4 Mbps or higher recommended |
| Scan type | Progressive |
| Audio codec | PCM, AAC, or MP3 |
| Audio | Stereo or mono, ≥ 96 kbps, ≥ 44.1 kHz |

## Display / online video

| Specification | Requirement |
|---|---|
| File size | 500 MB maximum |
| Aspect ratio | 16:9 |
| Dimensions | 1920 × 1080 or larger |
| Video bitrate | 4 Mbps minimum |
| Frame rate | 23.976, 24, 25, or 29.97 fps |
| Formats | H.264, MPEG-2, MPEG-4 |
| Audio | PCM or AAC, ≥ 192 kbps, 44.1 or 48 kHz |

## Creative rules

- **Show the product in the first two seconds**, and state key benefits within
  the first five.
- **Videos autoplay silent.** Customers switch audio on. If the video has no
  audio at all, say so on screen with a "No audio" disclaimer.
- **Text size:** at least 50 pt for 720p and 1080p (100 pt preferred), and at
  least 100 pt for 2160p (200 pt preferred). Text must contrast with the
  background and stay on screen long enough to read.
- **Keep text and critical information out of the lower right corner**, where
  the interface overlays it; use Amazon's video safe-zone template.
- **No black or blank frames**, including leading and trailing ones, and no
  letterboxing or pillarboxing.
- **No blurry, unclear, pixelated, or unrecognizable visuals.**
- **Prohibited content:** customer reviews or star ratings, Amazon branding or
  references to Amazon products, deals/discounts/savings promotions, flashing,
  spinning, blinking or pulsating objects, and pressuring or urgent language.
- **Logo last.** Customers remember the brand best when the logo is the final
  thing they see.
- **Language:** audio and text use the marketplace's primary language;
  subtitle anything multilingual. Amazon can embed subtitles within 10 days.

## Generating video for these slots

Veo produces 4–8 second clips, and Sponsored Brands video needs at least 6
seconds, ideally 15–30. So a compliant ad is either a single 6–8 second
generation, or several clips assembled in an editor. The 16:9-only rule means
no portrait generations, and the "product in the first two seconds" rule means
the opening shot has to be the product — plan the shot order around that
rather than opening on atmosphere.

Product fidelity applies exactly as it does to images: generate product shots
from the seller's real photos as references, and check the render before it
ships.

---

**Provenance:** Amazon Ads `resources/ad-specs/sponsored-brands-video` and the
video sections of `library/guides/sponsored-brands-display-ads-moderation`,
captured 2026-09-03.
